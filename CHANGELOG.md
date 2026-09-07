# Changelog

## Unreleased

### Added

- `harness init` / `harness init --profile <name>` to materialize a Harness-enabled project
- `harness init --dry-run` (fail-closed create / unchanged / conflict planning, no writes)
- Read-only content pack packaging under `harness.content` (schemas, profiles, rules, skills, tools registry, tool docs)
- Setuptools build hook (`setup.py`) that ships the content pack inside the wheel as `harness/content/_data`
- Init / content-pack tests (`tests/test_init.py`) including isolated external-project smoke coverage
- Local installable packaging via `pyproject.toml` (`pip install .`)
- Console script entrypoint: `harness = harness.cli:main`
- Packaging / installed-CLI smoke tests (`tests/test_packaging.py`)
- Claude Code adapter (`adapters/claude/`) projecting Rules/Skills into `.claude/`
- `generate claude` CLI dispatch (`python -m harness generate claude`)
- Claude adapter tests and fixtures under `tests/adapters/claude/`
- Initial Harness CLI (`python -m harness`)
- `validate` command
- `generate cursor` command
- Shared config validation module used by the CLI and `scripts/validate-config.py`
- Optional path-bootstrapped launcher: `python scripts/harness`
- Shared adapter helpers: `adapters/common/metadata.py`, `adapters/common/apply.py`
- Tests for Profile inherit/replace, fail-closed conflicts, stale removal, metadata/capabilities
- Cursor adapter Verification Status and Always Apply Policy documentation
- Adapter architecture
- Adapter contract
- Cursor adapter
- Cursor configuration generator
- Adapter tests
- Initial AI Engineering Harness foundation
- Agent instructions
- Core Rules architecture
- Context Engineering Rules
- Security Rules
- Quality Rules
- Production Rules
- Skills architecture contract (`docs/architecture/skills.md`)
- Skills template and catalog (`skills/`)
- Core Skills: task-analysis, planning, context-engineering, research, verification
- AI Engineering Skill: token-optimization
- Initial Tool Registry architecture
- Tool documentation standard
- Tool evaluation criteria
- Token optimization category
- RTK evaluation
- Initial Harness configuration (`.harness/harness.yaml`)
- Profile architecture (`profiles/`)
- Software Engineer profile
- Harness configuration schema (`schemas/harness.schema.json`)
- Profile schema (`schemas/profile.schema.json`)
- Configuration architecture documentation
- Configuration validation script (`scripts/validate-config.py`)

### Changed

- Content Pack / Consumer Project architecture: package-owned canonical content + project intent + self-contained projections
- `harness init` creates only `.harness/harness.yaml` (no project-local profiles/rules/skills/schemas/tools/docs)
- `resolve_harness`, `harness validate`, and `harness tools health` read canonical content from the content pack
- Cursor Rules are self-contained `.mdc` bodies (no `@rules/` wrappers)
- Claude Skills are self-contained (no project-local `skills/` dependency)
- Document Installed Engine vs Content Pack vs Project Intent vs Generated Vendor Projection
- Document installed (`harness`) vs development (`python -m harness`) invocation
- Cursor adapter conflicts are **fail-closed** (preflight before any writes)
- Cursor Rules default to `alwaysApply: false` with description (Apply Intelligently)
- `adapter.yaml` is loaded and validated; capabilities must match generator behavior
- Managed manifest includes `adapter_version` and documents inventory-only role
- Adapter tests use canonical `schemas/` (no fixture schema copies)
- Prefer `python -m adapters.cursor.generate` (script path bootstrap retained)
