---

name: docker-influx-grafana-stack
title: "Docker-based InfluxDB + Grafana Monitoring Stack"
description: "Use when user asks for Docker InfluxDB + Grafana stack setup, self-hosted time-series monitoring, Grafana provisioning via API, Home Assistant metrics in Grafana, Wear OS health pipeline. NOT for cloud-managed monitoring (Datadog/New Relic), non-Docker monitoring, or non-time-series data. Setup self-hosted Docker monitoring stack (InfluxDB 2.x + Grafana, optional Home Assistant)."
triggers:
  - "Self-hosted Fitness / Health Dashboard aufsetzen"
  - "InfluxDB + Grafana mit Docker deployen"
  - "Home Assistant Metriken in Grafana visualisieren"
  - "Docker-Monitoring-Stack für Wear OS Health-Daten bauen"
  - "InfluxDB 2.x vs 3.x Docker-Verfügbarkeit prüfen"
  - "Grafana volume permissions / uid 472 crash-loop fixen"
  - "Grafana DataSource via API provisionieren"
  - "Grafana Dashboard via API importieren"
  - "Health Connect → InfluxDB Pipeline auf Docker"
source: "2026-07-19 — Galaxy Watch 6 Health-Bridge Session (3 Bienen Schwarm-Build)"
license: MIT
trigger_keywords: ['grafana', 'monitoring', 'docker', 'influxdb', 'stack']
keywords: ['grafana', 'monitoring', 'docker', 'influxdb', 'stack']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['docker-install-ubuntu']
---
# Docker InfluxDB + Grafana Monitoring Stack

## Überblick

Dieses Skill beschreibt das **Deployment eines selbst-gehosteten Docker-Stacks** aus
InfluxDB 2.x, Grafana und optional Home Assistant — für die Aufzeichnung und Visualisierung
von Zeitreihen-Daten aus Wear OS Health, IoT-Sensoren, oder beliebigen anderen Quellen.

Der Stack ist **modular**: die drei Container teilen sich ein Docker-Netzwerk und
kommunizieren via Docker-DNS (Container-Namen als Hostnames).

## Docker-Compose Skelett

Siehe `templates/docker-compose.yml` für die vollständige Vorlage mit allen drei
Services, Secrets, Healthchecks und abhängigen Netzwerken.

### Kern-Pattern

```yaml
services:
  influxdb:
    image: influxdb:2.7  # NICHT influxdb:3-core — kein Docker-Tag verfügbar!
    ports: ["8086:8086"]
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
      DOCKER_INFLUXDB_INIT_ORG: health
      DOCKER_INFLUXDB_INIT_BUCKET: health
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUXDB_TOKEN}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: ""
    depends_on: [influxdb]
    user: "472"  # Grafana-interner User — NICHT root! Sonst Permission-Issues.

  ha:
    image: ghcr.io/home-assistant/home-assistant:stable  # optional
    ports: ["8123:8123"]
    volumes: ["./homeassistant:/config"]
```

## Secret-Generierung

```bash
INFLUXDB_TOKEN=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -base64 24)
INFLUXDB_PASSWORD=$(openssl rand -base64 24)  # nur wenn explizit gesetzt

cat > .env <<EOF
INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
INFLUXDB_PASSWORD=${INFLUXDB_PASSWORD}
EOF
```

`.env` muss **vor** dem ersten `docker compose up -d` existieren.

## Setup-Workflow (nach erstem Start)

### 1. InfluxDB Bucket anlegen
```bash
ORG_ID=$(curl -s http://localhost:8086/api/v2/orgs \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" | jq -r '.orgs[0].id')

curl -X POST http://localhost:8086/api/v2/buckets \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"health\",\"orgID\":\"${ORG_ID}\",\"retentionRules\":[{\"type\":\"expire\",\"everySeconds\":31536000}]}"
```

### 2. Write-Test
```bash
curl -X POST "http://localhost:8086/api/v2/write?bucket=health&org=health" \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  -d "health,source=test hr=72,steps=500"
```
Erwartet: HTTP 204.

### 3. Grafana DataSource via API
```bash
curl -X POST http://localhost:3000/api/datasources \
  -u "admin:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"InfluxDB-v2",
    "type":"influxdb",
    "access":"proxy",
    "url":"http://influxdb:8086",
    "user":"admin",
    "database":"health",
    "basicAuth":false,
    "isDefault":true,
    "jsonData":{
      "defaultBucket":"health",
      "organization":"health",
      "tlsSkipVerify":true,
      "version":"Flux"
    }
  }'
```

### 4. Grafana Dashboard importieren
```bash
DASH_JSON=$(cat path/to/dashboard.json)
curl -X POST http://localhost:3000/api/dashboards/db \
  -u "admin:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\":${DASH_JSON},\"overwrite\":true}"
```

## Bekannte Fallstricke

### 🚫 InfluxDB 3 Core hat kein Docker-Image
**Wahrheit:** Es gibt kein `influxdb:3-core` oder `influxdb3:latest` auf Docker Hub.
Verfügbar sind nur `influxdb:2.7.x`, `influxdata/influxdb3-ui` (Web-Explorer) und
`influxdata/influxdb3-edge`. **Verwende `influxdb:2.7`** — Flux-Queries sind kompatibel
und HA-InfluxDB-Integration arbeitet nativ mit 2.x via `api_version: 2`.

### 🚫 Grafana Volume Permissions (uid 472)
**Symptom:** Grafana startet nicht, Logs zeigen `Permission denied` auf `/var/lib/grafana/data`.
**Ursache:** Volume wurde von `root` (UID 0) angelegt, Grafana läuft als UID 472.
**Fix:** `docker compose down -v` → `docker compose up -d` (Volume neu anlegen).
Nicht `chown` versuchen — das Volume ist root-owned und bratan hat keine Rechte drauf.

### 🚫 InfluxDB Content-Type für Writes
InfluxDB 2.x Line-Protocol Write braucht `Content-Type: application/octet-stream`,
**nicht** `application/json` (das ist nur für die Management-API).
Fehlerhafter Content-Type → 400 Bad Request.

### 🚫 Grafana + Home Assistant Port-Konflikte
Wenn HA mit `network_mode: host` läuft, blockiert es Port 3000 und 8123 auf dem
Host. Grafana kann dann nicht binden. **Lösung:** HA im Bridge-Mode belassen (default),
nicht `network_mode: host` verwenden.

## Verknüpfte Skills

- `wear-os-health-api-boundaries` — Research für Wear OS Health-APIs, Referenz zur
  Health Self-Host Deployment Architecture (`references/health-selfhost-deployment-architecture.md`)
- `system-documentation` — Dokumentation des Deployments nach Build

## Templates

- `templates/docker-compose.yml` — Komplette Compose-Vorlage mit 3 Services
  (InfluxDB 2.7 + Grafana + Home Assistant), Healthchecks, Secrets, Netzwerk

## Reference Files

- `references/health-selfhost-deployment-notes.md` — Live-Bericht vom 2026-07-19
  Deployment mit Write-Tests, Dashboard-Import, Stack-Verifikation
