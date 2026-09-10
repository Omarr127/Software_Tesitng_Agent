# Maintenance Testing Skill

## Purpose

This skill provides reusable instructions for **Scenario 2 — Test Script Maintenance / Self-Healing**.

Its purpose is to guide the agent in how to:

<<<<<<< HEAD
- understand an existing Agent Browser functional test script,
- recover its original testing intent and expected behavior,
- inspect an updated application,
- detect UI changes,
- identify current semantic equivalents of old targets,
- dynamically resolve those current elements to coordinates,
- execute the maintained flow using physical mouse and clipboard Agent Browser commands,
- repair only what changed,
- preserve valid logical behavior,
- verify that the original expected behavior still holds,
- and generate an updated Agent Browser command script representing the maintained flow.

The goal is not merely to replay old coordinates.

The goal is to preserve the original functional behavior while dynamically adapting execution to the current UI.

---

## When to Use

Use this skill when:

```text
task_mode = maintenance
```

and the inputs include:

- an existing Agent Browser functional test script,
- and an updated or modified application.

Typical examples include:

- a button label changed,
- a field label changed,
- a button moved,
- an input moved,
- the form layout changed,
- navigation changed,
- old coordinates no longer point to the intended control,
- or an existing Agent Browser script no longer reproduces the original behavior.

Do not use this skill for generating a completely new test from only a requirement.

---

## Inputs

Relevant Scenario 2 state may include:

- `task_mode`
- `existing_script`
- `test_intent`
- `plan`
- `current_step`
- `current_screen`
- `target_elements`
- `next_action`
- `action_result`
- `executed_actions`
- `browser_commands`
- `action_successful`
- `more_steps`
- `retry_count`
- `retries_available`
- `expected_result`
- `actual_result`
- `repair_needed`
- `generated_output`
- `partial_result`

Do not invent new persistent state fields unless the agreed `AgentState` is intentionally changed.

---

## Maintenance Objective

Follow this principle:

```text
Preserve the original intent
        ↓
Inspect the updated application
        ↓
Reuse what still works logically
        ↓
Find current semantic equivalents
        ↓
Resolve current positions dynamically
        ↓
Execute with mouse / clipboard commands
        ↓
Verify original expected behavior
        ↓
Generate the maintained command script
```

A changed UI element or changed position does not necessarily mean that the application's functional behavior changed.
=======
* understand an existing functional test script,
* recover the original testing intent and expected behavior,
* inspect an updated or modified application,
* execute the original logical test flow against the updated application,
* detect UI changes that cause existing test steps to fail,
* identify equivalent UI elements or actions when the application has changed,
* repair only the broken portions of the test flow,
* preserve valid existing test behavior,
* verify that the repaired flow still satisfies the original expected behavior,
* and generate an updated functional test script that reflects the repaired application flow.

This skill defines **how the agent should maintain and self-heal an existing functional test**.

Browser tools provide the capabilities for interacting with the updated application, while LangGraph controls the execution, routing, retry, reflection, verification, and final generation stages.

---

# When to Use

Use this skill when the selected task mode is:

```text
maintenance
```

and the provided inputs include:

* an existing functional test script,
* and an updated or modified application path.

Typical examples include:

* a button label changed from `Login` to `Sign In`,
* an input field was renamed,
* a selector or element reference changed,
* a button moved to another part of the page,
* a form structure changed,
* navigation between pages changed,
* a previously working test step can no longer locate its target,
* or another UI modification caused an existing functional test to stop working.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Example:

```text
<<<<<<< HEAD
Old UI:
Login button at one location

Updated UI:
Sign In button at another location
```

If both controls serve the same authentication purpose, the maintenance task should use the currently observed `Sign In` control and dynamically resolve its new coordinates.

---

## Dynamic Element Location Policy

Scenario 2 must not repair broken tests by blindly reusing old coordinates.

Instead, maintenance should repair **the semantic target** and then dynamically locate the current element during execution.

Correct flow:

```text
Original Agent Browser script
        ↓
Understand original logical action
        ↓
Understand target meaning from script context
        ↓
Observe current UI
        ↓
Find current semantic equivalent
        ↓
select current temporary observed ref
        ↓
browser tool gets CURRENT bounding box
        ↓
Python calculates center coordinates
        ↓
physical mouse / clipboard interaction
```

### Old coordinates are evidence, not final execution locations

The existing Agent Browser script may contain:

```text
agent-browser mouse move 600 205
agent-browser mouse down left
agent-browser mouse up left
```

Those coordinates describe where the old UI element was located.

They must not automatically be reused against the updated application.

The current position must be rediscovered from the current UI.

### Refs are temporary internal handles

A ref such as:

```text
@e5
```

may be used internally after current observation.

It must not become the final click/fill locator in the generated script.

### Never invent coordinates

The model must never guess x/y values.

Coordinates must come from the current element bounding box returned by the browser tool.

### Never invent replacement selectors

Do not invent CSS, XPath, IDs, `data-test` attributes, or other static locator syntax.

The maintained execution is coordinate-based.

---

## Core Maintenance Principles

### Preserve Intent

Always preserve the purpose of the original test.

=======
Old test:
Click "Login"

Updated application:
"Login" was renamed to "Sign In"

