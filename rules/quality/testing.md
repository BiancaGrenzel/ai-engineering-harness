# Testing

Testing effort should match risk.

## Decide by risk factors

Consider:

- Likelihood of failure
- Impact of failure
- Complexity of the change
- Regression risk
- Criticality of the path

Higher risk warrants stronger testing.

## Prefer meaningful coverage

Test behavior that matters for correctness, security, and regressions.

Do not add low-value tests for ceremony.

## Tool neutrality

Do not require a specific testing framework or runner.

Use the project's existing test approach when one exists.

## Honest reporting

Report which tests were run and which were not.

If testing is incomplete, state what remains and why.
