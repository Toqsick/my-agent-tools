---
name: cyber-hunting-for-unusual-service-installations
title: Hunting For Unusual Service Installations
version: '1.0'
description: Detect suspicious Windows service installations (MITRE ATT&CK T1543.003) by parsing System event logs for Event
  ID 7045, analyzing service binary paths, and identifying indicators of persistence mechanisms.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- hunting-for-
- unusual-service-
- installations
- detect
- suspicious
keywords:
- hunting-for-
- unusual-service-
- installations
- detect
- suspicious
- windows
- service
- mitre
related_skills:
- cyber-detecting-privilege-escalation-attempts
- cyber-hunting-for-startup-folder-persistence
- cyber-implementing-email-sandboxing-with-proofpoint
- cyber-analyzing-persistence-mechanisms-in-linux
- cyber-performing-memory-forensics-with-volatility3-plugins
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
- T1543.003
- service-installation
- persistence
- Event-7045
- Sysmon
- Windows-services
---


# Hunting for Unusual Service Installations

## Overview

Attackers frequently install malicious Windows services for persistence and privilege escalation (MITRE ATT&CK T1543.003 — Create or Modify System Process: Windows Service). Event ID 7045 in the System event log records every new service installation. This skill parses .evtx log files to extract service installation events, flags suspicious binary paths (temp directories, PowerShell, cmd.exe, encoded commands), and correlates with known attack patterns.


## When to Use

- When investigating security incidents that require hunting for unusual service installations
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Python 3.9+ with `python-evtx`, `lxml`
- Windows System event log (.evtx) files
- Access to live System event log (optional, for real-time monitoring)
- Sysmon logs for enhanced process tracking (optional)

## Steps

1. Parse System.evtx for Event ID 7045 (new service installed)
2. Extract service name, binary path, service type, and account
3. Flag services with suspicious binary paths (temp dirs, encoded commands)
4. Detect PowerShell-based service creation patterns
5. Identify services running as LocalSystem with unusual paths
6. Cross-reference with known legitimate service baselines
7. Generate threat hunting report with MITRE ATT&CK T1543.003 mapping

## Expected Output

- JSON report listing all new service installations with risk scores, suspicious indicators, and remediation recommendations
- Timeline of service installation events with binary path analysis


