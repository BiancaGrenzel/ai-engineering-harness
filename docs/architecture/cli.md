# Harness CLI Architecture

Official standard for the AI Engineering Harness command-line interface.

The CLI is a **thin interface**. It exposes existing Harness capabilities; it does not own configuration semantics, adapter rendering, or conflict policy.

## Purpose

Provide a small, predictable entrypoint for:

- Validating project Harness configuration
- Generating agent-specific files through adapters
- Inspecting Tool Detection and Health for Registry Tools

It is not a runtime, package manager, plugin host, or orchestration framework.

## CLI × Harness Core

```text
harness CLI
     │
     ▼
Existing Harness APIs
  (config validation, project discovery)
```

| Concern | Owner |
| --- | --- |
| Schema validation of `harness.yaml` | Shared validator (`harness.config_validation`, also used by `scripts/validate-config.py`) |
| Profile merge / resource resolution | Adapters via `adapters/common/resolve.py` |
| Project selection of Profile / lists | `.harness/harness.yaml` |

The CLI does not redefine merge rules, schemas, or canonical resource layouts.

## CLI × Adapters

```text
harness generate <adapter>
     │
     ▼
Adapter dispatcher (static map)
     │
     ▼
Existing adapter generator (e.g. Cursor)
     │
     ├─ resolve
     ├─ plan / render
     ├─ preflight
     └─ apply
```

The CLI must not know details of:

- `.mdc` formatting
- Rule / Skill wrapper content
- Managed manifests
- Conflict markers
- Adapter-specific output paths

Those belong to each adapter and to `adapters/common/`.

## Commands (current)

| Command | Behavior |
| --- | --- |
| `harness validate` | Discover project root; validate `.harness/harness.yaml` against `schemas/harness.schema.json` (syntax only) |
| `harness generate cursor` | Dispatch to the Cursor adapter generator |
| `harness generate claude` | Dispatch to the Claude adapter generator |
| `harness tools health <tool>` | Resolve, detect, and health-check one Tool from `tools/registry.yaml` |
| `harness version` | Print **Harness** CLI/package version |

Not implemented (do not document as available):

- `init`, `doctor`, `analyze`, `skills`, `rules`, `profile`, `install`, `adapters`, `config`, `runtime`

### Installation

Distribution name: `ai-engineering-harness`. Import package: `harness`.

```bash
pip install .
```

This installs the engine locally. PyPI publishing and release automation are future work.

Console script entrypoint (declared in `pyproject.toml`):

```text
harness = harness.cli:main
```

### Installed invocation

After `pip install .` (or an equivalent local install), use the console script from any directory:

```bash
harness validate
harness generate cursor
harness generate cursor --dry-run
harness generate claude
harness generate claude --dry-run
harness tools health rtk
harness version
```

No `PYTHONPATH` and no repository checkout on `sys.path` are required for the installed CLI.

### Development invocation

Preferred during repository development (same `main()` as the console script):

```bash
# from the repository root (directory that contains the harness/ package)
python -m harness validate
python -m harness generate cursor
python -m harness generate cursor --dry-run
python -m harness generate claude
python -m harness generate claude --dry-run
python -m harness tools health rtk
python -m harness version
```

When the current working directory is a subdirectory, Python may not resolve the
`harness` package via `-m` unless the package is installed (editable or regular)
or the repository root is on `PYTHONPATH`. Project discovery (walking up for
`.harness/harness.yaml`) already supports subdirectory cwd once the package
imports.

In this repository, `python scripts/harness …` bootstraps `sys.path` so the
CLI can be invoked without setting `PYTHONPATH` during local development.

### Flags

| Flag | Commands | Meaning |
| --- | --- | --- |
| `--root PATH` | `validate`, `generate <adapter>`, `tools health` | Explicit project root; skips upward discovery |
| `--dry-run` | `generate cursor`, `generate claude` | Passed through to the adapter; no file writes |

## Exit codes

Minimal policy:

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Expected failure (missing config, invalid config, unknown adapter, adapter conflict / failure) |

Dependency install problems from the shared validator may still exit `2` (same as `scripts/validate-config.py`). Unexpected programming errors may print a traceback during development; expected user errors must not.

## Project root discovery

When `--root` is omitted:

1. Start at the current working directory
2. Walk upward looking for `.harness/harness.yaml`
3. Stop at the filesystem root

