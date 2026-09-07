#!/usr/bin/env python3
"""Tests for the Cursor adapter generator and shared adapter helpers.

Fixtures live under tests/adapters/cursor/fixtures/ (isolated from the real
.cursor/ directory). The test module stays at tests/ so unittest discovery
does not shadow the top-level adapters package.

Fixture projects carry minimal trees for inventory; they intentionally omit
``schemas/`` so resolve falls back to the installed/source content pack unless
a test materializes a full project-local pack.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PROJECT = (
    Path(__file__).resolve().parent / "adapters" / "cursor" / "fixtures" / "project"
)
GENERATOR = ROOT / "adapters" / "cursor" / "generate.py"
ADAPTER_YAML = ROOT / "adapters" / "cursor" / "adapter.yaml"
CANONICAL_SCHEMAS = ROOT / "schemas"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.apply import PlannedFile, detect_write_conflicts, preflight
from adapters.common.metadata import (
    AdapterMetadataError,
    assert_plan_matches_capabilities,
    load_adapter_metadata,
)
from adapters.common.resolve import MANAGED_MARKER, ResolutionError, resolve_harness
from adapters.cursor import generate as cursor_generate


def _deps_available() -> bool:
    try:
        import jsonschema  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def _write_harness(root: Path, text: str) -> None:
    path = root / ".harness" / "harness.yaml"
    path.write_text(text, encoding="utf-8")


class CursorAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_available():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")
        if not FIXTURE_PROJECT.is_dir():
            raise unittest.SkipTest(f"Missing fixtures: {FIXTURE_PROJECT}")
        if not CANONICAL_SCHEMAS.is_dir():
            raise unittest.SkipTest(f"Missing canonical schemas: {CANONICAL_SCHEMAS}")

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "project"
        shutil.copytree(FIXTURE_PROJECT, self.root)
        # Do not copy schemas/: project_content_root would treat this incomplete
        # fixture as a full project-local pack. Resolution uses the content pack.

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # --- Configuration ---

    def test_valid_harness_yaml(self) -> None:
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.version, 1)
        self.assertEqual(resolved.profile, "software-engineer")

    def test_valid_profile(self) -> None:
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.rule_ids, ["core"])
        self.assertEqual(resolved.skill_ids, ["task-analysis"])
        self.assertEqual(resolved.tool_ids, ["rtk"])

    def test_existing_rule(self) -> None:
        resolved = resolve_harness(self.root)
        self.assertTrue(any(path.name == "core.md" for path in resolved.rule_files))

    def test_existing_skill(self) -> None:
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.skill_files[0].name, "SKILL.md")

    def test_existing_tool(self) -> None:
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.tool_files[0].stem, "rtk")

    def test_missing_resource_errors(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\nrules:\n  - missing-rule\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )
        with self.assertRaises(ResolutionError):
            resolve_harness(self.root)
        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 1)

    # --- Profile inheritance / replacement ---

    def test_rules_inherit_from_profile(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(
            resolved.rule_ids,
            ["core", "context", "security", "quality", "production"],
        )

    def test_skills_inherit_from_profile(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\ntools:\n  - rtk\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(
            resolved.skill_ids,
            [
                "task-analysis",
                "planning",
                "context-engineering",
                "research",
                "verification",
                "token-optimization",
            ],
        )

    def test_tools_inherit_from_profile(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\nskills:\n  - task-analysis\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.tool_ids, ["rtk"])

    def test_explicit_rules_replace_profile_rules(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - security\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.rule_ids, ["security"])
        self.assertFalse(any(path.name == "core.md" for path in resolved.rule_files))
        self.assertTrue(any(path.name == "security.md" for path in resolved.rule_files))

    def test_explicit_skills_replace_profile_skills(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\n"
            "skills:\n  - verification\ntools:\n  - rtk\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.skill_ids, ["verification"])

    def test_explicit_tools_replace_profile_tools(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\nskills:\n  - task-analysis\n"
            "tools: []\n",
        )
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.tool_ids, [])
        self.assertEqual(resolved.tool_files, [])

    def test_unknown_tool_id_not_in_registry(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\nskills:\n  - task-analysis\n"
            "tools:\n  - not-registered\n",
        )
        with self.assertRaises(ResolutionError) as ctx:
            resolve_harness(self.root)
        self.assertIn("Unknown Tool id", str(ctx.exception))

    def test_tool_doc_without_registry_entry_is_not_enough(self) -> None:
        """docs/tools alone must not satisfy Tool identity."""
        orphan = self.root / "docs" / "tools" / "token" / "orphan-only.md"
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("# orphan\n", encoding="utf-8")
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\nskills:\n  - task-analysis\n"
            "tools:\n  - orphan-only\n",
        )
        with self.assertRaises(ResolutionError):
            resolve_harness(self.root)

    def test_project_local_registry_is_not_required(self) -> None:
        """Without schemas/, resolve falls back to the content-pack Registry."""
        project_registry = self.root / "tools" / "registry.yaml"
        if project_registry.is_file():
            project_registry.unlink()
        resolved = resolve_harness(self.root)
        self.assertEqual(resolved.tool_ids, ["rtk"])
        self.assertTrue(resolved.tool_files)
        self.assertNotEqual(resolved.content_root, self.root.resolve())

    # --- Adapter metadata ---

    def test_adapter_metadata_loading(self) -> None:
        metadata = load_adapter_metadata(ADAPTER_YAML)
        self.assertEqual(metadata.name, "cursor")
        self.assertEqual(metadata.agent, "cursor")
        self.assertEqual(metadata.version, 1)
        self.assertIn("rules", metadata.supported_capabilities)
        self.assertIn("skills", metadata.supported_capabilities)
        self.assertIn("tools", metadata.unsupported_capabilities)
        self.assertEqual(
            metadata.output_path("managed_manifest"),
            ".harness/adapters/cursor.managed.json",
        )

    def test_adapter_metadata_rejects_capability_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "adapter.yaml"
            path.write_text(
                "name: bad\nagent: bad\nversion: 1\nstatus: experimental\n"
                "supported_capabilities:\n  - rules\n"
                "unsupported_capabilities:\n  - rules\n"
                "output:\n  managed_manifest: x.json\n  rules_dir: r\n",
                encoding="utf-8",
            )
            with self.assertRaises(AdapterMetadataError):
                load_adapter_metadata(path)

    def test_adapter_metadata_matches_behavior(self) -> None:
        metadata = load_adapter_metadata(ADAPTER_YAML)
        resolved = resolve_harness(self.root)
        planned, _warnings = cursor_generate.build_plan(resolved, metadata)
        kinds = {item.kind for item in planned}
        self.assertEqual(kinds, {"rule", "skill"})
        assert_plan_matches_capabilities(metadata, kinds)
        self.assertTrue(any(item.kind == "rule" for item in planned))
        self.assertTrue(any(item.kind == "skill" for item in planned))
        self.assertFalse(any(item.kind == "tool" for item in planned))

        unsupported = mock.Mock()
        unsupported.name = "cursor"
        unsupported.supports = lambda cap: cap == "rules"
        with self.assertRaises(AdapterMetadataError):
            assert_plan_matches_capabilities(unsupported, {"rule", "skill"})

    # --- Generation ---

    def test_initial_generation(self) -> None:
        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 0)
        rule = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        skill = self.root / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
        manifest = self.root / ".harness" / "adapters" / "cursor.managed.json"
        self.assertTrue(rule.is_file())
        self.assertTrue(skill.is_file())
        self.assertTrue(manifest.is_file())
        rule_text = rule.read_text(encoding="utf-8")
        self.assertIn(MANAGED_MARKER, rule_text)
        self.assertNotIn("@rules/", rule_text)
        self.assertIn("Understand before modifying", rule_text)
        self.assertIn("alwaysApply: false", rule_text)
        self.assertIn("description:", rule_text)
        skill_text = skill.read_text(encoding="utf-8")
        self.assertIn(MANAGED_MARKER, skill_text)
        self.assertIn("# Task Analysis", skill_text)
        self.assertNotIn("skills/core/task-analysis", skill_text)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["adapter"], "cursor")
        self.assertEqual(data["adapter_version"], 1)
        self.assertEqual(data["marker"], MANAGED_MARKER)
        self.assertIn(".cursor/rules/harness/core--core.mdc", data["files"])

    def test_repeated_generation_idempotent(self) -> None:
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        rule = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        first = rule.read_text(encoding="utf-8")
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        second = rule.read_text(encoding="utf-8")
        self.assertEqual(first, second)

    def test_harness_managed_file_updated(self) -> None:
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        rule = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        rule.write_text(
            f"---\nalwaysApply: false\n---\n\n{MANAGED_MARKER}\n\nstale\n",
            encoding="utf-8",
        )
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        text = rule.read_text(encoding="utf-8")
        self.assertIn("Understand before modifying", text)
        self.assertNotIn("stale", text)

    def test_user_managed_file_not_overwritten(self) -> None:
        target = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        target.parent.mkdir(parents=True, exist_ok=True)
        original = "---\nalwaysApply: false\n---\n\nuser owned\n"
        target.write_text(original, encoding="utf-8")
        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 1)
        self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_conflict_reported(self) -> None:
        target = self.root / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# user skill\n", encoding="utf-8")
        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 1)
        self.assertEqual(target.read_text(encoding="utf-8"), "# user skill\n")

    def test_conflict_is_fail_closed(self) -> None:
        """One conflict must prevent writing any planned outputs or the manifest."""
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\n  - security\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )

        conflict_target = self.root / ".cursor" / "rules" / "harness" / "security--security.mdc"
        conflict_target.parent.mkdir(parents=True, exist_ok=True)
        conflict_original = "---\nalwaysApply: false\n---\n\nuser owned security\n"
        conflict_target.write_text(conflict_original, encoding="utf-8")

        core_out = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        skill_out = (
            self.root / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
        )
        manifest = self.root / ".harness" / "adapters" / "cursor.managed.json"

        self.assertFalse(core_out.exists())
        self.assertFalse(skill_out.exists())
        self.assertFalse(manifest.exists())

        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 1)

        self.assertFalse(core_out.exists())
        self.assertFalse(skill_out.exists())
        self.assertFalse(manifest.exists())
        self.assertEqual(conflict_target.read_text(encoding="utf-8"), conflict_original)

    def test_stale_managed_output_is_removed(self) -> None:
        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\n  - security\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        stale = self.root / ".cursor" / "rules" / "harness" / "security--security.mdc"
        keep = self.root / ".cursor" / "rules" / "harness" / "core--core.mdc"
        skill = self.root / ".cursor" / "skills" / "harness" / "task-analysis" / "SKILL.md"
        self.assertTrue(stale.is_file())
        self.assertTrue(keep.is_file())

        _write_harness(
            self.root,
            "version: 1\nprofile: software-engineer\n"
            "rules:\n  - core\n"
            "skills:\n  - task-analysis\ntools:\n  - rtk\n",
        )
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        self.assertFalse(stale.exists())
        self.assertTrue(keep.is_file())
        self.assertTrue(skill.is_file())
        manifest = json.loads(
            (self.root / ".harness" / "adapters" / "cursor.managed.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn(
            ".cursor/rules/harness/security--security.mdc",
            manifest["files"],
        )
        self.assertIn(".cursor/rules/harness/core--core.mdc", manifest["files"])

    def test_unmanaged_stale_file_is_not_removed(self) -> None:
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        stale_rel = ".cursor/rules/harness/legacy--gone.mdc"
        stale = self.root / stale_rel
        stale.write_text("---\nalwaysApply: false\n---\n\nuser kept\n", encoding="utf-8")
        manifest_path = self.root / ".harness" / "adapters" / "cursor.managed.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"].append(stale_rel)
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 0)
        self.assertTrue(stale.is_file())
        self.assertEqual(
            stale.read_text(encoding="utf-8"),
            "---\nalwaysApply: false\n---\n\nuser kept\n",
        )
        refreshed = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertNotIn(stale_rel, refreshed["files"])

    def test_unsupported_tool_capability_warning(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cursor_generate.run(self.root, dry_run=False)
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("Tool 'rtk'", output)
        self.assertIn("unsupported capability", output.lower())

    def test_dry_run_makes_no_changes(self) -> None:
        code = cursor_generate.run(self.root, dry_run=True)
        self.assertEqual(code, 0)
        self.assertFalse((self.root / ".cursor").exists())
        self.assertFalse((self.root / ".harness" / "adapters" / "cursor.managed.json").exists())

    def test_does_not_modify_project_intent(self) -> None:
        harness_before = (self.root / ".harness" / "harness.yaml").read_bytes()
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        self.assertEqual(
            (self.root / ".harness" / "harness.yaml").read_bytes(), harness_before
        )
        self.assertTrue((self.root / ".cursor" / "rules").is_dir())

    def test_manifest_correctness(self) -> None:
        self.assertEqual(cursor_generate.run(self.root, dry_run=False), 0)
        data = json.loads(
            (self.root / ".harness" / "adapters" / "cursor.managed.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["adapter"], "cursor")
        self.assertEqual(data["adapter_version"], 1)
        self.assertEqual(data["marker"], MANAGED_MARKER)
        for rel in data["files"]:
            text = (self.root / rel).read_text(encoding="utf-8")
            self.assertIn(MANAGED_MARKER, text)

    def test_preflight_detects_conflicts_without_writes(self) -> None:
        planned = [
            PlannedFile(
                relative_path=".cursor/rules/harness/core--core.mdc",
                content=f"{MANAGED_MARKER}\nok\n",
                kind="rule",
            )
        ]
        target = self.root / planned[0].relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("user\n", encoding="utf-8")
        conflicts = detect_write_conflicts(self.root, planned)
        self.assertEqual(conflicts, [planned[0].relative_path])
        report = preflight(self.root, planned, previous_files=[])
        self.assertTrue(report.has_failures)
        self.assertEqual(target.read_text(encoding="utf-8"), "user\n")

    def test_cli_entrypoint(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.root), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry-run", result.stdout)

    def test_module_entrypoint(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "adapters.cursor.generate",
                "--root",
                str(self.root),
                "--dry-run",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry-run", result.stdout)


if __name__ == "__main__":
    unittest.main()
