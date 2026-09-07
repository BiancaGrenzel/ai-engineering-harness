---
name: context-engineering
description: Select, prioritize, and expand only the minimum context required for correctness
category: core
---

# Context Engineering

## Purpose

Teach the agent to treat context as a limited engineering resource.

This Skill defines how to identify information needs, retrieve targeted material, prioritize relevance, reuse what is already known, compress when useful, and expand only when missing information blocks correctness.

## When to use

- Before loading large amounts of repository or tool output
- When a task could easily pull in irrelevant files or docs
- When context pressure is high or rising
- When deciding whether to search, summarize, or read in full
- Whenever progressive disclosure is needed for a non-trivial task

## When not to use

- When the required context is already loaded and sufficient
- For tiny tasks where a single targeted read is obviously enough
- As a substitute for Task Analysis when intent is still unclear

## Inputs

- Task goal and current unknowns
- Candidate information sources — files, docs, search hits, prior session knowledge
- Context pressure signals — size of loaded material, noisy tool output, long history

## Preconditions

- The agent knows what question the next context must answer
- Standing context Rules remain in effect
- The agent will not discard information required for correctness to save tokens

## Workflow

```text
Task
  ↓
Identify information requirements
  ↓
Search
  ↓
Rank relevance
  ↓
Load minimum sufficient context
  ↓
Work
  ↓
Detect missing information
  ↓
Expand context if necessary
  ↓
Verify
```

1. **Identify information requirements** — State what must be known to proceed correctly.
2. **Search** — Use targeted queries before broad reads.
3. **Rank relevance** — Prefer primary, current, and task-specific sources.
4. **Load minimum sufficient context** — Read only what is needed now.
5. **Work** — Execute with the loaded context.
6. **Detect missing information** — Notice concrete gaps, not vague curiosity.
7. **Expand if necessary** — Add the next smallest useful piece of context.
8. **Verify** — Confirm the loaded context supported a correct outcome.

Distinguish **necessary** context (required for correctness or safety) from **convenient** context (nice to have, but not required yet).

## Context Budget

Context has cost.

The objective is not merely to reduce tokens.

Maximize:

```text
useful information / context consumed
```

Never remove information required for correctness, security, or adequate verification merely to reduce context size.

Account for all contributors to context cost:

- System and standing instructions
- User prompt
- Conversation history
- Repository files
- Retrieved documents
- Tool output
- Logs
- Model output retained in the session

## Tools

- Targeted search — locate likely relevant files or symbols
- Focused file reads — load specific sections when possible
- Filtered command output — avoid dumping large results into context
- Summaries — compress large resources when full text is unnecessary

Prefer capability-efficient tools over broad exploratory dumps.

## Context requirements

Load:

- The current information requirement list
- Highest-ranked sources only
- Existing session knowledge before re-fetching

Avoid loading:

- Entire directories “just in case”
- Duplicate docs already represented by Rules or earlier reads
- Oversized examples unrelated to the active step
- Full tool transcripts when a filtered extract is enough

## Expected output

- A working set of context sufficient for the current step
- Clear awareness of what was not loaded and why
- Expansion only when a specific missing fact blocks progress
- Preserved necessary signal; reduced noise

## Verification

- The agent can point to why each major loaded item was needed
- Missing-information gaps were concrete before expansion
- No required correctness or safety information was discarded for savings
- Redundant reloads were avoided when session knowledge was sufficient
- Outcome quality was not harmed by under-loading

## Failure modes

- **Context hoarding** — loading everything early → unload mentally and restart from requirements
- **Context starvation** — omitting necessary facts to save tokens → restore required context
- **Relevance confusion** — treating convenient docs as necessary → re-rank
- **Redundant reload** — re-reading unchanged material → reuse session knowledge
- **Noise flood** — unfiltered tool output dominates → re-run with filters or summaries

## Anti-patterns

- “Load the whole repo first”
- Equating more context with better answers
- Copying Rule content into prompts instead of referencing Rules
- Expanding context out of curiosity rather than need
- Optimizing tokens at the expense of correctness

## Examples

### Example: Bug in one module

**Situation:** A failing function likely lives in one package.

**Approach:** Search for the symbol, read the function and its tests, then expand only if call sites are implicated.

**Result:** Small, high-signal context and faster diagnosis.

### Example: Architecture decision

**Situation:** Need the harness contract for Skills.

**Approach:** Read the architecture doc and related Skills README; do not load every Skill body up front.

**Result:** Enough contract detail to proceed without catalog overload.

## Related Rules

- `rules/context/context-selection.md`
- `rules/context/context-budget.md`
- `rules/context/context-reuse.md`
- `rules/core/tool-usage.md`
- `rules/core/core.md`
- `rules/production/cost.md`

## Related Skills

- `skills/core/task-analysis/SKILL.md`
- `skills/core/research/SKILL.md`
- `skills/core/verification/SKILL.md`
- `skills/ai-engineering/token-optimization/SKILL.md`

## References

- `AGENTS.md` — Sections 3 and 4
- `docs/architecture/skills.md`
