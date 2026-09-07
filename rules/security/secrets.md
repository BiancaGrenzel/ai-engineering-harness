# Secrets

Protect sensitive credentials at all times.

## Sensitive material includes

- API keys
- Access tokens
- Passwords
- Private keys
- Session secrets
- Database credentials
- Cloud credentials

## Never

- Print secrets unnecessarily
- Put secrets in documentation
- Commit secrets
- Store secrets in Rules or Skills
- Expose secrets in logs, prompts, issues, or pull requests
- Copy credentials into context without a clear, justified need

## Prefer safe handling

Reference secret locations or variable names when possible.

If a secret is encountered accidentally, do not repeat it. Warn and help remove or rotate it through appropriate channels.
