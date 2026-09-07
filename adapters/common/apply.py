#!/usr/bin/env python3
"""Shared managed-output planning helpers for adapters.

Provides fail-closed preflight, conflict detection, stale removal, and
manifest inventory handling. Agent-specific rendering stays in each adapter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from adapters.common.resolve import (
    MANAGED_MARKER,
    is_harness_managed,
    read_text_if_exists,
)


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
        path = root / item.relative_path
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
) -> tuple[list[str], list[str]]:
    """Return (removable managed paths, warnings for unmanaged stale paths)."""
    removable: list[str] = []
    warnings: list[str] = []
    for rel in sorted(set(previous_files) - desired_files):
        path = root / rel
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
    return removable, warnings


def preflight(
    root: Path,
    planned: list[PlannedFile],
    *,
    previous_files: list[str],
) -> GenerationReport:
    """Detect conflicts and classify planned actions without writing files.

    Fail-closed: callers must not apply when report.has_failures is true.
    """
    report = GenerationReport()
    desired = {item.relative_path for item in planned}
    report.conflicts.extend(detect_write_conflicts(root, planned))

    for item in planned:
        if item.relative_path in report.conflicts:
            continue
        path = root / item.relative_path
        existing = read_text_if_exists(path)
        if existing is None:
            report.created.append(item.relative_path)
        elif existing == item.content:
            report.unchanged.append(item.relative_path)
        else:
            report.updated.append(item.relative_path)

    removable, stale_warnings = plan_stale_removals(
        root,
        previous_files=previous_files,
        desired_files=desired,
    )
    report.removed.extend(removable)
    report.warnings.extend(stale_warnings)
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

    Raises AssertionError if called when conflicts exist (programming error).
    """
    if report.conflicts:
        raise AssertionError(
            "refuse to apply when conflicts exist (fail-closed); "
            "run preflight and abort before apply"
        )

    desired = {item.relative_path for item in planned}
    managed_written: list[str] = []

    for item in planned:
        path = root / item.relative_path
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
        if dry_run:
            continue
        path = root / rel
        if path.is_file():
            path.unlink()
            parent = path.parent
            if parent.name and parent != root and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()

    write_manifest(
        manifest_path,
        sorted(set(managed_written) & desired),
        adapter=adapter,
        adapter_version=adapter_version,
        dry_run=dry_run,
    )
