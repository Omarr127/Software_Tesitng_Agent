import json

from state import AgentState
from tools.browser_tools import (
    snapshot,
    screenshot,
    get_box,
    open_app
)
from skills.skill_loader import load_context_for_node
from model import invoke_vlm
from prompts.observe_prompt import build_observe_prompt
from utils.json_utils import clean_json_response
from metrics.tracker import metrics_logger


def _parse_box_output(output):
    """
    Parse the bounding box returned by Agent Browser.

    Expected information:

        x
        y
        width
        height

    The browser output format may vary slightly,
    so this function tries to handle JSON output
    safely.

    Returns:
        dict or None
    """

    if not output:
        return None

    # --------------------------------------------------
    # 1. Try JSON parsing
    # --------------------------------------------------

    try:

        data = json.loads(
            output
        )

        if isinstance(data, dict):

            box = {
                "x": data.get("x"),
                "y": data.get("y"),
                "width": data.get("width"),
                "height": data.get("height")
            }

            if all(
                value is not None
                for value in box.values()
            ):
                return box

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------
    # 2. Try to extract values from text
    #
    # This is a fallback in case Agent Browser
    # returns something such as:
    #
    # x: 120
    # y: 180
    # width: 300
    # height: 40
    # --------------------------------------------------

    import re

    patterns = {
        "x": r"x\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        "y": r"y\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        "width": r"width\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        "height": r"height\s*[:=]\s*(-?\d+(?:\.\d+)?)"
    }

    values = {}

    for key, pattern in patterns.items():

        match = re.search(
            pattern,
            output,
            re.IGNORECASE
        )

        if not match:
            return None

        value = match.group(1)

        try:

            number = float(value)

            if number.is_integer():
                number = int(number)

            values[key] = number

        except ValueError:

            return None

    return values


def _attach_element_boxes(
    elements
):
    """
    Get the real browser bounding box for every
    VLM-selected element.

    The VLM identifies the relevant element.

    Agent Browser determines its actual location.

    This keeps coordinate detection out of the
    VLM prompt and therefore does not increase
    VLM token usage.
    """

    elements_with_boxes = []

    for element in elements:

        if not isinstance(
            element,
            dict
        ):
            continue

        ref = element.get(
            "ref"
        )

        if not ref:
            continue

        # --------------------------------------------------
        # Get actual browser bounding box
        # --------------------------------------------------

        box_result = get_box(
            ref
        )

        box = None

        if box_result.get(
            "success"
        ):

            box = _parse_box_output(
                box_result.get(
                    "output",
                    ""
                )
            )

        # --------------------------------------------------
        # Preserve original element information
        # --------------------------------------------------

        updated_element = {
            "label": element.get(
                "label",
                ""
            ),
            "type": element.get(
                "type",
                ""
            ),
            "ref": ref,
            "box": box
        }

        elements_with_boxes.append(
            updated_element
        )

    return elements_with_boxes


def _validate_case_with_vlm(
    case_id,
    case_actions,
    snapshot_text,
    screenshot_path
):
    """
    Run VLM-based validation for a single explore-mode case.

    This is the per-case equivalent of _validate_final_result
    in generate.py — it uses the same approach (snapshot +
    screenshot + VLM) but scoped to one case's actions and
    their expected outcome.

    Called at the case boundary in observe_ui, while the page
    still shows the result of the just-completed case (before
    the page is reset for the next case).

    Returns:
        {
            "case_id": str,
            "validated": bool,
            "evidence": str
        }
    """

    # Build a summary of what this case did
    action_summary = []
    for action in case_actions:
        action_type = action.get("action", "")
        target = action.get("target", "")
        value = action.get("value", "")

        if action_type == "fill":
            action_summary.append(
                f"Filled {target} with \"{value}\""
            )
        elif action_type == "click":
            action_summary.append(
                f"Clicked {target}"
            )
        elif action_type == "navigate":
            action_summary.append(
                f"Navigated to {value}"
            )

    actions_text = "\n".join(action_summary) or "(no actions)"

    # Get the goal description from the last action's step
    case_goal = ""
    for action in case_actions:
        goal = action.get("goal", "")
        if goal:
            case_goal = goal

    validation_prompt = f"""
You are validating the result of one exploratory test case.

Case ID: {case_id}
Case goal: {case_goal}

Actions performed:
{actions_text}

Current page state (browser snapshot):
{snapshot_text}

Look at the screenshot together with the browser snapshot.

Determine whether the application handled this test case
correctly or whether a bug was found.

Evidence may include:
- A validation error message shown (handled correctly)
- Form submission blocked with feedback (handled correctly)
- Invalid input silently accepted (bug found)
- No feedback at all for invalid input (bug found)
- Application crash or unexpected behavior (bug found)
- Insufficient evidence to judge (inconclusive)

Return JSON only:

{{
    "validated": true,
    "evidence": "short description of what was observed"
}}

or:

{{
    "validated": false,
    "evidence": "short description of the issue found"
}}
"""

    try:

        response = invoke_vlm(
            validation_prompt,
            screenshot_path
        )

        response = clean_json_response(response)

        validation = json.loads(response)

        if not isinstance(validation, dict):
            return {
                "case_id": case_id,
                "validated": False,
                "evidence": "Validation returned invalid structure."
            }

        return {
            "case_id": case_id,
            "validated": validation.get("validated", False),
            "evidence": validation.get(
                "evidence",
                "No evidence provided."
            )
        }

    except Exception as e:

        print(
            f"Per-case VLM validation failed for {case_id}: {e}"
        )

        return {
            "case_id": case_id,
            "validated": False,
            "evidence": f"Validation request failed: {e}"
        }


