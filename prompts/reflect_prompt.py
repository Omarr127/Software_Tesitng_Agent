def build_reflect_prompt(
    context,
    task_mode,
    current_step,
    plan,
    next_action,
    action_result,
    target_elements,
    repair_needed,
    expected_result,
    actual_result
):
    return f"""
{context}

Task mode:
{task_mode}

Current testing step:
{current_step}

Current plan:
{plan}

Attempted action:
{next_action}

Action result:
{action_result}

Observed target elements:
{target_elements}

Repair needed:
{repair_needed}

Expected result:
{expected_result}

Actual result:
{actual_result}

Your responsibility:
Diagnose the current failure or maintenance mismatch
and produce the smallest necessary correction.

Rules:

- Preserve valid completed work.
- Preserve the original testing intent.
- Do not blindly repeat a failed action.
- Do not invent UI elements.
- Do not invent selectors or references.
- Modify only the part of the plan that requires recovery.
- Keep all still-valid steps unchanged.

If the browser action failed:
- Analyze the action result.
- Reconsider the current target using the observed UI.
- Adapt the current logical step when necessary.

If task_mode is "maintenance" and repair_needed is true:
- Compare expected behavior with actual behavior.
- Determine what part of the flow requires repair.
- Preserve the original expected behavior.
- Do not redefine the test merely to make it pass.

The revised current_step MUST be one of the steps
in the revised plan.

Return valid JSON only.

Expected format:

{{
    "current_step": {{
        "goal": "..."
    }},
    "plan": [
        {{
            "goal": "..."
        }}
    ]
}}
"""