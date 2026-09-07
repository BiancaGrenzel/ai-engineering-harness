"""Read-only content pack access and project content materialization.

The installed engine ships canonical Profiles, Rules, Skills, Schemas, Tool
Registry, and Tool docs under ``harness.content._data``. During source
development, the same content is authored at the repository root.

``harness init`` materializes selected content under ``.harness/``. After init,
those project-local trees are the project's Harness source of truth. Adapters
generate vendor projections under ``.cursor/`` / ``.claude/`` at the project root.
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
    CONTENT_PACK_VERSION,
    PROJECT_CONTENT_DIR,
    ContentPackError,
    build_intent_file_map,
    build_profile_file_map,
    content_pack_root,
    content_path,
    list_profiles,
    load_profile,
    project_content_root,
    read_content,
    registry_path,
    schema_path,
)

__all__ = [
    "CONTENT_PACK_VERSION",
    "PROJECT_CONTENT_DIR",
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
    "project_content_root",
    "read_content",
    "registry_path",
    "schema_path",
]
