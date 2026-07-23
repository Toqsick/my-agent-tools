---
name: cyber-detecting-privilege-escalation-attempts
title: Detecting Privilege Escalation Attempts
version: '1.0'
description: Detect privilege escalation attempts including token manipulation, UAC bypass, unquoted service paths, kernel
  exploits, and sudo/doas abuse across Windows and Linux.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-
- privilege-
- escalation-
- attempts
- detect
keywords:
- detecting-
- privilege-
- escalation-
- attempts
- detect
- privilege
- escalation
- including
related_skills:
- cyber-detecting-insider-threat-behaviors
- cyber-securing-github-actions-workflows
- cyber-detecting-broken-object-property-level-authorization
- cyber-auditing-kubernetes-cluster-rbac
- cyber-performing-cloud-native-forensics-with-falco
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1046
- T1057
- T1082
- T1083
- T1068
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- threat-hunting
- mitre-attack
- privilege-escalation
- token-manipulation
- uac-bypass
- proactive-detection
---


# Detecting Privilege Escalation Attempts

## When to Use

- When proactively hunting for indicators of detecting privilege escalation attempts in the environment
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
| T1134 | Access Token Manipulation |
| T1548.002 | UAC Bypass |
| T1068 | Exploitation for Privilege Escalation |
| T1574.009 | Unquoted Service Path |

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

1. **Scenario 1**: Potato exploit for SYSTEM token impersonation
2. **Scenario 2**: Fodhelper.exe UAC bypass technique
3. **Scenario 3**: PrintSpoofer privilege escalation from service to SYSTEM
4. **Scenario 4**: CVE kernel exploit for local privilege escalation

## Output Format

```
Hunt ID: TH-DETECT-[DATE]-[SEQ]
Technique: T1134
Host: [Hostname]
User: [Account context]
Evidence: [Log entries, process trees, network data]
Risk Level: [Critical/High/Medium/Low]
Confidence: [High/Medium/Low]
Recommended Action: [Containment, investigation, monitoring]
```


