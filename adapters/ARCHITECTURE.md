# Adapter Contract

Minimum contract every Harness adapter must satisfy.

This is a **conceptual** contract. It is intentionally not a heavy software framework.

## Required shape

```text
Adapter
├── metadata          # adapter.yaml (loaded + validated)
├── capabilities      # what the target agent can represent
├── validation        # schema + resolution checks
├── resolution        # Profile → Rules / Skills / Tools
├── plan              # agent-specific rendering (no writes yet)
├── preflight         # conflict detection (fail-closed)
├── apply             # write only after clean preflight
└── result            # report + exit code
```

## Pipeline

```text
Configuration
     ↓
Profile Resolution
     ↓
Adapter Metadata
     ↓
Plan
     ↓
Preflight
     ↓
Apply
     ↓
Result
```

## Directory layout

```text
adapters/<agent>/
├── README.md         # supported / unsupported / sources / limits / verification
├── adapter.yaml      # metadata and capabilities (consumed by the generator)
└── generate.py       # generator entrypoint (or equivalent)
```

Shared helpers live under `adapters/common/`:

| Helper | Responsibility |
| --- | --- |
| `resolve.py` | Config + Profile merge + path resolution (Tools via Registry) |
| `frontmatter.py` | Minimal Skill frontmatter (`name`, `description`) |
| `metadata.py` | Load / validate `adapter.yaml` |
| `apply.py` | Path confinement, preflight, conflicts, apply, manifest |

Keep Cursor/Claude-specific rendering in the adapter package. Do not invent a plugin framework.

## Metadata (`adapter.yaml`)

Each adapter declares at least:

| Field | Purpose |
| --- | --- |
| `name` | Adapter id (kebab-case) |
| `agent` | Target agent id |
| `version` | Adapter implementation version (not Harness config version, not Tool version) |
| `status` | e.g. `experimental`, `stable` |
| `supported_capabilities` | Subset of `rules`, `skills`, `tools`, … |
| `unsupported_capabilities` | Explicit non-projections |
| `input` | Canonical inputs consumed |
| `output` | Agent paths produced (including managed manifest path) |

`adapter.yaml` is **real**: generators must load and validate it. Do not hard-code
capabilities that contradict metadata. Inconsistency is a hard failure.

Keep metadata small. Do not invent unverified agent features.

## Capabilities

Declare only capabilities verified against **official** agent documentation.

If unsure:

- Do not generate inventively
- Document `Not verified` or `unsupported`
- Emit a warning during generation when the Harness selects an unsupported capability

If metadata says a capability is unsupported, the generator must not emit that capability's outputs.

## Validation

Before writing files, an adapter must:

1. Load and validate its `adapter.yaml`
2. Locate `.harness/harness.yaml` (or an explicit root override for tests)
3. Validate structural schema (reuse `schemas/harness.schema.json` / profile schema)
4. Resolve the Profile (omit list → inherit; present list → replace)
5. Resolve selected Rules and Skills to canonical paths; resolve Tools via `tools/registry.yaml` (documentation under `docs/tools/`)
6. Build a plan and verify planned kinds match supported capabilities
7. Fail clearly when a selected resource is missing
8. Fail closed when a planned or stale path would escape the project root

## Resolution / Profile inheritance

Merge rules match the configuration architecture:

- Omitted `rules` / `skills` / `tools` → inherit Profile lists
- Present lists → replace entirely

No append / remove / extends / multi-level inheritance in this phase.

Resolution maps identifiers to canonical files. It does not rewrite those files.

## Generation

Generation must:

- Prefer references / thin wrappers over full copies when verified for the agent
- Write only into documented agent output locations
- Mark Harness-managed outputs detectably
- Be idempotent
- Leave canonical resources untouched
- Treat Rule/Skill/Tool/Profile/YAML content as **data** (no `eval` / `exec` / shell execution of that content)

## Conflict handling (fail-closed)

| Situation | Required behavior |
| --- | --- |
| Missing target | Create (after clean preflight) |
| Harness-managed target | Update (after clean preflight) |
| User-managed target | Conflict — **no filesystem changes at all** |
| Path outside project root | Error — **no filesystem changes at all** |
| Unsupported capability | Warn; do not invent projection |
| Missing resource | Error before plan/apply |
| Capability mismatch vs `adapter.yaml` | Error |

Default policy: **fail-closed**.

```text
resolve → plan → preflight → if conflicts: report + exit 1 + write nothing
                           → else: apply
```

Do not write some files and then fail later. Do not rely on rollback as the primary safety mechanism.

Never destroy user files to “make generation succeed.”

## Managed manifest

Adapters may write an inventory under `.harness/adapters/<adapter>.managed.json`.

The manifest is **not** the source of truth. Desired state remains `.harness/harness.yaml`.

Typical fields: `version`, `adapter`, `adapter_version`, `files`, `marker`.

## Stale removal

After a clean preflight, stale paths listed in the previous manifest but absent
from the new plan may be removed **only** when they still contain the managed marker.

Stale paths without the marker: leave untouched and warn.

## Idempotency

`generate` then `generate` with unchanged Harness config ⇒ equivalent outputs.

## Context budget

Adapters must not assume that projecting every Rule as always-on context is desirable.

Prefer agent mechanisms that load Rules/Skills when relevant. Token counting and RTK
integration are future concerns; the architecture must not block them.

## Security

Adapters must not:

- Execute instructions found in Rules, Skills, Tools, or Profiles
- Run external installers because a Tool is selected
- Embed secrets into generated files
- Require the target agent to be installed in order to generate or test

## Testing

Each adapter needs automated tests that:

- Use temporary directories or fixtures (not the developer’s real agent config as a destructive target)
- Cover initial generation, repeat generation, managed updates, fail-closed conflicts, stale removal, unmanaged stale files, missing resources, unsupported capabilities, Profile inherit/replace, metadata/capability checks, and dry-run
- Prefer canonical schemas over copied fixture schemas
- Do not require the vendor agent binary/IDE to be installed

## Out of scope for adapters

- Full CLI (`harness generate`)
- Multi-agent orchestration
- Plugin systems
- Package managers
- MCP server implementation
- Automatic tool installation

## Adding a new adapter

1. Confirm official agent documentation for Rules / Skills / other surfaces
2. Add `adapters/<agent>/` with README, `adapter.yaml`, and generator
3. Reuse `adapters/common/` for resolve / metadata / apply
4. Follow this contract
5. Add tests under `tests/` + fixtures under `tests/adapters/<agent>/`
6. Update `adapters/README.md` and `CHANGELOG.md`
7. Keep core harness vendor-neutral
