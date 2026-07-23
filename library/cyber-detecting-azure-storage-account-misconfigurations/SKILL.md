---
name: cyber-detecting-azure-storage-account-misconfigurations
title: Detecting Azure Storage Account Misconfigurations
version: '1.0'
description: Audit Azure Blob and ADLS storage accounts for public access exposure, weak or long-lived SAS tokens, missing
  encryption at rest, disabled HTTPS-only traffic, and outdated TLS versions using the azure-mgmt-storage Python SDK.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-azure-
- storage-account-
- audit
- azure
- blob
keywords:
- detecting-azure-
- storage-account-
- audit
- azure
- blob
- adls
- storage
- accounts
related_skills:
- cyber-analyzing-cloud-storage-access-patterns
- cyber-detecting-misconfigured-azure-storage
- cyber-detecting-suspicious-oauth-application-consent
- cyber-auditing-azure-active-directory-configuration
- cyber-performing-service-account-audit
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: cloud-security
domain: cybersecurity
mitre_attack:
- T1530
- T1078.004
- T1619
- T1580
nist_csf:
- PR.IR-01
- ID.AM-08
- GV.SC-06
- DE.CM-01
tags:
- Azure
- storage-accounts
- blob-storage
- ADLS
- SAS-tokens
- encryption
- public-access
- cloud-misconfiguration
- azure-mgmt-storage
---


# Detecting Azure Storage Account Misconfigurations

## Overview

Azure Storage accounts are a frequent target for attackers due to misconfigured public access, long-lived SAS tokens, missing encryption, and outdated TLS versions. This skill uses the azure-mgmt-storage Python SDK with StorageManagementClient to enumerate all storage accounts in a subscription, inspect their security properties, list blob containers for public access settings, and generate a risk-scored audit report identifying critical misconfigurations.


## When to Use

- When investigating security incidents that require detecting azure storage account misconfigurations
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Python 3.9+ with `azure-mgmt-storage`, `azure-identity`
- Azure service principal with Reader role on target subscription
- Environment variables: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID

## Key Detection Areas

1. **Public blob access** — `allow_blob_public_access` enabled on storage account or individual containers set to Blob/Container access level
2. **HTTPS enforcement** — `enable_https_traffic_only` disabled, allowing unencrypted HTTP traffic
3. **Minimum TLS version** — accounts accepting TLS 1.0 or TLS 1.1 instead of minimum TLS 1.2
4. **Encryption at rest** — storage service encryption not enabled or missing customer-managed keys
5. **Network rules** — default action set to Allow instead of Deny, exposing storage to all networks
6. **SAS token risks** — account-level SAS with overly broad permissions or excessive lifetime

## Output

JSON report with per-account findings, severity ratings (Critical/High/Medium/Low), and remediation recommendations aligned with CIS Azure Benchmark controls.


