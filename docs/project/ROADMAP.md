# Roadmap

This is a direction map derived from the current repository, not a delivery commitment. “Completed” means present in the repository; future work remains subject to design and validation.

## Completed

- Foundation: agent instructions, vendor-neutral Rules and Skills, Profiles, declarative configuration and schemas.
- Tool catalog: Registry contract, documentation standard, validation, and read-only resolution/detection/health primitives.
- Projection: experimental Cursor and Claude adapters and thin CLI entrypoints (`validate`, `generate`, `tools health`, `version`).
- Packaging: local `pip install .` installs the engine; built-in content pack ships as package resources.
- Project bootstrap: `harness init --profile software-engineer` materializes project content under `.harness/`; project-local trees become the Harness source of truth; `.cursor/` / `.claude/` stay at the project root.

## In Progress

- Keep project entry documentation aligned with the committed Tool runtime layers (resolution, detection, health).

## Next

- Optional CLAUDE.md management policy only if an explicit, fail-closed product decision is accepted.
- Add another adapter only when there is a verified target format and a need. It depends on preserving the canonical-content boundary and is optional per vendor.
- Reconcile remaining README wording with runtime layers where docs still understate committed capabilities.
- PyPI publishing / release automation after local packaging and clean-install smoke coverage remain solid.

## Future

- Security-specific Profiles (`red-team`, `blue-team`, `appsec`, `cloud-security`, `detection-engineering`, `threat-hunting`, `security-research`) as content additions when compositions are ready. Depends on reusable Rules/Skills; optional.
- Context and token optimization integrations beyond the current RTK catalog entry. Depends on evidence-based tool evaluation; optional.
- MCP integration design. It depends on explicit scope and security boundaries; optional rather than implied by catalog support.
- Tool installation/configuration design. It depends on a separate authorization and provenance model; not a prerequisite for documentation or detection.
- Separate content-pack versioning / remote registries only if independent content releases become necessary.

## Long Term

- Broader vendor-neutral adapter coverage.
- Deliberate runtime capabilities, observability, and hardening only where they add proportional value and preserve least privilege.
- A stable v1.0 after contracts, adapters, tests, and documentation have converged. No target date is defined.
