---
name: system-security-audit
title: "System Security Audit (Router)"
description: "Use when assessing a Linux host for TPM, fwupd HSI, Secure Boot, SSH, firewall, open-port, service-hardening, or quick security-remediation gaps. ROUTER: delegates to security-audit-host (TPM/HSI/SecureBoot/SSH), security-audit-network (HTTP API Services/Connection Audit), security-audit-secrets (forensic secret-audit for cloud agents). NOT for one-off vulnerability scans without remediation context."
category: devops
version: '2.0'
created: '2026-07-23'
author: Yuno (Hermes)
lane: koenigin
agent: universal
trigger_keywords: ['security', 'audit', 'tpm', 'fwupd', 'ssh', 'firewall', 'hardening', 'linux', 'host', 'compliance']
keywords: ['security', 'audit', 'linux', 'host', 'tpm', 'fwupd', 'ssh', 'firewall', 'hardening', 'compliance', 'forensic']
related_skills: ['security-audit-host', 'security-audit-network', 'security-audit-secrets', 'host-security-audit', 'security-audit', 'local-ai-security-hygiene', 'claude-security-auditor']
last_curated: '2026-07-23'
curated_by: 'Yuno (split into sub-skills 2026-07-23)'

license: MIT
---

# System Security Audit (Router)

This is a router skill. Choose the sub-skill based on your intent:

## Security Audit — Host Layer (TPM, HSI, Secure Boot, SSH)

Use when assessing a Linux host for TPM, fwupd HSI, Secure Boot, SSH config, firewall, service-hardening gaps, or quick-fix cheatsheet. NOT for network/API audit (use security-audit-network) or secret-scanning (use security-audit-secrets).

## Security Audit — Network + API Services

Use when auditing HTTP API services, network connections, open ports, or running connection-drop audits. NOT for host-layer hardening (use security-audit-host).

## Security Audit — Forensic Secret-Scanning

Use when running forensic secret-audits for cloud-coding-agenten or scanning for leaked tokens/keys. NOT for host-hardening (use security-audit-host).


## Related Skills

- `security-audit-host`
- `security-audit-network`
- `security-audit-secrets`
- `host-security-audit`
- `security-audit`
- `local-ai-security-hygiene`
- `claude-security-auditor`
