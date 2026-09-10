import json
<<<<<<< HEAD
import re
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

from state import AgentState
from tools.browser_tools import (
    snapshot,
    screenshot,
<<<<<<< HEAD
    get_box,
    open_app
=======
    get_box
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
)
from skills.skill_loader import load_context_for_node
from model import invoke_vlm
from prompts.observe_prompt import build_observe_prompt
from utils.json_utils import clean_json_response
from metrics.tracker import metrics_logger


<<<<<<< HEAD
# --------------------------------------------------
# Token optimization helpers
#
# Goal:
# - Keep the same browser behavior.
# - Keep screenshots/VLM when semantic reasoning is needed.
# - Avoid sending the same large accessibility tree to the
#   VLM for simple, obvious interaction steps.
# - Keep full snapshots internally for debugging/evidence.
# --------------------------------------------------

_INTERACTIVE_TYPES = {
    "textbox",
    "combobox",
    "button",
    "link",
    "checkbox",
    "radio",
    "option"
}

_STOP_WORDS = {
    "the",
    "a",
    "an",
    "to",
    "into",
    "in",
    "on",
    "of",
    "for",
    "with",
    "and",
    "or",
    "then",
    "this",
    "that",
    "field",
    "box",
    "input",
    "element",
    "button",
    "textbox",
    "combobox",
    "dropdown",
    "menu",
    "click",
    "open",
    "type",
    "fill",
    "enter",
    "press",
    "select",
    "submit",
    "verify",
    "observe",
    "test",
    "check"
}


def _parse_snapshot_interactive_elements(snapshot_text):
    """
    Parse obvious interactive elements directly from the
    Agent Browser accessibility snapshot.

    This does NOT invent refs. It only extracts refs that
    already exist in the current snapshot.

    Example input line:

        - button "Search" [ref=e6]

    Returns:
        [
            {
                "label": "Search",
                "type": "button",
                "ref": "e6"
            }
        ]
    """

    elements = []

    if not snapshot_text:
        return elements

    pattern = re.compile(
        r'-\s*'
        r'(textbox|combobox|button|link|checkbox|radio|option)'
        r'(?:\s+"([^"]*)")?'
        r'.*?'
        r'\[.*?ref=(e\d+).*?\]',
        re.IGNORECASE
    )

    seen_refs = set()

    for line in snapshot_text.splitlines():

        match = pattern.search(line)

        if not match:
            continue

        element_type = (
            match.group(1) or ""
        ).lower()

        label = (
            match.group(2) or ""
        ).strip()

        ref = match.group(3)

        if (
            element_type not in _INTERACTIVE_TYPES
            or not ref
            or ref in seen_refs
        ):
            continue

        seen_refs.add(ref)

        elements.append({
            "label": label,
            "type": element_type,
            "ref": ref
        })

    return elements


def _meaningful_words(text):
    """
    Extract simple semantic keywords used only for deterministic
    matching between the current plan step and labels already
    present in the accessibility snapshot.
    """

    words = re.findall(
        r"[a-z0-9]+",
        str(text or "").lower()
    )

    return {
        word
        for word in words
        if len(word) > 1
        and word not in _STOP_WORDS
    }


def _expected_element_types(step_text):
    """
    Infer broad element types from the current step.

    This is intentionally conservative. If the step is not
    obvious, return no restriction and let the VLM handle it.
    """

    step = str(
        step_text or ""
    ).lower()

    expected = set()

    if any(
        phrase in step
        for phrase in (
            "type ",
            "fill ",
            "enter text",
            "search box",
            "search field",
            "textbox",
            "input field"
        )
    ):
        expected.add("textbox")

    if any(
        phrase in step
        for phrase in (
            "combobox",
            "dropdown",
            "filter by category",
            "category filter",
            "open the category",
            "select category"
        )
    ):
        expected.add("combobox")

    if (
        "click" in step
        and "button" in step
    ):
        expected.add("button")

    if (
        "click the search" in step
        or "search button" in step
    ):
        expected.add("button")

    if (
        "link" in step
        or "navigate by clicking" in step
    ):
        expected.add("link")

    return expected


