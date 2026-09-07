# Roadmap

This is a direction map derived from the current repository, not a delivery commitment. “Completed” means present in the repository; future work remains subject to design and validation.

## Completed

- Foundation: agent instructions, vendor-neutral Rules and Skills, Profiles, declarative configuration and schemas.
- Tool catalog: Registry contract, documentation standard, validation, and read-only resolution/detection/health primitives.
- Projection: experimental Cursor and Claude adapters and thin CLI entrypoints (`validate`, `generate`, `tools health`, `version`).

## In Progress

- Keep project entry documentation aligned with the committed Tool runtime layers (resolution, detection, health).

## Next

- Design `harness init` (or equivalent) to scaffold a Harness-enabled project with schemas / minimal Profile / Rules / Skills outside this repository.
- Reconcile top-level README wording with the committed Tool runtime state where it still understates existing layers.
- Optional CLAUDE.md management policy only if an explicit, fail-closed product decision is accepted.
- Add another adapter only when there is a verified target format and a need. It depends on preserving the canonical-content boundary and is optional per vendor.

## Future

- Security-specific Profiles, if a reusable composition can be defined without duplicating Rules. Depends on actual resource needs; optional.
- Context and token optimization integrations beyond the current RTK catalog entry. Depends on evidence-based tool evaluation; optional.
- MCP integration design. It depends on explicit scope and security boundaries; optional rather than implied by catalog support.
- Tool installation/configuration design. It depends on a separate authorization and provenance model; not a prerequisite for documentation or detection.

## Long Term

- Broader vendor-neutral adapter coverage.
- Deliberate runtime capabilities, observability, and hardening only where they add proportional value and preserve least privilege.
- A stable v1.0 after contracts, adapters, tests, and documentation have converged. No target date is defined.
