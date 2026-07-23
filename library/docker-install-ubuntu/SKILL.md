---
name: docker-install-ubuntu
description: "Use when user asks for Docker installation on Ubuntu Server, fresh Ubuntu Docker setup, Docker GPG key + repo setup. NOT for Docker Compose patterns, Kubernetes, or non-Ubuntu distros. Step-by-step guide for Docker installation on Ubuntu Server (fresh)."
version: 1.0.0
author: yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - docker
    - ubuntu
    - server
    - installation
    - devops
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['docker', 'ubuntu', 'installation', 'server', 'fresh']
keywords: ['docker', 'ubuntu', 'installation', 'server', 'fresh']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['docker-influx-grafana-stack']
---



# Docker Installation Ubuntu

Leitfaden für Docker-Installation auf Ubuntu Server (frische VM).

## Schritt-für-Schritt

```bash

set -euo pipefail
# 1. Paketlisten aktualisieren
sudo apt update

# 2. prerequisites
sudo apt install ca-certificates curl gnupg

# 3. Docker GPG-Schlüssel
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 4. Repository hinzufügen
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Installieren
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Auto-start aktivieren
sudo systemctl start docker
sudo systemctl enable docker

# 7. User-Gruppen-Zugriff (ohne sudo)
sudo usermod -aG docker $USER
```

## Verifizierung
```bash

set -euo pipefail
docker --version
docker compose version
```

## Pitfalls
- Auf Google Cloud VMs: `sudo` nötig, kein `venv` vorinstalliert
- Nach `usermod -aG docker` neue Shell/session öffnen oder `newgrp docker` ausführen
