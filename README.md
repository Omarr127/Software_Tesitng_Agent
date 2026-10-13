# Software Testing Agent

A LangGraph-based AI agent for automated web testing.

The project uses AI, browser automation, reusable testing skills, and LangGraph to generate, execute, and maintain web test scripts.

## Project Scenarios

The project supports three main scenarios.

### Scenario 1 — Generate a Test from a Requirement

The user provides:

- A testing requirement
- An application URL or path

Example:

```powershell
py main.py --requirement "Test the login form with valid credentials" --app_path "http://127.0.0.1:5000"
```

The agent:

1. Opens the application.
2. Understands the requirement.
3. Observes the UI.
4. Creates a test plan.
5. Executes the required actions.
6. Verifies the behavior.
7. Generates the final test script.

---

### Scenario 2 — Maintain an Existing Test Script

The user provides:

- An existing test script
- The updated application path

Example:

```powershell
py main.py --existing_script "open http://127.0.0.1:5000
fill e2 Ahmed
click e3" --app_path "http://127.0.0.1:5050"
```

The agent:

1. Opens the updated application.
2. Reads the old test script.
3. Checks whether the old steps still work.
4. Detects changed or missing UI elements.
5. Finds replacement elements or flows.
6. Repairs the broken test steps.
7. Generates an updated test script.

This scenario provides self-healing test maintenance when the application changes.

---

### Scenario 3 — General / Autonomous Testing

The user provides only:

- The application URL or path

No testing requirement is required.

Example:

```powershell
py main.py --app_path "http://127.0.0.1:5000"
```

The agent automatically explores the application and discovers useful test cases.

It can:

1. Open the application.
2. Inspect the visible UI.
3. Discover pages, forms, buttons, links, and important user flows.
4. Identify possible functional test cases.
5. Prioritize important flows such as:
   - Login
   - Sign up
   - Search
   - Navigation
   - Form validation
   - Create / edit / delete flows
6. Execute selected test cases.
7. Verify the application behavior.
8. Generate one or more reusable test scripts.

Example output:

```text
Generated Tests

Test 1: Login with valid credentials
Test 2: Login with invalid credentials
Test 3: Empty login form validation
Test 4: Navigation to registration page
Test 5: Sign-up form validation
```

Scenario 3 is different from Scenario 1 because the agent creates its own testing goals instead of receiving a requirement from the user.

A useful name for this mode is:

**Autonomous Test Discovery**

---

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

## Main Components

| Component | Purpose |
|---|---|
| `main.py` | Entry point and project integration |
| `state.py` | Shared LangGraph agent state |
| `graph.py` | Builds and connects the LangGraph workflow |
| `nodes/` | Agent reasoning and execution nodes |
| `tools/` | Browser automation tools |
| `skills/` | Reusable testing instructions |
| `prompts/` | Prompts used by the agent |
| `metrics/` | Runtime and model usage measurements |
| `samples/` | Example test cases and demo applications |

---

## How the Agent Works

```text
User Input
   ↓
main.py
   ↓
Classify Scenario
   ↓
LangGraph Workflow
   ↓
Understand / Discover Testing Goal
   ↓
Create Test Plan
   ↓
Observe Application UI
   ↓
Decide Next Action
   ↓
Execute Browser Action
   ↓
Verify Result
   ↓
Reflect / Re-plan
   ↓
Generate Test Script
```

For Scenario 3, the agent adds an exploration step:

```text
Application Path
   ↓
Explore Application
   ↓
Discover Test Opportunities
   ↓
Prioritize Test Cases
   ↓
Execute Tests
   ↓
Generate Test Scripts
```

---

## Agent Nodes

The workflow can include:

- Receive and Classify Input
- Understand Task
- Explore Application
- Discover Test Cases
- Create Plan
- Observe and Analyze UI
- Decide Action
- Execute Action
- Verify Behavior
- Reflect and Re-plan
- Generate Output

Not every scenario needs every node.

---

## Browser Tools

The browser layer provides functions such as:

```python
open_app(path)
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)
```

A common response format is:

```python
{
    "success": True,
    "output": "...",
    "error": ""
}
```

---

## Skills

Testing behavior is stored in reusable skills.

Example:

```python
load_skill("e2e_test")
```

Possible skill structure:

```text
skills/
├── e2e_test/
│   └── SKILL.md
├── maintenance_test/
│   └── SKILL.md
└── general_test/
    └── SKILL.md
```