Maintenance behavior:
Identify "Sign In" as the equivalent action,
execute it,
verify that the original login behavior still succeeds,
and update the existing test script.
```

Do not use this skill for generating a completely new test from only a high-level requirement.

Scenario 1 should use the Scenario 1 E2E testing skill.

---

# Inputs

The skill may use information already available through the LangGraph state and browser/runtime environment.

Relevant Scenario 2 information can include:

* `task_mode` — identifies the task as `maintenance`,
* `existing_script` — the original functional test script,
* `test_intent` — the functional behavior represented by the existing script,
* `plan` — the ordered logical steps extracted from or derived from the original test,
* `current_step` — the step currently being validated or repaired,
* `current_screen` — the latest observation of the updated application,
* `target_elements` — relevant UI elements identified during observation,
* `next_action` — the browser action currently selected,
* `action_result` — the browser tool result,
* `executed_actions` — successful actions established against the updated application,
* `action_successful` — whether the browser action executed successfully,
* `more_steps` — whether additional test steps remain,
* `retry_count` — the current recovery attempt count,
* `retries_available` — whether another recovery attempt is permitted,
* `expected_result` — the original behavior that the existing test intends to verify,
* `actual_result` — the behavior observed after executing the maintained flow,
* `repair_needed` — whether the test flow still requires repair,
* `generated_output` — the final patched functional test script,
* `partial_result` — useful information preserved if maintenance cannot be completed.

Application initialization and opening are handled outside the LangGraph when appropriate.

Do not invent persistent state fields unless the team explicitly updates the agreed `AgentState`.

---

# Maintenance Objective

The primary objective is **not to rewrite the test from scratch**.

The objective is to preserve the original functional intent of the existing test while adapting only the parts that are no longer compatible with the updated application.

The agent should follow this principle:

```text
Preserve what still works.
Repair what changed.
Verify the original behavior.
Patch the existing test.
```

A changed UI element does not necessarily mean that application behavior has changed.

For example:

```text
Old UI:
Login

Updated UI:
Sign In
```

If both controls perform the same logical operation, the correct maintenance action is to map the old step to the new equivalent element rather than changing the intended test behavior.

The maintained script should continue testing the same logical requirement whenever possible.

---

# Core Maintenance Principles

## Preserve Intent

Always preserve the purpose of the original test.

Do not change the test objective merely because the UI changed.

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
Example:

```text
Original intent:
<<<<<<< HEAD
Verify that a user can successfully create an account.
```

A moved or renamed control does not change that intent.

### Preserve Valid Logical Work

Do not replace logical steps that still remain valid.
=======
Verify that a valid user can authenticate successfully.
```

A change from:

```text
Login
```

to:

```text
Sign In
```

does not change that intent.

---

## Preserve Valid Work

Do not replace or rewrite steps that still work correctly.

If only one action is broken, repair that action whenever possible.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Prefer:

```text
<<<<<<< HEAD
Keep step 1 intent
Keep step 2 intent
Repair step 3 target mapping
Keep step 4 intent
```

over rebuilding an unrelated test.

### Repair by Meaning

Use evidence such as:

- label,
- type,
- role,
- surrounding UI,
- test intent,
- expected behavior,
- current step,
- workflow position,
- and visual context

to identify the current equivalent.

### Evidence Before Repair

Do not invent:

- refs,
- coordinates,
- fields,
- buttons,
- links,
- URLs,
- messages,
- pages,
- redirects,
- or application behavior.

---

## Workflow

### 1. Understand the Existing Test

Read the existing Agent Browser script before interacting with the updated application.

Determine:

1. the functional behavior,
2. the user flow,
3. the test data,
4. required logical actions,
5. expected outcome,
6. any final observation or validation commands.

Separate logical meaning from old physical coordinates.

Example existing Agent Browser script:

```text
agent-browser mouse move 600 205
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "John Doe"
agent-browser clipboard paste

agent-browser mouse move 470 430
agent-browser mouse down left
agent-browser mouse up left

agent-browser snapshot
agent-browser screenshot validation_screen.png
```

Logical meaning:

```text
Enter the required signup data
→ submit the account creation form
→ verify successful account creation
```

The old coordinates are implementation details from the previous UI state.

The logical behavior must be preserved.

---

### 2. Determine Original Expected Behavior

Extract the expected behavior from:

- the existing Agent Browser script,
- the original testing intent,
- final snapshot/screenshot behavior when present,
- and clearly established application behavior.

Do not change the expected result merely to make the maintenance run pass.

---

### 3. Create a Maintenance Plan

Create an ordered logical plan preserving:

- original action order,
- original intent,
- existing test data,
- and the interaction sequence required to reach the original expected behavior.

The maintenance plan must contain **only executable user-interaction steps** that can become:

```text
fill
click
navigate
```

Do not put guessed current refs or guessed coordinates into the plan.

Do not include verification-only steps such as:

```text
Take a screenshot
Take a snapshot
Verify the result
Check success
Validate the result
Compare actual and expected behavior
```

Final behavior verification belongs to the separate Scenario 2 Verify node.

A valid plan may look like:

