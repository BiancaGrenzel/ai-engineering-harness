# Reliability

Production systems should fail in predictable, recoverable ways.

## Core principles

Prefer:

- Predictable behavior under normal and failure conditions
- Explicit error handling
- Timeouts for operations that can hang
- Retries only when safe and useful
- Fallbacks when a degraded path is better than hard failure
- Idempotency when retries or duplicate requests are possible

## Architecture neutrality

Do not assume a specific architecture, runtime, or cloud provider.

Apply reliability controls that fit the system under change.

## Avoid silent failure

Errors should be visible to operators or callers in a useful form.

Do not swallow failures without a deliberate reason.
