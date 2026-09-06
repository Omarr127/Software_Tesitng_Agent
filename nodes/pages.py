import json
from urllib.parse import urlparse

from state import AgentState
from tools.browser_tools import open_app, list_page_links


# --------------------------------------------------
# Scenario 3 requirement: explore beyond the first page, but with
# hard, code-enforced (not just prompt-enforced) limits:
#
#   - depth = 1 (links found on the FIRST page only -- discover_pages
#     runs exactly once, guarded by "pages_discovered", and never
#     looks for links on any page it navigates to afterwards).
#   - same domain only (external links are filtered out here in
#     Python, not left to the model to "remember" not to follow).
#   - a hard page-count ceiling, to protect the model API rate/quota.
# --------------------------------------------------

HARD_MAX_PAGES = 4
DEFAULT_MAX_PAGES = 3


def _normalize(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def discover_pages(state: AgentState):
    """
    Run once, right after the first page is observed. Extracts
    same-domain links from the homepage only (depth 1) and queues up
    to (max_pages - 1) of them for later exploration.

    A no-op (cheap passthrough, no LLM/browser calls) for:
      - task_mode other than "explore",
      - a second call once pages_discovered is already True,
      - non-http(s) app paths (e.g. local file:// samples), where
        "same domain" isn't a meaningful concept and there is nothing
        to safely crawl.
    """

    if state.get("task_mode") != "explore":
        return {}

    if state.get("pages_discovered"):
        return {}

    max_pages = state.get("max_pages") or DEFAULT_MAX_PAGES
    max_pages = max(1, min(max_pages, HARD_MAX_PAGES))

    app_path = state.get("app_path", "") or ""
    parsed = urlparse(app_path)

    if parsed.scheme not in ("http", "https") or max_pages <= 1:
        return {
            "pages_discovered": True,
            "pages_queue": [],
            "max_pages": max_pages
        }

    base_domain = parsed.netloc

    link_result = list_page_links()

    if not link_result.get("success"):
        print(
            "Could not read links from the homepage "
            f"({link_result.get('error')}) -- staying on a single page."
        )
        return {
            "pages_discovered": True,
            "pages_queue": [],
            "base_domain": base_domain,
            "max_pages": max_pages
        }

    try:
        raw_links = json.loads(link_result.get("output") or "[]")
    except json.JSONDecodeError:
        print("Link discovery returned invalid JSON -- staying on a single page.")
        raw_links = []

    if not isinstance(raw_links, list):
        raw_links = []

    seen = {_normalize(app_path)}
    same_domain_links = []

    for link in raw_links:
        if not isinstance(link, dict):
            continue

        href = link.get("href", "") or ""

        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        link_parsed = urlparse(href)

        if link_parsed.scheme not in ("http", "https"):
            continue

        # Hard same-domain filter -- external links are never queued,
        # regardless of anything the model might later "decide".
        if link_parsed.netloc != base_domain:
            continue

        normalized = _normalize(href)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        same_domain_links.append(href)

    # Homepage already counts as page 1 of the budget.
    budget = max(0, max_pages - 1)
    pages_queue = same_domain_links[:budget]

    print(
        f"Discovered {len(same_domain_links)} same-domain link(s) on the "
        f"homepage; queuing {len(pages_queue)} within the {max_pages}-page "
        "budget (depth 1, homepage links only)."
    )

    return {
        "pages_discovered": True,
        "pages_queue": pages_queue,
        "base_domain": base_domain,
        "max_pages": max_pages
    }


def go_to_next_page(state: AgentState):
    """
    Explore mode only: advance to the next queued same-domain page, if
    the page budget allows it. Skips over any queued link that fails
    to open (broken/unreachable) instead of stalling the run.
    """

    if state.get("task_mode") != "explore":
        return {"has_next_page": False}

    queue = list(state.get("pages_queue", []))
    visited = list(state.get("visited_pages", []))
    max_pages = state.get("max_pages") or DEFAULT_MAX_PAGES

    while queue and len(visited) < max_pages:

        next_url = queue.pop(0)
        open_result = open_app(next_url)

        if open_result.get("success"):
            visited.append(next_url)

            return {
                "pages_queue": queue,
                "visited_pages": visited,
                "current_page_url": next_url,
                # Fresh page -> fresh plan/case tracking.
                "plan": [],
                "current_step": None,
                "last_case_id": None,
                "has_next_page": True
            }

        print(
            f"Skipping unreachable page {next_url}: "
            f"{open_result.get('error')}"
        )

    return {
        "pages_queue": queue,
        "has_next_page": False
    }
