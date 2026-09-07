"""Project root discovery for the Harness CLI."""

from __future__ import annotations

from pathlib import Path

CONFIG_REL = Path(".harness") / "harness.yaml"


def find_project_root(start: Path | None = None) -> Path | None:
    """Locate the nearest ancestor containing ``.harness/harness.yaml``.

    Walks from ``start`` (default: cwd) toward the filesystem root.
    Stops at the filesystem root (``Path.parent`` of a root equals itself).

    Returns:
        The project root Path, or None if no harness config is found.
    """
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / CONFIG_REL).is_file():
            return candidate
    return None


def require_project_root(start: Path | None = None) -> Path:
    """Return project root or raise FileNotFoundError with a clear message."""
    root = find_project_root(start)
    if root is None:
        raise FileNotFoundError("Harness configuration not found.")
    return root


def resolve_root_arg(root: Path | None) -> Path:
    """Resolve an explicit ``--root`` or discover from the current directory."""
    if root is not None:
        resolved = root.resolve()
        config = resolved / CONFIG_REL
        if not config.is_file():
            raise FileNotFoundError("Harness configuration not found.")
        return resolved
    return require_project_root()
