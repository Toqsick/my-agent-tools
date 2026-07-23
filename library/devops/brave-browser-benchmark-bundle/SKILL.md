---
name: brave-browser-benchmark-bundle
description: Reproduzierbares Bundle zum Vergleich mehrerer Brave-Browser-Installationen (Flatpak/.deb/Custom) auf Linux. Misst Hardware, Profile, Extensions, Cold/Warm-Start, CDP-Navigation, JS-Heap, Tab-Workloads. Verwendet psutil + Chrome DevTools Protocol via WebSocket. Erkennt VERIFIED vs UNVERIFIED strikt. Output als JSON mit SHA-256 + Markdown-Artefakte.
when_to_use: User hat mehrere Browser parallel und will verstehen welcher für welchen Use-Case besser ist. User braucht reproduzierbare Performance-Messungen mit Statistik. User will Browser-Extensions systematisch inventarisieren. CDP-Fallen gelöst (FCP via PerformanceObserver, --remote-allow-origins).
when_not_to_use: Windows/macOS (nur Linux getestet). Enterprise-Setups. Browser-Hersteller-intern. Wenn nur ein Browser installiert ist.
trigger_keywords: ['reproduzierbares', 'bundle', 'vergleich', 'mehrerer', 'brave']
keywords: ['reproduzierbares', 'bundle', 'vergleich', 'mehrerer', 'brave']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Brave-Browser-Benchmark-Bundle

Strukturiertes Bundle zum evidenzbasierten Vergleich mehrerer Browser-Installationen
auf einem Linux-Host. Basiert auf realem Projekt vom 2026-07-23 (Zorin OS 18.1,
Intel i7-13620H, Brave Stable Flatpak vs Brave Origin .deb).

## Wann benutzen

Triggere diesen Skill wenn:
- User fragt "vergleich Brave Stable mit X" oder "welcher Browser ist schneller"
- User hat Flatpak- und/oder .deb-Installationen parallel
- User braucht reproduzierbare Browser-Metriken mit Statistik
- User will wissen wie viel Speicher welche Extensions wirklich brauchen
- User fragt nach "wie schnell startet Brave" oder "verbraucht zu viel RAM"
- User erwähnt Chrome DevTools Protocol oder Performance-Messung

## Methodik (strikt befolgen)

### Phase 0: Gates definieren (VOR jedem Tool-Aufruf!)

Definiere IMMER explizite Gates für jede Aktion:

- **G1 (read-only inventory):** `lscpu`, `free`, `lsmod`, `flatpak info`, `dpkg -S`
- **G2 (passive psutil measurement):** Prozesse angucken, NICHT starten/stoppen
- **G3 (profile schema scan):** Preferences-SCHLÜSSEL lesen, KEINE WERTE
- **G4 (metadata stat):** `du -sh` auf IndexedDB/Cache, KEIN Inhalt
- **G5 (browser lifecycle):** Browser killen + neu starten — TABS GEHEN VERLOREN
- **G6 (CDP probe):** WebSocket-Calls via `--remote-debugging-port`

Frage den User EXPLIZIT für jedes Gate bevor du es nutzt. Beispiel:

> "G5 erteilen würde bedeuten: Ich darf den Browser beenden und neu starten.
> Geöffnete Tabs gehen verloren, Profile-Preferences werden gesichert."

### Phase 1: Browser-Identität klären (VOR Messungen!)

Bevor du misst: was ist der Browser WIRKLICH?

```bash
# 1. Binary-Pfad und -Typ
readlink -f /usr/bin/brave-origin
file -L /usr/bin/brave-origin
sha256sum /usr/bin/brave-origin

# 2. Echtes Binary dahinter
/opt/brave.com/brave-origin/brave --version

# 3. Wrapper-Pattern erkennen (Standard Chromium = 80 Zeilen bash)
head -n 80 /opt/brave.com/brave-origin/brave-origin

# 4. Paketquelle
dpkg -S /opt/brave.com/brave-origin/brave
flatpak info com.brave.Browser
```

Häufige Falle: "Brave Origin" klingt nach Wrapper, ist aber oft vollwertige
zweite Installation. VERIFIZIEREN bevor du irgendetwas annimmst.

### Phase 2: Bundle-Architektur

Standardisierte Struktur für reproduzierbare Vergleiche:

