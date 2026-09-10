from pathlib import Path
import re


# --------------------------------------------------
# Skills directory
# --------------------------------------------------

_SKILLS_DIR = Path(__file__).resolve().parent


# --------------------------------------------------
# Map each task mode to its skill folder
# --------------------------------------------------

_SKILL_BY_TASK_MODE = {
    "new_test": "e2e_test",
<<<<<<< HEAD
    "maintenance": "maintenance_test",
    "explore": "exploratory_test"
=======
    "maintenance": "maintenance_test"
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
}


# --------------------------------------------------
# Node-specific SKILL.md sections
#
# SKILL.md remains the single source of truth.
#
# This mapping contains ONLY section names.
# It does not duplicate skill instructions.
#
# The loader reads the appropriate SKILL.md and
# dynamically extracts only the sections required
# by each LangGraph node.
# --------------------------------------------------

_NODE_CONTEXT = {

    # ==================================================
    # Scenario 1 - New Test
    # ==================================================
"new_test": {

    "understand": [
        "Testing Objective"
    ],

    "plan": [
        "Testing Objective"
    ],

    "observe": [
        "1. Inspect"
    ],

    "decide": [
        "2. Decide"
    ],

    "reflect": [
        "6. Recover / Re-plan"
    ],

    "generate": [
        "8. Generate Test Script"
    ]
},



    # ==================================================
    # Scenario 2 - Maintenance
    # ==================================================

    "maintenance": {

        "understand": [
            "When to Use",
            "1. Understand the Existing Test",
            "Maintenance Objective",
            "Core Maintenance Principles"
        ],

        "plan": [
            "3. Create a Maintenance Plan",
            "Maintenance Objective",
            "Core Maintenance Principles"
        ],

        "observe": [
            "4. Inspect the Updated Application",
            "5. Compare Original Intent with Current UI",
            "Detecting a Broken Test Step",
            "Tool Usage Rules"
        ],

        "decide": [
            "6. Decide the Next Action",
            "Self-Healing Rules",
            "Tool Usage Rules"
        ],

        "reflect": [
            "Reflection and Re-Planning",
            "Retry Rules",
            "Failure Conditions"
        ],

        "verify": [
            "Verification",
            "Verification Sources",
            "Verification Outcomes",
            "Distinguishing Test Repair from Application Failure",
            "Expected Behavior Rules"
        ],

        "generate": [
            "Patch Strategy",
            "Test Script Generation Instructions",
            "Selector Generation Rules",
            "Expected Behavior Rules",
            "Completion Criteria",
            "Output Requirements"
        ]
<<<<<<< HEAD
    },


    # ==================================================
    # Scenario 3 - Explore
    # ==================================================

    "explore": {

        "understand": [
            "Purpose",
            "Mindset"
        ],

        "plan": [
            "Purpose",
            "Mindset",
            "Workflow"
        ],

        "observe": [
            "Workflow",
            "Rules"
        ],

        "decide": [
            "Workflow",
            "Rules"
        ],

        "reflect": [
            "Rules"
        ],

        "generate": [
            "Output Requirements"
        ]
    }

=======
    }
>>>>>>> 7de6a10e48b0b5a56661fe83a54f9e299779b3d2
}


# --------------------------------------------------
# Load complete skill
# --------------------------------------------------

