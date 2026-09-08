import json
import re
import subprocess

from state import AgentState

from tools.browser_tools import (
    snapshot,
    screenshot
)

from model import invoke_llm, invoke_vlm

from utils.json_utils import clean_json_response

from metrics.tracker import metrics_logger

from memory import memory_store

from skills.skill_loader import load_context_for_node


def _has_unsafe_runtime_selectors(script):
    """
    Reject application-specific selectors that the model could
    have guessed instead of grounding in observed evidence.

    Runtime validation may still use a very small set of generic
    semantic browser selectors that are portable across apps.
    """

    allowed_selectors = {
        ":invalid",
        "[role=\"status\"]",
        "[role='status']",
        "[role=\"alert\"]",
        "[role='alert']"
    }

    selector_patterns = (
        r"querySelector\(\s*(['\"])(.*?)\1\s*\)",
        r"querySelectorAll\(\s*(['\"])(.*?)\1\s*\)"
    )

    for pattern in selector_patterns:
        for match in re.finditer(
            pattern,
            script,
            flags=re.IGNORECASE | re.DOTALL
        ):
            selector = match.group(2).strip()

            if selector not in allowed_selectors:
                print(
                    "Runtime validation rejected guessed "
                    f"selector: {selector}"
                )
                return True

    # Also reject direct app-specific selector APIs such as
    # getElementById because the ID would be invented unless it
    # had been explicitly established elsewhere.
    if re.search(
        r"getElementById\s*\(",
        script,
        flags=re.IGNORECASE
    ):
        print(
            "Runtime validation rejected application-specific "
            "getElementById usage."
        )
        return True

    return False


def _extract_inner_text_includes_literals(script):
    """
    Extract string literals used specifically in:

        document.body.innerText.includes("...")

    These literals should come from evidence actually
    observed for the current exploratory case.
    """

    if not isinstance(script, str):
        return []

    pattern = (
        r"document\.body\.innerText\.includes"
        r"\(\s*(['\"])(.*?)\1\s*\)"
    )

    return [
        match.group(2)
        for match in re.finditer(
            pattern,
            script,
            flags=re.IGNORECASE | re.DOTALL
        )
    ]


def _has_ungrounded_runtime_text(
    script,
    grounded_text="",
    fill_values=None
):
    """
    Reject body.innerText checks that rely on text which
    was not actually observed for the case.

    Also reject using a typed fill value itself as a
    body.innerText proof. Input values live in control.value
    and are not reliably represented by body.innerText.
    """

    fill_values = {
        str(value)
        for value in (fill_values or [])
        if value is not None
    }

    grounded_text = str(grounded_text or "")

    for literal in _extract_inner_text_includes_literals(
        script
    ):

        if literal in fill_values:
            print(
                "Runtime validation rejected input value "
                "used as body.innerText evidence: "
                f"{literal}"
            )
            return True

        if literal not in grounded_text:
            print(
                "Runtime validation rejected unobserved "
                f"text evidence: {literal}"
            )
            return True

    return False



def _recover_explore_case_id(
    action,
    action_index,
    plan_steps
):
    """
    Recover a Scenario 3 case_id without ever using "unknown".

    Priority:
    1. case_id already stored by execute.py
    2. case_id on the corresponding plan step
    3. deterministic numbered fallback

    The fallback keeps report generation stable even if an older
    plan did not attach case IDs.
    """

    if isinstance(action, dict):
        cid = action.get("case_id")

        if cid:
            return str(cid)

    if (
        action_index < len(plan_steps)
        and isinstance(
            plan_steps[action_index],
            dict
        )
    ):
        cid = plan_steps[
            action_index
        ].get("case_id")

        if cid:
            return str(cid)

    return f"case_{action_index + 1}"


def _case_goal_from_plan(
    state,
    case_id
):
    """
    Return a compact goal description for one exploratory case.
    """

    goals = []

    for step in state.get(
        "plan",
        []
    ):

        if not isinstance(
            step,
            dict
        ):
            continue

        if step.get(
            "case_id"
        ) != case_id:
            continue

        goal = str(
            step.get(
                "goal",
                ""
            )
        ).strip()

        if (
            goal
            and goal not in goals
        ):
            goals.append(
                goal
            )

    return " ".join(
        goals
    )


