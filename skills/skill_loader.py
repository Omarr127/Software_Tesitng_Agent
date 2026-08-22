from pathlib import Path


_SKILLS_DIR = Path(__file__).resolve().parent


def load_skill(name: str) -> str:
    """
    Load a skill's SKILL.md file and return its contents as a string.

    Example:
        skill_text = load_skill("e2e_test")

    Args:
        name: Skill directory name inside the skills/ folder.

    Returns:
        The full SKILL.md content as a string.

    Raises:
        TypeError: If name is not a string.
        ValueError: If name is empty or contains unsafe path characters.
        FileNotFoundError: If the skill directory or SKILL.md file does not exist.
    """
    if not isinstance(name, str):
        raise TypeError("Skill name must be a string.")

    name = name.strip()
    if not name:
        raise ValueError("Skill name cannot be empty.")

    # Skills are loaded by directory name only.
    # This prevents path traversal such as "../other_folder".
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError("Skill name must be a simple directory name.")

    skill_dir = _SKILLS_DIR / name
    skill_file = skill_dir / "SKILL.md"

    if not skill_dir.is_dir():
        raise FileNotFoundError(f"Skill not found: {name}")

    if not skill_file.is_file():
        raise FileNotFoundError(
            f"SKILL.md not found for skill: {name}"
        )

    content = skill_file.read_text(encoding="utf-8").strip()

    if not content:
        raise ValueError(f"SKILL.md is empty for skill: {name}")

    return content
