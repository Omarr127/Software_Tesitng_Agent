def build_generate_prompt(
    context,
    task_mode,
    requirement,
    existing_script,
    test_intent,
    plan,
    executed_actions,
    app_path,
    expected_result,
    actual_result,
    visited_pages=None
):
    """
    Build a compact prompt for final Playwright
    test-script generation.
    """

    visited_pages = visited_pages or []

    return f"""
{context}

Generate a Python Playwright test script.

Requirement:
{requirement}

Application:
{app_path}

Testing intent:
{test_intent}

Plan:
{plan}

Executed actions:
{executed_actions}

Expected result:
{expected_result}

Actual result:
{actual_result}

Task mode:
{task_mode}

Existing script:
{existing_script if task_mode == "maintenance" else ""}

Pages visited (explore mode, in the order explored):
{visited_pages}

Rules:

- Return ONLY the final Python Playwright script.
- Do not return markdown.
- Do not return explanations.
- Do not return JSON.
- Generate runnable Python Playwright code.
- Keep the script short.
- Preserve the actual execution order.
- Preserve the actual test data.
- Use the actual application path.
- Do not invent elements.
- Do not invent selectors.
- Do not invent pages.
- Do not invent URLs.
- Do not invent application behavior.
- Agent Browser refs such as e2, e3, e4, e5 are temporary.
- Never use Agent Browser refs as Playwright selectors.
- Use the observed element information from Executed actions.
- If a bounding box is available, use its coordinates for dynamic
  element location instead of relying on a static Agent Browser ref.
- Do not invent coordinates.

Validation:

- Add a validation/assertion only when reliable evidence exists
  in Actual result or the observed execution data.
- If a success message/status was actually observed, validate it.
- For example, if the observed result contains
  "Account created successfully.", validate that message.
- Do not invent a success message.
- Do not add verification merely because the requirement says
  "test" or "register".
- If no reliable validation evidence exists, do not invent an assertion.

For new_test:

- Generate a new functional Playwright test.
- Use the executed actions as the primary source of truth.
- Preserve the actual values used.
- Use dynamic element positioning when bounding boxes are available.

For maintenance:

- Preserve the existing test structure.
- Preserve valid existing assertions.
- Patch only broken interactions.
- Use newly observed element information.
- Preserve the original testing intent.
- Return a complete runnable Python Playwright script.

For explore:

- Each executed action carries "case_id" and "page_url".
- Group the executed actions FIRST by page_url (in the order given
  by "Pages visited"), THEN by case_id (in first-seen order within
  that page).
- Do not regroup by re-reading the free-text "goal" — case_id is
  the ground truth for which actions belong to the same case.
- For each case, output its own command sequence followed by its
  own verdict line, judged only from the executed actions that carry
  that case_id.
- Do not invent an outcome that was not observed, and do not judge
  a case from an action that belongs to a different case_id.

Important:

The generated script must describe only behavior established
during the actual browser execution.

Return ONLY the Python code.
"""