# Cursor Adapter

Experimental adapter that projects canonical Harness configuration into Cursor-compatible files.

```text
.harness/harness.yaml
        ↓
Profile Resolution
        ↓
adapter.yaml (capabilities)
        ↓
Plan (.mdc / SKILL projections)
        ↓
Preflight (fail-closed)
        ↓
Apply
        ↓
.cursor/rules/harness/*.mdc
.cursor/skills/harness/*/SKILL.md
.harness/adapters/cursor.managed.json
```

## What it does

1. Loads and validates `adapters/cursor/adapter.yaml`
2. Reads `.harness/harness.yaml` (project intent)
3. Validates structure against content-pack Harness schemas
4. Loads the selected Profile from the content pack and merges lists (omit → inherit; present → replace)
5. Resolves Rules, Skills, and Tools from the content pack
6. Plans self-contained Cursor Rules and Skills using declared output paths
7. Verifies planned kinds match supported capabilities
8. Prefights conflicts (**fail-closed** — no writes if any conflict)
9. Warns for Tools (selected but not projected)
10. Applies writes and refreshes the managed manifest

Canonical content stays in the content pack (or this repository when developing from source). Generated Cursor files are self-contained projections.

## Supported

| Capability | Projection |
| --- | --- |
| Rules | `.cursor/rules/harness/<category>--<stem>.mdc` thin wrappers with `@`-references to canonical Rule markdown |
| Skills | `.cursor/skills/harness/<skill-id>/SKILL.md` thin wrappers that point at canonical `skills/**/SKILL.md` |

Declared in `adapter.yaml` and enforced by the generator.

## Not supported

| Capability | Behavior |
| --- | --- |
| Tools | Resolved for existence; **not** written as Cursor config. Warning emitted. |
| MCP install / hooks | Out of scope |
| User Rules / Team Rules | Out of scope |
| Editing `AGENTS.md` | Out of scope (`AGENTS.md` remains harness-owned documentation; Cursor may read it natively) |

## Always Apply Policy

Official Cursor Project Rules support four activation modes via frontmatter:

| Mode | Frontmatter pattern |
| --- | --- |
| Always Apply | `alwaysApply: true` |
| Apply Intelligently | `alwaysApply: false` + `description` |
| Apply to Specific Files | `alwaysApply: false` + `globs` |
| Apply Manually | `alwaysApply: false`, no description/globs ( `@`-mention ) |

**Harness decision (v1):** generated Rule wrappers use:

```yaml
alwaysApply: false
description: "<meaningful category/stem description>"
```

### Why

- The harness optimizes for context / token efficiency
- `alwaysApply: true` for every Rule would inject all projected Rules into every chat
- Official docs recommend focused, scoped rules; intelligent apply uses the description

### Impact

- Rules are not guaranteed present in every Cursor session
- The agent may omit a Rule when it judges the description irrelevant
- Core behavioral guarantees that must always be present may need a future per-Rule override

### When to revise

- When Rule-level metadata (e.g. optional `alwaysApply` / `globs` in canonical Rules or adapter policy maps) is introduced
- When measured context cost shows under- or over-application
- When official Cursor activation semantics change

### Extensibility (not implemented yet)

A small future extension point can allow per-Rule overrides without a large system:

- optional Rule frontmatter or side-car policy for `alwaysApply` / `globs`
- adapter keeps the default as intelligent apply

## Wrapper strategy

Desired model:

```text
Harness canonical file
        ↓
Cursor thin wrapper
        ↓
Cursor loads canonical content
```

| Strategy | Status | Trade-off |
| --- | --- | --- |
| Thin Rule wrapper + `@path` reference | Used; runtime end-to-end **Not verified** | Low drift; depends on Cursor `@` inclusion behavior |
| Thin Skill wrapper pointing at canonical path | Used; agent must open the canonical file | Low drift; not a native “remote skill path” |
| Materialized full copy into `.cursor/` | Not used | Higher reliability if references fail; higher drift / context duplication |
| Symlinks | Not used | Portability concerns (Windows / CI) |

If `@path` inclusion proves unreliable in practice, revisit materialized copies for Rules — do not invent unsupported Cursor APIs.

## How it works

### Generation model

Cursor Project Rules require `.mdc` files under `.cursor/rules` (plain `.md` is ignored by the rules system). Official docs encourage referencing files with `@path` instead of copying content.

Harness Skills already use `SKILL.md` + frontmatter. Cursor discovers skills under `.cursor/skills/` (and related paths). There is no verified official mechanism to point Cursor at `skills/` outside those discovery roots without a local skill entry.

Therefore this adapter:

1. **Rules** — generate thin `.mdc` wrappers (`alwaysApply: false` + description) whose bodies `@`-reference canonical files under `rules/`
2. **Skills** — generate thin `SKILL.md` wrappers under `.cursor/skills/harness/<id>/` that preserve `name` / `description` and instruct the agent to follow the canonical Skill path
3. **Does not copy** full canonical bodies into `.cursor/`

### Harness-managed detection

Generated files include:

