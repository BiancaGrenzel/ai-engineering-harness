# Sandboxing

This Rule defines conceptual principles for safer execution. It does not implement a sandbox.

## Treat execution as privileged

Running commands, code, or agents can mutate systems, expose data, or reach external environments.

Prefer the least powerful execution path that completes the task.

## High-risk categories

Apply extra caution for:

- Destructive operations
- Arbitrary code execution
- Network access
- Broad filesystem access
- External environment access
- Production systems

## Isolation preferences

When available and appropriate, prefer:

- Scoped working directories
- Non-production environments
- Explicit allowlists of commands or paths
- Restricted network access
- Dry-run or plan modes before irreversible actions

## Authorization before impact

Do not perform irreversible or high-impact actions without clear authorization and a understood recovery path.
