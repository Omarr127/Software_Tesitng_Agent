import json

from state import AgentState

from tools.browser_tools import (
    snapshot,
    screenshot
)

from model import invoke_vlm

from utils.json_utils import clean_json_response

from metrics.tracker import metrics_logger

from memory import memory_store


def _validate_final_result(
    state: AgentState
):
    """
    Perform final visual validation for Scenario 1.

    The validation happens only after the complete
    browser interaction flow has finished.

    It uses:
        1. Agent Browser snapshot
        2. Agent Browser screenshot
        3. Existing VLM function

    No separate LangGraph node is required.

    Returns:
        {
            "validated": bool,
            "evidence": str,
            "snapshot_command": str,
            "screenshot_command": str
        }
    """

    # --------------------------------------------------
    # 1. Get expected testing intent
    # --------------------------------------------------

    test_intent = state.get(
        "test_intent",
        ""
    )

    requirement = state.get(
        "requirement",
        ""
    )

    # --------------------------------------------------
    # 2. Get final browser snapshot
    # --------------------------------------------------

    snapshot_result = snapshot()

    snapshot_command = snapshot_result.get(
        "command"
    )

    if not snapshot_result.get(
        "success"
    ):

        print(
            "Validation: final browser snapshot failed."
        )

        return {
            "validated": False,
            "evidence": (
                "Unable to inspect the final browser state."
            ),
            "snapshot_command": snapshot_command,
            "screenshot_command": None
        }

    snapshot_text = snapshot_result.get(
        "output",
        ""
    )

    # --------------------------------------------------
    # 3. Capture final screenshot
    # --------------------------------------------------

    screenshot_path = "validation_screen.png"

    screenshot_result = screenshot(
        screenshot_path
    )

    screenshot_command = screenshot_result.get(
        "command"
    )

    if not screenshot_result.get(
        "success"
    ):

        print(
            "Validation: final screenshot failed."
        )

        return {
            "validated": False,
            "evidence": (
                "Unable to capture the final application screen."
            ),
            "snapshot_command": snapshot_command,
            "screenshot_command": screenshot_command
        }

    # --------------------------------------------------
    # 4. Record screenshot metrics
    # --------------------------------------------------

    metrics_logger.log_screenshot(
        screenshot_path
    )

    # --------------------------------------------------
    # 5. Build compact validation prompt
    #
    # No separate prompt file is required.
    # --------------------------------------------------

    validation_prompt = f"""
You are validating the final result of a browser test.

Requirement:
{requirement}

Testing intent:
{test_intent}

Final browser snapshot:
{snapshot_text}

Look at the screenshot together with the browser snapshot.

Determine whether there is reliable visible or textual evidence
that the requested action was successfully completed.

For example, evidence may include:
- a success message
- a success alert
- a confirmation message
- a successful completion screen
- a page that clearly indicates the requested operation succeeded

Do NOT assume success merely because the button was clicked.

Do NOT treat the absence of an error as proof of success.

Return JSON only:

{{
    "validated": true,
    "evidence": "short description of the observed success evidence"
}}

or:

{{
    "validated": false,
    "evidence": "short description of why success was not established"
}}
"""

    # --------------------------------------------------
    # 6. Ask existing VLM to visually validate
    # --------------------------------------------------

    try:

        response = invoke_vlm(
            validation_prompt,
            screenshot_path
        )

    except Exception as e:

        print(
            f"Validation VLM request failed: {e}"
        )

        return {
            "validated": False,
            "evidence": (
                "Validation model request failed."
            ),
            "snapshot_command": snapshot_command,
            "screenshot_command": screenshot_command
        }

    # --------------------------------------------------
    # 7. Clean VLM response
    # --------------------------------------------------

    response = clean_json_response(
        response
    )

    # --------------------------------------------------
    # 8. Parse validation response
    # --------------------------------------------------

    try:

        validation = json.loads(
            response
        )

    except json.JSONDecodeError:

        print(
            "Validation VLM returned invalid JSON:"
        )

        print(
            response
        )

        return {
            "validated": False,
            "evidence": (
                "Validation model returned invalid JSON."
            ),
            "snapshot_command": snapshot_command,
            "screenshot_command": screenshot_command
        }

    # --------------------------------------------------
    # 9. Validate response structure
    # --------------------------------------------------

    if not isinstance(
        validation,
        dict
    ):

        return {
            "validated": False,
            "evidence": (
                "Validation model returned an invalid structure."
            ),
            "snapshot_command": snapshot_command,
            "screenshot_command": screenshot_command
        }

    # --------------------------------------------------
    # 10. Extract validation result
    # --------------------------------------------------

    validated = validation.get(
        "validated",
        False
    )

    evidence = validation.get(
        "evidence",
        ""
    )

    # --------------------------------------------------
    # 11. Validate returned values
    # --------------------------------------------------

    if not isinstance(
        validated,
        bool
    ):

        validated = False

    if not isinstance(
        evidence,
        str
    ):

        evidence = ""

    evidence = evidence.strip()

    if not evidence:

        evidence = (
            "No reliable validation evidence was provided."
        )

    # --------------------------------------------------
    # 12. Print validation result
    # --------------------------------------------------

    print(
        "\n========== FINAL VALIDATION =========="
    )

    print(
        "Validated:",
        validated
    )

    print(
        "Evidence:",
        evidence
    )

    print(
        "======================================\n"
    )

    return {
        "validated": validated,
        "evidence": evidence,
        "snapshot_command": snapshot_command,
        "screenshot_command": screenshot_command
    }


