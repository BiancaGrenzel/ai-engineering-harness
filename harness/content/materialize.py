"""Fail-closed materialization of content-pack files into a project tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from adapters.common.apply import PathConfinementError, confined_path


@dataclass
class MaterializeReport:
    """Classification of planned materialization actions."""

    created: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.errors or self.conflicts)


def plan_materialization(root: Path, files: dict[str, bytes]) -> MaterializeReport:
    """Classify each planned file without writing.

    - missing → created
    - existing and byte-identical → unchanged
    - existing and different → conflict (fail-closed)
    """
    report = MaterializeReport()
    root = root.resolve()

    for relative in sorted(files):
        try:
            target = confined_path(root, relative)
        except PathConfinementError as exc:
            report.errors.append(str(exc))
            continue

        if not target.exists():
            report.created.append(relative)
            continue
        if not target.is_file():
            report.conflicts.append(relative)
            report.errors.append(
                f"Refusing to replace non-file path: {relative}"
            )
            continue
        existing = target.read_bytes()
        if existing == files[relative]:
            report.unchanged.append(relative)
        else:
            report.conflicts.append(relative)

    return report


def apply_plan(
    root: Path,
    files: dict[str, bytes],
    report: MaterializeReport,
    *,
    dry_run: bool,
) -> None:
    """Write created files after a successful plan.

    Raises AssertionError when called with failures (fail-closed).
    """
    if report.has_failures:
        raise AssertionError(
            "refuse to materialize when conflicts or path errors exist "
            "(fail-closed); run plan and abort before apply"
        )
    if dry_run:
        return

    root = root.resolve()
    for relative in report.created:
        target = confined_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[relative])


def format_report(report: MaterializeReport, *, dry_run: bool) -> str:
    """Human-readable materialization summary."""
    lines: list[str] = []
    prefix = "Dry-run: " if dry_run else ""
    if report.created:
        lines.append(f"{prefix}Created ({len(report.created)}):")
        lines.extend(f"  {path}" for path in report.created)
    if report.unchanged:
        lines.append(f"{prefix}Unchanged ({len(report.unchanged)}):")
        lines.extend(f"  {path}" for path in report.unchanged)
    if report.conflicts:
        lines.append(f"Conflicts ({len(report.conflicts)}):")
        lines.extend(f"  {path}" for path in report.conflicts)
    if report.errors:
        lines.append(f"Errors ({len(report.errors)}):")
        lines.extend(f"  {msg}" for msg in report.errors)
    if not lines:
        lines.append(f"{prefix}No files planned.")
    return "\n".join(lines)


def materialize(
    root: Path,
    files: dict[str, bytes],
    *,
    dry_run: bool = False,
) -> MaterializeReport:
    """Plan and optionally apply materialization. Fail-closed on conflicts."""
    report = plan_materialization(root, files)
    if not report.has_failures:
        apply_plan(root, files, report, dry_run=dry_run)
    return report
