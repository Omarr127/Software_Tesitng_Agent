import json

from state import AgentState
from skills.skill_loader import load_context_for_node
from model import invoke_llm
from prompts.plan_prompt import build_plan_prompt
from utils.json_utils import clean_json_response
from memory import memory_store


def _parse_plan(response: str, task_mode: str = "new_test") -> list:
    """
    Parse and validate a plan response into a list of step dicts.

    For "explore", every step also carries a "case_id" so multiple
    consecutive steps (e.g. fill an invalid value, then click submit)
    can be recognized as belonging to the same test case rather than
    being treated as unrelated one-action steps.
    """

    try:
        plan = json.loads(response)
    except json.JSONDecodeError:
        print("Plan node returned invalid JSON:")
        print(response)
        return []

    valid_plan = []

    if isinstance(plan, list):
        for index, step in enumerate(plan):
            if not isinstance(step, dict):
                continue

            goal = step.get("goal")

            if not isinstance(goal, str):
                continue

            goal = goal.strip()

            if not goal:
                continue

            case_id = step.get("case_id")

            if task_mode == "explore":
                # If the model forgot to group steps into cases, fall
                # back to treating each step as its own case rather
                # than silently losing the grouping information.
                if not case_id or not isinstance(case_id, str):
                    case_id = f"case_{index + 1}"

            valid_plan.append({
                "goal": goal,
                "case_id": case_id
            })

    return valid_plan


def _distinct_case_count(plan: list) -> int:
    return len({
        step.get("case_id")
        for step in plan
        if step.get("case_id")
    })


def create_plan(state: AgentState):
    """
    Create an ordered, atomic testing plan.

    Each plan step should represent ONE logical browser action
    so that the LangGraph execution model remains:

        Observe
            ↓
        Decide ONE action
            ↓
        Execute
            ↓
        Next plan step
    """

    # --------------------------------------------------
    # 1. Get task mode
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    # --------------------------------------------------
    # 2. Load only Plan-specific skill context
    # --------------------------------------------------

    context = load_context_for_node(
        task_mode,
        "plan"
    )

    # --------------------------------------------------
    # 2.1 Explore mode: get memory history for this page
    #
    # The plan prompt gets a short summary of cases
    # already tried on this same page in earlier runs,
    # so repeat runs explore new ground instead of
    # rediscovering the same case every time.
    # --------------------------------------------------

    known_history = None

    if task_mode == "explore" and state.get("app_path"):
        page_url = (
            state.get("current_page_url")
            or state.get("app_path")
        )

        history = memory_store.get_page_history(
            state["app_path"],
            page_url
        )

        known_history = memory_store.format_history_for_prompt(
            history
        )

    # --------------------------------------------------
    # 3. Build Plan prompt
    # --------------------------------------------------

    prompt = build_plan_prompt(
        context=context,
        task_mode=task_mode,
        test_intent=state.get(
            "test_intent",
            ""
        ),
        existing_script=state.get(
            "existing_script",
            ""
        ),
        observed_elements=state.get(
            "target_elements",
            []
        ),
        known_history=known_history
    )

    # --------------------------------------------------
    # 4. Ask model to create the plan
    # --------------------------------------------------

    response = invoke_llm(
        prompt
    )

    # --------------------------------------------------
    # 5. Clean model response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 6. Parse plan
    # --------------------------------------------------

    valid_plan = _parse_plan(response, task_mode)

    # --------------------------------------------------
    # 6.1 Explore mode requires at least 3 DISTINCT CASES
    #
    # This is a mechanical retry to enforce the count the
    # skill/prompt already asks for, not new content we
    # are supplying. We count distinct case_id values,
    # not steps, since a single case can legitimately
    # need more than one step (e.g. fill + submit).
    # --------------------------------------------------

    MIN_EXPLORE_CASES = 3
    MAX_PLAN_RETRIES = 1

    retries_done = 0

    while (
        task_mode == "explore"
        and _distinct_case_count(valid_plan) < MIN_EXPLORE_CASES
        and retries_done < MAX_PLAN_RETRIES
    ):
        print(
            f"Plan returned only {_distinct_case_count(valid_plan)} "
            "distinct case(s) in explore mode -- retrying to meet the "
            f"minimum of {MIN_EXPLORE_CASES}."
        )

        response = invoke_llm(prompt)
        response = clean_json_response(response)

        retry_plan = _parse_plan(response, task_mode)

        # Keep whichever attempt covers more distinct cases
        if _distinct_case_count(retry_plan) > _distinct_case_count(valid_plan):
            valid_plan = retry_plan

        retries_done += 1

    # --------------------------------------------------
    # 7. Select first step
    # --------------------------------------------------

    current_step = (
        valid_plan[0]
        if valid_plan
        else None
    )

    # --------------------------------------------------
    # 8. Update LangGraph state
    # --------------------------------------------------

    return {
        "plan": valid_plan,
        "current_step": current_step
    }