def _try_resolve_simple_step_from_snapshot(
    task_mode,
    current_step,
    snapshot_text
):
    """
    Fast path for simple Scenario 1 / Scenario 3 interaction steps.

    If the current structured snapshot contains one clear semantic
    match for the current step, return it directly and avoid a VLM
    observation call.

    Safety:
    - Only current snapshot refs are used.
    - No coordinates are guessed.
    - Bounding boxes are still fetched from Agent Browser.
    - Maintenance mode is excluded because self-healing benefits
      from full semantic VLM reasoning.
    - Ambiguous matches fall back to the VLM.
    """

    if task_mode not in (
        "new_test",
        "explore"
    ):
        return []

    if not current_step:
        return []

    step_text = (
        current_step.get("goal", "")
        if isinstance(current_step, dict)
        else str(current_step)
    )

    if not step_text.strip():
        return []

    elements = _parse_snapshot_interactive_elements(
        snapshot_text
    )

    if not elements:
        return []

    expected_types = _expected_element_types(
        step_text
    )

    step_words = _meaningful_words(
        step_text
    )

    scored = []

    for element in elements:

        element_type = element.get(
            "type",
            ""
        )

        if (
            expected_types
            and element_type not in expected_types
        ):
            continue

        label = element.get(
            "label",
            ""
        )

        label_words = _meaningful_words(
            label
        )

        overlap = (
            step_words
            & label_words
        )

        score = len(overlap)

        # Strong exact phrase hints.
        step_lower = step_text.lower()
        label_lower = label.lower()

        if (
            label_lower
            and label_lower in step_lower
        ):
            score += 4

        # Useful role hints.
        if (
            element_type == "textbox"
            and any(
                word in step_lower
                for word in (
                    "type",
                    "fill",
                    "search box",
                    "search field"
                )
            )
        ):
            score += 2

        if (
            element_type == "button"
            and "click" in step_lower
        ):
            score += 2

        if (
            element_type == "combobox"
            and any(
                word in step_lower
                for word in (
                    "combobox",
                    "dropdown",
                    "filter",
                    "category"
                )
            )
        ):
            score += 2

        if score > 0:
            scored.append(
                (
                    score,
                    element
                )
            )

    if not scored:
        return []

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_score = scored[0][0]

    best = [
        item[1]
        for item in scored
        if item[0] == best_score
    ]

    # Only use the deterministic fast path when one target
    # is clearly best. Ambiguity falls back to VLM.
    if len(best) != 1:
        return []

    # Require enough confidence that we matched something
    # semantically meaningful.
    if best_score < 2:
        return []

    print(
        "Observe: using structured snapshot fast path "
        f"for step: {step_text}"
    )

    return _attach_element_boxes(
        best
    )


def _compact_snapshot_for_observe(
    snapshot_text,
    max_chars=5000
):
    """
    Compact a large accessibility snapshot before sending it
    to the observation VLM.

    Preserve:
    - interactive controls
    - headings
    - status / alert / error-like lines
    - currently selected/expanded state
    - short static evidence lines

    Drop:
    - repetitive deep product descriptions
    - prices and low-value content when the page is very large

    The FULL snapshot is still kept internally and printed in
    debug output.
    """

    if not snapshot_text:
        return ""

    important_tokens = (
        "textbox",
        "combobox",
        "button",
        "link",
        "checkbox",
        "radio",
        "option",
        "heading",
        "status",
        "alert",
        "required",
        "selected",
        "expanded=",
        "no ",
        "success",
        "error",
        "invalid",
        "failed",
        "found"
    )

    kept = []
    seen = set()

    for raw_line in snapshot_text.splitlines():

        stripped = raw_line.strip()
        lowered = stripped.lower()

        if not stripped:
            continue

        keep = any(
            token in lowered
            for token in important_tokens
        )

        # Keep short StaticText lines because they often contain
        # important visible outcome evidence.
        if (
            "statictext" in lowered
            and len(stripped) <= 140
        ):
            keep = True

        if not keep:
            continue

        normalized = stripped

        if normalized in seen:
            continue

        seen.add(normalized)
        kept.append(raw_line)

        if len(
            "\n".join(kept)
        ) >= max_chars:
            break

    compacted = "\n".join(
        kept
    ).strip()

    if not compacted:
        compacted = snapshot_text[
            :max_chars
        ]

    return compacted


