# Tools Architecture

Official standard for documenting and classifying Tools in the AI Engineering Harness.

Canonical operational Tool metadata lives in
[`tools/registry.yaml`](../../tools/registry.yaml). Canonical Tool documentation
lives in [`docs/tools/`](../tools/). This document defines the metadata model,
taxonomies, and evaluation posture. Provider adapters and runtime integrations may
consume the Registry later; they must not become a second source of truth.

Actual installers, wrappers, and integration code (when added later) belong under
the repository `tools/` directory described in [`AGENTS.md`](../../AGENTS.md).
Read-only CLI detection is documented in
[`tool-detection.md`](tool-detection.md); read-only health checking is documented
in [`tool-health.md`](tool-health.md). Both consume Registry metadata and do not
replace this catalog contract.

## What is a Tool?

A Tool is an **external capability** that can increase agent effectiveness or improve an engineering workflow.

Examples of form factors:

- CLI
- Library
- SDK
- MCP server
- External service
- Observability platform
- Evaluation framework
- Context or token optimization utility
- Developer tool
- Agent framework

These form factors are **not interchangeable**. The registry must record the primary type so agents and humans can reason about installation, trust boundaries, and operational cost.

## Rule vs Skill vs Tool

| Resource | Purpose | Example |
| --- | --- | --- |
| Rule | Persistent behavior | Prefer filtered tool output |
| Skill | Specialized procedure | Token optimization workflow |
| Tool | External capability | RTK |
| Profile | Composition | Software engineer profile |

- **Rules** constrain default behavior.
- **Skills** describe how to perform a problem class and may reference Tools.
- **Tools** are external capabilities Skills or agents may invoke.
- **Profiles** compose Rules, Skills, and Tools; project selection lives in `.harness/harness.yaml`. See [`docs/architecture/configuration.md`](configuration.md).

Do not duplicate Tool installation or CLI details inside Skills. Reference Tool docs instead.

## Catalog lifecycle

```text
Candidate
    ↓
Research
    ↓
Evaluate
    ↓
Document
    ↓
Classify
    ↓
Registry
    ↓
Optional Integration
```

See [`docs/tools/evaluation.md`](../tools/evaluation.md) and [`docs/tools/recommendation-policy.md`](../tools/recommendation-policy.md).

Existence in documentation is not a recommendation. Status must be explicit.

## Documentation metadata model

`tools/registry.yaml` is the machine-readable metadata source. The frontmatter
below is documentation metadata for Tool pages, whose body follows
[`docs/tools/TOOL_TEMPLATE.md`](../tools/TOOL_TEMPLATE.md). It must not be treated
as a second operational Registry.

### Format

```yaml
---
name: tool-name
description: Short description of the Tool
category: token
type: cli
maturity: emerging
license: Apache-2.0
source: https://example.com/repo
official_documentation: https://example.com/docs
installation: documented
platforms: [linux, macos, windows]
agent_compatibility:
  claude: possible
  cursor: possible
  codex: possible
  gemini: possible
  other: unknown
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
```

Fields that cannot be confirmed must use `unknown`, `not-verified`, or an explicit prose `Not verified` in the body. Do not invent values.

### Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Stable kebab-case identifier; should match the doc filename stem |
| `description` | Yes | One short sentence for discovery and selection |
| `category` | Yes | Top-level category under `docs/tools/` |
| `type` | Yes | Primary form factor (see Type taxonomy) |
| `maturity` | Yes | Upstream project maturity, not harness preference |
| `license` | Yes when known | Legal reuse and redistribution constraints |
| `source` | Yes when known | Canonical upstream repository or product home |
| `official_documentation` | Yes when known | Authoritative docs URL |
| `installation` | Yes | Whether install steps are documented (`documented`, `not-documented`, `not-applicable`) |
| `platforms` | Yes when known | Environments where upstream claims support |
| `agent_compatibility` | Yes | Per-agent support evidence (see Agent compatibility) |
| `token_impact` | Yes | Effect and magnitude on token consumption |
| `context_impact` | Yes | Effect of Tool output on model context |
| `cost` | Yes | Coarse cost class; never invent prices |
| `security_level` | Yes | Risk classification from defined criteria |
| `network_required` | Yes | Whether network access is required for core use |
| `local_execution` | Yes | Whether primary execution can be local |
| `status` | Yes | Harness recommendation status |
| `verified_on` | Recommended | ISO date of last harness source verification |

### Design decisions

- Keep metadata small and purposeful.
- Prefer fields that help **selection, risk, and context cost** decisions.
- Do not encode vendor-specific activation syntax in metadata.
- Do not add scoring fields until a concrete need appears.
- Body prose carries nuance; metadata carries filterable signals.

## Type taxonomy

Primary `type` values:

| Type | Meaning |
| --- | --- |
| `cli` | Command-line executable |
| `library` | Importable code library |
| `sdk` | Vendor or platform software development kit |
| `mcp-server` | Model Context Protocol server |
| `service` | Externally hosted API or managed service |
| `platform` | Multi-capability hosted product surface |
| `framework` | Opinionated application or agent framework |
| `protocol` | Interoperability protocol (not an implementation) |
| `utility` | Narrow helper that is not best described by the above |

Use only the types that fit. A Tool has one primary `type`. Secondary forms may be noted in prose (for example “CLI with optional MCP wrapper”) without inventing a multi-type schema.

## Maturity taxonomy

