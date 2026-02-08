"""Configuration management for Canvas CLI."""

import re
from pathlib import Path
from typing import Optional
import yaml


def parse_course_info(course_name: str) -> dict:
    """Parse course name to extract semester and course code.

    Example: "2026SP-PHIL-123-001H-16W: AI and Ethics"
    Returns: {"semester": "SP26", "course_code": "PHIL-123"}
    """
    # Match pattern: YYYYSS-DEPT-NNN-...
    match = re.match(r'(\d{4})([A-Za-z]{2})-([A-Za-z]+)-(\d+)', course_name)
    if match:
        year, sem, dept, num = match.groups()
        # Transform 2026SP → SP26
        semester = f"{sem.upper()}{year[2:]}"
        course_code = f"{dept.upper()}-{num}"
        return {"semester": semester, "course_code": course_code}
    return {"semester": "", "course_code": ""}


def get_default_folder(config: dict) -> str:
    """Get configured default content folder with legacy compatibility."""
    return config.get("default_folder") or config.get("courses_dir") or "courses"


def find_config_file() -> Optional[Path]:
    """Find .canvas-config.yaml by walking up from current directory."""
    current = Path.cwd()
    while current != current.parent:
        config_path = current / ".canvas-config.yaml"
        if config_path.exists():
            return config_path
        current = current.parent
    return None


def load_config() -> dict:
    """Load configuration from .canvas-config.yaml."""
    config_path = find_config_file()
    if not config_path:
        raise FileNotFoundError(
            "No .canvas-config.yaml found. Run 'canvas config' to set up."
        )

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Store the config directory for relative paths
    config["_config_dir"] = config_path.parent
    return config


def get_courses_dir() -> Path:
    """Get the default courses directory path."""
    config = load_config()
    config_dir = config["_config_dir"]
    courses_dir = get_default_folder(config)
    return config_dir / courses_dir


def get_course_folder(course_code: str, course_name: str = "") -> Path:
    """Get the folder for a specific course based on its code.

    Uses course_folders mapping from config to route courses to subject folders.
    Returns path like: CWI/Philosophy/SP26-PHIL-123-codex-course for PHIL courses.
    """
    config = load_config()
    config_dir = config["_config_dir"]
    course_folders = config.get("course_folders", {})
    default_folder = get_default_folder(config)

    # Combine code and name for matching (e.g., "AI and Ethics: PHIL-123-001H" + course name)
    search_text = f"{course_code} {course_name}".upper()

    # Try to match course code prefix anywhere in the text
    target_folder = default_folder
    # Prefer the longest prefix first so specific mappings win over broad ones.
    for prefix, folder in sorted(course_folders.items(), key=lambda item: len(item[0]), reverse=True):
        escaped = re.escape(prefix.upper())
        pattern = rf"(^|[^A-Z0-9]){escaped}([^A-Z0-9]|$)"
        if re.search(pattern, search_text):
            target_folder = folder
            break

    # Parse course name to get semester and course code for folder name
    course_info = parse_course_info(course_name)
    if course_info["semester"] and course_info["course_code"]:
        subfolder = f"{course_info['semester']}-{course_info['course_code']}-codex-course"
    else:
        # Fallback for courses without standard naming
        subfolder = "codex-course"

    return config_dir / target_folder / subfolder


def save_config(config: dict, path: Optional[Path] = None) -> None:
    """Save configuration to file."""
    if path is None:
        path = find_config_file()
        if path is None:
            path = Path.cwd() / ".canvas-config.yaml"

    # Remove internal keys before saving
    save_data = {k: v for k, v in config.items() if not k.startswith("_")}

    with open(path, "w") as f:
        yaml.dump(save_data, f, default_flow_style=False)
