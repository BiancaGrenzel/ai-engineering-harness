"""Read-only content pack access and project intent materialization.

The installed engine ships canonical Profiles, Rules, Skills, Schemas, Tool
Registry, and Tool docs under ``harness.content._data``. During source
development, the same content is authored at the repository root.

Consumer projects keep only project intent (``.harness/harness.yaml``).
Adapters generate self-contained vendor projections under ``.cursor/`` /
``.claude/``.
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
    build_intent_file_map,
    build_profile_file_map,
    content_pack_root,
    content_path,
    list_profiles,
    load_profile,
    read_content,
    registry_path,
    schema_path,
)

__all__ = [
    "ContentPackError",
    "MaterializeReport",
    "apply_plan",
    "build_intent_file_map",
    "build_profile_file_map",
    "content_pack_root",
    "content_path",
    "format_report",
    "list_profiles",
    "load_profile",
    "materialize",
    "plan_materialization",
    "read_content",
    "registry_path",
    "schema_path",
]
