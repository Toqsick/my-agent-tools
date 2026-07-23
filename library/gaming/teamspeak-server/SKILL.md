---
name: teamspeak-server
description: "Use when user asks for TeamSpeak server hosting, TeamSpeak 6 self-hosted setup, TeamSpeak server operations. NOT for Discord servers, Mumble, or non-voice-chat services. Host and operate TeamSpeak servers (especially TeamSpeak 6 beta)."
tags:
- teamspeak
- ts6
- voice
- server
- docker
- linux
- vps
version: 1.0.0
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['teamspeak', 'server', 'servers', 'teamspeak-server', 'hosting']
keywords: ['teamspeak', 'server', 'servers', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['mcp-server-authoring']
---



# TeamSpeak Server Hosting

## When to use

Use this skill when the user asks about hosting TeamSpeak servers, especially:

- TeamSpeak 6 self-hosted server setup on Linux/VPS
- TeamSpeak 6 Docker Compose deployment
- TeamSpeak 6 firewall, ports, DNS, update, or backup workflow
- Comparing self-hosted TS6 with official TeamSpeak-hosted Communities
- Explaining TS6 beta limitations, licensing, and TS3 compatibility constraints

This is a class-level voice-server skill. Keep TeamSpeak-specific details here, not in Minecraft/server-pack or generic Docker skills.

## Gather context before operating

Before creating or changing a live server, ask for:

1. OS and access model: local Linux, VPS, Docker already installed?
2. Domain/subdomain: IP-only or DNS name like `ts6.example.de`?
3. Public or private server?
4. Expected slot count and whether the 32-slot TS6 beta license is enough.
5. Firewall tool: `ufw`, `firewalld`, cloud firewall, or provider security group.
6. Backup expectation: none, manual backup, or recurring automated backup.
7. Update policy: manual updates only or auto-pull latest image.

If the user only asks conceptually, give a concise comparison first, then offer Docker-based setup.

## Current TeamSpeak 6 hosting options

### 1. Self-hosted TS6 beta server

TeamSpeak publishes the TS6 server beta through the official `teamspeak/teamspeak6-server` repository and Docker image:

```text
teamspeaksystems/teamspeak6-server:latest
```

set -euo pipefail
Important beta facts to communicate clearly:

- TS6 server is still beta and not fully feature-complete.
- TS3 server licenses are not compatible with TS6.
- There is currently no migration path from TS3 server licenses/configs to TS6.
- The beta includes a 32-slot license that has been renewed during the beta/evaluation period.
- Larger TS6 licenses or upgrades may not be generally available yet; verify current licensing before promising scale.
- Because this is beta, verify current behavior against the official GitHub README/CONFIG.md before giving definitive operational claims.

### 2. Official TeamSpeak-hosted Communities/servers

Use this when the user wants the easiest path and does not need full server control. TeamSpeak can host official TS6 servers/Communities directly; this is usually simpler but less flexible than self-hosting.

### 3. Third-party hosters

Some providers may offer TS6 or TS6-compatible hosting. Verify provider docs because TS6 is still moving.

## Recommended Linux/VPS setup: Docker Compose

Default ports:

```text
9987/udp   Voice
30033/tcp  File Transfer
10080/tcp  Optional WebQuery, only if needed
```

set -euo pipefail
Typical Ubuntu/Debian install:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin curl ufw
sudo systemctl enable --now docker
```

set -euo pipefail
Firewall for a public server:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 9987/udp comment "TeamSpeak 6 Voice"
sudo ufw allow 30033/tcp comment "TeamSpeak 6 File Transfer"
sudo ufw enable
sudo ufw status
```

set -euo pipefail
If the VPS already uses `firewalld`, cloud security groups, or another firewall, do not blindly run `ufw enable`; configure the active firewall instead.

Create a persistent Compose setup:

```bash
mkdir -p ~/teamspeak6
cd ~/teamspeak6
nano docker-compose.yml
```

set -euo pipefail
Minimal `docker-compose.yml`:

```yaml
services:
  teamspeak6:
    image: teamspeaksystems/teamspeak6-server:latest
    container_name: teamspeak6
    restart: unless-stopped
    ports:
      - "9987:9987/udp"
      - "30033:30033/tcp"
      # - "10080:10080/tcp"
    environment:
      TSSERVER_LICENSE_ACCEPTED: "accept"
    volumes:
      - teamspeak6-data:/var/tsserver

volumes:
  teamspeak6-data:
    name: teamspeak6-data
```

set -euo pipefail
Start and inspect:

```bash
docker compose up -d
docker logs -f teamspeak6
```

set -euo pipefail
Connect in the TS6 client with:

```text
<VPS-IP-or-domain>:9987
```

set -euo pipefail
## Operations

### Start/stop/restart

```bash
cd ~/teamspeak6
docker compose stop
docker compose start
docker compose restart
```

set -euo pipefail
### Logs

```bash
docker logs -f teamspeak6
```

set -euo pipefail
Use logs to find startup status, admin/privilege information, and errors.

### Update

Manual update is safest for beta software:

```bash
cd ~/teamspeak6
docker compose pull
docker compose up -d
docker logs -f teamspeak6
```

set -euo pipefail
Do not enable silent auto-update unless the user explicitly wants it; beta images can introduce breaking changes.

### Backup

Recommended manual backup:

```bash
cd ~/teamspeak6
docker compose stop
sudo tar -czf ~/teamspeak6-backup-$(date +%F).tar.gz -C /var/lib/docker/volumes/teamspeak6-data _data
docker compose start
```

set -euo pipefail
Restore:

```bash
cd ~/teamspeak6
docker compose stop
sudo rm -rf /var/lib/docker/volumes/teamspeak6-data/_data/*
sudo tar -xzf ~/teamspeak6-backup-YYYY-MM-DD.tar.gz -C /var/lib/docker/volumes/teamspeak6-data/_data
docker compose start
```

set -euo pipefail
Never delete the Docker volume unless the user explicitly wants a fresh server:

```bash
docker volume rm teamspeak6-data
```

set -euo pipefail
That permanently deletes TS6 server data.

## Verification checklist

After setup, verify:

1. Container is running:

```bash
docker ps --filter name=teamspeak6
```

set -euo pipefail
2. Logs show no fatal startup errors:

```bash
docker logs --tail=200 teamspeak6
```

set -euo pipefail
3. Required ports are open:

```bash
sudo ufw status | grep -E '9987|30033'
```

set -euo pipefail
4. TS6 client can connect to:

```text
<VPS-IP-or-domain>:9987
```

set -euo pipefail
5. If using a domain, DNS A/AAAA record points to the VPS IP.

## Troubleshooting patterns

### Cannot connect

Check in order:

```bash
docker ps
docker logs -f teamspeak6
sudo ufw status
```

set -euo pipefail
Confirm UDP `9987` is open. Many users only open TCP and forget UDP.

### Container exits immediately

```bash
docker compose logs teamspeak6
```

set -euo pipefail
Common causes:

- License not accepted / env var missing
- Port conflict
- Invalid volume permissions
- Upstream beta image issue

### Need a different port

Change the host side of the Compose port mapping, e.g.:

```yaml
ports:
  - "9999:9987/udp"
  - "30033:30033/tcp"
```

set -euo pipefail
Then reconnect clients with:

```text
domain:9999
```

### Need WebQuery

Only expose `10080/tcp` if the user actually needs it. It is not required for normal voice use.

## Pitfalls

- Do not confuse TeamSpeak 3 server setup with TeamSpeak 6. TS3 licenses/configs are not compatible with TS6.
- TS6 server is beta; avoid promising stable long-term behavior or larger slot licenses without checking current official docs.
- Voice traffic uses UDP `9987`; TCP-only firewall rules will not work.
- Do not expose WebQuery `10080/tcp` unless needed.
- Do not delete the Docker volume during troubleshooting unless the user explicitly accepts data loss.
- Manual updates are preferred during beta; auto-pulling `latest` can break a working server.
- If the VPS is behind a cloud firewall/security group, opening ports inside Linux is not enough; open them at the provider level too.
- For remote SSH sessions, keep `22/tcp` allowed before enabling `ufw`.

## References

- `references/teamspeak6-self-hosting-2026-06-19.md` contains the condensed official TS6 beta setup notes, Docker Compose example, ports, beta license facts, and backup/update commands found during this session.