def _compact_snapshot_for_validation(
    snapshot_text,
    max_chars=4500
):
    """
    Compact case-validation snapshot text.

    Validation still receives the screenshot, so the text only
    needs to preserve strong textual evidence and current UI state.
    """

    return _compact_snapshot_for_observe(
        snapshot_text,
        max_chars=max_chars
    )


def _compact_observe_context(
    context,
    task_mode
):
    """
    Reduce repeated Observe skill text for Scenario 1/3.

    Maintenance keeps its original context because semantic
    self-healing can depend on richer instructions.
    """

    if task_mode == "maintenance":
        return context

    return """
Inspect the current application state and identify only the
element(s) relevant to the current testing step.

Rules:
- Use only elements actually present in the current snapshot/screenshot.
- Never invent elements, refs, coordinates, URLs, or selectors.
- Prefer the smallest set of relevant interactive elements.
- Current refs are temporary internal evidence only.
- Coordinates are resolved separately by Agent Browser.
- Return JSON only as a list of objects with:
  label, type, ref.
""".strip()


=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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
<<<<<<< HEAD
    # --------------------------------------------------

=======
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

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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
<<<<<<< HEAD
    selected element.

    The selector chooses the relevant element.
=======
    VLM-selected element.

    The VLM identifies the relevant element.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

    Agent Browser determines its actual location.

    This keeps coordinate detection out of the
<<<<<<< HEAD
    model prompt.
=======
    VLM prompt and therefore does not increase
    VLM token usage.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
        # --------------------------------------------------
        # Get actual browser bounding box
        # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
        # --------------------------------------------------
        # Preserve original element information
        # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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


<<<<<<< HEAD
def _validate_case_with_vlm(
    case_id,
    case_actions,
    snapshot_text,
    screenshot_path
):
    """
    Run VLM-based validation for a single explore-mode case.

    This keeps the same snapshot + screenshot + VLM validation
    architecture, but sends a compact textual snapshot to avoid
    repeatedly paying for low-value page text.
    """

    action_summary = []

    for action in case_actions:

        action_type = action.get(
            "action",
            ""
        )

        value = action.get(
            "value",
            ""
        )

        element = action.get(
            "element"
        ) or {}

        label = element.get(
            "label"
        ) or action.get(
            "target",
            ""
        )

        if action_type == "fill":
            action_summary.append(
                f'Filled "{label}" with "{value}"'
            )

        elif action_type == "click":
            action_summary.append(
                f'Clicked "{label}"'
            )

        elif action_type == "navigate":
            action_summary.append(
                f"Navigated to {value}"
            )

        elif action_type == "press":
            action_summary.append(
                f"Pressed {value}"
            )

    actions_text = (
        "\n".join(action_summary)
        or "(no actions)"
    )

    case_goal = ""

    for action in case_actions:

        goal = action.get(
            "goal",
            ""
        )

        if goal:
            case_goal = goal

    compact_snapshot = (
        _compact_snapshot_for_validation(
            snapshot_text
        )
    )

    validation_prompt = f"""
Validate one exploratory browser test case.

Case ID: {case_id}
Case goal: {case_goal}

Actions:
{actions_text}

Current page evidence:
{compact_snapshot}

Use the screenshot together with the textual evidence.

Return:
- validated=true when the observed result safely/correctly
  handled this case.
- validated=false when observed evidence shows incorrect
  behavior or a bug.
- If evidence is insufficient, explain that clearly.

Do not judge from command success alone.
Do not invent messages or behavior.

Return JSON only:

{{
    "validated": true,
    "evidence": "short observed evidence"
}}

or:

{{
    "validated": false,
    "evidence": "short observed issue"
}}
"""

    try:

        response = invoke_vlm(
            validation_prompt,
            screenshot_path
        )

        response = clean_json_response(
            response
        )

        validation = json.loads(
            response
        )

        if not isinstance(
            validation,
            dict
        ):

            return {
                "case_id": case_id,
                "validated": False,
                "evidence": (
                    "Validation returned invalid structure."
                )
            }

        return {
            "case_id": case_id,
            "validated": validation.get(
                "validated",
                False
            ),
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
            "evidence": (
                f"Validation request failed: {e}"
            )
        }


