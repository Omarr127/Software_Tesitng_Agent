def build_verify_prompt(
    context,
    test_intent,
    existing_script,
    snapshot_text
):
    return f"""
{context}

Testing intent:
{test_intent}

Existing test script:
{existing_script}

Current application snapshot after test execution:
{snapshot_text}

Your responsibility:
Verify the final behavior of the updated application
against the expected behavior of the existing test script.

Rules:
- Use the existing test script as the source of the expected behavior.
- Use the current application snapshot and screenshot as the source of the actual behavior.
- Identify the final expected result from the existing script.
- Identify what actually happened in the current updated application.
- Compare actual behavior with expected behavior.
- Do not invent UI elements, messages, pages, redirects, or application behavior.
- If the expected behavior is satisfied, set repair_needed to false.
- If the expected behavior is not satisfied, or the old test assertion must be updated because the final UI behavior changed, set repair_needed to true.
- If there is insufficient evidence to verify the expected behavior, set repair_needed to true.
- Keep expected_result and actual_result concise and specific.
- Return valid JSON only.

Expected format:

{{
    "expected_result": "...",
    "actual_result": "...",
    "repair_needed": false
}}
"""