```
brave-comparison/
├── README.md
├── plan.md                      # Scope, Gates, Methodik
├── risk-register.md             # Risiken klassifiziert + Mitigation
├── gate-report.md               # Welche Gates erteilt?
├── research-summary.md          # Subagent-Pre-Research
├── inventory.md                 # Hardware + Software-Inventar
├── benchmark-plan.md            # Vor Messung abnicken
├── addon-integration.md         # Perplexity-Add-on Status
├── architecture-findings.md     # Code/Feature-Diff
├── final-comparison-table.md    # Verifizierte Metriken
├── tuning-plan.md               # Optimierungen mit Rückbau
├── consolidation.md             # Lessons Learned
├── collect.sh                   # Wrapper für collect_inventory.py
├── collect_inventory.py         # Read-only Inventar (psutil + subprocess)
├── run_benchmarks.py            # psutil Idle-RSS/CPU
├── cold_warm_start.py           # Cold/Warm-Start + CDP-Probe
├── cold_start_repeated.py       # Cold-Start Statistik
├── warm_start_repeated.py       # Warm-Start Statistik
├── workload_benchmark.py        # 5/10 Tab-Workload
├── redact.py                    # Nachträglich sensitive Daten redigieren
├── verify-output.py             # JSON-Schema-Validierung + SHA-256
├── benchmark-config.yaml        # Sampling-Parameter
├── requirements.txt
├── .gitignore
├── schemas/
│   ├── inventory.schema.json
│   ├── benchmarks.schema.json
│   └── manifest.schema.json
└── output/                      # Messergebnisse (NICHT in git)
```

### Phase 3: CDP-Fallen (WICHTIG — die haben mich Zeit gekostet)

Chrome DevTools Protocol hat subtile Fallen. Diese IMMER beachten:

1. **`--remote-allow-origins=*`** beim Browser-Start MUSS gesetzt sein.
   Sonst WebSocket-Handshake mit 403 Forbidden.

2. **`Performance.getMetrics` liefert FMP (FirstMeaningfulPaint), NICHT FCP!**
   Für First Contentful Paint braucht man `PerformanceObserver` mit
   `{ type: 'paint' }` registriert VOR `Page.navigate`.

3. **Browser-WebSocket** liegt unter `/json/version`, nicht in `/json/list`.

4. **`attachToTarget` mit `flatten=true`** ist essentiell. Liefert `sessionId`
   die bei jedem Call als `sessionId` mitgeschickt werden muss.

5. **Phantom-URLs:** Doku-Sites haben oft alte Pfade:
   - `/devtools-protocol/timeline/` → PHANTOM 404
   - `/devtools-protocol/tot/runtime/` → PHANTOM 404 (lowercase)
   - Korrekt: `/tot/Runtime/` und `/tot/Performance/`

### Phase 4: Statistik-Mindest-Anforderungen

Für signifikante Aussagen:
- **Cold-Start:** 5+ Runs mit 8-10s Pause (Page-Cache warmen lassen)
- **Warm-Start:** 3+ Runs mit 30s Pause (echter Warm-Start, kein Cold-Cache-Effekt)
- **Idle-Messung:** 2+ Runs à 60-120s (1s Sampling-Intervall)
- **Workloads:** Jeweils 1× pro Browser, dokumentieren welche Tabs offen waren

Berechne: Median, Mean, StdDev, Min, Max, Range.

**WICHTIG:** Erster Run nach Reboot hat KALTEN Page-Cache. Das ist nicht
vergleichbar mit 5× Statistik im warmen Cache. Beide separat dokumentieren.

### Phase 5: Output-Format

Jeder Run schreibt JSON + SHA-256:

```json
{
  "browser": "brave-origin",
  "mode": "cold_start_repeated",
  "repetitions": 5,
  "wait_between_seconds": 8,
  "runs": [
    {
      "run_number": 1,
      "cdp_available": true,
      "cdp_response_time_seconds": 0.488,
      "total_start_duration_seconds": 0.488,
      "kill_duration_seconds": 0.102,
      "kill_success": true,
      "browser_version": "Chrome/150.0.7871.182",
      "process_pid": 12345,
      "backup_dir": "/tmp/brave-benchmark-backup-...",
      "start_iso": "2026-07-23T18:16:42+00:00"
    }
  ],
  "statistics_total_duration": {
    "samples": 5,
    "median": 0.4519,
    "mean": 0.4242,
    "stdev": 0.0833,
    "min": 0.3251,
    "max": 0.5087
  },
  "timestamp": "2026-07-23T18:16:49+00:00"
}
```

## Best Practices

### Verifizierungs-Standards

1. **VERIFIED_TARGET_EVIDENCE** = Echte Messung am Zielsystem mit dokumentierter Methode
2. **GENERAL_RESEARCH** = Recherche aus autoritativen Quellen, nicht am Zielsystem
3. **RECOMMENDATION** = Handlungsempfehlung, noch zu validieren
4. **UNVERIFIED** = Keine ausreichende Evidenz

Niemals Werte extrapolieren, schätzen oder erfinden. Lieber `UNVERIFIED`
markieren als lügen.

### Anti-Patterns

