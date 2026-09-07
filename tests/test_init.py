#!/usr/bin/env python3
"""Tests for ``harness init`` project materialization."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent

try:
    import jsonschema  # noqa: F401
    import yaml  # noqa: F401
except ImportError:  # pragma: no cover
    jsonschema = None  # type: ignore[assignment]
    yaml = None  # type: ignore[assignment]


def _deps_ready() -> bool:
    return jsonschema is not None and yaml is not None


class InitUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_ready():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="harness-init-")
        self.root = Path(self._tmp.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_init(self, *argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "harness", "init", *argv],
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_init_basic_with_profile(self) -> None:
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        harness = self.root / ".harness"
        self.assertTrue((harness / "harness.yaml").is_file())
        self.assertTrue((harness / "profiles" / "software-engineer.yaml").is_file())
        self.assertTrue((harness / "schemas" / "harness.schema.json").is_file())
        self.assertTrue((harness / "rules" / "core" / "core.md").is_file())
        self.assertTrue(
            (harness / "skills" / "core" / "task-analysis" / "SKILL.md").is_file()
        )
        self.assertTrue((harness / "tools" / "registry.yaml").is_file())
        self.assertTrue((harness / "docs" / "tools" / "token" / "rtk.md").is_file())
        for rel in ("profiles", "rules", "skills", "schemas", "tools", "docs"):
            self.assertFalse((self.root / rel).exists(), rel)
        self.assertFalse((self.root / ".cursor").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_init_profile_software_engineer(self) -> None:
        from harness.content.pack import build_profile_file_map, load_profile

        profile = load_profile("software-engineer")
        files = build_profile_file_map("software-engineer")
        self.assertEqual(profile["name"], "software-engineer")
        self.assertIn(".harness/harness.yaml", files)
        self.assertIn(".harness/profiles/software-engineer.yaml", files)
        self.assertIn(".harness/schemas/harness.schema.json", files)
        self.assertIn(".harness/tools/registry.yaml", files)
        self.assertTrue(any(path.startswith(".harness/rules/") for path in files))
        self.assertTrue(any(path.endswith("/SKILL.md") for path in files))
        self.assertFalse(any(path.startswith("profiles/") for path in files))
        self.assertFalse(any(path.startswith("rules/") for path in files))
        harness_text = files[".harness/harness.yaml"].decode("utf-8")
        self.assertIn("profile: software-engineer", harness_text)
        self.assertNotIn("\nrules:", harness_text)
        self.assertNotIn("\nskills:", harness_text)
        self.assertNotIn("\ntools:", harness_text)

    def test_unknown_profile(self) -> None:
        result = self._run_init("--profile", "does-not-exist")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown profile", result.stderr)

    def test_already_initialized_idempotent(self) -> None:
        first = self._run_init("--profile", "software-engineer")
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        second = self._run_init("--profile", "software-engineer")
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        self.assertIn("already has Harness", second.stderr)
        self.assertIn("Unchanged", second.stdout)
        self.assertNotIn("Created (", second.stdout)

    def test_conflict_with_divergent_harness_yaml(self) -> None:
        (self.root / ".harness").mkdir()
        (self.root / ".harness" / "harness.yaml").write_text(
            "version: 1\nprofile: other\n",
            encoding="utf-8",
        )
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Conflicts", result.stdout)
        self.assertIn(".harness/harness.yaml", result.stdout)
        self.assertIn("fail-closed", result.stderr)
        self.assertFalse((self.root / ".harness" / "profiles").exists())

    def test_conflict_with_divergent_profile_file(self) -> None:
        (self.root / ".harness" / "profiles").mkdir(parents=True)
        (self.root / ".harness" / "profiles" / "software-engineer.yaml").write_text(
            "name: software-engineer\ndescription: divergent\nrules: []\nskills: []\ntools: []\n",
            encoding="utf-8",
        )
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Conflicts", result.stdout)
        self.assertIn(".harness/profiles/software-engineer.yaml", result.stdout)
        self.assertIn("fail-closed", result.stderr)
        self.assertFalse((self.root / ".harness" / "harness.yaml").exists())
        for rel in ("profiles", "rules", "skills", "schemas", "tools", "docs"):
            self.assertFalse((self.root / rel).exists(), rel)

    def test_dry_run_writes_nothing(self) -> None:
        result = self._run_init("--profile", "software-engineer", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Dry-run", result.stdout)
        self.assertFalse((self.root / ".harness").exists())
        for rel in ("profiles", "rules", "skills", "schemas", "tools", "docs"):
            self.assertFalse((self.root / rel).exists(), rel)

    def test_noninteractive_requires_profile(self) -> None:
        from harness.init import resolve_profile_choice

        chosen, error = resolve_profile_choice(None, interactive=False)
        self.assertIsNone(chosen)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("--profile", error)

    def test_materialized_structure(self) -> None:
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

        expected = (
            ".harness/harness.yaml",
            ".harness/profiles/software-engineer.yaml",
            ".harness/schemas/harness.schema.json",
            ".harness/schemas/profile.schema.json",
            ".harness/schemas/tool-registry.schema.json",
            ".harness/tools/registry.yaml",
            ".harness/docs/tools/token/rtk.md",
            ".harness/rules/core/core.md",
            ".harness/skills/core/task-analysis/SKILL.md",
        )
        for rel in expected:
            self.assertTrue((self.root / rel).is_file(), rel)
        for rel in ("profiles", "rules", "skills", "schemas", "tools", "docs"):
            self.assertFalse((self.root / rel).exists(), rel)
        self.assertFalse((self.root / ".cursor").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_validate_and_resolve_after_init(self) -> None:
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

        from adapters.common.resolve import resolve_harness
        from harness import config_validation

        code = config_validation.validate_repository(self.root)
        self.assertEqual(code, 0)
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.profile, "software-engineer")
        self.assertEqual(resolved.content_root, (self.root / ".harness").resolve())
        self.assertTrue(resolved.rule_files)
        self.assertTrue(resolved.skill_files)
        self.assertTrue(resolved.tool_files)
        self.assertTrue(all(path.is_file() for path in resolved.rule_files))
        content_root = (self.root / ".harness").resolve()
        for path in (*resolved.rule_files, *resolved.skill_files, *resolved.tool_files):
            self.assertTrue(
                str(path.resolve()).startswith(str(content_root)),
                path,
            )

    def test_does_not_modify_files_outside_harness_areas(self) -> None:
        sentinel = self.root / "src" / "app.py"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text("print('hello')\n", encoding="utf-8")
        agents = self.root / "AGENTS.md"
        agents.write_text("# keep me\n", encoding="utf-8")
        package_json = self.root / "package.json"
        package_json.write_text('{"name":"demo"}\n', encoding="utf-8")

        before = {
            sentinel: sentinel.read_bytes(),
            agents: agents.read_bytes(),
            package_json: package_json.read_bytes(),
        }
        result = self._run_init("--profile", "software-engineer")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_cli_exit_codes(self) -> None:
        ok = self._run_init("--profile", "software-engineer")
        self.assertEqual(ok.returncode, 0)
        bad = self._run_init("--profile", "missing-profile")
        self.assertEqual(bad.returncode, 1)

        (self.root / ".harness").mkdir(exist_ok=True)
        (self.root / ".harness" / "harness.yaml").write_text(
            "version: 1\nprofile: other\n",
            encoding="utf-8",
        )
        conflict = self._run_init("--profile", "software-engineer")
        self.assertEqual(conflict.returncode, 1)

    def test_init_root_flag(self) -> None:
        other = Path(self._tmp.name) / "other"
        other.mkdir()
        result = self._run_init(
            "--profile", "software-engineer", "--root", str(other), cwd=self.root
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((other / ".harness" / "harness.yaml").is_file())
        self.assertTrue(
            (other / ".harness" / "profiles" / "software-engineer.yaml").is_file()
        )
        self.assertFalse((other / "profiles").exists())
        self.assertFalse((self.root / ".harness").exists())


class InitPackagingSmokeTests(unittest.TestCase):
    """Exercise init / validate / generate from an isolated pip-installed environment."""

    _venv_dir: Path | None = None
    _harness_bin: Path | None = None
    _python_bin: Path | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_ready():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")

        cls._venv_dir = Path(tempfile.mkdtemp(prefix="harness-init-pkg-"))
        try:
            import venv

            builder = venv.EnvBuilder(with_pip=True, clear=True)
            builder.create(cls._venv_dir)
            if os.name == "nt":
                scripts = cls._venv_dir / "Scripts"
                cls._python_bin = scripts / "python.exe"
                cls._harness_bin = scripts / "harness.exe"
            else:
                scripts = cls._venv_dir / "bin"
                cls._python_bin = scripts / "python"
                cls._harness_bin = scripts / "harness"

            upgrade = subprocess.run(
                [str(cls._python_bin), "-m", "pip", "install", "--upgrade", "pip"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if upgrade.returncode != 0:
                raise unittest.SkipTest(f"pip upgrade failed:\n{upgrade.stderr}")

            install = subprocess.run(
                [str(cls._python_bin), "-m", "pip", "install", str(ROOT)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if install.returncode != 0:
                raise AssertionError(
                    "pip install . failed:\n" + install.stdout + "\n" + install.stderr
                )
            if not cls._harness_bin.is_file():
                raise AssertionError(f"Missing console script: {cls._harness_bin}")
        except Exception:
            shutil.rmtree(cls._venv_dir, ignore_errors=True)
            cls._venv_dir = None
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._venv_dir is not None:
            shutil.rmtree(cls._venv_dir, ignore_errors=True)
            cls._venv_dir = None

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        return env

    def _run(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert self._harness_bin is not None
        return subprocess.run(
            [str(self._harness_bin), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            env=self._env(),
        )

    def test_external_project_init_validate_generate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="external-project-") as tmp:
            project = Path(tmp) / "external-project"
            project.mkdir()
            (project / "src").mkdir()
            (project / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (project / "package.json").write_text('{"name":"external"}\n', encoding="utf-8")

            init = self._run("init", "--profile", "software-engineer", cwd=project)
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            harness = project / ".harness"
            self.assertTrue((harness / "harness.yaml").is_file())
            self.assertTrue((harness / "profiles" / "software-engineer.yaml").is_file())
            self.assertTrue((harness / "schemas" / "harness.schema.json").is_file())
            self.assertTrue((harness / "rules" / "core" / "core.md").is_file())
            self.assertTrue(
                (harness / "skills" / "core" / "task-analysis" / "SKILL.md").is_file()
            )
            self.assertTrue((harness / "tools" / "registry.yaml").is_file())
            self.assertTrue((harness / "docs" / "tools" / "token" / "rtk.md").is_file())
            for rel in ("profiles", "rules", "skills", "schemas", "tools", "docs"):
                self.assertFalse((project / rel).exists(), rel)
            self.assertEqual((project / "src" / "main.py").read_text(encoding="utf-8"), "x = 1\n")

            assert self._python_bin is not None
            probe = subprocess.run(
                [
                    str(self._python_bin),
                    "-c",
                    "from pathlib import Path; "
                    "from harness.content.pack import content_pack_root, project_content_root; "
                    f"project = Path({str(project)!r}); "
                    "pack = content_pack_root(); "
                    "local = project_content_root(project); "
                    "assert local == (project / '.harness').resolve(), (local, project); "
                    "assert pack != project.resolve(); "
                    "print(pack)",
                ],
                cwd=str(project),
                capture_output=True,
                text=True,
                check=False,
                env=self._env(),
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            pack_root = Path(probe.stdout.strip())
            self.assertTrue(
                (pack_root / "schemas" / "harness.schema.json").is_file(),
                pack_root,
            )
            self.assertNotEqual(pack_root.resolve(), ROOT.resolve())

            validate = self._run("validate", cwd=project)
            self.assertEqual(validate.returncode, 0, validate.stderr + validate.stdout)

            cursor = self._run("generate", "cursor", "--dry-run", cwd=project)
            self.assertEqual(cursor.returncode, 0, cursor.stderr + cursor.stdout)
            self.assertIn("Dry-run", cursor.stdout)

            claude = self._run("generate", "claude", "--dry-run", cwd=project)
            self.assertEqual(claude.returncode, 0, claude.stderr + claude.stdout)
            self.assertIn("Dry-run", claude.stdout)

            cursor_write = self._run("generate", "cursor", cwd=project)
            self.assertEqual(cursor_write.returncode, 0, cursor_write.stderr + cursor_write.stdout)
            rule = project / ".cursor" / "rules" / "harness" / "core--core.mdc"
            skill = (
                project / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
            )
            self.assertTrue(rule.is_file())
            self.assertTrue(skill.is_file())
            rule_text = rule.read_text(encoding="utf-8")
            skill_text = skill.read_text(encoding="utf-8")
            self.assertNotIn("@rules/", rule_text)
            self.assertIn("Understand before modifying", rule_text)
            self.assertIn("# Task Analysis", skill_text)
            self.assertNotIn("skills/core/task-analysis", skill_text)
            self.assertNotIn(str(pack_root), rule_text)
            self.assertNotIn(str(pack_root), skill_text)

            claude_write = self._run("generate", "claude", cwd=project)
            self.assertEqual(
                claude_write.returncode, 0, claude_write.stderr + claude_write.stdout
            )
            claude_rule = project / ".claude" / "rules" / "harness" / "core--core.md"
            claude_skill = project / ".claude" / "skills" / "task-analysis" / "SKILL.md"
            self.assertTrue(claude_rule.is_file())
            self.assertTrue(claude_skill.is_file())
            # Vendor projections stay at project root, not under .harness/.
            self.assertFalse((project / ".harness" / ".cursor").exists())
            self.assertFalse((project / ".harness" / ".claude").exists())

            nested = project / "src" / "components"
            nested.mkdir(parents=True)
            nested_validate = self._run("validate", cwd=nested)
            self.assertEqual(
                nested_validate.returncode, 0, nested_validate.stderr + nested_validate.stdout
            )

            health = self._run("tools", "health", "rtk", cwd=project)
            self.assertIn(health.returncode, (0, 1), health.stderr + health.stdout)
            self.assertNotIn("Tool Registry not found", health.stderr)
            self.assertNotIn("Unknown Tool id", health.stderr)

            again = self._run("init", "--profile", "software-engineer", cwd=project)
            self.assertEqual(again.returncode, 0, again.stderr + again.stdout)


class InitApiHelpersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_ready():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")

    def test_format_and_plan_helpers(self) -> None:
        from harness.content.materialize import format_report, plan_materialization

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {"a.txt": b"one\n", "b.txt": b"two\n"}
            (root / "b.txt").write_bytes(b"two\n")
            (root / "c_conflict.txt").write_text("nope", encoding="utf-8")
            files["c_conflict.txt"] = b"yes\n"
            report = plan_materialization(root, files)
            self.assertEqual(report.created, ["a.txt"])
            self.assertEqual(report.unchanged, ["b.txt"])
            self.assertEqual(report.conflicts, ["c_conflict.txt"])
            text = format_report(report, dry_run=True)
            self.assertIn("Dry-run: Created", text)
            self.assertIn("Conflicts", text)

    def test_interactive_selection(self) -> None:
        from harness.init import select_profile_interactive

        with mock.patch("builtins.input", return_value="1"):
            chosen = select_profile_interactive(["software-engineer"])
        self.assertEqual(chosen, "software-engineer")

        with mock.patch("builtins.input", return_value="software-engineer"):
            chosen = select_profile_interactive(["software-engineer"])
        self.assertEqual(chosen, "software-engineer")

    def test_content_pack_version_matches_harness(self) -> None:
        from harness import __version__
        from harness.content.pack import CONTENT_PACK_VERSION

        self.assertEqual(CONTENT_PACK_VERSION, __version__)


if __name__ == "__main__":
    unittest.main()
