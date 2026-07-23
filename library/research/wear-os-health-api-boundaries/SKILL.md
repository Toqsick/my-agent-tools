---


name: wear-os-health-api-boundaries
title: "Wear OS Health & Sensor-API-Grenzflächen Research"
description: 'Use when user asks about Wear OS or Galaxy Watch sensor access, Health Connect, AHS, SensorManager, Samsung Health SDKs, permissions, background collection, or open-source apps using those APIs. NOT for general smartwatch health advice or unrelated Android application work. Maps the federated API boundaries, OEM restrictions, terminology, and deployment path.'
triggers:
  - "Sensor-Zugriff auf Galaxy Watch / Wear OS recherchieren"
  - "Health API-Grenzen zwischen AOSP und Samsung verstehen"
  - "Health Connect auf Wear OS Verfügbarkeit prüfen"
  - "BODY_SENSORS / background permissions Deprecation recherchieren"
  - "Samsung Partner Program / Privileged SDK Requirements"
  - "Open-Source Fitness-App für Galaxy Watch / Wear OS finden und verifizieren"
  - "Samsung-unabhängigen Health-Tracking-Stack auf Wear OS aufbauen"
  - "Health Connect kompatible open-source Apps recherchieren"
  - "RunnerUp / OpenTracks / FitoTrack Vergleich"
  - "Welche open-source Wear OS Apps haben einen echten Wear OS companion?"
source: "Hermes Session 2026-07-19 — Galaxy Watch 6 / Wear OS Sensor & Health API Research + App-Layer Research 2026-07-19"
license: MIT
trigger_keywords: ['health', 'wear-os-health-api-boundaries', 'about', 'wear', 'galaxy']
keywords: ['health', 'user', 'asks', 'about', 'wear']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---



# Wear OS Health & Sensor-API-Grenzflächen Research

## Übersicht

Health-Sensor-Zugriff auf Wear OS (speziell Galaxy Watch) ist eine **federierte API-Landschaft**:
mehrere getrennte SDKs mit jeweils eigenen Datenquellen, Permissions und Hersteller-Bindungen.
Diese Skill-Anleitung systematisiert die Recherche, um keine API-Oberfläche auszulassen und
typische Fallstricke zu vermeiden.

## Architecture Overview — Die 4+ relevanten API-Oberflächen

