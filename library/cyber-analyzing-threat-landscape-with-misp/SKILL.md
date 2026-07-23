---
name: cyber-analyzing-threat-landscape-with-misp
title: Analyzing Threat Landscape With Misp
version: '1.0'
description: Analyze the threat landscape using MISP (Malware Information Sharing Platform) by querying event statistics,
  attribute distributions, threat actor galaxy clusters, and tag trends over time. Uses PyMISP to pull event data, compute
  IOC type breakdowns, identify top threat actors and malware families, and generate threat landscape reports with temporal
  trends.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-threat
- landscape-with-
- misp
- analyze
- threat
keywords:
- analyzing-threat
- landscape-with-
- misp
- analyze
- threat
- landscape
- using
- malware
related_skills:
- cyber-performing-memory-forensics-with-volatility3-plugins
- cyber-performing-ip-reputation-analysis-with-shodan
- cyber-analyzing-apt-group-with-mitre-navigator
- cyber-reverse-engineering-dotnet-malware-with-dnspy
- cyber-implementing-security-information-sharing-with-stix2
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-intelligence
domain: cybersecurity
mitre_attack:
- T1566
- T1071.001
- T1568
- T1583.001
- T1102
nist_csf:
- ID.RA-01
- ID.RA-05
- DE.CM-01
- DE.AE-02
tags:
- threat-intelligence
- misp
- threat-landscape
- ioc-analysis
- cti
- threat-sharing
---


# Analyzing Threat Landscape with MISP


## When to Use

- When investigating security incidents that require analyzing threat landscape with misp
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with threat intelligence concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install pymisp`
2. Configure MISP URL and API key.
3. Run the agent to generate threat landscape analysis:
   - Pull event statistics by threat level and date range
   - Analyze attribute type distributions (IP, domain, hash, URL)
   - Identify top MITRE ATT&CK techniques from event tags
   - Track threat actor activity via galaxy clusters
   - Generate temporal trend analysis of IOC submissions

```bash
python scripts/agent.py --misp-url https://misp.local --api-key YOUR_KEY --days 90 --output landscape_report.json
```

## Examples

### Threat Landscape Summary
```
Period: Last 90 days
Events analyzed: 1,247
Top threat level: High (43%)
Top attribute type: ip-dst (31%), domain (22%), sha256 (18%)
Top MITRE technique: T1566 Phishing (89 events)
Top threat actor: APT28 (34 events)
```