def _extract_grounded_quoted_evidence(
    evidence,
    final_state,
    fill_values=None
):
    """
    Find quoted evidence phrases that were actually observed
    in the final browser state.

    These phrases can be used for a conservative runtime
    fallback when the model-generated script is rejected.
    """

    evidence = str(
        evidence or ""
    )

    final_state = str(
        final_state or ""
    )

    fill_values = {
        str(value)
        for value in (
            fill_values or []
        )
        if value is not None
    }

    candidates = []

    for match in re.finditer(
        r"""['"]([^'"]{3,160})['"]""",
        evidence
    ):

        literal = match.group(
            1
        ).strip()

        if not literal:
            continue

        if literal in fill_values:
            continue

        if literal not in final_state:
            continue

        if literal not in candidates:
            candidates.append(
                literal
            )

    candidates.sort(
        key=len,
        reverse=True
    )

    return candidates


def _build_grounded_explore_fallback(
    case
):
    """
    Build a conservative case-specific runtime validation.

    This is used only when the model-generated validation was
    rejected by grounding checks.

    It never invents an error message.

    For transient UI cases such as opening a combobox/dropdown,
    visible text that already existed before the interaction is
    not enough proof, so the fallback returns INCONCLUSIVE.
    """

    case_id = str(
        case.get(
            "case_id",
            ""
        )
    )

    goal = str(
        case.get(
            "case_goal",
            ""
        )
    ).lower()

    evidence = str(
        case.get(
            "observed_evidence",
            ""
        )
    )

    final_state = str(
        case.get(
            "final_browser_state",
            ""
        )
    )

    observed_verdict = str(
        case.get(
            "observed_verdict",
            "INCONCLUSIVE"
        )
    )

    fill_values = [
        action.get(
            "value"
        )
        for action in case.get(
            "actions",
            []
        )
        if action.get(
            "action"
        ) == "fill"
    ]

    transient_keywords = (
        "open ",
        "opened",
        "expand",
        "expanded",
        "dropdown",
        "combobox",
        "menu"
    )

    is_transient_case = any(
        keyword in goal
        for keyword in transient_keywords
    )

    # For transient/native UI state, do not pretend that
    # unrelated visible page text proves the interaction.
    if is_transient_case:

        script = (
            "(() => { "
            "if (false) { return 'HANDLED'; } "
            "else if (false) { return 'BUG FOUND'; } "
            "else { return 'INCONCLUSIVE'; } "
            "})()"
        )

        return _build_eval_command(
            script,
            (
                "HANDLED",
                "BUG FOUND",
                "INCONCLUSIVE"
            )
        )

    phrases = _extract_grounded_quoted_evidence(
        evidence,
        final_state,
        fill_values=fill_values
    )

    if not phrases:

        script = (
            "(() => { "
            "if (false) { return 'HANDLED'; } "
            "else if (false) { return 'BUG FOUND'; } "
            "else { return 'INCONCLUSIVE'; } "
            "})()"
        )

        return _build_eval_command(
            script,
            (
                "HANDLED",
                "BUG FOUND",
                "INCONCLUSIVE"
            )
        )

    literal = json.dumps(
        phrases[0],
        ensure_ascii=False
    )

    if observed_verdict == "HANDLED":

        script = (
            "(() => { "
            "const text = document.body.innerText; "
            f"if (text.includes({literal})) "
            "{ return 'HANDLED'; } "
            "else if (false) { return 'BUG FOUND'; } "
            "else { return 'INCONCLUSIVE'; } "
            "})()"
        )

    elif observed_verdict == "BUG FOUND":

        script = (
            "(() => { "
            "const text = document.body.innerText; "
            "if (false) { return 'HANDLED'; } "
            f"else if (text.includes({literal})) "
            "{ return 'BUG FOUND'; } "
            "else { return 'INCONCLUSIVE'; } "
            "})()"
        )

    else:

        script = (
            "(() => { "
            "if (false) { return 'HANDLED'; } "
            "else if (false) { return 'BUG FOUND'; } "
            "else { return 'INCONCLUSIVE'; } "
            "})()"
        )

    return _build_eval_command(
        script,
        (
            "HANDLED",
            "BUG FOUND",
            "INCONCLUSIVE"
        )
    )

