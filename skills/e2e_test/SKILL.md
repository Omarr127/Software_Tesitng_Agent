# E2E Testing Skill

## Purpose

<<<<<<< HEAD
This skill provides reusable instructions for performing **Scenario 1 — New End-to-End Functional Test Generation**.
=======
This skill provides reusable instructions for performing Scenario 1 end-to-end functional web testing.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

Its purpose is to guide the agent in how to:

- understand the testing objective,
- inspect the current user interface,
- identify relevant UI elements,
<<<<<<< HEAD
- choose appropriate browser actions,
- dynamically resolve the current position of each target element,
- execute interactions through physical mouse and clipboard Agent Browser commands,
- observe the application after actions,
- recover from failed actions when retries are available,
- complete the required functional flow,
- and generate a runnable Agent Browser command script from the successful testing flow.

This skill defines **how the agent should perform Scenario 1 E2E testing**.

Browser tools provide the actual interaction capabilities. LangGraph controls when each stage of the workflow is executed.
=======
- choose and execute appropriate browser actions,
- observe the application after actions,
- recover from failed actions when retries are available,
- complete the required interaction flow,
- and generate a complete functional test script from the successful testing flow.

This skill defines **how the agent should perform E2E testing**. Browser tools provide the capabilities for interacting with the application, while the LangGraph controls when each stage of the workflow is executed.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## When to Use

<<<<<<< HEAD
Use this skill when:

```text
task_mode = new_test
```

and the goal is to generate a new functional test from a high-level requirement.

Examples include:

- Sign Up,
- Login,
- Search,
- navigation,
- form submission,
- or another supported functional user flow.

Do not use this skill for repairing an existing test script. Scenario 2 has separate maintenance instructions.
=======
Use this skill when the selected task mode is:

```text
new_test
```

and the goal is to generate a new functional test script from a high-level testing requirement.

Examples include:

- testing a Sign Up flow,
- testing Login,
- testing Search by keyword,
- testing navigation,
- testing form submission,
- or another functional user flow supported by the available browser tools.

Do not use this Scenario 1 skill as instructions for repairing an existing test script unless the project explicitly extends it for maintenance behavior.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Inputs

<<<<<<< HEAD
Relevant Scenario 1 state may include:

- `task_mode`
- `requirement`
- `test_intent`
- `plan`
- `current_step`
- `current_screen`
- `target_elements`
- `next_action`
- `action_result`
- `action_successful`
- `more_steps`
- `retries_available`
- `executed_actions`
- `browser_commands`
- `generated_output`
- `partial_result`

Application initialization is handled outside the LangGraph where appropriate.

Do not create new persistent graph-state fields only for this skill unless the agreed `AgentState` is intentionally changed.
=======
The skill may operate using information already available through the LangGraph state and browser/runtime environment.

Relevant Scenario 1 information can include:

- `task_mode` — identifies the task as `new_test`,
- `requirement` — the user's high-level testing requirement,
- `test_intent` — the functional behavior that needs to be tested,
- `plan` — the ordered testing steps,
- `current_step` — the step currently being executed,
- `current_screen` — the current UI observation,
- `target_elements` — UI elements identified during observation,
- `next_action` — the selected browser action,
- `action_result` — the result returned after executing an action,
- `action_successful` — whether the action succeeded,
- `more_steps` — whether additional planned steps remain,
- `retries_available` — whether recovery may be attempted,
- `generated_output` — the final generated test script,
- `partial_result` — the partial result returned if execution cannot continue.

Application/environment initialization is handled outside the LangGraph. Do not create additional graph-state fields only for this skill.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Testing Objective

<<<<<<< HEAD
The objective is not merely to issue browser commands.

The objective is to understand the requested behavior, carry out the required functional flow against the real application, and collect reliable execution evidence for a usable generated test.

A successful `click()` or `fill()` call does not by itself prove that the requested application behavior succeeded.

Scenario 1 must complete the planned interaction flow and then use the project’s final validation behavior to judge the requested result.

---

## Dynamic Element Location Policy

Scenario 1 uses **dynamic element discovery with coordinate-based physical execution**.

