# Health Self-Host Deployment Architecture
## Erprobt auf Galaxy Watch 6 Classic → Zorin Workstation (2026-07-19)

Dieses Reference-Dokument beschreibt die **konkrete Deployment-Architektur**, die aus der
Research in die Praxis umgesetzt wurde. Es ergänzt die abstrakten API-Grenzen der
Haupt-SKILL.md um einen verifizierten, lauffähigen Pfad.

## Architektur-Entscheidung

```
[Galaxy Watch 6 Classic]
  ├── Samsung Health App (vorinstalliert, nicht entfernbar)
  │   └── sammelt: HR, Steps, SpO2, Schlaf, Workouts, Stress
  └── Wear OS Health Services (AHS) — für eigene Apps
      └── MeasureClient (HR, Steps) wenn Watch-App installiert
              │
              ▼ (automatischer Samsung Health Sync)
[Samsung Health App auf Phone]
  └── schreibt in Health Connect (automatisch seit OneUI 5+)
              │ (Health Connect API Read)
              ▼
[Home Assistant Core] — Docker-Container
  ├── HA Companion App auf Phone (Health Connect Integration)
  │   → Entities: sensor.galaxy_watch_heart_rate, sensor.galaxy_watch_steps
  └── InfluxDB-Integration sendet State-Changes als Line-Protocol
              │
              ▼
[InfluxDB 2.7] — Docker-Container
  ├── Bucket: "health" (8760h = 1 Jahr Retention)
  ├── Data: HA-State-Snapshots (HR, Steps, Distance, Calories)
  └── Flux-Queries für Aggregation über Zeitfenster
              │
              ▼
[Grafana 13.1] — Docker-Container
  └── Dashboard "Galaxy Watch 6 - Health Overview" (13 Panels)
      ├── Current HR (Gauge)
      ├── HR Timeline (7d)
      ├── Steps Today (Stat)
      ├── Daily Steps (Bar Chart, 30d)
      ├── HR Zones (Donut)
      ├── Avg HR by Hour (Heatmap)
      ├── HR Variability (Timeseries, 24h)
      ├── Calorie Burn (Stat + Timeseries)
      ├── Distance (Timeseries)
      └── 4 weitere: Sleep/Workout-integration-ready
```

## Warum dieser Pfad (nicht der direkte Watch-Sensor-Pfad)

| Ansatz | Status | Begründung |
|---|---|---|
| **Watch → Wear OS App → Phone App → InfluxDB** (dieser Pfad) | ✅ **Empfohlen** | Samsung Health Sync läuft out-of-the-box, HC-Bridge ist stabil |
| **Eigene Watch-App mit Health Services AHS direkt** | ⏳ Build-Ready | Kotlin-Code liegt im Repo, benötigt Sideload + Android-SDK |
| **Samsung Health Sensor SDK (raw PPG/ECG)** | ❌ Enterprise-Gated | Partner-Programm nötig, Dev-Mode nur zum Testen |
| **Gadgetbridge** | ❌ Nicht kompatibel | Galaxy Watch 6 spricht kein Gadgetbridge-Protokoll |

## InfluxDB-Version-Wahl (Lessons Learned)

**InfluxDB 3 Core existiert NICHT als Docker-Image** — zumindest kein offizieller
Docker-Hub-Tag für `influxdb:3-core` oder `influxdb3:latest`. Die einzigen verfügbaren
Images sind:
- `influxdb:2.7.x` (stabil, aktiv maintained, bis 2027)
- `influxdata/influxdb3-ui` (Web-UI-Explorer, kein Core)
- `influxdata/influxdb3-edge` (Edge-Only, kein voller Ersatz)

**Resümee:** InfluxDB 2.7 ist der richtige Pick für Docker-Deployments bis auf Weiteres.
Home Assistant InfluxDB-Integration arbeitet nativ mit 2.x (via `api_version: 2`).
Flux-Queries sind cross-version-kompatibel.

## Deployment-Kommandos (verifiziert)

### Stack erstmalig starten
```bash
# Secrets generieren (einmalig)
INFLUXDB_TOKEN=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -base64 24)
cat > ~/docker/health-stack/.env <<EOF
INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
EOF

# Stack starten
docker compose -f ~/docker/health-stack/docker-compose.yml up -d

# Bucket anlegen
curl -fsS -X POST http://localhost:8086/api/v2/buckets \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"health","orgID":"$(curl -s http://localhost:8086/api/v2/orgs -H "Authorization: Token ${INFLUXDB_TOKEN}" | jq -r '.orgs[0].id')","retentionRules":[{"type":"expire","everySeconds":31536000}]}'
```

### Grafana-Datasource + Dashboard provisonieren
```bash
# DataSource anlegen (Flux-Format)
curl -fsS -X POST http://localhost:3000/api/datasources \
  -u "admin:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"name":"InfluxDB-v2","type":"influxdb","access":"proxy","url":"http://influxdb:8086","user":"admin","database":"health","basicAuth":false,"isDefault":true,"jsonData":{"defaultBucket":"health","organization":"health","tlsSkipVerify":true,"version":"Flux"}}'

# Dashboard importieren (UID suchbar, json aus Datei)
DASH_JSON=$(cat ~/10-Projekte/10-active/projects/health-bridge/grafana/dashboard.json)
curl -fsS -X POST http://localhost:3000/api/dashboards/db \
  -u "admin:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\":${DASH_JSON},\"overwrite\":true}"
```

## Bekannte Fallstricke (Live-Erfahrung)

### Grafana startet nicht (Permission-Denied auf Volume)
**Symptom:** Grafana-Container restartet in Loop, Logs zeigen `mkdir: can't create directory '/var/lib/grafana/data': Permission denied`

**Ursache:** Docker-Volume wurde von `root` (UID 0) angelegt, Grafana läuft als UID 472.

**Fix:**
```bash
# Volume löschen und neu starten
docker compose down -v
docker compose up -d
# Ohne -v: Volume behält alte Permissions → gleicher Fehler
```

### InfluxDB Write-Test schlägt fehl (falscher Content-Type)
**Symptom:** curl-Write mit `Content-Type: application/json` gibt 400/500 zurück

**Fix:** Line-Protocol braucht `Content-Type: application/octet-stream` für InfluxDB 2.x API:
```bash
curl -X POST http://localhost:8086/api/v2/write?bucket=health&org=health \
  -H "Authorization: Token ${TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  -d "health,source=test hr=72,steps=500"
```

### Grafana-API: user:password per curl
Grafana-API authentifiziert per Basic Auth mit dem Admin-User (default `admin`).
Das Passwort steht in der docker-compose.yml unter `GF_SECURITY_ADMIN_PASSWORD`.
Bei Secret-Generierung aus `.env` loaded kompatibel.
