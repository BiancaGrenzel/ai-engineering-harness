---
name: tool-name
description: One-sentence description of what this Tool does
category: category-name
type: cli
maturity: unknown
license: Unknown
source: Not verified
official_documentation: Not verified
installation: not-documented
platforms: []
agent_compatibility:
  claude: unknown
  cursor: unknown
  codex: unknown
  gemini: unknown
  other: unknown
token_impact:
  effect: unknown
  magnitude: unknown
context_impact:
  magnitude: unknown
  output_profile: unknown
cost: unknown
security_level: unknown
network_required: unknown
local_execution: unknown
status: candidate
verified_on: YYYY-MM-DD
---

# Tool Name

## Summary

`<What the Tool is and the primary outcome it provides.>`

## Category

`<Category directory name, for example Token Optimization>`

## Type

`<Primary type from the architecture taxonomy>`

## Problem it solves

`<Concrete engineering problem. Do not invent problems.>`

## When to use

- `<Situation where the Tool is a good fit>`
- `<Situation where the Tool is a good fit>`

## When not to use

- `<Situation where the Tool adds little value>`
- `<Situation where risk or complexity outweighs benefit>`

## Capabilities

- `<Verified capability>`
- `<Verified capability>`

Mark uncertain items as `Not verified`.

## Installation

`<Only verified install paths from official sources.>`

If unknown:

`Not verified`

## Configuration

`<Only verified configuration.>`

If unknown:

`Not verified`

## Usage

```text
<Minimal correct example from official docs>
```

## Agent compatibility

| Agent | Compatibility | Notes |
| --- | --- | --- |
| Claude | `unknown` | `<evidence or Not verified>` |
| Cursor | `unknown` | `<evidence or Not verified>` |
| Codex | `unknown` | `<evidence or Not verified>` |
| Gemini | `unknown` | `<evidence or Not verified>` |
| Other agents | `unknown` | `<evidence or Not verified>` |

Use only: `verified`, `partial`, `possible`, `unknown`.

## Token / Context impact

- Token effect: `<reduce | increase | neutral | variable | unknown>`
- Token magnitude: `<low | medium | high | variable | unknown>`
- Context magnitude: `<low | medium | high | variable | unknown>`
- Output profile: `<small | moderate | large | filterable | structured | potentially_unbounded>`

Explain mechanism and limits. Do not invent percentages.

If citing upstream numbers, label them **Official benchmark** and distinguish from harness-observed results.

## Performance impact

`<Only if reliable evidence exists. Otherwise: Not verified>`

## Cost

- Software cost: `<...>`
- Infrastructure cost: `<...>`
- API / model cost: `<...>`
- Operational cost: `<...>`

Do not invent prices.

## Security considerations

- Filesystem: `<...>`
- Execution: `<...>`
- Network: `<...>`
- Credentials: `<...>`
- Persistence: `<...>`
- Supply chain: `<...>`

Only claim what sources support.

## Privacy considerations

`<Data collected, retained, or transmitted. Opt-out if documented. Otherwise: Not verified>`

## Limitations

- `<Explicit limitation>`
- `<Explicit limitation>`

## Alternatives

List only relevant alternatives with a reason. If none are evaluated:

`None evaluated in this harness yet.`

## Related Rules

- `rules/<category>/<rule>.md`

## Related Skills

- `skills/<category>/<skill-name>/SKILL.md`

## References

- `<Official documentation URL>`
- `<Official repository URL>`
- Verification date: `YYYY-MM-DD`
