def build_decide_prompt(
    context,
    task_mode,
    current_step,
    target_elements,
    existing_script
):
    return f"""
{context}

Task:
{current_step}

Observed elements:
{target_elements}

{f"Existing script: {existing_script}" if task_mode == "maintenance" else ""}

Choose ONE action that completes the task.

Actions:
- fill: enter text into an observed input
- click: activate an observed element
- navigate: open a URL only when the task requires navigation

Rules:
- Use only an observed element ref.
- Never invent a ref.
- Choose exactly one action.
- For fill, provide the required test value.
- For click, value must be "".
- For navigate, target must be "" and value must be the destination URL.
- Ignore bounding-box coordinates when choosing the action.
- Do not add explanations.

For new_test:
- Follow the current task exactly.
- Use the observed element that matches the task.
- Preserve the required test data.

For maintenance:
- Preserve the original testing intent.
- Use the existing script to understand the original action.
- Use only currently observed elements.
- Do not reuse an old ref if it is no longer observed.

Return JSON only:

{{
    "action": "fill | click | navigate",
    "target": "...",
    "value": "..."
}}
"""