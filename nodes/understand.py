import json

from state import AgentState
from skills.skill_loader import load_context_for_node
from model import invoke_llm
from prompts.understand_prompt import build_understand_prompt
from utils.json_utils import clean_json_response


def understand_task(state: AgentState):
    """
    Understand the testing task and identify the test intent.

    Only the skill context relevant to the Understand node
    is loaded into the model prompt.
    """

    # --------------------------------------------------
    # 1. Get task mode
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    # --------------------------------------------------
    # 2. Load only Understand-specific skill context
    # --------------------------------------------------

    context = load_context_for_node(
        task_mode,
        "understand"
    )

    # --------------------------------------------------
    # 3. Select the correct task input
    # --------------------------------------------------

    if task_mode == "new_test":

        task_input = state.get(
            "requirement",
            ""
        )

    elif task_mode == "maintenance":

        task_input = state.get(
            "existing_script",
            ""
        )

    else:

        # explore: no requirement or script was given — tell the
        # model its job is to propose its own edge cases to probe.
        task_input = (
            "No requirement or existing script was provided. "
            "Explore the application and identify edge cases worth "
            "probing, following the exploratory testing skill."
        )

    # --------------------------------------------------
    # 4. Build the prompt
    # --------------------------------------------------

    prompt = build_understand_prompt(
        context=context,
        task_mode=task_mode,
        task_input=task_input
    )

    # --------------------------------------------------
    # 5. Send prompt to Gemini
    # --------------------------------------------------

    response = invoke_llm(
        prompt
    )

    # --------------------------------------------------
    # 6. Clean Gemini response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 7. Parse response
    # --------------------------------------------------

    try:

        parsed_response = json.loads(
            response
        )

        test_intent = parsed_response.get(
            "test_intent"
        )

        if not isinstance(
            test_intent,
            str
        ):
            raise ValueError(
                "Missing test_intent"
            )

        test_intent = test_intent.strip()

        if not test_intent:
            raise ValueError(
                "Empty test_intent"
            )

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError
    ):

        print(
            "Understand node returned invalid JSON:"
        )

        print(response)

        test_intent = response.strip()

    # --------------------------------------------------
    # 8. Update LangGraph state
    # --------------------------------------------------

    return {
        "test_intent": test_intent
    }