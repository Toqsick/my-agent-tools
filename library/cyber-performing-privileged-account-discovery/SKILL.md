---
name: cyber-performing-privileged-account-discovery
title: Performing Privileged Account Discovery
version: '1.0'
description: Discover and inventory all privileged accounts across enterprise infrastructure including domain admins, local
  admins, service accounts, database admins, cloud IAM roles, and application admin account
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- performing-
- privileged-
- account-
- discovery
- discover
keywords:
- performing-
- privileged-
- account-
- discovery
- discover
- inventory
- privileged
- accounts
related_skills:
- cyber-detecting-shadow-api-endpoints
- cyber-performing-service-account-audit
- cyber-performing-api-inventory-and-discovery
- cyber-performing-privileged-account-access-review
- cyber-implementing-privileged-access-management-with-cyberark
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: identity-access-management
domain: cybersecurity
mitre_attack:
- T1078
- T1110
- T1556
- T1098
- T1078.004
nist_csf:
- PR.AA-01
- PR.AA-02
- PR.AA-05
- PR.AA-06
tags:
- iam
- identity
- access-control
- privileged-access
- discovery
- inventory
---


# Performing Privileged Account Discovery

## Overview
Discover and inventory all privileged accounts across enterprise infrastructure including domain admins, local admins, service accounts, database admins, cloud IAM roles, and application admin accounts. Covers automated scanning, risk classification, and onboarding to PAM.


## When to Use

- When conducting security assessments that involve performing privileged account discovery
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Familiarity with identity access management concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Objectives
- Implement comprehensive performing privileged account discovery capability
- Establish automated discovery and monitoring processes
- Integrate with enterprise IAM and security tools
- Generate compliance-ready documentation and reports
- Align with NIST 800-53 access control requirements

## Security Controls
| Control | NIST 800-53 | Description |
|---------|-------------|-------------|
| Account Management | AC-2 | Lifecycle management |
| Access Enforcement | AC-3 | Policy-based access control |
| Least Privilege | AC-6 | Minimum necessary permissions |
| Audit Logging | AU-3 | Authentication and access events |
| Identification | IA-2 | User and service identification |

## Verification
- [ ] Implementation tested in non-production environment
- [ ] Security policies configured and enforced
- [ ] Audit logging enabled and forwarding to SIEM
- [ ] Documentation and runbooks complete
- [ ] Compliance evidence generated