The correct separation is:

```text
Observe current UI
        ↓
identify the correct observed element
        ↓
use its temporary current ref internally
        ↓
browser tool requests the element's CURRENT bounding box
        ↓
Python calculates the current center coordinates
        ↓
physical mouse / clipboard commands are executed
```

### Temporary refs are internal only

An observed ref such as:

```text
@e2
```

is a temporary internal handle used to ask Agent Browser for the element's current bounding box.

It is **not** the locator format of the final generated test.

### Never invent coordinates

The model must never guess values such as:

```text
x = 600
y = 300
```

Coordinates must come from the real bounding box returned by the browser tool for the currently observed element.

### Never invent static selectors

Do not invent or use unobserved:

- CSS selectors,
- XPath expressions,
- element IDs,
- data-test selectors,
- or other static locator strings

as replacements for current observed elements.

### Final physical interaction format

For a click, the execution layer should produce physical commands equivalent to:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
```

For text entry, the execution layer should produce commands equivalent to:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "VALUE"
agent-browser clipboard paste
```

The model chooses **what element** is needed.

The browser execution layer determines **where that element currently is**.
=======
The objective is not merely to execute browser actions.

The objective is to understand and execute the requested functional flow and to collect enough reliable information to generate a usable initial test script.

An action such as clicking a button or filling an input does not by itself mean that the current step succeeded.

For Scenario 1, completion is based on successfully carrying out the required planned steps, handling failures through the graph when necessary, and collecting enough reliable information to generate the initial test script. Actual-versus-expected behavior verification belongs to Scenario 2 maintenance.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Workflow

### 1. Inspect

Inspect the current application state before choosing an interaction.

<<<<<<< HEAD
Use the available UI observation to:

1. understand the current page,
2. identify elements relevant to the current testing step,
3. determine whether the required target exists,
4. determine whether it is suitable for the intended action,
5. avoid interacting with elements that have not been observed with reasonable confidence.

Prefer structured UI observation with:

```text
snapshot()
```

when it provides enough information.

Use:

```text
screenshot()
```

when visual information is necessary.

Do not assume an element exists merely because the requirement implies it should exist.
=======
Use the available UI observation information to:

1. understand what page or screen is currently displayed,
2. identify elements relevant to the current testing step,
3. determine whether the required target element exists,
4. determine whether the element is suitable for the intended action,
5. avoid interacting with elements that have not been identified with reasonable confidence.

Prefer structured UI observation using `snapshot()` when it provides enough information.

Use `screenshot()` when visual information is necessary to understand the current UI or when structured observation alone is insufficient.

Inspection should produce only useful information needed for the current testing task.

Do not assume that an element exists simply because the requirement implies that it should exist.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 2. Decide

<<<<<<< HEAD
Read the current test step and the latest UI observation.

Choose exactly one appropriate next action.
=======
Read the current test step and the latest UI observation before selecting the next action.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

The selected action should:

- directly support the current testing objective,
<<<<<<< HEAD
- use an element identified in the current observation,
- correspond to the current plan step,
- avoid unnecessary interactions,
- and be possible using the available browser tools.

For `fill` and `click` actions:

- choose only a ref that came from the current observed UI,
- treat the ref only as an internal temporary target,
- never invent a ref,
- never invent coordinates,
- never invent CSS/XPath selectors,
- never try to convert the element into a static locator in the prompt.

The execution layer will dynamically resolve the selected observed ref to its current bounding box and physical coordinates.

Examples of valid high-level decisions include:

```text
fill the currently observed Email field with the required value
click the currently observed Sign Up button
navigate to the required URL
```

Do not blindly execute a sequence when the page has changed.
=======
- use an element identified during observation,
- correspond to the current step in the plan,
- avoid unnecessary interactions,
- and be possible using the available browser tools.

Choose one appropriate next action at a time.

Examples include:

- filling an identified input,
- clicking an identified button,
- navigating when navigation is required,
- or requesting additional observation when the current UI information is insufficient.

Do not blindly execute a sequence of actions when the application state has changed.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 3. Act

