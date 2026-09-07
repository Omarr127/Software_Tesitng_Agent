import json

from state import AgentState
from skills.skill_loader import load_context_for_node
from model import invoke_llm
from prompts.plan_prompt import build_plan_prompt
from utils.json_utils import clean_json_response
from memory import memory_store


def _is_maintenance_execution_step(goal: str) -> bool:
    """
    Return True when a Scenario 2 plan step represents
    a real user/browser interaction that belongs in the
    Execute node.

    Scenario 2 verification is handled separately by
    the Verify node, so plan steps such as:

        Take a screenshot
        Verify success
        Check result
        Validate outcome
        Observe final state

    must NOT become executable maintenance steps.

    This prevents Execute from receiving:

        action = None

    for a verification-only plan step.
    """

    if not isinstance(goal, str):
        return False

    normalized = goal.strip().lower()

    if not normalized:
        return False

    # --------------------------------------------------
    # Verification / observation-only steps do not
    # belong in the Scenario 2 execution plan.
    # --------------------------------------------------

    non_execution_prefixes = (
        "take a screenshot",
        "capture a screenshot",
        "take screenshot",
        "capture screenshot",
        "screenshot",
        "verify ",
        "validate ",
        "assert ",
        "check ",
        "confirm ",
        "inspect ",
        "observe ",
        "compare ",
        "ensure ",
    )

    if normalized.startswith(
        non_execution_prefixes
    ):
        return False

    # --------------------------------------------------
    # These are also clearly verification-oriented
    # phrases rather than user interactions.
    # --------------------------------------------------

    verification_phrases = (
        "verify the registration result",
        "verify the result",
        "verify the outcome",
        "verify successful",
        "validate the result",
        "validate the outcome",
        "check the result",
        "check the outcome",
        "confirm success",
        "confirm the result",
        "compare actual",
        "compare expected",
        "expected result",
        "actual result",
    )

    for phrase in verification_phrases:

        if phrase in normalized:
            return False

    return True


def _parse_plan(
    response: str,
    task_mode: str = "new_test"
) -> list:
    """
    Parse and validate a plan response into a list
    of step dictionaries.

    Scenario 1:
        Normal functional interaction steps.

    Scenario 2:
        Keep only executable browser interaction
        steps. Final verification is handled by
        the Verify node.

    Scenario 3:
        Every step also carries a case_id so
        multiple consecutive actions can belong
        to the same exploratory case.
    """

    try:

        plan = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "Plan node returned invalid JSON:"
        )

        print(
            response
        )

        return []

    valid_plan = []

    if isinstance(
        plan,
        list
    ):

        for index, step in enumerate(
            plan
        ):

            if not isinstance(
                step,
                dict
            ):
                continue

            goal = step.get(
                "goal"
            )

            if not isinstance(
                goal,
                str
            ):
                continue

            goal = goal.strip()

            if not goal:
                continue

            # --------------------------------------------------
            # Scenario 2:
            #
            # Keep only browser interaction steps.
            #
            # Verification / screenshots / assertions belong
            # to the Verify node and must not enter Execute.
            # --------------------------------------------------

            if (
                task_mode == "maintenance"
                and not _is_maintenance_execution_step(
                    goal
                )
            ):

                print(
                    "Plan: removing maintenance "
                    "verification-only step:"
                )

                print(
                    f"  {goal}"
                )

                continue

            case_id = step.get(
                "case_id"
            )

            if task_mode == "explore":

                # --------------------------------------------------
                # If the model forgot to group steps into
                # exploratory cases, treat each step as its
                # own case rather than losing grouping data.
                # --------------------------------------------------

                if (
                    not case_id
                    or not isinstance(
                        case_id,
                        str
                    )
                ):

                    case_id = (
                        f"case_{index + 1}"
                    )

            valid_plan.append({
                "goal": goal,
                "case_id": case_id
            })

    return valid_plan


def _distinct_case_count(
    plan: list
) -> int:

    return len({
        step.get(
            "case_id"
        )
        for step in plan
        if step.get(
            "case_id"
        )
    })


