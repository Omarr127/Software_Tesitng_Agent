# E2E Testing Skill

## Purpose

This skill provides reusable instructions for performing Scenario 1 end-to-end functional web testing.

Its purpose is to guide the agent in how to:

- understand the testing objective,
- inspect the current user interface,
- identify relevant UI elements,
- choose and execute appropriate browser actions,
- observe the application after actions,
- recover from failed actions when retries are available,
- complete the required interaction flow,
- and generate a complete functional test script from the successful testing flow.

This skill defines **how the agent should perform E2E testing**. Browser tools provide the capabilities for interacting with the application, while the LangGraph controls when each stage of the workflow is executed.

---

## When to Use

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

---

## Inputs

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

---

## Testing Objective

The objective is not merely to execute browser actions.

The objective is to understand and execute the requested functional flow and to collect enough reliable information to generate a usable initial test script.

An action such as clicking a button or filling an input does not by itself mean that the current step succeeded.

For Scenario 1, completion is based on successfully carrying out the required planned steps, handling failures through the graph when necessary, and collecting enough reliable information to generate the initial test script. Actual-versus-expected behavior verification belongs to Scenario 2 maintenance.

---

## Workflow

### 1. Inspect

Inspect the current application state before choosing an interaction.

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

---

### 2. Decide

Read the current test step and the latest UI observation before selecting the next action.

The selected action should:

- directly support the current testing objective,
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

---

### 3. Act

Execute the selected action using the appropriate browser tool.

Available browser capabilities include:

```text
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)
```

Application opening or runtime initialization may use `open_app(path)` outside the LangGraph execution boundary.

For an action:

- use `fill(target, text)` when text must be entered,
- use `click(target)` when an identified interactive element must be activated,
- use `navigate(url)` when navigation to another URL is required,
- use observation tools instead of interaction tools when more UI information is needed.

After execution, inspect the returned result.

Do not assume that a browser action succeeded merely because the tool was called.

The execution result must be used to determine whether the action was successful.

---

### 4. Re-inspect

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

```text
Observe
→ Decide
→ Execute
→ Check action result
→ Observe updated UI
→ Decide next action
```

Do not rely on stale UI information after an action that may have changed the page.

The latest observation should replace or update outdated UI assumptions with information useful for the current step.

---

### 5. Complete Scenario 1 Execution

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

---

### 6. Recover / Re-plan

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

---

### 7. Complete Testing

Execution is ready for final output only when:

1. the required testing steps have been completed,
2. there are no remaining execution steps,
3. required UI targets were observed rather than invented,
4. browser actions required for the flow succeeded or were successfully recovered,
5. and enough reliable information has been collected to generate the initial functional test script.

For Scenario 1, do not route to final behavior verification after the planned steps are complete. The graph proceeds to Generate Output.

If execution cannot continue and no retry is available, stop testing and allow the graph to return the available partial result through the FAIL path.

---

### 8. Generate Test Script

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

---

## Tool Usage Rules

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

---

## Retry Rules

Retry only when recovery is allowed by the graph.

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
Observe UI again
      ↓
Choose corrected action
      ↓
Execute
```

If no retry is available:

```text
Action failed
      ↓
Retries available?
      ↓
No
      ↓
FAIL
```

During recovery:

- do not repeat exactly the same failed action without a reason,
- inspect again when the UI may have changed,
- reconsider the target element,
- reconsider the current step,
- update the current step and/or plan when necessary,
- retain valid completed steps,
- and avoid infinite retry loops.

The graph determines whether retries remain available. This skill must not invent its own independent retry counter.

---

## Stop Conditions

Stop normal action execution when any of the following is true:

1. all planned steps have been completed and output generation should begin,
2. the required Scenario 1 execution flow has been completed and output generation can proceed,
3. execution has failed and no retry is available,
4. the graph routes execution to FAIL,
5. continuing would require inventing unavailable UI information or unsupported tools.

Do not continue interacting with the application after all required Scenario 1 steps have been completed unless another planned step remains.

---

## Failure Conditions

Treat the current execution path as unsuccessful when relevant conditions include:

- the requested target element cannot be reliably identified,
- a browser action returns an unsuccessful result,
- the application is in an unexpected state that prevents the current step,
- recovery attempts are no longer available.

A failed action and a failed complete test are not always the same thing.

A failed action may still be recoverable through Reflect + Re-plan when retries are available.

The complete run reaches FAIL when the graph determines that execution cannot continue.

---

## Information to Preserve

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

---

## Completion Criteria

Scenario 1 testing is complete when:

- the testing requirement has been understood,
- an appropriate plan has been executed,
- required UI targets were observed rather than invented,
- browser actions required for the flow succeeded or were successfully recovered,
- no required execution steps remain,
- and a full test script can be generated from the successfully established flow.

Successful execution of the required planned steps, together with the collected UI/action information, is sufficient to proceed to Scenario 1 output generation. Actual-versus-expected verification is reserved for Scenario 2 maintenance.

---

## Output Requirements

During graph execution, produce information compatible with the state field or fields owned by the current LangGraph node.

Do not invent additional persistent AgentState fields unless the team explicitly changes the agreed state definition.

For Scenario 1, the final successful output is:

```text
generated_output
```

containing the complete generated functional test script.

The generated test should reflect:

1. the tested requirement,
2. the successful action sequence,
3. the test data used where applicable,
4. the observed UI targets required by the flow,
5. and verification/assertion of the expected final behavior.

If execution reaches FAIL, return the available:

```text
partial_result
```

instead of presenting an incomplete test as successful.