```text
1. Fill the Name field with "John Doe".
2. Fill the Email field with "user@example.com".
3. Fill the Password field with "Password123!".
4. Click the Create Account button.
```

After the final interaction step, the graph should route to Verify.

---

### 4. Inspect the Updated Application

Before executing the current step, observe the current UI.

Determine:

1. what page is visible,
2. whether the old logical target still exists,
3. what labels/roles/structure changed,
4. what currently observed elements are relevant,
5. whether a semantic equivalent exists,
6. whether the application is in the expected state.

Prefer:
=======
Keep step 1
Keep step 2
Repair step 3
Keep step 4
```

instead of:

```text
Generate an entirely different test.
```

---

## Repair by Meaning, Not Only by Text

Do not search only for exact text matches.

When an original target is unavailable, identify the most likely semantic equivalent using evidence from:

* element label,
* element type,
* role,
* surrounding UI,
* current step,
* test intent,
* expected behavior,
* position in the user flow,
* and available browser snapshot information.

For example:

```text
Original:
button "Login"

Possible updated equivalent:
button "Sign In"
```

may be a strong semantic match.

However:

```text
button "Create Account"
```

should not automatically be considered equivalent simply because it is also a button.

---

## Evidence Before Repair

Do not repair a step based only on assumption.

A replacement target should be supported by the current UI observation.

The agent should not invent:

* selectors,
* element references,
* fields,
* buttons,
* links,
* URLs,
* pages,
* redirects,
* messages,
* or application behavior.

---

# Workflow

## 1. Understand the Existing Test

Read the existing script before interacting with the updated application.

Determine:

1. what functional behavior the test is trying to validate,
2. what user flow the script performs,
3. what test data is used,
4. which actions are required,
5. what expected outcome the script verifies,
6. and which assertions represent the original success criteria.

Separate the **logical test intent** from implementation details.

Example:

```python
page.get_by_label("Email").fill("user@example.com")
page.get_by_label("Password").fill("123456")
page.get_by_role("button", name="Login").click()
```

The logical meaning is:

```text
Enter valid credentials
→ submit authentication
→ verify successful login
```

The selectors are implementation details.

The logical behavior must be preserved even when those implementation details change.

---

## 2. Determine Original Expected Behavior

Identify what the original script expects to happen after successful execution.

The expected behavior may be represented by assertions such as:

```python
expect(page).to_have_url(...)
```

```python
expect(page.get_by_text(...)).to_be_visible()
```

```python
expect(element).to_contain_text(...)
```

or equivalent test logic.

Extract the expected behavior carefully.

Do not invent an expected result that is not supported by:

* the existing script,
* the original testing intent,
* or clearly established application behavior.

Store or communicate the result through the agreed:

```text
expected_result
```

state field when appropriate.

---

## 3. Create a Maintenance Plan

Create an ordered plan representing the logical steps of the original test.

The plan should preserve:

* the original order,
* the original intent,
* relevant test data,
* and the relationship between actions and expected behavior.

Do not create an unrelated new testing flow.

A useful logical plan may look like:

```text
1. Enter the existing email test value.
2. Enter the existing password test value.
3. Submit the authentication form.
4. Confirm the original successful authentication behavior.
```

The maintenance plan should describe **logical goals**, not invent current element references before observation.

---

## 4. Inspect the Updated Application

Before executing the current step, inspect the current application state.

Use available UI observation information to determine:

1. what page or screen is currently visible,
2. whether the original target still exists,
3. whether its label, role, or structure changed,
4. what elements are relevant to the current maintenance step,
5. whether an equivalent replacement element exists,
6. and whether the application is in the expected state for continuing the test.

Prefer structured observation using:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
snapshot()
```

<<<<<<< HEAD
and use:
=======
when it provides enough information.

Use:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
screenshot()
```

<<<<<<< HEAD
when visual context is necessary.

---

### 5. Compare Original Intent with Current UI

For each step compare:
=======
when visual information is necessary to understand the updated UI or when structured observation is insufficient.

Do not assume that the updated application has the same structure as the original application.

---

## 5. Compare Original Intent with Current UI

For each step, conceptually compare:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
Original logical action
+
Original target meaning
+
<<<<<<< HEAD
Current observed UI
```

Possible outcomes:

#### Case A — Same logical target is directly available

Use the current observed element.

#### Case B — Target changed but an equivalent exists
=======
Current UI
```

Then determine whether:

### Case A — Original behavior is still directly available
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Example:

```text
Old:
<<<<<<< HEAD
Login

New:
Sign In
```

Use the currently observed equivalent.

#### Case C — Structure changed

Example:

```text
Old:
Email
Password
Login

New:
Email
Continue
Password
Sign In
```

Adapt the logical sequence while preserving authentication intent.

#### Case D — No reliable equivalent exists

Do not guess.

Use recovery or fail safely.

---

### 6. Decide the Next Action

Choose exactly one valid browser action based on:

- current maintenance step,
- original test intent,
- latest UI observation,
- observed current targets.

Allowed high-level actions include:
=======
Email input

New:
Email input
```

Proceed using the current observed element.

---

### Case B — Target changed but an equivalent exists

Example:

```text
Old:
Login button

New:
Sign In button
```

Use the new observed equivalent if there is sufficient evidence that it performs the same logical function.