def analyze_ui_with_vlm(
    task_mode,
    current_step,
    existing_script,
    snapshot_text,
    screenshot_path
):
    """
    Analyze the current UI using the VLM.

    The VLM receives only the context required for UI observation:
    - the node-specific observation instructions
    - the task mode
    - the current testing step
    - the existing script when needed for maintenance
    - the current browser snapshot
    - the screenshot

    The VLM identifies relevant elements.

    Bounding boxes are obtained separately from
    Agent Browser after the VLM response.
    """

    # --------------------------------------------------
    # 1. Make sure screenshot exists
    # --------------------------------------------------

    if not screenshot_path:

        print(
            "Observe: screenshot path is missing."
        )

        return []

    # --------------------------------------------------
    # 2. Load only the Observe-specific skill context
    # --------------------------------------------------

    try:

        context = load_context_for_node(
            task_mode,
            "observe"
        )

    except Exception as e:

        print(
            f"Observe skill context loading failed: {e}"
        )

        return []

    # --------------------------------------------------
    # 3. Build VLM prompt
    # --------------------------------------------------

    prompt = build_observe_prompt(
        context,
        task_mode,
        current_step,
        existing_script,
        snapshot_text
    )

    # --------------------------------------------------
    # 4. Debug information
    # --------------------------------------------------

    print(
        "\n========== OBSERVE DEBUG =========="
    )

    print(
        "Task mode:"
    )

    print(
        task_mode
    )

    print(
        "\nCurrent step:"
    )

    print(
        current_step
    )

    print(
        "\nBrowser snapshot:"
    )

    print(
        snapshot_text
    )

    print(
        "\nObserve context loaded:"
    )

    print(
        context
    )

    print(
        "\nScreenshot:"
    )

    print(
        screenshot_path
    )

    print(
        "===================================\n"
    )

    # --------------------------------------------------
    # 5. Send prompt + screenshot to VLM
    # --------------------------------------------------

    try:

        response = invoke_vlm(
            prompt,
            screenshot_path
        )

        print(
            "\n========== RAW VLM RESPONSE =========="
        )

        print(
            response
        )

        print(
            "======================================\n"
        )

        response = clean_json_response(
            response
        )

    except Exception as e:

        print(
            f"VLM request failed: {e}"
        )

        return []

    # --------------------------------------------------
    # 6. Parse VLM response
    # --------------------------------------------------

    try:

        target_elements = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "\n========== CLEANED VLM RESPONSE =========="
        )

        print(
            response
        )

        print(
            "===========================================\n"
        )

        print(
            "VLM returned invalid JSON."
        )

        return []

    # --------------------------------------------------
    # 7. Validate returned structure
    # --------------------------------------------------

    if not isinstance(
        target_elements,
        list
    ):

        print(
            "Observe: VLM response is not a list."
        )

        print(
            "Received type:",
            type(target_elements).__name__
        )

        return []

    # --------------------------------------------------
    # 8. Validate individual elements
    # --------------------------------------------------

    valid_elements = []

    for element in target_elements:

        if not isinstance(
            element,
            dict
        ):
            continue

        ref = element.get(
            "ref"
        )

        if not ref:
            continue

        valid_elements.append(
            {
                "label": element.get(
                    "label",
                    ""
                ),
                "type": element.get(
                    "type",
                    ""
                ),
                "ref": ref
            }
        )

    # --------------------------------------------------
    # 9. Get real browser coordinates
    #
    # IMPORTANT:
    #
    # The VLM does NOT generate these coordinates.
    #
    # Agent Browser gets them directly.
    # --------------------------------------------------

    valid_elements = _attach_element_boxes(
        valid_elements
    )

    # --------------------------------------------------
    # 10. Show final observation result
    # --------------------------------------------------

    print(
        "\n========== OBSERVE RESULT =========="
    )

    print(
        "Target elements:"
    )

    print(
        valid_elements
    )

    print(
        "====================================\n"
    )

    return valid_elements


