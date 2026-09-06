import json

from state import AgentState
from skills.skill_loader import load_context_for_node
from model import invoke_llm
from prompts.reflect_prompt import build_reflect_prompt
from utils.json_utils import clean_json_response


def reflect_replan(state: AgentState):
    """
    Diagnose an action failure or maintenance verification mismatch
    and adjust the current step or plan.

    Only the skill context relevant to the Reflect node is loaded.
    """

    # --------------------------------------------------
    # 1. Get task mode
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    # --------------------------------------------------
    # 2. Load only Reflect-specific skill context
    # --------------------------------------------------

    context = load_context_for_node(
        task_mode,
        "reflect"
    )

    # --------------------------------------------------
    # 3. Build reflection prompt
    # --------------------------------------------------

    prompt = build_reflect_prompt(
        context=context,
        task_mode=task_mode,
        current_step=state.get(
            "current_step"
        ),
        plan=state.get(
            "plan",
            []
        ),
        next_action=state.get(
            "next_action"
        ),
        action_result=state.get(
            "action_result"
        ),
        target_elements=state.get(
            "target_elements",
            []
        ),
        repair_needed=state.get(
            "repair_needed",
            False
        ),
        expected_result=state.get(
            "expected_result"
        ),
        actual_result=state.get(
            "actual_result"
        )
    )

    # --------------------------------------------------
    # 4. Send prompt to Gemini
    # --------------------------------------------------

    response = invoke_llm(
        prompt
    )

    # --------------------------------------------------
    # 5. Clean Gemini response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 6. Parse response
    # --------------------------------------------------

    try:

        revised_data = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "Reflect node returned invalid JSON:"
        )

        print(response)

        revised_data = {}

    # --------------------------------------------------
    # 7. Get revised current step
    # --------------------------------------------------

    revised_step = revised_data.get(
        "current_step",
        state.get("current_step")
    )

    # --------------------------------------------------
    # 8. Get revised plan
    # --------------------------------------------------

    revised_plan = revised_data.get(
        "plan",
        state.get("plan", [])
    )

    # --------------------------------------------------
    # 9. Validate current step
    # --------------------------------------------------

    if not isinstance(
        revised_step,
        dict
    ):

        revised_step = state.get(
            "current_step"
        )

    # --------------------------------------------------
    # 10. Validate plan
    # --------------------------------------------------

    valid_plan = []

    if isinstance(
        revised_plan,
        list
    ):

        for step in revised_plan:

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

            valid_plan.append(
                {
                    "goal": goal
                }
            )

    # --------------------------------------------------
    # 11. Fall back to existing plan if necessary
    # --------------------------------------------------

    if not valid_plan:

        valid_plan = state.get(
            "plan",
            []
        )

    # --------------------------------------------------
    # 12. Make sure current step belongs to plan
    # --------------------------------------------------

    if (
        revised_step is None
        or revised_step not in valid_plan
    ):

        revised_step = (
            valid_plan[0]
            if valid_plan
            else None
        )

    # --------------------------------------------------
    # 13. Update LangGraph state
    # --------------------------------------------------

    return {
        "current_step": revised_step,
        "plan": valid_plan
    }