def build_plan_prompt(
    context,
    task_mode,
    test_intent,
<<<<<<< HEAD
    existing_script,
    observed_elements=None,
    known_history=None
):
    observed_elements = observed_elements or []

    history_block = ""
    if task_mode == "explore":
        history_block = f"""
Earlier runs already tried on THIS page (most recent last, from memory):
{known_history or "(no earlier runs recorded for this page)"}
"""

=======
    existing_script
):
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
    return f"""
{context}

Task mode:
{task_mode}

Testing intent:
{test_intent}

Existing test script:
{existing_script}

<<<<<<< HEAD
Elements actually observed on the currently open page (label/type/ref):
{observed_elements}
{history_block}

=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
Create an ordered plan of atomic browser actions.

Execution model:
Observe → Decide ONE action → Execute → next step.

Rules:
- One plan step = one browser action.
- Keep steps simple and executable.
- Do not create browser commands.
- Do not create element references.
- Do not create selectors.
- Do not choose UI targets.
- Observe identifies actual elements later.
- Decide chooses the actual action later.
- The application is already open.
- Do not create open, localhost, or base-URL steps.
- Add navigation only when explicitly required.

Scenario 1 - new_test:
- Build the plan only from the testing requirement.
- Each form field must be a separate fill step.
- Submission must be a separate click step.
- Do not create verification or assertion steps.
- Do not create validate, verify, check, confirm, or success steps.
- Validation is handled separately after the functional actions.
- If the required form is already displayed, start with the first
  required interaction.

Example:
If the application already shows Name, Email, Password, and
Create Account, and the requirement is to test registration:

[
    {{"goal": "Fill the name field."}},
    {{"goal": "Fill the email field."}},
    {{"goal": "Fill the password field."}},
    {{"goal": "Click the Create Account button."}}
]

Scenario 2 - maintenance:
- Preserve the existing test's original intent.
- Preserve the original logical order.
- Preserve important test data.
- Convert interactions into atomic browser steps.
- Do not copy old selectors.
- Do not copy old Agent Browser references.
- Observe and Decide must adapt interactions to the updated UI.
- Do not add unrelated actions.
- Preserve verification-related steps when they are part of the
  existing maintenance flow.

<<<<<<< HEAD
Scenario 3 - explore:
- No requirement or script was given. You must decide what is worth testing
  entirely on your own, based only on the "Elements actually observed" list
  above -- never invent a field, button, or behavior that isn't in that list.
- Think in terms of independent CASES, not individual actions. A case is
  one edge-case idea (e.g. "invalid email format", "empty required field",
  "whitespace-only input"). Most cases need MORE THAN ONE action to reach a
  judgeable outcome -- e.g. filling an invalid value only means something
  once you also click the button that submits/validates it. A case that
  stops after "fill" with no follow-up action almost never proves anything
  by itself.
- Every step object must carry a "case_id" (e.g. "case_1", "case_2", ...).
  Steps that belong to the SAME case share the SAME case_id, listed in the
  exact order they must run (e.g. case_1's first step fills an invalid
  value, case_1's second step clicks the button that reveals the result).
  Only give a case a single step if one action is genuinely enough to
  observe the outcome (e.g. clicking "submit" on an already-empty form).
- You must propose AT LEAST 3 distinct case_id values, and up to 6. This is
  a hard minimum on the number of DISTINCT CASES, not on the number of
  steps -- a run with 3 cases and 5 total steps satisfies this; a run with
  5 steps that are all really the same case does not.
- Each case must reference something you actually observed (a specific
  field, its evident purpose, its type) and reflect your own reasoning
  about why probing it is worthwhile -- not a generic, reusable checklist
  item.
- Different applications should lead to different plans -- do not default
  to the same set of ideas regardless of what you observed.
- Do not just repeat a case verbatim from "Earlier runs already tried
  on THIS page" above -- cover ground that isn't already listed there.
  The exception is a deliberate regression check: you may re-test a
  case that was previously "BUG FOUND" to see whether it has since
  been fixed, but if you do, say so explicitly in that case's goal
  (e.g. "Re-check: previously found the app accepted an invalid
  email -- verify whether this is still true").

Return valid JSON only.

Expected format (task_mode "new_test" / "maintenance"):

=======
Return valid JSON only.

Expected format:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
[
    {{"goal": "One atomic browser action"}},
    {{"goal": "Another atomic browser action"}}
]
<<<<<<< HEAD

Expected format (task_mode "explore"):

[
    {{
        "case_id": "case_1",
        "goal": "Fill the email field with an invalid format (missing @) to check validation"
    }},
    {{
        "case_id": "case_1",
        "goal": "Click submit to see whether the invalid email is rejected"
    }},
    {{
        "case_id": "case_2",
        "goal": "Submit the form with the required name field left empty"
    }}
]
=======
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
"""