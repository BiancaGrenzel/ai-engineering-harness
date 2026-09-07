# Tool Evaluation Criteria

How the harness evaluates a Tool before changing its registry status.

These criteria are **qualitative**. This phase does not define a mandatory numeric score.

## Purpose

Evaluation answers:

1. Does this Tool solve a real problem for agent-assisted engineering?
2. Is the evidence strong enough to document and classify it honestly?
3. Should the harness treat it as candidate, evaluated, recommended, optional, or deprecated?

Evaluation is not marketing review. Prefer primary sources and reproducible claims.

## Criteria

### Utility

- Does it solve a concrete engineering or agent-workflow problem?
- Is the problem common enough to justify catalog cost?
- Can the same outcome be achieved with simpler existing means?

### Reliability

- Is behavior predictable under normal use?
- Are failure modes documented?
- Does upstream communicate breaking changes responsibly?

Evidence may include release cadence, issue handling, and documented limitations. Absence of evidence is not proof of reliability.

### Maintenance

- Is the project actively maintained?
- Are security issues addressable?
- Is there a clear upstream source of truth?

Stale projects can still be documented as `optional` or `deprecated` when historically relevant.

### Security

- What is the security level under [`docs/architecture/tools.md`](../architecture/tools.md)?
- Does it require EXECUTE, NETWORK, credential access, or production reach?
- Are install and update paths trustworthy enough for the claimed risk?

### Privacy

- What data is read, stored, or transmitted?
- Is telemetry opt-in or opt-out?
- Are secrets or repository contents at risk of exposure?

### Context efficiency

- Does typical output stay small, moderate, or large?
- Is output filterable or structured?
- Could output become unbounded?

### Token efficiency

- Does the Tool reduce, increase, or leave token use unchanged?
- Through what mechanism (filtering, summarization, caching, model calls, verbosity)?
- Are savings claims labeled as official, observed, or unverified?

### Performance

- What is the runtime or latency overhead when known?
- Does it block critical paths?
- If unknown, record `Not verified`.

### Cost

Separate:

- Software cost
- Infrastructure cost
- API / model cost
- Operational cost

Do not invent prices. Unknown costs remain unknown.

### Compatibility

- Which platforms are claimed?
- Which agents are claimed, and with what integration method?
- What has the harness actually verified?

### Complexity

- How much new surface area does adoption add (hooks, config, mental model)?
- Does it complicate debugging when outputs are filtered or rewritten?
- Is the complexity proportional to the benefit?

### Reversibility

- Can the Tool be disabled or uninstalled cleanly?
- Does it leave durable hooks, config, or local databases?
- Is rollback documented by upstream?

### Observability

- Can users see what the Tool did (logs, savings reports, dry-run, tee/raw recovery)?
- Can agents detect when filtering removed necessary signal?

## Evidence standards

Prefer:

1. Official documentation
2. Official repository
3. License and security policy files
4. Versioned releases

Treat community posts as secondary. Do not promote marketing numbers to facts.

For each material claim, one of:

- Verified from official source (cite it)
- Official benchmark (cite it; do not equate to harness observation)
- Not verified

## Outcome of evaluation

After evaluation, set status using [`recommendation-policy.md`](recommendation-policy.md) and publish:

1. Tool page from [`TOOL_TEMPLATE.md`](TOOL_TEMPLATE.md)
2. Registry row in [`registry.md`](registry.md)
3. Category README update when the Tool is the first in that category

## Out of scope for this phase

- Numeric scoring models
- Automated ranking
- Automatic installation
- Continuous upstream monitoring
