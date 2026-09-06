import json
import os
import re
import time
import hashlib
from urllib.parse import urlparse


# --------------------------------------------------
# Cross-run memory for Scenario 3 (explore).
#
# Every run used to start from zero: same app, same page, run twice
# in a row, and the agent had no way to know what it already tried
# last time -- so a second run could easily rediscover the exact same
# case, or "forget" a bug it had already found.  This stores, per
# app + per page, a rolling history of past cases and their verdicts
# in a small JSON file on disk, so:
#
#   - plan.py can steer the model away from re-proposing an identical
#     case it already ran, and instead cover new ground -- or
#     deliberately re-check a case that was previously "BUG FOUND",
#     to see if it has since been fixed.
#   - generate.py records this run's verdicts back into the same file
#     once the report is produced, so the NEXT run benefits too.
#
# Deliberately simple (flat JSON files, no DB): this agent already
# calls out to an LLM for every real decision, so the memory layer
# itself should stay cheap, dependency-free, and easy to inspect or
# delete by hand (just remove the file under memory/store/).
# --------------------------------------------------

STORE_DIR = os.path.join(os.path.dirname(__file__), "store")

# Oldest entries for a page are dropped once a page has more than
# this many stored, so the file can't grow forever.
MAX_HISTORY_PER_PAGE = 30

# Only the most recent N history items per page are ever shown back
# to the model in a prompt, to keep prompts small and cheap.
MAX_HISTORY_IN_PROMPT = 8


def _slug_for_app(app_path: str) -> str:
    parsed = urlparse(app_path)
    readable = (parsed.netloc or parsed.path or "app").strip("/")
    readable = re.sub(r"[^a-zA-Z0-9._-]+", "_", readable)[:60] or "app"
    digest = hashlib.sha1(app_path.encode("utf-8")).hexdigest()[:10]
    return f"{readable}_{digest}.json"


def _path_for_app(app_path: str) -> str:
    os.makedirs(STORE_DIR, exist_ok=True)
    return os.path.join(STORE_DIR, _slug_for_app(app_path))


def load(app_path: str) -> dict:
    path = _path_for_app(app_path)

    if not os.path.exists(path):
        return {"app_path": app_path, "pages": {}}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt/unreadable memory should never crash a run --
        # just start fresh for this app.
        return {"app_path": app_path, "pages": {}}

    if not isinstance(data, dict):
        return {"app_path": app_path, "pages": {}}

    data.setdefault("pages", {})
    return data


def save(app_path: str, data: dict):
    path = _path_for_app(app_path)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Warning: could not save exploration memory for {app_path}: {e}")


def get_page_history(
    app_path: str,
    page_url: str,
    limit: int = MAX_HISTORY_IN_PROMPT
) -> list:
    data = load(app_path)
    entries = data.get("pages", {}).get(page_url, [])
    return entries[-limit:]


def record_page_cases(app_path: str, page_url: str, cases: list):
    """
    cases: list of {"name": str, "verdict": str, "reason": str}
    """

    if not cases:
        return

    data = load(app_path)
    pages = data.setdefault("pages", {})
    entries = pages.setdefault(page_url, [])

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    for case in cases:
        entries.append({
            "name": (case.get("name") or "")[:120],
            "verdict": case.get("verdict") or "",
            "reason": (case.get("reason") or "")[:200],
            "seen_at": timestamp
        })

    # Keep only the most recent MAX_HISTORY_PER_PAGE entries per page.
    pages[page_url] = entries[-MAX_HISTORY_PER_PAGE:]

    save(app_path, data)


def format_history_for_prompt(history: list) -> str:
    if not history:
        return "(no earlier runs recorded for this page)"

    lines = []
    for entry in history:
        lines.append(
            f'- "{entry.get("name", "")}" -> {entry.get("verdict", "")} '
            f'(seen {entry.get("seen_at", "in an earlier run")})'
        )
    return "\n".join(lines)


# --------------------------------------------------
# Pulls structured data back out of generate_output's human-readable
# report, using the "# Page: <url>" / "# Case: <name> - VERDICT -
# reason" line formats the generate prompt already asks for.
# Best-effort: lines that don't match the expected shape are simply
# skipped -- this must never raise or block a run just because the
# model's formatting drifted slightly on a given run.
# --------------------------------------------------

_CASE_LINE_RE = re.compile(
    r"^#\s*Case:\s*(?P<name>.+?)\s*-\s*"
    r"(?P<verdict>HANDLED|BUG FOUND|INCONCLUSIVE)\s*-\s*"
    r"(?P<reason>.+?)\s*$"
)

_PAGE_LINE_RE = re.compile(r"^#\s*Page:\s*(?P<url>\S+)\s*$")


def parse_case_report(generated_text: str, default_page_url: str) -> dict:
    current_page = default_page_url
    result = {}

    for raw_line in (generated_text or "").splitlines():
        line = raw_line.strip()

        page_match = _PAGE_LINE_RE.match(line)
        if page_match:
            current_page = page_match.group("url")
            continue

        case_match = _CASE_LINE_RE.match(line)
        if case_match:
            result.setdefault(current_page, []).append({
                "name": case_match.group("name"),
                "verdict": case_match.group("verdict"),
                "reason": case_match.group("reason")
            })

    return result
