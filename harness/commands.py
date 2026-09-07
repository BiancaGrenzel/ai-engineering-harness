"""CLI command handlers — thin wrappers over existing Harness APIs."""

from __future__ import annotations

import sys

from harness import __version__
from harness import config_validation
from harness import dispatch
from harness.project import resolve_root_arg


def cmd_version(_args: object) -> int:
    """Print Harness package/CLI version (not adapter or config version)."""
    print(__version__)
    return 0


def cmd_validate(args: object) -> int:
    """Validate ``.harness/harness.yaml`` using the shared config validator."""
    try:
        root = resolve_root_arg(getattr(args, "root", None))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    config_path = root / ".harness" / "harness.yaml"
    schema_path = root / "schemas" / "harness.schema.json"
    return config_validation.validate_paths(config_path, schema_path)


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
