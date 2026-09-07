---
name: verification
description: Verify work with checks proportional to risk and report evidence honestly
category: core
---

# Verification

## Purpose

Teach the agent to verify results before claiming success.

Verification is evidence-based. Depth must match risk, impact, and complexity. This Skill covers choosing a verification level, running checks, inspecting results, fixing failures, re-running, and reporting evidence.

## When to use

- After any change that can affect correctness, security, or behavior
- Before claiming that work is complete
- When a Skill or plan defines verification checkpoints
- When failures need a disciplined fix-and-recheck loop

## When not to use

- When no change occurred and the task was purely explanatory
- When verification for the same change is already complete with still-valid evidence
- When the only remaining work is reporting already-gathered results

## Inputs

- Change set — files or systems modified
- Risk profile — impact, blast radius, sensitivity
- Available checks — inspection, static checks, tests, build, runtime, security reviews
- Prior plan or Skill verification criteria

## Preconditions

- The intended success criteria are known
- The agent will not claim checks that were not run
- Destructive or production validation requires appropriate authorization

## Workflow

```text
Change
  ↓
Identify verification level
  ↓
Run appropriate checks
  ↓
Inspect results
  ↓
Fix failures
  ↓
Re-run
  ↓
Report evidence
```

1. **Identify verification level** — Choose the minimum level that matches risk.
2. **Run appropriate checks** — Prefer existing project checks over inventing a new toolchain.
3. **Inspect results** — Read failures carefully; do not ignore warnings that affect correctness.
4. **Fix failures** — Correct real defects caused by the change.
5. **Re-run** — Confirm the fix with the same or stronger checks.
6. **Report evidence** — State what was run, what passed, what did not, and what remains unverified.

### Verification levels

| Level | Meaning | Typical use |
| --- | --- | --- |
| 0 | Inspection only | Trivial docs or clearly local text edits |
| 1 | Syntax / static validation | Markdown structure, schema, lint, types when available |
| 2 | Tests | Behavior covered by existing or new focused tests |
| 3 | Build / integration | Compile, package, or integration checks |
| 4 | Runtime validation | Running the system or affected path |
| 5 | Security / production validation | Authorized high-risk or production-facing checks |

Do not require Level 5 for every change. Escalate only when risk justifies it.

### What to consider

- **Correctness** — Does the change satisfy the request?
- **Regression** — Did nearby behavior break?
- **Edge cases** — Are boundary and failure paths handled?
- **Security** — Are secrets, trust boundaries, and permissions safe?
- **Performance** — Only when relevant to the change

## Tools

- File and diff inspection — Level 0 evidence
- Linters, type checkers, schema or markdown validators — Level 1
- Project test runners — Level 2
- Build and integration commands — Level 3
- Runtime or smoke checks — Level 4
- Authorized security review tooling or procedures — Level 5

Use the project's existing verification approach when one exists. Do not invent mandatory frameworks.

## Context requirements

Load:

- The changed files and success criteria
- Relevant test, lint, or build entry points
- Failure output needed to diagnose issues

Avoid loading:

- Full unrelated test suites in context when only summaries or failing subsets are needed
- Production secrets or sensitive logs
- Broad system dumps unrelated to the failing check

## Expected output

- A chosen verification level with rationale
- Evidence of checks actually performed
- Fixes for failures caused by the change, when feasible
- Honest limitations when a needed check could not be run
- No unverified success claims

## Verification

This Skill is recursive by nature. Success means:

- The selected level matches risk
- Checks were actually executed or explicitly skipped with reason
- Failures were inspected and addressed or reported
- Final claims match the evidence

## Failure modes

- **Appearance-based confidence** — claiming success because the patch “looks right” → run proportional checks
- **Wrong level** — over-testing trivia or under-testing risky changes → reassess risk
- **Ignored failures** — treating red checks as noise → inspect and fix or explain
- **One-shot syndrome** — fixing without re-running → re-run
- **False reporting** — stating tests passed when not run → correct the report

## Anti-patterns

- “Verified” with no evidence
- Mandatory production validation for low-risk docs edits
- Skipping verification because the change seems small but is high-impact
- Adding low-value ceremonial tests instead of meaningful checks
- Dumping entire CI logs into context when a failing subset is enough

## Examples

### Example: Documentation structure change

**Situation:** Add a new markdown architecture doc and Skill files.

**Approach:** Level 0–1 — inspect structure, metadata consistency, and internal links.

**Result:** Structural validation without unnecessary runtime checks.

### Example: Authentication logic change

**Situation:** Modify access-control behavior.

**Approach:** Higher level — tests, targeted runtime checks, and security-focused review as authorized.

**Result:** Evidence matched to risk.

## Related Rules

- `rules/core/verification.md`
- `rules/core/communication.md`
- `rules/quality/testing.md`
- `rules/quality/review.md`
- `rules/security/security.md`
- `rules/security/sandboxing.md`

## Related Skills

- `skills/core/task-analysis/SKILL.md`
- `skills/core/planning/SKILL.md`
- `skills/core/context-engineering/SKILL.md`
- `skills/core/research/SKILL.md`

## References

- `AGENTS.md` — Sections 14 and 21
- `docs/architecture/skills.md`
