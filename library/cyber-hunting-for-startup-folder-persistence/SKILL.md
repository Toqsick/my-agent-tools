---
name: cyber-hunting-for-startup-folder-persistence
title: Hunting For Startup Folder Persistence
version: '1.0'
description: Detect T1547.001 startup folder persistence by monitoring Windows startup directories for suspicious file creation,
  analyzing autoruns entries, and using Python watchdog for real-time filesystem monitoring.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- hunting-for-
- startup-folder-
- persistence
- detect
- startup
keywords:
- hunting-for-
- startup-folder-
- persistence
- detect
- startup
- folder
- monitoring
- windows
related_skills:
- cyber-analyzing-persistence-mechanisms-in-linux
- cyber-hunting-for-persistence-mechanisms-in-windows
- cyber-hunting-for-data-staging-before-exfiltration
- cyber-extracting-windows-event-logs-artifacts
- cyber-detecting-t1003-credential-dumping-with-edr
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
- T1547.001
- startup-folder
- persistence
- autoruns
- watchdog
- filesystem-monitoring
---


# Hunting for Startup Folder Persistence

## Overview

Attackers use Windows startup folders for persistence (MITRE ATT&CK T1547.001 — Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder). Files placed in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup` or `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup` execute automatically at user logon. This skill scans startup directories for suspicious files, monitors for real-time changes using Python watchdog, and analyzes file metadata to detect persistence implants.


## When to Use

- When investigating security incidents that require hunting for startup folder persistence
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Python 3.9+ with `watchdog`, `pefile` (optional for PE analysis)
- Access to Windows startup folders (user and all-users)
- Windows Event Logs for Event ID 4663 correlation (optional)

## Steps

1. Enumerate all files in user and system startup directories
2. Analyze file types, creation timestamps, and digital signatures
3. Flag suspicious file extensions (.bat, .vbs, .ps1, .lnk, .exe)
4. Check for recently created files (< 7 days) as potential implants
5. Monitor startup folders in real-time using watchdog FileSystemEventHandler
6. Correlate with known legitimate startup entries
7. Generate threat hunting report with T1547.001 MITRE mapping

## Expected Output

- JSON report listing all startup folder contents with risk scores, file metadata, and suspicious indicators
- Real-time monitoring alerts for new file creation in startup directories


