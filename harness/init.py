"""``harness init`` — materialize Harness project intent and profile content."""

from __future__ import annotations

import sys
from pathlib import Path

from harness.content.materialize import MaterializeReport, format_report, materialize
from harness.content.pack import (
    ContentPackError,
    build_profile_file_map,
    content_pack_root,
    list_profiles,
)
from harness.project import CONFIG_REL, resolve_init_root


def _stdin_interactive() -> bool:
    return bool(getattr(sys.stdin, "isatty", lambda: False)() and sys.stdin.isatty())


def select_profile_interactive(available: list[str]) -> str | None:
    """Prompt for a profile when stdin is a TTY. Returns None if cancelled."""
    if not available:
        print("No profiles are available in the content pack.", file=sys.stderr)
        return None

    print("Select a Harness profile:")
    for index, name in enumerate(available, start=1):
        print(f"  {index}. {name}")
    print("Enter a number (or profile name). Empty input cancels.")

    try:
        raw = input("> ").strip()
    except EOFError:
        return None
    if not raw:
        return None
    if raw.isdigit():
        choice = int(raw)
        if 1 <= choice <= len(available):
            return available[choice - 1]
        print(f"Invalid selection: {raw}", file=sys.stderr)
        return None
    if raw in available:
        return raw
    print(f"Unknown profile: {raw}", file=sys.stderr)
    return None


def resolve_profile_choice(
    profile: str | None,
    *,
    interactive: bool | None = None,
) -> tuple[str | None, str | None]:
    """Return ``(profile, error_message)``."""
    try:
        pack_root = content_pack_root()
        available = list_profiles(pack_root)
    except ContentPackError as exc:
        return None, str(exc)

    if profile:
        if profile not in available:
            listed = ", ".join(available) or "(none)"
            return None, f"Unknown profile: {profile}\nAvailable profiles: {listed}"
        return profile, None

    use_interactive = _stdin_interactive() if interactive is None else interactive
    if not use_interactive:
        return None, (
            "No profile specified. Pass --profile <name>, or run in an "
            "interactive terminal to select one.\n"
            f"Available profiles: {', '.join(available) or '(none)'}"
        )

    chosen = select_profile_interactive(available)
    if chosen is None:
        return None, "Profile selection cancelled."
    return chosen, None


def run_init(
    *,
    root: Path | None = None,
    profile: str | None = None,
    dry_run: bool = False,
    interactive: bool | None = None,
) -> tuple[int, MaterializeReport | None]:
    """Materialize project intent and selected profile content.

    Returns ``(exit_code, report)``. Fail-closed: conflicts perform zero writes.
    """
    try:
        project_root = resolve_init_root(root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(str(exc), file=sys.stderr)
        return 1, None

    chosen, error = resolve_profile_choice(profile, interactive=interactive)
    if error or chosen is None:
        print(error or "Profile selection failed.", file=sys.stderr)
        return 1, None

    config_path = project_root / CONFIG_REL
    already_initialized = config_path.is_file()
    if already_initialized:
        print(
            f"Project already has Harness configuration at {CONFIG_REL.as_posix()}.",
            file=sys.stderr,
        )

    try:
        files = build_profile_file_map(chosen)
    except ContentPackError as exc:
        print(str(exc), file=sys.stderr)
        return 1, None

    report = materialize(project_root, files, dry_run=dry_run)
    print(format_report(report, dry_run=dry_run))

    if report.has_failures:
        print(
            "Init aborted (fail-closed). Resolve conflicts and retry.",
            file=sys.stderr,
        )
        return 1, report

    if dry_run:
        print("Dry-run complete. No files were written.")
    elif report.created:
        print(
            f"Initialized Harness project with profile '{chosen}' "
            f"({len(report.created)} file(s) created)."
        )
        print("Next: harness validate && harness generate <adapter>")
    else:
        print(f"Harness project already up to date for profile '{chosen}'.")

    return 0, report
