# Software Testing Agent

LangGraph-based AI agent for automated web testing.

## Project Goal

The project has two scenarios:

- **Scenario 1:** Generate a new functional test script from a requirement and application path.
- **Scenario 2:** Maintain and repair an existing test script when the application changes.

The current focus is **Scenario 1**.

## Project Structure

```text
agent/
├── main.py
├── state.py
├── graph.py
├── nodes/
├── tools/
├── skills/
├── prompts/
├── metrics/
└── samples/
```

## Team Roles

### Member 1 — Browser / Execution Layer

**Owns:** `tools/`

Tasks:
- Set up and test Agent Browser.
- Connect Agent Browser commands to Python using `subprocess`.
- Implement:
  - `open_app(path)`
  - `snapshot()`
  - `screenshot()`
  - `click(target)`
  - `fill(target, text)`
  - `navigate(url)`
- Return a common result format such as:
  ```python
  {
      "success": True,
      "output": "...",
      "error": ""
  }
  ```

Handoff:
- Working browser tools that LangGraph nodes can call.

---

### Member 2 — Skills + Dynamic Loading

**Owns:** `skills/`

Tasks:
- Review the provided E2E testing video and GitHub skill.
- Create the Scenario 1 E2E testing skill.
- Include useful instructions such as:
  - prompts/instructions
  - testing steps
  - tool-use rules
  - retry/recovery rules
  - output format
- Implement dynamic loading, for example:
  ```python
  load_skill("e2e_test")
  ```
- Make the skill available to the relevant LangGraph node prompts.

Handoff:
- `SKILL.md`
- Skill-loading logic.

---

### Member 3 — LangGraph Core

**Owns:** `state.py`, `graph.py`, and `nodes/`

Tasks:
- Implement the agreed `AgentState`.
- Implement the LangGraph nodes:
  - Receive + Classify Input
  - Understand Task
  - Create Plan
  - Observe + Analyze UI
  - Decide Action
  - Execute Action
  - Verify Behavior for Scenario 2
  - Reflect + Re-plan
  - Generate Output
- Connect the nodes with normal and conditional edges.
- Use Member 1 browser tools.
- Use Member 2 skill instructions.
- Handle screenshot/VLM flow inside the relevant nodes.
- Export the LangGraph visualization.

Handoff:
- Runnable compiled LangGraph.

---

### Member 4 — Integration + Context Engineering + Testing

**Owns:** `main.py`, `metrics/`, and final integration.

Tasks:
- Connect all team components.
- Create `main.py` to receive:
  - requirement
  - application path
- Run Scenario 1 end-to-end.
- Test on simple Sign Up and Search examples.
- Measure:
  - prompt/context size
  - token usage
  - screenshots/images
  - model calls
  - node execution time
  - total run time
- Prepare the final demo and report integration problems to the correct member.

Handoff:
- Working Scenario 1 demo.
- Generated test script.
- Basic metrics/context report.

## Shared Interfaces

The team should keep these function names unless everyone agrees to change them.

```python
# Member 1
open_app(path)
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)

# Member 2
load_skill("e2e_test") -> str

# Member 3
build_graph() -> compiled graph

# Member 4
run_scenario1(requirement, app_path) -> final_state
```

## How the Parts Connect

```text
main.py
   ↓
graph.py
   ↓
nodes/
   ↓
state.py + tools/ + skills/ + prompts/
   ↓
Browser / VLM
   ↓
Final generated test script

metrics/
→ measures context and runtime information
```

## Git Workflow

Each member should work on a separate branch.

Suggested branches:

```text
member1-browser-tools
member2-skills
member3-langgraph
member4-integration
```

Workflow:

```text
Pull latest main
→ work on your branch
→ commit changes
→ push branch
→ create Pull Request
→ review and merge
```


Scenario 2 will add more work later for script maintenance, UI changes, repair, and self-healing.
