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
docs/        # documentation (includes human Tool catalog docs)
profiles/    # role-specific compositions
.harness/    # project harness configuration
schemas/     # JSON Schemas for configuration
scripts/     # small development utilities
adapters/    # agent compatibility layer (Cursor first)
harness/     # thin CLI (validate, generate, tools health)
tools/       # Tool Registry (+ planned installers/wrappers)
```

Provider-specific output (for example `.cursor/`) is produced by adapters. Canonical resources stay vendor-neutral.

### Rules, Skills, Tools, Profiles, Configuration

| Layer | Role |
| --- | --- |
| **Rules** | Persistent agent behavior |
| **Skills** | Specialized procedures |
| **Tools** | External capabilities (CLI, MCP, services, utilities, …) |
| **Profiles** | Reusable default compositions of Rules, Skills, and Tools |
| **Configuration** | Project selection of a Profile and optional overrides (`.harness/harness.yaml`) |

The **Tool Registry** (`tools/registry.yaml`) is the machine-readable catalog of Tool identity and operational metadata. Human documentation lives in [`docs/tools/`](docs/tools/). Read-only Tool Detection and Health are implemented in the CLI (`harness tools health`). Installers and runtime wrappers under `tools/` are not implemented yet.

## Configuration

Project configuration is declarative and lives in [`.harness/harness.yaml`](.harness/harness.yaml).

- Configuration declares desired state (which Profile and resource lists apply)
- Profiles compose defaults ([`profiles/`](profiles/))
- Rules define persistent behavior
- Skills define specialized procedures
- Tools provide external capabilities

Contract: [`docs/architecture/configuration.md`](docs/architecture/configuration.md)

Validate configuration:

```bash
pip install -r scripts/requirements.txt
python -m harness validate
# equivalent script:
python scripts/validate-config.py
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## CLI

Thin interface over existing Harness validation and adapters. Architecture: [`docs/architecture/cli.md`](docs/architecture/cli.md).

```bash
python -m harness --help
python -m harness validate
python -m harness generate cursor --dry-run
python -m harness generate cursor
python -m harness tools health rtk
python -m harness version
```

Run `python -m harness` from the project root (or set `PYTHONPATH` to that root). A console-script `harness` entrypoint is not packaged yet; for a path-bootstrapped launcher in this repo: `python scripts/harness validate`.

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

## Adapters

Adapters translate canonical Harness configuration into agent-specific files:

```text
Harness configuration
        ↓
     Adapter
        ↓
Agent-specific configuration
```

`.harness/harness.yaml` remains the source of truth. Adapters must not invert that flow.

| Adapter | Status | Docs |
| --- | --- | --- |
| Cursor | experimental | [`adapters/cursor/`](adapters/cursor/) |

Architecture: [`docs/architecture/adapters.md`](docs/architecture/adapters.md) · Contract: [`adapters/ARCHITECTURE.md`](adapters/ARCHITECTURE.md)

Generate Cursor wrappers:

```bash
python -m harness generate cursor
python -m harness generate cursor --dry-run
# equivalent adapter entrypoint:
python -m adapters.cursor.generate
python -m adapters.cursor.generate --dry-run
```

## Supported Environments

The project aims to remain **vendor-neutral**.

It is intended to support multiple agent environments through adapters, including Claude, Cursor, Codex, Gemini, and other compatible agents.

The Cursor adapter is experimental. Additional agent adapters are not implemented yet.

## Roadmap

| Phase | Status | Focus |
| --- | --- | --- |
| Agent instructions (`AGENTS.md`, `CLAUDE.md`) | Done | Project principles and agent entrypoint |
| Rules foundation | Done | Canonical Rules + project docs |
| Skills architecture | Done | Skill contract + core and AI Engineering Skills |
| Tool Registry architecture | Done | Catalog, template, evaluation policy, RTK docs |
| Profiles + `.harness/` configuration | Done | Declarative config, schema, syntax validator |
| Adapter architecture + Cursor adapter | Done (experimental) | Harness → agent projection |
| Initial CLI (`validate`, `generate cursor`, `tools health`) | Done | Thin interface over existing APIs |
| Tool Registry + Detection + Health | Done | Declarative catalog; read-only local probes |
| Runtime Tool installers / wrappers | Not implemented | Install, configure, or package Tools |
| Additional agent adapters (Claude, Codex, …) | Not implemented | More vendor projections |
| `harness doctor` / more CLI commands | Not implemented | Operational tooling |
| MCP, RTK wiring, RAG, observability runtime | Not implemented | External capability wiring |

## License

See [LICENSE](LICENSE).
