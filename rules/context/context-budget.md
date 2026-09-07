# Context Budget

Context is a limited engineering resource.

## What counts as context

Account for:

- Number of files loaded
- Size of files
- Tool output
- Conversation history
- Documentation
- Logs
- Search results

## Optimize usefulness, not just size

The goal is not merely to use fewer tokens.

Maximize:

```text
useful context / total context
```

Reduce noise. Keep signal.

## Correctness first

Never remove context required for correctness merely to save tokens.

Token efficiency must not compromise accuracy, security, or verification quality.
