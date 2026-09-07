# Tool Recommendation Policy

Defines when a Tool may hold each registry status.

This policy protects the harness from popularity-driven recommendations and from silent promotion of unevaluated software.

## Status definitions

### Candidate

Use when:

- Someone proposed the Tool for a real problem class
- Research is incomplete
- Documentation may be partial or missing

A candidate must not be presented as endorsed.

### Evaluated

Use when:

- Official sources were researched
- A Tool page exists using the standard template
- Metadata and classifications are filled honestly (`unknown` / `Not verified` where needed)
- Security, privacy, token, and context impacts are considered
- The Tool appears in [`registry.md`](registry.md)

Evaluated means “documented with evidence,” not “default choice.”

### Recommended

Use only when **all** of the following are true:

1. **Problem fit** — Solves a concrete harness-relevant problem better than doing nothing.
2. **Evidence** — Claims about capabilities come from authoritative sources; uncertain items are marked.
3. **Security** — Security level is understood; residual risks are explicit and acceptable for the intended use.
4. **Maintenance** — Upstream maintenance posture is acceptable for the intended adoption window.
5. **Cost** — Cost classes are known enough to advise users, or unknowns are explicit and tolerable.
6. **Complexity** — Added complexity is justified by benefit.
7. **Compatibility** — At least one intended agent/platform path is documented; unverified paths are not overstated.
8. **Context / tokens** — Impact on context and tokens is understood directionally and does not systematically harm correctness.
9. **Reversibility** — Disable/uninstall path is known or clearly bounded.

Popular ≠ recommended.

A Tool may remain `evaluated` indefinitely if evidence is strong for documentation but weak for default adoption advice.

### Optional

Use when:

- The Tool is useful in some environments or workflows
- It is not a default recommendation
- Trade-offs (complexity, security, cost, compatibility) make blanket recommendation inappropriate

### Deprecated

Use when:

- Upstream is deprecated, abandoned in a way that creates risk, or superseded for harness purposes
- Continued new adoption would be harmful or misleading

Deprecated Tools may remain in the registry for historical reference with explicit warnings.

## Promotion rules

```text
candidate  → evaluated     requires research + documentation
evaluated  → recommended   requires recommendation checklist above
evaluated  → optional      when useful but not default
any        → deprecated    when continued adoption is discouraged
recommended → optional/deprecated when evidence or risk changes
```

Demote freely when new evidence weakens the case. Promote only with fresh verification notes (`verified_on`).

## Anti-patterns

- Recommending because a Tool is trending
- Filling unknown fields with optimistic guesses
- Treating vendor marketing benchmarks as harness-verified savings
- Assuming multi-agent compatibility from a single integration
- Ignoring telemetry, hook persistence, or supply-chain install risk
- Duplicating Tool docs inside Rules or Skills instead of linking

## Relationship to integrations

Registry status is independent of whether the harness has automated installers or adapters.

A Tool can be `recommended` in documentation before integration code exists.
A Tool can be integrated experimentally while still `evaluated` or `optional`.

This phase documents Tools only; it does not install them.
