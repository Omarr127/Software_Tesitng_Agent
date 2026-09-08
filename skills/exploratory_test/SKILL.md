# Exploratory Testing Skill

## Purpose

This skill guides the agent in **Scenario 3 — Exploratory Testing / Autonomous Bug Discovery**.

Unlike Scenario 1, which starts from a requirement, and Scenario 2, which starts from an existing test, Scenario 3 may receive only an application path.

The agent must think like an experienced QA tester, inspect the real application, choose worthwhile cases from what it actually observes, execute those cases, and report evidence-based outcomes.

All click/fill execution must use the project's dynamic coordinate-location mechanism and physical Agent Browser mouse / clipboard commands.

---

## When to Use

Use this skill when:

```text
task_mode = explore
```

with no requirement and no existing script.

---

## Mindset

Do not apply a fixed generic checklist blindly.

Base every exploratory idea on what is actually observed on the current page:

- fields,
- field types,
- constraints,
- buttons,
- links,
- visible workflow,
- apparent purpose,
- and current page context.

Ask:

- What is this element for?
- What might a real user enter or do here?
- What input would violate its apparent purpose?
- What edge case is specifically valuable for this element?
- What visible response would indicate correct handling?

Prefer a small set of high-value cases over many generic cases.

---

## Dynamic Element Location Policy

Scenario 3 uses dynamic element discovery and coordinate-based physical execution.

Correct flow:

```text
Observe current page
        ↓
choose a real observed element
        ↓
use its temporary current ref internally
        ↓
browser tool requests CURRENT bounding box
        ↓
Python calculates current center coordinates
        ↓
physical mouse interaction
        ↓
clipboard input when text is required
```

### Refs are internal only

A current ref such as:

```text
@e3
```

may be used internally to identify the selected element.

It must not appear as the final click/fill locator in the generated exploratory script.

### Never invent coordinates

The model must never guess x/y positions.

Coordinates must come from the live bounding box of the current observed element.

### Never invent selectors

Do not invent CSS, XPath, IDs, or other static locator syntax.

### Re-observe between changing states

Exploratory cases may alter the page.

After meaningful UI changes or resets, use the latest observation and current refs.

Do not reuse stale refs from an earlier page state.

---

## Workflow

### 1. Observe First

Take a snapshot and/or screenshot before proposing cases.

Every case must come from elements actually observed.

Do not propose a case for a field or button that was not seen.

---

### 2. Reason Case-by-Case

For each element worth probing, reason briefly about why the case is valuable for that specific element.

Do not use a predefined list without grounding it in the actual page.

---

### 3. Propose a Short List of Cases

Create roughly 3–6 high-value cases.

Each case should have:

- a one-line goal,
- the specific observed element(s) involved,
- what is being probed,
- and what a correct application should visibly do.

Each case should be independent whenever possible.

---

### 4. Decide Actions from Current Observations

For each step:

- choose only currently observed elements,
- use only current refs internally,
- never invent a ref,
- never invent coordinates,
- never invent static selectors.

The execution layer will convert the current observed ref into current coordinates.

---

### 5. Execute Each Case

Use available browser actions:

```text
fill
click
navigate
```

For a click, physical execution should become:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
```

For text entry, physical execution should become:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "VALUE"
agent-browser clipboard paste
```

The model must not manually guess these coordinates.

The browser tools generate them from the current bounding box.

---

### 6. Observe the Actual Outcome

After each case, inspect the resulting UI using snapshot and/or screenshot.

Do not judge the result from the fact that commands executed.

Judge from actual visible or textual application evidence.

---

### 7. Judge the Result

Use one of:

```text
HANDLED
BUG FOUND
INCONCLUSIVE
```

#### HANDLED

Use when there is evidence that the application safely and correctly handled the tested case.

#### BUG FOUND

Use when observed evidence shows incorrect or unsafe behavior.

Examples may include accepting clearly invalid input when it should not, broken flow, crash-like behavior, or missing required handling.

Do not report a bug without observed evidence.

