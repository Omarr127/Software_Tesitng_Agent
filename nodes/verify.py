import json

from state import AgentState
from tools.browser_tools import snapshot, screenshot
from skills.skill_loader import load_context_for_node
from model import invoke_vlm
from prompts.verify_prompt import build_verify_prompt
from utils.json_utils import clean_json_response
from metrics.tracker import metrics_logger


def verify_behavior(state: AgentState):
    """
    Verify the final behavior of the updated application
    against the expected behavior of the existing test script.

    This node is used by Scenario 2 (maintenance).

    Only verification-specific skill context is loaded.
    """

    # --------------------------------------------------
    # 1. Get a fresh browser snapshot
    # --------------------------------------------------

    snapshot_result = snapshot()

    if not snapshot_result.get("success"):

        return {
            "actual_result": (
                "Unable to inspect final application state."
            ),
            "expected_result": None,
            "repair_needed": True
        }

    snapshot_text = snapshot_result.get(
        "output",
        ""
    )

    # --------------------------------------------------
    # 2. Capture a fresh final screenshot
    # --------------------------------------------------

    screenshot_path = "verify_screen.png"

    screenshot_result = screenshot(
        screenshot_path
    )

    if not screenshot_result.get("success"):

        return {
            "actual_result": (
                "Unable to capture final application screen."
            ),
            "expected_result": None,
            "repair_needed": True
        }

    # --------------------------------------------------
    # 3. Log screenshot metrics
    # --------------------------------------------------

    metrics_logger.log_screenshot(
        screenshot_path
    )

    # --------------------------------------------------
    # 4. Get task mode
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "maintenance"
    )

    # --------------------------------------------------
    # 5. Load only Verify-specific context
    # --------------------------------------------------

    context = load_context_for_node(
        task_mode,
        "verify"
    )

    # --------------------------------------------------
    # 6. Build verification prompt
    # --------------------------------------------------

    prompt = build_verify_prompt(
        context=context,
        test_intent=state.get(
            "test_intent",
            ""
        ),
        existing_script=state.get(
            "existing_script",
            ""
        ),
        snapshot_text=snapshot_text
    )

    # --------------------------------------------------
    # 7. Send prompt + final screenshot to Gemini VLM
    # --------------------------------------------------

    try:

        response = invoke_vlm(
            prompt,
            screenshot_path
        )

    except Exception as e:

        print(
            f"Verify VLM request failed: {e}"
        )

        return {
            "current_screen": screenshot_path,
            "actual_result": (
                "Verification model request failed."
            ),
            "expected_result": None,
            "repair_needed": True
        }

    # --------------------------------------------------
    # 8. Clean Gemini response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 9. Parse verification response
    # --------------------------------------------------

    try:

        verification = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "Verify node returned invalid JSON:"
        )

        print(response)

        return {
            "current_screen": screenshot_path,
            "actual_result": response.strip(),
            "expected_result": None,
            "repair_needed": True
        }

    # --------------------------------------------------
    # 10. Validate response structure
    # --------------------------------------------------

    if not isinstance(
        verification,
        dict
    ):

        return {
            "current_screen": screenshot_path,
            "actual_result": None,
            "expected_result": None,
            "repair_needed": True
        }

    # --------------------------------------------------
    # 11. Extract verification results
    # --------------------------------------------------

    expected_result = verification.get(
        "expected_result"
    )

    actual_result = verification.get(
        "actual_result"
    )

    repair_needed = verification.get(
        "repair_needed",
        True
    )

    # --------------------------------------------------
    # 12. Validate expected result
    # --------------------------------------------------

    if not isinstance(
        expected_result,
        str
    ):

        expected_result = None

    elif not expected_result.strip():

        expected_result = None

    # --------------------------------------------------
    # 13. Validate actual result
    # --------------------------------------------------

    if not isinstance(
        actual_result,
        str
    ):

        actual_result = None

    elif not actual_result.strip():

        actual_result = None

    # --------------------------------------------------
    # 14. Validate repair flag
    # --------------------------------------------------

    if not isinstance(
        repair_needed,
        bool
    ):

        repair_needed = True

    # --------------------------------------------------
    # 15. Missing verification evidence
    # --------------------------------------------------

    if (
        expected_result is None
        or actual_result is None
    ):

        repair_needed = True

    # --------------------------------------------------
    # 16. Update LangGraph state
    # --------------------------------------------------

    return {
        "current_screen": screenshot_path,
        "expected_result": expected_result,
        "actual_result": actual_result,
        "repair_needed": repair_needed
    }