# Harness configuration

Project-local configuration for the AI Engineering Harness.

## What is `.harness`?

`.harness/` holds **project configuration** for this harness — not Rules, Skills, Tools, or Profiles.

| Path | Role |
| --- | --- |
| `.harness/harness.yaml` | Declarative desired configuration for this project |
| `.harness/README.md` | Short practical guide (this file) |
| `.harness/adapters/` | Optional manifests written by adapters (Harness-managed output inventory) |

Canonical resources stay elsewhere:

| Resource | Location |
| --- | --- |
| Rules | `rules/` |
| Skills | `skills/` |
| Profiles | `profiles/` |
| Tool catalog | `docs/tools/` |
| Schemas | `schemas/` |

## What is `harness.yaml`?

A small, declarative file that answers:

> Which Harness configuration does this project want to use?

It declares state. It does not contain agent instructions, workflows, or tool manuals.

## Minimal example

```yaml
version: 1
profile: software-engineer
```

With only `version` and `profile`, Rule/Skill/Tool lists inherit from the Profile.

This repository also lists selections explicitly for clarity:

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

## How it works

1. Read `.harness/harness.yaml`.
2. Load the named Profile from `profiles/<profile>.yaml`.
3. Apply merge rules (see architecture doc): omitted lists inherit; present lists replace.
4. Resolve identifiers to canonical Rules, Skills, and Tools (future semantic resolution).

Today, only **syntax validation** is implemented. Semantic resolution is not implemented yet.

## Relation to Profiles

A **Profile** is a reusable default composition (`profiles/`).

**Harness configuration** selects a Profile and may override lists for this project.

## Relation to Rules, Skills, and Tools

| Layer | Role in configuration |
| --- | --- |
| Rules | Named categories or identifiers of persistent behavior to include |
| Skills | Named specialized procedures available to the project |
| Tools | Named external capabilities selected for the project |

Configuration **selects**. It does not redefine Rule text, Skill workflows, or Tool docs.

## Validate

Syntax validation:

```bash
python -m harness validate
# equivalent:
python scripts/validate-config.py
```

Requires dependencies listed in `scripts/requirements.txt`.

Full contract: [`docs/architecture/configuration.md`](../docs/architecture/configuration.md) · CLI: [`docs/architecture/cli.md`](../docs/architecture/cli.md)
