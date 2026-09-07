# Current State

Snapshot based on the repository working tree on 2026-09-07. Status reflects observable code and documentation, not planned work.

## Implemented

| Area | Status | Current scope |
| --- | --- | --- |
| Declarative configuration | Implemented | Schema validation for `.harness/harness.yaml`; Profile lists use replace-or-inherit semantics. |
| Profiles, Rules, and Skills | Implemented | One `software-engineer` Profile and canonical Rules/Skills with documented contracts. |
| Tool Registry | Implemented | `tools/registry.yaml`, schema validation, documentation-reference validation, and one RTK entry. |
| Tool resolution | Implemented | Read-only Registry loading and lookup by stable Tool id. |
| Tool detection | Implemented | Read-only CLI detection library with platform checks, constrained version probes, and transient results. |
| Tool health | Implemented | Read-only CLI health probe composed with DetectionResult; optional declarative Registry `health` contract; `harness tools health <tool>`. |
| Cursor adapter | Experimental | Generates a Cursor projection from canonical configuration with fail-closed conflict handling. |
| Claude adapter | Experimental | Generates a Claude Code projection (`.claude/rules`, `.claude/skills`) without managing `CLAUDE.md`. |
| CLI | Implemented | Thin `validate`, `generate cursor|claude`, `tools health`, and `version` interface. |
| Security Profiles | Planned | No security-specific Profile exists; security is currently a selected Rule category. |

## Commands

Run from the repository root:

```text
python scripts/validate-config.py
python -m harness validate
python -m harness generate cursor --dry-run
python -m harness generate cursor
python -m harness generate claude --dry-run
python -m harness generate claude
python -m harness tools health rtk
python -m harness version
python -m adapters.cursor.generate --dry-run
python -m adapters.claude.generate --dry-run
python -m unittest discover -s tests -q
```

## Current repository structure

```text
.harness/       project selection and adapter manifests
adapters/       vendor-specific projections (Cursor, Claude)
docs/           architecture, Tool docs, and project context
harness/        thin CLI and shared runtime code
profiles/       reusable capability compositions
rules/          canonical persistent behavior
schemas/        configuration and Registry schemas
scripts/        validation and bootstrap helpers
skills/         canonical reusable procedures
tests/          unit and adapter tests
tools/          declarative Tool Registry
```

## Current tests

The standard command is `python -m unittest discover -s tests -q`. At this snapshot it ran 122 tests successfully after Health checking landed.

## Known limitations

- There is one implemented, experimental Cursor adapter; no Claude, Codex, or other adapter generator exists.
- Configuration validation is structural. Semantic resolution occurs in the adapter path rather than as a standalone validation command.
- The Registry currently contains one Tool and has no installation, configuration, package-management, or MCP runtime layer.
- Detection and Health support declared CLI Tools only. Health uses a minimal declared liveness probe; it does not prove full Tool capability.
- No effective-risk, authorization, provenance, trust, or persisted runtime observation model exists.

## Current risks

- `README.md` may still describe runtime `tools/` integrations more narrowly than the committed resolution, detection, and health layers. Keep entry docs aligned when they drift.
- Health liveness must not be confused with authorization, baseline risk, or effective risk.