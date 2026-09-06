# Exploratory Testing Skill

## Purpose

This skill guides the agent in **Scenario 3 — Exploratory Testing / Autonomous Bug Discovery**.

Unlike Scenario 1 (build a test from a stated requirement) or Scenario 2 (repair an existing test), this scenario gives the agent no requirement and no existing script — only an application to explore. The agent must think like an experienced QA tester and decide, entirely on its own, which behaviors are worth probing on this specific application.

## When to Use

Use this skill when `task_mode` is `explore`: no `requirement` and no `existing_script` were provided, only an `app_path`.

## Mindset

Do not rely on a fixed checklist of "standard" test ideas. Instead, base every idea on what you actually observe on this page: its fields, their types, their constraints, and their apparent purpose.

For each element you observe, reason about it directly:
- What is this field's evident purpose, and what would a real user realistically enter?
- What would happen if the value given to it violated what its type or purpose implies?
- What would a skeptical, experienced tester specifically worry about for *this* element, given what it is?

Two different applications should lead you to different ideas, because the ideas come from what you actually see, not from a fixed list applied identically everywhere. Prefer a small set of high-value, well-reasoned cases over a long list of generic ones.

## Workflow

1. **Observe first.** Take a snapshot/screenshot of the app before proposing anything. Your ideas must come from elements you actually observed — never propose a case for a field or button you have not seen.
2. **Reason case-by-case.** For each observed element worth probing, explain to yourself (briefly) why it is worth probing, grounded in what that specific element is.
3. **Propose a short list of scenarios** (roughly 3-6), each with:
   - a one-line goal describing the case and what you are probing,
   - what a *correct* application should do in response.
4. **Execute each scenario** using the available browser actions (fill, click, navigate), one at a time.
5. **Observe the actual outcome** after each scenario (snapshot/screenshot).
6. **Judge the result:**
   - `handled correctly` — the app responded safely (e.g. validation message, submission blocked).
   - `bug found` — the app accepted invalid input, showed no feedback, crashed the flow, or otherwise misbehaved.
   - `inconclusive` — insufficient evidence to judge; do not guess.

## Rules

- Do not invent UI elements, error messages, or behavior that were not actually observed.
- Do not report a bug without an observed action + observed outcome as evidence.
- Every scenario must be traceable to a specific element you actually observed, and to your own reasoning about it — not to a predefined category.
- Each scenario should be independent and runnable on its own.

## Output Requirements

For successful Scenario 3 execution, produce a report where each explored case has:

1. the scenario tried,
2. the runnable Agent Browser command sequence for that case (same format as Scenario 1: lines prefixed with `agent-browser`, refs with `@`),
3. a one-line verdict: `HANDLED`, `BUG FOUND`, or `INCONCLUSIVE`, with a short reason grounded in the observed outcome.

Do not fabricate a bug to seem more useful, and do not mark something `HANDLED` without observed evidence.
