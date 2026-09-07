# Harness CLI Architecture

Official standard for the AI Engineering Harness command-line interface.

The CLI is a **thin interface**. It exposes existing Harness capabilities; it does not own configuration semantics, adapter rendering, or conflict policy.

## Purpose

Provide a small, predictable entrypoint for:

- Initializing project intent (`.harness/harness.yaml`)
- Validating project intent against the content pack
- Generating self-contained agent projections through adapters
- Inspecting Tool Detection and Health for Registry Tools

It is not a runtime, package manager, plugin host, or orchestration framework.

## CLI × Harness Core

```text
harness CLI
     │
     ▼
Existing Harness APIs
  (content pack, config validation, project discovery)
```

| Concern | Owner |
| --- | --- |
| Schema validation of `harness.yaml` | Shared validator (`harness.config_validation`, also used by `scripts/validate-config.py`) |
| Canonical Profiles / Rules / Skills / Schemas / Tools | Content pack (`harness.content.pack`) |
| Profile merge / resource resolution | Adapters via `adapters/common/resolve.py` (pack-aware) |
| Project selection of Profile / lists | `.harness/harness.yaml` (project intent) |

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
     ├─ resolve (project intent + content pack)
     ├─ plan / render (self-contained projection)
     ├─ preflight
     └─ apply
```

The CLI must not know details of:

- `.mdc` formatting
- Rule / Skill projection content
- Managed manifests
- Conflict markers
- Adapter-specific output paths

Those belong to each adapter and to `adapters/common/`.

## Commands (current)

| Command | Behavior |
| --- | --- |
| `harness init` | Create project intent only (`.harness/harness.yaml`) |
| `harness validate` | Discover project root; validate intent against content-pack schemas; resolve selected Profile / Rules / Skills / Tools; validate packaged Registry |
| `harness generate cursor` | Dispatch to the Cursor adapter generator |
| `harness generate claude` | Dispatch to the Claude adapter generator |
| `harness tools health <tool>` | Resolve from the content-pack Registry, detect, and health-check one Tool |
| `harness version` | Print **Harness** CLI/package version |

Not implemented (do not document as available):

- `doctor`, `analyze`, `skills`, `rules`, `profile use`, remote profiles, `install`, `adapters`, `config`, `runtime`, content export

### Installation

Distribution name: `ai-engineering-harness`. Import package: `harness`.

```bash
pip install .
```

This installs the **Installed Engine** locally, including a read-only content pack. PyPI publishing and release automation are future work.

Console script entrypoint (declared in `pyproject.toml`):

```text
harness = harness.cli:main
```

### Installed invocation

After `pip install .` (or an equivalent local install), use the console script from any directory:

```bash
harness init --profile software-engineer
harness init --profile software-engineer --dry-run
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
python -m harness init --profile software-engineer --dry-run
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
| `--root PATH` | `init` | Target directory for intent creation (default: cwd; does not walk upward) |
| `--root PATH` | `validate`, `generate <adapter>`, `tools health` | Explicit project root; skips upward discovery |
| `--profile NAME` | `init` | Profile to select; required when stdin is non-interactive |
| `--dry-run` | `init`, `generate cursor`, `generate claude` | Plan only; no file writes |

## Exit codes

Minimal policy:

| Code | Meaning |
| --- | --- |
| `0` | Success (including idempotent init with only unchanged files) |
| `1` | Expected failure (missing config, invalid config, unknown adapter/profile, init/adapter conflict / failure, non-interactive init without `--profile`) |

Dependency install problems from the shared validator may still exit `2` (same as `scripts/validate-config.py`). Unexpected programming errors may print a traceback during development; expected user errors must not.

## Project root discovery

### `harness init`

Init targets an uninitialized (or already initialized) directory:

1. Use `--root PATH` when provided
2. Otherwise use the current working directory
3. Do **not** walk upward looking for an existing `.harness/harness.yaml`

This avoids accidentally writing into a parent Harness project.

### Other commands

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

## Installed Engine vs Project Intent vs Vendor Projection

Keep these layers separate:

```text
Installed Engine
  harness/ + adapters/ + read-only content pack
        │
        │  harness init
        ▼
Project Intent
  .harness/harness.yaml
        │
        │  harness generate <adapter>
        ▼
Generated Vendor Projection (self-contained)
  .cursor/  .claude/  (future adapters)
```

Canonical Profiles, Rules, Skills, Schemas, Tool Registry, and Tool docs are
**not** copied into consumer projects. They remain in the content pack.

