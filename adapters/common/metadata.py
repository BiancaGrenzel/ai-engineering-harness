#!/usr/bin/env python3
"""Load and validate adapter.yaml metadata.

Adapter metadata is the declared capability contract for one adapter.
It is not a second configuration source of truth for the project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.common.resolve import load_yaml, require_deps

KNOWN_CAPABILITIES = frozenset({"rules", "skills", "tools"})

# PlannedFile.kind uses singular forms; adapter.yaml uses plural capability names.
KIND_TO_CAPABILITY = {
    "rule": "rules",
    "skill": "skills",
    "tool": "tools",
}


class AdapterMetadataError(Exception):
    """Raised when adapter.yaml is missing, invalid, or inconsistent."""


@dataclass(frozen=True)
class AdapterMetadata:
    """Validated adapter declaration from adapter.yaml."""

    path: Path
    name: str
    agent: str
    version: int
    status: str
    supported_capabilities: tuple[str, ...]
    unsupported_capabilities: tuple[str, ...]
    input_paths: tuple[str, ...]
    output: dict[str, str]
    notes: tuple[str, ...]

    def supports(self, capability: str) -> bool:
        return capability in self.supported_capabilities

    def output_path(self, key: str) -> str:
        value = self.output.get(key)
        if not value:
            raise AdapterMetadataError(
                f"adapter.yaml output.{key} is required for adapter '{self.name}'"
            )
        return value


def _as_str_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise AdapterMetadataError(f"adapter.yaml field '{key}' must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise AdapterMetadataError(f"adapter.yaml field '{key}' entries must be non-empty strings")
        result.append(item.strip())
    return result


def _as_str_map(data: dict[str, Any], key: str) -> dict[str, str]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise AdapterMetadataError(f"adapter.yaml field '{key}' must be a mapping")
    result: dict[str, str] = {}
    for map_key, map_value in value.items():
        if not isinstance(map_key, str) or not isinstance(map_value, str):
            raise AdapterMetadataError(
                f"adapter.yaml field '{key}' must map strings to strings"
            )
        result[map_key] = map_value
    return result


def load_adapter_metadata(path: Path) -> AdapterMetadata:
    """Load and validate adapter.yaml from the given path."""
    require_deps()
    path = path.resolve()
    if not path.is_file():
        raise AdapterMetadataError(f"adapter metadata not found: {path}")

    data = load_yaml(path)
    if not isinstance(data, dict):
        raise AdapterMetadataError("adapter.yaml root must be a mapping")

    required_strings = ("name", "agent", "status")
    for field in required_strings:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise AdapterMetadataError(f"adapter.yaml field '{field}' must be a non-empty string")

    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        raise AdapterMetadataError(
            "adapter.yaml field 'version' must be a positive integer "
            "(adapter implementation version; not Harness config version or Tool version)"
        )

    supported = _as_str_list(data, "supported_capabilities")
    unsupported = _as_str_list(data, "unsupported_capabilities")

    unknown = sorted(set(supported + unsupported) - KNOWN_CAPABILITIES)
    if unknown:
        raise AdapterMetadataError(
            "adapter.yaml declares unknown capabilities: " + ", ".join(unknown)
        )

    overlap = sorted(set(supported) & set(unsupported))
    if overlap:
        raise AdapterMetadataError(
            "adapter.yaml capabilities cannot be both supported and unsupported: "
            + ", ".join(overlap)
        )

    if not supported:
        raise AdapterMetadataError(
            "adapter.yaml must declare at least one supported_capabilities entry"
        )

    output = _as_str_map(data, "output")
    if "managed_manifest" not in output:
        raise AdapterMetadataError("adapter.yaml output.managed_manifest is required")
    if "rules" in supported and "rules_dir" not in output:
        raise AdapterMetadataError(
            "adapter.yaml supports rules but output.rules_dir is missing"
        )
    if "skills" in supported and "skills_dir" not in output:
        raise AdapterMetadataError(
            "adapter.yaml supports skills but output.skills_dir is missing"
        )

    return AdapterMetadata(
        path=path,
        name=str(data["name"]).strip(),
        agent=str(data["agent"]).strip(),
        version=version,
        status=str(data["status"]).strip(),
        supported_capabilities=tuple(supported),
        unsupported_capabilities=tuple(unsupported),
        input_paths=tuple(_as_str_list(data, "input")),
        output=output,
        notes=tuple(_as_str_list(data, "notes")),
    )


def assert_plan_matches_capabilities(
    metadata: AdapterMetadata,
    planned_kinds: set[str],
) -> None:
    """Fail when planned outputs contradict adapter.yaml capabilities."""
    for kind in sorted(planned_kinds):
        capability = KIND_TO_CAPABILITY.get(kind)
        if capability is None:
            raise AdapterMetadataError(
                f"planned output kind '{kind}' is not a known capability"
            )
        if not metadata.supports(capability):
            raise AdapterMetadataError(
                f"adapter '{metadata.name}' planned '{kind}' outputs but "
                f"adapter.yaml does not list '{capability}' under supported_capabilities"
            )
