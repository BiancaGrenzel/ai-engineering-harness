---
name: planning
description: Create an implementation plan whose depth matches task complexity
category: core
---

# Planning

## Purpose

Teach the agent to plan in proportion to task size and risk.

Planning should prevent two failures: acting on complex work without a plan, and producing oversized plans for simple work.

## When to use

- After Task Analysis when the work is non-trivial
- When the change touches multiple files, systems, or phases
- When dependencies, ordering, or risk need to be made explicit
- When the user asks for a plan before implementation

## When not to use

- Trivial tasks that can be executed safely in one or two obvious steps
- When an adequate plan already exists for the same task in the current session
- When the next need is research or context gathering, not an implementation plan

## Inputs

- Task analysis outcome — intent, scope, constraints, unknowns, verification strategy
- Complexity estimate — trivial, small, medium, or large
- Known risks — regressions, security, production impact, irreversibility

## Preconditions

- Intent and success criteria are understood at least at a basic level
- Critical unknowns that block planning have been identified
- The agent is not inventing requirements beyond the request

## Workflow

```text
Assess complexity
  ↓
Select planning depth
  ↓
Define steps or phases
  ↓
Identify dependencies and risks
  ↓
Define verification checkpoints
  ↓
Execute only after the plan is sufficient
```

### Complexity guide

| Size | Planning depth |
| --- | --- |
| Trivial | Execute directly. No written plan. |
| Small | Short plan: goal, files/areas, steps, verification. |
| Medium | Explicit implementation steps, ordering, and checks. |
| Large | Phases, dependencies, risks, rollback or recovery notes, and verification per phase. |

### Criteria for depth

Increase planning depth when more of these are true:

- Multiple components or ownership boundaries are involved
- Behavior changes are user-visible or production-facing
- Security, data integrity, or permissions are affected
- Ordering and dependencies are non-obvious
- Rollback is difficult
- Unknowns remain material

Decrease planning depth when:

- Scope is local and obvious
- Risk is low
- The path is already well understood
- Extra planning would delay a safe, small fix

## Tools

- File and symbol search — confirm touch points before sequencing work
- Diff and status inspection — understand current state before planning changes
- Test or build discovery — identify verification checkpoints early

Do not run broad exploratory commands merely to decorate a plan.

## Context requirements

Load:

- Task analysis results already available in the session
- Key files or docs needed to sequence the work correctly
- Existing project conventions that constrain the approach

Avoid loading:

- Full unrelated subsystem trees
- Multiple alternative design essays when one sufficient approach exists

## Expected output

A plan whose size matches the task:

- **Trivial:** immediate execution
- **Small:** brief step list and verification note
- **Medium:** ordered implementation steps and checks
- **Large:** phased plan with dependencies, risks, and verification points

The plan should make scope, order, and “done” criteria clear enough to prevent drift.

## Verification

- Planning depth matches complexity and risk
- Steps are actionable and ordered
- Out-of-scope work is excluded
- Verification is included, not deferred indefinitely
- The plan does not invent APIs, paths, or capabilities

## Failure modes

- **No plan for complex work** — skip planning → stop and create a proportional plan
- **Giant plan for a tiny change** — over-planning → collapse to a short plan and execute
- **Plan as theater** — vague steps with no verification → make steps concrete
- **Hidden scope creep** — plan absorbs unrelated cleanup → remove it or ask
- **Premature detail** — detailing unknowns as if known → mark research first

## Anti-patterns

- Writing multi-phase plans for one-line fixes
- Starting large refactors without phases or checkpoints
- Planning tools and vendors that are not required
- Treating the plan as immutable when evidence changes
- Duplicating Task Analysis content instead of building on it

## Examples

### Example: Small docs fix

**Situation:** Correct a broken internal link in one markdown file.

**Approach:** No formal plan; edit and verify the link.

**Result:** Fast, safe completion.

### Example: Large architectural addition

**Situation:** Introduce a new canonical resource layer used by multiple adapters later.

**Approach:** Phased plan with dependencies, risks, documentation updates, and verification per phase.

**Result:** Controlled implementation without unnecessary expansion.

## Related Rules

- `rules/core/core.md`
- `rules/core/verification.md`
- `rules/core/communication.md`
- `rules/quality/review.md`
- `rules/security/permissions.md`

## Related Skills

- `skills/core/task-analysis/SKILL.md`
- `skills/core/context-engineering/SKILL.md`
- `skills/core/research/SKILL.md`
- `skills/core/verification/SKILL.md`

## References

- `AGENTS.md` — Sections 19 and 20
- `docs/architecture/skills.md`