```
┌────────────────────────────────────────────────────────┐
│                      Galaxy Watch                       │
│  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │  Android Health   │  │  Samsung Health Platform     │ │
│  │  Services (AHS)   │  │  (com.samsung...health)      │ │
│  │  ─────────────── │  │  ──────────────────────────  │ │
│  │  Guaranteed data  │  │  RAW ECG @ 500 Hz           │ │
│  │  HR, Steps, Loc   │  │  RAW PPG @ 25/100 Hz        │ │
│  │  Optional: SpO2,  │  │  BIA, MF-BIA                │ │
│  │  SkinTemp, Sleep   │  │  IBI/HRV granular           │ │
│  │                   │  │  SkinTemp, SweatLoss         │ │
│  └──────────────────┘  └─────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Android SensorManager                               │ │
│  │  TYPE_HEART_RATE, TYPE_ACCELEROMETER, etc.           │ │
│  │  Benötigt WakeLock + Wake-Up-Sensor für Screen-Off   │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────┘
                               │ (Wearable Data Layer)
                               ▼
┌────────────────────────────────────────────────────────┐
│                   Companion Phone                        │
│  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │  Samsung Health   │  │  Health Connect             │ │
│  │  App (optional)   │  │  (NUR auf Phone!)           │ │
│  │                   │  │  50+ Data Types             │ │
│  │  Aggregiert vom   │  │  Kein Wear OS-Client       │ │
│  │  Watch via Sync   │  │                             │ │
│  └──────────────────┘  └─────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Research-Methodik

### Schritt 1: API-Inventar erstellen

Identifiziere ALLE relevanten API/Oberflächen bevor Du Detailrecherche startest.
Die typische Liste für Wear OS Health:

1. **Android Health Services (AHS)** — `androidx.health.services` — Wear OS-Systemdienst
2. **Health Connect** — `androidx.health.connect` — Phone-only, **NICHT auf Wear OS**
3. **Android SensorManager** — `android.hardware.Sensor` — Low-Level Raw-Sensoren
4. **Samsung Health Data SDK** — aggregierte Data-Historie, benötigt Samsung Health App
5. **Samsung Health Sensor SDK** — privilegierte Watch-Sensoren (ECG, PPG, BIA, etc.)
6. **Health Platform API** — `com.google.android.libraries.healthdata` — Samsung-only historische Daten

### Schritt 2: Primärquellen parallel abfragen

Nutze `web_search` für die initiale URL-Entdeckung, dann `web_extract` für die eigentliche
Dokumentation. **Erwarte 404s** — Samsung und Google restrukturieren ihre Docs-Seiten regelmäßig.

Empfohlenes Batch-Pattern:
- Batch 1: search für alle APIs + permissions + background-collection
- Batch 2: extract die überlebenden Docs-URLs
- Batch 3: recovery für 404s via site:-Suche

### Schritt 3: Begriffs-Disambiguierung (Critical!)

Die Terminologie ist **extrem verwirrend** — folgende 5 Konzepte werden oft verwechselt:

| Begriff | Was es ist | Wo es läuft | Komponente |
|---|---|---|---|
| **Health Platform** | Samsung-proprietärer Systemdienst (`com.samsung.android.service.health`) | Watch + Phone | Gatekeeper für Sensor SDK |
| **Health Connect** | Googles geräteübergreifende Health-Daten-Plattform (`androidx.health.connect`) | **NUR Phone** — offiziell "nicht auf Wear OS" (Samsung FAQ) |
| **Samsung Health** | User-facing App (Samsung Health App) | Phone + Watch | Daten-Aggregator + Sync-Brücke |
| **Health Services** | Wear OS Systemdienst (`androidx.health.services`) | Watch (alle W3+) | Google-tracked Sensor-Daten |
| **Health Data SDK** | Samsung API für historische/aggregierte Daten | Phone | Liest aus Samsung Health |

**Wichtige Erkenntnis:** Health Platform (Samsung Systemdienst) ≠ Health Connect (Google).
NICHT verwechseln. Der Samsung Health Data SDK liest aus **Samsung Health** und Health Platform,
der Samsung Health Sensor SDK (auf der Watch) liest aus Health Platform direkt.

### Schritt 4: Permission-Landschaft karieren

1. **Aktuelle (GW6, API 34-35):** `BODY_SENSORS` + `BODY_SENSORS_BACKGROUND`
2. **Zukünftige (API 36+, Wear OS 6):** Granulare `android.permission.health.READ_*` Permissions — `BODY_SENSORS` deprecated
3. **Screen-Off:** Zusätzlich nötig: WakeLock + Wake-Up-Sensor-Variante (`getDefaultSensor(type, true)`) + ForegroundService mit `type="health"`
4. **Samsung Sensor SDK:** Braucht Partner-Registration (SHA-256 im Health Platform System) — sonst `SDK_POLICY_ERROR`; Developer Mode als Workaround

### Schritt 5: Cross-Reference

Jede Behauptung gegen eine zweite Quelle prüfen. Z.B.:
- Samsung FAQ sagt "Health Connect nicht auf Wear OS" — StackOverflow (76628089) bestätigt
- AHS Compatibility Matrix zeigt optional vs guaranteed data types
- Blog-Posts vs API-Reference-Landing-Pages abgleichen

## Bekannte Fallstricke (Pitfalls)

### 🚫 Health Connect auf Wear OS existiert nicht
Samsungs offizielles FAQ: "Health Connect can be installed on Android mobile devices. It does not support Wear OS devices."
Gesundheitsdaten fließen nur indirekt: Watch → Samsung Health (Phone) → Health Connect (Phone).

### 🚫 Samsung Health App ist nicht nötig für Sensor SDK
Der Samsung Health Sensor SDK hängt von **Health Platform** auf der Watch ab, NICHT von
der Samsung Health App auf dem Phone. Umgekehrt: Samsung Health Data SDK OHNE Samsung
Health App auf dem Phone liefert leere Reads.

### 🚫 Partner Registration ist ein Muss für Distribution
Ohne Partner-Programm-Registration funktioniert Sensor SDK nur im Developer Mode:
Settings → Apps → Health Platform → Titel 10× tippen → \[Dev mode\] erscheint.

### 🚫 URL-Rot vorprogrammiert
- Samsung: `/health/android/data` → `/health/data` (manche noch 404)
- Google: `/health-and-fitness/health-connect/plan/architecture` → `/health-and-fitness/guides/health-connect/`
- Google Fit wird Ende 2026 deprecated

### 🚫 On-Demand Trackers sind restriktiv
- Nur 1 On-Demand-Tracker gleichzeitig
- Max 30 Sekunden Messdauer
- Nur im Foreground
- Während On-Demand-Messung liefern Continuous-Tracker invalid values

## App-Layer Research — Open-Source Apps die diese APIs nutzen

Zusätzlich zur API-Recherche beantwortet dieser Skill auch die Frage:
**"Welche open-source Apps nutzen diese APIs und laufen auf Galaxy Watch?"**

### Architektur-Klärung (Critical!)

Es gibt **keine vollständig open-source Alternative zu Samsung Health auf der Uhr selbst.**
Der native Sensorzugriff auf Galaxy Watch 6 (optische HR, BIA, SpO2, raw PPG/ECG)
ist an Samsung Health Platform und Health Sensor SDK gebunden, die Partner-Registration
erfordern. Die open-source Strategie ist daher **zweistufig**:

```
Watch (Samsung Health + Health Services AHS)
  ↕ Health Connect Sync (automatisch, write from Samsung Health)
