---
name: cyber-analyzing-kubernetes-audit-logs
title: Analyzing Kubernetes Audit Logs
version: '1.0'
description: 'Parses Kubernetes API server audit logs (JSON lines) to detect exec-into-pod, secret access, RBAC modifications,
  privileged pod creation, and anonymous API access. Builds threat detection rules from audit event patterns. Use when investigating
  Kubernetes cluster compromise or building k8s-specific SIEM detection rules.

  '
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- analyzing-
- kubernetes-audit
- logs
- parses
- kubernetes
keywords:
- analyzing-
- kubernetes-audit
- logs
- parses
- kubernetes
- server
- audit
- json
related_skills:
- cyber-analyzing-cloud-storage-access-patterns
- cyber-detecting-suspicious-oauth-application-consent
- cyber-implementing-web-application-logging-with-modsecurity
- cyber-performing-kubernetes-penetration-testing
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: container-security
domain: cybersecurity
mitre_attack:
- T1610
- T1613
- T1078
- T1552.007
nist_csf:
- PR.PS-01
- PR.IR-01
- ID.AM-08
- DE.CM-01
tags:
- kubernetes-security
- container-security
- audit-log-analysis
- rbac
- privilege-escalation
- k8s-api-server
- threat-detection
---


# Analyzing Kubernetes Audit Logs


## When to Use

- When investigating security incidents that require analyzing kubernetes audit logs
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with container security concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Parse Kubernetes audit log files (JSON lines format) to detect security-relevant
events including unauthorized access, privilege escalation, and data exfiltration.

```python
import json

with open("/var/log/kubernetes/audit.log") as f:
    for line in f:
        event = json.loads(line)
        verb = event.get("verb")
        resource = event.get("objectRef", {}).get("resource")
        user = event.get("user", {}).get("username")
        if verb == "create" and resource == "pods/exec":
            print(f"Pod exec by {user}")
```

Key events to detect:
1. pods/exec and pods/attach (shell into containers)
2. secrets access (get/list/watch)
3. clusterrolebindings creation (RBAC escalation)
4. Privileged pod creation
5. Anonymous or system:unauthenticated access

## Examples

```python
# Detect secret enumeration
if verb in ("get", "list") and resource == "secrets":
    print(f"Secret access: {user} -> {event['objectRef'].get('name')}")
```


