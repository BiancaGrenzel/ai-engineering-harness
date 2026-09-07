---
name: task-analysis
description: Transform a request into a technically clear task before making changes
category: core
---

# Task Analysis

## Purpose

Teach the agent to convert a user request into a technically understandable task before executing changes.

The goal is clarity of intent, scope, constraints, unknowns, required context, tools, and verification — not bureaucracy.

## When to use

- Before non-trivial implementation or modification work
- When the request is ambiguous, multi-part, or high-impact
- When the affected systems or success criteria are unclear
- When choosing between multiple plausible approaches

## When not to use

- Trivial, unambiguous edits with obvious scope
- Pure lookup or explanation tasks that do not require a change plan
- When Task Analysis has already been completed for the same request in the current session

Depth must match complexity. Do not force a full analysis checklist on small tasks.

## Inputs

- User request — the stated goal and any constraints provided
- Available repository signals — structure, docs, existing conventions
- Known environment limits — permissions, tools, time, risk tolerance

## Preconditions

- The request is available
- The agent has not already produced an equivalent analysis for this task
- Standing Rules for understanding before modifying remain in effect

## Workflow

```text
Request
  ↓
Intent
  ↓
Constraints
  ↓
Affected systems
  ↓
Unknowns
  ↓
Required context
  ↓
Required tools
  ↓
Execution strategy
  ↓
Verification strategy
```

1. **Request** — Restate what was asked in concrete technical terms.
2. **Intent** — Identify why the change is needed and what success means.
3. **Constraints** — Capture explicit and implied limits (scope, compatibility, security, style, non-goals).
4. **Affected systems** — List files, modules, interfaces, docs, or environments that may change or be impacted.
5. **Unknowns** — Record what is still unknown and whether investigation is required before acting.
6. **Required context** — Decide the minimum information needed to proceed correctly.
7. **Required tools** — Identify capability classes likely needed (search, read, edit, execute, network).
8. **Execution strategy** — Choose a proportional approach: direct action, short plan, or phased work.
9. **Verification strategy** — Define how completion will be proven.

For trivial tasks, compress steps 1–9 into a brief internal check. For complex tasks, make the analysis explicit.

## Tools

- Repository search and file inspection — locate affected systems and conventions
- Documentation readers — clarify contracts and constraints
- Issue or request text — extract intent and acceptance criteria

Prefer targeted inspection over broad repository dumps.

## Context requirements

Load:

- The request and any attached acceptance criteria
- Relevant entry docs or architecture notes for the affected area
- Only the files needed to identify scope and unknowns

Avoid loading:

- Entire unrelated directories
- Full catalogs of Rules or Skills
- Large historical logs unrelated to the request

## Expected output

A concise task understanding that answers:

- What needs to be done?
- Why does it need to be done?
- What is in scope and out of scope?
- What constraints apply?
- Which files or systems may be affected?
- What is still unknown?
- What context is required next?
- What tools may be required?
- How will correctness be verified?

The output may be internal for small tasks or written for medium and large tasks.

## Verification

- The restated intent matches the request
- Scope and non-goals are explicit enough to prevent drift
- Unknowns that block safe execution are identified
- Verification criteria are defined before major changes begin
- Analysis depth is proportional to complexity

## Failure modes

- **False clarity** — restating jargon without understanding → investigate before proceeding
- **Hidden scope expansion** — treating adjacent improvements as required → separate them
- **Ignored constraints** — missing security, compatibility, or vendor-neutrality limits → re-check constraints
- **Analysis paralysis** — over-analyzing a trivial request → reduce depth and act
- **Unresolved blockers** — proceeding despite critical unknowns → research or ask

## Anti-patterns

- Turning every request into a long questionnaire
- Skipping analysis on complex or risky work
- Treating assumptions as facts
- Loading large context before knowing what is needed
- Duplicating Rule text instead of referencing Rules

## Examples

### Example: Trivial rename

**Situation:** Rename a clearly identified local variable in one file.

**Approach:** Brief intent and scope check; no formal written analysis.

**Result:** Direct edit with light verification.

### Example: Multi-area behavior change

**Situation:** Change authentication error handling across API and client.

**Approach:** Explicit intent, affected systems, unknowns, context needs, and verification strategy before edits.

**Result:** Clear execution and verification plan with bounded scope.

## Related Rules

- `rules/core/core.md`
- `rules/core/tool-usage.md`
- `rules/core/verification.md`
- `rules/core/communication.md`
- `rules/context/context-selection.md`
- `rules/security/permissions.md`

## Related Skills

- `skills/core/planning/SKILL.md`
- `skills/core/context-engineering/SKILL.md`
- `skills/core/research/SKILL.md`
- `skills/core/verification/SKILL.md`

## References

- `AGENTS.md` — Sections 2, 19, and 20
- `docs/architecture/skills.md`
