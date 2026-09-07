"""Build helpers for ai-engineering-harness.

Copies the repository's canonical project content into
``harness/content/_data`` inside the build tree so wheels ship a read-only
built-in content pack. ``harness init`` materializes selected content into
consumer projects from that pack. Source trees keep a single canonical
authoring copy at the repository root.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent


def _copy_content_pack(destination: Path) -> None:
    # Import lazily so the build can resolve the helper from the source tree.
    sys.path.insert(0, str(ROOT))
    try:
        from harness.content.pack import collect_pack_source_files
    finally:
        if sys.path and sys.path[0] == str(ROOT):
            sys.path.pop(0)

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for source, relative in collect_pack_source_files(ROOT):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        dest = Path(self.build_lib) / "harness" / "content" / "_data"
        _copy_content_pack(dest)


setup(cmdclass={"build_py": build_py})
