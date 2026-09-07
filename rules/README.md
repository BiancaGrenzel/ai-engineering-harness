# Rules

Canonical Rules for the AI Engineering Harness.

## What are Rules?

Rules describe **persistent agent behavior**.

They are short, actionable constraints that apply repeatedly across tasks. Rules shape how an agent thinks and acts by default.

Rules are not specialized workflows. They are standing expectations.

## Rule vs Skill

| Resource | Purpose |
| --- | --- |
| Rule | Persistent agent behavior |
| Skill | Specialized procedure |
| Tool | External capability |
| Profile | Composition of capabilities |

- A **Rule** says how the agent should always behave within a scope.
- A **Skill** explains how to perform a specific class of task: purpose, when to use, workflow, verification, failure modes.
- A **Tool** is an external capability the agent may invoke.
- A **Profile** composes Rules, Skills, Tools, and configuration for a discipline or role.

Do not put specialized workflows inside Rules.

## Structure

```text
rules/
├── core/          # general agent behavior
├── context/       # context engineering
├── security/      # least privilege, secrets, safe execution
├── quality/       # code quality, testing, review
└── production/    # reliability, observability, cost
```

This directory is the **canonical** source. Provider-specific adapters may reference or project these Rules later. Adapters must not become a second source of truth.

## How to create a new Rule

1. Confirm the behavior is persistent and repeated.
2. Search existing Rules for an equivalent.
3. Prefer extending an existing Rule over creating a near-duplicate.
4. Keep the Rule short, specific, actionable, and verifiable.
5. Keep it language-, framework-, and vendor-neutral.
6. Place it in the correct category.
7. Update this README only if the category structure changes.
8. Consider whether tooling could enforce the behavior more reliably than a Rule.

Before adding a Rule, ask:

1. Is this behavior important?
2. Does it apply repeatedly?
3. Can it be expressed clearly?
4. Can it be enforced or verified?
5. Does it justify its context cost?

Prefer a small number of high-value Rules.

## Choosing a category

| Category | Use when the Rule is about |
| --- | --- |
| `core/` | General agent conduct, tools, verification, docs, communication |
| `context/` | Selecting, budgeting, or reusing model context |
| `security/` | Permissions, secrets, trust boundaries, safer execution |
| `quality/` | Code quality, testing posture, review expectations |
| `production/` | Reliability, observability, and cost in production systems |

If a Rule spans categories, place it where the primary behavior lives and cross-reference sparingly.

## Avoid duplication

- Do not restate `AGENTS.md` wholesale inside a Rule.
- Do not copy the same instruction across multiple Rules.
- Do not duplicate canonical Rules inside provider adapters.
- Extend or refine existing Rules when behavior overlaps.

## How adapters use Rules

Agent environments (for example Cursor, Claude Code, Codex, Gemini, and other compatible agents) may consume these Rules through adapters.

Expected pattern:

1. Canonical Rules live in `rules/`.
2. Adapters map or load the relevant Rules into the agent-specific format.
3. Profiles may select subsets of Rules for a role or discipline.
4. Adapter-specific behavior stays in the adapter, not in canonical Rules.

See [`adapters/`](../adapters/) for the adapter contract. The Cursor adapter can project selected Rules into `.cursor/rules/harness/` as thin wrappers.
