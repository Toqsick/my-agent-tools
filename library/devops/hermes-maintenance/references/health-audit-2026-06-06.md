# Infra, Messaging & Gateway Health Audit — 2026-06-06

Template audit report. Follow the procedure in the "Infrastructure Health Audit"
section of the parent SKILL.md, then fill in results here.

## System Health

| Metric | Value | Status |
|--------|-------|--------|
| Uptime | | |
| CPU Load | | |
| Memory | | |
| Disk `/` | | |
| Swap | | |
| Temperature | | |
| Systemd (user) | | |
| Systemd (system) | | |

## Hermes Agent

| Check | Result | Status |
|-------|--------|--------|
| Version | | |
| Python | | |
| Config version | | |
| Model | | |
| Provider | | |
| Secret redaction | | |
| Linger | | |

## Gateway

| Platform | Status | Notes |
|----------|--------|-------|
| Telegram | | |
| Discord | | |
| Signal | | |
| WhatsApp | | |
| Slack | | |

## Config Audit

- [ ] model.provider explicit
- [ ] model.api_key not ollama
- [ ] model.default == model.model
- [ ] fallback_providers valid
- [ ] auxiliary.*.provider explicit
- [ ] telegram.dm_policy correct
- [ ] telegram.home_channel numeric (not @username)
- [ ] security.redact_secrets enabled
- [ ] Linger enabled

## Issues Found

| Severity | Issue | Fix |
|----------|-------|-----|
| 🔴 | | |
| 🟡 | | |
| 🟢 | | |