def load_skill(name: str) -> str:
    """
    Load a skill's SKILL.md file and return its
    complete contents as a string.
    """

    # --------------------------------------------------
    # 1. Validate input type
    # --------------------------------------------------

    if not isinstance(name, str):
        raise TypeError(
            "Skill name must be a string."
        )

    # --------------------------------------------------
    # 2. Remove unnecessary spaces
    # --------------------------------------------------

    name = name.strip()

    if not name:
        raise ValueError(
            "Skill name cannot be empty."
        )

    # --------------------------------------------------
    # 3. Prevent unsafe paths
    # --------------------------------------------------

    if (
        Path(name).name != name
        or name in {".", ".."}
    ):
        raise ValueError(
            "Skill name must be a simple directory name."
        )

    # --------------------------------------------------
    # 4. Build skill directory path
    # --------------------------------------------------

    skill_dir = _SKILLS_DIR / name

    # --------------------------------------------------
    # 5. Build SKILL.md path
    # --------------------------------------------------

    skill_file = skill_dir / "SKILL.md"

    # --------------------------------------------------
    # 6. Make sure skill directory exists
    # --------------------------------------------------

    if not skill_dir.is_dir():
        raise FileNotFoundError(
            f"Skill not found: {name}"
        )

    # --------------------------------------------------
    # 7. Make sure SKILL.md exists
    # --------------------------------------------------

    if not skill_file.is_file():
        raise FileNotFoundError(
            f"SKILL.md not found for skill: {name}"
        )

    # --------------------------------------------------
    # 8. Read skill content
    # --------------------------------------------------

    content = skill_file.read_text(
        encoding="utf-8"
    ).strip()

    # --------------------------------------------------
    # 9. Make sure skill is not empty
    # --------------------------------------------------

    if not content:
        raise ValueError(
            f"SKILL.md is empty for skill: {name}"
        )

    # --------------------------------------------------
    # 10. Return complete skill
    # --------------------------------------------------

    return content


# --------------------------------------------------
# Load skill based on task mode
# --------------------------------------------------

def load_skill_for_mode(task_mode: str) -> str:
    """
    Dynamically load the complete skill based on
    task mode.

    Mapping:

        new_test
            -> skills/e2e_test/SKILL.md

        maintenance
            -> skills/maintenance_test/SKILL.md

    This function remains available for compatibility
    with existing code.

    Node implementations should use:

        load_context_for_node()

    when only node-specific context is required.
    """

    # --------------------------------------------------
    # 1. Validate task mode type
    # --------------------------------------------------

    if not isinstance(task_mode, str):
        raise TypeError(
            "Task mode must be a string."
        )

    # --------------------------------------------------
    # 2. Normalize task mode
    # --------------------------------------------------

    task_mode = task_mode.strip()

    if not task_mode:
        raise ValueError(
            "Task mode cannot be empty."
        )

    # --------------------------------------------------
    # 3. Find corresponding skill
    # --------------------------------------------------

    skill_name = _SKILL_BY_TASK_MODE.get(
        task_mode
    )

    # --------------------------------------------------
    # 4. Reject unsupported task modes
    # --------------------------------------------------

    if skill_name is None:
        raise ValueError(
            f"Unsupported task mode: {task_mode}"
        )

    # --------------------------------------------------
    # 5. Load complete skill
    # --------------------------------------------------

    return load_skill(
        skill_name
    )


# --------------------------------------------------
# Extract a Markdown section
# --------------------------------------------------

def _extract_section(
    content: str,
    section_name: str
) -> str:
    """
    Extract one Markdown heading section.

    The returned section includes:

    - the requested heading
    - its content
    - child subsections

    Extraction stops at the next heading with
    the same or higher heading level.
    """

    lines = content.splitlines()

    target_index = None
    target_level = None

    pattern = re.compile(
        r"^(#+)\s+(.*?)\s*$"
    )

    # --------------------------------------------------
    # Find requested heading
    # --------------------------------------------------

    for index, line in enumerate(lines):

        match = pattern.match(line)

        if not match:
            continue

        heading_level = len(
            match.group(1)
        )

        heading_name = match.group(2).strip()

        if heading_name.lower() == section_name.lower():

            target_index = index
            target_level = heading_level

            break

    # --------------------------------------------------
    # Section not found
    # --------------------------------------------------

    if target_index is None:
        return ""

    # --------------------------------------------------
    # Find section end
    # --------------------------------------------------

    end_index = len(lines)

    for index in range(
        target_index + 1,
        len(lines)
    ):

        match = pattern.match(
            lines[index]
        )

        if not match:
            continue

        heading_level = len(
            match.group(1)
        )

        # Stop at same-level or higher heading.
        if heading_level <= target_level:

            end_index = index

            break

    # --------------------------------------------------
    # Return section
    # --------------------------------------------------

    section = "\n".join(
        lines[target_index:end_index]
    ).strip()

    return section


