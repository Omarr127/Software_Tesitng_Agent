# Maintenance Testing Skill

## Purpose

This skill provides reusable instructions for **Scenario 2 — Test Script Maintenance / Self-Healing**.

Its purpose is to guide the agent in how to:

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

Example:

```text
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

Example:

```text
Original intent:
Verify that a user can successfully create an account.
```

A moved or renamed control does not change that intent.

### Preserve Valid Logical Work

Do not replace logical steps that still remain valid.

Prefer:

```text
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

```text
snapshot()
```

and use:

```text
screenshot()
```

when visual context is necessary.

---

### 5. Compare Original Intent with Current UI

For each step compare:

```text
Original logical action
+
Original target meaning
+
Current observed UI
```

Possible outcomes:

#### Case A — Same logical target is directly available

Use the current observed element.

#### Case B — Target changed but an equivalent exists

Example:

```text
Old:
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

```text
fill
click
navigate
```

For `fill` and `click`:

- use only a ref from the current observation,
- treat that ref as internal and temporary,
- never invent coordinates,
- never invent static selectors.

The execution layer will resolve the current ref to the live bounding box and physical coordinates.

---

### 7. Execute the Action

Execute through:

```text
fill(target, text)
click(target)
navigate(url)
```

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

Do not assume success merely because the command was issued.

---

### 8. Re-Inspect After UI Changes

After meaningful interactions, observe again.

Follow:

```text
Observe
→ Decide
→ Execute
→ Check result
→ Re-observe
→ Continue
```

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

1. same semantic purpose,
2. same functional role,
3. compatible element type,
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

```text
Do not guess.
```

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

```text
Action failed
      ↓
Retries available?
      ↓
Yes
      ↓
Reflect + Re-plan
      ↓
Observe updated UI
      ↓
Find current semantic equivalent
      ↓
Resolve current coordinates
      ↓
Execute
```

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

```text
expected_result
```

with:

```text
actual_result
```

Verification must be based on reliable evidence from the current application.

---

## Verification Sources

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

---

## Verification Outcomes

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

```text
repair_needed = False
```

The maintenance flow may proceed to Generate Output.

### Behavior Does Not Match Expected Result

If browser interactions execute successfully but the final observed application behavior does not satisfy the original expectation:

```text
repair_needed = True
```

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

Example:

```text
Original:
Enter email
Enter password
Click Login

Updated:
Enter email
Click Continue
Enter password
Click Sign In
```

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

Preserve high-value information such as:

```text
test intent
current step
original target meaning
current relevant elements
last action result
expected behavior
```

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

```text
generated_output
```

must contain the maintained Agent Browser CLI sequence based on commands actually executed against the updated application.

For click and fill actions, the final output must use physical mouse and clipboard commands rather than static locators, refs, or blindly reused old coordinates.

If maintenance cannot be completed, preserve:

```text
partial_result
```

rather than pretending that repair succeeded.

---

## Final Maintenance Principle

Always follow:

```text
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
