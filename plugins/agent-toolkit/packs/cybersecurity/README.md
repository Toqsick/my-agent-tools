# Pack: Cybersecurity

**Category:** security · **Skills:** 50

50 defensive-security and DFIR skills — CIS hardening, Docker/K8s and container security, network detection & hunting (Zeek/Suricata/Wireshark), forensics (Volatility/disk/IR), and compliance/supply-chain (SBOM/SLSA/gitleaks).

The full defensive-security and DFIR set: CIS hardening, Docker/Kubernetes and container security, network detection & hunting (Zeek, Suricata, Wireshark, Scapy), memory/disk/endpoint forensics (Volatility, Foremost, PhotoRec), incident response, and compliance/supply-chain (SBOM, SLSA, gitleaks, TruffleHog). Use these for audits, hunting, and forensics.

## When to use this pack

See the trigger words in each skill's description. This pack is the right starting point when the task falls in this domain; the `/toolkit <pack>` command lists these skills interactively.

## Skills

| Skill | What it does |
|---|---|
| `hardening-linux-endpoint-with-cis-benchmark` | Hardens Linux endpoints using CIS Benchmark recommendations for Ubuntu, RHEL, and CentOS to reduce attack surface, enforce security baselines, and meet compl… |
| `analyzing-linux-audit-logs-for-intrusion` | Uses the Linux Audit framework (auditd) with ausearch and aureport utilities to detect intrusion attempts, unauthorized access, privilege escalation, and sus… |
| `analyzing-linux-system-artifacts` | Examine Linux system artifacts including auth logs, cron jobs, shell history, and system configuration to uncover evidence of compromise or unauthorized acti… |
| `analyzing-persistence-mechanisms-in-linux` | Detect and analyze Linux persistence mechanisms including crontab entries, systemd service units, LD_PRELOAD hijacking, bashrc modifications, and authorized_… |
| `detecting-rootkit-activity` | Detects rootkit presence on compromised systems by identifying hidden processes, hooked system calls, modified kernel structures, hidden files, and covert ne… |
| `analyzing-linux-kernel-rootkits` | Detect kernel-level rootkits in Linux memory dumps using Volatility3 linux plugins (check_syscall, lsmod, hidden_modules), rkhunter system scanning, and /pro… |
| `performing-linux-log-forensics-investigation` | Perform forensic investigation of Linux system logs including syslog, auth.log, systemd journal, kern.log, and application logs to reconstruct user activity,… |
| `detecting-port-scanning-with-fail2ban` | Configures Fail2ban with custom filters and actions to detect port scanning activity, SSH brute force attempts, and network reconnaissance, automatically ban… |
| `implementing-network-segmentation-with-firewall-zones` | Design and implement network segmentation using firewall security zones, VLANs, ACLs, and microsegmentation policies to restrict lateral movement and enforce… |
| `hardening-docker-containers-for-production` | Hardening Docker containers for production involves applying security best practices aligned with CIS Docker Benchmark v1.8.0 to minimize attack surface, pre… |
| `hardening-docker-daemon-configuration` | Harden the Docker daemon by configuring daemon.json with user namespace remapping, TLS authentication, rootless mode, and CIS benchmark controls. |
| `performing-docker-bench-security-assessment` | Docker Bench for Security is an open-source script that checks dozens of common best practices around deploying Docker containers in production. Based on the… |
| `analyzing-docker-container-forensics` | Investigate compromised Docker containers by analyzing images, layers, volumes, logs, and runtime artifacts to identify malicious activity and evidence. |
| `detecting-container-escape-attempts` | Container escape is a critical attack technique where an adversary breaks out of container isolation to access the host system or other containers. Detection… |
| `detecting-container-runtime-threats-with-falco` | Write and deploy Falco rules with the modern eBPF driver to detect container escape, namespace abuse, privileged mounts, and anomalous syscalls at runtime in… |
| `scanning-docker-images-with-trivy` | Trivy is a comprehensive open-source vulnerability scanner by Aqua Security that detects vulnerabilities in OS packages, language-specific dependencies, misc… |
| `performing-container-security-scanning-with-trivy` | Scan container images, filesystems, and Kubernetes manifests for vulnerabilities, misconfigurations, exposed secrets, and license compliance issues using Aqu… |
| `implementing-container-image-minimal-base-with-distroless` | Reduce container attack surface by building application images on Google distroless base images that contain only the application runtime with no shell, pack… |
| `securing-container-registry-with-harbor` | Harbor is an open-source container registry that provides security features including vulnerability scanning (integrated Trivy), image signing (Notary/Cosign… |
| `implementing-kubernetes-pod-security-standards` | Pod Security Standards (PSS) define three levels of security policies -- Privileged, Baseline, and Restricted -- enforced by the Pod Security Admission (PSA)… |
| `analyzing-network-packets-with-scapy` | Craft, send, sniff, and dissect network packets using Scapy for protocol analysis, network reconnaissance, and traffic anomaly detection in authorized securi… |
| `analyzing-network-traffic-with-wireshark` | Captures and analyzes network packet data using Wireshark and tshark to identify malicious traffic patterns, diagnose protocol issues, extract artifacts, and… |
| `performing-network-forensics-with-wireshark` | Capture and analyze network traffic using Wireshark and tshark to reconstruct network events, extract artifacts, and identify malicious communications. |
| `configuring-suricata-for-network-monitoring` | Deploys and configures Suricata IDS/IPS with Emerging Threats rulesets, EVE JSON logging, and custom rules for real-time network traffic inspection, threat d… |
| `detecting-network-anomalies-with-zeek` | Deploys and configures Zeek (formerly Bro) network security monitor to passively analyze network traffic, generate structured logs, detect anomalous behavior… |
| `detecting-beaconing-patterns-with-zeek` | Performs statistical analysis of Zeek conn.log connection intervals to detect C2 beaconing patterns. Uses the ZAT library to load Zeek logs into Pandas DataF… |
| `detecting-dns-exfiltration-with-dns-query-analysis` | Detect data exfiltration through DNS tunneling by analyzing query entropy, subdomain length, query volume, TXT record abuse, and response payload sizes using… |
| `deploying-osquery-for-endpoint-monitoring` | Deploys and configures osquery for real-time endpoint monitoring using SQL-based queries to inspect running processes, open ports, installed software, and sy… |
| `building-detection-rules-with-sigma` | Builds vendor-agnostic detection rules using the Sigma rule format for threat detection across SIEM platforms including Splunk, Elastic, and Microsoft Sentin… |
| `performing-malware-triage-with-yara` | Performs rapid malware triage and classification using YARA rules to match file patterns, strings, byte sequences, and structural characteristics against kno… |
| `hunting-advanced-persistent-threats` | Proactively hunts for Advanced Persistent Threat (APT) activity within enterprise environments using hypothesis-driven searches across endpoint telemetry, ne… |
| `building-threat-hunt-hypothesis-framework` | Build a systematic threat hunt hypothesis framework that transforms threat intelligence, attack patterns, and environmental data into testable hunting hypoth… |
| `conducting-memory-forensics-with-volatility` | Performs memory forensics analysis using Volatility 3 to extract evidence of malware execution, process injection, network connections, and credential theft … |
| `performing-memory-forensics-with-volatility3` | Analyze volatile memory dumps using Volatility 3 to extract running processes, network connections, loaded modules, and evidence of malicious activity. |
| `performing-disk-forensics-investigation` | Conducts disk forensics investigations using forensic imaging, file system analysis, artifact recovery, and timeline reconstruction to support incident respo… |
| `performing-endpoint-forensics-investigation` | Performs digital forensics investigation on compromised endpoints including memory acquisition, disk imaging, artifact analysis, and timeline reconstruction.… |
| `performing-log-analysis-for-forensic-investigation` | Collect, parse, and correlate system, application, and security logs to reconstruct events and establish timelines during forensic investigations. |
| `building-incident-response-playbook` | Designs and documents structured incident response playbooks that define step-by-step procedures for specific incident types aligned with NIST SP 800-61r3 an… |
| `triaging-security-incident-with-ir-playbook` | Classify and prioritize security incidents using structured IR playbooks to determine severity, assign response teams, and initiate appropriate response proc… |
| `recovering-deleted-files-with-photorec` | Recover deleted files from disk images and storage media using PhotoRec's file signature-based carving engine regardless of file system damage. |
| `performing-file-carving-with-foremost` | Recover files from disk images and unallocated space using Foremost's header-footer signature carving to extract evidence regardless of file system state. |
| `performing-nist-csf-maturity-assessment` | The NIST Cybersecurity Framework (CSF) 2.0, released in February 2024, provides a comprehensive taxonomy for managing cybersecurity risk through six core Fun… |
| `implementing-attack-surface-management` | Implements external attack surface management (EASM) using Shodan, Censys, and ProjectDiscovery tools (subfinder, httpx, nuclei) for asset discovery, subdoma… |
| `auditing-cloud-with-cis-benchmarks` | This skill details how to conduct cloud security audits using Center for Internet Security benchmarks for AWS, Azure, and GCP. It covers interpreting CIS Fou… |
| `implementing-secret-scanning-with-gitleaks` | This skill covers implementing Gitleaks for detecting and preventing hardcoded secrets in git repositories. It addresses configuring pre-commit hooks, CI/CD … |
| `detecting-aws-credential-exposure-with-trufflehog` | Detecting exposed AWS credentials in source code repositories, CI/CD pipelines, and configuration files using TruffleHog, git-secrets, and AWS-native detecti… |
| `generating-and-analyzing-sboms` | Produce and ingest CycloneDX and SPDX SBOMs and correlate them to vulnerability intelligence. |
| `analyzing-sbom-for-supply-chain-vulnerabilities` | Parses Software Bill of Materials (SBOM) in CycloneDX and SPDX JSON formats to identify supply chain vulnerabilities by correlating components against the NV… |
| `verifying-build-provenance-with-slsa-sigstore` | Verify signed artifacts and SLSA build provenance with Sigstore cosign and slsa-verifier, enforce keyless OIDC identity, and apply SLSA Build levels to harde… |
| `performing-authenticated-vulnerability-scan` | Authenticated (credentialed) vulnerability scanning uses valid system credentials to log into target hosts and perform deep inspection of installed software,… |