def _build_eval_command(
    script,
    required_labels,
    grounded_text=None,
    fill_values=None
):
    """
    Convert model-generated JavaScript into a runnable
    Agent Browser eval command after basic validation.
    """

    if not isinstance(script, str):
        return None

    script = script.strip()

    if not script:
        return None

    lowered = script.lower()

    if (
        "if" not in lowered
        or "else" not in lowered
    ):
        return None

    if not all(
        label in script
        for label in required_labels
    ):
        return None

    # Final validation must not depend on temporary refs.
    if "@e" in lowered:
        return None

    # Do not allow the generated validation to invent
    # app-specific selectors such as article, .result, #success,
    # or input[type=...]. Keep it grounded in generic semantic
    # browser state or exact evidence observed during execution.
    if _has_unsafe_runtime_selectors(script):
        return None

    # Scenario 3 can provide case-specific evidence here.
    # Reject invented text checks and reject treating a typed
    # input value as if it were body.innerText evidence.
    if grounded_text is not None:
        if _has_ungrounded_runtime_text(
            script,
            grounded_text=grounded_text,
            fill_values=fill_values
        ):
            return None

    return subprocess.list2cmdline([
        "agent-browser",
        "eval",
        script
    ])


def _generate_scenario1_runtime_validation(
    state,
    validation
):
    """
    Generate the final Agent Browser if/else validation
    command for Scenario 1.
    """

    try:
        context = load_context_for_node(
            "new_test",
            "generate"
        )
    except Exception:
        context = ""

    executed_actions = state.get(
        "executed_actions",
        []
    )

    final_state = ""

    if executed_actions:
        final_state = (
            executed_actions[-1].get(
                "resulting_state",
                ""
            )
        )

    prompt = f"""
{context}

Generate ONLY the runtime validation JavaScript for
this Scenario 1 Agent Browser test.

Requirement:
{state.get("requirement", "")}

Testing intent:
{state.get("test_intent", "")}

Observed final browser state:
{final_state}

Observed validation evidence:
{validation.get("evidence", "")}

The generated JavaScript will be used as:

agent-browser eval "<SCRIPT>"

Rules:
- Generate the condition specifically for this test.
- Do not use one fixed hardcoded validation rule.
- Inspect browser state at runtime.
- Use explicit JavaScript if / else.
- Do not click, fill, submit, navigate, or mutate state.
- Do not use temporary refs such as @e2.
- Do not invent application-specific CSS/XPath selectors.
- Do NOT query guessed page structures such as `article`,
  `input[type=...]`, `.result`, `#success`, product-card classes,
  or other selectors that were not established by observation.
- Prefer selector-free browser state such as:
  `document.body.innerText`, `location.href`, `location.pathname`,
  and `document.forms` / native form validity when appropriate.
- If a selector is genuinely needed, only generic semantic selectors
  are allowed here: `:invalid`, `[role="status"]`, `[role="alert"]`.
- Prefer evidence grounded in the observed application:
  URL/path, form validity, visible status/alert state,
  confirmation/error state, enabled/disabled state,
  or other established DOM state.
- Exact text may be checked only when that exact text was
  actually present in the observed browser state or validation
  evidence and is meaningful evidence for this requirement.

The JavaScript must return PASS or FAIL:

if (RUNTIME_CONDITION) {{
    return 'PASS';
}} else {{
    return 'FAIL';
}}

Return JSON only:
{{
    "script": "(() => {{ if (...) {{ return 'PASS'; }} else {{ return 'FAIL'; }} }})()"
}}
"""

    try:
        response = invoke_llm(prompt)
        response = clean_json_response(response)
        data = json.loads(response)
    except Exception as e:
        print(
            "Scenario 1 runtime validation "
            f"generation failed: {e}"
        )
        return None

    if not isinstance(data, dict):
        return None

    return _build_eval_command(
        data.get("script"),
        ("PASS", "FAIL")
    )