def observe_ui(state: AgentState):
    """
    Observe and analyze the current application UI.
    """

    # --------------------------------------------------
    # 0. Explore mode: per-case boundary handling
    #
    # Every CASE must be independent and self-contained
    # (per the exploratory skill) — but a case can
    # legitimately span more than one action (e.g. fill
    # an invalid value, then click submit).
    #
    # When we detect a case_id change:
    #   1. Run VLM validation on the just-completed case
    #      (the page still shows its result)
    #   2. Then reset the page for the next case
    #
    # No reset is needed for the very first action of
    # a page — main.py / go_to_next_page already opened
    # it fresh.
    # --------------------------------------------------

    case_validations = list(
        state.get("case_validations", [])
    )

    if state.get("task_mode") == "explore":

        current_step = state.get("current_step") or {}
        current_case_id = current_step.get("case_id")
        last_case_id = state.get("last_case_id")

        if (
            current_case_id != last_case_id
            and last_case_id is not None
        ):
            # --------------------------------------------------
            # The previous case just finished. The page still
            # shows its result. Run VLM validation NOW, before
            # we reset the page.
            # --------------------------------------------------

            # Collect actions belonging to the completed case
            case_actions = [
                action for action in state.get(
                    "executed_actions", []
                )
                if action.get("case_id") == last_case_id
            ]

            # Take validation screenshot
            val_screenshot_path = "case_validation_screen.png"
            val_screenshot_result = screenshot(val_screenshot_path)

            val_snapshot_result = snapshot()
            val_snapshot_text = val_snapshot_result.get(
                "output", ""
            ) if val_snapshot_result.get("success") else ""

            if val_screenshot_result.get("success"):
                metrics_logger.log_screenshot(
                    val_screenshot_path
                )

                validation = _validate_case_with_vlm(
                    last_case_id,
                    case_actions,
                    val_snapshot_text,
                    val_screenshot_path
                )

                case_validations.append(validation)

                print(
                    f"\n========== CASE VALIDATION: "
                    f"{last_case_id} =========="
                )
                print(
                    f"Validated: {validation.get('validated')}"
                )
                print(
                    f"Evidence: {validation.get('evidence')}"
                )
                print(
                    "========================================\n"
                )

            # --------------------------------------------------
            # Now reset the page for the new case
            # --------------------------------------------------

            target_url = (
                state.get("current_page_url")
                or state.get("app_path")
            )

            if target_url:
                reopen_result = open_app(target_url)

                if not reopen_result.get("success"):
                    print(
                        "Warning: failed to reset to "
                        f"{target_url} before this case: "
                        f"{reopen_result.get('error')}"
                    )

    # --------------------------------------------------
    # 1. Get structured browser information
    # --------------------------------------------------

    snapshot_result = snapshot()

    if not snapshot_result.get(
        "success"
    ):

        print(
            "Observe: browser snapshot failed."
        )

        print(
            "Snapshot result:",
            snapshot_result
        )

        return {
            "current_screen": None,
            "target_elements": [],
            "case_validations": case_validations
        }

    snapshot_text = snapshot_result.get(
        "output",
        ""
    )

    # --------------------------------------------------
    # 1.1 Validate snapshot content
    # --------------------------------------------------

    if not snapshot_text.strip():

        print(
            "Observe: browser snapshot is empty."
        )

    # --------------------------------------------------
    # 2. Capture current browser screen
    # --------------------------------------------------

    screenshot_path = "current_screen.png"

    screenshot_result = screenshot(
        screenshot_path
    )

    if not screenshot_result.get(
        "success"
    ):

        print(
            "Observe: screenshot failed."
        )

        print(
            "Screenshot result:",
            screenshot_result
        )

        return {
            "current_screen": None,
            "target_elements": [],
            "case_validations": case_validations
        }

    # --------------------------------------------------
    # 2.1 Log screenshot metrics
    # --------------------------------------------------

    metrics_logger.log_screenshot(
        screenshot_path
    )

    # --------------------------------------------------
    # 3. Analyze UI using VLM
    # --------------------------------------------------

    target_elements = analyze_ui_with_vlm(
        task_mode=state.get(
            "task_mode",
            "new_test"
        ),
        current_step=state.get(
            "current_step"
        ),
        existing_script=state.get(
            "existing_script",
            ""
        ),
        snapshot_text=snapshot_text,
        screenshot_path=screenshot_path
    )

    # --------------------------------------------------
    # 4. Keep useful UI information in state
    # --------------------------------------------------

    return {
        "current_screen": screenshot_path,
        "target_elements": target_elements,
        "case_validations": case_validations
    }