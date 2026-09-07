#!/usr/bin/env python3
"""Shared managed-output planning helpers for adapters.

Provides fail-closed preflight, conflict detection, stale removal, and
manifest inventory handling. Agent-specific rendering stays in each adapter.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from adapters.common.resolve import (
    MANAGED_MARKER,
    is_harness_managed,
    read_text_if_exists,
)

# Drive-letter and UNC forms that Path.is_absolute() may miss on non-Windows hosts.
_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
_UNC_RE = re.compile(r"^[/\\]{2}")


class PathConfinementError(ValueError):
    """Raised when a planned or managed path would escape the project root."""


@dataclass(frozen=True)
class PlannedFile:
    """One agent-specific file the adapter intends to write."""

    relative_path: str
    content: str
    kind: str


@dataclass
class GenerationReport:
    """Structured result of preflight and/or apply."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.errors or self.conflicts)


def confined_path(root: Path, relative_path: str) -> Path:
    """Resolve ``relative_path`` under ``root`` or raise ``PathConfinementError``.

    Rejects absolute paths, drive/UNC forms, and any path that resolves outside
    ``root`` (including ``..`` traversal and symlink escapes after resolve).
    """
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise PathConfinementError(f"Invalid managed path: {relative_path!r}")

    raw = relative_path.strip()
    candidate = Path(raw)

    if candidate.is_absolute() or _WINDOWS_ABS_RE.match(raw) or _UNC_RE.match(raw):
        raise PathConfinementError(
            f"Absolute or non-relative managed path rejected: {relative_path}"
        )

    root_resolved = root.resolve()
    full = (root_resolved / raw).resolve()
    try:
        full.relative_to(root_resolved)
    except ValueError as exc:
        raise PathConfinementError(
            f"Managed path escapes project root: {relative_path}"
        ) from exc
    return full


def assert_under_root(root: Path, path: Path, *, label: str) -> Path:
    """Ensure an absolute-ish ``path`` resolves inside ``root``."""
    root_resolved = root.resolve()
    full = path.resolve()
    try:
        full.relative_to(root_resolved)
    except ValueError as exc:
        raise PathConfinementError(
            f"{label} escapes project root: {path}"
        ) from exc
    return full


def default_manifest(
    *,
    adapter: str,
    adapter_version: int,
) -> dict:
    return {
        "version": 1,
        "adapter": adapter,
        "adapter_version": adapter_version,
        "files": [],
        "marker": MANAGED_MARKER,
    }


def load_manifest(
    path: Path,
    *,
    adapter: str,
    adapter_version: int,
) -> dict:
    """Load managed-output inventory. Not a configuration source of truth."""
    if not path.is_file():
        return default_manifest(adapter=adapter, adapter_version=adapter_version)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_manifest(adapter=adapter, adapter_version=adapter_version)
    if not isinstance(data, dict):
        return default_manifest(adapter=adapter, adapter_version=adapter_version)
    files = data.get("files", [])
    if not isinstance(files, list):
        files = []
    return {
        "version": 1,
        "adapter": adapter,
        "adapter_version": adapter_version,
        "files": [str(item) for item in files if isinstance(item, str)],
        "marker": MANAGED_MARKER,
    }


def write_manifest(
    path: Path,
    files: list[str],
    *,
    adapter: str,
    adapter_version: int,
    dry_run: bool,
) -> None:
    payload = {
        "version": 1,
        "adapter": adapter,
        "adapter_version": adapter_version,
        "files": sorted(files),
        "marker": MANAGED_MARKER,
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def detect_write_conflicts(root: Path, planned: list[PlannedFile]) -> list[str]:
    """Return relative paths that exist and are not Harness-managed."""
    conflicts: list[str] = []
    for item in planned:
        path = confined_path(root, item.relative_path)
        existing = read_text_if_exists(path)
        if existing is None:
            continue
        if is_harness_managed(existing):
            continue
        conflicts.append(item.relative_path)
    return conflicts


def plan_stale_removals(
    root: Path,
    *,
    previous_files: list[str],
    desired_files: set[str],
) -> tuple[list[str], list[str], list[str]]:
    """Return (removable, warnings, confinement_errors)."""
    removable: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    for rel in sorted(set(previous_files) - desired_files):
        try:
            path = confined_path(root, rel)
        except PathConfinementError as exc:
            errors.append(str(exc))
            continue
        existing = read_text_if_exists(path)
        if existing is None:
            continue
        if not is_harness_managed(existing):
            warnings.append(
                f"Stale path '{rel}' was listed as managed but is user-managed now; "
                "left untouched."
            )
            continue
        removable.append(rel)
    return removable, warnings, errors


def preflight(
    root: Path,
    planned: list[PlannedFile],
    *,
    previous_files: list[str],
) -> GenerationReport:
    """Detect conflicts and classify planned actions without writing files.

    Fail-closed: callers must not apply when report.has_failures is true.
    Invalid paths (escapes, absolute) are errors and prevent apply.
    """
    report = GenerationReport()
    desired = {item.relative_path for item in planned}

    for item in planned:
        try:
            confined_path(root, item.relative_path)
        except PathConfinementError as exc:
            report.errors.append(str(exc))

    if report.errors:
        # Still check stale previous_files for additional confinement errors.
        _removable, _warnings, stale_errors = plan_stale_removals(
            root,
            previous_files=previous_files,
            desired_files=desired,
        )
        report.errors.extend(stale_errors)
        return report

    report.conflicts.extend(detect_write_conflicts(root, planned))

    for item in planned:
        if item.relative_path in report.conflicts:
            continue
        path = confined_path(root, item.relative_path)
        existing = read_text_if_exists(path)
        if existing is None:
            report.created.append(item.relative_path)
        elif existing == item.content:
            report.unchanged.append(item.relative_path)
        else:
            report.updated.append(item.relative_path)

    removable, stale_warnings, stale_errors = plan_stale_removals(
        root,
        previous_files=previous_files,
        desired_files=desired,
    )
    report.removed.extend(removable)
    report.warnings.extend(stale_warnings)
    report.errors.extend(stale_errors)
    return report


def apply_preflighted_plan(
    root: Path,
    planned: list[PlannedFile],
    report: GenerationReport,
    *,
    manifest_path: Path,
    adapter: str,
    adapter_version: int,
    dry_run: bool,
) -> None:
    """Write planned outputs after a successful preflight.

    Raises AssertionError if called when conflicts or path errors exist.
    """
    if report.has_failures:
        raise AssertionError(
            "refuse to apply when conflicts or path errors exist (fail-closed); "
            "run preflight and abort before apply"
        )

    desired = {item.relative_path for item in planned}
    managed_written: list[str] = []
    safe_manifest = assert_under_root(root, manifest_path, label="managed manifest")

    for item in planned:
        path = confined_path(root, item.relative_path)
        if item.relative_path in report.unchanged:
            managed_written.append(item.relative_path)
            continue
        if dry_run:
            managed_written.append(item.relative_path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content, encoding="utf-8")
        managed_written.append(item.relative_path)

    for rel in report.removed:
        path = confined_path(root, rel)
        if dry_run:
            continue
        if path.is_file():
            path.unlink()
            parent = path.parent
            root_resolved = root.resolve()
            if (
                parent.name
                and parent != root_resolved
                and parent.is_dir()
                and not any(parent.iterdir())
            ):
                try:
                    parent.relative_to(root_resolved)
                except ValueError:
                    continue
                parent.rmdir()

    write_manifest(
        safe_manifest,
        sorted(set(managed_written) & desired),
        adapter=adapter,
        adapter_version=adapter_version,
        dry_run=dry_run,
    )
