# ADR: Tool System Architecture

## Status

Accepted

## Context

The Harness currently documents Tools under `docs/tools/` and lets projects select
Tool identifiers in `.harness/harness.yaml`. A future Tool System must support
resolution, compatibility checks, diagnostics, installation guidance, and optional
agent integration without coupling those concerns to the CLI, documentation, or a
specific agent vendor.

This ADR records the architecture boundary only. It does not introduce a Registry,
runtime implementation, installer, MCP integration, or CLI command.

## Decision

The future Tool System will use a declarative `tools/registry.yaml` as the
canonical source of operational Tool metadata. It will describe identity,
platform and version support, detection and health contracts, installation options,
capabilities, security metadata, and vendor-neutral integration modes.

The Registry must not contain executable code, arbitrary scripts, package-manager
logic, Adapter logic, or runtime state.

## Source of Truth

The system separates four kinds of information:

- `.harness/harness.yaml` declares project intent: which Tools are in scope.
- Future `tools/registry.yaml` is the machine-readable source of operational Tool
  metadata.
- `docs/tools/` remains human-readable documentation, evidence, rationale, and
  usage guidance.
- Runtime state is an observed, transient result and is never configuration or
  catalog truth.

Documentation and Registry metadata should reference one another where useful, but
must not duplicate facts unnecessarily.

## Tool Model

A Tool is an external engineering capability, not necessarily a CLI. It may be a
CLI, MCP server, API service, local service, library, platform, or utility. Each
Tool has a stable, vendor-neutral `id`; display names, binaries, packages, URLs,
and providers are attributes rather than identity.

Project configuration remains intentionally simple:

```yaml
tools:
  - rtk
```

Selection means that the Tool is part of project intent. It does not authorize or
request automatic installation. Per-Tool objects may be added later only when a
concrete project-level requirement exists.

Capabilities describe what a Tool offers, for example `token-reduction`,
`command-wrapping`, and `output-compression`. They do not grant authority to use
the Tool.

## Lifecycle

Tool state is multidimensional, not linear, because catalog status, project
declaration, local presence, compatibility, configuration, health, and agent
exposure can differ independently.

| Dimension | States |
| --- | --- |
| Catalog | `known`, `deprecated` |
| Project | `undeclared`, `declared` |
| Runtime | `absent`, `detected` |
| Compatibility | `unknown`, `compatible`, `incompatible` |
| Configuration | `not-required`, `unconfigured`, `configured` |
| Health | `unsupported`, `unavailable`, `healthy`, `unhealthy`, `timeout`, `error` |
| Exposure | `unavailable`, `available` |

For example, a Tool can be declared but absent, detected but incompatible, or
healthy without being exposed to the selected agent.

## Detection and Health

Detection answers: “Does a candidate installation or access path exist?” It may
report evidence such as path, endpoint, and detected version.

Health answers: “Does the Tool function minimally according to a safe check?” A
health check is separate from detection and must not be assumed from a binary being
present.

`detected != healthy`; `healthy != safe`; and `healthy != exposed to an agent`.

CLI Detection and CLI Health are implemented as separate read-only runtime layers
over Registry metadata. Health composes `DetectionResult` and uses an optional
declarative `health` contract; it does not reuse `detection.version_arguments`
automatically. Installation and agent exposure remain future work.

## Installation Boundary

Responsibilities are separated as follows:

```text
Harness Core → Tool Registry → future Tool Installer
```

The Core coordinates resolution, policy, and reporting. The Registry describes
Tools and their supported installation options. A future Installer performs an
explicitly authorized installation.

The Core must not acquire tool-specific knowledge of Homebrew, npm, Cargo, winget,
apt, or other package managers. An Installer must evaluate the declared method,
its prerequisites, platform, provenance, and authorization independently.

## Security Model

Tool metadata separates:

- **Capabilities** — what the Tool offers.
- **Permissions / access surface** — what the Tool can reach, such as command
  execution, filesystem, network, secrets, and persistent data.
- **Baseline risk** — the catalog-level potential impact and blast radius of that
  access under the Tool's normal documented behavior.

The future Registry is the source of truth for this catalog-level security
metadata. Runtime may report additional local conditions, but must not silently
rewrite Registry classification or project configuration.

Effective runtime risk is future runtime observation, not Registry metadata.
Provenance and trust are future, separate metadata concerns; they are neither
access surface nor baseline risk.

## Agent Integration

The Tool Registry remains vendor-neutral. A Tool may declare neutral integration
modes, such as explicit CLI use, command-rewrite hook, MCP, API, or instruction.

An Adapter decides whether and how a particular agent can use a declared mode.
Therefore the Registry is not Cursor, Claude, or Codex configuration, and
Tool-specific agent projection remains in the corresponding Adapter.

## Consequences

- Tool selection, operational metadata, human documentation, and observed runtime
  state have explicit ownership boundaries.
- Future `check`, `doctor`, `install`, and `update` CLI commands can delegate to
  dedicated services rather than embed Tool logic in the CLI.
- The architecture supports non-CLI Tools and multiple installation methods without
  assuming a package manager or agent vendor.
- Security and compatibility can be reported consistently before installation is
  introduced.
- CLI Tool Detection is a separate, read-only runtime layer over Registry
  metadata.
- CLI Tool Health is a separate, read-only runtime layer that composes Detection
  results and optional declarative health probes.
- Installation and agent exposure remain future work.

## Alternatives Considered

- **Tool Registry as Python code:** rejected because catalog data should be
  declarative, reviewable, and consumable without importing runtime logic.
- **JSON as source of truth:** rejected in favor of YAML for consistency with the
  Harness configuration and maintainable declarative review; JSON may be generated
  or consumed later.
- **Documentation as source of truth:** rejected because prose is unsuitable for
  deterministic resolution and validation.
- **Linear lifecycle:** rejected because Tool conditions are independent rather
  than sequential.
- **Installer inside the Core:** rejected to preserve least privilege and isolate
  package-manager-specific execution.
- **Tool-specific logic inside Adapters:** rejected to preserve vendor neutrality
  and prevent duplicated Tool semantics.
- **Mandatory complex project configuration:** rejected because a list of Tool IDs
  expresses current intent with less configuration cost.
- **Complete dependency resolver:** rejected because independent validation covers
  the initial need without solver complexity.

## Open Questions

- Whether organizations or projects will be allowed to extend the canonical
  Registry.
- Which provenance verification policy will be required before installation exists.
- How secret-bearing, authenticated, or production-facing Tools will be selected
  by future policy.
- How long runtime observations may be cached without becoming assumed truth.
- Which version constraint forms are justified beyond direct compatibility checks.
