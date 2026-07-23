# TeamSpeak 6 Self-Hosting Reference

Captured 2026-06-19 from the official TeamSpeak TS6 Server Beta GitHub README and TeamSpeak support search results. TS6 is still beta, so verify current licensing and feature status before production use.

## Official sources

- GitHub repo: `teamspeak/teamspeak6-server`
- Docker image used in official docs: `teamspeaksystems/teamspeak6-server:latest`
- Official support article title found: `How To Self-Host The TeamSpeak 6 Beta Server`

## Beta status and licensing notes

- TS6 server is a beta release; some features are still in development and may be unstable.
- Self-hosted server files are still under active development and are not fully feature-complete.
- TeamSpeak 3 server licenses are not compatible with TeamSpeak 6 servers.
- There is currently no migration path between TS3 and TS6 servers.
- The beta server includes a 32-slot beta license that has been renewed during the beta/evaluation period.
- Larger TS6 licenses/upgrades may not be generally available yet; check current TeamSpeak announcements before promising more than 32 slots.

## Ports

```text
9987/udp   Voice port, required for normal client connections
30033/tcp  File transfer port
10080/tcp  Optional WebQuery, only if explicitly needed
```

Important: opening only TCP `9987` is not enough. Voice requires UDP.

## Minimal Docker Compose

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

Start:

```bash
docker compose up -d
docker logs -f teamspeak6
```

Manage:

```bash
docker compose stop
docker compose start
docker compose restart
```

Update:

```bash
docker compose pull
docker compose up -d
docker logs -f teamspeak6
```

## Firewall

For Ubuntu/Debian with UFW:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 9987/udp comment "TeamSpeak 6 Voice"
sudo ufw allow 30033/tcp comment "TeamSpeak 6 File Transfer"
sudo ufw enable
sudo ufw status
```

If the VPS is behind a cloud firewall/security group, also open the ports at the provider level.

## Backup and restore

Backup:

```bash
cd ~/teamspeak6
docker compose stop
sudo tar -czf ~/teamspeak6-backup-$(date +%F).tar.gz -C /var/lib/docker/volumes/teamspeak6-data _data
docker compose start
```

Restore:

```bash
cd ~/teamspeak6
docker compose stop
sudo rm -rf /var/lib/docker/volumes/teamspeak6-data/_data/*
sudo tar -xzf ~/teamspeak6-backup-YYYY-MM-DD.tar.gz -C /var/lib/docker/volumes/teamspeak6-data/_data
docker compose start
```

Do not delete the Docker volume unless the user explicitly wants a fresh server:

```bash
docker volume rm teamspeak6-data
```

## Troubleshooting checklist

```bash
docker ps --filter name=teamspeak6
docker logs --tail=200 teamspeak6
sudo ufw status | grep -E '9987|30033'
```

Most common failure: firewall allows TCP but not UDP `9987`.
