# Security Policy

## Scope

This repository contains:
- **Claude Code agent skills** — prompt/instruction files, no executable code that handles user data
- **MCP server configuration** — references to external tools via `${ENV_VAR}` placeholders only
- **CI/CD workflows** — GitHub Actions for validation and automation

Credentials and tokens are **never stored** in this repository. All secrets are environment variables.

## Reporting a Vulnerability

If you discover a security issue in this repository (e.g. a committed secret, a workflow that could be exploited, or a skill that leaks sensitive information), please:

1. **Do not open a public GitHub issue.**
2. Report privately via [GitHub's private vulnerability reporting](https://github.com/Toqsick/my-agent-tools/security/advisories/new).
3. Include:
   - Description of the issue
   - File path and line number (if applicable)
   - Potential impact
   - Suggested fix (optional)

## Response Time

| Severity | Expected response |
|---|---|
| Critical (leaked secret, RCE) | Within 24 hours |
| High (workflow injection, data exposure) | Within 72 hours |
| Medium / Low | Within 7 days |

## Supported Versions

Only the `main` branch is actively maintained. No versioned releases are supported for security patches.

## Known Non-Issues

- **Library skills with offensive security content** — intentional. The `library/` folder is a reference arsenal for defensive security research. It is never auto-executed.
- **`npx` package resolution at runtime** — packages are resolved from npm at tool startup, not pinned in lockfiles. Dependabot monitors for updates weekly.

## Secret Scanning

This repository runs [Gitleaks](https://github.com/gitleaks/gitleaks) on every push and pull request via `.github/workflows/secret-scanning.yml`. If a secret is accidentally committed, the workflow will catch it before it lands on `main`.
