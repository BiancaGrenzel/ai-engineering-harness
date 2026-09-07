# Tools

Canonical Tool catalog for the AI Engineering Harness.

This directory documents external capabilities. It is not an installer, package manager, or MCP runtime.

Architecture contract: [`docs/architecture/tools.md`](../architecture/tools.md)

## What are Tools?

Tools are **external capabilities** that can improve agent-assisted engineering workflows.

They may be CLIs, libraries, SDKs, MCP servers, services, platforms, frameworks, protocols, or utilities.

The catalog distinguishes those types. A protocol is not a platform. A CLI is not an MCP server.

## Tool Registry

[`tools/registry.yaml`](../../tools/registry.yaml) is the canonical,
machine-readable catalog of operational Tool metadata. It supports deterministic
validation and future resolution without becoming an installer, runtime, or
agent-specific configuration file.

`docs/tools/` remains the human-readable source for explanation, evidence,
rationale, limitations, and guidance. The Registry points to the relevant Tool
page; documentation must not become a second operational schema.

The Registry records a Tool's stable identity, minimal kind, documentation path,
capabilities, declared platform support, safe detection metadata, and security
metadata. It must not contain executable code, shell scripts, package-manager
commands, Adapter logic, runtime state, credentials, or installation automation.

Read-only runtime probing of declared CLI Tools is described in
[`docs/architecture/tool-detection.md`](../architecture/tool-detection.md).
Detection observes the local environment; it does not install Tools or rewrite
the Registry.

The catalog helps agents and humans assess:

- Problem fit
- Security and privacy
- Token and context cost
- Compatibility
- Maintenance and reversibility

The Registry optimizes for **useful entries**, not entry count.

## Tool vs Skill

| Resource | Purpose |
| --- | --- |
| Tool | External capability you can install or call |
| Skill | Procedure for when/how to apply a class of work |

Example: RTK is a Tool. Token Optimization is a Skill that may reference RTK.

Skills must not re-document Tool install/CLI details. Link here instead.

## Tool vs Rule

| Resource | Purpose |
| --- | --- |
| Tool | Capability |
| Rule | Persistent behavior |

Example: “Prefer filtered tool output” is a Rule. A filtering CLI is a Tool that can help satisfy that Rule.

## Tool categories

| Category | Path | Purpose |
| --- | --- | --- |
| Token Optimization | [`token/`](token/) | Reduce or control token consumption |
| Context Engineering | [`context/`](context/) | Select, compress, or manage model context |
| MCP | [`mcp/`](mcp/) | Model Context Protocol servers and related tooling |
| Search | [`search/`](search/) | Code, doc, and knowledge search capabilities |
| Agents | [`agents/`](agents/) | Agent runtimes, orchestrators, and frameworks |
| RAG | [`rag/`](rag/) | Retrieval-augmented generation components |
| Memory | [`memory/`](memory/) | Persistent or session memory systems |
| Observability | [`observability/`](observability/) | Traces, metrics, logs, and usage visibility |
| Evaluation | [`evals/`](evals/) | Eval harnesses and quality measurement |
| Security | [`security/`](security/) | Defensive and authorized security tooling |
| Development | [`development/`](development/) | General developer productivity tools |
| Infrastructure | [`infrastructure/`](infrastructure/) | Runtime, deploy, and infra-oriented tools |

## Tool metadata

The Registry contract is defined by
[`schemas/tool-registry.schema.json`](../../schemas/tool-registry.schema.json).
Every documented Tool should follow [`TOOL_TEMPLATE.md`](TOOL_TEMPLATE.md) for
human-facing content and the metadata model in
[`docs/architecture/tools.md`](../architecture/tools.md).

Unknown facts stay unknown.

## Evaluation criteria

Before recommending a Tool, evaluate it with [`evaluation.md`](evaluation.md).

## Security considerations

Registry `security.baseline_risk` classifies a Tool's normal documented behavior,
not its effective risk in a particular environment. Access metadata describes
potential reach; it is not an authorization grant. Provenance and trust remain
future metadata separate from access and baseline risk. Popular Tools with broad
execution or network reach are not automatically low risk.

## Token/context considerations

Record token **effect** and **magnitude**, plus context magnitude and output profile.

A Tool that reduces bash noise can still increase risk if it hides required signal. Correctness outranks savings.

## How to add a Tool

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

1. Confirm no equivalent entry exists.
2. Research official sources only for capability claims.
3. Evaluate with [`evaluation.md`](evaluation.md).
4. Create `docs/tools/<category>/<tool>.md` from [`TOOL_TEMPLATE.md`](TOOL_TEMPLATE.md).
5. Classify type, maturity, status, token/context impact, security, compatibility.
6. Add a declarative entry to [`tools/registry.yaml`](../../tools/registry.yaml)
   that references the new documentation page.
7. Update the category README if needed.
8. Apply [`recommendation-policy.md`](recommendation-policy.md) before setting `recommended`.
9. Do **not** add installers or adapters in the documentation-only phase unless explicitly requested.

## Example

The RTK entry demonstrates the minimum CLI metadata without installing or
configuring RTK:

```yaml
- id: rtk
  name: RTK
  kind: cli
  documentation: docs/tools/token/rtk.md
  capabilities: [token-reduction, command-wrapping, output-compression]
  detection:
    executable: rtk
    version_arguments: [--version]
```

The full entry is in [`tools/registry.yaml`](../../tools/registry.yaml). Its
human-facing evidence and limitations are in [`token/rtk.md`](token/rtk.md).

## Out of scope for this phase

- Automatic installation
- CLI for the harness
- MCP server implementations
- Provider adapters under `.cursor/` or `.claude/` (see [`adapters/`](../../adapters/) for the Cursor generator)
- Numeric scoring database
- Automatic Profile → Tool installation wiring
