---
name: cyber-performing-container-security-scanning-with-trivy
title: Performing Container Security Scanning With Trivy
version: '1.0'
description: Scan container images, filesystems, and Kubernetes manifests for vulnerabilities, misconfigurations, exposed
  secrets, and license compliance issues using Aqua Security Trivy with SBOM generation and CI/CD integration.
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- performing-
- container-
- security-
- scanning-with-
- trivy
keywords:
- performing-
- container-
- security-
- scanning-with-
- trivy
- scan
- container
- images
related_skills:
- cyber-scanning-iac-and-images-with-trivy
- cyber-scanning-container-images-with-grype
- cyber-securing-container-registry-images
- cyber-implementing-aqua-security-for-container-scanning
- cyber-implementing-gcp-binary-authorization
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: container-security
domain: cybersecurity
mitre_attack:
- T1610
- T1611
- T1609
- T1525
- T1195
nist_csf:
- PR.PS-01
- PR.IR-01
- ID.AM-08
- DE.CM-01
tags:
- trivy
- container-security
- vulnerability-scanning
- sbom
- docker
- kubernetes
- devsecops
- supply-chain
---


# Performing Container Security Scanning with Trivy

## Overview

Trivy is an open-source security scanner by Aqua Security that detects vulnerabilities in OS packages and language-specific dependencies, infrastructure-as-code misconfigurations, exposed secrets, and software license issues across container images, filesystems, Git repositories, and Kubernetes clusters. Trivy generates Software Bill of Materials (SBOM) in CycloneDX and SPDX formats for supply chain transparency. This skill covers comprehensive container image scanning, CI/CD pipeline integration, Kubernetes operator deployment, and scan result triage for security operations.


## When to Use

- When conducting security assessments that involve performing container security scanning with trivy
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Trivy v0.50+ installed (binary, Docker, or Homebrew)
- Docker daemon access for local image scanning
- Container registry credentials for remote image scanning
- CI/CD platform (GitHub Actions, GitLab CI, Jenkins) for pipeline integration
- Kubernetes cluster for Trivy Operator deployment (optional)

## Steps

### Step 1: Scan Container Images

Run vulnerability and secret scanning against container images from local builds or remote registries. Configure severity thresholds and ignore unfixed vulnerabilities.

### Step 2: Generate SBOM

Produce CycloneDX or SPDX SBOM documents from scanned images for supply chain compliance and vulnerability tracking across the software lifecycle.

### Step 3: Scan IaC and Kubernetes Manifests

Detect misconfigurations in Dockerfiles, Kubernetes YAML, Terraform, and Helm charts using built-in policy checks aligned with CIS benchmarks.

### Step 4: Integrate into CI/CD

Add Trivy scanning as a pipeline gate that blocks builds with critical/high vulnerabilities, generates SARIF reports for GitHub Advanced Security, and produces JUnit XML for test dashboards.

## Expected Output

JSON/table report listing CVEs with severity, CVSS scores, fixed versions, affected packages, misconfiguration findings, and exposed secrets with file locations.