Phone (OpenSource App ← Health Connect read + own GPS)
```

### Research-Methodik für App-Suche

Nutze diese Phasen wenn der User nach Apps fragt (statt nach APIs):

**Phase 1 — Quellen-Sampling:**
1. Awesome Lists scannen (`awesome-health-fitness-oss`, `awesome-wear-os`)
   → geben Überblick, aber **nie als Fakten zitieren** (nicht verifiziert)
2. GitHub / Codeberg search — Repos nach Keywords
3. Play Store + F-Droid abgleichen — die Wahrheit liegt in den Distribution-Pages

**Phase 2 — Dreieck-Verifikation:**
Jede Behauptung gegen **mindestens zwei unabhängige Quellen** prüfen:

```
GitHub (README, Commits, Tags, Releases, Issues)
  → Play Store Description (Wear OS companion erwähnt?)
  → F-Droid Anti-Features Liste (was fehlt im FOSS-Build?)
  → Letzter Commit + Release-Datum (Projekt lebendig?)
```

**Konkrete Checks (nicht verhandelbar):**
- `wear/` directory im Repo? → Indiz für native Wear OS App
- Play Store Text: "companion Wear OS app"?
- F-Droid Anti-Features: Wird Wear OS oder ANT+ entfernt?
- Letzter Commit: Wie aktiv? Releases im letzten Jahr?

**Phase 3 — Caveat-Mapping:**
Jede Empfehlung braucht explizite Begrenzungen. Typische Arten:

| Caveat-Typ | Beispiel |
|---|---|
| **Distribution Gap** | RunnerUp Wear OS = Play-only, nicht F-Droid |
| **API-Gated** | GW6 HR Sensor nur via Samsung Health → HC |
| **Architecture Limit** | OpenTracks phone-only, kein on-Watch UI |
| **In Development** | RunnerUp HC Support: Issue #1149, nicht ausgeliefert |
| **URL-Rot** | OpenTracks GitHub → Codeberg migration (2025-08) |

**Phase 4 — Empfehlungs-Matrix:**
Finale als Entscheidungsbaum statt flacher Liste:

```
Willst du:
├── Strukturiertes Workout + Watch UI?
│   └── RunnerUp (Google Play ONLY — F-Droid stripped)
├── Outdoor-GPS + GPX Export?
│   └── OpenTracks (v4.28.0+, Health Connect export)
├── Einfaches Outdoor-Logging?
│   └── FitoTrack
└── Nur Steps auf der Watch?
    └── On Track (marginal, Single-Maintainer-Risiko)
```

### Wichtiger Anti-Pattern

- **Gadgetbridge ≠ Galaxy Watch.** Gadgetbridge spricht proprietäre BT-Protokolle
  (Pebble, Mi Band, Amazfit, Bangle.js). Galaxy Watch 6 spricht diese nicht.
  Immer prüfen: „Unterstützt dein Gerät die Gadgetbridge-Protokolle?" — nicht
  automatisch annehmen.

## Verwandte Skills

- `firecrawl-web` — Web Scraping (für große Doc-Seiten)
- `research-tools` — arXiv, RSS (für Paper Discovery)
- `tech-fact-check` — Mehrquellen-Verifikationstechnik (komplementär: dort für security claims, hier für App-Recherche)
- `stl-printables-research` — Ähnliche Research/Curation-Methodik für 3D-Druck-Dateien (paralleles Workflow-Pattern)
- `docker-influx-grafana-stack` — Deployment der Infrastruktur (Docker-Stack mit InfluxDB + Grafana + Home Assistant)

## Deployment-Pfad (verifiziert 2026-07-19)

Für eine konkrete, produktiv getestete Deployment-Architektur siehe:
`references/health-selfhost-deployment-architecture.md`

Dieses Reference-Dokument beschreibt den **empfohlenen Pfad** für Galaxy Watch 6:
Watch (Samsung Health) → Phone (Health Connect) → Home Assistant → InfluxDB 2.7 → Grafana,
mit allen verifizierten Kommandos, Fallstricken und Begründungen für jede Architekturentscheidung.

## Reference Files

- `references/research-table.md` — Vollständige Evidenztabelle API/SDK-Layer (2026-07-19)
- `references/oss-apps-for-wear-os-health-connect.md` — Verifizierte open-source App-Findergebnisse + Research-Methodik (2026-07-19)
- `references/health-selfhost-deployment-architecture.md` — Konkrete Deployment-Architektur + Docker-Stack + Fallstricke aus Live-Test (2026-07-19)
