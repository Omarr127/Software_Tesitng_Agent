import json

from state import AgentState
from skills.skill_loader import load_context_for_node
from model import invoke_llm
from prompts.decide_prompt import build_decide_prompt
from utils.json_utils import clean_json_response


def _empty_action():
    """
    Return a safe empty action.

    The Decide node must never invent an action when
    Observe did not provide usable UI information.
    """

    return {
        "action": None,
        "target": None,
        "value": None
    }


def decide_action(state: AgentState):
    """
    Decide the next concrete browser action for the current step.

    Important safety rule:
    Decide may only act on information discovered by Observe.
    It must never invent a browser reference or URL.
    """

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    target_elements = state.get(
        "target_elements",
        []
    )

    current_step = state.get(
        "current_step"
    )

    existing_script = state.get(
        "existing_script",
        ""
    )

    # --------------------------------------------------
    # 1. Safety check
    #
    # If Observe found nothing, Decide has no valid
    # UI target to act on.
    #
    # Do NOT ask the LLM to guess.
    # --------------------------------------------------

    if not target_elements:

        print(
            "Decide: no target elements were observed."
        )

        return {
            "next_action": _empty_action()
        }

    # --------------------------------------------------
    # 2. Load node-specific context
    # --------------------------------------------------

    context = load_context_for_node(
        task_mode,
        "decide"
    )

    # --------------------------------------------------
    # 3. Build decision prompt
    # --------------------------------------------------

    prompt = build_decide_prompt(
        context,
        task_mode,
        current_step,
        target_elements,
        existing_script
    )

    # --------------------------------------------------
    # 4. Send prompt to Gemini
    # --------------------------------------------------

    try:

        response = invoke_llm(
            prompt
        )

    except Exception as e:

        print(
            f"Decide LLM request failed: {e}"
        )

        return {
            "next_action": _empty_action()
        }

    # --------------------------------------------------
    # 5. Clean response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 6. Parse JSON
    # --------------------------------------------------

    try:

        next_action = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "Decide node returned invalid JSON:"
        )

        print(response)

        return {
            "next_action": _empty_action()
        }

    # --------------------------------------------------
    # 7. Validate response structure
    # --------------------------------------------------

    if not isinstance(
        next_action,
        dict
    ):

        return {
            "next_action": _empty_action()
        }

    action_type = next_action.get(
        "action"
    )

    target = next_action.get(
        "target"
    )

    value = next_action.get(
        "value"
    )

    # --------------------------------------------------
    # 8. Validate action type
    # --------------------------------------------------

    if action_type not in [
        "fill",
        "click",
        "navigate"
    ]:

        return {
            "next_action": _empty_action()
        }

    # --------------------------------------------------
    # 9. IMPORTANT:
    # fill / click MUST use an observed reference
    # --------------------------------------------------

    if action_type in [
        "fill",
        "click"
    ]:

        observed_refs = {
            element.get("ref")
            for element in target_elements
            if isinstance(element, dict)
            and element.get("ref")
        }

        if target not in observed_refs:

            print(
                f"Decide rejected invented target: {target}"
            )

            return {
                "next_action": _empty_action()
            }

    # --------------------------------------------------
    # 10. Navigate validation
    # --------------------------------------------------

    if action_type == "navigate":

        step_text = str(
            current_step or ""
        ).lower()

        navigation_keywords = [
            "navigate",
            "go to",
            "open page",
            "open the page",
            "visit",
            "navigate to",
            "redirect"
        ]

        navigation_required = any(
            keyword in step_text
            for keyword in navigation_keywords
        )

        if not navigation_required:

            print(
                "Decide rejected unexpected navigation "
                f"for step: {current_step}"
            )

            return {
                "next_action": _empty_action()
            }

        if not value:

            return {
                "next_action": _empty_action()
            }

    # --------------------------------------------------
    # 11. Normalize navigate
    # --------------------------------------------------

    if action_type == "navigate":

        next_action["target"] = ""

        if not next_action.get("value"):

            next_action["value"] = target

    # --------------------------------------------------
    # 12. Normalize click
    # --------------------------------------------------

    if action_type == "click":

        next_action["value"] = ""

    # --------------------------------------------------
    # 13. Normalize fill
    # --------------------------------------------------

    if action_type == "fill":

        if value is None:

            return {
                "next_action": _empty_action()
            }

        next_action["value"] = str(
            value
        )

    # --------------------------------------------------
    # 14. Preserve the observed element
    #
    # IMPORTANT:
    #
    # The LLM chooses the target ref.
    # The browser observation provides the actual
    # element information and bounding box.
    #
    # Coordinates are NEVER generated by the LLM.
    # --------------------------------------------------

    if action_type in [
        "fill",
        "click"
    ]:

        selected_element = None

        for element in target_elements:

            if not isinstance(
                element,
                dict
            ):
                continue

            if element.get("ref") == target:

                selected_element = element.copy()

                break

        if selected_element is not None:

            next_action["element"] = selected_element

    # --------------------------------------------------
    # 15. Return validated action
    # --------------------------------------------------

    return {
        "next_action": next_action
    }