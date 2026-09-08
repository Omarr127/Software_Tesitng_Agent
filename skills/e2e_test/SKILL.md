# E2E Testing Skill

## Purpose

This skill provides reusable instructions for performing **Scenario 1 — New End-to-End Functional Test Generation**.

Its purpose is to guide the agent in how to:

- understand the testing objective,
- inspect the current user interface,
- identify relevant UI elements,
- choose appropriate browser actions,
- dynamically resolve the current position of each target element,
- execute interactions through physical mouse and clipboard Agent Browser commands,
- observe the application after actions,
- recover from failed actions when retries are available,
- complete the required functional flow,
- and generate a runnable Agent Browser command script from the successful testing flow.

This skill defines **how the agent should perform Scenario 1 E2E testing**.

Browser tools provide the actual interaction capabilities. LangGraph controls when each stage of the workflow is executed.

---

## When to Use

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

---

## Inputs

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

---

## Testing Objective

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

---

## Workflow

### 1. Inspect

Inspect the current application state before choosing an interaction.

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

---

### 2. Decide

Read the current test step and the latest UI observation.

Choose exactly one appropriate next action.

The selected action should:

- directly support the current testing objective,
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

---

### 3. Act

Execute the selected action through the existing browser-tool interface.

Available capabilities include:

```text
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)
```

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

---

### 4. Re-inspect

After a successful action that may change the UI, observe again before choosing the next action.

Follow:

```text
Observe
→ Decide
→ Execute
→ Check result
→ Observe updated UI
→ Decide next action
```

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

---

### 5. Complete Scenario 1 Execution

When all planned execution steps are complete, the graph may proceed to output generation and final validation.

Successful Scenario 1 execution means:

- the required steps were executed successfully or recovered successfully,
- no required steps remain,
- current UI targets were observed rather than invented,
- physical browser interactions were generated from current element coordinates,
- and enough reliable information exists to validate and generate the final output.

---

### 6. Recover / Re-plan

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

---

### 7. Complete Testing

Execution is ready for final output only when:

1. all required testing steps are complete,
2. no required execution steps remain,
3. required UI targets were observed,
4. browser actions succeeded or were successfully recovered,
5. coordinate-based physical commands were produced by the execution layer,
6. and enough reliable evidence exists for final output and validation.

If execution cannot continue and no retry remains, stop and preserve the partial result.

---

### 8. Generate Test Script

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

---

## Tool Usage Rules

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

---

## Retry Rules

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
Observe current UI again
      ↓
Choose a current observed target
      ↓
Resolve its current coordinates
      ↓
Execute
```

If retries are exhausted:

```text
Action failed
      ↓
No retries
      ↓
FAIL
```

Do not repeat the exact same failed action without new evidence.

Do not maintain an independent retry counter inside the skill.

---

## Stop Conditions

Stop normal execution when:

1. all planned steps are complete,
2. output generation should begin,
3. execution failed and no retry remains,
4. the graph routes to FAIL,
5. continuing would require inventing a target, selector, coordinate, or unsupported browser operation.

---

## Failure Conditions

Treat the current execution path as unsuccessful when relevant conditions include:

- the required target cannot be reliably identified,
- the browser cannot obtain a usable current bounding box,
- coordinate-based interaction fails,
- clipboard-based text entry fails,
- the application is in an unexpected state,
- or recovery attempts are exhausted.

A failed individual action may still be recoverable through Reflect + Re-plan.

---

## Information to Preserve

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

---

## Completion Criteria

Scenario 1 is complete when:

- the requirement has been understood,
- an appropriate plan was executed,
- required UI targets were observed,
- target positions were resolved dynamically from current bounding boxes,
- browser actions were executed through physical mouse / clipboard commands,
- no required execution steps remain,
- and the final behavior can be validated.

---

## Output Requirements

For successful Scenario 1 execution:

```text
generated_output
```

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

```text
partial_result
```

instead of presenting an incomplete flow as successful.