---

### Case C — Structure changed

Example:

```text
Old:
Single login form

New:
Email step
→ Continue
→ Password step
→ Sign In
```

The agent may need to adapt the execution plan while preserving the same authentication intent.

Do not force the original exact action sequence when the updated interface requires a logically equivalent sequence.

---

### Case D — No reliable equivalent exists

Do not invent one.

Allow normal recovery and failure handling.

---

## 6. Decide the Next Action

Use:

* the current maintenance step,
* the original test intent,
* the current UI observation,
* and identified target elements

to choose exactly one valid browser action.

Available browser actions may include:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
fill
click
navigate
```

<<<<<<< HEAD
For `fill` and `click`:

- use only a ref from the current observation,
- treat that ref as internal and temporary,
- never invent coordinates,
- never invent static selectors.

The execution layer will resolve the current ref to the live bounding box and physical coordinates.

---

### 7. Execute the Action

Execute through:
=======
Observation capabilities include:

```text
snapshot
screenshot
```

The selected action should:

* directly support the original test intent,
* use an observed target,
* be suitable for the current UI,
* preserve original test data when applicable,
* and avoid unrelated interactions.

When an original target changed, choose the current equivalent based on evidence rather than exact text matching alone.

---

## 7. Execute the Action

Execute the selected action through the available browser tool interface.

Examples:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
fill(target, text)
click(target)
navigate(url)
```

<<<<<<< HEAD
Internally:

```text
current observed ref
        ↓
get current box
        ↓
calculate center
        ↓
mouse move
        ↓
mouse click
```

For text entry:

```text
mouse click
        ↓
Control+a
        ↓
clipboard write
        ↓
clipboard paste
```

Preserve original test data unless the original test itself legitimately requires otherwise.

Check the browser-tool result.
=======
Use the original test data unless:

* the existing script explicitly derives it dynamically,
* the value is unavailable,
* or the application modification legitimately requires a different representation without changing test intent.

Inspect the browser tool result after execution.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Do not assume success merely because the command was issued.

---

<<<<<<< HEAD
### 8. Re-Inspect After UI Changes

After meaningful interactions, observe again.
=======
## 8. Re-Inspect After UI Changes

After an action that may change the application state, observe the application again before selecting the next action.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Follow:

```text
Observe
→ Decide
→ Execute
→ Check result
→ Re-observe
→ Continue
```

<<<<<<< HEAD
Do not reuse stale refs after UI changes.

If the control moved, changed, or was replaced, the next action must be based on the newest observation and a newly resolved current bounding box.

---

## Detecting a Broken Test Step

A step may need repair when:

- old coordinates no longer target the intended element,
- the original target cannot be found,
- the label changed,
- the element moved,
- the structure changed,
- the sequence changed,
- navigation changed,
- or a browser action fails.

Do not call a step functionally broken merely because the old physical location changed if an equivalent current action still exists.

---

## Self-Healing Rules

When a step no longer works, identify a current semantic equivalent using approximately this priority:
=======
This is especially important during maintenance because UI updates may have changed:

* element references,
* page structure,
* navigation,
* labels,
* visibility,
* form organization,
* or available actions.

Do not reuse stale element references after the UI changes.

---

# Detecting a Broken Test Step

A test step may require repair when:

* the original target cannot be found,
* the original selector or reference is invalid,
* the original label changed,
* the original element exists but is no longer usable,
* the application structure changed,
* an action fails,
* the original sequence is no longer compatible with the current UI,
* navigation changed,
* or an equivalent logical action is now represented differently.

Do not classify a step as broken merely because an implementation detail changed if the same logical operation can still be performed.

---

# Self-Healing Rules

When a test step no longer works, attempt to identify a reliable equivalent.

Use evidence in approximately this priority:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

1. same semantic purpose,
2. same functional role,
3. compatible element type,
<<<<<<< HEAD
4. relationship to current logical step,
5. surrounding labels/context,
6. similar accessible name,
7. position in expected workflow,
8. visual evidence where necessary.

Once a current equivalent is chosen, the physical location must still be resolved dynamically from the current bounding box.

Do not reuse old coordinates simply because they came from the existing script.

---

## Repair Confidence

Repair only when there is reasonable evidence that the new current element is logically equivalent.

If several candidates are plausible and no reliable choice exists:
=======
4. relationship to the current logical step,
5. nearby labels or context,
6. similar accessible name,
7. location within the expected user flow,
8. current visual evidence when necessary.

Example:

```text
Original target:
button "Login"

Observed updated elements:
button "Create Account"
button "Sign In"
link "Forgot Password"
```

The strongest replacement is likely:

```text
button "Sign In"
```

because its semantic purpose matches the authentication action.

Do not select replacements merely because they have the same element type.

---

# Repair Confidence

Only repair when there is reasonable evidence that the new action is logically equivalent to the original action.

High-confidence evidence may include:

* strongly equivalent wording,
* matching element role,
* matching form context,
* matching surrounding labels,
* matching expected navigation behavior,
* matching workflow position,
* or successful execution followed by the original expected behavior.

