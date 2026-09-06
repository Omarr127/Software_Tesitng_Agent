def build_observe_prompt(
    context,
    task_mode,
    current_step,
    existing_script,
    snapshot_text
):
    """
    Build a compact Observe prompt.

    The browser snapshot is the source of truth for refs.
    The screenshot is used as visual evidence.
    """

    maintenance_context = (
        f"\nExisting test script:\n{existing_script}"
        if task_mode == "maintenance"
        else ""
    )

    return f"""
{context}

Step:
{current_step}

Snapshot:
{snapshot_text}
{maintenance_context}

Identify only the UI element(s) needed for this step.

Rules:
- Use only refs present in the snapshot.
- Do not invent refs or elements.
- Return only relevant elements.
- For maintenance, preserve the original interaction intent.
- Return [] if the required element is not present.
- Output JSON only.

Format:
[
  {{
    "label": "element label",
    "type": "element type",
    "ref": "existing ref"
  }}
]
"""