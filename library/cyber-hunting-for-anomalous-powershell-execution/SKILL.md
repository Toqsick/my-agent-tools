---
name: cyber-hunting-for-anomalous-powershell-execution
title: Hunting For Anomalous Powershell Execution
version: '1.0'
description: 'Hunt for malicious PowerShell activity by analyzing Script Block Logging (Event 4104), Module Logging (Event
  4103), and process creation events. The analyst parses Windows Event Log EVTX files to detect obfuscated commands, AMSI
  bypass attempts, encoded payloads, credential dumping keywords, and suspicious download cradles. Activates for requests
  involving PowerShell threat hunting, script block analysis, encoded command detection, or AMSI bypass identification.

  '
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- hunting-for-
- anomalous-
- powershell-
- execution
- hunt
keywords:
- hunting-for-
- anomalous-
- powershell-
- execution
- hunt
- malicious
- powershell
- activity
related_skills:
- cyber-hunting-for-shadow-copy-deletion
- cyber-hunting-bootkits-in-efi-system-partition
- cyber-detecting-dll-sideloading-attacks
- cyber-performing-memory-forensics-with-volatility3
- cyber-configuring-snort-ids-for-intrusion-detection
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1046
- T1057
- T1082
- T1083
- T1003
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- powershell
- script-block-logging
- event-4104
- amsi
- threat-hunting
- evtx
- obfuscation
---


# Hunting for Anomalous PowerShell Execution

## Overview

PowerShell Script Block Logging (Event ID 4104) records the full deobfuscated script text
executed on a Windows endpoint, making it the primary data source for hunting malicious
PowerShell. Combined with Module Logging (4103) and process creation events, analysts can
detect encoded commands, AMSI bypass patterns, download cradles, credential theft tools,
and fileless attack techniques even when the attacker uses obfuscation layers.


## When to Use

- When investigating security incidents that require hunting for anomalous powershell execution
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Windows Event Log exports (.evtx) from Microsoft-Windows-PowerShell/Operational
- Python 3.8+ with python-evtx and lxml libraries
- Script Block Logging enabled via Group Policy
- Understanding of common PowerShell attack techniques

## Steps

1. Parse EVTX files extracting Event 4104 script block text and metadata
2. Reassemble multi-part script blocks using ScriptBlock ID correlation
3. Scan script text for AMSI bypass indicators and obfuscation patterns
4. Detect encoded command execution and base64 payloads
5. Identify download cradles, credential dumping, and lateral movement commands
6. Score and prioritize findings by threat severity

## Expected Output

```json
{
  "total_events": 1247,
  "suspicious_events": 23,
  "amsi_bypass_attempts": 2,
  "encoded_commands": 8,
  "download_cradles": 5,
  "credential_access": 3
}
```


