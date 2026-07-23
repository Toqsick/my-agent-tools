---
name: cyber-hunting-credential-stuffing-attacks
title: Hunting Credential Stuffing Attacks
version: '1.0'
description: 'Detects credential stuffing attacks by analyzing authentication logs for login velocity anomalies, ASN diversity,
  password spray patterns, and geographic distribution of failed logins. Uses statistical analysis on Splunk or raw log data.
  Use when investigating account takeover campaigns or building detection rules for auth abuse.

  '
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- hunting-
- credential-
- stuffing-attacks
- detects
- credential
keywords:
- hunting-
- credential-
- stuffing-attacks
- detects
- credential
- stuffing
- attacks
- analyzing
related_skills:
- cyber-securing-github-actions-workflows
- cyber-performing-container-escape-detection
- cyber-conducting-phishing-incident-response
- cyber-hunting-for-ntlm-relay-attacks
- cyber-detecting-fileless-attacks-on-endpoints
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: security-operations
domain: cybersecurity
mitre_attack:
- T1078
- T1190
- T1059
- T1003
- T1110
nist_csf:
- DE.CM-01
- RS.MA-01
- GV.OV-01
- DE.AE-02
tags:
- credential-stuffing
- authentication-logs
- login-anomaly
- asn-analysis
- threat-hunting
- account-takeover
---


# Hunting Credential Stuffing Attacks


## When to Use

- When investigating security incidents that require hunting credential stuffing attacks
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Analyze authentication logs to detect credential stuffing by identifying patterns
of distributed login failures, high IP diversity, and suspicious ASN distribution.

```python
import pandas as pd
from collections import Counter

# Load auth logs
df = pd.read_csv("auth_logs.csv", parse_dates=["timestamp"])

# Credential stuffing indicator: many IPs trying few accounts
ip_per_account = df[df["status"] == "failed"].groupby("username")["source_ip"].nunique()
accounts_under_attack = ip_per_account[ip_per_account > 50]
```

Key detection indicators:
1. High unique source IPs per failed username
2. Low success rate across many accounts (< 1%)
3. ASN concentration from cloud/proxy providers
4. Geographic impossibility (same account, distant locations)
5. User-agent uniformity across distributed IPs

## Examples

```python
# Password spray: one password tried across many accounts
spray = df[df["status"] == "failed"].groupby(["source_ip", "password_hash"]).agg(
    accounts=("username", "nunique")).reset_index()
sprays = spray[spray["accounts"] > 10]
```


