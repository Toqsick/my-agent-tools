# Open-Source Fitness Apps for Wear OS / Health Connect

> Stand: 2026-07-19 · Quelle: Wear OS Fitness App Research Session
> Diese Datei dokumentiert die App-Ebene **oberhalb** der Health APIs.
> Für die API/SDK-Landschaft siehe `references/research-table.md`.

## Ausgangsfrage

Welche open-source Fitness-Apps laufen **tatsächlich** auf einer Galaxy Watch 6
(oder jeder Wear OS 4/5 Watch) — **ohne Samsung Health als primäres Tracking?**

## Kritische Architektur-Erkenntnis

**Es gibt keine vollständig open-source Alternative zu Samsung Health auf der Uhr selbst.**
Der native Sensorzugriff auf Galaxy Watch 6 (optische HR, BIA, SpO2, raw PPG/ECG)
ist an Samsung Health Platform und Health Sensor SDK gebunden, die Partner-Registration
erfordern. Die open-source Strategie ist daher **zweistufig**:

```
Watch (Samsung Health + Health Services AHS)
  ↕ Health Connect Sync (automatisch, write from Samsung Health)
Phone (OpenSource App ← Health Connect read + own GPS)
```

## Evidence-Matrix: Bewertete Apps

### RunnerUp ⭐ Top-Empfehlung für strukturierte Workouts

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | GPL-3.0 |
| **Source** | https://github.com/jonasoreland/runnerup |
| **Play Store** | https://play.google.com/store/apps/details?id=org.runnerup |
| **F-Droid** | https://f-droid.org/packages/org.runnerup.free/ |
| **Letztes Release** | v2.11.0.1 — 2026-03-29 (F-Droid) / 2026-02-21 (Play) |
| **Letzter Commit** | 2026-07-17 (2 Tage vor diesem Research) |
| **Aktivität** | 3.295 Commits, 62 Contributors, aktiv |

**Wear OS Integration:**
- Hat ein natives **Wear OS Modul** (`wear/` — eigenes `build.gradle`, eigene Activity)
- Zeigt Live-Stats (pace, Zeit, Distanz) auf der Watch
- Bietet Watch-Steuerung: Pause/Resume/Next Lap
- **⚠️ WICHTIG: Nur in der Play-Version enthalten.** Der F-Droid Build entfernt:
  - Wear OS companion (benötigt Play Services)
  - ANT+ HRM (closed-source lib)
  - MapBox (statt OsmDroid)
  - Runalyze/Dropbox-Upload

**Sourced-Recording:** Das Workout läuft auf dem **Phone** (GPS, BLE HRM),
die Watch ist ein Remote-Display + Controller.

