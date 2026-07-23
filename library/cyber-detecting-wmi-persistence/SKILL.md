---
name: cyber-detecting-wmi-persistence
title: Detecting Wmi Persistence
version: '1.0'
description: Detect WMI event subscription persistence by analyzing Sysmon Event IDs 19, 20, and 21 for malicious EventFilter,
  EventConsumer, and FilterToConsumerBinding creation.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-wmi-
- persistence
- detect
- event
- subscription
keywords:
- detecting-wmi-
- persistence
- detect
- event
- subscription
- analyzing
- sysmon
- malicious
related_skills:
- cyber-hunting-for-ntlm-relay-attacks
- cyber-extracting-windows-event-logs-artifacts
- cyber-detecting-t1055-process-injection-with-sysmon
- cyber-analyzing-cloud-storage-access-patterns
- cyber-hunting-for-domain-fronting-c2-traffic
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1546.003
- T1047
- T1059.001
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- threat-hunting
- wmi
- persistence
- sysmon
- t1546.003
- mitre-attack
- windows
- dfir
---


# Detecting WMI Persistence

## When to Use

- When hunting for WMI event subscription persistence (MITRE ATT&CK T1546.003)
- After detecting suspicious WMI activity in endpoint telemetry
- During incident response to identify attacker persistence mechanisms
- When Sysmon alerts trigger on Event IDs 19, 20, or 21
- During purple team exercises testing WMI-based persistence

## Prerequisites

- Sysmon v6.1+ deployed with WMI event logging enabled (Event IDs 19, 20, 21)
- Windows Security Event Log forwarding configured
- SIEM with Sysmon data ingested (Splunk, Elastic, Sentinel)
- PowerShell access for WMI enumeration on endpoints
- Sysinternals Autoruns for manual WMI subscription review

## Workflow

1. **Collect Telemetry**: Parse Sysmon Event IDs 19 (WmiEventFilter), 20 (WmiEventConsumer), 21 (WmiEventConsumerToFilter).
2. **Identify Suspicious Consumers**: Flag CommandLineEventConsumer and ActiveScriptEventConsumer types executing code.
3. **Analyze Event Filters**: Examine WQL queries in EventFilters for process start triggers or timer-based execution.
4. **Correlate Bindings**: Match FilterToConsumerBindings linking suspicious filters to consumers.
5. **Check Persistence Locations**: Query WMI namespaces root\subscription and root\default for active subscriptions.
6. **Validate Findings**: Cross-reference with known-good WMI subscriptions (SCCM, AV products).
7. **Document and Remediate**: Remove malicious subscriptions and update detection rules.

## Key Concepts

| Concept | Description |
|---------|-------------|
| Sysmon Event 19 | WmiEventFilter creation detected |
| Sysmon Event 20 | WmiEventConsumer creation detected |
| Sysmon Event 21 | WmiEventConsumerToFilter binding detected |
| T1546.003 | Event Triggered Execution: WMI Event Subscription |
| CommandLineEventConsumer | Executes system commands when filter triggers |
| ActiveScriptEventConsumer | Runs VBScript/JScript when filter triggers |

## Tools & Systems

| Tool | Purpose |
|------|---------|
| Sysmon | Windows event monitoring for WMI activity |
| WMI Explorer | GUI tool for browsing WMI namespaces |
| Autoruns | Sysinternals tool listing persistence mechanisms |
| PowerShell Get-WMIObject | Enumerate WMI event subscriptions |
| Splunk | SIEM analysis of Sysmon WMI events |
| Velociraptor | Endpoint WMI artifact collection |

## Output Format

```
Hunt ID: TH-WMI-[DATE]-[SEQ]
Technique: T1546.003
Host: [Hostname]
Event Type: [EventFilter|EventConsumer|Binding]
Consumer Type: [CommandLine|ActiveScript]
WQL Query: [Filter query text]
Command: [Executed command or script]
Risk Level: [Critical/High/Medium/Low]
Recommended Action: [Remove subscription, investigate lateral movement]
```