```html
<!-- ai-engineering-harness:managed -->
```

A managed-output inventory is written to:

```text
.harness/adapters/cursor.managed.json
```

| Field | Meaning |
| --- | --- |
| `version` | Manifest format version |
| `adapter` | `cursor` |
| `adapter_version` | From `adapter.yaml` `version` |
| `files` | Relative paths currently managed |
| `marker` | Managed marker string |

The manifest is **not** source of truth. Desired state remains `.harness/harness.yaml`.

| Kind | Policy |
| --- | --- |
| Harness-managed | Safe to update or remove on regenerate |
| User-managed (no marker) | Never overwritten; fail-closed |
| Canonical `rules/` / `skills/` | Never modified by this adapter |

### Conflict handling (fail-closed)

| Case | Result |
| --- | --- |
| File missing | Create (after clean preflight) |
| File exists + managed marker | Update (after clean preflight) |
| File exists without marker | Conflict — **no filesystem changes**, exit 1 |
| Missing Rule/Skill/Tool | Error — no partial inventing |
| Selected Tool | Warning — unsupported projection |
| Capability mismatch vs `adapter.yaml` | Error |

### Stale removal

Managed outputs listed in the previous manifest but absent from the new plan are removed only when they still contain the managed marker. Unmanaged stale files are left untouched.

### Idempotency

Re-running the generator with the same harness config regenerates the same managed wrappers and refreshes the manifest.

## Generated files

```text
.cursor/rules/harness/<category>--<rule-stem>.mdc
.cursor/skills/harness/<skill-id>/SKILL.md
.harness/adapters/cursor.managed.json
```

Example Rule projection shape (self-contained body):

```markdown
---
description: "Harness Rule core/core. Apply when this project's agent behavior for this category is relevant."
alwaysApply: false
---

<!-- ai-engineering-harness:managed -->

# Core Principles
...
```

Generated Skills likewise embed the Skill workflow body. They do **not** depend on
project-local `rules/` or `skills/` trees.

## Usage

From the repository root (preferred — no `sys.path` mutation):

```bash
python -m adapters.cursor.generate
python -m adapters.cursor.generate --dry-run
python -m adapters.cursor.generate --root /path/to/project
```

Direct script form still works via a minimal path bootstrap:

```bash
python adapters/cursor/generate.py
python adapters/cursor/generate.py --dry-run
```

## Verification Status

Classify harness claims about Cursor behavior honestly.

| Topic | Status | Notes |
| --- | --- | --- |
| Project Rules live under `.cursor/rules` as `.mdc` | **Verified** | Official Cursor Rules docs |
| Plain `.md` under `.cursor/rules` ignored by rules system | **Verified** | Official docs |
| Frontmatter `description` / `globs` / `alwaysApply` | **Verified** | Official docs |
| `@path` references inside Project Rules | **Verified** (documented) | Official docs encourage `@` file references |
| Runtime that `@path` always inlines canonical Rule bodies as expected in every Cursor build | **Not verified** | Documented mechanism; not end-to-end tested by this harness |
| Skills discovered under `.cursor/skills/<name>/SKILL.md` | **Verified** | Official Skills docs |
| Thin Skill wrappers causing the agent to open canonical `skills/**/SKILL.md` | **Not verified** | Relies on agent following wrapper instructions |
| Nested `.cursor/skills` discovery quirks beyond documented paths | **Not verified** | Treat edge cases cautiously |
| Tools projection into Cursor-native config | **Not supported** | Declared unsupported in `adapter.yaml` |

## Limitations

- Status: **experimental**
- Does not install or configure Tools (including RTK)
- Does not require Cursor to be installed; it only writes files
- Thin Skill wrappers rely on the agent reading the canonical Skill file
- Symlinks are not used (portability; Windows and CI friendliness)
- Context budget / token counting not implemented in the adapter
- No per-Rule `alwaysApply` / `globs` overrides yet

## Compatibility

| Input | Required |
| --- | --- |
| `.harness/harness.yaml` | Yes |
| Matching Profile under `profiles/` | Yes |
| Selected Rules / Skills / Tools on disk | Yes |
| `adapters/cursor/adapter.yaml` | Yes (loaded by generator) |
| Cursor IDE installed | No (generation/tests) |

## Verification

```bash
python scripts/validate-config.py
python -m unittest discover -s tests -q
python -m adapters.cursor.generate --dry-run
```

## Sources

Official Cursor documentation consulted while implementing this adapter:

| Topic | URL | Notes |
| --- | --- | --- |
| Project Rules (`.cursor/rules`, `.mdc`, frontmatter, `alwaysApply`) | https://cursor.com/docs/rules | Verified: `.mdc` required; activation modes documented; `@` file references documented |
| Agent Skills | https://cursor.com/docs/skills.md | Verified: `.cursor/skills/<name>/SKILL.md`; frontmatter `name` + `description` |
| Skills help | https://cursor.com/help/customization/skills | Verified: discovery paths and Rules vs Skills guidance |

Last reviewed against those pages for this adapter hardening pass.

Anything not listed above should be treated as **Not verified**.