# --------------------------------------------------
# Dynamically load node-specific context
# --------------------------------------------------

def load_context_for_node(
    task_mode: str,
    node_name: str
) -> str:
    """
    Dynamically load only the SKILL.md sections
    required by a specific LangGraph node.

    The flow is:

        task_mode
            ↓
        skill folder
            ↓
        SKILL.md
            ↓
        node section mapping
            ↓
        selected sections
            ↓
        model context

    Example:

        load_context_for_node(
            "new_test",
            "observe"
        )

    loads only the Observe-related sections
    from skills/e2e_test/SKILL.md.
    """

    # --------------------------------------------------
    # 1. Validate task mode
    # --------------------------------------------------

    if not isinstance(task_mode, str):
        raise TypeError(
            "Task mode must be a string."
        )

    task_mode = task_mode.strip()

    if not task_mode:
        raise ValueError(
            "Task mode cannot be empty."
        )

    # --------------------------------------------------
    # 2. Validate node name
    # --------------------------------------------------

    if not isinstance(node_name, str):
        raise TypeError(
            "Node name must be a string."
        )

    node_name = node_name.strip()

    if not node_name:
        raise ValueError(
            "Node name cannot be empty."
        )

    # --------------------------------------------------
    # 3. Validate task mode
    # --------------------------------------------------

    if task_mode not in _SKILL_BY_TASK_MODE:

        raise ValueError(
            f"Unsupported task mode: {task_mode}"
        )

    # --------------------------------------------------
    # 4. Find node section mapping
    # --------------------------------------------------

    task_context = _NODE_CONTEXT.get(
        task_mode
    )

    if task_context is None:

        raise ValueError(
            f"No node context configuration found "
            f"for task mode: {task_mode}"
        )

    # --------------------------------------------------
    # 5. Find requested node
    # --------------------------------------------------

    section_names = task_context.get(
        node_name
    )

    if section_names is None:

        raise ValueError(
            f"No context configuration found "
            f"for node '{node_name}' "
            f"in task mode '{task_mode}'"
        )

    # --------------------------------------------------
    # 6. Make sure section configuration is valid
    # --------------------------------------------------

    if not isinstance(section_names, list):

        raise TypeError(
            f"Context configuration for "
            f"'{task_mode}/{node_name}' "
            f"must be a list of section names."
        )

    if not section_names:

        raise ValueError(
            f"No SKILL.md sections configured "
            f"for '{task_mode}/{node_name}'"
        )

    # --------------------------------------------------
    # 7. Load the actual SKILL.md
    #
    # This is important:
    #
    # The instructions are NOT duplicated here.
    #
    # The real content always comes from SKILL.md.
    # --------------------------------------------------

    skill = load_skill_for_mode(
        task_mode
    )

    # --------------------------------------------------
    # 8. Extract requested sections
    # --------------------------------------------------

    selected_sections = []

    missing_sections = []

    for section_name in section_names:

        if not isinstance(
            section_name,
            str
        ):
            continue

        section = _extract_section(
            skill,
            section_name
        )

        if section:

            selected_sections.append(
                section
            )

        else:

            missing_sections.append(
                section_name
            )

    # --------------------------------------------------
    # 9. Detect missing SKILL.md sections
    #
    # Do not silently send incomplete context.
    # --------------------------------------------------

    if missing_sections:

        raise ValueError(
            "The following SKILL.md sections were "
            f"not found for '{task_mode}/{node_name}': "
            + ", ".join(missing_sections)
        )

    # --------------------------------------------------
    # 10. Make sure context was found
    # --------------------------------------------------

    if not selected_sections:

        raise ValueError(
            f"No matching SKILL.md sections found "
            f"for node '{node_name}' "
            f"in task mode '{task_mode}'"
        )

    # --------------------------------------------------
    # 11. Combine selected sections
    # --------------------------------------------------

    context = "\n\n---\n\n".join(
        selected_sections
    )

    # --------------------------------------------------
    # 12. Return node-specific context
    # --------------------------------------------------

    return context