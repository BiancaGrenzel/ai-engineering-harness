"""Locate and resolve the read-only Harness content pack.

Canonical project resources live at the repository root during development.
Installed wheels ship a copy under ``harness/content/_data`` (package data).
Neither location is treated as mutable global configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


class ContentPackError(Exception):
    """Raised when the content pack cannot be located or resolved."""


_PACKAGE_DIR = Path(__file__).resolve().parent
_BUNDLED_DATA = _PACKAGE_DIR / "_data"
# harness/content/pack.py → harness/content → harness → repository root
_REPO_ROOT = _PACKAGE_DIR.parent.parent


def _looks_like_pack_root(root: Path) -> bool:
    return (root / "schemas" / "harness.schema.json").is_file() and (
        root / "profiles"
    ).is_dir()


def content_pack_root() -> Path:
    """Return the read-only content pack root.

    Preference order:
    1. Bundled package data (``harness/content/_data``) when present
    2. Repository root when developing from a source checkout / editable install
    """
    if _looks_like_pack_root(_BUNDLED_DATA):
        return _BUNDLED_DATA
    if _looks_like_pack_root(_REPO_ROOT):
        return _REPO_ROOT
    raise ContentPackError(
        "Harness content pack not found. Reinstall the package or run from a "
        "source checkout that includes schemas/ and profiles/."
    )


def _require_yaml() -> None:
    if yaml is None:
        raise ContentPackError(
            "Missing dependency: PyYAML. Install with:\n"
            "  pip install ai-engineering-harness"
        )


def load_yaml(path: Path) -> Any:
    _require_yaml()
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def list_profiles(pack_root: Path | None = None) -> list[str]:
    """Return sorted profile ids available in the content pack."""
    root = pack_root or content_pack_root()
    profiles_dir = root / "profiles"
    if not profiles_dir.is_dir():
        return []
    names = sorted(
        path.stem
        for path in profiles_dir.glob("*.yaml")
        if path.is_file() and path.name.lower() != "readme.yaml"
    )
    return names


def load_profile(profile: str, pack_root: Path | None = None) -> dict[str, Any]:
    """Load and return one profile mapping from the content pack."""
    root = pack_root or content_pack_root()
    path = root / "profiles" / f"{profile}.yaml"
    if not path.is_file():
        available = ", ".join(list_profiles(root)) or "(none)"
        raise ContentPackError(
            f"Unknown profile: {profile}\nAvailable profiles: {available}"
        )
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ContentPackError(f"Profile '{profile}' root must be a mapping")
    name = data.get("name")
    if name != profile:
        raise ContentPackError(
            f"Profile name mismatch: file stem '{profile}' vs name {name!r}"
        )
    return data


def _tool_name(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"]
    raise ContentPackError(f"Invalid tool entry in profile: {entry!r}")


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _add_file(mapping: dict[str, bytes], pack_root: Path, relative: str) -> None:
    relative = relative.replace("\\", "/").lstrip("/")
    source = pack_root / relative
    if not source.is_file():
        raise ContentPackError(f"Content pack missing required file: {relative}")
    mapping[relative] = _read_bytes(source)


def _find_skill_relative(pack_root: Path, skill_id: str) -> str:
    skills_root = pack_root / "skills"
    if not skills_root.is_dir():
        raise ContentPackError(f"Content pack missing skills/: {skill_id}")
    matches = sorted(
        path
        for path in skills_root.glob(f"**/{skill_id}/SKILL.md")
        if path.is_file()
    )
    if not matches:
        raise ContentPackError(f"Content pack missing Skill: {skill_id}")
    if len(matches) > 1:
        rels = ", ".join(str(path.relative_to(pack_root)).replace("\\", "/") for path in matches)
        raise ContentPackError(f"Skill '{skill_id}' resolves ambiguously: {rels}")
    return str(matches[0].relative_to(pack_root)).replace("\\", "/")


def _rule_category_files(pack_root: Path, category: str) -> list[str]:
    category_dir = pack_root / "rules" / category
    if not category_dir.is_dir():
        raise ContentPackError(f"Content pack missing Rule category: {category}")
    files = sorted(
        path
        for path in category_dir.glob("*.md")
        if path.is_file() and path.name.lower() != "readme.md"
    )
    if not files:
        raise ContentPackError(f"Content pack Rule category is empty: {category}")
    return [str(path.relative_to(pack_root)).replace("\\", "/") for path in files]


def _filtered_registry_bytes(pack_root: Path, tool_ids: list[str]) -> bytes:
    """Return a Registry document containing only the selected tools."""
    registry_path = pack_root / "tools" / "registry.yaml"
    if not registry_path.is_file():
        raise ContentPackError("Content pack missing tools/registry.yaml")
    data = load_yaml(registry_path)
    if not isinstance(data, dict):
        raise ContentPackError("Tool Registry root must be a mapping")
    tools = data.get("tools")
    if not isinstance(tools, list):
        raise ContentPackError("Tool Registry 'tools' must be a list")

    by_id: dict[str, dict[str, Any]] = {}
    for entry in tools:
        if not isinstance(entry, dict):
            raise ContentPackError("Tool Registry entries must be mappings")
        tool_id = entry.get("id")
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ContentPackError("Tool Registry entry missing non-empty 'id'")
        by_id[tool_id.strip()] = entry

    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for tool_id in tool_ids:
        entry = by_id.get(tool_id)
        if entry is None:
            missing.append(tool_id)
            continue
        selected.append(entry)
    if missing:
        raise ContentPackError(
            "Profile references unknown Tool id(s): " + ", ".join(missing)
        )

    payload = {"version": data.get("version", 1), "tools": selected}
    _require_yaml()
    text = yaml.safe_dump(  # type: ignore[union-attr]
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    if not text.endswith("\n"):
        text += "\n"
    # Prefer LF for deterministic cross-platform materialization.
    return text.replace("\r\n", "\n").encode("utf-8")


def _minimal_harness_yaml(profile: str) -> bytes:
    text = (
        "# Project Harness configuration.\n"
        "# Schema: schemas/harness.schema.json\n"
        "#\n"
        "# Profile provides defaults. Omitting rules/skills/tools inherits\n"
        "# those lists from the selected Profile.\n"
        "\n"
        "version: 1\n"
        f"profile: {profile}\n"
    )
    return text.encode("utf-8")


def build_profile_file_map(
    profile: str,
    pack_root: Path | None = None,
) -> dict[str, bytes]:
    """Build the relative-path → bytes map to materialize for ``profile``.

    Includes only the selected Profile and its Rule / Skill / Tool dependencies,
    plus the schemas required for validate/resolve.
    """
    root = pack_root or content_pack_root()
    data = load_profile(profile, root)

    mapping: dict[str, bytes] = {}
    mapping[".harness/harness.yaml"] = _minimal_harness_yaml(profile)
    _add_file(mapping, root, f"profiles/{profile}.yaml")

    for schema_name in (
        "harness.schema.json",
        "profile.schema.json",
        "tool-registry.schema.json",
    ):
        _add_file(mapping, root, f"schemas/{schema_name}")

    rule_ids = [str(item) for item in (data.get("rules") or [])]
    for rule_id in rule_ids:
        for rel in _rule_category_files(root, rule_id):
            _add_file(mapping, root, rel)

    skill_ids = [str(item) for item in (data.get("skills") or [])]
    for skill_id in skill_ids:
        _add_file(mapping, root, _find_skill_relative(root, skill_id))

    tool_ids = [_tool_name(entry) for entry in (data.get("tools") or [])]
    if tool_ids:
        mapping["tools/registry.yaml"] = _filtered_registry_bytes(root, tool_ids)
        registry_data = load_yaml(root / "tools" / "registry.yaml")
        assert isinstance(registry_data, dict)
        tools = registry_data.get("tools") or []
        by_id = {
            entry["id"]: entry
            for entry in tools
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        }
        for tool_id in tool_ids:
            entry = by_id[tool_id]
            documentation = entry.get("documentation")
            if not isinstance(documentation, str) or not documentation.strip():
                raise ContentPackError(
                    f"Tool '{tool_id}' is missing a documentation path in the Registry"
                )
            doc_rel = documentation.strip().replace("\\", "/")
            _add_file(mapping, root, doc_rel)

    return mapping


def collect_pack_source_files(repo_root: Path) -> list[tuple[Path, str]]:
    """Return (source_path, relative_under_pack) pairs for wheel packaging.

    Used by the setuptools build hook. Skips README/template noise.
    Does not require PyYAML so the build backend can run with setuptools only.
    """
    import re

    pairs: list[tuple[Path, str]] = []

    schemas = repo_root / "schemas"
    if schemas.is_dir():
        for path in sorted(schemas.glob("*.json")):
            if path.is_file():
                pairs.append((path, f"schemas/{path.name}"))

    profiles = repo_root / "profiles"
    if profiles.is_dir():
        for path in sorted(profiles.glob("*.yaml")):
            if path.is_file():
                pairs.append((path, f"profiles/{path.name}"))

    rules = repo_root / "rules"
    if rules.is_dir():
        for path in sorted(rules.glob("*/*.md")):
            if path.is_file() and path.name.lower() != "readme.md":
                rel = path.relative_to(repo_root).as_posix()
                pairs.append((path, rel))

    skills = repo_root / "skills"
    if skills.is_dir():
        for path in sorted(skills.glob("**/SKILL.md")):
            if path.is_file():
                rel = path.relative_to(repo_root).as_posix()
                pairs.append((path, rel))

    registry = repo_root / "tools" / "registry.yaml"
    if registry.is_file():
        pairs.append((registry, "tools/registry.yaml"))
        # Lightweight parse so packaging does not require PyYAML at build time.
        text = registry.read_text(encoding="utf-8")
        for match in re.finditer(r"(?m)^\s*documentation:\s*(\S+)\s*$", text):
            doc_rel = match.group(1).strip().strip("\"'").replace("\\", "/")
            doc_path = repo_root / doc_rel
            if doc_path.is_file():
                pairs.append((doc_path, doc_rel))

    return pairs
