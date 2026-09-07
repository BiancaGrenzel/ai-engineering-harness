# Permissions

Permissions are conceptual capability levels. Grant them only when needed.

## Levels

| Level | Meaning |
| --- | --- |
| READ | Inspect files, docs, or state without mutation |
| WRITE | Modify repository or local artifacts |
| EXECUTE | Run commands or code |
| NETWORK | Access external systems or the public internet |
| DEPLOY | Change production or release-facing systems |

Risk generally increases from READ to DEPLOY.

## Independent grants

Do not assume that one permission implies another.

Examples:

- WRITE does not imply EXECUTE
- EXECUTE does not imply NETWORK
- NETWORK does not imply DEPLOY

## Minimal request

Ask for or use the lowest permission level that can complete the task safely.

Escalate only when the task requires it and authorization is clear.
