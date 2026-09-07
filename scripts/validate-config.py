#!/usr/bin/env python3
"""Validate .harness/harness.yaml against schemas/harness.schema.json.

Thin wrapper around harness.config_validation (shared with ``harness validate``).

Syntax validation only. Does not resolve whether referenced profiles, rules,
skills, or tools exist on disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness.config_validation import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
