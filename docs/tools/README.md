# Tools

Canonical Tool catalog for the AI Engineering Harness.

This directory documents external capabilities. It is not an installer, package manager, or MCP runtime.

Architecture contract: [`docs/architecture/tools.md`](../architecture/tools.md)

## What are Tools?

Tools are **external capabilities** that can improve agent-assisted engineering workflows.

They may be CLIs, libraries, SDKs, MCP servers, services, platforms, frameworks, protocols, or utilities.

The catalog distinguishes those types. A protocol is not a platform. A CLI is not an MCP server.

## Why a Tool Registry?

Agents and humans need a shared, evidence-based inventory of capabilities that considers:

- Problem fit
- Security and privacy
- Token and context cost
- Compatibility
- Maintenance and reversibility

Without a registry, Tool advice becomes folklore: popular names, unverified claims, and accidental vendor lock-in.

The registry optimizes for **useful entries**, not entry count.

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

Every documented Tool should follow [`TOOL_TEMPLATE.md`](TOOL_TEMPLATE.md) and the metadata model in [`docs/architecture/tools.md`](../architecture/tools.md).

Unknown facts stay unknown.

## Evaluation criteria

Before recommending a Tool, evaluate it with [`evaluation.md`](evaluation.md).

## Security considerations

Classify security using the criteria in the architecture doc. Popular Tools with broad execution or network reach are not automatically low risk.

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
6. Add a row to [`registry.md`](registry.md).
7. Update the category README if needed.
8. Apply [`recommendation-policy.md`](recommendation-policy.md) before setting `recommended`.
9. Do **not** add installers or adapters in the documentation-only phase unless explicitly requested.

## Registry

Central catalog: [`registry.md`](registry.md)

## Out of scope for this phase

- Automatic installation
- CLI for the harness
- MCP server implementations
- Provider adapters under `.cursor/` or `.claude/`
- Profiles wiring
- Numeric scoring database
