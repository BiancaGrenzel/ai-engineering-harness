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

Skills are not implemented yet. When they are:

1. Search for a similar Skill first.
2. Define one coherent problem class.
3. Include purpose, activation criteria, workflow, verification, failure modes, and anti-patterns.
4. Keep Skills focused. Avoid “do everything” Skills.

## Document a tool

When documenting an external tool:

1. Verify the official source.
2. Explain when to use and when not to use it.
3. Cover installation, configuration, security, limitations, and trade-offs.
4. Prefer orchestration and references over copying third-party software into the repo.

Do not recommend a tool only because it is popular.

## Avoid duplication

Canonical resources live in `rules/` (and later `skills/`, `docs/`, `tools/`, `profiles/`).

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
