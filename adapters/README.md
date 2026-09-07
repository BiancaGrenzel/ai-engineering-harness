# Adapters

Compatibility layer between the AI Engineering Harness and specific AI coding agents.

```text
.harness/harness.yaml
        ↓
   Harness Config
        ↓
      Adapter
        ↓
Agent-specific configuration
```

## Purpose

Adapters **project** a canonical Harness configuration into the on-disk format expected by an agent.

They do not replace:

- Rules (`rules/`)
- Skills (`skills/`)
- Tools (`docs/tools/`)
- Profiles (`profiles/`)
- Project config (`.harness/harness.yaml`)

## Source of truth

Always:

```text
Harness configuration → Adapter → Agent configuration
```

Never the reverse.

## Layout

```text
adapters/
├── README.md           # this file
├── ARCHITECTURE.md     # adapter contract
├── common/             # shared concepts and helpers
└── cursor/             # Cursor adapter (experimental)
```

Future adapters (Claude, Codex, Gemini, …) may be added later. Do not create empty vendor directories in advance.

## Implemented adapters

| Adapter | Status | Generator |
| --- | --- | --- |
| [Cursor](cursor/README.md) | experimental | `python -m adapters.cursor.generate` |

Shared helpers: [`common/`](common/) (`resolve`, `metadata`, `apply`).

## Documentation

- Architecture contract: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Design rationale: [`docs/architecture/adapters.md`](../docs/architecture/adapters.md)
- Configuration contract: [`docs/architecture/configuration.md`](../docs/architecture/configuration.md)