**Health Connect:**
- Issue [#1149](https://githubissues.com/jonasoreland/runnerup/1149) — offen
- Health Connect Support ist in Entwicklung, **noch nicht ausgeliefert**

**Export & Upload:** TCX, GPX, Strava, Runalyze, RunKeeper, RunningAHEAD, WebDAV

**HR-BLE:** BLE HRM (chest strap) + ANT+ (Play version). Watch-eigene optische HR
wird nicht direkt gelesen — fließt nur via Health Connect → Samsung Health Bridge.

### OpenTracks ⭐ Top-Empfehlung für Outdoortracking & GPX

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | Apache-2.0 |
| **Source** | https://codeberg.org/OpenTracksApp/OpenTracks |
| **Play Store** | https://play.google.com/store/apps/details?id=de.dennisguse.opentracks |
| **F-Droid** | https://f-droid.org/packages/de.dennisguse.opentracks/ |
| **Letztes Release** | **v4.28.0 — 2026-07-10** (sehr aktuell) |
| **Wear OS App** | ❌ Keine native Wear OS App. Nur Phone. |

**Health Connect (NEU in v4.28.0!):**
- `WRITE_EXERCISE` + `WRITE_EXERCISE_ROUTE` permissions beobachtet
- **Exportiert Workouts in Health Connect** → Daten fließen zu anderen HC-kompatiblen Apps
- Das ist der **umgekehrte Weg** als erwartet: OpenTracks schreibt in HC, nicht liest von HC

**Herz für die Ohren:** Strukturierte Analyse, kein Samsung-Sensor-Passthrough (HC import/export).
Eigene BLE HRM + GPS.

**Sensoren:** BLE HRM, cycling cadence/speed/power sensors, eBike sensors (Stages, Shimano, etc.)

**Exportformate:** GPX 1.1, KML 2.3, KMZ 2.3 (mit eingebetteten Fotos)

**GitHub → Codeberg Migration:** Das alte GitHub-Repo
(OpenTracksApp/OpenTracks) ist seit 2025-08-24 archiviert. Der Live-Dev ist
auf Codeberg. Alle neuen Releases sind nur dort.

### FitoTrack

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | GPL-3.0 |
| **Source** | https://codeberg.org/jannis/FitoTrack |
| **F-Droid** | https://f-droid.org/packages/de.tadris.fitness/ |
| **Letztes Release** | v16.2 — 2026-06-30 |
| **Wear OS App** | ❌ Keine. Nur Phone. |

**Health Connect:** Ja, Import + Export (etabliert, anders als RunnerUp)

**Profil:** Einfaches Outdoor-Workout-Logging. Running, Cycling, Hiking, Walking +.
Weniger Features als OpenTracks, dafür einfacher.

### Paseo

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | MIT |
| **Source** | https://gitlab.com/pardomi/paseo |
| **F-Droid** | https://f-droid.org/packages/ca.chancehorizon.paseo/ |
| **Wear OS App** | ❌ Keine. Nur Phone. |

**Profil:** Reiner Step Counter + einfaches Workout-Log. Kein HR, kein GPS-Tracking
(outdoor). Minimalistisch.

**Health Connect:** Nein.

### On Track (gondwanasoft)

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | MIT |
| **Source** | https://github.com/gondwanasoft/wear-os-on-track |
| **Letztes Update** | 2025-02-12 (v1.3.1) |
| **Wear OS App** | ✅ Ja. Native Wear OS app mit Tiles + Complications. |
| **Play Store** | https://play.google.com/store/apps/details?id=au.gondwanasoftware.ontrack |

**Profil:** Zeigt Aktivitätsfortschritt im Vergleich zum Tagesziel auf der Watch.
Kein HR, kein GPS, keine Workout-Aufzeichnung. **Marginal Utility** — eher eine
Motivations-Complication als ein Tracker.

**⚠️ Autor warnt:** "The app will probably be removed from the Google Play Store
shortly due to Google's prohibition on personal developers publishing
fitness-related apps." → Einzelentwickler-Risiko.

### Gadgetbridge

| Eigenschaft | Wert |
|---|---|
| **Lizenz** | GPL-3.0 |
| **Source** | https://codeberg.org/Freeyourgadget/Gadgetbridge |
| **Letzter Commit** | 2026-07-19 (heute) |
| **Wear OS App** | ❌ Nicht für Galaxy Watch. Nur als Companion für Pebble, Mi Band, Bangle.js, etc. |

**Kardinal:** Gadgetbridge verbindet sich via proprietären BT-Protokollen mit
der **Fremd-Hardware** (Pebble, Xiaomi, Amazfit, Bangle.js). Samsung Galaxy Watch 6
spricht nicht diese Protokolle. **Nicht kompatibel.**

## Research-Methodik (wie zu diesen Ergebnissen)

Diese Methodik ist auf **jede Software-Recherche** anwendbar — nicht nur Wear OS:

### Phase 1: Quellen-Sampling

1. **Awesome Lists scannen** — `awesome-health-fitness-oss`, `awesome-wear-os`
   geben einen Überblick. Aber **nie als Fakten zitieren** — awesome lists sind
   kategorisiert nach Einreichungen, nicht nach Verifikation.
2. **GitHub search** — Repos nach Schlüsselbegriffen finden
3. **Play Store + F-Droid** — Die Distributionskanäle, die die Wahrheit sagen:
   - Play Store: Zeigt Beschreibung (Wear OS? Health Connect?), Version, Updates
   - F-Droid: Zeigt Anti-Features (welche Komponenten fehlen im Open-Source-Build),
     Permissions, tatsächliche APK-Builds

### Phase 2: Dreieck-Verifikation

Jede Behauptung aus Phase 1 muss gegen **mindestens zwei unabhängige Quellen**
geprüft werden. Das **Verifikations-Dreieck**:

```
                GitHub / Codeberg
               /        |         \
              /         |          \
     README/Description  Commits    Releases/Tags
           |                |            |
           v                v            v
    [Behauptung A]    [Aktivität]   [Version vX.Y.Z]
           \                |            /
            \               |           /
             v              v          v
          Play Store  ←→  F-Droid  ←→  Web Search
```

**Konkrete Checks:**
- **GitHub README** → Behauptet Wear OS? Behauptet Health Connect?
- **`wear/` directory** → Existiert es? (Ja bei RunnerUp, Nein bei OpenTracks/FitoTrack)
- **Play Store description** → Wörtliche Erwähnung von Wear OS companion
- **F-Droid Anti-Features** → Wenn eine App auf F-Droid Wear OS aus der
  Feature-Liste entfernt (wie RunnerUp), ist das ein harter Beweis
- **Letzter Commit + Release** → Ist das Projekt tot oder aktiv? GitHub Commits
  sind das beste Signal
- **Issue Tracker** → Health Connect Support offen/geschlossen/merged?

### Phase 3: Caveat-Mapping

Jede Empfehlung muss ihre **Begrenzungen explizit machen**:

| Caveat-Typ | Beispiele aus dieser Recherche |
|---|---|
| **Distribution Gap** | RunnerUp Wear OS = Play-only, nicht auf F-Droid |
| **Single-Maintainer Risk** | On Track — Autor sagt selbst "wird bald entfernt" |
| **API-Gated** | Galaxy Watch 6 HR Sensor nur via Samsung Health → HC |
| **Architecture Limit** | OpenTracks/FitoTrack: phone-only, kein on-Watch UI |
| **Still in Development** | RunnerUp HC import/export: Issue #1149, nicht ausgeliefert |
| **URL-Rot** | OpenTracks GitHub → Codeberg migration (2025-08) |

### Phase 4: Empfehlungs-Matrix

Baue die finale Empfehlung als **Entscheidungsbaum** statt als flache Liste:

```
Frage: "Welche App für Galaxy Watch 6 ohne Samsung Health?"

Willst du:
├── Strukturiertes Workout + Watch UI?
│   └── RunnerUp (Google Play — F-Droid ohne Wear!)
├── Outdoor-GPS-Tracking + GPX/KML Export?
│   └── OpenTracks (Apache-2.0, Health Connect export v4.28.0)
├── Einfaches Outdoor-Logging + Health Connect?
│   └── FitoTrack (GPL-3.0, simpler als OpenTracks)
└── Nur Steps + Tagesziel auf Watch?
    └── On Track (marginal, Single-Maintainer-Risiko)
```

## Empfohlener Stack (Samsung-unabhängig)

1. **Samsung Health + Health Connect auf der Watch lassen** — das ist der einzige
   Weg, die optische HR, Schritte und Workouts der Watch in open-source Apps zu
   bekommen.
2. **OpenTracks** (F-Droid/Play) — für GPS-Touren, GPX Export, BLE HRM, eBike Sensoren
3. **RunnerUp** (Play — nicht F-Droid) — für strukturierte Workouts, Intervalle,
   Audio-Cues, Strava-Upload, und Wear OS Remote
4. **FitoTrack** (F-Droid) — einfachere Alternative zu OpenTracks

## Live URLs (alle verifiziert 2026-07-19)

- OpenTracks (Codeberg, live dev): https://codeberg.org/OpenTracksApp/OpenTracks
- OpenTracks (F-Droid): https://f-droid.org/packages/de.dennisguse.opentracks/
- RunnerUp (GitHub): https://github.com/jonasoreland/runnerup
- RunnerUp (F-Droid, stripped): https://f-droid.org/packages/org.runnerup.free/
- RunnerUp (Play, full): https://play.google.com/store/apps/details?id=org.runnerup
- FitoTrack (Codeberg): https://codeberg.org/jannis/FitoTrack
- FitoTrack (F-Droid): https://f-droid.org/packages/de.tadris.fitness/
- Paseo (GitLab): https://gitlab.com/pardomi/paseo
- On Track (GitHub): https://github.com/gondwanasoft/wear-os-on-track
- Gadgetbridge (Codeberg): https://codeberg.org/Freeyourgadget/Gadgetbridge
- Gadgetbridge (F-Droid): https://f-droid.org/packages/nodomain.freeyourgadget.gadgetbridge/
- Awesome Health/Fitness OSS: https://github.com/Dieterbe/awesome-health-fitness-oss
- Awesome Wear OS: https://github.com/WearOSCommunity/awesome-wear-os
