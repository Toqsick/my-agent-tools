# Health Self-Host Deployment Notes
## Live-Bericht vom 2026-07-19 — Galaxy Watch 6 Health-Bridge

## Verifizierte Stack-Konfiguration

| Container | Image | Tag/Version | Port | State |
|---|---|---|---|---|
| health-influxdb | influxdb | 2.7 | 8086 | ✅ healthy (v2.7.12) |
| health-grafana | grafana/grafana | latest (13.1.0) | 3000 | ✅ healthy |
| health-ha | ghcr.io/home-assistant/home-assistant | stable | 8123 | ✅ healthy |

## Ausführungslog

### 1. docker-compose.yml geschrieben
Dreier-Stack mit Healthchecks, Secrets aus `.env`, `health-net` Bridge-Netzwerk.
Grafana als User 472, InfluxDB init-mode setup.

### 2. Volume-Löschung nach Permission-Fehler
Erster Start: Grafana crash-loopt mit `Permission denied` auf `/var/lib/grafana/data`.
`docker compose down -v` + `docker compose up -d` hat gefixt.
`chown 472:472` ging nicht — Volume root-owned, Basti als `bratan` hat keine Rechte.

### 3. InfluxDB Init
Nach Healthcheck: Write-Test via Line-Protocol → HTTP 204.
Bucket `health` existiert (8760h = 1 Jahr).

### 4. Grafana DataSource + Dashboard
DataSource `InfluxDB-v2` via API erstellt → Status 200.
Dashboard `gw6-health-overview` via API importiert → 13 Panels, 8 Flux-Queries.

### 5. Write-Test
```bash
curl -X POST "http://localhost:8086/api/v2/write?bucket=health&org=health" \
  -H "Authorization: Token ${INFLUXDB_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  -d "health,source=test hr=72,steps=500" \
  -w "\nHTTP %{http_code}\n"
```
→ HTTP 204 ✅
→ Flux-Query: `curl -X POST http://localhost:8086/api/v2/query?org=health -H "Authorization: Token ${TOKEN}" -H "Accept: application/csv" -H "Content-Type: application/vnd.flux" -d 'from(bucket:"health") |> range(start:-1h) |> last()'`

### 6. Grafana live
Dashboard unter `http://localhost:3000/d/gw6-health-overview/galaxy-watch-6-health-overview`
aufrufbar (noch ohne Daten weil HA nicht verbunden).

## Secrets

Gespeichert in `~/docker/health-stack/.env`:
- `INFLUXDB_TOKEN` = 64 Zeichen hex (openssl rand -hex 32)
- `GRAFANA_PASSWORD` = Base64 24 Zeichen

## Repository

- Kotlin Skeleton: `~/10-Projekte/10-active/projects/health-bridge/`
- Initial Commit: `3e9b56f` auf branch `main`
- 26 Files, 9 Kotlin, 2 MD, 6 Gradle/Properties
- Gradle-Wrapper 8.9 vom raw.githubusercontent.com geladen
- Ready für `./gradlew :wear:assembleDebug` sobald Android-SDK + JDK 17 da
