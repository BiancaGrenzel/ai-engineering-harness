#!/usr/bin/env python3
"""Packaging and installed-CLI integration tests.

Verifies pyproject metadata and that an isolated ``pip install .`` yields a
working ``harness`` console script that does not depend on PYTHONPATH or the
repository checkout being on sys.path.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_SCHEMAS = ROOT / "schemas"
CURSOR_FIXTURE = (
    Path(__file__).resolve().parent / "adapters" / "cursor" / "fixtures" / "project"
)
CLAUDE_FIXTURE = (
    Path(__file__).resolve().parent / "adapters" / "claude" / "fixtures" / "project"
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None  # type: ignore[assignment]


def _load_pyproject() -> dict:
    if tomllib is None:
        raise unittest.SkipTest("tomllib requires Python 3.11+")
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


class PackagingMetadataTests(unittest.TestCase):
    def test_pyproject_exists(self) -> None:
        self.assertTrue((ROOT / "pyproject.toml").is_file())

    def test_package_metadata(self) -> None:
        data = _load_pyproject()
        project = data["project"]
        self.assertEqual(project["name"], "ai-engineering-harness")
        self.assertEqual(project["dynamic"], ["version"])
        self.assertIn("PyYAML", " ".join(project["dependencies"]))
        self.assertIn("jsonschema", " ".join(project["dependencies"]))
        scripts = project["scripts"]
        self.assertEqual(scripts["harness"], "harness.cli:main")

    def test_version_source_is_harness_package(self) -> None:
        data = _load_pyproject()
        dynamic = data["tool"]["setuptools"]["dynamic"]
        self.assertEqual(dynamic["version"]["attr"], "harness.__version__")
        from harness import __version__

        self.assertEqual(__version__, "0.1.1")

    def test_packages_include_harness_and_adapters(self) -> None:
        data = _load_pyproject()
        find = data["tool"]["setuptools"]["packages"]["find"]
        include = find["include"]
        self.assertIn("harness*", include)
        self.assertIn("adapters*", include)
        package_data = data["tool"]["setuptools"]["package-data"]
        self.assertIn("adapter.yaml", package_data["adapters.cursor"])
        self.assertIn("adapter.yaml", package_data["adapters.claude"])
        self.assertIn("_data/**/*", package_data["harness.content"])


class InstalledCliSmokeTests(unittest.TestCase):
    """Create a clean venv, install the package, exercise the console script."""

    _venv_dir: Path | None = None
    _harness_bin: Path | None = None
    _python_bin: Path | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if not CURSOR_FIXTURE.is_dir() or not CLAUDE_FIXTURE.is_dir():
            raise unittest.SkipTest("Adapter fixtures missing")
        if not CANONICAL_SCHEMAS.is_dir():
            raise unittest.SkipTest("Canonical schemas missing")

        cls._venv_dir = Path(tempfile.mkdtemp(prefix="harness-pkg-"))
        try:
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

            install = subprocess.run(
                [
                    str(cls._python_bin),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "pip",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if install.returncode != 0:
                raise unittest.SkipTest(
                    f"pip upgrade failed in isolated venv:\n{install.stderr}"
                )

            install = subprocess.run(
                [str(cls._python_bin), "-m", "pip", "install", str(ROOT)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            if install.returncode != 0:
                raise AssertionError(
                    "pip install . failed in isolated venv:\n"
                    f"{install.stdout}\n{install.stderr}"
                )
            if not cls._harness_bin.is_file():
                raise AssertionError(
                    f"Console script missing after install: {cls._harness_bin}"
                )
        except Exception:
            shutil.rmtree(cls._venv_dir, ignore_errors=True)
            cls._venv_dir = None
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._venv_dir is not None:
            shutil.rmtree(cls._venv_dir, ignore_errors=True)
            cls._venv_dir = None

    def _env_without_repo_pythonpath(self) -> dict[str, str]:
        env = os.environ.copy()
        # Ensure the installed package is used, not the repo via PYTHONPATH.
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        return env

    def _run_harness(
        self, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        assert self._harness_bin is not None
        return subprocess.run(
            [str(self._harness_bin), *args],
            cwd=str(cwd or tempfile.gettempdir()),
            capture_output=True,
            text=True,
            check=False,
            env=self._env_without_repo_pythonpath(),
        )

    def _seed_project(self, fixture: Path, dest: Path) -> Path:
        shutil.copytree(fixture, dest)
        # Schemas are optional for consumer projects; pack supplies them.
        return dest

    def test_console_script_version(self) -> None:
        from harness import __version__

        result = self._run_harness("version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), __version__)

    def test_validate_from_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._seed_project(CURSOR_FIXTURE, Path(tmp) / "project")
            nested = root / "src" / "components"
            nested.mkdir(parents=True)
            result = self._run_harness("validate", cwd=nested)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Harness configuration is valid.", result.stdout)

    def test_generate_cursor_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._seed_project(CURSOR_FIXTURE, Path(tmp) / "project")
            result = self._run_harness(
                "generate", "cursor", "--root", str(root), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("Dry-run", result.stdout)
            self.assertFalse((root / ".cursor").exists())

    def test_generate_claude_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._seed_project(CLAUDE_FIXTURE, Path(tmp) / "project")
            result = self._run_harness(
                "generate", "claude", "--root", str(root), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("Dry-run", result.stdout)
            self.assertFalse((root / ".claude").exists())

    def test_missing_harness_project_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            nested = empty / "a" / "b"
            nested.mkdir(parents=True)
            result = self._run_harness("validate", cwd=nested)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Harness configuration not found.", result.stderr)

    def test_installed_import_does_not_need_repo_on_path(self) -> None:
        assert self._python_bin is not None
        result = subprocess.run(
            [
                str(self._python_bin),
                "-c",
                "import harness, adapters.cursor, adapters.claude; "
                "from harness import __version__; print(__version__)",
            ],
            cwd=str(tempfile.gettempdir()),
            capture_output=True,
            text=True,
            check=False,
            env=self._env_without_repo_pythonpath(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        from harness import __version__

        self.assertEqual(result.stdout.strip(), __version__)

    def test_adapter_yaml_packaged(self) -> None:
        assert self._python_bin is not None
        script = (
            "from importlib import resources; "
            "from pathlib import Path; "
            "import adapters.cursor, adapters.claude; "
            "c = Path(adapters.cursor.__file__).with_name('adapter.yaml'); "
            "l = Path(adapters.claude.__file__).with_name('adapter.yaml'); "
            "assert c.is_file(), c; assert l.is_file(), l; print('ok')"
        )
        result = subprocess.run(
            [str(self._python_bin), "-c", script],
            cwd=str(tempfile.gettempdir()),
            capture_output=True,
            text=True,
            check=False,
            env=self._env_without_repo_pythonpath(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_content_pack_bundled_for_init(self) -> None:
        assert self._python_bin is not None
        script = (
            "from pathlib import Path; "
            "from harness import __version__; "
            "from harness.content.pack import ( "
            "  CONTENT_PACK_VERSION, content_pack_root, list_profiles); "
            "root = content_pack_root(); "
            "assert CONTENT_PACK_VERSION == __version__; "
            "assert (root / 'schemas' / 'harness.schema.json').is_file(), root; "
            "assert (root / 'profiles' / 'software-engineer.yaml').is_file(), root; "
            "assert 'software-engineer' in list_profiles(root); "
            "assert (root / 'rules' / 'core' / 'core.md').is_file(), root; "
            "assert (root / 'tools' / 'registry.yaml').is_file(), root; "
            "print(root)"
        )
        result = subprocess.run(
            [str(self._python_bin), "-c", script],
            cwd=str(tempfile.gettempdir()),
            capture_output=True,
            text=True,
            check=False,
            env=self._env_without_repo_pythonpath(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        pack_root = Path(result.stdout.strip())
        self.assertNotEqual(pack_root.resolve(), ROOT.resolve())
        self.assertTrue((pack_root / "tools" / "registry.yaml").is_file())
        self.assertTrue((pack_root / "docs" / "tools" / "token" / "rtk.md").is_file())


if __name__ == "__main__":
    unittest.main()
