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