<<<<<<< HEAD
Execute the selected action through the existing browser-tool interface.

Available capabilities include:
=======
Execute the selected action using the appropriate browser tool.

Available browser capabilities include:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)
```

<<<<<<< HEAD
For LangGraph reasoning, `target` may be the current observed ref.

However, the physical execution of `click(target)` and `fill(target, text)` is coordinate-based:

```text
target ref
    ↓
get current bounding box
    ↓
calculate current center
    ↓
mouse move
    ↓
physical click
```

For `fill(target, text)`, text entry uses:

```text
physical click
    ↓
Control+a
    ↓
clipboard write
    ↓
clipboard paste
```

Do not manually invent the coordinate commands inside the LLM response. The browser tools own this translation.

After execution, inspect the returned tool result.

Do not assume success merely because a tool was called.
=======
Application opening or runtime initialization may use `open_app(path)` outside the LangGraph execution boundary.

For an action:

- use `fill(target, text)` when text must be entered,
- use `click(target)` when an identified interactive element must be activated,
- use `navigate(url)` when navigation to another URL is required,
- use observation tools instead of interaction tools when more UI information is needed.

After execution, inspect the returned result.

Do not assume that a browser action succeeded merely because the tool was called.

The execution result must be used to determine whether the action was successful.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 4. Re-inspect

<<<<<<< HEAD
After a successful action that may change the UI, observe again before choosing the next action.

Follow:
=======
When a successful action is followed by additional testing steps, observe the UI again before deciding the next action.

This is required because an interaction may:

- change the page,
- reveal new elements,
- hide previous elements,
- update text or results,
- change element references,
- open another screen,
- or otherwise modify the application state.

Follow this pattern:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
Observe
→ Decide
→ Execute
<<<<<<< HEAD
→ Check result
=======
→ Check action result
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
→ Observe updated UI
→ Decide next action
```

<<<<<<< HEAD
This is required because interactions may:

- navigate,
- reveal new elements,
- remove old elements,
- change labels,
- change element refs,
- move controls,
- change form state,
- or otherwise invalidate old observations.

Never assume that an old ref is still valid after a meaningful UI change.

The next interaction must be grounded in the latest observation.
=======
Do not rely on stale UI information after an action that may have changed the page.

The latest observation should replace or update outdated UI assumptions with information useful for the current step.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 5. Complete Scenario 1 Execution

<<<<<<< HEAD
When all planned execution steps are complete, the graph may proceed to output generation and final validation.

Successful Scenario 1 execution means:

- the required steps were executed successfully or recovered successfully,
- no required steps remain,
- current UI targets were observed rather than invented,
- physical browser interactions were generated from current element coordinates,
- and enough reliable information exists to validate and generate the final output.
=======
When no planned execution steps remain, Scenario 1 execution is complete and the graph can proceed to output generation.

Scenario 1 does not compare:

```text
actual_result
```

with:

```text
expected_result
```

and does not use `repair_needed`.

Those fields and the Verify Behavior / Repair Needed path belong to Scenario 2 maintenance.

For Scenario 1, successful completion means that the required planned browser actions were carried out successfully or recovered successfully, no required steps remain, and enough reliable action and UI information has been collected to generate the initial functional test script.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 6. Recover / Re-plan

<<<<<<< HEAD
If an action fails, do not blindly continue.

Use existing state such as:

- `action_result`
- `current_step`
- `current_screen`
- `target_elements`
- `plan`
- previously executed actions

to diagnose the problem.

When retries are available:

1. observe the current UI again,
2. determine whether the target disappeared, changed, or moved,
3. reconsider the current logical step,
4. select a new currently observed equivalent if appropriate,
5. let the execution layer dynamically resolve the new target's current coordinates,
6. retry through the normal Observe → Decide → Execute path.

Do not reuse a stale ref simply because it was valid earlier.

Do not guess replacement coordinates.
=======
If an action fails, do not blindly continue to the next planned step.

Use the existing state information to diagnose the failure, including relevant information such as:

- `action_result`,
- `current_step`,
- `current_screen`,
- `target_elements`,
- and the existing `plan`.

