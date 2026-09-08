import re
import subprocess
import sys
from pathlib import Path

import streamlit as st


# --------------------------------------------------
# Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_ROOT / "main.py"


# --------------------------------------------------
# Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="Software Testing Agent",
    page_icon="🧪",
    layout="wide"
)


# --------------------------------------------------
# Scenario names
# --------------------------------------------------

AUTO_MODE = "Auto-detect"
NEW_TEST_MODE = "New Functional Test"
MAINTENANCE_MODE = "Maintain Existing Test"
EXPLORE_MODE = "Exploratory Testing"


# --------------------------------------------------
# Intent detection
# --------------------------------------------------

_EXPLORE_PATTERNS = (
    r"\bexplore\b",
    r"\bexploratory\b",
    r"\bfind bugs?\b",
    r"\bdiscover bugs?\b",
    r"\bedge cases?\b",
    r"\btest the app\b",
    r"\btest this app\b",
    r"\blook for bugs?\b",
    r"\bprobe\b"
)

_MAINTENANCE_PATTERNS = (
    r"\bmaintain\b",
    r"\bmaintenance\b",
    r"\bself[- ]?heal\b",
    r"\brepair\b",
    r"\bfix (?:this|the|my) (?:old )?test\b",
    r"\bold test\b",
    r"\bexisting test\b",
    r"\bui changed\b",
    r"\bcoordinates? changed\b"
)


def detect_mode(
    user_request,
    existing_script
):
    """
    Detect which working backend scenario should run.

    Priority:
    1. Existing Agent Browser script -> Maintenance.
    2. Explicit maintenance intent -> Maintenance.
    3. Explicit exploratory intent -> Exploratory Testing.
    4. Empty request -> Exploratory Testing.
    5. Otherwise -> New Functional Test.
    """

    request = str(
        user_request or ""
    ).strip()

    script = str(
        existing_script or ""
    ).strip()

    if script:
        return MAINTENANCE_MODE

    lowered = request.lower()

    if any(
        re.search(
            pattern,
            lowered
        )
        for pattern in _MAINTENANCE_PATTERNS
    ):
        return MAINTENANCE_MODE

    if not request:
        return EXPLORE_MODE

    if any(
        re.search(
            pattern,
            lowered
        )
        for pattern in _EXPLORE_PATTERNS
    ):
        return EXPLORE_MODE

    return NEW_TEST_MODE


def resolve_mode(
    selected_mode,
    user_request,
    existing_script
):
    """
    Auto-detect by default, but allow an advanced user
    to explicitly override the routing.
    """

    if selected_mode != AUTO_MODE:
        return selected_mode

    return detect_mode(
        user_request,
        existing_script
    )


# --------------------------------------------------
# CLI command construction
# --------------------------------------------------

def build_command(
    resolved_mode,
    app_path,
    user_request="",
    existing_script=""
):
    """
    Build the same CLI commands that already work from CMD.

    Arguments are passed as a Python list and executed with
    shell=False, which avoids Windows command-line quoting issues.
    """

    if resolved_mode == NEW_TEST_MODE:

        return [
            sys.executable,
            str(MAIN_FILE),
            "--requirement",
            user_request,
            "--app_path",
            app_path
        ]

    if resolved_mode == MAINTENANCE_MODE:

        return [
            sys.executable,
            str(MAIN_FILE),
            "--existing_script",
            existing_script,
            "--app_path",
            app_path
        ]

    return [
        sys.executable,
        str(MAIN_FILE),
        "--app_path",
        app_path
    ]


# --------------------------------------------------
# Output parsing
# --------------------------------------------------

def extract_generated_output(
    log_text
):
    """
    Extract the final generated test/report section
    from the complete console output.
    """

    marker = (
        "=== Generated Test Script ==="
    )

    if marker not in log_text:
        return ""

    return log_text.split(
        marker,
        1
    )[1].strip()


