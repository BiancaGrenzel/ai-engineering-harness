---
name: skill-name
description: One-sentence description of what this Skill does
category: category-name
---

# Skill Name

## Purpose

`<What specialized capability this Skill provides and what problem class it solves.>`

## When to use

- `<Activation condition 1>`
- `<Activation condition 2>`
- `<Activation condition 3>`

## When not to use

- `<Situation where this Skill should not be loaded>`
- `<Overlap with another Skill or with standing Rules>`
- `<Trivial case that does not justify this procedure>`

## Inputs

- `<Required input>` — `<what it is>`
- `<Optional input>` — `<what it is>`

## Preconditions

- `<Condition that must be true before starting>`
- `<Authorization, environment, or information requirement>`

## Workflow

1. `<Step>`
2. `<Step>`
3. `<Step>`
4. `<Step>`

Use a diagram when the flow is non-linear:

```text
Start
  ↓
Step
  ↓
Decision
  ↓
End
```

## Tools

- `<Tool or capability class>` — `<why it may be needed>`
- Prefer capability classes over vendor-specific product names unless a specific tool is required.

## Context requirements

Load:

- `<Minimum files, docs, or state needed>`

Avoid loading:

- `<Common noise sources for this Skill>`

## Expected output

- `<Artifact, decision, or change produced by this Skill>`
- `<What “done” looks like>`

## Verification

- `<How to check that the Skill succeeded>`
- `<Checks proportional to risk>`
- `<What evidence to report>`

## Failure modes

- `<How this Skill can fail>` — `<what to do>`
- `<Ambiguous input>` — `<clarify or stop>`
- `<Missing context>` — `<expand context or ask>`

## Anti-patterns

- `<What not to do while using this Skill>`
- `<Over-application to trivial tasks>`
- `<Copying Rule content instead of referencing Rules>`

## Examples

### Example: `<short title>`

**Situation:** `<brief scenario>`

**Approach:** `<how the Skill should be applied>`

**Result:** `<expected outcome>`

## Related Rules

- `rules/<category>/<rule>.md`

## Related Skills

- `skills/<category>/<skill-name>/SKILL.md`

## References

- `<Canonical docs, architecture notes, or standards>`
- Prefer repository paths or official external sources. Do not invent references.
