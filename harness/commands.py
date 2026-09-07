"""CLI command handlers — thin wrappers over existing Harness APIs."""

from __future__ import annotations

import sys

from harness import __version__
from harness import config_validation
from harness import dispatch
from harness.project import resolve_root_arg
from harness.tools.detection import ToolDetector
from harness.tools.health import ToolHealthChecker, format_health_cli_report
from harness.tools.resolution import (
    ToolResolutionError,
    load_tool_registry,
    resolve_tool,
)


def cmd_version(_args: object) -> int:
    """Print Harness package/CLI version (not adapter or config version)."""
    print(__version__)
    return 0


def cmd_validate(args: object) -> int:
    """Validate Harness configuration and the project Tool Registry when present."""
    try:
        root = resolve_root_arg(getattr(args, "root", None))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return config_validation.validate_repository(root)


def cmd_generate(args: object) -> int:
    """Dispatch ``generate <adapter>`` to the static adapter map."""
    adapter = getattr(args, "adapter")
    dry_run = bool(getattr(args, "dry_run", False))
    try:
        root = resolve_root_arg(getattr(args, "root", None))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return dispatch.generate(adapter, root, dry_run=dry_run)


def cmd_tools_health(args: object) -> int:
    """Resolve, detect, and health-check one Tool; print a human report."""
    tool_id = getattr(args, "tool_id")
    try:
        root = resolve_root_arg(getattr(args, "root", None))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    registry_path = root / "tools" / "registry.yaml"
    if not registry_path.is_file():
        print(f"Tool Registry not found: {registry_path}", file=sys.stderr)
        return 1

    try:
        registry = load_tool_registry(registry_path)
        tool = resolve_tool(registry, tool_id)
    except ToolResolutionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    detection = ToolDetector().detect(tool)
    health = ToolHealthChecker().check(tool, detection)

    tool_name = tool.get("name")
    if not isinstance(tool_name, str) or not tool_name:
        tool_name = tool_id

    print(format_health_cli_report(tool_name=tool_name, detection=detection, health=health))
    return 0 if health.healthy else 1
