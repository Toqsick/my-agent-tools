---
name: cyber-detecting-email-forwarding-rules-attack
title: Detecting Email Forwarding Rules Attack
version: '1.0'
description: Detect malicious email forwarding rules created by adversaries to maintain persistent access to email communications
  for intelligence collection and BEC attacks.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-email-
- forwarding-rules
- attack
- detect
- malicious
keywords:
- detecting-email-
- forwarding-rules
- attack
- detect
- malicious
- email
- forwarding
- rules
related_skills:
- cyber-detecting-email-account-compromise
- cyber-implementing-email-sandboxing-with-proofpoint
- cyber-detecting-qr-code-phishing-with-email-security
- cyber-implementing-semgrep-for-custom-sast-rules
- cyber-implementing-web-application-logging-with-modsecurity
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1046
- T1057
- T1082
- T1083
- T1547
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- threat-hunting
- mitre-attack
- email-forwarding
- persistence
- bec
- t1114
- proactive-detection
---


# Detecting Email Forwarding Rules Attack

## When to Use

- When proactively hunting for indicators of detecting email forwarding rules attack in the environment
- After threat intelligence indicates active campaigns using these techniques
- During incident response to scope compromise related to these techniques
- When EDR or SIEM alerts trigger on related indicators
- During periodic security assessments and purple team exercises

## Prerequisites

- EDR platform with process and network telemetry (CrowdStrike, MDE, SentinelOne)
- SIEM with relevant log data ingested (Splunk, Elastic, Sentinel)
- Sysmon deployed with comprehensive configuration
- Windows Security Event Log forwarding enabled
- Threat intelligence feeds for IOC correlation

## Workflow

1. **Formulate Hypothesis**: Define a testable hypothesis based on threat intelligence or ATT&CK gap analysis.
2. **Identify Data Sources**: Determine which logs and telemetry are needed to validate or refute the hypothesis.
3. **Execute Queries**: Run detection queries against SIEM and EDR platforms to collect relevant events.
4. **Analyze Results**: Examine query results for anomalies, correlating across multiple data sources.
5. **Validate Findings**: Distinguish true positives from false positives through contextual analysis.
6. **Correlate Activity**: Link findings to broader attack chains and threat actor TTPs.
7. **Document and Report**: Record findings, update detection rules, and recommend response actions.

## Key Concepts

| Concept | Description |
|---------|-------------|
| T1114.003 | Email Forwarding Rule |
| T1114.002 | Remote Email Collection |
| T1098.002 | Additional Email Delegate Permissions |

## Tools & Systems

| Tool | Purpose |
|------|---------|
| CrowdStrike Falcon | EDR telemetry and threat detection |
| Microsoft Defender for Endpoint | Advanced hunting with KQL |
| Splunk Enterprise | SIEM log analysis with SPL queries |
| Elastic Security | Detection rules and investigation timeline |
| Sysmon | Detailed Windows event monitoring |
| Velociraptor | Endpoint artifact collection and hunting |
| Sigma Rules | Cross-platform detection rule format |

## Common Scenarios

1. **Scenario 1**: BEC actor creating forwarding rule to external email
2. **Scenario 2**: Compromised account with rule deleting security alerts
3. **Scenario 3**: Inbox rule forwarding CEO emails to attacker mailbox
4. **Scenario 4**: OAuth app abuse creating transport rules for data collection

## Output Format

```
Hunt ID: TH-DETECT-[DATE]-[SEQ]
Technique: T1114.003
Host: [Hostname]
User: [Account context]
Evidence: [Log entries, process trees, network data]
Risk Level: [Critical/High/Medium/Low]
Confidence: [High/Medium/Low]
Recommended Action: [Containment, investigation, monitoring]
```


