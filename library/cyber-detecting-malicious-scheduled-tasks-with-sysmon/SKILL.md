---
name: cyber-detecting-malicious-scheduled-tasks-with-sysmon
title: Detecting Malicious Scheduled Tasks With Sysmon
version: '1.0'
description: 'Detect malicious scheduled task creation and modification using Sysmon Event IDs 1 (Process Create for schtasks.exe),
  11 (File Create for task XML), and Windows Security Event 4698/4702. The analyst correlates task creation with suspicious
  parent processes, public directory paths, and encoded command arguments to identify persistence and lateral movement via
  scheduled tasks. Activates for requests involving scheduled task detection, Sysmon persistence hunting, or T1053.005 Scheduled
  Task/Job analysis.

  '
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-
- malicious-
- scheduled-tasks-
- with-sysmon
- detect
keywords:
- detecting-
- malicious-
- scheduled-tasks-
- with-sysmon
- detect
- malicious
- scheduled
- task
related_skills:
- cyber-detecting-dll-sideloading-attacks
- cyber-performing-second-order-sql-injection
- cyber-detecting-wmi-persistence
- cyber-hunting-for-suspicious-scheduled-tasks
- cyber-hunting-for-scheduled-task-persistence
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1046
- T1057
- T1082
- T1083
- T1021
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- sysmon
- scheduled-tasks
- persistence
- detection
- threat-hunting
- windows-security
---


# Detecting Malicious Scheduled Tasks with Sysmon

## Overview

Adversaries abuse Windows Task Scheduler (schtasks.exe, at.exe) for persistence (T1053.005)
and lateral movement. Sysmon Event ID 1 captures schtasks.exe process creation with full
command-line arguments, while Event ID 11 captures task XML files written to
C:\Windows\System32\Tasks\. Windows Security Event 4698 logs task registration details.
This skill covers building detection rules that correlate these events to identify
malicious scheduled tasks created from suspicious paths, with encoded payloads, or
targeting remote systems.


## When to Use

- When investigating security incidents that require detecting malicious scheduled tasks with sysmon
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Sysmon installed with a detection-focused configuration (e.g., SwiftOnSecurity or Olaf Hartong)
- Windows Event Log forwarding to SIEM (Splunk, Elastic, or Sentinel)
- PowerShell ScriptBlock Logging enabled (Event 4104)

## Steps

1. Configure Sysmon to log Event IDs 1, 11, 12, 13 with task-related filters
2. Build detection rules for schtasks.exe /create with suspicious arguments
3. Correlate Event 4698 (task registered) with Sysmon Event 1 (process create)
4. Hunt for tasks executing from public directories or with encoded commands
5. Alert on remote task creation (schtasks /s) for lateral movement detection

## Expected Output

```
[CRITICAL] Suspicious Scheduled Task Detected
  Task: \Microsoft\Windows\UpdateCheck
  Command: powershell.exe -enc SQBuAHYAbwBrAGUALQBXAGUAYgBSAGU...
  Created By: DOMAIN\compromised_user
  Parent Process: cmd.exe (PID 4532)
  Source: \\192.168.1.50 (remote creation)
  MITRE: T1053.005 - Scheduled Task/Job
```


