---
name: cyber-implementing-endpoint-detection-with-wazuh
title: Implementing Endpoint Detection With Wazuh
version: '1.0'
description: Deploy and configure Wazuh SIEM/XDR for endpoint detection including agent management, custom decoder and rule
  XML creation, alert querying via the Wazuh REST API, and automated response actions.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- implementing-
- endpoint-
- detection-with-
- wazuh
- deploy
keywords:
- implementing-
- endpoint-
- detection-with-
- wazuh
- deploy
- configure
- siem
- endpoint
related_skills:
- cyber-implementing-velociraptor-for-ir-collection
- cyber-implementing-proofpoint-email-security-gateway
- cyber-implementing-network-intrusion-prevention-with-suricata
- cyber-deploying-tailscale-for-zero-trust-vpn
- cyber-implementing-dragos-platform-for-ot-monitoring
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: security-operations
domain: cybersecurity
mitre_attack:
- T1078
- T1190
- T1059
- T1685.002
- T1685.005
nist_csf:
- DE.CM-01
- RS.MA-01
- GV.OV-01
- DE.AE-02
tags:
- siem
- xdr
- wazuh
- endpoint-detection
- custom-rules
- incident-response
---


# Implementing Endpoint Detection with Wazuh

## Overview

Wazuh is an open-source SIEM and XDR platform for endpoint monitoring, threat detection, and compliance. This skill covers managing agents via the Wazuh REST API, creating custom decoders and rules in XML for organization-specific detections, querying alerts, and testing rule logic using the logtest endpoint.


## When to Use

- When deploying or configuring implementing endpoint detection with wazuh capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- Wazuh Manager 4.x deployed with API enabled
- Python 3.9+ with `requests` library
- API credentials (username/password for JWT authentication)
- Understanding of Wazuh decoder and rule XML syntax

## Steps

### Step 1: Authenticate to Wazuh API
Obtain JWT token via POST to /security/user/authenticate.

### Step 2: List and Monitor Agents
Query agent status, versions, and last keep-alive via /agents endpoint.

### Step 3: Query Security Alerts
Search alerts by rule ID, severity, agent, or time range.

### Step 4: Test Custom Rules with Logtest
Use the /logtest endpoint to validate decoder and rule logic against sample log lines.

## Expected Output

JSON report with agent inventory, alert statistics, rule coverage, and logtest validation results.


