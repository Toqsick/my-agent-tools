---
name: cyber-detecting-golden-ticket-forgery
title: Detecting Golden Ticket Forgery
version: '1.0'
description: Detect Kerberos Golden Ticket forgery by analyzing Windows Event ID 4769 for RC4 encryption downgrades (0x17),
  abnormal ticket lifetimes, and krbtgt account anomalies in Splunk and Elastic SIEM
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-golden
- ticket-forgery
- detect
- kerberos
- golden
keywords:
- detecting-golden
- ticket-forgery
- detect
- kerberos
- golden
- ticket
- forgery
- analyzing
related_skills:
- cyber-performing-active-directory-compromise-investigation
- cyber-exploiting-adcs-with-certipy
- cyber-analyzing-cloud-storage-access-patterns
- cyber-hunting-for-domain-fronting-c2-traffic
- cyber-detecting-kerberoasting-attacks
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-detection
domain: cybersecurity
mitre_attack:
- T1078
- T1190
- T1059
- T1003
- T1110
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-06
- ID.RA-05
tags:
- golden-ticket
- kerberos
- active-directory
- mimikatz
- splunk
- credential-theft
- windows-security
---


# Detecting Golden Ticket Forgery

## Overview

A Golden Ticket attack (MITRE ATT&CK T1558.001) involves forging a Kerberos Ticket Granting Ticket (TGT) using the krbtgt account NTLM hash, granting unrestricted access to any service in the Active Directory domain. This skill detects Golden Ticket usage by analyzing Event ID 4769 for RC4 encryption type (0x17) in environments enforcing AES, identifying tickets with abnormal lifetimes exceeding domain policy, correlating TGS requests with missing corresponding TGT requests (Event ID 4768), and detecting krbtgt password age anomalies.


## When to Use

- When investigating security incidents that require detecting golden ticket forgery
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Windows Domain Controller with Kerberos audit logging enabled
- Splunk or Elastic SIEM ingesting Windows Security event logs
- Python 3.8+ for offline event log analysis
- Knowledge of domain Kerberos encryption policy (AES vs RC4)

## Steps

1. Audit domain Kerberos encryption policy to establish AES-only baseline
2. Forward Event IDs 4768 and 4769 to SIEM platform
3. Detect RC4 (0x17) encryption in TGS requests where AES is enforced
4. Identify TGS requests without corresponding TGT requests (forged ticket indicator)
5. Alert on ticket lifetimes exceeding MaxTicketAge domain policy
6. Monitor krbtgt account password age and last reset date
7. Correlate findings with host/user context for risk scoring

## Expected Output

JSON report with Golden Ticket indicators including RC4 downgrades, orphaned TGS requests, abnormal ticket lifetimes, and risk-scored alerts with MITRE ATT&CK technique mapping.