def extract_metrics(
    log_text
):
    """
    Extract top-level run metrics from the first metrics report.
    """

    metrics = {}

    patterns = {
        "Run Time": (
            r"Total Run Time\s*:\s*([^\r\n]+)"
        ),
        "Prompt Tokens": (
            r"Prompt Tokens\s*:\s*(\d+)"
        ),
        "Output Tokens": (
            r"Output Tokens\s*:\s*(\d+)"
        ),
        "Total Tokens": (
            r"Total Tokens\s*:\s*(\d+)"
        ),
        "Screenshots": (
            r"Screenshots Count\s*:\s*(\d+)"
        )
    }

    metrics_section = log_text

    marker = (
        "==================== METRICS REPORT ===================="
    )

    if marker in log_text:

        metrics_section = log_text.split(
            marker,
            1
        )[1]

        next_marker = (
            "==================== NODE MODEL METRICS ===================="
        )

        if next_marker in metrics_section:

            metrics_section = (
                metrics_section.split(
                    next_marker,
                    1
                )[0]
            )

    for name, pattern in patterns.items():

        match = re.search(
            pattern,
            metrics_section
        )

        if match:
            metrics[name] = (
                match.group(1).strip()
            )

    return metrics


# --------------------------------------------------
# Agent execution
# --------------------------------------------------

def run_agent(
    command
):
    """
    Run the existing agent and stream its stdout/stderr
    into the Streamlit interface.

    Streamlit does not replace the agent. It simply launches
    the already-working main.py command.
    """

    log_placeholder = st.empty()
    logs = []

    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        shell=False
    )

    if process.stdout is not None:

        for line in iter(
            process.stdout.readline,
            ""
        ):

            if not line:
                break

            logs.append(
                line
            )

            visible_log = "".join(
                logs[-250:]
            )

            log_placeholder.code(
                visible_log,
                language="text"
            )

        process.stdout.close()

    return_code = process.wait()

    full_log = "".join(
        logs
    )

    return (
        return_code,
        full_log
    )


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title(
    "🧪 Software Testing Agent"
)