### Installed Engine (pip package)

| Resource | Role |
| --- | --- |
| `harness/` | CLI, project discovery, config validation, Tool Detection / Health, content-pack access |
| `adapters/` | Cursor and Claude generators plus `adapters/common/` |
| `adapters/*/adapter.yaml` | Adapter capability metadata (package data) |
| `harness/content/_data` | Read-only content pack (installed distribution) |
| Runtime deps | `PyYAML`, `jsonschema` |

During **source development** of this repository, the same content is authored at
the repository root (`profiles/`, `rules/`, `skills/`, `schemas/`, `tools/`,
`docs/tools/`). The locator prefers the bundled pack when present, otherwise the
authoring repository root.

### Project Intent (after `harness init`)

| Resource | Role |
| --- | --- |
| `.harness/harness.yaml` | Project selection (required for discovery) |

Consumer projects do **not** need:

| Resource | Why absent |
| --- | --- |
| `profiles/` | Owned by the content pack |
| `rules/` | Owned by the content pack; projected into agent config |
| `skills/` | Owned by the content pack; projected into agent config |
| `schemas/` | Owned by the content pack |
| `tools/` | Owned by the content pack |
| `docs/tools/` | Owned by the content pack |

### Generated Vendor Projection

| Resource | Role |
| --- | --- |
| `.cursor/` | Cursor adapter output (`harness generate cursor`) — self-contained |
| `.claude/` | Claude adapter output (`harness generate claude`) — self-contained |

`harness init` does **not** create vendor projections and does not modify
`CLAUDE.md`, `AGENTS.md`, `src/`, or other user project files.

After upgrading the Harness package, regenerate agent projections so they pick up
updated canonical content:

```bash
harness generate cursor
harness generate claude
```

## `harness init` contract

```bash
harness init
harness init --profile software-engineer
harness init --profile software-engineer --dry-run
harness init --root /path/to/project --profile software-engineer
```

Behavior:

1. Resolve target root (`--root` or cwd)
2. Resolve profile (`--profile`, or interactive prompt when stdin is a TTY)
3. Build an intent-only file map (`.harness/harness.yaml`)
4. Classify: create / unchanged / conflict
5. Fail-closed on conflicts (no writes)
6. Write only the missing intent file when the plan is clean

Idempotency: running the same init twice is safe when existing intent is
byte-identical. Divergent `.harness/harness.yaml` is a conflict.

Currently shipped Profile: `software-engineer`. Future Profiles are content
additions inside the pack, not engine features.

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

Init output uses the same create / unchanged / conflict vocabulary for intent
materialization (no silent updates of divergent files).

Validate success / failure messages match the shared validator:

- `Harness configuration is valid.`
- `Harness configuration is invalid.` plus error details

`tools health` presents Detection and Health observations using
`format_health_cli_report` from `harness.tools`. Exit code `0` means healthy;
exit code `1` covers unhealthy, unavailable, unsupported, timeout, error, missing
Tool, or missing project/registry.

## Migration (older consumer projects)

Projects created by the previous `harness init` may contain materialized
`profiles/`, `rules/`, `skills/`, `schemas/`, `tools/`, and `docs/` trees.

- Those trees are **not** deleted automatically
- Resolution and validation prefer the **content pack**, not project-local copies
- Safe migration: keep `.harness/harness.yaml`, regenerate agent projections, then
  optionally remove unused materialized trees by hand after review

## Extensibility (future)

Logical next steps (not implemented here):

- Additional Profiles as content-pack additions
- PyPI publishing / release automation
- Additional `generate <adapter>` entries when new adapters land
- Content version pinning / project overrides / Tool content packs
- Further commands only when they wrap real Harness capabilities

Prefer keeping the CLI thin. New behavior should land in core/adapters/content first, then be exposed by the CLI.

## Related

- Configuration: [`configuration.md`](configuration.md)
- Adapters: [`adapters.md`](adapters.md)
- Tool Detection: [`tool-detection.md`](tool-detection.md)
- Tool Health: [`tool-health.md`](tool-health.md)
- Cursor adapter: [`../../adapters/cursor/README.md`](../../adapters/cursor/README.md)
- Claude adapter: [`../../adapters/claude/README.md`](../../adapters/claude/README.md)
- Package: [`../../harness/`](../../harness/)
- Packaging metadata: [`../../pyproject.toml`](../../pyproject.toml)
