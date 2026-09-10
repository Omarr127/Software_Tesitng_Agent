import time

from langgraph.graph import StateGraph, START, END

from state import AgentState

from nodes.receive import receive_classify
from nodes.understand import understand_task
from nodes.plan import create_plan
from nodes.observe import observe_ui
from nodes.decide import decide_action
from nodes.execute import execute_action
from nodes.reflect import reflect_replan
from nodes.verify import verify_behavior
from nodes.generate import generate_output
<<<<<<< HEAD
from nodes.pages import discover_pages, go_to_next_page

from nodes.routing import (
    route_needs_plan,
=======

from nodes.routing import (
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    route_action_success,
    route_more_steps,
    route_retry,
    route_task_mode,
<<<<<<< HEAD
    route_has_next_page,
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    route_repair
)

from metrics.tracker import metrics_logger


def timed_node(node_name, node_function):
    """
    Measure execution time for a node.
    """

    def wrapper(state):
        start_time = time.time()

        result = node_function(state)

        duration = time.time() - start_time

        metrics_logger.log_node_time(
            node_name,
            duration
        )

        return result

    return wrapper


def check_more_steps(state: AgentState):
    """
    Move to the next step in the plan if one exists.
    """

    plan = state.get("plan", [])
    current_step = state.get("current_step")

    if not plan or current_step is None:
        return {
            "more_steps": False
        }

    try:
        current_index = plan.index(current_step)

    except ValueError:
        return {
            "more_steps": False
        }

    next_index = current_index + 1

    if next_index < len(plan):
        return {
            "current_step": plan[next_index],
            "more_steps": True
        }

    return {
        "more_steps": False
    }


def check_retries(state: AgentState):
    """
    Allow a limited number of recovery attempts.
    """

    MAX_RETRIES = 2

    retry_count = state.get("retry_count", 0)

    if retry_count < MAX_RETRIES:
        return {
            "retry_count": retry_count + 1,
            "retries_available": True
        }

    return {
        "retries_available": False
    }


def check_task_mode(state: AgentState):
    """
    Pass state to the task-mode routing decision.
    """

    return {}


def fail_node(state: AgentState):
    """
    Preserve useful information when the task cannot continue.
    """

    return {
        "partial_result": {
            "plan": state.get("plan"),
            "current_step": state.get("current_step"),
            "action_result": state.get("action_result")
        }
    }


def build_graph():

    # Create LangGraph using our AgentState
    builder = StateGraph(AgentState)

    # --------------------------------------------------
    # Add Nodes
    # --------------------------------------------------

    builder.add_node(
        "receive",
        timed_node(
            "receive",
            receive_classify
        )
    )

    builder.add_node(
        "understand",
        timed_node(
            "understand",
            understand_task
        )
    )

    builder.add_node(
<<<<<<< HEAD
        "observe",
        timed_node(
            "observe",
            observe_ui
        )
    )

    builder.add_node(
        "discover_pages",
        timed_node(
            "discover_pages",
            discover_pages
        )
    )

    builder.add_node(
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        "plan",
        timed_node(
            "plan",
            create_plan
        )
    )

    builder.add_node(
<<<<<<< HEAD
=======
        "observe",
        timed_node(
            "observe",
            observe_ui
        )
    )

    builder.add_node(
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        "decide",
        timed_node(
            "decide",
            decide_action
        )
    )

    builder.add_node(
        "execute",
        timed_node(
            "execute",
            execute_action
        )
    )

    builder.add_node(
        "check_more_steps",
        timed_node(
            "check_more_steps",
            check_more_steps
        )
    )

    builder.add_node(
        "check_retries",
        timed_node(
            "check_retries",
            check_retries
        )
    )

    builder.add_node(
        "check_task_mode",
        timed_node(
            "check_task_mode",
            check_task_mode
        )
    )

    builder.add_node(
        "reflect",
        timed_node(
            "reflect",
            reflect_replan
        )
    )

    builder.add_node(
        "verify",
        timed_node(
            "verify",
            verify_behavior
        )
    )

    builder.add_node(
<<<<<<< HEAD
        "next_page",
        timed_node(
            "next_page",
            go_to_next_page
        )
    )

    builder.add_node(
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        "generate",
        timed_node(
            "generate",
            generate_output
        )
    )

    builder.add_node(
        "fail",
        timed_node(
            "fail",
            fail_node
        )
    )

    # --------------------------------------------------
    # Normal Flow
<<<<<<< HEAD
    #
    # KEY CHANGE: observe runs BEFORE plan.
    #
    # The old ordering was:
    #   understand → plan → observe → decide → ...
    #
    # The new ordering is:
    #   understand → observe → discover_pages →
    #       [route_needs_plan] → plan or decide → ...
    #
    # This ensures:
    # 1. plan can see the observed elements (critical
    #    for explore, also useful for S1/S2).
    # 2. plan only fires ONCE per page — on later loop
    #    iterations (check_more_steps → continue), we
    #    go observe → route_needs_plan → decide directly,
    #    instead of re-generating the entire plan every
    #    iteration.
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    # --------------------------------------------------

    builder.add_edge(
        START,
        "receive"
    )

    builder.add_edge(
        "receive",
        "understand"
    )

<<<<<<< HEAD
    # understand → observe (observe BEFORE plan)
    builder.add_edge(
        "understand",
        "observe"
    )

    # observe → discover_pages
    builder.add_edge(
        "observe",
        "discover_pages"
    )

    # --------------------------------------------------
    # Route: needs_plan or has_plan?
    #
    # First time on this page: plan is empty → needs_plan
    # Subsequent loop iterations: plan exists → has_plan
    # --------------------------------------------------

    builder.add_conditional_edges(
        "discover_pages",
        route_needs_plan,
        {
            "needs_plan": "plan",
            "has_plan": "decide"
        }
    )

    # plan → decide
    builder.add_edge(
        "plan",
=======
    builder.add_edge(
        "understand",
        "plan"
    )

    builder.add_edge(
        "plan",
        "observe"
    )

    builder.add_edge(
        "observe",
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        "decide"
    )

    builder.add_edge(
        "decide",
        "execute"
    )

    # --------------------------------------------------
    # Action Successful?
    # --------------------------------------------------

    builder.add_conditional_edges(
        "execute",
        route_action_success,
        {
            "success": "check_more_steps",
            "failure": "check_retries"
        }
    )

    # --------------------------------------------------
    # More Steps?
<<<<<<< HEAD
    #
    # "continue" goes back to observe (which now runs
    # BEFORE plan), then route_needs_plan skips plan
    # since a plan already exists.
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    # --------------------------------------------------

    builder.add_conditional_edges(
        "check_more_steps",
        route_more_steps,
        {
            "continue": "observe",
            "finished": "check_task_mode"
        }
    )

    # --------------------------------------------------
    # Task Mode?
<<<<<<< HEAD
    #
    # new_test → generate
    # maintenance → verify
    # explore_next_page → next_page (crawl more pages)
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    # --------------------------------------------------

    builder.add_conditional_edges(
        "check_task_mode",
        route_task_mode,
        {
            "new_test": "generate",
<<<<<<< HEAD
            "maintenance": "verify",
            "explore_next_page": "next_page"
        }
    )

    # --------------------------------------------------
    # Explore: next page navigation
    # --------------------------------------------------

    builder.add_conditional_edges(
        "next_page",
        route_has_next_page,
        {
            "continue": "observe",
            "generate": "generate"
=======
            "maintenance": "verify"
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        }
    )

    # --------------------------------------------------
    # Retries Available?
    # --------------------------------------------------

    builder.add_conditional_edges(
        "check_retries",
        route_retry,
        {
            "retry": "reflect",
            "fail": "fail"
        }
    )

    # --------------------------------------------------
    # Verify Behavior / Repair Needed?
    # --------------------------------------------------

    builder.add_conditional_edges(
        "verify",
        route_repair,
        {
            "repair": "reflect",
            "complete": "generate"
        }
    )

    # --------------------------------------------------
    # Reflect → Observe
    # --------------------------------------------------

    builder.add_edge(
        "reflect",
        "observe"
    )

    # --------------------------------------------------
    # End Paths
    # --------------------------------------------------

    builder.add_edge(
        "generate",
        END
    )

    builder.add_edge(
        "fail",
        END
    )

    # --------------------------------------------------
    # Compile Graph
    # --------------------------------------------------

    agent = builder.compile()

    # --------------------------------------------------
    # Save Graph Design as PNG
    # --------------------------------------------------

<<<<<<< HEAD
    try:
        with open("plannergraph.png", "wb") as f:
            f.write(
                agent.get_graph(
                    xray=True
                ).draw_mermaid_png()
            )
    except Exception:
        # PNG rendering may fail in environments without
        # graphviz / mermaid — not critical for the run.
        pass

    return agent


=======
    with open("plannergraph.png", "wb") as f:
        f.write(
            agent.get_graph(
                xray=True
            ).draw_mermaid_png()
        )

    return agent
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
if __name__ == "__main__":
    print("Building LangGraph...")

    graph = build_graph()

    print("Graph built successfully.")
<<<<<<< HEAD
    print("Graph image saved as plannergraph.png")
=======
    print("Graph image saved as plannergraph.png")
    
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
