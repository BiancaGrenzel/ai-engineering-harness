"""Static adapter dispatch for ``harness generate <adapter>``.

Extensible by adding entries to ADAPTERS. No plugin discovery, no dynamic
package loading, no remote registry.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


def _run_cursor(root: Path, *, dry_run: bool) -> int:
    """Dispatch to the existing Cursor adapter generator."""
    try:
        from adapters.cursor import generate as cursor_generate
    except ImportError as exc:  # pragma: no cover - environment guard
        print(f"Cursor adapter is unavailable.\n\n{exc}", file=sys.stderr)
        return 1
    return cursor_generate.run(root, dry_run=dry_run)


def _run_claude(root: Path, *, dry_run: bool) -> int:
    """Dispatch to the existing Claude adapter generator."""
    try:
        from adapters.claude import generate as claude_generate
    except ImportError as exc:  # pragma: no cover - environment guard
        print(f"Claude adapter is unavailable.\n\n{exc}", file=sys.stderr)
        return 1
    return claude_generate.run(root, dry_run=dry_run)


# Static map only. Add future adapters here when implemented.
ADAPTERS: dict[str, Callable[..., int]] = {
    "cursor": _run_cursor,
    "claude": _run_claude,
}


def supported_adapters() -> list[str]:
    return sorted(ADAPTERS)


def generate(adapter: str, root: Path, *, dry_run: bool = False) -> int:
    """Run the named adapter's generator. Returns the adapter exit code."""
    runner = ADAPTERS.get(adapter)
    if runner is None:
        print(f"Unknown or unsupported adapter: {adapter}", file=sys.stderr)
        return 1
    return runner(root, dry_run=dry_run)
