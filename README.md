# AI Engineering Harness

A vendor-neutral foundation for using AI agents in software engineering and related technical disciplines.

## What is this?

An **AI Engineering Harness** is a reusable architecture for agent-assisted work.

It organizes persistent behavior, specialized procedures, tools, security controls, and operational practices so agents can work more reliably across projects and environments.

This is not a giant prompt collection. It is a structured harness based on Context Engineering, Rules, Skills, Tools, MCP, security, evaluation, observability, and production practices.

## Goals

- Context efficiency
- Reusable agent behavior
- Tool integration
- Security
- Evaluation
- Observability
- Production readiness

## Architecture

Canonical layout:

```text
rules/       # persistent agent behavior (canonical)
skills/      # specialized procedures (canonical)
docs/        # documentation (includes Tool Registry)
profiles/    # role-specific compositions
.harness/    # project harness configuration
schemas/     # JSON Schemas for configuration
scripts/     # small development utilities
tools/       # integrations and utilities (planned)
.cursor/     # Cursor adapter (planned)
.claude/     # Claude adapter (planned)
```

Provider-specific directories act as adapters. Canonical resources stay vendor-neutral.

### Rules, Skills, Tools, Profiles, Configuration

| Layer | Role |
| --- | --- |
| **Rules** | Persistent agent behavior |
| **Skills** | Specialized procedures |
| **Tools** | External capabilities (CLI, MCP, services, utilities, …) |
| **Profiles** | Reusable default compositions of Rules, Skills, and Tools |
| **Configuration** | Project selection of a Profile and optional overrides (`.harness/harness.yaml`) |

The **Tool Registry** documents external tools with evidence-based metadata: type, status, security, token/context impact, and agent compatibility. Catalog docs live in [`docs/tools/`](docs/tools/). Runtime integrations under `tools/` are not implemented yet.

## Configuration

Project configuration is declarative and lives in [`.harness/harness.yaml`](.harness/harness.yaml).

- Configuration declares desired state (which Profile and resource lists apply)
- Profiles compose defaults ([`profiles/`](profiles/))
- Rules define persistent behavior
- Skills define specialized procedures
- Tools provide external capabilities

Contract: [`docs/architecture/configuration.md`](docs/architecture/configuration.md)

Validate syntax (CLI is **not** implemented yet):

```bash
pip install -r scripts/requirements.txt
python scripts/validate-config.py
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Principles

- Understand before modifying
- Make the minimal sufficient change
- Reuse before creating
- Do not invent APIs, paths, or capabilities
- Load minimum sufficient context
- Prefer least privilege
- Verify before claiming success
- Keep the harness useful across agents and disciplines

See [AGENTS.md](AGENTS.md) for the full agent instructions, [rules/](rules/) for canonical Rules, and [skills/](skills/) for canonical Skills. The Skills contract is defined in [docs/architecture/skills.md](docs/architecture/skills.md). The Tools contract is defined in [docs/architecture/tools.md](docs/architecture/tools.md). The Configuration contract is defined in [docs/architecture/configuration.md](docs/architecture/configuration.md).

## Supported Environments

The project aims to remain **vendor-neutral**.

It is intended to support multiple agent environments through adapters, including Claude, Cursor, Codex, Gemini, and other compatible agents.

Adapters are not implemented yet.

## Roadmap

| Phase | Status | Focus |
| --- | --- | --- |
| Agent instructions (`AGENTS.md`, `CLAUDE.md`) | Done | Project principles and agent entrypoint |
| Rules foundation | Done | Canonical Rules + project docs |
| Skills architecture | Done | Skill contract + core and AI Engineering Skills |
| Tool Registry architecture | Done | Catalog, template, evaluation policy, RTK docs |
| Profiles + `.harness/` configuration | Done | Declarative config, schema, syntax validator |
| Runtime `tools/` integrations | Not implemented | Installers, wrappers, adapters for Tools |
| Agent adapters (`.cursor/`, `.claude/`, …) | Not implemented | Provider-specific projection |
| CLI / `harness doctor` / installers | Not implemented | Operational tooling |
| MCP, RTK, RAG, observability runtime integrations | Not implemented | External capability wiring |

## License

See [LICENSE](LICENSE).
