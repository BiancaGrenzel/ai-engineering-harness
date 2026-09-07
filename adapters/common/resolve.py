#!/usr/bin/env python3
"""Vendor-neutral harness resolution helpers for adapters.

Treats configuration content as data. Does not execute Rules, Skills, Tools,
or Profile content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[misc, assignment]


MANAGED_MARKER = "<!-- ai-engineering-harness:managed -->"


@dataclass(frozen=True)
class ResolvedHarness:
    """Effective configuration after Profile merge and path resolution."""

    root: Path
    version: int
    profile: str
    rule_ids: list[str]
    skill_ids: list[str]
    tool_ids: list[str]
    rule_files: list[Path]
    skill_files: list[Path]
    tool_files: list[Path]


class ResolutionError(Exception):
    """Raised when harness configuration cannot be resolved safely."""


def require_deps() -> None:
    if yaml is None:
        raise ResolutionError(
            "Missing dependency: PyYAML. Install with:\n"
            "  pip install -r scripts/requirements.txt"
        )
    if Draft202012Validator is None:
        raise ResolutionError(
            "Missing dependency: jsonschema. Install with:\n"
            "  pip install -r scripts/requirements.txt"
        )


def load_yaml(path: Path) -> Any:
    require_deps()
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_yaml_string(raw: str) -> Any:
    """Parse YAML text as data (no arbitrary code execution)."""
    require_deps()
    return yaml.safe_load(raw)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_against_schema(instance: Any, schema_path: Path) -> list[str]:
    require_deps()
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        return ["schema: root must be a JSON object"]
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    messages: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path)
        location = path if path else "(root)"
        messages.append(f"{location}: {error.message}")
    return messages


def tool_name(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"]
    raise ResolutionError(f"Invalid tool entry: {entry!r}")


def merge_lists(profile_data: dict[str, Any], harness_data: dict[str, Any], key: str) -> list[Any]:
    if key in harness_data:
        value = harness_data[key]
        if value is None:
            raise ResolutionError(f"harness.yaml field '{key}' must not be null")
        return list(value)
    return list(profile_data.get(key) or [])


def find_skill_file(root: Path, skill_id: str) -> Path | None:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return None
    matches = sorted(skills_root.glob(f"**/{skill_id}/SKILL.md"))
    # Prefer category/skill layout; ignore template-only paths.
    matches = [path for path in matches if path.is_file()]
    if not matches:
        return None
    if len(matches) > 1:
        raise ResolutionError(
            f"Skill '{skill_id}' resolves ambiguously: "
            + ", ".join(str(path.relative_to(root)) for path in matches)
        )
    return matches[0]


def find_tool_file(root: Path, tool_id: str) -> Path | None:
    tools_root = root / "docs" / "tools"
    if not tools_root.is_dir():
        return None
    matches = [
        path
        for path in sorted(tools_root.glob(f"**/{tool_id}.md"))
        if path.is_file() and path.name.lower() not in {"readme.md", "registry.md"}
    ]
    if not matches:
        return None
    if len(matches) > 1:
        raise ResolutionError(
            f"Tool '{tool_id}' resolves ambiguously: "
            + ", ".join(str(path.relative_to(root)) for path in matches)
        )
    return matches[0]


def resolve_rule_files(root: Path, rule_ids: list[str]) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []
    for rule_id in rule_ids:
        category = root / "rules" / rule_id
        if not category.is_dir():
            missing.append(rule_id)
            continue
        rule_md = sorted(
            path
            for path in category.glob("*.md")
            if path.is_file() and path.name.lower() != "readme.md"
        )
        if not rule_md:
            missing.append(rule_id)
            continue
        files.extend(rule_md)
    if missing:
        raise ResolutionError(
            "Missing or empty Rule categories: " + ", ".join(missing)
        )
    return files


def resolve_skill_files(root: Path, skill_ids: list[str]) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []
    for skill_id in skill_ids:
        path = find_skill_file(root, skill_id)
        if path is None:
            missing.append(skill_id)
            continue
        files.append(path)
    if missing:
        raise ResolutionError("Missing Skills: " + ", ".join(missing))
    return files


def resolve_tool_files(root: Path, tool_ids: list[str]) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []
    for tool_id in tool_ids:
        path = find_tool_file(root, tool_id)
        if path is None:
            missing.append(tool_id)
            continue
        files.append(path)
    if missing:
        raise ResolutionError("Missing Tools: " + ", ".join(missing))
    return files


def resolve_harness(root: Path) -> ResolvedHarness:
    """Load, validate, merge, and resolve harness configuration under root."""
    require_deps()
    root = root.resolve()
    config_path = root / ".harness" / "harness.yaml"
    harness_schema = root / "schemas" / "harness.schema.json"
    profile_schema = root / "schemas" / "profile.schema.json"

    if not config_path.is_file():
        raise ResolutionError(f"Config not found: {config_path}")
    if not harness_schema.is_file():
        raise ResolutionError(f"Schema not found: {harness_schema}")
    if not profile_schema.is_file():
        raise ResolutionError(f"Schema not found: {profile_schema}")

    harness_data = load_yaml(config_path)
    if not isinstance(harness_data, dict):
        raise ResolutionError("harness.yaml root must be a mapping")

    harness_errors = validate_against_schema(harness_data, harness_schema)
    if harness_errors:
        raise ResolutionError(
            "harness.yaml failed schema validation:\n- " + "\n- ".join(harness_errors)
        )

    profile_name = harness_data["profile"]
    profile_path = root / "profiles" / f"{profile_name}.yaml"
    if not profile_path.is_file():
        raise ResolutionError(f"Profile not found: {profile_path.relative_to(root)}")

    profile_data = load_yaml(profile_path)
    if not isinstance(profile_data, dict):
        raise ResolutionError("profile root must be a mapping")

    profile_errors = validate_against_schema(profile_data, profile_schema)
    if profile_errors:
        raise ResolutionError(
            f"Profile '{profile_name}' failed schema validation:\n- "
            + "\n- ".join(profile_errors)
        )

    if profile_data.get("name") != profile_name:
        raise ResolutionError(
            f"Profile name mismatch: file stem '{profile_name}' vs name "
            f"'{profile_data.get('name')}'"
        )

    rule_ids = [str(item) for item in merge_lists(profile_data, harness_data, "rules")]
    skill_ids = [str(item) for item in merge_lists(profile_data, harness_data, "skills")]
    tool_entries = merge_lists(profile_data, harness_data, "tools")
    tool_ids = [tool_name(entry) for entry in tool_entries]

    return ResolvedHarness(
        root=root,
        version=int(harness_data["version"]),
        profile=profile_name,
        rule_ids=rule_ids,
        skill_ids=skill_ids,
        tool_ids=tool_ids,
        rule_files=resolve_rule_files(root, rule_ids),
        skill_files=resolve_skill_files(root, skill_ids),
        tool_files=resolve_tool_files(root, tool_ids),
    )


def is_harness_managed(text: str) -> bool:
    return MANAGED_MARKER in text


def read_text_if_exists(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")