=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
def analyze_ui_with_vlm(
    task_mode,
    current_step,
    existing_script,
    snapshot_text,
    screenshot_path
):
    """
    Analyze the current UI using the VLM.

<<<<<<< HEAD
    Token optimization:
    - Full snapshot remains available internally.
    - The VLM receives a compact observation snapshot.
    - Scenario 1/3 use compact Observe instructions.
    - Maintenance keeps its richer original context.
    """

=======
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

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    if not screenshot_path:

        print(
            "Observe: screenshot path is missing."
        )

        return []

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 2. Load only the Observe-specific skill context
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
    model_context = (
        _compact_observe_context(
            context,
            task_mode
        )
    )

    model_snapshot = (
        snapshot_text
        if task_mode == "maintenance"
        else _compact_snapshot_for_observe(
            snapshot_text
        )
    )

    prompt = build_observe_prompt(
        model_context,
        task_mode,
        current_step,
        existing_script,
        model_snapshot
    )

=======
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

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
    # Keep FULL snapshot in local debug output.
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    print(
        snapshot_text
    )

    print(
<<<<<<< HEAD
        "\nObserve model snapshot:"
    )

    print(
        model_snapshot
    )

    print(
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        "\nObserve context loaded:"
    )

    print(
<<<<<<< HEAD
        model_context
=======
        context
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 5. Send prompt + screenshot to Gemini VLM
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 6. Parse VLM response
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 7. Validate returned structure
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 8. Validate individual elements
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 9. Get real browser coordinates
    #
    # IMPORTANT:
    #
    # The VLM does NOT generate these coordinates.
    #
    # Agent Browser gets them directly.
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    valid_elements = _attach_element_boxes(
        valid_elements
    )

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 10. Show final observation result
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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
<<<<<<< HEAD

    Optimization strategy:
    - Case-boundary VLM validation remains unchanged in behavior.
    - Full structured snapshot is always captured.
    - For obvious Scenario 1/3 action steps, resolve the current
      element directly from the snapshot and skip a redundant
      screenshot/VLM observation call.
    - Ambiguous steps still use screenshot + VLM.
    """

    # --------------------------------------------------
    # 0. Explore mode: per-case boundary handling
    # --------------------------------------------------

    case_validations = list(
        state.get(
            "case_validations",
            []
        )
    )

    if state.get(
        "task_mode"
    ) == "explore":

        current_step = (
            state.get(
                "current_step"
            )
            or {}
        )

        current_case_id = (
            current_step.get(
                "case_id"
            )
        )

        last_case_id = state.get(
            "last_case_id"
        )

        if (
            current_case_id
            != last_case_id
            and last_case_id is not None
        ):

            case_actions = [
                action
                for action in state.get(
                    "executed_actions",
                    []
                )
                if action.get(
                    "case_id"
                ) == last_case_id
            ]

            val_screenshot_path = (
                "case_validation_screen.png"
            )

            val_screenshot_result = screenshot(
                val_screenshot_path
            )

            val_snapshot_result = snapshot()

            val_snapshot_text = (
                val_snapshot_result.get(
                    "output",
                    ""
                )
                if val_snapshot_result.get(
                    "success"
                )
                else ""
            )

            if val_screenshot_result.get(
                "success"
            ):

                metrics_logger.log_screenshot(
                    val_screenshot_path
                )

                validation = (
                    _validate_case_with_vlm(
                        last_case_id,
                        case_actions,
                        val_snapshot_text,
                        val_screenshot_path
                    )
                )

                case_validations.append(
                    validation
                )

                print(
                    f"\n========== CASE VALIDATION: "
                    f"{last_case_id} =========="
                )

                print(
                    f"Validated: "
                    f"{validation.get('validated')}"
                )

                print(
                    f"Evidence: "
                    f"{validation.get('evidence')}"
                )

                print(
                    "========================================\n"
                )

            target_url = (
                state.get(
                    "current_page_url"
                )
                or state.get(
                    "app_path"
                )
            )

            if target_url:

                reopen_result = open_app(
                    target_url
                )

                if not reopen_result.get(
                    "success"
                ):

                    print(
                        "Warning: failed to reset to "
                        f"{target_url} before this case: "
                        f"{reopen_result.get('error')}"
                    )

    # --------------------------------------------------
=======
    """

    # --------------------------------------------------
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
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
<<<<<<< HEAD
            "target_elements": [],
            "case_validations": (
                case_validations
            )
=======
            "target_elements": []
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        }

    snapshot_text = snapshot_result.get(
        "output",
        ""
    )

