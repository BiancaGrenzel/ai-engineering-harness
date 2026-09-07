# Harness CLI Architecture

Official standard for the AI Engineering Harness command-line interface.

The CLI is a **thin interface**. It exposes existing Harness capabilities; it does not own configuration semantics, adapter rendering, or conflict policy.

## Purpose

Provide a small, predictable entrypoint for:

- Validating project Harness configuration
- Generating agent-specific files through adapters

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
| `harness version` | Print **Harness** CLI/package version |

Not implemented (do not document as available):

- `init`, `doctor`, `analyze`, `tools`, `skills`, `rules`, `profile`, `install`, `adapters`, `config`, `runtime`

### Invocation

Preferred entrypoint (no packaging / publishing in this phase):

```bash
# from the project root (directory that contains the harness/ package)
python -m harness validate
python -m harness generate cursor
python -m harness generate cursor --dry-run
python -m harness version
```

When the current working directory is a subdirectory, Python may not resolve the
`harness` package via `-m`. Either:

- run from the project root, or
- set `PYTHONPATH` to the project root (the directory that contains `harness/`), or
- use an explicit root: `python -m harness validate --root /path/to/project` (still requires the package to be importable)

A standalone `harness` console-script entrypoint is deferred until a minimal
packaging setup is introduced. Config discovery (walking up for
`.harness/harness.yaml`) already supports subdirectory cwd once the package
imports.

In this repository, `python scripts/harness …` bootstraps `sys.path` so the
CLI can be invoked without setting `PYTHONPATH`.

### Flags

| Flag | Commands | Meaning |
| --- | --- | --- |
| `--root PATH` | `validate`, `generate <adapter>` | Explicit project root; skips upward discovery |
| `--dry-run` | `generate cursor` | Passed through to the adapter; no file writes |

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
| Harness version (`harness version`) | CLI / `harness` package version |
| Adapter version | Implementation version in that adapter's `adapter.yaml` |
| Tool version | External tool releases (catalog / ecosystem) |
| Project `version` in `harness.yaml` | Configuration format version |

Do not conflate these.

## Output

Generation output is owned by the adapter (Created / Updated / Unchanged / Conflicts / Warnings / Errors). The CLI presents that output without a second formatting system.

Validate success / failure messages match the shared validator:

- `Harness configuration is valid.`
- `Harness configuration is invalid.` plus error details

## Extensibility (future)

Logical next steps (not implemented here):

- Additional `generate <adapter>` entries when new adapters land
- Optional packaging entrypoint for a `harness` binary
- Further commands only when they wrap real Harness capabilities

Prefer keeping the CLI thin. New behavior should land in core/adapters first, then be exposed by the CLI.

## Related

- Configuration: [`configuration.md`](configuration.md)
- Adapters: [`adapters.md`](adapters.md)
- Cursor adapter: [`../../adapters/cursor/README.md`](../../adapters/cursor/README.md)
- Package: [`../../harness/`](../../harness/)
