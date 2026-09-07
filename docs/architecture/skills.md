# Skills Architecture

Official standard for creating and maintaining Skills in the AI Engineering Harness.

Canonical Skills live in [`skills/`](../../skills/). This document defines the contract. Provider adapters may load Skills later; they must not become a second source of truth.

## What is a Skill?

A Skill is a reusable procedural capability that teaches an agent how to perform a **specific class of tasks**.

Skills are not standing policy. They are specialized workflows with clear activation criteria, steps, outputs, and verification.

## Rule vs Skill

| Resource | Purpose | Example |
| --- | --- | --- |
| Rule | Persistent behavior | Verify changes |
| Skill | Specialized procedure | Debug a failing application |
| Tool | External capability | Git, MCP, RTK |
| Profile | Composition | Backend engineer |

- **Rules** constrain default behavior across tasks.
- **Skills** describe how to execute a coherent problem class.
- **Tools** provide external capabilities Skills may invoke.
- **Profiles** compose Rules, Skills, Tools, and configuration for a role or discipline.

Do not put specialized workflows inside Rules. Do not turn Skills into standing policy documents.

## Skill lifecycle

```text
Discovery
    ↓
Activation
    ↓
Context loading
    ↓
Execution
    ↓
Verification
    ↓
Completion
```

| Stage | Meaning |
| --- | --- |
| Discovery | The agent becomes aware that a Skill exists (catalog, profile, or search). |
| Activation | The agent selects the Skill because the task matches its domain. |
| Context loading | The agent loads the Skill and only the additional context it requires. |
| Execution | The agent follows the Skill workflow. |
| Verification | The agent validates outcomes using the Skill's verification guidance. |
| Completion | The agent reports results, evidence, and limitations. |

Existence is not activation. A Skill must not be loaded merely because it is present in the repository.

## Skill design principles

Skills must be:

- **Focused** — one coherent problem class
- **Composable** — usable with other Skills without duplication
- **Reusable** — applicable across projects and stacks when possible
- **Explicit** — clear activation, workflow, and outputs
- **Verifiable** — defines how to check success
- **Vendor-neutral** — not tied to a single agent vendor or model
- **Context-efficient** — loads only what the procedure needs

Avoid Skills that are:

- Giant “do everything” procedures
- Too generic to guide action
- Duplicates of existing Skills or Rules
- Specific to a single project without justification
- Dependent on a single model
- Dependent on a single vendor when neutrality is possible

## Skill activation

Load a Skill when:

- The task matches the Skill's domain
- The procedure would materially improve correctness, safety, or efficiency
- A related Rule alone is not enough to guide the specialized workflow

Do not load a Skill when:

- The task is trivial and already covered by standing Rules
- Another active Skill already covers the same procedure
- The Skill is only tangentially related

Prefer progressive activation: start with the Skill that matches the current phase (for example Task Analysis before Token Optimization).

## Context efficiency

A Skill should avoid loading:

- Unnecessary documentation
- Irrelevant files
- Duplicated instructions already present in Rules
- Oversized examples

Prefer references to Rules and related Skills over copying their content.

## Verification

Every Skill that produces changes must define how to verify its result.

Verification depth should match risk. See [`skills/core/verification/SKILL.md`](../../skills/core/verification/SKILL.md) and [`rules/core/verification.md`](../../rules/core/verification.md).

Skills that produce analysis or plans must still define success criteria for their output quality.

## Metadata

Skills use a **minimal YAML frontmatter** block for discovery across agents and future adapters.

### Format

```yaml
---
name: skill-name
description: Short description of the Skill's purpose
category: core
---
```

### Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Stable kebab-case identifier; must match the Skill directory name |
| `description` | Yes | One short sentence for discovery and selection |
| `category` | Yes | Top-level category under `skills/` (for example `core`, `ai-engineering`) |

### Design decisions

- Keep metadata small so it is easy to read, write, and parse.
- Prefer fields that help **discovery and selection**, not execution logic.
- Do not encode vendor-specific activation syntax in canonical Skills.
- Do not invent required fields until adapters need them.
- Additional fields may be added later if a concrete interoperability need appears.

Body content after the frontmatter follows [`skills/SKILL_TEMPLATE.md`](../../skills/SKILL_TEMPLATE.md).

## File layout

```text
skills/
├── README.md
├── SKILL_TEMPLATE.md
├── <category>/
│   └── <skill-name>/
│       └── SKILL.md
```

Conventions:

- One Skill per directory
- Directory name equals the `name` field
- Entry file is always `SKILL.md`
- Categories group related Skills without implying automatic loading

## Creating a new Skill

1. Search existing Skills for an equivalent.
2. Confirm the behavior is a specialized procedure, not a persistent Rule.
3. Choose the correct category.
4. Copy `skills/SKILL_TEMPLATE.md` into `skills/<category>/<skill-name>/SKILL.md`.
5. Fill every section; remove only sections that truly do not apply, and prefer keeping the standard headings.
6. Add minimal frontmatter.
7. Reference related Rules and Skills instead of copying them.
8. Keep the Skill vendor-neutral and context-efficient.
9. Update [`skills/README.md`](../../skills/README.md) when the category tree changes.
10. Validate links, metadata consistency, and that Related Rules/Skills exist.

## Relationship to AGENTS.md

[`AGENTS.md`](../../AGENTS.md) remains the primary agent contract for this repository.

This document specializes Section 8 (Skills) and Section 17 (Adding a New Skill). If there is conflict, resolve it by updating this architecture doc and keeping `AGENTS.md` as the concise contract.
