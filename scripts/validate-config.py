#!/usr/bin/env python3
"""Validate Harness configuration and the declarative Tool Registry.

Thin wrapper around harness.config_validation (shared with ``harness validate``).

Syntax validation only. It does not detect, install, configure, or execute Tools.
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