When retries are available:

1. inspect the current UI again when necessary,
2. determine whether the target or UI state has changed,
3. reconsider the current step,
4. adjust the current step and/or plan when appropriate,
5. select a new valid action,
6. retry through the normal Observe → Decide → Execute flow.

Re-planning should correct the current execution path without unnecessarily discarding valid completed work.

Do not create separate persistent state fields such as:

```text
failure_reason
reflection_text
retry_count
```

unless the team changes the agreed `AgentState`.

Failure diagnosis is part of the Reflect + Re-plan behavior and should use the state already defined by the graph.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 7. Complete Testing

Execution is ready for final output only when:

<<<<<<< HEAD
1. all required testing steps are complete,
2. no required execution steps remain,
3. required UI targets were observed,
4. browser actions succeeded or were successfully recovered,
5. coordinate-based physical commands were produced by the execution layer,
6. and enough reliable evidence exists for final output and validation.

If execution cannot continue and no retry remains, stop and preserve the partial result.
=======
1. the required testing steps have been completed,
2. there are no remaining execution steps,
3. required UI targets were observed rather than invented,
4. browser actions required for the flow succeeded or were successfully recovered,
5. and enough reliable information has been collected to generate the initial functional test script.

For Scenario 1, do not route to final behavior verification after the planned steps are complete. The graph proceeds to Generate Output.

If execution cannot continue and no retry is available, stop testing and allow the graph to return the available partial result through the FAIL path.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

### 8. Generate Test Script

<<<<<<< HEAD
Generate the final Scenario 1 script from the **actual successful Agent Browser commands returned by the browser tools**.

Do not reconstruct click/fill actions from refs.

The final generated interaction script should preserve the exact physical command sequence that was successfully executed.

For click actions, final output should contain commands such as:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
```

For fill actions, final output should contain commands such as:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "VALUE"
agent-browser clipboard paste
```

The final interaction script must **not** replace these with:

```text
agent-browser click @e2
agent-browser fill @e3 "VALUE"
```

Refs may remain in internal state for debugging and traceability, but they are not final test locators.

Navigation and validation commands may remain as their supported Agent Browser commands.

### Runtime Agent Browser Validation

The final generated Scenario 1 script must end with a **runtime validation command executed by Agent Browser**.

The validation must be generated specifically for the current test. It must not use one fixed validation rule for every application or every requirement.

Use this structure:

```text
agent-browser eval "(() => {
    if (RUNTIME_CONDITION) {
        return 'PASS';
    } else {
        return 'FAIL';
    }
})()"
```

Requirements:

- the JavaScript must contain an explicit `if / else`,
- the condition must be derived from the current requirement, testing intent, executed actions, and observed final application evidence,
- the condition must inspect the browser state at runtime,
- the validation must be side-effect-free,
- do not click, fill, submit, navigate, mutate application state, or call application APIs during validation,
- do not use Agent Browser refs such as `@e2` in the validation,
- do not invent application-specific CSS/XPath selectors,
- prefer semantic runtime signals that are grounded in observed evidence, such as:
  - current URL or pathname,
  - form validity,
  - visible status or alert regions,
  - visible confirmation/error state,
  - element enabled/disabled state,
  - DOM state that was actually observed during execution,
- do not use one universal hardcoded success message,
- do not invent application-specific selectors such as `article`, `input[type=...]`, `.result`, `#success`, product-card classes, or other guessed page structures,
- prefer selector-free runtime state such as `document.body.innerText`, `location.href`, `location.pathname`, and native form validity,
- if a selector is genuinely needed, use only generic semantic selectors such as `:invalid`, `[role="status"]`, or `[role="alert"]`,
- exact text may be checked only when that exact text was actually observed and is meaningful evidence for the current requirement,
- return `PASS` only when the runtime browser state satisfies the expected behavior,
- otherwise return `FAIL`.

The validation condition is generated intelligently for the current test, while Agent Browser performs the actual runtime check.
=======
For Scenario 1, generate a complete functional test script representing the successfully established testing flow.

The generated script should be based on actions and observations that were actually established during testing.

