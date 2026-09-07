# AI Engineering Harness

## What is the project?

AI Engineering Harness is a vendor-neutral foundation for agent-assisted engineering. It gives projects a small, reusable structure for persistent behavior, task procedures, tool metadata, security posture, and configuration selection. It exists to make those concerns explicit, composable, and portable instead of embedding them in one large vendor prompt.

The long-term direction is infrastructure that can serve developers and AI agents across software engineering, frontend, backend, DevOps, AI engineering, and defensive or authorized security work. It is not tied to one model, programming language, framework, or agent product: vendor-specific formats are produced by adapters while the canonical content remains shared.

## Core principles

- Canonical Rules, Skills, Profiles, configuration, and Tool metadata are vendor-neutral; adapters are projections for a particular agent.
- `.harness/harness.yaml` declares project intent. Profiles provide reusable defaults, and explicit lists replace a Profile list rather than deep-merge.
- Configuration and Registry data are declarative. Generation is designed to be deterministic and Cursor conflicts are fail-closed before writes.
- Runtime observations are separate from project configuration and catalog metadata. Detection does not persist its results.
- Tools describe capabilities and catalog-level security metadata; selecting or detecting a Tool is not authorization to use it.
- The core stays deliberately small: no plugin discovery, package manager, remote registry, or runtime orchestration is implied by the current code.
- Security uses restricted data contracts and structured process arguments for CLI detection and health; it avoids arbitrary commands and shell evaluation.

## High-level architecture

```text
.harness/harness.yaml (project intent)
                |
                v
          Profile defaults
                |
                v
   Rules / Skills / Tool selection
                |
                v
  Core validation, resolution, and adapters
                |
                v
     Agent-specific projection (Cursor today)
```

- **Configuration** selects a Profile and optional Rule, Skill, and Tool lists.
- **Profiles** are reusable compositions; they do not duplicate content.
- **Rules** define persistent behavior; **Skills** define reusable procedures.
- **Tools** are external capabilities described in a declarative Registry.
- **Core** provides thin validation, resolution, detection, health checking, and adapter dispatch.
- **Adapters** translate canonical intent into vendor-specific generated files.

## Source of truth

| Source | Represents |
| --- | --- |
| `.harness/harness.yaml` | This project's selected Profile and explicit resource selection |
| `profiles/` | Reusable default compositions |
| `rules/` and `skills/` | Canonical behavioral and procedural content |
| `tools/registry.yaml` | Canonical machine-readable Tool metadata |
| `docs/` | Contracts, rationale, operating guidance, and project context |
| Runtime observations | Ephemeral local facts such as a Tool DetectionResult; not catalog or configuration truth |

When documentation diverges from implementation or configuration, inspect and follow the implementation/configuration, then correct the documentation.

## Agent adapters

Cursor is the only implemented adapter and is experimental. It reads the canonical configuration and generates Cursor-specific configuration; it does not become a second source of truth. Claude is represented by a repository entrypoint (`CLAUDE.md`) but has no generated adapter. Other adapters are future work and must preserve this canonical-to-vendor direction.

## Tools and security model

The Registry supplies Tool identity, capabilities, supported platforms, detection and optional health metadata for CLI Tools, and `security.baseline_risk` plus declared access surfaces. Resolution is data lookup. Detection is a read-only local observation of whether a declared CLI executable is available and probeable. Health is a separate read-only observation of whether a detected Tool responds to a declared minimal probe.

The following distinctions matter:

- **Capability** is what a Tool can do; **access surface** is the kind of access it normally needs (for example filesystem or network).
- **Baseline risk** is catalog-level risk, not the risk of a particular host.
- **Detection** records availability; **Health** records minimal operational response and must not be inferred from presence alone.
- **Authorization, scope, provenance, and effective runtime risk** are not implemented policy or runtime models. They remain separate concerns for future design rather than implications of Registry metadata.

## Important non-goals

The current Harness is not a pentest, malware, or exploit framework; an agent orchestration framework; a package manager; a security authorization engine; or a general runtime for MCP servers. It documents and selects capabilities but does not install, configure, or authorize them.

# Mental model

The Harness defines canonical intent, not an agent vendor. Profiles compose the context needed for a kind of work. Rules constrain behavior, Skills provide reusable procedures, and Tools describe capabilities plus limited runtime observations. An adapter translates the selected canonical resources into the format required by one agent environment.

# Working With AI Agents

1. Read `AGENTS.md`; read `CLAUDE.md` when working with Claude.
2. Read this file and `CURRENT_STATE.md`, then the architecture document that governs the area being changed.
3. Inspect the relevant implementation and configuration before modifying it.
4. Preserve source-of-truth boundaries and avoid duplicating canonical content in an adapter or Profile.
5. Run proportionate validation and tests, then report evidence and limitations.

# Context Recovery

These documents let work resume in another chat, agent, computer, or by a new developer. If conversation history is unavailable, repository documentation must be treated as the primary context. The real code and configuration remain the final source of truth when they conflict with documentation.
