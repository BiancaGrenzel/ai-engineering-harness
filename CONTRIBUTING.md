# Contributing

Contributions should improve correctness, reusability, security, agent effectiveness, context efficiency, observability, or maintainability.

Keep changes small and aligned with [AGENTS.md](AGENTS.md).

## Propose a Rule

1. Confirm the behavior is persistent and repeated.
2. Search [rules/](rules/) for an existing equivalent.
3. Prefer extending an existing Rule over creating a duplicate.
4. Keep it short, actionable, vendor-neutral, and verifiable.
5. Place it in the correct category. See [rules/README.md](rules/README.md).

Do not put specialized workflows in Rules. Those belong in Skills.

## Propose a Skill

1. Search [skills/](skills/) for a similar Skill first.
2. Confirm the need is a specialized procedure, not a persistent Rule.
3. Define one coherent problem class with clear activation criteria.
4. Copy [skills/SKILL_TEMPLATE.md](skills/SKILL_TEMPLATE.md) and fill every section.
5. Add minimal frontmatter (`name`, `description`, `category`).
6. Reference Related Rules and Skills; do not copy their content.
7. Keep Skills focused, vendor-neutral, and context-efficient. Avoid “do everything” Skills.

See [docs/architecture/skills.md](docs/architecture/skills.md) and [skills/README.md](skills/README.md).

## Document a tool

When documenting an external tool:

1. Verify the official source.
2. Explain when to use and when not to use it.
3. Cover installation, configuration, security, limitations, and trade-offs.
4. Prefer orchestration and references over copying third-party software into the repo.

Do not recommend a tool only because it is popular.

## Avoid duplication

Canonical resources live in `rules/`, `skills/`, and `docs/` (and later `tools/`, `profiles/`).

Do not create parallel copies in provider adapters unless an adapter mapping is required.

## Keep vendor neutrality

Canonical Rules, Skills, and docs must remain usable across agents and stacks.

Provider-specific details belong in adapters.

## Verify changes

Before submitting:

- Confirm files are non-empty and correctly placed
- Check internal links
- Confirm no secrets were added
- Confirm the change matches the requested scope
- State what was validated and what was not

## Keep documentation current

Update [README.md](README.md), [CHANGELOG.md](CHANGELOG.md), and related docs when structure or behavior changes.
