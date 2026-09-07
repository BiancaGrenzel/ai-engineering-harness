#!/usr/bin/env python3
"""Tests for adapter path confinement (adapters.common.apply)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.apply import (
    PathConfinementError,
    PlannedFile,
    apply_preflighted_plan,
    confined_path,
    preflight,
)
from adapters.common.resolve import MANAGED_MARKER


class PathConfinementTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "project"
        self.root.mkdir()
        (self.root / "safe").mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_normal_relative_path_allowed(self) -> None:
        path = confined_path(self.root, "safe/out.md")
        self.assertEqual(path, (self.root / "safe" / "out.md").resolve())

    def test_parent_escape_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, "../escape.md")

    def test_double_parent_escape_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, "../../escape.md")

    def test_nested_parent_escape_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, "safe/../../outside.md")

    def test_posix_absolute_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, "/etc/passwd")

    def test_windows_drive_absolute_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, r"C:\Windows\System32\drivers\etc\hosts")
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, "C:/Windows/System32/drivers/etc/hosts")

    def test_unc_path_rejected(self) -> None:
        with self.assertRaises(PathConfinementError):
            confined_path(self.root, r"\\server\share\file.txt")

    def test_preflight_rejects_escape_with_zero_writes(self) -> None:
        planned = [
            PlannedFile(
                relative_path="../evil.md",
                content=f"{MANAGED_MARKER}\nx\n",
                kind="rule",
            )
        ]
        outside = self.root.parent / "evil.md"
        self.assertFalse(outside.exists())
        report = preflight(self.root, planned, previous_files=[])
        self.assertTrue(report.has_failures)
        self.assertTrue(report.errors)
        self.assertFalse(outside.exists())
        self.assertFalse((self.root / "evil.md").exists())

    def test_stale_removal_outside_root_rejected(self) -> None:
        planned: list[PlannedFile] = []
        report = preflight(
            self.root,
            planned,
            previous_files=["../outside-stale.md"],
        )
        self.assertTrue(report.has_failures)
        self.assertTrue(any("escapes" in err or "Absolute" in err or "rejected" in err for err in report.errors))
        self.assertEqual(report.removed, [])

    def test_apply_refuses_when_path_errors(self) -> None:
        planned = [
            PlannedFile(
                relative_path="../evil.md",
                content=f"{MANAGED_MARKER}\nx\n",
                kind="rule",
            )
        ]
        report = preflight(self.root, planned, previous_files=[])
        self.assertTrue(report.has_failures)
        with self.assertRaises(AssertionError):
            apply_preflighted_plan(
                self.root,
                planned,
                report,
                manifest_path=self.root / ".harness" / "adapters" / "test.managed.json",
                adapter="test",
                adapter_version=1,
                dry_run=False,
            )
        self.assertFalse((self.root.parent / "evil.md").exists())

    def test_apply_writes_only_under_root(self) -> None:
        rel = "safe/managed.md"
        content = f"{MANAGED_MARKER}\nok\n"
        planned = [PlannedFile(relative_path=rel, content=content, kind="rule")]
        report = preflight(self.root, planned, previous_files=[])
        self.assertFalse(report.has_failures)
        apply_preflighted_plan(
            self.root,
            planned,
            report,
            manifest_path=self.root / ".harness" / "adapters" / "test.managed.json",
            adapter="test",
            adapter_version=1,
            dry_run=False,
        )
        written = self.root / rel
        self.assertTrue(written.is_file())
        self.assertEqual(written.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
