from state import AgentState


def receive_classify(state: AgentState):
    """
    Identify whether the task is:
    - new_test
    - maintenance
    """

    if state.get("existing_script"):
        task_mode = "maintenance"
    else:
        task_mode = "new_test"

    return {
        "task_mode": task_mode
    }