The script should:

- represent the intended user flow,
- preserve the successful order of actions,
- use targets supported by UI observations,
- include the required test data,
- include verification/assertion behavior for the expected outcome,
- avoid adding unnecessary interactions,
- avoid inventing UI elements that were never observed,
- and represent the intended functional behavior described by the requirement.

Do not treat a list of browser actions alone as a complete test script.

The generated script must also contain verification of the expected functional outcome.

If the graph reaches FAIL instead of successful generation, preserve the available partial result rather than pretending that a complete successful script was produced.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Tool Usage Rules

<<<<<<< HEAD
1. **Inspect before interacting.**

2. **Use observed targets only.**

3. **Treat observed refs as temporary internal handles only.**

4. **Never invent x/y coordinates.**

5. **Never invent CSS or XPath selectors.**

6. **Resolve location dynamically.**

   For `click()` and `fill()`, the browser execution layer must obtain the target's current bounding box immediately for the current action.

7. **Use physical coordinate interaction for click/fill.**

8. **Use clipboard-based text entry.**

9. **Check every browser-tool result.**

10. **Do not assume success.**

11. **Re-observe after meaningful UI changes.**

12. **Do not use stale refs after the page changes.**

13. **Prefer relevant actions only.**

14. **Use screenshots only when they add useful visual evidence.**

15. **Stay within the provided browser interface.**
=======
Follow these rules whenever browser tools are involved:

1. **Inspect before interacting.**  
   Identify relevant UI elements before attempting to click or fill them.

2. **Use the correct tool for the intended operation.**

   ```text
   Understand current UI      → snapshot()
   Need visual UI evidence    → screenshot()
   Enter text                 → fill(target, text)
   Activate an element        → click(target)
   Navigate to another URL    → navigate(url)
   ```

3. **Check the tool result.**  
   Browser tools return execution information. Use the result to determine whether the action succeeded.

4. **Do not assume success.**  
   Calling a tool is not evidence that the intended application behavior occurred.

5. **Do not use stale targets.**  
   If an action changes the UI, re-observe before using targets from the previous screen.

6. **Prefer relevant actions.**  
   Do not click or navigate through unrelated parts of the application.

7. **Do not invent elements.**  
   Actions should be based on elements discovered from the current UI.

8. **Use screenshots when they add useful information.**  
   Do not request screenshots unnecessarily when structured UI observation already provides enough information.

9. **Keep observation focused.**  
   Preserve information useful for the current test rather than unnecessary raw UI/context data.

10. **Stay within the provided browser interface.**  
    Do not invent new browser tools when the required operation can be performed using the agreed interface.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Retry Rules

<<<<<<< HEAD
=======
Retry only when recovery is allowed by the graph.

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
When an action fails:

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
Observe current UI again
      ↓
Choose a current observed target
      ↓
Resolve its current coordinates
=======
Observe UI again
      ↓
Choose corrected action
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
      ↓
Execute
```

<<<<<<< HEAD
If retries are exhausted:
=======
If no retry is available:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
Action failed
      ↓
<<<<<<< HEAD
No retries
=======
Retries available?
      ↓
No
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
      ↓
FAIL
```

<<<<<<< HEAD
Do not repeat the exact same failed action without new evidence.

Do not maintain an independent retry counter inside the skill.
=======
During recovery:

- do not repeat exactly the same failed action without a reason,
- inspect again when the UI may have changed,
- reconsider the target element,
- reconsider the current step,
- update the current step and/or plan when necessary,
- retain valid completed steps,
- and avoid infinite retry loops.

The graph determines whether retries remain available. This skill must not invent its own independent retry counter.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Stop Conditions

<<<<<<< HEAD
Stop normal execution when:

1. all planned steps are complete,
2. output generation should begin,
3. execution failed and no retry remains,
4. the graph routes to FAIL,
5. continuing would require inventing a target, selector, coordinate, or unsupported browser operation.
=======
Stop normal action execution when any of the following is true:

