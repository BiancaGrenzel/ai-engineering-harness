# Skills

Canonical Skills for the AI Engineering Harness.

## What are Skills?

Skills describe **specialized procedures**.

A Skill teaches an agent how to perform a coherent class of tasks: when to use it, how to execute it, what to produce, and how to verify the result.

Skills are not standing policy. Persistent behavior belongs in Rules.

## How Skills work

1. A Skill exists in the catalog (`skills/`).
2. The agent activates it only when the task matches its domain.
3. The agent loads the Skill and the minimum additional context it needs.
4. The agent follows the workflow.
5. The agent verifies outcomes and reports evidence.

Existence is not activation. Do not load every Skill for every task.

## When Skills are loaded

Load a Skill when:

- The task matches the Skill's purpose and activation criteria
- Standing Rules alone are not enough to guide the specialized procedure
- The Skill would improve correctness, safety, efficiency, or verification

Do not load a Skill when:

- The task is trivial and already covered by Rules
- Another active Skill already covers the same procedure
- The Skill is only loosely related

## Rule vs Skill vs Tool

| Resource | Purpose | Example |
| --- | --- | --- |
| Rule | Persistent behavior | Verify changes |
| Skill | Specialized procedure | Analyze a task before editing |
| Tool | External capability | Git, MCP, RTK |
| Profile | Composition | Backend engineer |

Official contract: [`docs/architecture/skills.md`](../docs/architecture/skills.md)

## Structure

```text
skills/
├── README.md
├── SKILL_TEMPLATE.md
├── core/
│   ├── task-analysis/
│   │   └── SKILL.md
│   ├── planning/
│   │   └── SKILL.md
│   ├── context-engineering/
│   │   └── SKILL.md
│   ├── research/
│   │   └── SKILL.md
│   └── verification/
│       └── SKILL.md
└── ai-engineering/
    └── token-optimization/
        └── SKILL.md
```

This directory is the **canonical** source. Provider adapters may reference or project these Skills later. Adapters must not become a second source of truth.

## Naming conventions

- Category directory: short kebab-case domain (`core`, `ai-engineering`)
- Skill directory: short kebab-case name matching frontmatter `name`
- Entry file: always `SKILL.md`
- One Skill per directory

## Template

New Skills start from [`SKILL_TEMPLATE.md`](SKILL_TEMPLATE.md).

Required sections:

- Purpose
- When to use / When not to use
- Inputs
- Preconditions
- Workflow
- Tools
- Context requirements
- Expected output
- Verification
- Failure modes
- Anti-patterns
- Examples
- Related Rules
- Related Skills
- References

## Metadata

Each `SKILL.md` begins with minimal YAML frontmatter:

```yaml
---
name: skill-name
description: Short description
category: core
---
```

See [`docs/architecture/skills.md`](../docs/architecture/skills.md) for the metadata decision and field definitions.

## Skill graph

Current conceptual relationships (documentation only; no automatic dependency system):

```text
Task Analysis
      ↓
Planning
      ↓
Context Engineering
      ↓
Research
      ↓
Execution
      ↓
Verification
```

```text
Context Engineering
      ↓
Token Optimization
```

Notes:

- Not every task uses every Skill.
- Research may occur before Planning when unknowns block a plan.
- Context Engineering can apply at multiple points.
- Verification applies whenever changes are produced.

## Implemented Skills

| Skill | Category | Purpose |
| --- | --- | --- |
| [task-analysis](core/task-analysis/SKILL.md) | core | Clarify intent, scope, constraints, and verification before changes |
| [planning](core/planning/SKILL.md) | core | Plan in proportion to task complexity |
| [context-engineering](core/context-engineering/SKILL.md) | core | Load minimum sufficient context with progressive expansion |
| [research](core/research/SKILL.md) | core | Investigate unknowns from authoritative sources |
| [verification](core/verification/SKILL.md) | core | Verify outcomes with risk-proportional checks |
| [token-optimization](ai-engineering/token-optimization/SKILL.md) | ai-engineering | Reduce token waste without harming correctness |

## How to create a new Skill

1. Search existing Skills for an equivalent.
2. Confirm the need is a specialized procedure, not a persistent Rule.
3. Choose the correct category. Prefer extending an existing Skill over creating a near-duplicate.
4. Copy `SKILL_TEMPLATE.md` to `skills/<category>/<skill-name>/SKILL.md`.
5. Fill frontmatter and all sections.
6. Reference Related Rules and Related Skills; do not copy their content.
7. Keep the Skill focused, vendor-neutral, and context-efficient.
8. Update this README if the category tree changes.
9. Validate links, metadata, and that referenced files exist.

Before adding a Skill, ask:

1. Does this solve one coherent problem class?
2. Can an existing Skill or Rule cover it?
3. Are activation criteria clear?
4. Is verification defined?
5. Does it justify its context cost?

## Avoid duplication

- Do not restate `AGENTS.md` or Rules wholesale inside Skills.
- Do not create overlapping Skills for the same procedure.
- Do not duplicate canonical Skills inside provider adapters.
- Prefer references over copied text.
- Framework-specific Skills should wait until the foundational layer is stable.

## Relating Skills

Use **Related Skills** for collaborative workflows, not hard runtime dependencies.

Example: Task Analysis often precedes Planning; Context Engineering often precedes Token Optimization.

Keep relationships sparse and purposeful.

## How to verify a Skill

Before considering a Skill complete:

- `SKILL.md` exists and follows the template headings
- Frontmatter `name` matches the directory name
- Frontmatter `category` matches the parent category directory
- Related Rules exist
- Related Skills exist
- No vendor-specific lock-in unless required and justified
- No invented external tool details
- Examples are illustrative, not project-secret-bearing
- Content stays consistent with `AGENTS.md` and `docs/architecture/skills.md`

## Out of scope for this phase

Not created yet:

- Frontend, backend, mobile, or framework-specific Skills
- Security exploitation Skills
- RAG, MCP, or deployment implementation Skills
- DevOps-only Skills
- Automatic Skill dependency resolution
- Additional provider adapters beyond the experimental Cursor adapter

See [`adapters/`](../adapters/) for projection into agent-specific Skill locations.