| Value | Meaning |
| --- | --- |
| `experimental` | Early, unstable, or rapidly changing |
| `emerging` | Usable, still evolving APIs or ecosystem position |
| `stable` | Suitable for careful production adoption with normal change risk |
| `mature` | Long-lived, well-understood operational expectations |
| `deprecated` | Upstream discourages new adoption |

Maturity is **not** a quality ranking and **not** a harness recommendation. A mature Tool can be a poor fit. An emerging Tool can be the right answer for a narrow problem.

## Status taxonomy

Harness-facing lifecycle status (independent of upstream maturity):

| Value | Meaning |
| --- | --- |
| `candidate` | Proposed; research incomplete |
| `evaluated` | Researched and documented with evidence; not yet a default recommendation |
| `recommended` | Meets recommendation policy for a defined problem class |
| `optional` | Useful in some contexts; not a default |
| `deprecated` | Should not be newly adopted in this harness |

Popular ≠ recommended. See [`docs/tools/recommendation-policy.md`](../tools/recommendation-policy.md).

## Token impact

Token impact has two dimensions so reduction is first-class:

### Effect

| Value | Meaning |
| --- | --- |
| `reduce` | Tends to lower tokens reaching the model or billed usage |
| `increase` | Tends to raise token consumption |
| `neutral` | Negligible intentional effect |
| `variable` | Effect depends on workload or configuration |
| `unknown` | Not established from reliable evidence |

### Magnitude

| Value | Meaning |
| --- | --- |
| `low` | Small effect relative to typical task cost |
| `medium` | Material but not dominant |
| `high` | Dominant factor for affected workloads |
| `variable` | Magnitude swings by usage pattern |
| `unknown` | Not established |

### Mechanisms to consider

A Tool may:

- Consume tokens directly (model or embedding calls)
- Reduce tokens (compression, filtering, caching)
- Produce excessive output that becomes context
- Filter or structure output
- Reduce the need to load context
- Increase context through verbose results
- Save model round-trips

Registry shorthand examples:

- `reduce / high`
- `increase / medium`
- `variable / variable`
- `unknown / unknown`

Do not invent savings percentages. If upstream publishes benchmarks, label them as **Official benchmark** and distinguish from harness-observed results.

## Context impact

Context impact describes how Tool results enter the model window.

### Magnitude

| Value | Meaning |
| --- | --- |
| `low` | Typically small or highly compressed results |
| `medium` | Moderate volume under normal use |
| `high` | Large volume likely without careful scoping |
| `variable` | Depends heavily on inputs or flags |
| `unknown` | Not established |

### Output profile

Record one or more characteristics in prose or metadata:

| Profile | Meaning |
| --- | --- |
| `small` | Compact by design |
| `moderate` | Typical engineering command output size |
| `large` | Often large dumps |
| `filterable` | Supports filtering, truncation, or scoped queries |
| `structured` | Machine-readable or consistently shaped |
| `potentially_unbounded` | Can grow without a hard bound |

Agents should prefer Tools whose output profile matches the current context budget.

## Security classification

The Registry records `security.baseline_risk`: a catalog-level classification of
the Tool's normal documented behavior and potential blast radius. It is not the
effective risk of a particular machine, target, credential set, or execution mode.
Future runtime observations may report effective risk separately; they must not
rewrite Registry metadata. Provenance and trust are future concerns separate from
both access surface and baseline risk. Tool Health may observe local process
liveness, but healthy does not mean low risk, authorized, or safe.

| Level | Criteria (any strong match can raise the level) |
| --- | --- |
| `low` | Read-mostly, narrow scope, no credential handling, no arbitrary execution, no sensitive persistence |
| `medium` | Local execution of commands, meaningful filesystem access, optional network, or local persistence of operational data |
| `high` | Broad filesystem access, credential handling, persistent privileged hooks, production-adjacent control, or routine external data exfiltration risk |
| `critical` | Unrestricted execution with production blast radius, secret material exposure by design, or equivalent high-impact capability |

Additional signals that raise risk:

- Filesystem read/write breadth
- Arbitrary code or shell execution
- Network egress
- Credential or secret access
- Production system reach
- Sensitive data in inputs/outputs
- Persistence of command history or raw logs
- Supply-chain trust (install scripts, binary provenance)

Popularity does not lower security level.

## Agent compatibility

Document compatibility per agent family without assuming support.

| Value | Meaning |
| --- | --- |
| `verified` | Confirmed working in a harness-controlled check (record version/date) |
| `partial` | Works with documented limitations |
| `possible` | Credible upstream documentation or design suggests support; not harness-verified |
| `unknown` | No adequate evidence |

Minimum agent keys for registry summaries:

- `claude` (including Claude Code where relevant)
- `cursor`
- `codex`
- `gemini`
- `other`

When evidence exists, record verification date and upstream version. Do not copy marketing claims as harness verification.

## Cost classes

Use coarse classes unless verified pricing is cited:

| Value | Meaning |
| --- | --- |
| `free-software` | No license fee for the software itself (infrastructure/API costs may still apply) |
| `freemium` | Free tier with paid upgrades |
| `paid` | Requires payment for core use |
| `usage-based` | Billed by consumption |
| `unknown` | Not established |

Always separate in prose:

- Software cost
- Infrastructure cost
- API / model cost
- Operational cost

## Relationship to AGENTS.md

[`AGENTS.md`](../../AGENTS.md) remains the primary agent contract.

This document specializes Section 10 (External Tools) and Section 16 (Adding a New Tool). If conflict arises, update this architecture doc and keep `AGENTS.md` as the concise contract.
