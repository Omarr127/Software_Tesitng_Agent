from state import AgentState


def receive_classify(state: AgentState):
    """
    Identify whether the task is:
    - new_test      (a requirement was given)
    - maintenance   (an existing script was given)
    - explore       (neither was given — Scenario 3)
    """

    if state.get("existing_script"):
        task_mode = "maintenance"
    elif state.get("requirement"):
        task_mode = "new_test"
    else:
        task_mode = "explore"

    return {
        "task_mode": task_mode
    }