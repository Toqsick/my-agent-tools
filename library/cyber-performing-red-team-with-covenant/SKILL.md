---
name: cyber-performing-red-team-with-covenant
title: Performing Red Team With Covenant
version: '1.0'
description: Conduct red team operations using the Covenant C2 framework for authorized adversary simulation, including listener
  setup, grunt deployment, task execution, and lateral movement tracking.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- performing-red-
- team-with-
- covenant
- conduct
- team
keywords:
- performing-red-
- team-with-
- covenant
- conduct
- team
- operations
- using
- framework
related_skills:
- cyber-building-red-team-c2-infrastructure-with-havoc
- cyber-performing-initial-access-with-evilginx3
- cyber-building-c2-infrastructure-with-sliver-framework
- cyber-performing-threat-emulation-with-atomic-red-team
- cyber-performing-purple-team-exercise
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: red-team
domain: cybersecurity
mitre_attack:
- T1595
- T1190
- T1059
- T1078
- T1021
nist_csf:
- ID.RA-01
- GV.OV-02
- DE.AE-07
tags:
- red-team
- c2
- covenant
- adversary-simulation
- penetration-testing
---


# Performing Red Team Operations with Covenant C2

## Overview

Covenant is a collaborative .NET C2 framework for red teamers that provides a Swagger-documented REST API for managing listeners, launchers, grunts (agents), and tasks. This skill covers automating Covenant operations through its API for authorized red team engagements: creating HTTP/HTTPS listeners, generating binary and PowerShell launchers, deploying grunts, executing tasks on compromised hosts, and tracking lateral movement.


## When to Use

- When conducting security assessments that involve performing red team with covenant
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Covenant C2 server deployed (Docker or .NET 6)
- Python 3.9+ with `requests` library
- Covenant API token (obtained via /api/users/login)
- Written authorization for red team engagement
- Isolated lab or authorized target environment

## Steps

### Step 1: Authenticate to Covenant API
Obtain a JWT token by posting credentials to /api/users/login endpoint.

### Step 2: Create Listener
Configure an HTTP or HTTPS listener with callback URLs and bind address.

### Step 3: Generate Launcher
Create a binary, PowerShell, or MSBuild launcher tied to the listener for grunt deployment.

### Step 4: Deploy and Manage Grunts
Monitor grunt callbacks, execute tasks, and collect output from compromised hosts.

### Step 5: Document Operations
Generate an operations report documenting all actions, timestamps, and findings.

## Expected Output

JSON report with listener configuration, active grunts, executed tasks, and task output for engagement documentation.


