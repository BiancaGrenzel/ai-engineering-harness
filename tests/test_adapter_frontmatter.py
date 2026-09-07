#!/usr/bin/env python3
"""Tests for shared Skill frontmatter parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.frontmatter import parse_skill_frontmatter


def _deps_available() -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


class SkillFrontmatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _deps_available():
            raise unittest.SkipTest("Install scripts/requirements.txt before running tests")

    def test_valid_frontmatter(self) -> None:
        text = (
            "---\n"
            "name: task-analysis\n"
            "description: Transform a request into a clear task\n"
            "category: core\n"
            "---\n\n"
            "# Task Analysis\n\nBody text.\n"
        )
        meta = parse_skill_frontmatter(text)
        self.assertEqual(meta["name"], "task-analysis")
        self.assertEqual(meta["description"], "Transform a request into a clear task")
        self.assertNotIn("category", meta)

    def test_absence_of_frontmatter(self) -> None:
        text = "# Just markdown\n\nNo frontmatter here.\n"
        self.assertEqual(parse_skill_frontmatter(text), {})

    def test_name_absent(self) -> None:
        text = "---\ndescription: Only description\n---\n\n# Skill\n"
        meta = parse_skill_frontmatter(text)
        self.assertNotIn("name", meta)
        self.assertEqual(meta["description"], "Only description")

    def test_description_absent(self) -> None:
        text = "---\nname: only-name\n---\n\n# Skill\n"
        meta = parse_skill_frontmatter(text)
        self.assertEqual(meta["name"], "only-name")
        self.assertNotIn("description", meta)

    def test_valid_markdown_without_yaml_fields(self) -> None:
        text = "---\ncategory: core\n---\n\n# Skill\n\nStill valid markdown.\n"
        self.assertEqual(parse_skill_frontmatter(text), {})


if __name__ == "__main__":
    unittest.main()
