---
name: rtk
description: CLI proxy that filters and compresses command output before it reaches an LLM context
category: token
type: cli
maturity: emerging
license: Apache-2.0
source: https://github.com/rtk-ai/rtk
official_documentation: https://www.rtk-ai.app/docs/
installation: documented
platforms: [linux, macos, windows]
agent_compatibility:
  claude: possible
  cursor: possible
  codex: possible
  gemini: possible
  other: possible
token_impact:
  effect: reduce
  magnitude: high
context_impact:
  magnitude: low
  output_profile: filterable
cost: free-software
security_level: medium
network_required: optional
local_execution: true
status: evaluated
verified_on: 2026-09-07
---

# RTK

## Summary

RTK (**Rust Token Killer**) is an open-source CLI proxy that filters and compresses development-command output before that output reaches an AI assistant’s context window.

It can be invoked explicitly (`rtk <command>`) or installed as an agent hook that rewrites shell commands to RTK equivalents.

## Category

Token Optimization

## Type

`cli`

Secondary description: local utility / CLI proxy. Not an MCP server, hosted model API, or agent framework.

## Problem it solves

AI coding agents often ingest large, noisy shell output (test runners, git, package managers, directory listings). Much of that text is boilerplate, progress bars, or repetitive success lines. That volume:

- Consumes context window space
- Increases input-token cost for affected turns
- Can obscure the few lines that matter

RTK addresses **bash/command output noise**, not the entire bill. Official docs state that bash output is only one contributor to input tokens, and input tokens are only part of total cost.

## How it works

Verified from official README and docs:

1. A command runs through RTK (directly or via a PreToolUse / equivalent hook rewrite such as `git status` → `rtk git status`).
2. RTK applies per-command strategies: smart filtering, grouping, truncation, and deduplication.
3. The agent receives compact output instead of the full raw stream.
4. On failure, a tee mode can save full raw output locally and print a path so the agent can read detail without re-running the command (default tee mode: failures).

Official docs also state RTK reports token estimates as roughly `bytes / 4` (no bundled tokenizer): **percentages of bash-output reduction are treated as more reliable than absolute token counts**.

## When to use

- Agent sessions that frequently run verbose shell tools (git, tests, package managers, linters, containers)
- Context pressure driven by command output rather than by missing source files
- Teams that want local, no-API-key filtering of CLI noise
- Environments where official agent hooks are available and acceptable

## When not to use

- Tasks that need full unmodified command transcripts (forensic logs, exact progress output, teaching raw CLI UX)
- Workflows that already use narrow, low-noise commands and do not benefit from another layer
- Situations where filtering might hide required signal and no recovery path (tee/raw read) is acceptable
- As a substitute for good context selection (loading fewer files still matters)
- When install/hook complexity is not justified for short or one-off sessions

## Capabilities

Verified from official documentation (non-exhaustive):

- Compact wrappers for many common commands (git, test runners, linters, docker/kubectl, package managers, and others)
- Auto-rewrite hooks for multiple AI coding tools
- Savings analytics: `rtk gain`, `rtk discover`, `rtk session`
- Configurable excludes, tee recovery, and optional custom filters (custom filters require explicit trust)
- Local execution as a single Rust binary

Not verified by this harness:

- Exact count of supported commands at a given release (upstream claims “100+”; treat as upstream claim)
- End-to-end savings on this repository’s workloads

## Installation

Verified install paths from official README / INSTALL guidance:

### Homebrew

```bash
brew install rtk
```

### Quick install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

Official docs note install to `~/.local/bin` and PATH setup may be required.

### Cargo

```bash
cargo install --git https://github.com/rtk-ai/rtk
```

### Pre-built binaries

