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


def _is_enter_step(current_step) -> bool:
    """
    Return True when the current plan step explicitly
    asks to press Enter / Return.

    This lets Decide safely normalize a model response
    such as:

        fill(target, "\\n")

    into the real keyboard action:

        press("Enter")

    instead of trying to write a newline through the
    clipboard.
    """

    step_text = str(
        current_step or ""
    ).lower()

    enter_phrases = [
        "press enter",
        "hit enter",
        "press return",
        "hit return",
        "submit with enter",
        "submit using enter",
        "submit by pressing enter",
        "submit the search query with enter",
    ]

    return any(
        phrase in step_text
        for phrase in enter_phrases
    )


def decide_action(state: AgentState):
    """
    Decide the next concrete browser action for the current step.

    Important safety rule:
    Decide may only act on information discovered by Observe.
    It must never invent a browser reference or URL.

    Supported actions:

        fill
        click
        navigate
        press

    The press action is currently used for an explicitly
    requested Enter/Return step.
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
    # If Observe found nothing, Decide normally has no
    # valid UI target to act on.
    #
    # A keyboard-only Enter step is the exception because
    # it acts on the currently focused browser element and
    # does not require a new ref.
    # --------------------------------------------------

    if (
        not target_elements
        and not _is_enter_step(
            current_step
        )
    ):

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
    # 3.1 Add a small execution rule for Enter
    #
    # This keeps the existing prompt architecture intact
    # while making the new press action explicit.
    # --------------------------------------------------

    if _is_enter_step(
        current_step
    ):

        prompt += """

IMPORTANT KEYBOARD ACTION RULE:

The current step explicitly requires pressing Enter/Return.

Return:

{
  "action": "press",
  "target": "",
  "value": "Enter"
}

Do NOT represent Enter as:
- a fill action,
- "\\n",
- "\\r",
- clipboard text,
- or a click on an invented target.
"""

    # --------------------------------------------------
    # 4. Send prompt to model
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
    # 7.1 Backward-compatible Enter normalization
    #
    # Smaller models may still return:
    #
    #   action = fill
    #   value = "\\n"
    #
    # for a clear "Press Enter" step.
    #
    # Convert that mechanical representation into the
    # real keyboard action instead of sending a newline
    # to clipboard write.
    # --------------------------------------------------

    if (
        _is_enter_step(
            current_step
        )
        and action_type == "fill"
        and value in [
            "\n",
            "\r",
            "\r\n",
            "Enter",
            "enter",
            "Return",
            "return"
        ]
    ):

        print(
            "Decide: normalized Enter from fill "
            "into a press action."
        )

        action_type = "press"

        next_action = {
            "action": "press",
            "target": "",
            "value": "Enter"
        }

        target = ""
        value = "Enter"

    # --------------------------------------------------
    # 8. Validate action type
    # --------------------------------------------------

    if action_type not in [
        "fill",
        "click",
        "navigate",
        "press"
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
    # 10.1 Press validation
    #
    # For now, only allow Enter/Return when the current
    # plan step explicitly requests it.
    # --------------------------------------------------

    if action_type == "press":

        if not _is_enter_step(
            current_step
        ):

            print(
                "Decide rejected unexpected key press "
                f"for step: {current_step}"
            )

            return {
                "next_action": _empty_action()
            }

        key_value = str(
            value or target or ""
        ).strip().lower()

        if key_value not in [
            "enter",
            "return"
        ]:

            print(
                "Decide rejected unsupported key press: "
                f"{value or target}"
            )

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
    # 13.1 Normalize press
    # --------------------------------------------------

    if action_type == "press":

        next_action["target"] = ""
        next_action["value"] = "Enter"

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
