---
name: cyber-detecting-sql-injection-via-waf-logs
title: Detecting Sql Injection Via Waf Logs
version: '1.0'
description: Analyze WAF (ModSecurity/AWS WAF/Cloudflare) logs to detect SQL injection attack campaigns. Parses ModSecurity
  audit logs and JSON WAF event logs to identify SQLi patterns (UNION SELECT, OR 1=1, SLEEP(), BENCHMARK()), tracks attack
  sources, correlates multi-stage injection attempts, and generates incident reports with OWASP classification.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-sql-
- injection-via-
- waf-logs
- analyze
- modsecurity
keywords:
- detecting-sql-
- injection-via-
- waf-logs
- analyze
- modsecurity
- cloudflare
- logs
- detect
related_skills:
- cyber-implementing-web-application-logging-with-modsecurity
- cyber-detecting-network-anomalies-with-zeek
- cyber-extracting-windows-event-logs-artifacts
- cyber-analyzing-cloud-storage-access-patterns
- cyber-analyzing-tls-certificate-transparency-logs
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: security-operations
domain: cybersecurity
mitre_attack:
- T1190
- T1505.003
- T1059.007
nist_csf:
- DE.CM-01
- RS.MA-01
- GV.OV-01
- DE.AE-02
tags:
- waf-log-analysis
- sql-injection-detection
- modsecurity
- aws-waf
- cloudflare-waf
- web-application-security
---


# Detecting SQL Injection via WAF Logs


## When to Use

- When investigating security incidents that require detecting sql injection via waf logs
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install requests`
2. Collect WAF logs (ModSecurity audit log, AWS WAF JSON logs, or Cloudflare firewall events).
3. Run the agent to parse and analyze:
   - Detect SQLi payloads via 15+ regex patterns
   - Classify attacks by OWASP injection type (classic, blind, time-based, UNION-based)
   - Identify persistent attackers by IP clustering
   - Correlate multi-request injection campaigns
   - Calculate attack success probability based on response codes

```bash
python scripts/agent.py --log-file /var/log/modsec_audit.log --format modsecurity --output sqli_report.json
```

## Examples

### ModSecurity SQLi Detection
```
Rule 942100 triggered: SQL Injection Attack Detected via libinjection
URI: /api/users?id=1' UNION SELECT username,password FROM users--
Source IP: 203.0.113.42 (47 requests in 5 minutes)
Classification: UNION-based SQLi campaign
```


