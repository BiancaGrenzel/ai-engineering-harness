---
name: token-optimization
description: Treat tokens as an engineering dimension and reduce waste without harming correctness
category: ai-engineering
---

# Token Optimization

## Purpose

Teach the agent to treat tokens as an engineering dimension.

This Skill covers identifying waste across the prompt and context stack, reducing redundancy, filtering tool output, reusing context, choosing efficient tools and models, using caching when appropriate, and verifying that optimization does not remove necessary information.

## When to use

- When context pressure is high or rising
- When tool output is large or noisy
- When repeated prompts reload the same material
- When designing or reviewing agent workflows for efficiency
- When cost, latency, or context limits matter for the task

## When not to use

- When the immediate need is correctness investigation and context is already lean
- When optimization would delay a trivial change with negligible token cost
- When a dedicated Context Engineering pass is enough and no broader token strategy is required

This Skill complements Context Engineering. Context Engineering selects what to load. Token Optimization improves how token-consuming surfaces are managed across the whole interaction.

## Inputs

- Current context composition — instructions, history, retrieved material, tool output
- Task requirements — what information is necessary for correctness
- Efficiency constraints — cost, latency, context window pressure
- Available optimization mechanisms — filtering, reuse, caching, routing, retrieval

## Preconditions

- Necessary information for correctness is identified or identifiable
- The agent will not sacrifice required verification or security for savings
- Measurements or estimates are preferred over vague claims when available

## Workflow

```text
Map token consumers
  ↓
Identify waste
  ↓
Measure when possible
  ↓
Reduce redundancy
  ↓
Filter tool output
  ↓
Remove unnecessary context
  ↓
Reuse existing context
  ↓
Choose efficient tools and models
  ↓
Apply caching when appropriate
  ↓
Verify signal preserved
```

1. **Map token consumers** — Inspect where tokens are going.
2. **Identify waste** — Find duplication, irrelevance, and oversized outputs.
3. **Measure when possible** — Prefer concrete estimates or tooling over guesswork.
4. **Reduce redundancy** — Eliminate repeated instructions and re-loads.
5. **Filter tool output** — Keep only the lines or fields needed.
6. **Remove unnecessary context** — Drop convenient but non-necessary material.
7. **Reuse existing context** — Prefer session knowledge over re-fetching.
8. **Choose efficient tools and models** — Match capability and cost to the task.
9. **Apply caching when appropriate** — Reuse stable prompt prefixes or semantic results when the environment supports it.
10. **Verify signal preserved** — Confirm optimization did not remove required information.

### Token consumers to inspect

- System instructions
- User prompt
- Conversation history
- Repository context
- Retrieved documents
- Tool output
- Logs
- Model output retained for later steps

## Optimization Techniques

Documented conceptually by this harness:

| Technique | Intent |
| --- | --- |
| Output filtering | Keep only relevant tool or command output |
| Context reduction | Load fewer, higher-value sources |
| Context reuse | Avoid re-reading unchanged material |
| Prompt compression | Remove repeated or low-value instruction text |
| Prompt caching | Reuse stable prompt prefixes when supported |
| Semantic caching | Reuse prior answers for equivalent questions when safe |
| Model routing | Use a model whose capability matches task difficulty |
| Retrieval | Fetch targeted material instead of preloading corpora |
| Structured output | Prefer compact machine-readable results over prose dumps |
| Token-aware tooling | Prefer tools that minimize noisy context ingress |

Specific tool implementations (for example RTK) are documented separately under `docs/tools/` when added. Do not invent installation or CLI details here.

## Tools

- Filtered search and scoped commands — reduce ingress volume
- Summarization of large artifacts — when full text is unnecessary
- Token-aware wrappers or utilities — when available and documented
- Model selection controls — when the environment supports routing

Prefer vendor-neutral descriptions unless a specific documented tool is required.

## Context requirements

Load:

- The active task requirements
- Evidence of the largest token consumers
- Any already-available summaries or prior results

Avoid loading:

- Full raw logs when samples or filtered slices suffice
- Duplicate Rule or Skill bodies already represented by references
- Broad corpora that retrieval could replace

## Expected output

- Lower noise for the same or better task outcome
- Clear notes on what was optimized
- Preservation of information required for correctness, security, and verification
- No false claims of savings without basis

## Verification

- Necessary information remains available
- Verification quality is not weakened
- Security and secret-handling posture is unchanged or improved
- Claimed optimizations correspond to real reductions in redundancy or noise
- If measurement was not possible, uncertainty is stated

## Failure modes

- **Destructive compression** — removing facts needed for correctness → restore them
- **False economy** — saving tokens but causing rework that costs more → prioritize correctness
- **Unmeasured bragging** — claiming large savings without evidence → qualify claims
- **Cache staleness** — reusing outdated cached answers → invalidate and refresh
- **Wrong model routing** — choosing a too-weak model for a hard task → escalate capability

## Anti-patterns

- Deleting verification steps to save tokens
- Stripping security warnings from context
- Re-fetching large files instead of reusing known results
- Optimizing trivia while leaving huge unfiltered tool output untouched
- Introducing vendor lock-in for a generic optimization technique

## Examples

### Example: Noisy command output

**Situation:** A status command returns hundreds of irrelevant lines.

**Approach:** Re-run with a narrower query or filter to the failing section only.

**Result:** Same diagnosis, far less context cost.

### Example: Repeated architecture reload

**Situation:** Each step re-reads the same architecture doc.

**Approach:** Reuse the earlier summary and open only the section needed for a new question.

**Result:** Stable understanding with lower token use.

## Related Rules

- `rules/context/context-budget.md`
- `rules/context/context-selection.md`
- `rules/context/context-reuse.md`
- `rules/core/tool-usage.md`
- `rules/production/cost.md`
- `rules/core/verification.md`

## Related Skills

- `skills/core/context-engineering/SKILL.md`
- `skills/core/research/SKILL.md`
- `skills/core/verification/SKILL.md`

## References

- `AGENTS.md` — Section 4
- `docs/architecture/skills.md`
- `docs/tools/token/rtk.md`
