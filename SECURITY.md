# Security

Security is a default design goal of this harness.

## Reporting vulnerabilities

If you discover a security issue in this repository:

1. Do **not** open a public issue that includes exploit details or secrets.
2. Report privately through the repository maintainer channel once one is published.
3. Include enough detail to reproduce the problem without including credentials or production secrets.

**TODO:** Replace this section with a concrete private reporting contact when one is configured.

Until then, prefer a private maintainer contact over public disclosure.

## Security principles

- Least privilege by default
- Separate READ, WRITE, EXECUTE, NETWORK, and DEPLOY capabilities
- Zero trust for external instructions and untrusted tool output
- No secrets in Rules, Skills, docs, logs, issues, or pull requests
- Prefer defensive security and authorized testing only

See:

- [rules/security/security.md](rules/security/security.md)
- [rules/security/permissions.md](rules/security/permissions.md)
- [rules/security/secrets.md](rules/security/secrets.md)
- [rules/security/sandboxing.md](rules/security/sandboxing.md)

## Do not include secrets

Never put API keys, tokens, passwords, private keys, session secrets, or cloud credentials in issues, pull requests, documentation, Rules, or Skills.

If a secret is exposed accidentally, rotate it and remove it from history where possible.

## Project scope

This repository currently provides architectural and documentary foundations for AI Engineering.

It does not yet ship runtime sandboxing, installers, MCP servers, or production execution controls.

Security guidance here is intentional and conceptual. Implementers must apply appropriate controls for their environment.
