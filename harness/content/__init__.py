"""Read-only content pack access and project materialization.

The installed engine may ship a copy of canonical project resources under
``harness.content._data``. That copy is package data only: read-only defaults
for ``harness init``. After init, the project tree is the source of truth.
"""

from __future__ import annotations

from harness.content.materialize import (
    MaterializeReport,
    apply_plan,
    format_report,
    materialize,
    plan_materialization,
)
from harness.content.pack import (
    ContentPackError,
    build_profile_file_map,
    content_pack_root,
    list_profiles,
    load_profile,
)

__all__ = [
    "ContentPackError",
    "MaterializeReport",
    "apply_plan",
    "build_profile_file_map",
    "content_pack_root",
    "format_report",
    "list_profiles",
    "load_profile",
    "materialize",
    "plan_materialization",
]
