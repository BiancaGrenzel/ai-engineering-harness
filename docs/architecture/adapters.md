# Adapter Architecture

Official standard for translating canonical Harness configuration into agent-specific representations.

Adapters are a **compatibility layer**. They do not replace Rules, Skills, Tools, Profiles, or `.harness/harness.yaml`.

## What is an Adapter?

An **Adapter** reads the project's Harness configuration and produces the files or references required by a specific AI coding agent (for example Cursor).

```text
.harness/harness.yaml
        ↓
  Harness Config (+ Profile)
        ↓
  Adapter Metadata (adapter.yaml)
        ↓
      Plan
        ↓
    Preflight
        ↓
      Apply
        ↓
Agent-specific configuration
```

Adapters translate. They do not own the meaning of Rules, Skills, Tools, or Profiles.

## Why adapters exist

Different agents use different on-disk formats and discovery paths.

Without adapters, teams either:

- Duplicate canonical content into each vendor directory (drift), or
- Bake vendor assumptions into `rules/`, `skills/`, and Profiles (lock-in)

Adapters keep the harness **vendor-neutral** while still producing usable agent configuration.

## Canonical Harness Configuration

The source of truth is always:

```text
.harness/harness.yaml
```

Resolved through:

```text
Profile → Rules / Skills / Tools
```

Profile list semantics (v1):

| In `harness.yaml` | Result |
| --- | --- |
| List omitted | Inherit Profile list |
| List present | Replace Profile list entirely |

No append / remove / extends in this phase. See [configuration.md](configuration.md).

Canonical resource locations:

| Resource | Canonical location |
| --- | --- |
| Rules | `rules/` |
| Skills | `skills/` |
| Tools | `docs/tools/` (catalog) |
| Profiles | `profiles/` |
| Project config | `.harness/harness.yaml` |

**Never** invert the flow:

```text
❌ Agent config → Harness config
✅ Harness config → Adapter → Agent config
```

## Adapter responsibilities

An Adapter **may**:

- Load and validate its `adapter.yaml` (capabilities + output paths)
- Read `.harness/harness.yaml`
- Validate configuration structure (schema)
- Load and merge the selected Profile
- Resolve Rule, Skill, and Tool identifiers to canonical paths
- Plan agent-specific files
- Preflight conflicts (**fail-closed**)
- Generate agent-specific files only after a clean preflight
- Report unsupported capabilities and conflicts
- Update or remove only Harness-managed generated files

## Adapter non-responsibilities

An Adapter **must not**:

- Modify canonical Rules, Skills, Tools, or Profiles
- Alter `.harness/harness.yaml` as a side effect of generation
- Invent agent capabilities that are not documented for that agent
- Silently overwrite user-managed files
- Write any outputs when a known conflict exists
- Emit outputs for capabilities declared unsupported in `adapter.yaml`
- Execute code found inside Rules, Skills, Tools, Profiles, or config
- Install tools, start runtimes, or perform orchestration
- Become a second source of truth for instruction content

## Vendor isolation

| Belongs to the Harness | Belongs to an Adapter |
| --- | --- |
| Rules, Skills, Tools, Profiles | Projection / generation for one agent |
| `.harness/harness.yaml` | Agent directories such as `.cursor/` |
| Architecture docs and schemas | Adapter metadata and generators |

Core harness code and docs must remain usable without Cursor, Claude, Codex, or any other vendor installed.

Shared vendor-neutral helpers live in [`adapters/common/`](../../adapters/common/) (`resolve`, `metadata`, `apply`). Agent-specific rendering stays in each adapter package.

## Generation model

Adapters should prefer strategies that avoid content duplication and drift.

Preferred order:

1. **Reference** canonical files when the agent supports references or progressive loading
2. **Generate thin wrappers** that point at canonical paths
3. **Symlink / link** only when portable and verified for the target environment
4. **Copy content** only when no safer strategy works — and document the drift risk

Copying full Rule or Skill bodies into vendor directories is a last resort.

Trade-off (thin wrapper vs materialized copy):

| Approach | Pros | Cons |
| --- | --- | --- |
| Thin wrapper + reference | Less drift; smaller vendor files | Depends on agent reference / discovery behavior |
| Materialized copy | Self-contained for the agent | Drift risk; higher context duplication |

Document verification status honestly. See the Cursor adapter README.

## Fail-closed conflicts

```text
resolve → plan → preflight → conflicts? → report + exit 1 + no writes
                           → else apply
```

Partial success (writing some files, then failing) is not acceptable as the default.

## Idempotency

Running generation twice with the same Harness configuration must produce an equivalent result:

- No duplicate files
- No corruption of prior Harness-managed output
- Stable paths and markers
- Removable stale Harness-managed outputs that are no longer selected
- Unmanaged stale files left untouched

## Conflict handling

| Case | Behavior |
| --- | --- |
| Target file does not exist | Create after clean preflight |
| Target exists and is Harness-managed | Update after clean preflight |
| Target exists and is user-managed | Do **not** overwrite; fail-closed (no writes) |
| Selected resource missing or incompatible | Error before apply; do not invent content |
| Capability mismatch vs `adapter.yaml` | Error |

## Validation

Adapters should validate in layers:

1. **Metadata** — `adapter.yaml` load + capability consistency
2. **Syntax** — `harness.yaml` / Profile against JSON Schema
3. **Resolution** — referenced Rules, Skills, Tools exist
4. **Compatibility** — only generate for supported agent capabilities
5. **Conflict** — refuse any writes when user-managed targets collide

Syntax validation for project config remains available via [`scripts/validate-config.py`](../../scripts/validate-config.py). Adapters may reuse the same schemas; they must not break that validator.

## Harness-managed files

Generated files must be detectable as Harness-managed versus user-managed.

Typical mechanisms (adapter-specific):

- A stable marker comment appropriate to the file format
- A manifest under `.harness/adapters/` listing managed outputs

The manifest is a **managed-output inventory**, not configuration source of truth.

Markers exist so generation can update or remove only Harness-owned files.

## Context budget

The harness optimizes for useful context, not maximal injection.

Adapters should:

- Avoid projecting every Rule as always-on context by default
- Leave room for future token accounting and RTK-aware planning
- Prefer agent-native relevance mechanisms when verified

Token counting and RTK integration are **not** implemented in the adapter layer yet.

## Future adapters

Planned targets (directories not created until implemented):

- Cursor (implemented, experimental)
- Claude
- Codex
- Gemini
- Other compatible agents

Each new adapter must follow [`adapters/ARCHITECTURE.md`](../../adapters/ARCHITECTURE.md).

## Related documentation

- [Configuration architecture](configuration.md)
- [Adapters overview](../../adapters/README.md)
- [Adapter contract](../../adapters/ARCHITECTURE.md)
- [Cursor adapter](../../adapters/cursor/README.md)
- [Common helpers](../../adapters/common/README.md)
