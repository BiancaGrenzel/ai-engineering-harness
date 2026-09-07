#!/usr/bin/env python3
"""Schema tests for harness configuration validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "harness.schema.json"
VALIDATOR = ROOT / "scripts" / "validate-config.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "harness"


def run_validator(config_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--config", str(config_path), "--schema", str(SCHEMA_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )


class HarnessSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import jsonschema  # noqa: F401
            import yaml  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(
                "Install scripts/requirements.txt before running tests"
            ) from exc

        if not SCHEMA_PATH.is_file():
            raise unittest.SkipTest(f"Missing schema: {SCHEMA_PATH}")

        with SCHEMA_PATH.open(encoding="utf-8") as handle:
            json.load(handle)  # schema must be valid JSON

    def test_valid_configuration(self) -> None:
        result = run_validator(FIXTURES / "valid.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Harness configuration is valid.", result.stdout)

    def test_real_repo_harness_yaml(self) -> None:
        result = run_validator(ROOT / ".harness" / "harness.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_version(self) -> None:
        result = run_validator(FIXTURES / "missing-version.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid", result.stderr.lower())

    def test_invalid_profile_structure(self) -> None:
        result = run_validator(FIXTURES / "invalid-profile.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("profile", result.stderr.lower())

    def test_rules_invalid_type(self) -> None:
        result = run_validator(FIXTURES / "rules-invalid-type.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rules", result.stderr.lower())

    def test_skills_invalid_type(self) -> None:
        result = run_validator(FIXTURES / "skills-invalid-type.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills", result.stderr.lower())

    def test_tools_invalid_type(self) -> None:
        result = run_validator(FIXTURES / "tools-invalid-type.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tools", result.stderr.lower())

    def test_unknown_property(self) -> None:
        result = run_validator(FIXTURES / "unknown-property.yaml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("additional", result.stderr.lower())

    def test_inline_invalid_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("version: 1\nprofile: Not_Valid\n", encoding="utf-8")
            result = run_validator(path)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
