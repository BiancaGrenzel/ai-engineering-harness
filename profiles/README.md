# Profiles

Reusable capability compositions for the AI Engineering Harness.

## What is a Profile?

A **Profile** declares a default set of:

- Rules
- Skills
- Tools

for a type of work (for example software engineering).

Profiles compose existing canonical resources. They do not copy Rule bodies, Skill workflows, or Tool documentation.

## Why Profiles exist

Projects share common capability bundles. Profiles give a stable name to those bundles so `.harness/harness.yaml` can select defaults without repeating every identifier.

```text
Profile
    ↓
default Rules / Skills / Tools

Harness configuration
    ↓
project-specific selection / overrides
```

## Profile vs project configuration

| Concept | Location | Purpose |
| --- | --- | --- |
| Profile | `profiles/<name>.yaml` | Reusable defaults for a work type |
| Harness configuration | `.harness/harness.yaml` | This project's selected Profile and optional overrides |

Do not put project-only secrets, vendor adapter settings, or long instructions in a Profile.

## Structure

```text
profiles/
├── README.md
└── software-engineer.yaml
```

## Naming convention

- Lowercase
- kebab-case when multiple words
- Stable identifiers
- Vendor-neutral (no product lock-in in the name)
- Short and descriptive

Examples: `software-engineer`, `frontend`, `security` (future).

Filename must match the `name` field: `profiles/software-engineer.yaml` → `name: software-engineer`.

## How to create a Profile

1. Confirm no existing Profile covers the same work type.
2. Compose only resources that exist (or will exist in the same change).
3. Create `profiles/<name>.yaml` with `name`, optional `description`, and `rules` / `skills` / `tools` lists.
4. Keep the Profile stack-agnostic unless the Profile's purpose is intentionally stack-specific.
5. Validate structure against `schemas/profile.schema.json` when practical.
6. Update this README if the tree changes.

Do not nest Profiles. Do not use `extends` or conditional expressions in this phase.

## Composition

| Field | Meaning |
| --- | --- |
| `rules` | Rule **category** identifiers under `rules/` (for example `core`, `security`) |
| `skills` | Skill identifiers (directory / frontmatter `name`, for example `task-analysis`) |
| `tools` | Tool identifiers from the Tool Registry (for example `rtk`) |

Profiles select **which** resources belong in the default set. Activation of a Skill for a given task still follows that Skill's criteria.

## Implemented Profiles

| Profile | Purpose |
| --- | --- |
| [software-engineer](software-engineer.yaml) | Generic software engineering defaults |

## Schema

Profiles use [`schemas/profile.schema.json`](../schemas/profile.schema.json).

## Related documentation

- [Configuration architecture](../docs/architecture/configuration.md)
- [`.harness/README.md`](../.harness/README.md)
- [Rules](../rules/README.md)
- [Skills](../skills/README.md)
- [Tools](../docs/tools/README.md)
