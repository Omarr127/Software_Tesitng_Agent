from state import AgentState


def receive_classify(state: AgentState):
    """
    Identify whether the task is:
<<<<<<< HEAD
    - new_test      (a requirement was given)
    - maintenance   (an existing script was given)
    - explore       (neither was given — Scenario 3)
=======
    - new_test
    - maintenance
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    """

    if state.get("existing_script"):
        task_mode = "maintenance"
<<<<<<< HEAD
    elif state.get("requirement"):
        task_mode = "new_test"
    else:
        task_mode = "explore"
=======
    else:
        task_mode = "new_test"
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

    return {
        "task_mode": task_mode
    }