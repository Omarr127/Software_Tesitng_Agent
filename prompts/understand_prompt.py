def build_understand_prompt(
    context,
    task_mode,
    task_input
):
    return f"""
{context}

Task mode:
{task_mode}

Task input:
{task_input}

Identify the main functional testing intent.

Rules:

- For "new_test":
  - Extract the testing objective from the requirement.

- For "maintenance":
  - Extract the original testing intent from the existing test script.
  - Preserve the original purpose.
  - Do not create a new testing objective.
  - Preserve the original expected behavior.

- Keep the intent concise.
- Do not describe implementation details.
- Do not create test steps.
- Do not invent behavior.
- Return valid JSON only.

Expected format:

{{
    "test_intent": "..."
}}
"""