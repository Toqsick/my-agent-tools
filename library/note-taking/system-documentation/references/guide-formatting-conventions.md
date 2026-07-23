# Guide-Formatting-Conventions (Galaxy-Watch-6-Setup 2026-07-19)

> Session-Detail zur system-documentation Guide & How-To Section.
> Enthält konkrete Beispiele aus dem Galaxy Watch 6 Classic
> Health-Tracking-Setup.

## Verwendete Struktur (Phasen-Modell)

Die Doku gliedert sich in nummerierte Phasen, die chronologisch
aufbauen — späteres Set baut auf früherem auf:

```
Phase 1: InfluxDB 3 Core + Grafana      ← Basis (DB, Visualisierung)
Phase 2: Home Assistant Core             ← Middleware (Sensor-Verarbeitung)
Phase 3: Galaxy Watch 6 einrichten      ← Sensoren freischalten (Phone-Seite)
Phase 4: HA Companion (Phone + Wear)    ← Bridge zwischen Watch und HA
Phase 5: InfluxDB-Integration in HA     ← Daten fließen in Time-Series-DB
Phase 6: Open-Source-Workout-Apps       ← Optional, erweitert Funktionsumfang
```

**Regel**: Phase 1 ist immer das Foundation-Layer (DB/Infra).
Phase 2 ist die Middleware (HA/Odysseus/etc.).
Erst dann kommen Client-seitige Schritte (Phone, Watch, Endgerät).

## ASCII-Diagramm-Anforderungen

- Verwende Unicode-Box-Zeichen (`┌┐└┘│├┤─`)
- Maximal 70 Zeichen Breite (auf schmale Terminals optimiert)
- Zeige Datenfluss-Richtung mit Pfeilen an (`←`, `→`, `↓`)
- Label je Box: was läuft da? (nicht nur Technologie-Name)
- Beispiel aus Galaxy-Watch-Setup:

```
┌──────────────────────────┐         ┌──────────────────────────┐
│ Galaxy Watch 6 Classic   │  BLE    │ Android Phone (>=10)     │
│ Sensoren:                │◀───────▶│ Apps:                    │
│   - HR (optisch)         │         │   - Health Connect       │
│   - SpO2 (on-demand)     │         │   - Samsung Health       │
│   - SkinTemp             │         │     (no account)         │
│   - Accelerometer        │         │   - HA Companion (Phone) │
└──────────────────────────┘         │   - HA Companion (Wear)  │
                                     └──────────┬───────────────┘
                                                │ Data Layer API
                                                ▼
                                     ┌──────────────────────────┐
                                     │ Home Assistant Core      │
                                     │ Container                │
                                     │ - sensor.* entities      │
                                     │ - influxdb integration   │
                                     └─────┬──────────┬─────────┘
                                           │          │
                                           ▼          ▼
                                ┌─────────────────┐  ┌──────────────────┐
                                │ InfluxDB 3 Core │  │ Grafana          │
                                │ Docker          │  │ Docker           │
                                │ Time-Series DB  │  │ Dashboards       │
                                └─────────────────┘  └──────────────────┘
```

## Verification-Tabelle-Format

Jede Guide-Phase endet mit einer Verification-Tabelle.
Format: 3 Spalten (Schritt, Test-Befehl, Erwartet).

| Schritt | Test-Befehl | Erwartet |
|---|---|---|
| InfluxDB läuft | `curl http://localhost:8086/health` | `{"status":"pass"}` |
| Grafana läuft | `curl http://localhost:3000/api/health` | `{"database":"ok"}` |
| HA läuft | `curl http://localhost:8123` | HTTP 200 + HTML |
| Watch sendet HR | HA Developer Tools → States | numerischer Wert |

## Copy-Paste-Regeln

- **Jeder CLI-Befehl** muss in einem eigenen Code-Block stehen
- **Kommentare** im Code-Block auf Deutsch
- **Platzhalter** in GROSSBUCHSTABEN mit Hinweis: `BITTE-GENERIEREN-MIT-openssl-rand-hex-32`
- **docker-compose.yml** Blöcke vollständig, nicht als Diff oder Auszug
- **sed/cat/adb**-Befehle direkt ausführbar, nicht als Beschreibung

## Fehlervermeidung (aus dieser Session gelernt)

1. **Docker-Container-Name-Kollision**: Wenn Guides mehrere Docker-Stacks
   erwähnt, müssen Container-Namen eindeutig sein. Prefix wie `health-`
   oder Service-Name als Prefix nutzen.

2. **Health Connect Permissions**: Variieren zwischen Android-Versionen.
   Bei Android 14+ ist Health Connect System-App; bei 10–13 muss es
   aus Play Store installiert werden. In der Prerequisites-Sektion
   beide Fälle abdecken.

3. **Samsung-Health-ohne-Account**: Galaxy Wearable nur für Pairing öffnen.
   Danach schließen, sonst überschreibt es Health-Connect-Config.
   Samsung Health installieren OHNE Account anzumelden.

4. **HA-Integration-YAML-Deprecation**: Home Assistant 2026.9.0 entfernt
   den YAML-Import für Integrationen. InfluxDB-Integration muss über
   die UI erfolgen, nicht über `configuration.yaml`.

5. **Galaxy Wearable nicht erneut öffnen**: Nach dem initialen Pairing
   darf Galaxy Wearable nicht mehr gestartet werden — es würde die
   Health-Connect-Bridge überschreiben.

## Siehe auch

- `~/docs/system/galaxy-watch6-selfhost-setup-2026-07-19.md` — das konkrete Dokument
- `system-documentation/SKILL.md` → Guide & How-To Document Format — die allgemeine Regel
- `wear-os-health-api-boundaries` — Skill für Health-API-Recherche
