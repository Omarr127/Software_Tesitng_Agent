from state import AgentState
from tools.browser_tools import (
    click,
    fill,
    navigate,
    press,
    snapshot
)


def execute_action(state: AgentState):
    """
    Execute the browser action selected by the Decide node.

    Responsibilities:
    - Execute the selected Agent Browser action.
    - Store successful actions.
    - Preserve observed element information,
      including dynamic bounding boxes.
    - Store the real Agent Browser CLI command sequence
      used for each successful action.
    - Tag actions with case_id / page_url for explore mode.
    - Capture post-action page state for explore mode.

    This node does not use an LLM.
    """

    # --------------------------------------------------
    # 1. Get selected action
    # --------------------------------------------------

    action = state.get(
        "next_action",
        {}
    )

    current_step = state.get(
        "current_step"
    ) or {}

    case_id = current_step.get("case_id")

    action_type = action.get(
        "action"
    )

    target = action.get(
        "target"
    )

    value = action.get(
        "value"
    )

    # --------------------------------------------------
    # 2. Execute browser action
    # --------------------------------------------------

    if action_type == "fill":

        result = fill(
            target,
            value
        )

    elif action_type == "click":

        result = click(
            target
        )

    elif action_type == "navigate":

        result = navigate(
            value
        )

    elif action_type == "press":

        result = press(
            value
        )

    else:

        result = {
            "success": False,
            "output": None,
            "error": f"Unsupported action: {action_type}",
            "command": None
        }

    # --------------------------------------------------
    # 3. Check execution result
    # --------------------------------------------------

    success = result.get(
        "success",
        False
    )

    # Keep the exact command sequence returned by the
    # browser tool. For click/fill this is now the real
    # coordinate-based mouse/clipboard sequence.
    # For press, this is the real Agent Browser key command.
    command = result.get(
        "command"
    )

    # --------------------------------------------------
    # 4. Get previous executed actions
    # --------------------------------------------------

    executed_actions = state.get(
        "executed_actions",
        []
    ).copy()

    # --------------------------------------------------
    # 5. Store successful action
    # --------------------------------------------------

    if success:

        executed_action = action.copy()

        # --------------------------------------------------
        # Store the REAL command sequence that was executed.
        #
        # Example for fill:
        #
        # agent-browser mouse move 631 218
        # agent-browser mouse down left
        # agent-browser mouse up left
        # agent-browser press Control+a
        # agent-browser clipboard write "Aya"
        # agent-browser clipboard paste
        #
        # Example for press:
        #
        # agent-browser press Enter
        #
        # The element ref may remain in target internally,
        # but generate.py can now output this command instead
        # of rebuilding a static ref-based command.
        # --------------------------------------------------

        executed_action["command"] = command

        # --------------------------------------------------
        # Tag the executed action with which case/page it
        # belongs to, so generate() can group Scenario 3's
        # report by page and by case without having to
        # re-derive that from free-text goals.
        # --------------------------------------------------

        executed_action["case_id"] = case_id
        executed_action["page_url"] = (
            state.get("current_page_url")
            or state.get("app_path")
        )

        # --------------------------------------------------
        # Attach the observed element.
        #
        # This preserves:
        #
        # label
        # type
        # ref
        # box
        #
        # The ref/box remain useful as INTERNAL evidence
        # and debugging information. They are not used as
        # the final generated click/fill commands.
        # --------------------------------------------------

        if action_type in (
            "fill",
            "click"
        ):

            for element in state.get(
                "target_elements",
                []
            ):

                if not isinstance(
                    element,
                    dict
                ):
                    continue

                if element.get(
                    "ref"
                ) == target:

                    executed_action[
                        "element"
                    ] = element

                    break

        # --------------------------------------------------
        # Capture the resulting page state as evidence.
        # Without this, later steps (like generate) only
        # know that the action ran, not what actually
        # happened after it — which makes it impossible
        # to judge outcomes like "was a validation error
        # shown?" without guessing.
        # --------------------------------------------------

        post_action_snapshot = snapshot()

        if post_action_snapshot.get("success"):
            executed_action["resulting_state"] = (
                post_action_snapshot.get("output", "")
            )
        else:
            executed_action["resulting_state"] = None

        executed_actions.append(
            executed_action
        )

    # --------------------------------------------------
    # 6. Store Agent Browser commands
    # --------------------------------------------------

    browser_commands = state.get(
        "browser_commands",
        []
    ).copy()

    if success and command:

        browser_commands.append(
            command
        )

    # --------------------------------------------------
    # 7. Update state
    # --------------------------------------------------

    return {

        "action_result": result,

        "action_successful": success,

        "retry_count": (
            0
            if success
            else state.get(
                "retry_count",
                0
            )
        ),

        "executed_actions": executed_actions,

        "browser_commands": browser_commands,

        # Record which case this attempt belonged to
        # (win or fail) so observe_ui knows whether
        # the *next* step is a continuation of the same
        # case (no reset) or the start of a new one
        # (reset). Set unconditionally, not just on
        # success, so a retry of a failed action within
        # the same case is still recognized as "same
        # case" and doesn't get reset mid-retry.
        "last_case_id": case_id

    }