If multiple elements are plausible and no reliable choice can be made:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
Do not guess.
```

<<<<<<< HEAD
Observe further, reflect, retry, or fail.

---

## Reflection and Re-Planning

When an action fails:

1. preserve successful logical steps,
2. re-observe if the UI may have changed,
3. reconsider the target meaning,
4. search current observed elements for a semantic equivalent,
5. adjust the remaining logical plan only when required,
6. select a current observed target,
7. let the browser execution layer resolve its current coordinates,
8. execute again.

Do not repeat the exact same failed action without new evidence.

---

## Retry Rules

LangGraph controls retry availability.

Do not create an independent retry system inside this skill.
=======
Allow reflection, further observation, retry, or failure.

---

# Reflection and Re-Planning

When an action fails, do not immediately discard the original plan.

Use available state information such as:

* `current_step`,
* `plan`,
* `next_action`,
* `action_result`,
* `current_screen`,
* `target_elements`,
* `test_intent`,
* `expected_result`,
* and previously successful actions.

Diagnose likely causes such as:

* stale target,
* renamed element,
* moved control,
* changed navigation,
* changed page structure,
* incorrect semantic match,
* missing element,
* unexpected application state,
* or insufficient observation.

When retries are available:

1. preserve successfully completed steps,
2. inspect the current UI again when necessary,
3. reconsider the failed target,
4. search for a semantically equivalent element,
5. adjust the current logical step when required,
6. adjust the remaining plan only when necessary,
7. choose a corrected action,
8. return through the normal Observe → Decide → Execute loop.

Do not repeat exactly the same failed action unless new evidence justifies it.

---

# Retry Rules

The LangGraph controls retry availability.

The skill must not maintain an independent retry counter.

Follow:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
Action failed
      ↓
Retries available?
      ↓
Yes
      ↓
Reflect + Re-plan
      ↓
<<<<<<< HEAD
Observe updated UI
      ↓
Find current semantic equivalent
      ↓
Resolve current coordinates
=======
Observe updated application
      ↓
Find corrected/equivalent action
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
      ↓
Execute
```

<<<<<<< HEAD
If retries are exhausted:

```text
FAIL
```

---

## Verification

Verification is required in Scenario 2.

Successful mouse/clipboard execution does not prove that maintenance succeeded.

After all interaction plan steps are complete, the graph should route to the Verify node.

The Verify node compares:
=======
When retries are exhausted:

```text
Action failed
      ↓
Retries available?
      ↓
No
      ↓
FAIL
```

Do not create infinite repair loops.

---

# Verification

Verification is a required part of Scenario 2.

Successful execution of browser commands alone does not prove that maintenance succeeded.

After the required interaction flow is completed, compare:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
expected_result
```

with:

```text
actual_result
```

<<<<<<< HEAD
Verification must be based on reliable evidence from the current application.
=======
The purpose is to determine whether the updated application still satisfies the original functional behavior.

Example:

```text
Original expected result:
Successful authentication reaches the authenticated application state.

Updated flow:
Email filled
Password filled
"Sign In" clicked

Actual result:
Authenticated application state reached
```

Result:

```text
Original behavior preserved.
```
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Verification Sources

<<<<<<< HEAD
Determine the actual application behavior using reliable evidence from the updated application.

Verification evidence may include:

- the current browser snapshot,
- the current screenshot,
- visible status or confirmation text,
- page state,
- navigation result,
- current URL,
- relevant visible UI components,
- or other information directly observable through the available browser tools.

Do not claim successful maintenance merely because mouse or clipboard commands executed successfully.

The final observed application state must provide evidence that the original expected behavior was achieved.

Example:

```text
Original expected behavior:
Account registration succeeds.

Observed current result:
"Account created successfully."
```

This is reliable evidence that the maintained interaction flow preserved the original behavior.

Do not invent missing success messages, redirects, page states, or other evidence.
=======
Actual behavior may be determined from reliable evidence such as:

* current browser snapshot,
* current screenshot,
* visible text,
* page state,
* navigation result,
* relevant URL,
* expected UI component,
* or other information observable through available tools.

Do not claim successful verification without supporting evidence.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Verification Outcomes

<<<<<<< HEAD
Compare:

```text
expected_result
```

with:

```text
actual_result
```

and determine whether further repair is required.

### Behavior Matches Expected Result

If the actual observed behavior satisfies the original expected behavior:
=======
### Behavior matches expectation

If:

```text
actual_result ≈ expected_result
```

then:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
repair_needed = False
```

<<<<<<< HEAD
The maintenance flow may proceed to Generate Output.

### Behavior Does Not Match Expected Result

If browser interactions execute successfully but the final observed application behavior does not satisfy the original expectation:
=======
The maintenance process may proceed to final script generation.

---

### Behavior does not match expectation