def create_plan(
    state: AgentState
):
    """
    Create an ordered, atomic testing plan.

    Each plan step should represent ONE logical
    browser interaction so the execution model
    remains:

        Observe
            ↓
        Decide ONE action
            ↓
        Execute
            ↓
        Next plan step

    Scenario 2 is special:

        Browser interaction steps
            ↓
        Complete plan
            ↓
        Verify node

    Screenshot / assertion / verification steps
    therefore do not belong inside its plan.
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
    # 2.1 Explore mode:
    #
    # Get previous memory for the current page.
    # --------------------------------------------------

    known_history = None

    if (
        task_mode == "explore"
        and state.get(
            "app_path"
        )
    ):

        page_url = (
            state.get(
                "current_page_url"
            )
            or state.get(
                "app_path"
            )
        )

        history = (
            memory_store.get_page_history(
                state[
                    "app_path"
                ],
                page_url
            )
        )

        known_history = (
            memory_store.format_history_for_prompt(
                history
            )
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
    # 3.1 Scenario 2:
    #
    # Explicitly prevent the model from putting
    # verification operations in the interaction plan.
    #
    # The Verify node already owns final validation.
    # --------------------------------------------------

    if task_mode == "maintenance":

        prompt += """

IMPORTANT SCENARIO 2 PLANNING RULES:

Return ONLY executable user-interaction steps.

Each plan step must describe one interaction that
can eventually become one of these browser actions:

- fill
- click
- navigate

Examples of valid plan steps:

- Fill the Name field with "John Doe".
- Fill the Email field with "user@example.com".
- Fill the Password field with "Password123!".
- Click the Create Account button.

DO NOT add plan steps for:

- taking screenshots
- taking snapshots
- observing the page
- inspecting the result
- verifying the result
- validating the result
- checking success
- checking an assertion
- comparing actual and expected behavior
- confirming the final result

Scenario 2 final behavior verification is performed
separately by the Verify node after all interaction
steps are complete.

Therefore the last plan step should be the final
required USER INTERACTION, not a verification step.
"""

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

    valid_plan = _parse_plan(
        response,
        task_mode
    )

    # --------------------------------------------------
    # 6.1 Explore mode requires at least
    # 3 DISTINCT CASES.
    # --------------------------------------------------

    MIN_EXPLORE_CASES = 3

    MAX_PLAN_RETRIES = 1

    retries_done = 0

    while (
        task_mode == "explore"
        and _distinct_case_count(
            valid_plan
        ) < MIN_EXPLORE_CASES
        and retries_done
        < MAX_PLAN_RETRIES
    ):

        print(
            f"Plan returned only "
            f"{_distinct_case_count(valid_plan)} "
            "distinct case(s) in explore mode "
            "-- retrying to meet the minimum of "
            f"{MIN_EXPLORE_CASES}."
        )

        response = invoke_llm(
            prompt
        )

        response = clean_json_response(
            response
        )

        retry_plan = _parse_plan(
            response,
            task_mode
        )

        # Keep whichever attempt covers
        # more distinct exploratory cases.

        if (
            _distinct_case_count(
                retry_plan
            )
            >
            _distinct_case_count(
                valid_plan
            )
        ):

            valid_plan = retry_plan

        retries_done += 1

    # --------------------------------------------------
    # 7. Debug Scenario 2 plan
    # --------------------------------------------------

    if task_mode == "maintenance":

        print(
            "\n========== MAINTENANCE PLAN =========="
        )

        for index, step in enumerate(
            valid_plan,
            start=1
        ):

            print(
                f"{index}. "
                f"{step.get('goal')}"
            )

        print(
            "======================================\n"
        )

    # --------------------------------------------------
    # 8. Select first step
    # --------------------------------------------------

    current_step = (
        valid_plan[0]
        if valid_plan
        else None
    )

    # --------------------------------------------------
    # 9. Update LangGraph state
    # --------------------------------------------------

    return {
        "plan": valid_plan,
        "current_step": current_step
    }