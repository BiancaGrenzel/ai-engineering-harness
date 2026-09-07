#!/usr/bin/env python3
"""Tests for the Harness CLI (thin interface over existing APIs)."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PROJECT = (
    Path(__file__).resolve().parent / "adapters" / "cursor" / "fixtures" / "project"
)
CANONICAL_SCHEMAS = ROOT / "schemas"
VALID_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "harness" / "valid.yaml"
INVALID_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "harness" / "missing-version.yaml"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness import __version__
from harness import cli as harness_cli
from harness import dispatch
from harness.project import find_project_root


def _deps_available() -> bool:
    try:
        import jsonschema  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def _run_module(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    # python -m resolves packages from cwd; keep the repo root on PYTHONPATH so
    # the CLI is importable when tests run from a subdirectory or temp project.
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(ROOT) if not existing else os.pathsep.join([str(ROOT), existing])
    )
    return subprocess.run(
        [sys.executable, "-m", "harness", *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class HarnessCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_available():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")

    def test_help(self) -> None:
        result = _run_module("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("init", result.stdout.lower())
        self.assertIn("validate", result.stdout.lower())
        self.assertIn("generate", result.stdout.lower())
        self.assertIn("tools", result.stdout.lower())
        self.assertIn("version", result.stdout.lower())
        self.assertNotIn("doctor", result.stdout.lower())

    def test_validate_help(self) -> None:
        result = _run_module("validate", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("harness.yaml", result.stdout)

    def test_generate_help(self) -> None:
        result = _run_module("generate", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("cursor", result.stdout.lower())

    def test_generate_cursor_help(self) -> None:
        result = _run_module("generate", "cursor", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dry-run", result.stdout)

    def test_version(self) -> None:
        result = _run_module("version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), __version__)

    def test_validate_repo_config(self) -> None:
        result = _run_module("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Harness configuration is valid.", result.stdout)

    def test_validate_from_subdirectory(self) -> None:
        subdir = ROOT / "docs" / "architecture"
        self.assertTrue(subdir.is_dir())
        result = _run_module("validate", cwd=subdir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Harness configuration is valid.", result.stdout)

    def test_validate_valid_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / ".harness").mkdir()
            shutil.copy(VALID_FIXTURE, root / ".harness" / "harness.yaml")
            (root / "schemas").mkdir()
            shutil.copy(
                CANONICAL_SCHEMAS / "harness.schema.json",
                root / "schemas" / "harness.schema.json",
            )
            result = _run_module("validate", "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Harness configuration is valid.", result.stdout)

    def test_validate_invalid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / ".harness").mkdir()
            shutil.copy(INVALID_FIXTURE, root / ".harness" / "harness.yaml")
            (root / "schemas").mkdir()
            shutil.copy(
                CANONICAL_SCHEMAS / "harness.schema.json",
                root / "schemas" / "harness.schema.json",
            )
            result = _run_module("validate", "--root", str(root))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Harness configuration is invalid.", result.stderr)

    def test_validate_missing_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            nested = empty / "a" / "b"
            nested.mkdir(parents=True)
            result = _run_module("validate", cwd=nested)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Harness configuration not found.", result.stderr)

    def test_find_project_root_walks_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            nested = root / "src" / "components"
            nested.mkdir(parents=True)
            (root / ".harness").mkdir()
            (root / ".harness" / "harness.yaml").write_text(
                "version: 1\nprofile: software-engineer\n",
                encoding="utf-8",
            )
            found = find_project_root(nested)
            self.assertEqual(found, root.resolve())

    def test_unknown_adapter(self) -> None:
        result = _run_module("generate", "gemini")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown or unsupported adapter: gemini", result.stderr)

    def test_generate_cursor_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            shutil.copytree(FIXTURE_PROJECT, root)
            result = _run_module(
                "generate", "cursor", "--root", str(root), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry-run", result.stdout)
            self.assertFalse((root / ".cursor").exists())

    def test_generate_cursor_with_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            shutil.copytree(FIXTURE_PROJECT, root)
            result = _run_module("generate", "cursor", "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (root / ".cursor" / "rules" / "harness" / "core--core.mdc").is_file()
            )
            self.assertTrue(
                (
                    root
                    / ".cursor"
                    / "skills"
                    / "harness"
                    / "task-analysis"
                    / "SKILL.md"
                ).is_file()
            )
            manifest = root / ".harness" / "adapters" / "cursor.managed.json"
            self.assertTrue(manifest.is_file())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["adapter"], "cursor")

    def test_generate_claude_dry_run(self) -> None:
        claude_fixture = (
            Path(__file__).resolve().parent / "adapters" / "claude" / "fixtures" / "project"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            shutil.copytree(claude_fixture, root)
            result = _run_module(
                "generate", "claude", "--root", str(root), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry-run", result.stdout)
            self.assertFalse((root / ".claude").exists())

    def test_generate_claude_with_root(self) -> None:
        claude_fixture = (
            Path(__file__).resolve().parent / "adapters" / "claude" / "fixtures" / "project"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            shutil.copytree(claude_fixture, root)
            result = _run_module("generate", "claude", "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (root / ".claude" / "rules" / "harness" / "core--core.md").is_file()
            )
            self.assertTrue(
                (root / ".claude" / "skills" / "task-analysis" / "SKILL.md").is_file()
            )
            manifest = root / ".harness" / "adapters" / "claude.managed.json"
            self.assertTrue(manifest.is_file())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["adapter"], "claude")

    def test_cli_dispatches_to_claude_adapter(self) -> None:
        """CLI must call the Claude adapter run(); it must not reimplement generation."""
        fake_root = Path(tempfile.mkdtemp())
        try:
            (fake_root / ".harness").mkdir()
            (fake_root / ".harness" / "harness.yaml").write_text(
                "version: 1\nprofile: software-engineer\n",
                encoding="utf-8",
            )
            with mock.patch(
                "adapters.claude.generate.run", return_value=0
            ) as run_mock:
                code = harness_cli.main(
                    ["generate", "claude", "--root", str(fake_root), "--dry-run"]
                )
            self.assertEqual(code, 0)
            run_mock.assert_called_once_with(fake_root.resolve(), dry_run=True)
        finally:
            shutil.rmtree(fake_root, ignore_errors=True)

    def test_cli_dispatches_to_existing_adapter(self) -> None:
        """CLI must call the Cursor adapter run(); it must not reimplement generation."""
        fake_root = Path(tempfile.mkdtemp())
        try:
            (fake_root / ".harness").mkdir()
            (fake_root / ".harness" / "harness.yaml").write_text(
                "version: 1\nprofile: software-engineer\n",
                encoding="utf-8",
            )
            with mock.patch(
                "adapters.cursor.generate.run", return_value=0
            ) as run_mock:
                code = harness_cli.main(
                    ["generate", "cursor", "--root", str(fake_root), "--dry-run"]
                )
            self.assertEqual(code, 0)
            run_mock.assert_called_once_with(fake_root.resolve(), dry_run=True)
        finally:
            shutil.rmtree(fake_root, ignore_errors=True)

    def test_cli_does_not_duplicate_generation_logic(self) -> None:
        """Smoke check: CLI modules must not define plan/apply/render helpers."""
        cli_dir = ROOT / "harness"
        banned = (
            "build_plan",
            "rule_wrapper_content",
            "skill_wrapper_content",
            "apply_preflighted_plan",
            "preflight",
            "MANAGED_MARKER",
        )
        for path in cli_dir.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for name in banned:
                self.assertNotIn(
                    f"def {name}",
                    text,
                    f"{path.name} must not define {name}",
                )
                if name == "MANAGED_MARKER":
                    self.assertNotIn(name, text)

    def test_dispatch_unknown_adapter_direct(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = dispatch.generate("gemini", Path("."), dry_run=True)
        self.assertEqual(code, 1)
        self.assertIn("Unknown or unsupported adapter: gemini", buf.getvalue())

    def test_main_no_args_prints_help(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = harness_cli.main([])
        self.assertEqual(code, 0)
        self.assertIn("validate", buf.getvalue().lower())


class HarnessCliIntegrationTests(unittest.TestCase):
    """CLI → Cursor adapter → generation → on-disk output."""

    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_available():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")
        if not FIXTURE_PROJECT.is_dir():
            raise unittest.SkipTest(f"Missing fixtures: {FIXTURE_PROJECT}")

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "project"
        shutil.copytree(FIXTURE_PROJECT, self.root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_cli_generate_integration(self) -> None:
        nested = self.root / "src" / "components"
        nested.mkdir(parents=True)
        result = _run_module("generate", "cursor", cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        rule = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        skill = (
            self.root / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
        )
        self.assertTrue(rule.is_file())
        self.assertTrue(skill.is_file())
        self.assertIn("Generation", result.stdout)
        rule_text = rule.read_text(encoding="utf-8")
        self.assertNotIn("@rules/", rule_text)
        self.assertIn("Understand before modifying", rule_text)


if __name__ == "__main__":
    unittest.main()
