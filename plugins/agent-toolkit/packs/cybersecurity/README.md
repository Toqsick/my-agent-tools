# Pack: Cybersecurity

**Category:** security · **Skills:** 15

15 Docker- and auditd-native defensive-security and DFIR skills — Docker hardening/bench assessment and container forensics, auditd intrusion analysis, Suricata/Sigma detection engineering, IR playbooks, cloud CIS audits, and supply-chain (SBOM/SLSA).

The kept defensive-security set: everything that runs on stock Docker or auditd — Docker/Kubernetes container security, auditd-based intrusion and persistence analysis, Suricata/Sigma detection engineering, IR playbooks, cloud CIS audits, and supply-chain (SBOM, SLSA). Use these for audits, detection engineering, and forensics. Third-party-tool skills (Zeek, YARA, Volatility, Trivy, osquery, Falco, gitleaks, TruffleHog, Foremost, PhotoRec) moved to the `library/` reference tier.

## When to use this pack

See the trigger words in each skill's description. This pack is the right starting point when the task falls in this domain; the `/toolkit <pack>` command lists these skills interactively.

## Skills

| Skill | What it does |
|---|---|
| `analyzing-linux-audit-logs-for-intrusion` | Uses the Linux Audit framework (auditd) with ausearch and aureport utilities to detect intrusion attempts, unauthorized access, privilege escalation, … |
| `hardening-docker-containers-for-production` | Hardening Docker containers for production involves applying security best practices aligned with CIS Docker Benchmark v1.8.0 to minimize attack surfa… |
| `hardening-docker-daemon-configuration` | Harden the Docker daemon by configuring daemon.json with user namespace remapping, TLS authentication, rootless mode, and CIS benchmark controls. |
| `performing-docker-bench-security-assessment` | Docker Bench for Security is an open-source script that checks dozens of common best practices around deploying Docker containers in production. Based… |
| `analyzing-docker-container-forensics` | Investigate compromised Docker containers by analyzing images, layers, volumes, logs, and runtime artifacts to identify malicious activity and evidenc… |
| `detecting-container-escape-attempts` | Container escape is a critical attack technique where an adversary breaks out of container isolation to access the host system or other containers. De… |
| `configuring-suricata-for-network-monitoring` | Deploys and configures Suricata IDS/IPS with Emerging Threats rulesets, EVE JSON logging, and custom rules for real-time network traffic inspection, t… |
| `building-detection-rules-with-sigma` | Builds vendor-agnostic detection rules using the Sigma rule format for threat detection across SIEM platforms including Splunk, Elastic, and Microsoft… |
| `building-threat-hunt-hypothesis-framework` | Build a systematic threat hunt hypothesis framework that transforms threat intelligence, attack patterns, and environmental data into testable hunting… |
| `conducting-memory-forensics-with-volatility` | Performs memory forensics analysis using Volatility 3 to extract evidence of malware execution, process injection, network connections, and credential… |
| `building-incident-response-playbook` | Designs and documents structured incident response playbooks that define step-by-step procedures for specific incident types aligned with NIST SP 800-… |
| `triaging-security-incident-with-ir-playbook` | Classify and prioritize security incidents using structured IR playbooks to determine severity, assign response teams, and initiate appropriate respon… |
| `auditing-cloud-with-cis-benchmarks` | This skill details how to conduct cloud security audits using Center for Internet Security benchmarks for AWS, Azure, and GCP. It covers interpreting … |
| `generating-and-analyzing-sboms` | Produce and ingest CycloneDX and SPDX SBOMs and correlate them to vulnerability intelligence. |
| `verifying-build-provenance-with-slsa-sigstore` | Verify signed artifacts and SLSA build provenance with Sigstore cosign and slsa-verifier, enforce keyless OIDC identity, and apply SLSA Build levels t… |
