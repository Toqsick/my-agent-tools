---
name: cyber-analyzing-office365-audit-logs-for-compromise
title: Analyzing Office365 Audit Logs For Compromise
version: '1.0'
description: Parse Office 365 Unified Audit Logs via Microsoft Graph API to detect email forwarding rule creation, inbox delegation,
  suspicious OAuth app grants, and other indicators of account compromise.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-
- audit-logs-for-
- compromise
- parse
- office
keywords:
- analyzing-
- audit-logs-for-
- compromise
- parse
- office
- unified
- audit
- logs
related_skills:
- cyber-analyzing-cloud-storage-access-patterns
- cyber-detecting-suspicious-oauth-application-consent
- cyber-implementing-web-application-logging-with-modsecurity
- cyber-analyzing-kubernetes-audit-logs
- cyber-extracting-windows-event-logs-artifacts
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: cloud-security
domain: cybersecurity
mitre_attack:
- T1114.002
- T1098.002
- T1556.006
- T1078.004
nist_csf:
- PR.IR-01
- ID.AM-08
- GV.SC-06
- DE.CM-01
tags:
- Office365
- Microsoft-Graph
- audit-logs
- email-compromise
- inbox-rules
- OAuth
- BEC
---


# Analyzing Office 365 Audit Logs for Compromise

## Overview

Business Email Compromise (BEC) attacks often leave traces in Office 365 audit logs: suspicious inbox rule creation, email forwarding to external addresses, mailbox delegation changes, and unauthorized OAuth application consent grants. This skill uses the Microsoft Graph API to query the Unified Audit Log, enumerate inbox rules across mailboxes, detect forwarding configurations, and identify compromised account indicators.


## When to Use

- When investigating security incidents that require analyzing office365 audit logs for compromise
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Azure AD app registration with `AuditLog.Read.All`, `MailboxSettings.Read`, `Mail.Read` (application permissions)
- Python 3.9+ with `msal`, `requests`
- Client secret or certificate for authentication
- Global Reader or Security Reader role

## Steps

1. Authenticate to Microsoft Graph using MSAL client credentials flow
2. Query Unified Audit Log for suspicious operations (Set-Mailbox, New-InboxRule)
3. Enumerate inbox rules across mailboxes and flag forwarding rules
4. Detect mailbox delegation changes (Add-MailboxPermission)
5. Identify OAuth consent grants to suspicious applications
6. Check for suspicious sign-in patterns from audit logs
7. Generate compromise indicator report with timeline

## Expected Output

- JSON report listing forwarding rules, delegation changes, OAuth grants, and suspicious audit events with risk scores
- Timeline of compromise indicators with affected mailboxes