Suggested purpose:

```text
e2e_test
→ Scenario 1

maintenance_test
→ Scenario 2

general_test
→ Scenario 3
```

The `general_test` skill can contain rules for:

- Safe application exploration
- Discovering useful test cases
- Avoiding repeated actions
- Prioritizing important flows
- Form testing
- Navigation testing
- Validation testing
- Retry and recovery
- Test-script generation

---

## Running the Agent

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Scenario 1

```powershell
py main.py --requirement "Test the search functionality" --app_path "https://www.wikipedia.org/"
```

### Scenario 2

```powershell
py main.py --existing_script "open http://127.0.0.1:5000
fill e2 Ahmed
click e3" --app_path "http://127.0.0.1:5050"
```

### Scenario 3

```powershell
py main.py --app_path "http://127.0.0.1:5000"
```

A simple classification rule can be:

```python
if existing_script:
    mode = "maintenance"
elif requirement:
    mode = "e2e"
else:
    mode = "general"
```

---

## Shared Interfaces

```python
# Browser tools
open_app(path)
snapshot()
screenshot()
click(target)
fill(target, text)
navigate(url)

# Skills
load_skill("e2e_test") -> str
load_skill("maintenance_test") -> str
load_skill("general_test") -> str

# LangGraph
build_graph() -> compiled_graph

# Scenario runners
run_scenario1(requirement, app_path) -> final_state
run_scenario2(existing_script, app_path) -> final_state
run_scenario3(app_path) -> final_state
```

---

## Scenario 3 Safety and Scope

Autonomous exploration should have limits so the agent does not explore forever or perform dangerous actions.

Useful limits include:

```text
Maximum pages: 10
Maximum actions per test: 15
Maximum generated tests: 5
Maximum retries: 2
```

The agent should avoid destructive actions such as:

- Deleting real data
- Making purchases
- Sending real messages
- Changing important account settings

unless those actions are explicitly allowed in the testing environment.

---

## Team Responsibilities

### Member 1 — Browser / Execution Layer

Owns:

```text
tools/
```

Responsibilities:

- Set up Agent Browser.
- Connect browser commands to Python.
- Implement browser interactions.
- Return consistent results.

### Member 2 — Skills + Dynamic Loading

Owns:

```text
skills/
```

Responsibilities:

- Create testing skills for each scenario.
- Implement dynamic skill loading.
- Define testing, retry, and recovery rules.

### Member 3 — LangGraph Core

Owns:

```text
state.py
graph.py
nodes/
```

Responsibilities:

- Define `AgentState`.
- Implement LangGraph nodes.
- Connect workflow edges.
- Integrate browser tools and skills.
- Handle screenshots and vision-model flow.

### Member 4 — Integration + Metrics + Testing

Owns:

```text
main.py
metrics/
```

Responsibilities:

- Integrate all components.
- Implement scenario selection.
- Run tests end to end.
- Measure runtime and model usage.
- Prepare the final demo.

---

## Metrics

The project can measure:

- Prompt and context size
- Token usage
- Number of screenshots
- Number of model calls
- Number of browser actions
- Number of generated test cases
- Node execution time
- Total execution time

---

## Git Workflow

Each team member should work on a separate branch.

Suggested branches:

```text
member1-browser-tools
member2-skills
member3-langgraph
member4-integration
```

Recommended workflow:

```text
Pull latest main
    ↓
Work on your branch
    ↓
Commit changes
    ↓
Push branch
    ↓
Create Pull Request
    ↓
Review and merge
```

---

## Future Improvements

Possible future improvements include:

- Better autonomous test discovery
- UI-change detection
- Automatic test repair
- Test prioritization
- More advanced form validation testing
- Test coverage scoring
- Duplicate-test detection
- Improved retry and recovery
- Streamlit user interface
- Test reports and dashboards
- More reliable self-healing browser tests

---

## Summary

The Software Testing Agent supports three levels of automation:

```text
Scenario 1
Requirement + App Path
→ Generate a test script

Scenario 2
Existing Script + Updated App Path
→ Repair the test script

Scenario 3
App Path only
→ Discover tests and generate test scripts automatically
```

The project combines:

**LangGraph + LLM/VLM + Browser Automation + Testing Skills**

to create an AI testing agent that can generate, execute, discover, and maintain functional web tests.
