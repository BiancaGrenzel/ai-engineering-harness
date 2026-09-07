# Tool Health

Read-only runtime observation of whether a previously detected Tool responds to
a safe, declarative local probe.

This document describes the second Tool System runtime layer:

```text
tools/registry.yaml
        ↓
  Tool Resolution
        ↓
  Tool Detection
        ↓
  DetectionResult
        ↓
  Tool Health
        ↓
  HealthResult
```

Health does not install, configure, authorize, or expose Tools to agents.

## Purpose

Health answers: **can this detected Tool be established as minimally operational
through a safe local probe?**

That is distinct from Detection, which answers whether a candidate installation
exists.

## Detection vs Health

| Concern | Question |
| --- | --- |
| Detection | Is a candidate executable present and probeable? |
| Health | Does the detected Tool respond to its declared minimal probe? |

`detected != healthy`. Presence of a binary is not a functional guarantee.
Health therefore consumes a `DetectionResult` and does not reimplement PATH
lookup, platform taxonomy, or version discovery.

| Layer | Responsibility |
| --- | --- |
| Detection | `installed?` / `executable?` / `version?` / `compatible?` |
| Health | `operational?` / `responsive?` / `minimally functional?` |

If Detection reports that the Tool is not detected, Health returns
`unavailable` and does not start a process.

## Lifecycle composition

Preferred composition:

```text
resolve
   ↓
detect
   ↓
health
```

Health is not a second Detection implementation. It uses:

- Registry `health` metadata for the probe contract
- `DetectionResult.path` as the resolved executable
- Checker-owned timeout and `shell=False` execution

## Health contract

Public API in `harness.tools`:

- `ToolHealthChecker.check(tool, detection)` — observation only
- `HealthResult` / `HealthStatus` — transient runtime state
- `validate_health_contract` — contract validation before execution
- `format_health_cli_report` — human presentation helper for the CLI

### HealthResult

| Field | Purpose |
| --- | --- |
| `tool_id` | Stable Tool identifier |
| `healthy` | `true` only when status is `healthy` |
| `status` | Structured outcome enum |
| `reason` | Human-readable explanation when useful |
| `duration_ms` | Probe wall time when a process ran, otherwise check duration |
| `exit_code` | Probe exit code when a process completed |
| `detection_status` | Echo of the Detection status used as input |

### Status values

| Status | Meaning |
| --- | --- |
| `healthy` | Declared probe completed with exit code 0 |
| `unhealthy` | Declared probe completed with non-zero exit code |
| `unavailable` | Tool was not detected, or Detection classified the host as incompatible |
| `unsupported` | No health contract declared, or Tool `kind` is not CLI health |
| `timeout` | Probe exceeded the checker timeout |
| `error` | Invalid or unsafe metadata, or process launch failure |

Status is an enum (`HealthStatus`), not free-form strings.

These statuses intentionally avoid duplicating Detection outcomes such as
`not-found` or `version-unavailable`. Absence is expressed as Health
`unavailable` with `detection_status` preserved for composition.

## Registry contract

Health metadata is optional, declarative, and extremely restricted.

Example:

```yaml
health:
  kind: cli
  arguments: [--version]
```

### Why Health does not reuse `detection.version_arguments`

Version detection and health checking are different concerns:

- `version_arguments` exist to observe identity/version during Detection
- Health asks whether the Tool is responsive enough to use
- A Tool may later declare a dedicated liveness flag that is not its version flag
- Silent reuse would couple the two contracts and hide that distinction

Therefore the Registry uses a separate optional `health` block. Health never
falls back to `version_arguments` automatically.

### What is forbidden

The Registry must not become an executable language. Health metadata must not
contain:

- arbitrary shell command strings
- pipelines, redirects, or shell metacharacters
- `shell: true`
- scripts, Python, JavaScript, `eval`, or `exec`
- package-manager commands
- environment mutation
- install / update instructions

Only structured fields validated by
[`schemas/tool-registry.schema.json`](../../schemas/tool-registry.schema.json)
are accepted. Runtime validation re-checks the contract before any process
starts.

## Safe execution

Health probing uses the same narrow execution guarantees as Detection:

- Always `shell=False`
- Always argv list form: `[detection.path, *health.arguments]`
- Never a shell string
- Never pipes, redirects, `&&`, `||`, subshells, or eval
- Explicit checker-owned timeout
- No filesystem writes by the Health Checker
- No PATH mutation
- No installation
- No persistence of results

If metadata cannot be executed safely, the checker refuses the probe and returns
`status=error`.

## Minimal probe

The Health Checker uses the smallest declared probe.

It must not:

- modify the system
- create files
- connect to external targets
- scan networks
- alter configuration
- run destructive operations

If no safe declarative probe is declared for a Tool, Health returns
`unsupported`. That is preferred over inventing behavior.

A successful probe is a **runtime observation**, not proof of full product
capability. For example, exit code 0 on `--version` shows process liveness; it
does not prove that a token-reduction wrapper filters correctly.

## Security model

Keep these concepts separate:

| Concept | Question |
| --- | --- |
| Detection | Can I find this Tool? |
| Health | Can I safely establish that this Tool is operational? |
| Risk (`baseline_risk`) | What is the catalog-level baseline impact of this Tool? |
| Authorization | Am I allowed to use this Tool in this context? |

Health must not:

- raise or lower `security.baseline_risk`
- authorize a Tool
- determine target scope
- decide whether an operation is permitted
- install a Tool
- alter the Registry

## Relation to baseline risk and effective risk

`security.baseline_risk` remains catalog metadata.

Health may contribute future runtime observations, but this phase does **not**
compute `effective_risk`. Healthy does not mean safe, authorized, or low risk.

## Timeout

Health uses a small checker-owned timeout (`HEALTH_CHECK_TIMEOUT_SECONDS`,
currently 3 seconds). The timeout is not configured in the Registry so catalog
data cannot disable hang protection.

## Runtime observation

`HealthResult` is ephemeral. Automatic persistence would blur:

- project intent (`.harness/harness.yaml`)
- catalog truth (`tools/registry.yaml`)
- transient observation (local process behavior)

Health therefore writes nothing: no cache file, no database, and no Registry
mutation.

## CLI

```bash
python -m harness tools health <tool-id>
```

The CLI remains thin:

1. Locate the project
2. Resolve the Tool
3. Detect
4. Health-check
5. Present the result
6. Return exit code `0` when healthy, otherwise `1`

Example output:

```text
Tool Health

  RTK

  Detection: detected
  Health: healthy
  Version: rtk 0.9.0
  Duration: 42ms
```

## Limitations

- Only `kind: cli` Tools with a declared `health` block are supported
- Probe arguments are simple flags only
- No remote health checks
- No network probes
- No MCP / API / service health
- No effective-risk engine
- No authorization engine
- Minimal liveness is not full functional verification

## Out of scope

- Installer / package manager
- MCP runtime
- Tool auto-update
- Effective risk
- Provenance verification
- Trust engine
- Persistent runtime cache
- Target scanning

## Related documents

- [`tool-detection.md`](tool-detection.md)
- [`tools.md`](tools.md)
- [`adr/0001-tool-system-architecture.md`](adr/0001-tool-system-architecture.md)
- [`../tools/README.md`](../tools/README.md)
- [`cli.md`](cli.md)
