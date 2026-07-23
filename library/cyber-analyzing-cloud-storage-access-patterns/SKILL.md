---
name: cyber-analyzing-cloud-storage-access-patterns
title: Analyzing Cloud Storage Access Patterns
version: '1.0'
description: Detect abnormal access patterns in AWS S3, GCS, and Azure Blob Storage by analyzing CloudTrail Data Events, GCS
  audit logs, and Azure Storage Analytics. Identifies after-hours bulk downloads, access from new IP addresses, unusual API
  calls (GetObject spikes), and potential data exfiltration using statistical baselines and time-series anomaly detection.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-cloud-
- storage-access-
- patterns
- detect
- abnormal
keywords:
- analyzing-cloud-
- storage-access-
- patterns
- detect
- abnormal
- access
- azure
- blob
related_skills: []
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: cloud-security
domain: cybersecurity
mitre_attack:
- T1530
- T1567.002
- T1619
- T1078.004
- T1048
nist_csf:
- PR.IR-01
- ID.AM-08
- GV.SC-06
- DE.CM-01
tags:
- cloud-security
- aws-s3
- gcs
- azure-blob-storage
- cloudtrail
- data-access-anomaly
- exfiltration-detection
---


# Analyzing Cloud Storage Access Patterns


## When to Use

- When investigating security incidents that require analyzing cloud storage access patterns
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with cloud security concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

1. Install dependencies: `pip install boto3 requests`
2. Query CloudTrail for S3 Data Events using AWS CLI or boto3.
3. Build access baselines: hourly request volume, per-user object counts, source IP history.
4. Detect anomalies:
   - After-hours access (outside 8am-6pm local time)
   - Bulk downloads: >100 GetObject calls from single principal in 1 hour
   - New source IPs not seen in the prior 30 days
   - ListBucket enumeration spikes (reconnaissance indicator)
5. Generate prioritized findings report.

```bash
python scripts/agent.py --bucket my-sensitive-data --hours-back 24 --output s3_access_report.json
```

## Examples

### CloudTrail S3 Data Event
```json
{"eventName": "GetObject", "requestParameters": {"bucketName": "sensitive-data", "key": "financials/q4.xlsx"},
 "sourceIPAddress": "203.0.113.50", "userIdentity": {"arn": "arn:aws:iam::123456789012:user/analyst"}}
```