#### INCONCLUSIVE

Use when there is not enough evidence to decide.

Do not guess.

---

## Rules

- Do not invent UI elements.
- Do not invent error messages.
- Do not invent application behavior.
- Do not invent refs.
- Do not invent coordinates.
- Do not invent CSS/XPath selectors.
- Every case must be traceable to an actually observed element.
- Every verdict must be grounded in an observed action and observed outcome.
- Each case should be independent when possible.
- Re-observe after state changes.
- Use current bounding boxes for physical execution.
- Preserve the actual Agent Browser commands returned by execution.

---

## Multi-Page Exploration

When the graph permits page discovery:

- explore only allowed discovered pages,
- respect same-domain and configured page limits,
- observe each page before planning cases,
- treat refs as page-state-specific,
- dynamically resolve current coordinates separately on each page.

Do not assume an element's previous coordinates apply to another page or later page state.

---

## Output Requirements

For successful Scenario 3 execution, produce an exploratory report where each case includes:

1. the scenario tried,
2. the **actual runnable Agent Browser command sequence executed for that case**,
3. a one-line verdict:
   - `HANDLED`
   - `BUG FOUND`
   - `INCONCLUSIVE`
4. a short reason grounded in the observed outcome.

### Required command style

Click actions should appear as:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
```

Fill actions should appear as:

```text
agent-browser mouse move X Y
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write "VALUE"
agent-browser clipboard paste
```

### Forbidden final click/fill style

Do not reconstruct final exploratory commands as:

```text
agent-browser click @e5
agent-browser fill @e2 "VALUE"
```

Refs may exist internally for observation and execution targeting, but the final report must preserve the real coordinate/mouse/clipboard commands that were actually executed.

### Runtime Agent Browser Validation Per Case

After the actual Agent Browser command sequence for each exploratory case, the generated report must include a **case-specific runtime validation command executed by Agent Browser**.

The validation must be generated dynamically from:

- that case's goal,
- that case's executed actions,
- the observed resulting browser state,
- and the evidence used to judge that case.

Use an Agent Browser `eval` command whose JavaScript contains explicit conditional logic:

```text
agent-browser eval "(() => {
    if (RUNTIME_HANDLED_CONDITION) {
        return 'HANDLED';
    } else if (RUNTIME_BUG_CONDITION) {
        return 'BUG FOUND';
    } else {
        return 'INCONCLUSIVE';
    }
})()"
```

Requirements:

- generate a different validation condition when different cases require different evidence,
- do not use one fixed condition for every exploratory case,
- the validation must inspect browser state at runtime,
- the validation must be side-effect-free,
- do not click, fill, submit, navigate, mutate application state, or call application APIs during validation,
- do not use temporary Agent Browser refs in the final validation,
- do not invent application-specific CSS/XPath selectors,
- prefer semantic runtime signals grounded in actual observation, such as:
  - current URL or pathname,
  - form validity,
  - visible status or alert regions,
  - visible error/confirmation state,
  - enabled/disabled state,
  - DOM state actually observed for that case,
- do not rely on one universal hardcoded message,
- do not invent application-specific selectors such as `article`, `input[type=...]`, `.result`, `#success`, product-card classes, or other guessed page structures,
- prefer selector-free runtime state such as `document.body.innerText`, `location.href`, `location.pathname`, and native form validity,
- if a selector is genuinely needed, use only generic semantic selectors such as `:invalid`, `[role="status"]`, or `[role="alert"]`,
- exact text may be checked only when that exact text was actually observed and is meaningful evidence for the current case,
- return `HANDLED` only when runtime evidence shows correct handling,
- return `BUG FOUND` only when runtime evidence clearly shows incorrect behavior,
- return `INCONCLUSIVE` when the runtime evidence is insufficient.

The purpose is to make the final exploratory script validate each case at runtime using Agent Browser, while keeping the validation logic intelligent and case-specific.

Do not fabricate a bug to appear useful.

Do not mark a case `HANDLED` without observed evidence.