If the interaction flow completes but the actual application behavior does not satisfy the original expectation:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
repair_needed = True
```

<<<<<<< HEAD
The graph may route through the existing repair/reflection flow when retries are available.

Do not change the expected result merely to make the test pass.

### Behavior Cannot Be Verified

If there is insufficient reliable evidence:

- do not invent success,
- perform additional observation if the graph permits it,
- otherwise preserve the available partial result and fail safely.

---

## Distinguishing Test Repair from Application Failure

Old coordinates that no longer work are a test-maintenance problem.

A successfully located and clicked current equivalent that still fails to produce the original expected behavior may indicate an application behavior failure.

Do not hide real application failures by endlessly changing the test.

---

## Do Not Repair Expected Behavior to Hide Failures

Never change the original expected outcome simply to make the test pass.

Self-healing should preserve the original functional requirement unless the user explicitly changed it.

---

## Preserve Original Test Data

Existing test data should normally remain unchanged.

Do not generate random replacement values when the original values are still appropriate.

---

## Preserve Successful Actions

Keep the successful actions established against the updated application.

For each successful action, preserve the actual physical Agent Browser command string returned by the browser tools.

That command history is the basis of the final maintained script.

---

## Tool Usage Rules

1. Inspect before interaction.
2. Use currently observed targets only.
3. Treat refs as temporary internal handles.
4. Never invent coordinates.
5. Never invent CSS/XPath/static replacement selectors.
6. Resolve the target's current bounding box for coordinate execution.
7. Use physical mouse commands for clicks.
8. Use clipboard-based text entry for fills.
9. Check every action result.
10. Re-observe after meaningful UI changes.
11. Do not rely on stale refs.
12. Prefer minimal logical repairs.
13. Do not alter expected application behavior merely to make a test pass.

---

## Plan Modification Rules

Keep the existing logical plan stable when possible.

Modify it only when the updated UI requires a different sequence.
=======
The graph may route to recovery or repair when appropriate.

---

### Behavior cannot be verified

If insufficient evidence exists:

* do not invent successful behavior,
* attempt additional observation if permitted,
* otherwise preserve the partial result and fail safely.

---

# Distinguishing Test Repair from Application Failure

This distinction is critical.

A failing old test does **not automatically mean the updated application is broken**.

The failure may be caused by:

```text
Test implementation changed
```

rather than:

```text
Application behavior changed
```
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Example:

```text
<<<<<<< HEAD
Original:
Enter email
Enter password
Click Login

Updated:
=======
Old test:
Click button "Login"

Updated application:
Button renamed "Sign In"
```

The old script fails, but the application may still function correctly.

This is a **test maintenance problem**.

However:

```text
"Sign In" is clicked successfully
but valid credentials no longer authenticate
```

may represent an **application behavior failure**, not merely a broken selector.

The agent should not hide real application behavior failures by endlessly changing the test.

---

# Do Not Repair Assertions to Hide Failures

Never change the expected result simply to make the maintained test pass.

For example, if the original test expects:

```text
Successful login
```

but the updated application displays:

```text
Authentication failed
```

do not modify the test to assert:

```text
Authentication failed
```

unless the user explicitly changed the testing requirement.

Self-healing applies primarily to maintaining the test's compatibility with legitimate application changes.

It must not silently redefine the expected behavior.

---

# Preserve Original Test Data

Existing test data should normally remain unchanged.

Example:

```text
Email:
user@example.com

Password:
test1234
```

If these values are part of the existing test, preserve them unless there is a clear reason not to.

Do not generate random replacement credentials during maintenance when the original data is still appropriate.

---

# Preserve Successful Actions

Keep track of the actions that successfully reproduce the intended flow on the updated application.

Successful current actions are important evidence for:

* determining which steps changed,
* reconstructing the repaired script,
* preserving correct test order,
* and generating the final patched version.

Failed actions should not be presented as successfully repaired behavior.

---

# Tool Usage Rules

1. **Inspect before interaction.**

   Never assume the updated UI matches the old application.

2. **Use observed targets only.**

   Do not invent element references.

3. **Prefer structured UI evidence.**

   Use:

   ```text
   snapshot()
   ```

   whenever it provides enough information.

4. **Use visual analysis when necessary.**

   Use:

   ```text
   screenshot()
   ```

   when layout, appearance, placement, or other visual context helps resolve ambiguity.

5. **Use the correct action tool.**

   ```text
   Enter text      → fill(target, text)
   Activate target → click(target)
   Navigate        → navigate(url)
   ```

6. **Check every action result.**

7. **Re-observe after meaningful UI changes.**

8. **Do not rely on stale references.**

9. **Do not interact with unrelated elements.**

10. **Do not invent unsupported browser operations.**

11. **Prefer minimal repairs.**

12. **Do not change application behavior merely to make a test pass.**

---

# Plan Modification Rules

The existing logical plan should remain stable whenever possible.

Modify the plan only when the updated UI requires a different sequence to accomplish the same logical goal.

Example:

Original flow:

```text
Enter email
Enter password
Click Login
```

Updated flow:

```text
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
Enter email
Click Continue
Enter password
Click Sign In
```

<<<<<<< HEAD
The interaction sequence changed.

The authentication intent did not.

Verification remains outside the interaction plan.

---

## Patch Strategy

The maintenance output should preserve the original **logical behavior**, not old coordinates.

Preferred strategy:

```text
Existing Agent Browser script
      ↓
extract logical intent and test data
      ↓
identify broken logical step
      ↓
find current observed equivalent
      ↓
resolve CURRENT coordinates
      ↓
execute using mouse / clipboard commands
      ↓
preserve successful physical commands
      ↓
verify original expected behavior
      ↓
