---
name: cyber-detecting-email-account-compromise
title: Detecting Email Account Compromise
version: '1.0'
description: Detect compromised O365 and Google Workspace email accounts by analyzing inbox rule creation, suspicious sign-in
  locations, mail forwarding rules, and unusual API access patterns via Microsoft Graph and audit logs.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-email-
- account-
- compromise
- detect
- compromised
keywords:
- detecting-email-
- account-
- compromise
- detect
- compromised
- google
- workspace
- email
related_skills:
- productivity-suite
- google-oauth-setup
- google-workspace
- cyber-implementing-email-sandboxing-with-proofpoint
- cyber-hunting-for-supply-chain-compromise
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: incident-response
domain: cybersecurity
mitre_attack:
- T1486
- T1490
- T1070
- T1078
- T1566
nist_csf:
- RS.MA-01
- RS.MA-02
- RS.AN-03
- RC.RP-01
tags:
- email-compromise
- office365
- microsoft-graph
- bec
- inbox-rules
- sign-in-analysis
- account-takeover
---


# Detecting Email Account Compromise

## Overview

Email account compromise (EAC) is a prevalent attack vector where adversaries gain unauthorized access to mailboxes to exfiltrate sensitive data, conduct business email compromise (BEC), or establish persistence through inbox rule manipulation. Attackers commonly create forwarding rules to siphon emails, delete rules to hide evidence, or use OAuth tokens for persistent access. Detection relies on analyzing Microsoft 365 Unified Audit Logs, Azure AD sign-in logs for impossible travel or suspicious locations, inbox rule creation events (Set-InboxRule, New-InboxRule), and Microsoft Graph API access patterns. Key indicators include forwarding rules to external addresses, rules that delete or move messages matching keywords like "invoice" or "payment", and sign-ins from unusual user agents such as python-requests.


## When to Use

- When investigating security incidents that require detecting email account compromise
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Microsoft 365 with Unified Audit Logging enabled
- Azure AD P1/P2 for risk detection APIs
- Python 3.9+ with `requests`, `msal` libraries
- Microsoft Graph API application registration with Mail.Read, AuditLog.Read.All permissions
- Understanding of OAuth2 client credential flows

## Steps

1. Export audit logs or connect to Microsoft Graph API using MSAL authentication
2. Query inbox rules for all monitored mailboxes via `/users/{id}/mailFolders/inbox/messageRules`
3. Analyze rules for external forwarding (ForwardTo, RedirectTo external addresses)
4. Detect suspicious rule patterns: deletion rules, keyword-matching rules targeting financial terms
5. Query sign-in logs via `/auditLogs/signIns` for unusual locations and impossible travel
6. Check for suspicious user agent strings (python-requests, PowerShell, curl)
7. Identify OAuth application consent grants for suspicious third-party apps
8. Correlate findings across users to detect campaign-level compromise
9. Generate compromise indicators report with severity scores

## Expected Output

A JSON report listing compromised or suspicious accounts, malicious inbox rules detected, impossible travel events, suspicious OAuth grants, and recommended containment actions with severity ratings.


