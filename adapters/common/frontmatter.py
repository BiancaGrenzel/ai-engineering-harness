#!/usr/bin/env python3
"""Minimal Skill frontmatter parsing for adapters.

Vendor-neutral: extracts only ``name`` and ``description`` from YAML
frontmatter. Treats Skill content as data (no eval/exec).
"""

from __future__ import annotations

import re

from adapters.common.resolve import load_yaml_string, require_deps

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_skill_frontmatter(text: str) -> dict[str, str]:
    """Parse Skill YAML frontmatter as data.

    Returns a dict that may contain ``name`` and/or ``description`` when present
    as non-empty strings. Missing frontmatter or missing fields yield an empty
    or partial dict (never raises for ordinary markdown).
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    require_deps()
    data = load_yaml_string(match.group(1))
    if not isinstance(data, dict):
        return {}
    result: dict[str, str] = {}
    for key in ("name", "description"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    return result