<<<<<<< HEAD
=======
    # --------------------------------------------------
    # 1.1 Validate snapshot content
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    if not snapshot_text.strip():

        print(
            "Observe: browser snapshot is empty."
        )

    # --------------------------------------------------
<<<<<<< HEAD
    # 2. FAST PATH:
    #
    # For simple Scenario 1/3 steps, use the structured
    # snapshot directly and avoid another VLM call.
    #
    # This is the main token-saving change.
    # --------------------------------------------------

    task_mode = state.get(
        "task_mode",
        "new_test"
    )

    current_step = state.get(
        "current_step"
    )

    fast_elements = (
        _try_resolve_simple_step_from_snapshot(
            task_mode,
            current_step,
            snapshot_text
        )
    )

    if fast_elements:

        print(
            "\n========== OBSERVE RESULT =========="
        )

        print(
            "Target elements:"
        )

        print(
            fast_elements
        )

        print(
            "Source: structured snapshot fast path"
        )

        print(
            "====================================\n"
        )

        return {
            # Preserve the previous screen path when one exists.
            # The next real validation screenshot is still taken
            # at the case boundary.
            "current_screen": state.get(
                "current_screen"
            ),
            "target_elements": fast_elements,
            "case_validations": (
                case_validations
            )
        }

    # --------------------------------------------------
    # 3. Fallback: capture screenshot + use VLM
    #
    # Initial observation, maintenance, and ambiguous steps
    # continue to use the original semantic VLM path.
    # --------------------------------------------------

    screenshot_path = (
        "current_screen.png"
    )
=======
    # 2. Capture current browser screen
    # --------------------------------------------------

    screenshot_path = "current_screen.png"
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

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
<<<<<<< HEAD
            "target_elements": [],
            "case_validations": (
                case_validations
            )
        }

=======
            "target_elements": []
        }

    # --------------------------------------------------
    # 2.1 Log screenshot metrics
    # --------------------------------------------------

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    metrics_logger.log_screenshot(
        screenshot_path
    )

<<<<<<< HEAD
    target_elements = analyze_ui_with_vlm(
        task_mode=task_mode,
        current_step=current_step,
=======
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
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
        existing_script=state.get(
            "existing_script",
            ""
        ),
        snapshot_text=snapshot_text,
        screenshot_path=screenshot_path
    )

<<<<<<< HEAD
    return {
        "current_screen": screenshot_path,
        "target_elements": target_elements,
        "case_validations": case_validations
    }
=======
    # --------------------------------------------------
    # 4. Keep useful UI information in state
    # --------------------------------------------------

    return {
        "current_screen": screenshot_path,
        "target_elements": target_elements
    }
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
