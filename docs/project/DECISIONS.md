# Architectural Decisions

This is an index, not a replacement for architecture documents or ADRs.

## Core Architecture

**Decision:** Keep a vendor-neutral canonical core and place vendor formats in adapters.  
**Reason:** Shared content remains reusable across agent environments.  
**Status:** Accepted.  
**Reference:** `docs/architecture/adapters.md`, `adapters/ARCHITECTURE.md`.

## Configuration

**Decision:** Use `.harness/harness.yaml` for declarative project selection and Profiles for defaults; lists replace-or-inherit.  
**Reason:** Project intent stays small and composition is predictable.  
**Status:** Accepted.  
**Reference:** `docs/architecture/configuration.md`.

## Profiles

**Decision:** Profiles compose Rules, Skills, and Tools without inheritance or embedded content.  
**Reason:** Avoid hidden merges and duplicated procedures.  
**Status:** Accepted.  
**Reference:** `profiles/README.md`, `docs/architecture/configuration.md`.

## Rules / Skills

**Decision:** Rules are persistent behavior; Skills are focused, activated procedures.  
**Reason:** Policy and workflow have different lifecycles and context costs.  
**Status:** Accepted.  
**Reference:** `docs/architecture/skills.md`, `rules/README.md`.

## Tools

**Decision:** Keep Tool metadata declarative in `tools/registry.yaml`; separate resolution, detection, health, and future integration concerns.  
**Reason:** The Registry must not become an arbitrary execution surface.  
**Status:** Accepted.  
**Reference:** `docs/architecture/adr/0001-tool-system-architecture.md`, `docs/architecture/tools.md`, `docs/architecture/tool-detection.md`, `docs/architecture/tool-health.md`.

## Security

**Decision:** Record catalog baseline risk and access surfaces separately from runtime effective risk and authorization.  
**Reason:** Catalog metadata cannot determine the security context of a host or execution.  
**Status:** Accepted; effective-risk and authorization systems are not implemented.  
**Reference:** `docs/architecture/tools.md`, `docs/architecture/tool-detection.md`, `docs/architecture/tool-health.md`.

## Adapters

**Decision:** Adapter generation is deterministic and Cursor/Claude conflict handling is fail-closed before writes.
**Reason:** Generated vendor files must not silently overwrite user-owned state.
**Status:** Accepted; Cursor and Claude adapters are experimental.
**Reference:** `docs/architecture/adapters.md`, `adapters/cursor/README.md`, `adapters/claude/README.md`.

**Decision:** Claude adapter does not manage or overwrite project `CLAUDE.md`.
**Reason:** `CLAUDE.md` is commonly user/project-owned always-on instructions; Rules/Skills under `.claude/` are the safer modular projection surfaces.
**Status:** Accepted for Claude adapter v1.
**Reference:** `adapters/claude/README.md`.

**Decision:** Claude Rules are materialized under `.claude/rules/harness/` rather than at-path thin wrappers.
**Reason:** Official at-path imports are documented for `CLAUDE.md`, not verified for `.claude/rules/`; inventing that behavior would be unsafe.
**Status:** Accepted for Claude adapter v1.
**Reference:** `adapters/claude/README.md`.

**Decision:** Managed adapter paths must resolve strictly under the project root (path confinement in `adapters/common/apply.py`).
**Reason:** Fail-closed generation must not write or remove files outside the project.
**Status:** Accepted.
**Reference:** `adapters/common/apply.py`, `adapters/ARCHITECTURE.md`.

**Decision:** Adapter Tool identity resolves through `tools/registry.yaml`; `docs/tools/` remains human documentation referenced by Registry `documentation`.
**Reason:** Operational Tool identity must not diverge from the Registry.
**Status:** Accepted.
**Reference:** `adapters/common/resolve.py`, `docs/architecture/adapters.md`.

## CLI

**Decision:** The CLI is a thin dispatcher over validation, adapter, and Tool diagnostic logic.  
**Reason:** Prevent duplicated contracts and business logic.  
**Status:** Accepted.  
**Reference:** `docs/architecture/cli.md`, `harness/cli.py`.

**Decision:** Packaging installs the engine (`harness` + `adapters`) plus a read-only built-in content pack as package resources.
**Reason:** End users must be able to `pip install` without a repository checkout; the pack is the immutable seed for `harness init`.
**Status:** Accepted.
**Reference:** `pyproject.toml`, `setup.py`, `harness/content/`, `docs/architecture/cli.md`.

**Decision:** `harness init` materializes project intent plus the selected Profile's Rules, Skills, schemas, Tool Registry, and Tool docs under `.harness/`; conflicts are fail-closed; vendor projections (`.cursor/`, `.claude/`) remain at the project root via `harness generate`.
**Reason:** Keep Harness canonical content namespaced under `.harness/` so consumer project roots stay clean; adapters project only vendor-specific files at the root.
**Status:** Accepted.
**Reference:** `harness/init.py`, `harness/content/materialize.py`, `docs/architecture/cli.md`.

**Decision:** Resolve / validate / generate prefer `<project>/.harness/` when it contains schemas + profiles; then a legacy project-root pack layout; otherwise the installed content pack.
**Reason:** Current init writes under `.harness/`; dogfood/authoring and older root layouts remain readable without inventing a second source of truth.
**Status:** Accepted.
**Reference:** `harness.content.pack.project_content_root`, `adapters/common/resolve.py`.

**Decision:** Cursor Rules and Claude Skills are self-contained materialized projections (no runtime dependency on package filesystem paths).
**Reason:** Generated agent trees must work for agents without importing the Harness package path.
**Status:** Accepted.
**Reference:** `adapters/cursor/generate.py`, `adapters/claude/generate.py`.

**Decision:** Built-in content pack version matches the Harness distribution version for now (no separate content-pack versioning system).
**Reason:** Keep packaging simple until independent content releases are needed.
**Status:** Accepted.
**Reference:** `harness.content.pack.CONTENT_PACK_VERSION`, `harness.__version__`.

## Runtime

**Decision:** Detection and Health observations are transient and are never written back to configuration or the Registry.  
**Reason:** Project intent, catalog metadata, and local runtime state are different sources of truth.  
**Status:** Accepted.  
**Reference:** `docs/architecture/tool-detection.md`, `docs/architecture/tool-health.md`.

**Decision:** Health uses an optional declarative Registry contract separate from `detection.version_arguments`, composed with `DetectionResult`.  
**Reason:** Version presence and minimal operational liveness are different concerns; silent reuse would blur them.  
**Status:** Accepted.  
**Reference:** `docs/architecture/tool-health.md`, `harness/tools/health.py`.
