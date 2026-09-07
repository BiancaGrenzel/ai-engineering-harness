# Harness configuration

Project-local **intent** for the AI Engineering Harness.

## What is `.harness`?

`.harness/` holds **project intent** for this harness — not Rules, Skills, Tools, or Profiles.

| Path | Role |
| --- | --- |
| `.harness/harness.yaml` | Declarative desired configuration for this project |
| `.harness/README.md` | Short practical guide (this file) |
| `.harness/adapters/` | Optional manifests written by adapters (Harness-managed output inventory) |

Canonical resources live in the **content pack** (installed package or this
repository when developing from source):

| Resource | Location |
| --- | --- |
| Rules | content pack `rules/` |
| Skills | content pack `skills/` |
| Profiles | content pack `profiles/` |
| Tool Registry | content pack `tools/registry.yaml` |
| Tool catalog docs | content pack `docs/tools/` |
| Schemas | content pack `schemas/` |

Consumer projects do not need those directories at the project root.

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
2. Load the named Profile from the content pack.
3. Apply merge rules (see architecture doc): omitted lists inherit; present lists replace.
4. Resolve identifiers against the content pack (fail-closed if missing).
5. `harness generate` materializes self-contained agent projections.

## Relation to Profiles

A **Profile** is a reusable default composition in the content pack.

**Harness configuration** selects a Profile and may override lists for this project.

## Relation to Rules, Skills, and Tools

| Layer | Role in configuration |
| --- | --- |
| Rules | Named categories or identifiers of persistent behavior to include |
| Skills | Named specialized procedures available to the project |
| Tools | Named external capabilities selected for the project |

Configuration **selects**. It does not redefine Rule text, Skill workflows, or Tool docs.

## Validate

```bash
python -m harness validate
# equivalent:
python scripts/validate-config.py
```

Requires dependencies listed in `scripts/requirements.txt`.

Full contract: [`docs/architecture/configuration.md`](../docs/architecture/configuration.md) · CLI: [`docs/architecture/cli.md`](../docs/architecture/cli.md)