st.caption(
    "Describe what you want to test. "
    "The agent automatically chooses New Test, Maintenance, "
    "or Exploratory Testing."
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header(
        "Agent Settings"
    )

    mode_override = st.selectbox(
        "Mode",
        [
            AUTO_MODE,
            NEW_TEST_MODE,
            MAINTENANCE_MODE,
            EXPLORE_MODE
        ],
        index=0,
        help=(
            "Leave this on Auto-detect for normal use. "
            "Manual modes are available only when you want "
            "to force a specific backend scenario."
        )
    )

    st.divider()

    st.markdown(
        "**Project folder**"
    )

    st.code(
        str(PROJECT_ROOT),
        language="text"
    )


# --------------------------------------------------
# Main inputs
# --------------------------------------------------

left, right = st.columns(
    [2, 1]
)

with left:

    app_path = st.text_input(
        "Application URL",
        value="http://127.0.0.1:5050",
        placeholder="http://127.0.0.1:5050"
    )

with right:

    st.write("")
    st.write("")

    st.info(
        "The application must already be running "
        "before you start the testing agent."
    )


user_request = st.text_area(
    "What would you like the testing agent to do?",
    placeholder=(
        "Examples:\n"
        "• Test successful user signup\n"
        "• Test that searching for centrifuge returns relevant products\n"
        "• Explore this application and find bugs\n"
        "• Repair my existing test because the UI changed"
    ),
    height=150
)


# --------------------------------------------------
# Existing test script - optional
# --------------------------------------------------

with st.expander(
    "Existing Agent Browser test script (optional)"
):

    st.caption(
        "Use this only when you want the agent to maintain "
        "or self-heal an existing physical Agent Browser test."
    )

    uploaded_script = st.file_uploader(
        "Upload existing test",
        type=[
            "txt",
            "sh",
            "cmd"
        ]
    )

    uploaded_script_text = ""

    if uploaded_script is not None:

        try:

            uploaded_script_text = (
                uploaded_script.getvalue()
                .decode(
                    "utf-8"
                )
            )

        except UnicodeDecodeError:

            st.error(
                "The uploaded script must be a UTF-8 text file."
            )

    existing_script = st.text_area(
        "Or paste the existing Agent Browser script",
        value=uploaded_script_text,
        height=260,
        placeholder=(
            "agent-browser open http://127.0.0.1:5050\n"
            "agent-browser mouse move 430 260\n"
            "..."
        )
    )


# --------------------------------------------------
# Resolve and show detected task
# --------------------------------------------------

resolved_mode = resolve_mode(
    mode_override,
    user_request,
    existing_script
)

mode_descriptions = {
    NEW_TEST_MODE: (
        "Create a new functional test from your requirement."
    ),
    MAINTENANCE_MODE: (
        "Self-heal the supplied existing Agent Browser test."
    ),
    EXPLORE_MODE: (
        "Explore the application and discover grounded test cases."
    )
}

st.subheader(
    f"Detected task: {resolved_mode}"
)

st.caption(
    mode_descriptions.get(
        resolved_mode,
        ""
    )
)


# --------------------------------------------------
# Input validation
# --------------------------------------------------

can_run = True
validation_messages = []

if not app_path.strip():

    can_run = False

    validation_messages.append(
        "Application URL is required."
    )

if (
    resolved_mode == NEW_TEST_MODE
    and not user_request.strip()
):

    can_run = False

    validation_messages.append(
        "Describe the specific test you want to perform."
    )

if (
    resolved_mode == MAINTENANCE_MODE
    and not existing_script.strip()
):

    can_run = False

    validation_messages.append(
        "Maintenance requires an existing Agent Browser test script. "
        "Upload or paste one above."
    )

for message in validation_messages:

    st.warning(
        message
    )


# --------------------------------------------------
# Run button
# --------------------------------------------------

run_clicked = st.button(
    "▶ Run Testing Agent",
    type="primary",
    disabled=not can_run,
    use_container_width=True
)


# --------------------------------------------------
# Execute agent
# --------------------------------------------------

if run_clicked:

    if not MAIN_FILE.exists():

        st.error(
            f"main.py was not found at: {MAIN_FILE}"
        )

        st.stop()

    command = build_command(
        resolved_mode=resolved_mode,
        app_path=app_path.strip(),
        user_request=user_request.strip(),
        existing_script=existing_script.strip()
    )

    st.session_state[
        "last_detected_mode"
    ] = resolved_mode

    st.divider()

    st.subheader(
        "Live Agent Output"
    )

    st.info(
        f"Running: {resolved_mode}"
    )

    return_code, full_log = run_agent(
        command
    )

    st.session_state[
        "last_agent_log"
    ] = full_log

    st.session_state[
        "last_return_code"
    ] = return_code

    st.session_state[
        "last_generated_output"
    ] = extract_generated_output(
        full_log
    )

    if return_code == 0:

        st.success(
            "Agent run finished."
        )

    else:

        st.error(
            f"Agent process exited with code {return_code}."
        )


# --------------------------------------------------
# Completed run summary
# --------------------------------------------------

if st.session_state.get(
    "last_agent_log"
):

    full_log = st.session_state[
        "last_agent_log"
    ]

    generated_output = (
        st.session_state.get(
            "last_generated_output",
            ""
        )
    )

    metrics = extract_metrics(
        full_log
    )

    st.divider()

    completed_mode = (
        st.session_state.get(
            "last_detected_mode",
            resolved_mode
        )
    )

    st.subheader(
        "Run Summary"
    )

    st.write(
        f"**Task:** {completed_mode}"
    )

    if metrics:

        metric_columns = st.columns(
            5
        )

        metric_columns[0].metric(
            "Run Time",
            metrics.get(
                "Run Time",
                "—"
            )
        )

        metric_columns[1].metric(
            "Prompt Tokens",
            metrics.get(
                "Prompt Tokens",
                "—"
            )
        )

        metric_columns[2].metric(
            "Output Tokens",
            metrics.get(
                "Output Tokens",
                "—"
            )
        )

        metric_columns[3].metric(
            "Total Tokens",
            metrics.get(
                "Total Tokens",
                "—"
            )
        )

        metric_columns[4].metric(
            "Screenshots",
            metrics.get(
                "Screenshots",
                "—"
            )
        )

    st.subheader(
        "Generated Test Script / Report"
    )

    if generated_output:

        st.code(
            generated_output,
            language="text"
        )

        st.download_button(
            "Download Generated Output",
            data=generated_output,
            file_name=(
                "generated_test_output.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )

    else:

        st.warning(
            "No generated test script/report was found "
            "in the agent output."
        )

    with st.expander(
        "Show complete agent log"
    ):

        st.code(
            full_log,
            language="text"
        )

    st.download_button(
        "Download Full Run Log",
        data=full_log,
        file_name="agent_run_log.txt",
        mime="text/plain",
        use_container_width=True
    )
