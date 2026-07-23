---
id: security-audit
name: Defensive security audit
when_to_use: Auditing or hardening a Linux host, Docker/container stack, or network — blue-team review against a baseline.
agents: [security-auditor]
skills:
  - hardening-linux-endpoint-with-cis-benchmark
  - analyzing-linux-audit-logs-for-intrusion
  - detecting-rootkit-activity
  - hardening-docker-containers-for-production
  - performing-docker-bench-security-assessment
  - detecting-container-escape-attempts
  - analyzing-network-packets-with-scapy
  - configuring-suricata-for-network-monitoring
  - building-detection-rules-with-sigma
  - performing-nist-csf-maturity-assessment
  - implementing-secret-scanning-with-gitleaks
phases:
  - phase: Scope & baseline
    owner_agent: security-auditor
    skills: [performing-nist-csf-maturity-assessment]
    exit_criteria: Assets, threat model, and the baseline to audit against are stated.
    failure_modes: Auditing everything at once with no priority.
  - phase: Host hardening
    owner_agent: security-auditor
    skills: [hardening-linux-endpoint-with-cis-benchmark, analyzing-linux-audit-logs-for-intrusion, detecting-rootkit-activity]
    exit_criteria: Host findings ranked by severity with exact remediation commands.
    failure_modes: Applying changes before confirming they are safe on a live machine.
  - phase: Container review
    owner_agent: security-auditor
    skills: [hardening-docker-containers-for-production, performing-docker-bench-security-assessment, detecting-container-escape-attempts]
    exit_criteria: Docker daemon + image + runtime posture assessed (Docker Bench, escape checks).
    failure_modes: Ignoring 0.0.0.0-bound published ports and UFW rule state.
  - phase: Network & detection
    owner_agent: security-auditor
    skills: [analyzing-network-packets-with-scapy, configuring-suricata-for-network-monitoring, building-detection-rules-with-sigma]
    exit_criteria: Traffic/monitoring gaps identified; detection rules proposed.
    failure_modes: Detection without a hypothesis of what you are hunting.
  - phase: Supply chain & report
    owner_agent: security-auditor
    skills: [implementing-secret-scanning-with-gitleaks]
    exit_criteria: Secret/SBOM findings folded into one prioritized, read-only report.
    failure_modes: Reporting a low score from a tool run without sudo (false negative).
---

# Defensive security audit

Read-only-first posture review: **Scope → Host → Container → Network → Supply-chain report**. Owned by
the `security-auditor` agent, drawing on the installed defensive-security skills (and the far larger
`cybersecurity` set in the library for specialized techniques — forensics, YARA/Zeek, IR playbooks).

**Route in:** "audit / harden / is this secure / check open ports / container security." Diagnose and
report exact commands; confirm before any system-mutating change on a live host.
