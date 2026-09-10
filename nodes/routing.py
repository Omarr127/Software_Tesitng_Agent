from state import AgentState


<<<<<<< HEAD
def route_needs_plan(state: AgentState):
    """
    Route after observe/discover_pages.

    A plan must only be (re)created the FIRST time we reach this point
    for the current page — i.e. when there is no plan yet (state["plan"]
    is empty/None). On every later loop iteration — continuing on to the
    next already-planned step — we must go straight to "decide".

    This matters a lot: the loop that continues a multi-step plan is
    "check_more_steps" -> (continue) -> "observe". Before this router
    existed, "observe" always flowed on to "plan" unconditionally, which
    silently re-generated the ENTIRE plan (and reset current_step back to
    its first item) on every single step. In practice this meant the
    agent could never progress past step/case one — it kept re-planning
    and re-doing the first action forever, burning model calls (and
    tripping the Gemini free-tier rate limit) until something else (a
    recursion/step limit) finally stopped it. This affects Scenario 1 and
    2 as much as Scenario 3 — it is not explore-specific.

    go_to_next_page() intentionally resets plan to [] when moving to a
    new page, which correctly routes back into "needs_plan" so the new
    page gets its own fresh plan.
    """

    if state.get("plan"):
        return "has_plan"

    return "needs_plan"


=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
def route_action_success(state: AgentState):
    """
    Route after Execute Action.
    """

    if state["action_successful"]:
        return "success"

    return "failure"


def route_more_steps(state: AgentState):
    """
    Route based on whether more planned steps remain.
    """

    if state["more_steps"]:
        return "continue"

    return "finished"


def route_retry(state: AgentState):
    """
    Route based on whether retry is available.
    """

    if state["retries_available"]:
        return "retry"

    return "fail"


def route_task_mode(state: AgentState):
    """
<<<<<<< HEAD
    Route after all steps of the current plan are complete.

    - "maintenance" goes to verify (comparing actual vs expected
      behavior against an existing script).
    - "explore" goes to another page if the single-level, same-domain
      crawl still has one queued within the page budget; otherwise it
      falls through to generate, same as "new_test" — explore mode
      judges each case for itself during generate, it has no existing
      script to verify against.
    - "new_test" goes straight to generate.
    """

    if state["task_mode"] == "maintenance":
        return "maintenance"

    if state["task_mode"] == "explore":
        queue = state.get("pages_queue", [])
        visited = state.get("visited_pages", [])
        max_pages = state.get("max_pages") or 1

        if queue and len(visited) < max_pages:
            return "explore_next_page"

    return "new_test"


def route_has_next_page(state: AgentState):
    """
    Route after go_to_next_page. Separate from route_task_mode's own
    queue check because go_to_next_page may discover that every
    remaining queued link is actually unreachable, in which case there
    is no next page even though the queue looked non-empty beforehand.
    """

    if state.get("has_next_page"):
        return "continue"

    return "generate"
=======
    Route after all steps are complete.
    """

    if state["task_mode"] == "new_test":
        return "new_test"

    return "maintenance"
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2


def route_repair(state: AgentState):
    """
    Route after maintenance verification.
    """

    if state["repair_needed"]:
        return "repair"

    return "complete"