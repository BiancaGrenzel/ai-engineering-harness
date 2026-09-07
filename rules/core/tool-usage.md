# Tool Usage

Tools are capabilities, not goals. Use a tool only when it clearly benefits the current task.

## Prefer targeted operations

Prefer narrow queries and scoped commands over broad dumps of repository or system state.

Prefer searching for a specific symbol or concept over reading unrelated files.

## Reduce unnecessary output

Avoid loading large tool output into context when a filtered or summarized result is enough.

Prefer structured output when available.

## Consider context cost

Before using a tool, ask:

1. What information or action is required?
2. Is there a less expensive way to obtain it?
3. Does the tool introduce security or privacy risk?
4. Does the result need to enter model context?
5. Can the output be filtered?

## Do not use tools without need

Do not run tools for ceremony, speculation, or habit.

## Destructive operations require authorization

Do not perform destructive operations without appropriate authorization.

Examples: deleting files, dropping databases, resetting repositories, overwriting important configuration, force pushing, production deployment, destructive infrastructure changes.
