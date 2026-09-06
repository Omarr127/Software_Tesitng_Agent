from typing import TypedDict, Literal, Any


class AgentState(TypedDict, total=False):

    # ==================================================
    # Receive + Classify Input
    # ==================================================

    task_mode: Literal[
        "new_test",
        "maintenance",
        "explore"
    ]


    # ==================================================
    # Understand Task
    # ==================================================

    requirement: str | None

    app_path: str | None

    existing_script: str | None

    test_intent: str | None


    # ==================================================
    # Create Plan
    # ==================================================

    plan: list[dict]

    current_step: dict | None


    # ==================================================
    # Scenario 3 (explore) — grouping steps into
    # independent cases, so a case can span more than
    # one browser action (e.g. fill an invalid value,
    # then click submit) without losing track of which
    # actions belong together.
    # ==================================================

    last_case_id: str | None


    # ==================================================
    # Scenario 3 (explore) — single-level, same-domain
    # page crawl
    # ==================================================

    max_pages: int | None

    base_domain: str | None

    current_page_url: str | None

    visited_pages: list[str]

    pages_queue: list[str]

    pages_discovered: bool

    has_next_page: bool


    # ==================================================
    # Scenario 3 (explore) — per-case VLM validation
    # results captured at case boundaries
    # ==================================================

    case_validations: list[dict]


    # ==================================================
    # Observe + Analyze UI
    # ==================================================

    current_screen: Any | None

    target_elements: list[dict]


    # ==================================================
    # Decide Action
    # ==================================================

    next_action: dict | None


    # ==================================================
    # Execute Action
    # ==================================================

    action_result: dict | None


    # Successful actions history
    executed_actions: list[dict]


    # Agent Browser CLI commands history

    browser_commands: list[str]


    # Action Successful?
    action_successful: bool


    # ==================================================
    # Loop Control
    # ==================================================

    # More Steps?
    more_steps: bool


    # Retries Available?
    retries_available: bool

    retry_count: int


    # ==================================================
    # Verify Behavior
    # Scenario 2 / Maintenance only
    # ==================================================

    actual_result: Any | None

    expected_result: Any | None


    # Repair Needed?
    repair_needed: bool

    repair_attempts: int

    repair_retries_available: bool


    # ==================================================
    # Generate Output
    # ==================================================

    generated_output: str | None


    # ==================================================
    # Failure Handling
    # ==================================================

    partial_result: Any | None