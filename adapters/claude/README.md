# Claude Adapter

Experimental adapter that projects canonical Harness configuration into Claude Code-compatible files.

```text
.harness/harness.yaml
        ↓
Profile Resolution
        ↓
adapter.yaml (capabilities)
        ↓
Plan (.md rules / SKILL wrappers)
        ↓
Preflight (fail-closed)
        ↓
Apply
        ↓
.claude/rules/harness/*.md
.claude/skills/*/SKILL.md
.harness/adapters/claude.managed.json
```

## What it does

1. Loads and validates `adapters/claude/adapter.yaml`
2. Reads `.harness/harness.yaml`
3. Validates structure against Harness schemas
4. Loads the selected Profile and merges lists (omit → inherit; present → replace)
5. Resolves Rules, Skills, and Tools to canonical paths
6. Plans Claude Rules and Skills using declared output paths
7. Verifies planned kinds match supported capabilities
8. Prefights conflicts (**fail-closed** — no writes if any conflict)
9. Warns for Tools (selected but not projected)
10. Applies writes and refreshes the managed manifest

Canonical content stays in `rules/` and `skills/`. Generated Claude files are a representation, not a second source of truth.

## Supported

| Capability | Projection |
| --- | --- |
| Rules | `.claude/rules/harness/<category>--<stem>.md` materialized projections of canonical Rule markdown |
| Skills | `.claude/skills/<skill-id>/SKILL.md` thin wrappers that point at canonical `skills/**/SKILL.md` |

Declared in `adapter.yaml` and enforced by the generator.

## Not supported

| Capability | Behavior |
| --- | --- |
| Tools | Resolved for existence; **not** written as Claude config. Warning emitted. |
| MCP install / hooks / settings.json | Out of scope |
| Managing or overwriting `CLAUDE.md` | Out of scope (see below) |
| `.claude/commands/`, subagents, auto memory | Out of scope |

## CLAUDE.md policy

Official Claude Code docs: project instructions may live at `./CLAUDE.md` or `./.claude/CLAUDE.md`. That file is often authored and owned by the project team (or by `/init`), not by a vendor adapter.

**Harness decision (v1):** this adapter does **not** create, update, or overwrite `CLAUDE.md` / `.claude/CLAUDE.md`.

### Why

- `CLAUDE.md` is a high-impact, always-loaded project instruction surface
- Overwriting a user-managed `CLAUDE.md` would violate fail-closed ownership expectations
- Rules and Skills already provide documented modular surfaces under `.claude/`
- `@path` imports are verified for `CLAUDE.md`, but managing that file is a separate product decision

### Impact

- Project-root `CLAUDE.md` (including this repository’s own file) is left untouched
- Harness Rules/Skills are projected only under `.claude/rules/harness/` and `.claude/skills/`

### When to revise

- If a future explicit opt-in policy (e.g. managed fragment + import) is designed and documented
- If official Claude Code guidance changes how project memory and rules compose

## Rule load policy

Official Claude Code docs:

| Mode | Mechanism |
| --- | --- |
| Always at launch | Rule `.md` **without** `paths` frontmatter |
| Path-scoped | YAML frontmatter `paths:` with globs |

**Harness decision (v1):** generated Rules have **no** `paths` frontmatter, so they load at session start (same priority class as `.claude/CLAUDE.md` per official docs).

### Why

- Canonical Rules do not yet carry path-scope metadata
- Inventing globs would be unsafe and agent-specific guesswork
- Claude has no verified “Apply Intelligently via description” equivalent for `.claude/rules/` (that role is closer to Skills)

### Impact

- All selected Rules enter launch context (token cost scales with selection)
- Prefer keeping Harness Rule selections focused; use Skills for task-specific procedures

### Extensibility (not implemented yet)

Optional per-Rule `paths` when canonical metadata or adapter policy maps exist.

## Projection strategy

| Strategy | Status | Trade-off |
| --- | --- | --- |
| Materialized Rule body under `.claude/rules/harness/` | **Used** | Reliable load at launch; regenerate to sync; higher drift risk than references |
| Thin Rule wrapper + `@path` import | **Not used** | `@path` imports are documented for **CLAUDE.md**, not verified for `.claude/rules/` |
| Symlink canonical Rules into `.claude/rules/` | **Not used** | Officially supported for rules, but poor Windows/CI portability (same rationale as Cursor) |
| Thin Skill wrapper pointing at canonical path | **Used**; agent must open the canonical file | Low drift; not a native remote skill path |
| Materialized full Skill copy | Not used | Higher reliability if wrappers are ignored; higher drift |
| Managing `CLAUDE.md` with `@` imports of Rules | **Not used** | Avoids overwriting project/user CLAUDE.md |

If Claude later documents `@path` expansion inside `.claude/rules/` equivalently to CLAUDE.md, revisit thin Rule references — do not invent unsupported APIs.

## How it works

### Generation model

1. **Rules** — write managed `.md` files under `.claude/rules/harness/` containing the canonical Rule body plus a managed header
2. **Skills** — write thin `SKILL.md` wrappers under `.claude/skills/<skill-id>/` that preserve `name` / `description` and instruct the agent to follow the canonical Skill path
3. **Does not** manage `CLAUDE.md`