- ❌ Werte aus Cloudflare-blockierten Seiten annehmen ohne Snippet-Beleg
- ❌ Browser kalt/warm verwechseln (Cache-Zustand IMMER dokumentieren)
- ❌ Process-Tree nicht traversieren bei Flatpak (bwrap-Zwischenschicht!)
- ❌ Preferences-Werte lesen (nur Schlüssel!)
- ❌ IndexedDB-Inhalte extrahieren (nur Größe + Pfad!)
- ❌ Browser ohne User-Freigabe schließen
- ❌ Subagent glauben ohne Verification (immer curl/web_search für PRE-VERIFIED)
- ❌ Doku-URLs annehmen ohne HTTP-Status-Check (Phantom-URLs!)

### Skript-Wiederverwendung

`cold_warm_start.py` enthält ein `BROWSERS`-Dict das pro Browser angepasst wird:

```python
BROWSERS = {
    "brave-origin": {
        "binary": "/usr/bin/brave-origin",
        "real_binary": "/opt/brave.com/brave-origin/brave",
        "profile_dir": "/home/<user>/.config/BraveSoftware/Brave-Origin",
        "default_profile": "Profile 1",
        "kill_pattern": "/opt/brave.com/brave-origin/brave",
    },
    "brave-browser": {
        "binary": "/usr/bin/brave-browser",
        "real_binary": "/opt/brave.com/brave/brave",
        "profile_dir": "/home/<user>/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser",
        "default_profile": "Default",
        "kill_pattern": "/app/brave/brave",
        "launch_cmd": ["flatpak", "run", "com.brave.Browser"],
    },
}
```

`find_browser_processes()` matcht per Binary-Pfad + cmdline + Parent-Traversal
(damit Flatpak-bwrap-Kinder mit erwischt werden).

## Häufige Erkenntnisse (aus realem Projekt 2026-07-23)

1. **Origin ist KEIN Wrapper** — oft 290 MB ELF-Binary hinter Wrapper-Script
2. **3 Brave-Installationen** sind auf manchen Systemen (Flatpak + .deb + Origin)
3. **Origin gewinnt Cold-Start** (37-73% schneller) durch entfallenden Flatpak-Init
4. **Flatpak-Kill = 100× langsamer** als native SIGTERM (10s vs 0.1s)
5. **Perplexity-"Complexity"-Forks** sind legitim aber NICHT das offizielle Companion
6. **Comet Browser hat keinen Linux-Build** — Hilfe-Center listet nur Win/Mac
7. **uBlock+Shields aktiv** verbrauchen ~140k declarativeNetRequest-Regeln
   → +72% JS-Heap vs ohne diese Extensions
8. **zram zu 88% voll** kann Cold-Start um 0.3-0.5s verfälschen

## Schnellstart für neues Projekt

```bash
mkdir -p ~/20-Workspace/brave-comparison/{schemas,output}
cd ~/20-Workspace/brave-comparison

# Skripte kopieren oder neu schreiben (siehe Strukturskizze oben)
# 1. plan.md mit Gates G1-G6 definieren
# 2. risk-register.md mit Risiken + Mitigation
# 3. BROWSERS-Dict in cold_warm_start.py anpassen
# 4. User-Freigaben pro Gate einholen
# 5. Messen, dokumentieren, committen

# Git-Init NICHT vergessen
git init -b main
git config user.email "yuno@bratan.local"
git config user.name "Yuno (Basti's Assistant)"
```

## Tool-Referenzen

- psutil 7.2.2: systemweit verfügbar auf Ubuntu 24.04
- websocket-client 1.9.0: systemweit verfügbar
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- web.dev Web Vitals: https://web.dev/articles/lcp
- Chromium-Versionierung: Brave nutzt eigenes 1.x-Schema (NICHT Chromium-Version)

## Lessons Learned (für Skill-Selbst-Verbesserung)

1. **Phantom-URL-Fallen sind SYSTEMATISCH** — nie lowercase annehmen
2. **Subagent-Pre-Research** sparte 30-60 min für 20-URL-Verifikation
3. **Multi-Browser-Installationen sind häufig** — vor "compare X vs Y"
   IMMER erst `ls /opt/` und `ls /var/app/` für Vollständigkeit
4. **Brave verwendet 1.x-Schema** (nicht Chromium) — bei Version-Fragen
   github.com/brave/brave-browser/releases checken
5. **Perplexity-Add-on-IDs präzise zitieren** — Fake-Listings sind real
6. **Flatpak-Profil-Pfade sind vergraben** in `.var/app/...` — ls dort
   bevor du von "kein Profil" ausgehst
7. **Browser-Wrapper-Scripts verraten Architektur** — `head -n 80` zeigt
   ob es nur Standard Chromium-Pattern ist oder Custom-Logik
