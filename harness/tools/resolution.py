"""Resolve Tool definitions from the declarative Registry.

Resolution is pure data lookup. It does not detect, install, or execute Tools.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, MutableMapping

try:
    import yaml
except ImportError:  # pragma: no cover - dependency guard
    yaml = None  # type: ignore[assignment]

ToolDefinition = Mapping[str, Any]


class ToolResolutionError(ValueError):
    """Raised when Registry data cannot be loaded or a Tool cannot be resolved."""


def load_tool_registry(path: Path | str) -> MutableMapping[str, Any]:
    """Load ``tools/registry.yaml`` as a mapping.

    The file is read only. Callers must treat the result as catalog data, not
    runtime state.
    """
    if yaml is None:
        raise ToolResolutionError(
            "Missing dependency: PyYAML. Install with: pip install -r scripts/requirements.txt"
        )

    registry_path = Path(path)
    try:
        raw = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ToolResolutionError(f"Unable to read Tool Registry: {registry_path}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ToolResolutionError(f"Invalid Tool Registry YAML: {registry_path}") from exc

    if not isinstance(data, dict):
        raise ToolResolutionError("Tool Registry root must be a mapping")
    tools = data.get("tools")
    if not isinstance(tools, list):
        raise ToolResolutionError("Tool Registry 'tools' must be a list")
    return data


def resolve_tool(registry: Mapping[str, Any], tool_id: str) -> ToolDefinition:
    """Return the Tool definition for ``tool_id`` from a loaded Registry mapping."""
    if not tool_id or not isinstance(tool_id, str):
        raise ToolResolutionError("tool_id must be a non-empty string")

    tools = registry.get("tools")
    if not isinstance(tools, list):
        raise ToolResolutionError("Tool Registry 'tools' must be a list")

    matches = [tool for tool in tools if isinstance(tool, dict) and tool.get("id") == tool_id]
    if not matches:
        raise ToolResolutionError(f"Unknown Tool id: {tool_id}")
    if len(matches) > 1:
        raise ToolResolutionError(f"Duplicate Tool id in Registry: {tool_id}")
    return matches[0]