### Harness-managed detection

Generated files include:

```html
<!-- ai-engineering-harness:managed -->
```

A managed-output inventory is written to:

```text
.harness/adapters/claude.managed.json
```

| Field | Meaning |
| --- | --- |
| `version` | Manifest format version |
| `adapter` | `claude` |
| `adapter_version` | From `adapter.yaml` `version` |
| `files` | Relative paths currently managed |
| `marker` | Managed marker string |

The manifest is **not** source of truth. Desired state remains `.harness/harness.yaml`.

| Kind | Policy |
| --- | --- |
| Harness-managed | Safe to update or remove on regenerate |
| User-managed (no marker) | Never overwritten; fail-closed |
| Canonical `rules/` / `skills/` | Never modified by this adapter |
| Existing `CLAUDE.md` | Never modified by this adapter |

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

Re-running the generator with the same harness config regenerates the same managed outputs and refreshes the manifest.

## Generated files

```text
.claude/rules/harness/<category>--<rule-stem>.md
.claude/skills/<skill-id>/SKILL.md
.harness/adapters/claude.managed.json
```

Example Rule projection shape:

```markdown
<!-- ai-engineering-harness:managed -->

# Harness Rule: core/core

This file is a Claude Code projection generated by the AI Engineering Harness.

Canonical Rule (source of truth): `rules/core/core.md`

Do not edit this file by hand. Change the canonical Rule and regenerate.

---

# Core fixture rule

Always verify fixture generation.
```

## Usage

From the repository root (preferred — no `sys.path` mutation):

```bash
python -m adapters.claude.generate
python -m adapters.claude.generate --dry-run
python -m adapters.claude.generate --root /path/to/project
```

Via the thin Harness CLI:

```bash
python -m harness generate claude
python -m harness generate claude --dry-run
```

Direct script form still works via a minimal path bootstrap:

```bash
python adapters/claude/generate.py
python adapters/claude/generate.py --dry-run
```

## Verification Status

Classify harness claims about Claude Code behavior honestly.

| Topic | Status | Notes |
| --- | --- | --- |
| Project rules live under `.claude/rules/` as `.md` | **Verified** | Official Claude Code memory / directory docs |
| Rules discovered recursively under `.claude/rules/` | **Verified** | Official docs |
| Rules without `paths` load at launch | **Verified** | Official docs |
| Rules with `paths` frontmatter are path-scoped | **Verified** | Official docs (not emitted by this adapter yet) |
| `@path` imports inside `CLAUDE.md` | **Verified** | Official docs |
| `@path` import expansion inside `.claude/rules/*.md` | **Not verified** | Not claimed by this adapter |
| Symlinks under `.claude/rules/` | **Verified** (documented) | Not used (portability) |
| Skills at `.claude/skills/<name>/SKILL.md` | **Verified** | Official Skills docs |
| Skill frontmatter `name` + `description` | **Verified** | Official Skills docs |
| Thin Skill wrappers causing the agent to open canonical `skills/**/SKILL.md` | **Not verified** | Relies on agent following wrapper instructions |
| Nested skill directories under a `harness/` namespace folder | **Not used** | Official layout is `.claude/skills/<name>/SKILL.md` |
| Tools / MCP projection | **Not supported** | Declared unsupported in `adapter.yaml` |
| Runtime behavior with Claude Code binary installed | **Not verified** | Generation/tests do not require Claude Code |

## Limitations

- Status: **experimental**
- Does not install or configure Tools or MCP
- Does not require Claude Code to be installed; it only writes files
- Materialized Rules can drift until regenerate
- Thin Skill wrappers rely on the agent reading the canonical Skill file
- Symlinks are not used (portability; Windows and CI friendliness)
- Unconditional Rule load increases launch context cost
- No per-Rule `paths` overrides yet
- Does not manage `CLAUDE.md`

## Compatibility

| Input | Required |
| --- | --- |
| `.harness/harness.yaml` | Yes |
| Matching Profile under `profiles/` | Yes |
| Selected Rules / Skills / Tools on disk | Yes |
| `adapters/claude/adapter.yaml` | Yes (loaded by generator) |
| Claude Code installed | No (generation/tests) |

## Verification

```bash
python scripts/validate-config.py
python -m unittest discover -s tests -q
python -m adapters.claude.generate --dry-run
python -m harness generate claude --dry-run
```

## Sources

Official Claude Code documentation consulted while implementing this adapter:

| Topic | URL | Notes |
| --- | --- | --- |
| Memory / CLAUDE.md / `.claude/rules/` | https://code.claude.com/docs/en/memory | Verified: CLAUDE.md locations; `@` imports for CLAUDE.md; rules `.md` + optional `paths`; recursive discovery; symlinks for rules |
| Explore the `.claude` directory | https://code.claude.com/docs/en/claude-directory | Verified: layout for rules, skills, CLAUDE.md |
| Skills | https://code.claude.com/docs/en/skills | Verified: `.claude/skills/<name>/SKILL.md`; frontmatter; discovery; supporting files |

Last reviewed against those pages for this adapter implementation.

Anything not listed above should be treated as **Not verified**.