def generate_output(state: AgentState):
    """
    Generate the final Agent Browser CLI output.

    This node normally does not use an LLM.

    For Scenario 1, however, it performs one final
    visual validation after all browser actions have
    completed.

    The validation checks the final application state
    using:

        snapshot()
        screenshot()
        existing VLM

    The generated output remains based on actual
    Agent Browser commands executed during the test.
    """

    # --------------------------------------------------
    # 1. Get executed Agent Browser commands
    # --------------------------------------------------

    browser_commands = state.get(
        "browser_commands",
        []
    ).copy()

    # --------------------------------------------------
    # 2. Determine task mode
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    # --------------------------------------------------
    # 2.1 Explore mode: per-case report with VLM validation
    #
    # In explore mode, each case has already been VLM-validated
    # at its case boundary (in observe_ui). The only exception
    # is the LAST case — there is no subsequent case_id change
    # after it, so we validate it here before building the
    # final report.
    # --------------------------------------------------

    if task_mode == "explore":

        from nodes.observe import _validate_case_with_vlm

        case_validations = list(
            state.get("case_validations", [])
        )

        # --------------------------------------------------
        # Validate the LAST case (not yet validated by observe)
        # --------------------------------------------------

        last_case_id = state.get("last_case_id")
        validated_ids = {
            v.get("case_id") for v in case_validations
        }

        if (
            last_case_id
            and last_case_id not in validated_ids
        ):
            last_case_actions = [
                action for action in state.get(
                    "executed_actions", []
                )
                if action.get("case_id") == last_case_id
            ]

            if last_case_actions:
                # Page still shows the last case's result
                val_screenshot_path = "final_case_validation.png"
                val_screenshot_result = screenshot(
                    val_screenshot_path
                )

                val_snapshot_result = snapshot()
                val_snapshot_text = (
                    val_snapshot_result.get("output", "")
                    if val_snapshot_result.get("success")
                    else ""
                )

                if val_screenshot_result.get("success"):
                    metrics_logger.log_screenshot(
                        val_screenshot_path
                    )

                    final_validation = _validate_case_with_vlm(
                        last_case_id,
                        last_case_actions,
                        val_snapshot_text,
                        val_screenshot_path
                    )

                    case_validations.append(
                        final_validation
                    )

                    print(
                        f"\n========== FINAL CASE VALIDATION: "
                        f"{last_case_id} =========="
                    )
                    print(
                        f"Validated: "
                        f"{final_validation.get('validated')}"
                    )
                    print(
                        f"Evidence: "
                        f"{final_validation.get('evidence')}"
                    )
                    print(
                        "==========================================\n"
                    )

        # --------------------------------------------------
        # Build the explore report grouped by page and case
        # --------------------------------------------------

        executed_actions = state.get(
            "executed_actions", []
        )

        visited_pages = state.get(
            "visited_pages", []
        ) or [state.get("app_path", "")]

        # Index validations by case_id for quick lookup
        validation_by_case = {
            v.get("case_id"): v
            for v in case_validations
        }

        # Group executed actions by case_id, preserving order
        from collections import OrderedDict
        cases_ordered = OrderedDict()
        for action in executed_actions:
            cid = action.get("case_id") or "unknown"
            cases_ordered.setdefault(cid, []).append(action)

        output = []
        output.append(
            "=== Exploratory Test Report ===\n"
        )

        # Group cases by page for multi-page reports
        cases_by_page = OrderedDict()
        for cid, actions in cases_ordered.items():
            page = actions[0].get(
                "page_url", ""
            ) if actions else ""
            cases_by_page.setdefault(
                page, OrderedDict()
            )[cid] = actions

        multi_page = len(cases_by_page) > 1

        memory_cases_by_page = {}

        for page_url, page_cases in cases_by_page.items():

            if multi_page:
                output.append(
                    f"# Page: {page_url}\n"
                )

            for cid, actions in page_cases.items():

                # Build command lines for this case from the
                # EXACT commands that execute.py stored after
                # successful execution.
                #
                # Important:
                # - fill/click refs remain internal to the agent.
                # - The final report uses the physical commands
                #   returned by browser_tools.py instead:
                #
                #   agent-browser mouse move x y
                #   agent-browser mouse down left
                #   agent-browser mouse up left
                #   agent-browser press Control+a
                #   agent-browser clipboard write "value"
                #   agent-browser clipboard paste
                #
                # This prevents Scenario 3 from rebuilding old
                # static commands such as:
                #
                #   agent-browser fill @e2 "value"
                #   agent-browser click @e5
                # --------------------------------------------------

                for action in actions:

                    command = action.get(
                        "command"
                    )

                    if command:
                        output.append(
                            command
                        )

                # Determine verdict from VLM validation
                val = validation_by_case.get(cid)

                if val:
                    validated = val.get("validated", False)
                    evidence = val.get(
                        "evidence",
                        "No evidence."
                    )

                    if validated:
                        verdict = "HANDLED"
                    else:
                        verdict = "BUG FOUND"
                else:
                    verdict = "INCONCLUSIVE"
                    evidence = "No VLM validation available."

                # Case goal from the first action
                case_goal = ""
                for action in actions:
                    goal = action.get("goal", "")
                    if goal:
                        case_goal = goal
                        break

                case_name = case_goal or cid

                output.append(
                    f"# Case: {case_name} - {verdict} - "
                    f"{evidence}"
                )
                output.append("")

                # Collect for memory write-back
                memory_cases_by_page.setdefault(
                    page_url, []
                ).append({
                    "name": case_name,
                    "verdict": verdict,
                    "reason": evidence
                })

        # --------------------------------------------------
        # Write verdicts to memory for cross-run learning
        # --------------------------------------------------

        app_path = state.get("app_path")

        if app_path:
            try:
                for page_url, cases in (
                    memory_cases_by_page.items()
                ):
                    memory_store.record_page_cases(
                        app_path,
                        page_url,
                        cases
                    )
            except Exception as e:
                print(
                    "Warning: could not update "
                    f"exploration memory: {e}"
                )

        return {
            "generated_output": "\n".join(output)
        }

    # --------------------------------------------------
    # 3. Final validation
    #
    # Scenario 1:
    #
    # The complete functional flow has finished.
    # Now visually check whether the requested
    # operation actually succeeded.
    #
    # Scenario 2:
    #
    # The Verify node already performs validation,
    # so do not validate a second time here.
    # --------------------------------------------------

    validation = {
        "validated": True,
        "evidence": ""
    }

    if (
        task_mode == "new_test"
        and state.get(
            "action_successful",
            False
        )
        and not state.get(
            "more_steps",
            False
        )
        and state.get(
            "partial_result"
        ) is None
    ):

        validation = _validate_final_result(
            state
        )

        # --------------------------------------------------
        # Add validation commands to final command history
        #
        # These are real Agent Browser commands returned
        # by the browser tools.
        # --------------------------------------------------

        snapshot_command = validation.get(
            "snapshot_command"
        )

        screenshot_command = validation.get(
            "screenshot_command"
        )

        if (
            snapshot_command
            and snapshot_command
            not in browser_commands
        ):

            browser_commands.append(
                snapshot_command
            )

        if (
            screenshot_command
            and screenshot_command
            not in browser_commands
        ):

            browser_commands.append(
                screenshot_command
            )

    # --------------------------------------------------
    # 4. Build final CLI output
    # --------------------------------------------------

    output = []

    output.append(
        "=== Agent Browser CLI Output ===\n"
    )

    if browser_commands:

        for command in browser_commands:

            output.append(
                command
            )

            output.append(
                ""
            )

    else:

        output.append(
            "No browser commands were executed."
        )

    # --------------------------------------------------
    # 5. Add test result
    # --------------------------------------------------

    output.append(
        "\n=== Test Result ===\n"
    )

    # --------------------------------------------------
    # Determine final execution result
    # --------------------------------------------------

    action_successful = state.get(
        "action_successful",
        False
    )

    more_steps = state.get(
        "more_steps",
        False
    )

    partial_result = state.get(
        "partial_result"
    )

    # --------------------------------------------------
    # Scenario 1 result
    #
    # Functional execution AND final validation
    # must both succeed.
    # --------------------------------------------------

    if task_mode == "new_test":

        test_passed = (
            action_successful
            and not more_steps
            and partial_result is None
            and validation.get(
                "validated",
                False
            )
        )

    # --------------------------------------------------
    # Scenario 2 result
    #
    # Verify node already determined whether the
    # expected behavior was achieved.
    # --------------------------------------------------

    else:

        test_passed = (
            action_successful
            and not more_steps
            and partial_result is None
            and not state.get(
                "repair_needed",
                False
            )
        )

    # --------------------------------------------------
    # 6. Generate PASS / FAIL
    # --------------------------------------------------

    if test_passed:

        output.append(
            "PASS\n"
        )

        output.append(
            "The testing flow was completed successfully."
        )

        # Show evidence only internally in console,
        # not as a replacement for Agent Browser output.

        if (
            task_mode == "new_test"
            and validation.get(
                "evidence"
            )
        ):

            print(
                "\nValidation evidence:"
            )

            print(
                validation.get(
                    "evidence"
                )
            )

    else:

        output.append(
            "FAIL\n"
        )

        output.append(
            "The testing flow could not be completed."
        )

        if (
            task_mode == "new_test"
            and validation.get(
                "evidence"
            )
        ):

            print(
                "\nValidation evidence:"
            )

            print(
                validation.get(
                    "evidence"
                )
            )

    # --------------------------------------------------
    # 7. Store final output
    # --------------------------------------------------

    return {
        "generated_output": "\n".join(
            output
        ),

        # Keep browser command history updated
        # with the final validation commands.
        "browser_commands": browser_commands
    }