If none is found:

```text
Harness configuration not found.
```

Exit code `1`.

With `--root PATH`, that directory must contain `.harness/harness.yaml`; otherwise the same not-found message and exit code apply.

The current working directory is never treated as the project root merely because it is cwd; discovery always requires `.harness/harness.yaml` (or an explicit `--root` that contains it).

## Installed engine vs project resources

`pip install ai-engineering-harness` (or `pip install .`) installs the **engine**, not a global copy of Profiles / Rules / Skills.

### Installed with the package (engine)

| Resource | Role |
| --- | --- |
| `harness/` | CLI, project discovery, config validation helpers, Tool Detection / Health |
| `adapters/` | Cursor and Claude generators plus `adapters/common/` |
| `adapters/*/adapter.yaml` | Adapter capability metadata (package data) |
| Runtime deps | `PyYAML`, `jsonschema` |

### Expected in a Harness-enabled project

| Resource | Role |
| --- | --- |
| `.harness/harness.yaml` | Project selection (required for discovery) |
| `profiles/` | Profile defaults selected by config |
| `rules/` | Canonical Rules referenced by Profile / config |
| `skills/` | Canonical Skills referenced by Profile / config |
| `tools/registry.yaml` | Tool Registry when Tools are used |
| `docs/tools/` | Human Tool docs referenced by the Registry |
| `schemas/` | JSON Schemas used by validate / resolve (`harness.schema.json`, `profile.schema.json`, `tool-registry.schema.json`) |

After installation, the CLI may run from an arbitrary working directory. It discovers the nearest ancestor with `.harness/harness.yaml` and resolves Profiles, Rules, Skills, Tools, and schemas **relative to that project root**. It does not invent a repository-root location from the installed package.

**Limitation:** this packaging phase does not ship canonical Profiles / Rules / Skills / schemas as engine-owned defaults. A project outside this repository must supply those resources itself (or obtain them through a future bootstrap / distribution mechanism such as `harness init`). Packaging them into the wheel as global mutable content was intentionally avoided.

## Adapter dispatch

Adapters are registered in a **static** map (`harness.dispatch.ADAPTERS`).

- Extensible by adding a new entry when an adapter exists
- No plugin discovery
- No dynamic package loading
- No remote registry

Unknown names:

```text
Unknown or unsupported adapter: <name>
```

Exit code `1`.

## Version semantics

| Version | Meaning |
| --- | --- |
| Harness version (`harness version`) | CLI / `harness` package version (`harness.__version__`, also the distribution version) |
| Adapter version | Implementation version in that adapter's `adapter.yaml` |
| Tool version | External tool releases (catalog / ecosystem) |
| Project `version` in `harness.yaml` | Configuration format version |

Do not conflate these.

## Output

Generation output is owned by the adapter (Created / Updated / Unchanged / Conflicts / Warnings / Errors). The CLI presents that output without a second formatting system.

Validate success / failure messages match the shared validator:

- `Harness configuration is valid.`
- `Harness configuration is invalid.` plus error details

`tools health` presents Detection and Health observations using
`format_health_cli_report` from `harness.tools`. Exit code `0` means healthy;
exit code `1` covers unhealthy, unavailable, unsupported, timeout, error, missing
Tool, or missing project/registry.

## Extensibility (future)

Logical next steps (not implemented here):

- Project scaffolding (`harness init`) so a Harness-enabled tree can be created outside this repository
- Optional packaging of read-only schema defaults if product policy prefers engine-shipped schemas
- PyPI publishing / release automation
- Additional `generate <adapter>` entries when new adapters land
- Further commands only when they wrap real Harness capabilities

Prefer keeping the CLI thin. New behavior should land in core/adapters first, then be exposed by the CLI.

## Related

- Configuration: [`configuration.md`](configuration.md)
- Adapters: [`adapters.md`](adapters.md)
- Tool Detection: [`tool-detection.md`](tool-detection.md)
- Tool Health: [`tool-health.md`](tool-health.md)
- Cursor adapter: [`../../adapters/cursor/README.md`](../../adapters/cursor/README.md)
- Claude adapter: [`../../adapters/claude/README.md`](../../adapters/claude/README.md)
- Package: [`../../harness/`](../../harness/)
- Packaging metadata: [`../../pyproject.toml`](../../pyproject.toml)