def _generate_explore_runtime_validations(
    state,
    cases_ordered,
    validation_by_case
):
    """
    Generate runtime Agent Browser if/else validation
    for all Scenario 3 cases in one LLM call.
    """

    try:
        context = load_context_for_node(
            "explore",
            "generate"
        )
    except Exception:
        context = ""

    cases = []

    for cid, actions in cases_ordered.items():

        val = validation_by_case.get(
            cid
        )

        if val:
            observed_verdict = (
                "HANDLED"
                if val.get("validated", False)
                else "BUG FOUND"
            )
            evidence = val.get(
                "evidence",
                ""
            )
        else:
            observed_verdict = "INCONCLUSIVE"
            evidence = "No VLM validation available."

        final_state = ""

        if actions:
            final_state = actions[-1].get(
                "resulting_state",
                ""
            )

        compact_actions = []

        for action in actions:
            element = action.get(
                "element"
            ) or {}

            compact_actions.append({
                "action": action.get("action"),
                "value": action.get("value"),
                "element_label": element.get("label"),
                "element_type": element.get("type")
            })

        cases.append({
            "case_id": cid,
            "case_goal": _case_goal_from_plan(
                state,
                cid
            ),
            "actions": compact_actions,
            "final_browser_state": final_state,
            "observed_verdict": observed_verdict,
            "observed_evidence": evidence
        })

    prompt = f"""
{context}

Generate runtime Agent Browser validation JavaScript
for EACH Scenario 3 exploratory case.

Plan:
{json.dumps(state.get("plan", []), ensure_ascii=False)}

Cases:
{json.dumps(cases, ensure_ascii=False)}

Each JavaScript expression will run after replaying
that case's Agent Browser commands.

Rules for every case:
- Generate a case-specific runtime condition.
- Do not use one fixed hardcoded condition for all cases.
- Inspect browser state at runtime.
- Use explicit if / else if / else.
- Do not click, fill, submit, navigate, or mutate state.
- Do not use temporary refs such as @e2.
- Do not invent application-specific CSS/XPath selectors.
- Do NOT query guessed page structures such as `article`,
  `input[type=...]`, `.result`, `#success`, product-card classes,
  or other selectors that were not established by observation.
- Prefer selector-free browser state such as:
  `document.body.innerText`, `location.href`, `location.pathname`,
  and `document.forms` / native form validity when appropriate.
- If a selector is genuinely needed, only generic semantic selectors
  are allowed here: `:invalid`, `[role="status"]`, `[role="alert"]`.
- Ground the condition in the case goal, actions,
  observed browser state, and evidence.
- Exact text may be checked only when that exact text was
  actually present in the observed browser state/evidence
  and is meaningful for that case.
- NEVER invent negative/error text such as `TypeError`, `Uncaught`,
  `Error loading ...`, or any other message that was not actually
  observed for that case.
- A value typed into an input is NOT reliable `document.body.innerText`
  evidence. Do not use `body.innerText.includes(TYPED_VALUE)` to prove
  the input value. Prefer the visible outcome produced by the action.
- Do not use text that already existed before the interaction as a
  weak proxy for a transient state such as "combobox opened".
- If the tested outcome is a transient/native browser state and there
  is no grounded, side-effect-free runtime property that proves it,
  make both HANDLED and BUG conditions false so the result falls
  through to INCONCLUSIVE.
- Return HANDLED only when runtime evidence directly proves
  correct handling of THIS case.
- Return BUG FOUND only when runtime evidence directly proves
  incorrect behavior and that evidence was actually observed.
- If the observed verdict is HANDLED and there was no observed
  bug evidence, use `false` for the BUG FOUND condition instead
  of inventing a possible error message.
- If the observed verdict is BUG FOUND and there was no observed
  handled-state evidence, use `false` for the HANDLED condition.
- A single strong, observed outcome is enough. Do not add extra
  weak conditions merely to make the expression more complex.
- Otherwise return INCONCLUSIVE.

Required JavaScript structure:

if (RUNTIME_HANDLED_CONDITION) {{
    return 'HANDLED';
}} else if (RUNTIME_BUG_CONDITION) {{
    return 'BUG FOUND';
}} else {{
    return 'INCONCLUSIVE';
}}

Return JSON only:
{{
    "validations": [
        {{
            "case_id": "case_1",
            "script": "(() => {{ if (...) {{ return 'HANDLED'; }} else if (...) {{ return 'BUG FOUND'; }} else {{ return 'INCONCLUSIVE'; }} }})()"
        }}
    ]
}}
"""

    try:
        response = invoke_llm(prompt)
        response = clean_json_response(response)
        data = json.loads(response)
    except Exception as e:
        print(
            "Scenario 3 runtime validation "
            f"generation failed: {e}"
        )
        return {}

    if not isinstance(data, dict):
        return {}

    validations = data.get(
        "validations",
        []
    )

    if not isinstance(validations, list):
        return {}

    commands = {}

    valid_case_ids = set(
        cases_ordered.keys()
    )

    grounded_text_by_case = {}
    fill_values_by_case = {}

    for case in cases:
        cid = case.get("case_id")

        grounded_text_by_case[cid] = "\n".join([
            str(case.get("final_browser_state") or ""),
            str(case.get("observed_evidence") or "")
        ])

        fill_values_by_case[cid] = [
            action.get("value")
            for action in case.get("actions", [])
            if action.get("action") == "fill"
        ]

    for item in validations:

        if not isinstance(item, dict):
            continue

        cid = item.get(
            "case_id"
        )

        if cid not in valid_case_ids:
            continue

        command = _build_eval_command(
            item.get("script"),
            (
                "HANDLED",
                "BUG FOUND",
                "INCONCLUSIVE"
            ),
            grounded_text=grounded_text_by_case.get(
                cid,
                ""
            ),
            fill_values=fill_values_by_case.get(
                cid,
                []
            )
        )

        if not command:
            # Do not immediately collapse a grounded case to a
            # generic all-false validation.
            #
            # Build a conservative case-specific fallback from
            # text that the VLM actually observed for THIS case.
            #
            # If the case is transient or there is no strong
            # grounded phrase, the fallback remains INCONCLUSIVE.
            matching_case = next(
                (
                    case
                    for case in cases
                    if case.get(
                        "case_id"
                    ) == cid
                ),
                None
            )

            if matching_case:
                command = (
                    _build_grounded_explore_fallback(
                        matching_case
                    )
                )

        if command:
            commands[cid] = command

    return commands


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

    Scenario 1 and Scenario 3 also append dynamically
    generated Agent Browser eval validation containing
    runtime JavaScript if/else logic.

    Scenario 2 remains unchanged.
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

        # Group executed actions by case_id, preserving order.
        #
        # Never label a real case as "unknown".
        # Prefer the case_id stored by execute.py. If an older
        # action is missing it, recover the ID from the matching
        # plan step. Only then use a deterministic numbered ID.
        from collections import OrderedDict

        plan_steps = [
            step
            for step in state.get(
                "plan",
                []
            )
            if isinstance(
                step,
                dict
            )
        ]

        cases_ordered = OrderedDict()

        for action_index, action in enumerate(
            executed_actions
        ):

            cid = _recover_explore_case_id(
                action,
                action_index,
                plan_steps
            )

            # Preserve the recovered ID in the local action copy
            # used by generation so later report logic remains
            # consistent.
            if not action.get(
                "case_id"
            ):
                action = action.copy()
                action["case_id"] = cid

            cases_ordered.setdefault(
                cid,
                []
            ).append(
                action
            )

        # --------------------------------------------------
        # Generate runtime Agent Browser validation for
        # every exploratory case in one LLM call.
        # --------------------------------------------------

        runtime_validation_by_case = (
            _generate_explore_runtime_validations(
                state,
                cases_ordered,
                validation_by_case
            )
        )

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

                # Use the actual case_id as the stable report
                # name. Pull the descriptive goal from the plan
                # only as optional context; execute.py does not
                # need to duplicate plan goals inside each action.
                case_goal = _case_goal_from_plan(
                    state,
                    cid
                )

                case_name = cid

                # Add the generated Agent Browser runtime
                # if/else validation for this case.
                runtime_validation_command = (
                    runtime_validation_by_case.get(
                        cid
                    )
                )

                if runtime_validation_command:
                    output.append(
                        runtime_validation_command
                    )

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
        # Add the generated Agent Browser runtime
        # if/else validation to the final script.
        # --------------------------------------------------

        runtime_validation_command = (
            _generate_scenario1_runtime_validation(
                state,
                validation
            )
        )

        if runtime_validation_command:
            browser_commands.append(
                runtime_validation_command
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