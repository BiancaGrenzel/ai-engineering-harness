# Configuration Architecture

Official standard for Harness configuration and Profiles.

Project configuration lives in [`.harness/harness.yaml`](../../.harness/harness.yaml).
Reusable Profile defaults are authored in [`profiles/`](../../profiles/) and shipped
in the installed content pack. After `harness init`, a project-local
`profiles/<name>.yaml` (plus the selected Rules, Skills, schemas, and Tools) is
the project's source of truth. This document defines the contract. The CLI
(`python -m harness`) reads these files for validation and adapter generation;
see [`cli.md`](cli.md).

## Purpose

Configuration answers a single question for a project:

> Which AI Engineering Harness capabilities does this project want to use?

Configuration is **declarative**. It declares desired state. It does not contain long agent instructions, Skill workflows, or Tool manuals.

## Installed pack vs project-local content

| Location | Role |
| --- | --- |
| Installed content pack (`harness/content/_data`) | Immutable seed shipped with the package |
| Project trees after `harness init` | `.harness/profiles`, `.harness/rules`, `.harness/skills`, `.harness/schemas`, `.harness/tools`, `.harness/docs` — project Harness source of truth |
| This repository's root trees | Authoring / dogfooding source used to build the pack |

End users need the installed package, not a clone of this repository. There is no
remote content registry and no runtime download from GitHub. Vendor projections
(`.cursor/`, `.claude/`) stay at the project root and are not Harness canonical content.

## Core concepts

| Concept | Kind | Role |
| --- | --- | --- |
| Global agent instructions | Behavior contract | Standing expectations for agents working in this repository (`AGENTS.md`, entry adapters such as `CLAUDE.md`) |
| Harness configuration | Configuration | Project selection of Profile and optional Rule/Skill/Tool lists (`.harness/harness.yaml`) |
| Profile | Configuration composition | Reusable default lists of Rules, Skills, and Tools (`profiles/`) |
| Rules | Behavior | Persistent agent behavior (`rules/`) |
| Skills | Procedure | Specialized workflows (`skills/`) |
| Tools | Capability | External capabilities (catalog in `docs/tools/`) |
| Project-specific instructions | Behavior / policy | Repo-local guidance beyond the harness (for example team norms, ADRs) |

These layers are related but not interchangeable:

- **Configuration** selects what is in scope.
- **Behavior** constrains how the agent acts (Rules, agent instructions).
- **Procedure** explains how to perform a class of work (Skills).
- **Capability** is something the agent may invoke (Tools).

Do not put procedures in Profiles. Do not put Rule prose in `harness.yaml`. Do not put Tool install manuals in configuration.

## Layer relationships

```text
AGENTS.md / adapter entrypoints
        ↓ (behavior contract)
.harness/harness.yaml
        ↓ (selects)
Profile
        ↓ (defaults for)
Rules + Skills + Tools
        ↓ (used under)
Project-specific instructions
```

Precedence is about **role**, not automatic text override:

1. **Global agent instructions** — primary behavioral contract for agents in this repo.
2. **Harness configuration** — declares which Profile and resource lists apply to the project.
3. **Profile** — supplies default resource lists when the project omits them.
4. **Rules** — persistent behavior once selected/loaded.
5. **Skills** — procedures activated when the task matches (selection ≠ automatic activation of every Skill).
6. **Tools** — capabilities available when selected and present in the environment.
7. **Project-specific instructions** — additional local policy; must not silently contradict security or harness contracts without explicit intent.

A later layer does **not** rewrite an earlier layer's meaning. Configuration does not override Rule text. Profiles do not replace Skills. Tools do not redefine Rules.

## Profile vs Harness configuration

| | Profile | Harness configuration |
| --- | --- | --- |
| File | `profiles/<name>.yaml` | `.harness/harness.yaml` |
| Scope | Reusable work-type defaults | One project |
| Required fields | `name`, `rules`, `skills`, `tools` | `version`, `profile` |
| May override lists | No (it *is* the default) | Yes, by replacing a list |

Simple model (this phase):

- No Profile inheritance
- No `extends`
- No nested Profiles
- No expressions or templating

## Defaults

| Field in `harness.yaml` | Required | Default when omitted |
| --- | --- | --- |
| `version` | Yes | — (must be present) |
| `profile` | Yes | — (must be present) |
| `rules` | No | Use the Profile's `rules` list |
| `skills` | No | Use the Profile's `skills` list |
| `tools` | No | Use the Profile's `tools` list |

There are no magic implicit Rules beyond what the Profile (or an explicit list) declares.

Empty array means “no items in this list after merge,” not “fall back to Profile.”

## Merge strategy

Predictable **replace-or-inherit** strategy:

