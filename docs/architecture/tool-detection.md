# Tool Detection

Read-only runtime observation of whether a Registry-declared Tool is available
on the local host.

This document describes the first Tool System runtime layer:

```text
tools/registry.yaml
        ↓
  Tool Resolution
        ↓
  Tool Detection
        ↓
  DetectionResult
```

Detection does not install, configure, authorize, or expose Tools to agents.

## What Tool Detection is

Detection answers: **does a candidate CLI installation exist on this machine?**

For `kind: cli`, the detector:

1. Resolves the Tool definition from the Registry
2. Confirms the kind is supported
3. Validates safe detection metadata
4. Compares the host OS/architecture with declared `platforms`
5. Locates the declared executable basename via PATH lookup (`shutil.which`)
6. Runs only the declared version flags as a structured argv list
7. Returns a structured `DetectionResult`

The public API lives in `harness.tools`:

- `load_tool_registry` / `resolve_tool` — data lookup only
- `ToolDetector.detect` — observation only
- `DetectionResult` / `DetectionStatus` — transient runtime state

## Detection vs Health

| Concern | Question |
| --- | --- |
| Detection | Is a candidate executable present and probeable? |
| Health | Does the Tool function minimally under a safe check? |

`detected != healthy`. Presence of a binary is not a functional guarantee.
Health checking is a separate runtime layer documented in
[`tool-health.md`](tool-health.md). Detection produces a `DetectionResult` that
Health may consume; Detection does not infer health.

## Detection vs Installation

Detection never installs, upgrades, removes, or downloads Tools. It never
modifies PATH, package state, or user configuration. If a Tool is absent, the
result is `not-found` (or `incompatible` when the host is unsupported).

## Detection vs Compatibility

`detected` and `compatible` are independent:

- `detected=true` means an executable was found on PATH
- `compatible=false` means the host OS/architecture is outside Registry
  `platforms`

A Tool can be found on an unsupported platform. Discovery is still reported;
compatibility is not hidden.

## Detection vs Runtime Risk

Detection does **not** compute effective risk and does **not** modify
`security.baseline_risk`. The Registry remains catalog metadata; DetectionResult
is ephemeral observation only.

## DetectionResult

| Field | Purpose |
| --- | --- |
| `tool_id` | Stable Tool identifier |
| `detected` | Whether a candidate executable was found |
| `status` | Structured outcome enum |
| `executable` | Declared basename from Registry |
| `path` | Resolved filesystem path when found |
| `version` | Observed version text, if available |
| `compatible` | Host vs declared platforms |
| `platform` | Observed host OS (Registry taxonomy when known) |
| `architecture` | Observed host architecture |
| `reason` | Human-readable explanation when useful |

### Status values

| Status | Meaning |
| --- | --- |
| `detected` | Executable found; version probe succeeded |
| `not-found` | Compatible host; executable absent from PATH |
| `version-unavailable` | Executable found; version probe failed or empty |
| `incompatible` | Host outside declared platforms (discovery still reported when found) |
| `unsupported` | Tool `kind` is not CLI detection |
| `timeout` | Version probe exceeded the detector timeout |
| `error` | Invalid metadata, unsafe contract, or execution failure |

Status is an enum (`DetectionStatus`), not free-form strings.

## Security of execution

Version probing is intentionally narrow:

- Always `shell=False`
- Always argv list form: `[resolved_executable, *version_arguments]`
- Never a shell string such as `"rtk --version"`
- Never pipes, redirects, `&&`, `||`, subshells, or eval
- Never user-supplied command strings as the execution surface
- Executable must be a basename matching the Registry contract
- `version_arguments` must be simple flags only

The Registry is **data**. Detection re-validates that data before any process
starts. A malicious or malformed entry that tries to smuggle shell syntax is
rejected with `status=error` and no process is launched.

Forbidden interpreter-style flags such as `-c`, `-e`, and `-Command` are
rejected even though a future schema tightening may also exclude them. The goal
is a restricted contract, not a full shell parser.

## Why the Registry cannot contain arbitrary commands

If the Registry could store free-form command lines, validation and detection
would become an arbitrary code execution surface. The harness therefore allows
only:

- a basename executable
- a list of simple version flags

Package-manager commands, install scripts, and adapter logic remain outside the
Registry.

## Why Detection does not persist state

`DetectionResult` is runtime state. Automatic persistence would blur:

- project intent (`.harness/harness.yaml`)
- catalog truth (`tools/registry.yaml`)
- transient observation (local PATH and versions)

Detection therefore writes nothing: no cache file, no database, and no Registry
mutation. Callers may present results later; persistence is an explicit future
decision, not a side effect of probing.

## Timeout

Version detection uses a small detector-owned timeout
(`VERSION_DETECTION_TIMEOUT_SECONDS`, currently 3 seconds). The timeout is not
configured in the Registry so catalog data cannot disable hang protection.

## Unsupported kinds

For `mcp-server`, `api`, `library`, and `service`, detection returns
`status=unsupported` without probing.

## Out of scope

- Health probing semantics (see [`tool-health.md`](tool-health.md))
- Installation
- Package managers
- MCP runtime
- Adapter wiring
- Effective risk / provenance / trust
- Version constraint solvers (`>=`, `^`, `~`, …)
- Runtime orchestration or caching

## Related documents

- [`adr/0001-tool-system-architecture.md`](adr/0001-tool-system-architecture.md)
- [`tool-health.md`](tool-health.md)
- [`tools.md`](tools.md)
- [`../tools/README.md`](../tools/README.md)
