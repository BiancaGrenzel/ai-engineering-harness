# Token Optimization

Tools that reduce, measure, or control token consumption in agent workflows.

## What belongs here

Capabilities whose primary value is lowering wasted tokens or making token use visible, for example:

- Command-output filters and compressors
- Prompt or context compaction utilities
- Token usage measurement helpers tightly coupled to savings workflows

Related but distinct categories:

- Context selection/loading utilities → [`../context/`](../context/)
- Model eval cost tracking as part of broader observability → may fit [`../observability/`](../observability/) if token savings is not the primary purpose

## Classification criteria

Place a Tool here when:

1. The main problem statement is token waste or token cost.
2. The mechanism acts on prompts, tool output, caching, routing, or measurement for that purpose.
3. Documentation can state token impact `effect` and `magnitude` with evidence or explicit unknowns.

## Tools in this category

| Tool | Status | Notes |
| --- | --- | --- |
| [RTK](rtk.md) | evaluated | CLI proxy that filters/compresses command output before it reaches the model |

No other Tools are cataloged in this category yet.