generate maintained Agent Browser script
```

Do not rebuild final click/fill output using old coordinates, static locators, or refs.

---

## Test Script Generation Instructions

The final Scenario 2 output should be a complete maintained **Agent Browser CLI test script based on the actual successful commands executed against the updated application**.

The final script should:

1. preserve the original test intent,
2. preserve valid original test data,
3. reflect the current working logical sequence,
4. use actual physical mouse commands for clicks,
5. use clipboard commands for text entry,
6. preserve navigation commands when required,
7. preserve verification behavior supported by the project,
8. avoid invented static locators,
9. avoid invented coordinates,
10. avoid invented successful behavior,
11. and be built from successful execution evidence.

### Required click output style

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
```

### Required fill output style

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "VALUE"
agent-browser clipboard paste
```

### Forbidden final click/fill output

Do not generate final interaction lines such as:

```text
agent-browser click @e5
agent-browser fill @e2 "VALUE"
```

Do not blindly preserve obsolete old coordinates in the maintained script.

The existing script is used as the source of original intent, test data, action sequence, and expected behavior.

---

## Expected Behavior Rules

The expected behavior remains the original functional requirement.

Example:

```text
Old logical action:
Submit account creation.

Current equivalent:
Click the currently observed Create Account button.
```

The physical position may change.

The expected account-creation outcome does not.

---

## Stop Conditions

Stop normal maintenance execution when:

1. all required logical interaction steps were reproduced,
2. the original expected behavior has been verified,
3. no repair remains,
4. output generation is ready,
5. retries are exhausted,
6. no reliable equivalent exists,
7. original behavior can no longer be achieved,
8. continuing would require invented UI information,
9. or the graph routes to FAIL.

---

## Failure Conditions

Maintenance is unsuccessful when relevant conditions include:

- original intent cannot be determined,
- no reliable current equivalent exists,
- current bounding box cannot be obtained for a required target,
- physical mouse or clipboard execution repeatedly fails,
- the updated application prevents the original behavior,
- verification fails,
- retries are exhausted,
- or repair would require invented information.

---

## Information to Preserve

Preserve:

- original Agent Browser script,
- original intent,
- expected behavior,
- logical plan,
- current step,
- current observations,
- observed current elements,
- semantic replacement mappings,
- original test data,
- executed actions,
- actual physical Agent Browser command strings,
- verification result,
- generated output or partial result.

Avoid unnecessary duplicated context.

---

## Context Efficiency

Use only context necessary for the current decision.
=======
A plan adjustment is justified because the UI structure changed.

However, the test intent remains:

```text
Authenticate using valid credentials.
```

Do not unnecessarily discard completed or still-valid plan steps.

---

# Patch Strategy

When generating the maintained test script:

```text
Preserve unchanged code whenever possible.
Modify only what must change.
```

Preferred behavior:

```text
Original script
      ↓
Identify broken step
      ↓
Find equivalent updated action
      ↓
Patch broken step
      ↓
Keep other valid steps
```

Avoid:

```text
Original script
      ↓
Ignore it
      ↓