1. all planned steps have been completed and output generation should begin,
2. the required Scenario 1 execution flow has been completed and output generation can proceed,
3. execution has failed and no retry is available,
4. the graph routes execution to FAIL,
5. continuing would require inventing unavailable UI information or unsupported tools.

Do not continue interacting with the application after all required Scenario 1 steps have been completed unless another planned step remains.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Failure Conditions

Treat the current execution path as unsuccessful when relevant conditions include:

<<<<<<< HEAD
- the required target cannot be reliably identified,
- the browser cannot obtain a usable current bounding box,
- coordinate-based interaction fails,
- clipboard-based text entry fails,
- the application is in an unexpected state,
- or recovery attempts are exhausted.

A failed individual action may still be recoverable through Reflect + Re-plan.
=======
- the requested target element cannot be reliably identified,
- a browser action returns an unsuccessful result,
- the application is in an unexpected state that prevents the current step,
- recovery attempts are no longer available.

A failed action and a failed complete test are not always the same thing.

A failed action may still be recoverable through Reflect + Re-plan when retries are available.

The complete run reaches FAIL when the graph determines that execution cannot continue.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Information to Preserve

<<<<<<< HEAD
Preserve information useful for continuing the graph and generating the final script, including:

- test intent,
- plan,
- current step,
- useful current UI observations,
- current observed target elements,
- next action,
- action result,
- executed actions,
- actual returned Agent Browser command strings,
- final generated output or partial result.

Do not introduce permanent state fields that are not part of the agreed `AgentState`.

=======
Preserve information that is useful for continuing the graph and generating the final script.

This includes, when relevant:

- the identified test intent,
- the current plan,
- the current step,
- useful current UI observations,
- relevant target elements,
- the selected next action,
- the result of executed actions,
- the successful sequence needed for script generation,
- and the final generated output or partial result.

Do not introduce permanent state fields that are not part of the agreed `AgentState`.

Avoid keeping unnecessary UI details, screenshots, duplicated observations, or unrelated information in model context when they are no longer useful.

>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
---

## Completion Criteria

<<<<<<< HEAD
Scenario 1 is complete when:

- the requirement has been understood,
- an appropriate plan was executed,
- required UI targets were observed,
- target positions were resolved dynamically from current bounding boxes,
- browser actions were executed through physical mouse / clipboard commands,
- no required execution steps remain,
- and the final behavior can be validated.
=======
Scenario 1 testing is complete when:

- the testing requirement has been understood,
- an appropriate plan has been executed,
- required UI targets were observed rather than invented,
- browser actions required for the flow succeeded or were successfully recovered,
- no required execution steps remain,
- and a full test script can be generated from the successfully established flow.

Successful execution of the required planned steps, together with the collected UI/action information, is sufficient to proceed to Scenario 1 output generation. Actual-versus-expected verification is reserved for Scenario 2 maintenance.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

---

## Output Requirements

<<<<<<< HEAD
For successful Scenario 1 execution:
=======
During graph execution, produce information compatible with the state field or fields owned by the current LangGraph node.

Do not invent additional persistent AgentState fields unless the team explicitly changes the agreed state definition.

For Scenario 1, the final successful output is:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
generated_output
```

<<<<<<< HEAD
must contain the real Agent Browser CLI sequence established during execution.

The final script should reflect:

1. the tested requirement,
2. the successful action order,
3. the test data used,
4. coordinate-based physical mouse interaction,
5. clipboard-based text entry for fill actions,
6. and final validation behavior.

The final Scenario 1 script must include the dynamically generated `agent-browser eval` runtime validation command with JavaScript `if / else` that returns `PASS` or `FAIL`.

For click/fill actions, do not output static refs, CSS selectors, or XPath as final locators.

If execution reaches FAIL, preserve:
=======
containing the complete generated functional test script.

The generated test should reflect:

1. the tested requirement,
2. the successful action sequence,
3. the test data used where applicable,
4. the observed UI targets required by the flow,
5. and verification/assertion of the expected final behavior.

If execution reaches FAIL, return the available:
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2

```text
partial_result
```

<<<<<<< HEAD
instead of presenting an incomplete flow as successful.
=======
instead of presenting an incomplete test as successful.
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
