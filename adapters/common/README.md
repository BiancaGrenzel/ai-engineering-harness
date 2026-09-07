# Adapter common helpers

Shared vendor-neutral utilities used by adapters.

## Purpose

Keep agent-specific rendering inside each adapter directory.

Put only **vendor-neutral** helpers here:

- Loading `.harness/harness.yaml` (project intent)
- Merging Profile defaults from the content pack
- Resolving Rule / Skill identifiers to content-pack paths
- Resolving Tool identifiers via the content-pack `tools/registry.yaml`
- Loading and validating `adapter.yaml` metadata
- Parsing Skill frontmatter fields needed by adapters (`name`, `description`)
- Fail-closed preflight, path confinement, conflict detection, stale removal, and managed manifests

## Non-goals

- Cursor-specific `.mdc` formatting
- Claude / Codex / Gemini projections
- CLI orchestration
- Executing Tools
- Heavy plugin frameworks

## Modules

| Module | Role |
| --- | --- |
| [`resolve.py`](resolve.py) | Load config, merge Profile, resolve Rules/Skills; Tools via Registry |
| [`frontmatter.py`](frontmatter.py) | Minimal Skill `name` / `description` frontmatter parse |
| [`metadata.py`](metadata.py) | Load / validate `adapter.yaml`; capability consistency checks |
| [`apply.py`](apply.py) | Path confinement, preflight, conflicts, apply, managed-file detection, manifest inventory |

Adapters import these helpers. They must not become a second configuration source of truth.

## Path confinement

Every planned write and every stale removal must resolve **strictly under** the project `root`.

Rejected forms include parent traversal (`../`), absolute paths, Windows drive/UNC paths, and paths that escape `root` after resolution (including symlink escapes when applicable).

Invalid paths are preflight **errors**. Fail-closed: no writes when confinement fails.

## Pipeline

```text
Configuration
     ↓
Profile Resolution   (resolve.py)
     ↓
Adapter Metadata     (metadata.py)
     ↓
Plan                 (adapter-specific render)
     ↓
Preflight            (apply.py — detect conflicts, classify actions)
     ↓
Apply                (apply.py — only if preflight has no conflicts)
     ↓
Result
```

## Fail-closed conflicts

Preflight runs **before** any filesystem mutation.

If any planned path exists and is not Harness-managed:

- report the conflict
- exit non-zero
- write nothing (including the managed manifest)

Do not use rollback as a substitute for preflight.

## Manifest role

Manifest files under `.harness/adapters/` are a **managed-output inventory**.

They are not the project source of truth. Desired state remains `.harness/harness.yaml`.

Typical fields:

| Field | Meaning |
| --- | --- |
| `version` | Manifest format version |
| `adapter` | Adapter id |
| `adapter_version` | Adapter implementation version from `adapter.yaml` |
| `files` | Relative paths currently considered managed |
| `marker` | Stable marker string used in generated files |

## Version distinctions

| Version | Where | Meaning |
| --- | --- | --- |
| Harness `version` | `.harness/harness.yaml` | Configuration format version |
| Adapter `version` | `adapters/<agent>/adapter.yaml` | Adapter implementation / contract version |
| Tool version | Tool catalog docs | Upstream software release |

## sys.path / imports

Prefer module invocation so packages resolve without path hacks:

```bash
python -m adapters.cursor.generate
```

Direct script execution of `adapters/cursor/generate.py` keeps a minimal
`sys.path` bootstrap for local use without packaging. Packaging / `pyproject`
installers are intentionally out of scope for this phase.

## Context budget (future)

Shared helpers must not assume “more projected Rules/Skills is always better.”

Future token / context / RTK integrations should plug in at plan or post-resolve
stages. Do not hard-code “always inject everything” into common apply logic.