Generate unrelated new script
```

---

# Test Script Generation Instructions

The final Scenario 2 output should be a complete patched functional test script.

When generating the patched script:

1. use the existing script as the structural baseline,
2. preserve the original test intent,
3. preserve valid test data,
4. preserve steps that remain correct,
5. replace obsolete selectors or actions only when supported by observed evidence,
6. incorporate any required equivalent actions discovered during maintenance,
7. preserve meaningful assertions representing the original expected behavior,
8. update assertions only when the application changed in a legitimate way that still represents the same underlying requirement,
9. do not invent selectors or UI elements,
10. do not invent successful behavior,
11. do not remove important verification merely to make execution pass,
12. generate executable Python Playwright code when the project uses Python Playwright,
13. maintain reasonable readability,
14. and return a complete script rather than a textual explanation.

---

# Selector Generation Rules

When producing Playwright code, use selector information that can be supported by observations collected during maintenance.

Prefer robust semantic selectors when sufficient information exists, such as:

```python
page.get_by_role(...)
page.get_by_label(...)
page.get_by_text(...)
```

when those labels or roles were actually observed.

Do not invent:

```python
#login-button-v2
.dashboard-container
[data-test="success"]
```

unless that information was genuinely observed or available from the existing test.

Do not blindly preserve an obsolete selector if the maintenance flow established that it no longer represents the correct element.

---

# Expected Behavior Rules

Assertions should represent the original functional requirement.

Example:

Original script:

```python
page.get_by_role("button", name="Login").click()
expect(page).to_have_url("/dashboard")
```

Updated UI:

```text
"Login" became "Sign In"
```

Correct maintenance:

```python
page.get_by_role("button", name="Sign In").click()
expect(page).to_have_url("/dashboard")
```

The interaction changed.

The expected functional behavior did not.

---

# Stop Conditions

Stop normal maintenance execution when any of the following is true:

1. all required original logical steps have been successfully reproduced,
2. the final expected behavior has been verified,
3. no additional repair is required,
4. the graph is ready to generate the patched script,
5. execution has failed and no retry remains,
6. no reliable equivalent can be identified,
7. the original behavior can no longer be achieved,
8. continuing would require inventing unsupported UI information,
9. or the graph routes execution to FAIL.

---

# Failure Conditions

Treat maintenance as unsuccessful when relevant conditions include:

* the original test intent cannot be reliably determined,
* a required target cannot be found or mapped to a reliable equivalent,
* a required browser action repeatedly fails,
* the updated application prevents completion of the original functional flow,
* final behavior does not satisfy the original expectation,
* the agent cannot determine the new UI state with sufficient confidence,
* retries are exhausted,
* or successful repair would require fabricating unsupported information.

Do not return a fully successful patched script when the maintained behavior was not actually established.

---

# Information to Preserve

Preserve information useful for maintenance and final script generation, including when relevant:

* original test script,
* original test intent,
* original expected behavior,
* logical plan,
* current logical step,
* successful original-equivalent mappings,
* current UI observations,
* relevant observed elements,
* successful replacement actions,
* test data,
* executed actions,
* actual final behavior,
* verification result,
* and generated or partial output.

Avoid preserving unnecessary:

* full raw screenshots when no longer useful,
* unrelated UI details,
* repeated observations,
* duplicated context,
* failed candidate elements that no longer matter,
* or unrelated application content.

---

# Context Efficiency

Maintenance should use only the context necessary for the current decision.

The agent should avoid repeatedly sending irrelevant parts of:

* large browser snapshots,
* previous screenshots,
* unrelated UI elements,
* or the entire execution history

when a smaller relevant context is sufficient.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Preserve high-value information such as:

```text
test intent
current step
original target meaning
current relevant elements
last action result
expected behavior
```

<<<<<<< HEAD
Avoid repeatedly sending irrelevant full snapshots or execution history when a compact relevant subset is sufficient.

---

## Completion Criteria

Scenario 2 is complete only when:

1. the existing Agent Browser script has been understood,
2. original testing intent is known,
3. original expected behavior is known,
4. the updated application has been observed,
5. required logical steps were reproduced,
6. changed targets were mapped to current observed equivalents,
7. current target positions were dynamically resolved,
8. physical mouse/clipboard execution succeeded or was recovered,
9. actual behavior was observed,
10. actual behavior matches the original expectation,
11. no unresolved repair remains,
12. and a maintained Agent Browser command script can be generated.

---

## Output Requirements

For successful Scenario 2 execution:
=======
This reduces model context size and helps maintain accurate decisions.

---

# Completion Criteria

Scenario 2 maintenance is complete only when:

1. the existing script has been understood,
2. the original testing intent has been identified,
3. the original expected behavior has been established,
4. the updated application has been inspected,
5. required logical steps have been executed against the updated application,
6. broken steps have been repaired using observed equivalents,
7. valid steps have been preserved,
8. all required actions succeeded or were successfully recovered,
9. the final actual behavior has been observed,
10. actual behavior satisfies the original expected behavior,
11. no unresolved repair remains,
12. and a complete patched functional test script can be generated.

---

# Output Requirements

For successful Scenario 2 execution, the final output is:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
generated_output
```

<<<<<<< HEAD
must contain the maintained Agent Browser CLI sequence based on commands actually executed against the updated application.

For click and fill actions, the final output must use physical mouse and clipboard commands rather than static locators, refs, or blindly reused old coordinates.

If maintenance cannot be completed, preserve:
=======
containing the complete patched functional test script.

The patched script should reflect:

1. the original test intent,
2. the existing script structure where still valid,
3. preserved original test data,
4. successfully repaired UI interactions,
5. observed replacement targets,
6. the successful current action sequence,
7. and verification of the original expected functional behavior.

The final output should contain the updated executable test script rather than a maintenance explanation unless another output format is explicitly requested.

---

# FAIL Output

If maintenance cannot be completed successfully, preserve:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
partial_result
```

<<<<<<< HEAD
rather than pretending that repair succeeded.

---

## Final Maintenance Principle
=======
with useful available information rather than pretending that repair succeeded.

Useful partial information may include:

* current plan,
* failed current step,
* latest action result,
* successfully executed actions,
* available UI evidence,
* and the portion of the flow that was successfully reproduced.

Do not generate a misleading fully repaired test when the original behavior was not successfully established.

---

# Final Maintenance Principle
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Always follow:

```text
<<<<<<< HEAD
Understand original Agent Browser test
        ↓
Preserve intent and test data
        ↓
Inspect updated application
        ↓
Find current semantic equivalents
        ↓
Use temporary observed refs internally
        ↓
Resolve CURRENT bounding boxes
        ↓
Execute physical mouse / clipboard commands
        ↓
Verify actual vs expected behavior
        ↓
Generate maintained Agent Browser command script
```

The goal of self-healing is to maintain the original functional behavior without depending on obsolete static coordinates or static locators.
=======
Understand the original test
        ↓
Preserve its intent
        ↓
Inspect the updated application
        ↓
Reuse what still works
        ↓
Detect what changed
        ↓
Find an observed semantic equivalent
        ↓
Repair only what is necessary
        ↓
Execute the repaired flow
        ↓
Verify actual vs expected behavior
        ↓
Generate the patched script
```

The goal of self-healing is not simply to make a failing script execute.

The goal is to maintain the original functional test **without losing the behavior it was designed to validate**.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
