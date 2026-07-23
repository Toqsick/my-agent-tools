---
name: cyber-analyzing-ransomware-network-indicators
title: Analyzing Ransomware Network Indicators
version: '1.0'
description: Identify ransomware network indicators including C2 beaconing patterns, TOR exit node connections, data exfiltration
  flows, and encryption key exchange via Zeek conn.log and NetFlow analysis
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-
- ransomware-
- network-
- indicators
- identify
keywords:
- analyzing-
- ransomware-
- network-
- indicators
- identify
- ransomware
- network
- including
related_skills:
- cyber-detecting-insider-threat-behaviors
- cyber-implementing-ransomware-kill-switch-detection
- cyber-hunting-for-supply-chain-compromise
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: threat-hunting
domain: cybersecurity
mitre_attack:
- T1071.001
- T1573
- T1048
- T1567.002
- T1486
nist_csf:
- DE.CM-01
- DE.AE-02
- DE.AE-07
- ID.RA-05
tags:
- ransomware
- c2-beaconing
- zeek
- netflow
- tor
- exfiltration
- network-forensics
---


# Analyzing Ransomware Network Indicators

## Overview

Before and during ransomware execution, adversaries establish C2 channels, exfiltrate data, and download encryption keys. This skill analyzes Zeek conn.log and NetFlow data to detect beaconing patterns (regular-interval callbacks), connections to known TOR exit nodes, large outbound data transfers, and suspicious DNS activity associated with ransomware families.


## When to Use

- When investigating security incidents that require analyzing ransomware network indicators
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Zeek conn.log files or NetFlow CSV/JSON exports
- Python 3.8+ with standard library
- TOR exit node list (fetched from Tor Project or threat intel feeds)
- Optional: Known ransomware C2 IOC list

## Steps

1. **Parse Connection Logs** — Ingest Zeek conn.log (TSV) or NetFlow records into structured format
2. **Detect Beaconing Patterns** — Calculate connection interval statistics (mean, stddev, coefficient of variation) to identify periodic callbacks
3. **Check TOR Exit Node Connections** — Cross-reference destination IPs against current TOR exit node list
4. **Identify Data Exfiltration** — Flag connections with unusually high outbound byte ratios to external IPs
5. **Analyze DNS Patterns** — Detect DGA-like domain queries and high-entropy subdomains
6. **Score and Correlate** — Apply composite risk scoring across all indicator types
7. **Generate Report** — Produce structured report with timeline and MITRE ATT&CK mapping

## Expected Output

- JSON report with beaconing detections and interval statistics
- TOR exit node connection alerts
- Data exfiltration flow analysis
- Composite ransomware risk score with MITRE mapping (T1071, T1573, T1041)