1. Start from the Profile named by `profile`.
2. For each of `rules`, `skills`, `tools`:
   - If the field is **omitted** in `harness.yaml` → use the Profile list.
   - If the field is **present** in `harness.yaml` → use that list as the full replacement (no deep merge).

To add an item relative to a Profile: copy the Profile list and append.

To remove an item: copy the Profile list and omit that item.

No remove operators, patch syntax, or scripting in this phase.

## `harness.yaml` model

```yaml
version: 1
profile: software-engineer

rules:
  - core
  - context
  - security
  - quality
  - production

skills:
  - task-analysis
  - planning
  - context-engineering
  - research
  - verification
  - token-optimization

tools:
  - rtk
```

### Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `version` | integer | Configuration **format** version (not a Tool version, not a git tag) |
| `profile` | string | Profile id → `profiles/<id>.yaml` |
| `rules` | string[] | Rule category ids under `rules/` |
| `skills` | string[] | Skill ids |
| `tools` | tool entries | Tool ids (see Tool entries) |

## Tool entries

Initial representation: a **string** Tool id.

```yaml
tools:
  - rtk
```

Forward-compatible object form (allowed by schema; not required today):

```yaml
tools:
  - name: rtk
    enabled: true
    config: {}
```

Decision:

- Prefer strings in project configs until a Tool needs verified project-level settings.
- Do not invent RTK `config` values in this harness without verification from official RTK docs and a concrete project need.
- Tool-specific defaults still belong with the Tool (for example user-level RTK config), not in Harness configuration, unless the harness must declare project intent.

## Versioning

`version: 1` is the **Harness configuration schema/format version**.

| Increment when | Do not increment for |
| --- | --- |
| Incompatible field meaning or required-structure changes | Adding a new Profile |
| Removing or renaming fields without compatibility | Documenting a new Tool |
| Changing merge semantics incompatibly | Bumping an upstream Tool release |

Differences:

| Version | Meaning |
| --- | --- |
| Harness `version` | Format of `harness.yaml` / profile contract |
| Tool version | Upstream software release (documented on Tool pages) |
| Repository git version / tags | Source history of this project |

No migration system in this phase. Future major bumps should document a migration path when introduced.

## Naming conventions

All stable identifiers are:

- lowercase
- kebab-case when multi-word
- short and stable
- vendor-neutral when possible

| Kind | Examples | Notes |
| --- | --- | --- |
| Rule (in config) | `core`, `context`, `security` | Category directories under `rules/` |
| Skill | `task-analysis`, `token-optimization` | Matches Skill directory / frontmatter `name` |
| Tool | `rtk` | Matches Tool Registry `name` |
| Profile | `software-engineer` | Matches `profiles/<name>.yaml` |

Avoid agent-vendor names in canonical identifiers (`cursor-only-rules`, etc.).

## Syntax validation vs semantic resolution

### Syntax validation

Question: Does the YAML match the JSON Schema?

Implemented by [`scripts/validate-config.py`](../../scripts/validate-config.py) against [`schemas/harness.schema.json`](../../schemas/harness.schema.json).

Example: `rules: [security]` is syntactically valid.

### Semantic resolution

Question: Do referenced Profiles, Rules, Skills, and Tools exist and resolve unambiguously?

Example: `rules: [security]` is semantically valid only if `rules/security/` (or the agreed mapping) exists.

**Adapter generators** perform semantic resolution when projecting configuration (see [`adapters/common/resolve.py`](../../adapters/common/resolve.py)). A future CLI may expose the same checks directly.

Keep the separation:

| Check | Responsibility |
| --- | --- |
| Structure / types / required fields | JSON Schema |
| Existence / path mapping / duplicates across catalogs | Semantic resolver (adapters today; CLI later) |

## Schemas

| Schema | Validates |
| --- | --- |
| [`schemas/harness.schema.json`](../../schemas/harness.schema.json) | `.harness/harness.yaml` |
| [`schemas/profile.schema.json`](../../schemas/profile.schema.json) | `profiles/*.yaml` |

A separate Profile schema exists because Profiles have a different required shape (`name` + lists) than project configuration (`version` + `profile`).

Both schemas set `additionalProperties: false` at the document root to catch typos early, while leaving room for controlled evolution via format `version`.

## Out of scope for this phase

- CLI (`harness validate`, etc.)
- Semantic resolver
- Dependency / plugin / package managers
- MCP or agent runtimes
- Profile inheritance and conditionals
- Automatic Tool installation

## Relationship to AGENTS.md

[`AGENTS.md`](../../AGENTS.md) remains the primary agent contract.

This document specializes Section 12 (Source of Truth), Section 13 (Profiles), and the `.harness/` configuration path. If conflict arises, update this architecture doc and keep `AGENTS.md` as the concise contract.
