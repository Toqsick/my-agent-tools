---
name: cyber-analyzing-web-server-logs-for-intrusion
title: Analyzing Web Server Logs For Intrusion
version: '1.0'
description: Parse Apache and Nginx access logs to detect SQL injection attempts, local file inclusion, directory traversal,
  web scanner fingerprints, and brute-force patterns. Uses regex-based pattern matching against OWASP attack signatures, GeoIP
  enrichment for source attribution, and statistical anomaly detection for request frequency and response size outliers.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-web-
- server-logs-for-
- intrusion
- parse
- apache
keywords:
- analyzing-web-
- server-logs-for-
- intrusion
- parse
- apache
- nginx
- access
- logs
related_skills:
- cyber-analyzing-api-gateway-access-logs
- cyber-analyzing-cloud-storage-access-patterns
- cyber-performing-cloud-log-forensics-with-athena
- cyber-implementing-cloud-trail-log-analysis
- cyber-building-c2-redirector-infrastructure
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: security-operations
domain: cybersecurity
mitre_attack:
- T1190
- T1059.007
- T1110
- T1595.002
- T1505.003
nist_csf:
- DE.CM-01
- RS.MA-01
- GV.OV-01
- DE.AE-02
tags:
- web-log-analysis
- apache-logs
- nginx-logs
- sql-injection-detection
- lfi-detection
- directory-traversal
- intrusion-detection
---


# Analyzing Web Server Logs for Intrusion


## When to Use

- When investigating security incidents that require analyzing web server logs for intrusion
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install geoip2 user-agents`
2. Collect web server access logs in Combined Log Format (Apache) or Nginx default format.
3. Parse each log entry extracting: IP, timestamp, method, URI, status code, response size, user-agent, referer.
4. Apply detection rules:
   - SQL injection: `UNION SELECT`, `OR 1=1`, `' OR '`, hex encoding patterns
   - LFI/Path traversal: `../`, `/etc/passwd`, `/proc/self`, `php://filter`
   - XSS: `<script>`, `javascript:`, `onerror=`, `onload=`
   - Scanner signatures: nikto, sqlmap, dirbuster, gobuster, wfuzz user-agents
   - Brute force: >50 POST requests to login endpoints from same IP in 5 minutes
5. Enrich with GeoIP data and generate a prioritized findings report.

```bash
python scripts/agent.py --log-file /var/log/nginx/access.log --geoip-db GeoLite2-City.mmdb --output web_intrusion_report.json
```

## Examples

### Detect SQLi in URI
```
192.168.1.100 - - [15/Jan/2024:10:30:45 +0000] "GET /products?id=1' UNION SELECT username,password FROM users-- HTTP/1.1" 200 4532
```

### Scanner User-Agent Detection
```
Nikto/2.1.6, sqlmap/1.7, DirBuster-1.0-RC1, gobuster/3.1.0
```