Download from [GitHub Releases](https://github.com/rtk-ai/rtk/releases) for macOS, Linux, and Windows archives.

### Name collision warning

Another project named “rtk” (Rust Type Kit) exists. Official guidance: verify with `rtk gain` (savings dashboard). If `rtk gain` fails after install, the wrong package may be present. Prefer the explicit Git URL above rather than assuming `cargo install rtk` from crates.io is correct.

### Verify

```bash
rtk --version
rtk gain
```

This harness has **not** installed RTK as part of documenting it. Runtime install success on every platform: `Not verified` here.

## Configuration

Official config locations:

| Platform | Path |
| --- | --- |
| Linux | `~/.config/rtk/config.toml` |
| macOS | `~/Library/Application Support/rtk/config.toml` |
| Windows | `Not verified` in the configuration page checked; Windows binary/hook support is documented in the README |

Documented areas include tracking, display, filters/ignore patterns, tee, telemetry, and hook exclude lists.

Useful environment variables (official):

| Variable | Purpose |
| --- | --- |
| `RTK_DISABLED=1` | Disable RTK for a single command |
| `RTK_TELEMETRY_DISABLED=1` | Block telemetry regardless of consent |
| `RTK_TEE_DIR` | Override tee directory |
| `RTK_HOOK_AUDIT=1` | Enable hook audit logging |

Agent hook setup examples from official README:

```bash
rtk init -g                     # Claude Code / Copilot (default)
rtk init -g --agent cursor      # Cursor
rtk init -g --codex             # Codex
rtk init -g --gemini            # Gemini CLI
```

Uninstall (official):

```bash
rtk init -g --uninstall
```

Plus package uninstall via `cargo uninstall rtk` or `brew uninstall rtk` when those install methods were used.

## Usage

Explicit proxy examples from official docs:

```bash
rtk git status
rtk git diff
rtk pytest
rtk cargo test
rtk ls .
rtk gain
```

With hooks configured, agents may keep writing ordinary commands; RTK rewrites supported shell tool calls.

Important upstream limitation: hooks that only intercept Bash/shell tool calls do **not** automatically wrap built-in agent tools such as dedicated Read/Grep/Glob APIs. For those workflows, use shell equivalents or explicit `rtk read` / `rtk grep` / `rtk find` when desired.

## Agent compatibility

Compatibility below reflects **upstream documentation claims**, not harness-controlled verification.

| Agent | Compatibility | Notes |
| --- | --- | --- |
| Claude (Claude Code) | `possible` | Official: `rtk init -g` installs PreToolUse hook (native binary). Bash-tool scope limitation applies. Harness-local verification: Not verified. |
| Cursor | `possible` | Official: `rtk init -g --agent cursor` via `hooks.json` preToolUse. Harness-local verification: Not verified. |
| Codex | `possible` | Official: `rtk init -g --codex` using AGENTS.md + RTK.md instructions (instruction-based, not the same as a native PreToolUse binary hook). Harness-local verification: Not verified. |
| Gemini (Gemini CLI) | `possible` | Official: `rtk init -g --gemini` BeforeTool hook. Harness-local verification: Not verified. |
| Other agents | `possible` | Upstream documents additional tools (Copilot, Windsurf, Cline/Roo, OpenCode, Hermes, and others). Treat each as separately evidenced. Harness-local verification: Not verified. |

## Token / Context impact

- Token effect: `reduce`
- Token magnitude: `high` for workloads dominated by verbose command output (directional classification based on upstream design; not a harness-measured guarantee)
- Context magnitude: `low` relative to unfiltered command dumps when filters apply
- Output profile: `filterable` (also typically `small`/`moderate` after filtering; unfiltered passthrough remains possible)

### Mechanism

Savings occur by shrinking **command stdout/stderr** before the agent reads it. Strategies include filtering noise, grouping, truncation, and deduplication.

### Official benchmark / claims

Upstream marketing and docs claim large reductions in bash output (commonly cited band around 60–90% fewer bash output bytes for supported commands). Official docs explicitly warn:

- This is **not** the same as reducing the total API bill by the same percentage.
- Reported token counts are **estimates**.

Harness-observed savings on this repository: `Not verified` (RTK was not executed here for measurement).

### Limitations on savings

- Unsupported commands may pass through unchanged.
- Built-in non-shell agent tools may bypass hooks.
- Over-filtering can remove needed detail (mitigated by tee/raw recovery when enabled).

## Performance impact

Upstream README claims low overhead (example claim: `<10ms`). 

Harness measurement: `Not verified`.

## Cost

- Software cost: Open-source under Apache License 2.0; no API key required for core CLI use (official).
- Infrastructure cost: Local CPU/disk only for core filtering; optional telemetry network ping if opted in.
- API / model cost: Indirect savings possible when less command output enters billed input tokens; magnitude workload-dependent; not priced by RTK.
- Operational cost: Hook/config maintenance; local SQLite history/tee storage.
- Commercial offerings: Upstream mentions RTK Pro / cloud products for teams. Pricing: `Not verified` in this evaluation (not required for core OSS CLI docs).

Do not invent dollar savings.

## Security considerations

Assigned harness `security_level`: **medium**

Reasons:

- **Execution:** Runs as a local CLI and can wrap arbitrary shell commands; hooks rewrite agent shell invocations.
- **Filesystem:** Reads command output; may write tee logs and local history DB under user data directories.
- **Network:** Core filtering is local. Optional telemetry uses HTTPS when explicitly enabled. Some wrapped commands (for example `curl`) may use network themselves; that is the wrapped tool’s behavior.
- **Credentials:** Official telemetry docs state secrets/env values are not collected in telemetry. RTK does not remove the need for normal secret hygiene in command output that still reaches the model.
- **Persistence:** Local history and tee files can retain operational output; configure retention/tee mode deliberately.
- **Supply chain:** Install via Homebrew, curl script, Cargo git, or release binaries — each carries normal binary/script trust considerations. Prefer verifying checksums/releases when possible. `Not verified`: harness did not audit the install script contents line-by-line in this pass.
- **Custom filters:** Upstream requires explicit trust because filters change what an agent sees.

Not a low-risk Tool: broad command proxying and agent hooks raise the bar above read-only utilities.

## Privacy considerations

Official telemetry policy (verified from docs):

- Telemetry **disabled by default**
- Requires explicit opt-in (`rtk init` consent or `rtk telemetry enable`)
- Anonymous aggregate daily ping when enabled
- Docs list collected fields (device hash, version, OS, command-name aggregates, savings metrics, etc.)
- Docs state source code, full command lines/args, file paths, secrets, and repo contents are **not** collected
- Opt out: `rtk telemetry disable`, `rtk telemetry forget`, or `RTK_TELEMETRY_DISABLED=1`

Local history DB path is documented by upstream (example Linux-style path `~/.local/share/rtk/history.db`). Exact Windows paths beyond README binary guidance: partially documented; treat path details as platform-specific.

## Limitations

- Reduces bash/command output, not all token consumers (system prompt, chat history, file reads via non-shell tools).
- Hook coverage depends on agent integration method and tool surface.
- Filtering can drop signal; failure recovery depends on tee/settings.
- Name collision with unrelated `rtk` packages creates install footguns.
- Absolute token numbers from `rtk gain` are estimates.
- Harness has not runtime-verified install, hooks, or savings.

## Alternatives

None evaluated in this harness yet.

Manual alternatives that already exist without a new dependency:

- Narrower CLI flags and scoped paths
- Head/tail/rg filtering by hand
- Preferring structured or quieter commands

Those are techniques, not cataloged Tools.

## Related Rules

- `rules/core/tool-usage.md`
- `rules/context/context-budget.md`
- `rules/context/context-selection.md`
- `rules/production/cost.md`
- `rules/security/permissions.md`
- `rules/security/sandboxing.md`

## Related Skills

- `skills/ai-engineering/token-optimization/SKILL.md`
- `skills/core/context-engineering/SKILL.md`
- `skills/core/research/SKILL.md`

## References

- Website: https://www.rtk-ai.app/
- Docs: https://www.rtk-ai.app/docs/
- Telemetry & Privacy: https://www.rtk-ai.app/docs/resources/telemetry/
- Configuration: https://www.rtk-ai.app/docs/getting-started/configuration/
- Repository: https://github.com/rtk-ai/rtk
- License: Apache License 2.0 ([LICENSE](https://github.com/rtk-ai/rtk/blob/HEAD/LICENSE))
- Verification date: `2026-09-07`
