---
name: daily-briefing
description: >-
  Use when user asks for starting a Hermes work session, reviewing the last session and open work, checking cron and system status, validating today daily note, or requesting a morning or daily briefing. NOT for end-of-session handoff or a standalone reminder about an empty daily note. Builds an evidence-backed session briefing from recent context, schedules, delivery health, optional news, and vault hygiene checks.
version: 1.4.0
author: Yuno
license: MIT
lane: koenigin
reasoning_effort: xhigh
trigger_keywords: ['session', 'daily', 'work', 'note', 'briefing']
keywords: ['session', 'daily', 'work', 'note', 'briefing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['daily-report-trigger', 'session-handoff', 'todo-kanban-promotion']
---

# Daily Briefing

Lade diese Skill zu Beginn jeder Session mit dem Benutzer (Basti). Führe das Briefing durch, bevor du mit Aufgaben beginnst.

## Ablauf

### 0. Skill-Loading (Duplicate Name Resolution)

**⚠️ Bekanntes Problem:** Es gibt ZWEI `daily-briefing` Skills:
- `/home/bratan/.hermes/skills/productivity/daily-briefing/SKILL.md`
- `/home/bratan/.hermes/skills/skills/productivity/daily-briefing/SKILL.md`

`skill_view(name='daily-briefing')` schlägt fehl mit "Ambiguous skill name".
**Fix:** Immer den QUALIFIZIERTEN Pfad nutzen: `skill_view(name='productivity/daily-briefing')`.

### 0.5. Reconstruction Mode — Makeup Briefing für fehlende Tage

**Wann anwenden:** Wenn Basti einen Tagesrückblick/eine Briefing für einen
**vergangenen Tag** nachfordert („Tagesbericht von gestern", „Mittwoch nachholen")
und kein fertiger Bericht in `~/.hermes/docus/handoffs/`, im Vault oder in
`~/.hermes/docus/reports/` existiert.

**NICHT anwenden für:** Den heutigen Tag (→ Standard-Briefing-Sektionen 1-4).

#### 0.5.1. Schrittweiser Workflow

**Schritt 1 — Bestandsaufnahme: Gespeicherte Artefakte checken**

Such parallel (batch-read) ob bereits ein Bericht existiert:
- `search_files(pattern='YYYY-MM-DD', path='~/.hermes/docus/handoffs/', target='files')` — Handoff-Berichte
- `search_files(pattern='YYYY-MM-DD', path='~/.hermes/docus/reports/', target='files')` — Sonstige Reports
- `search_files(pattern='YYYY-MM-DD', path="~/Dokumente/Obsidian Vault/06 Daily Notes/", target='files')` — Vault-Dailies
- `ls ~/.hermes/docus/handoffs/ 2>/dev/null | tail -10` — Schnelle Orientierung

→ Wenn Datei existiert: REKONSTRUKTION ABGEKÜRZT. Datei lesen, kurz prüfen ob aktuell, und so ausliefern.

**Schritt 2 — Session-Trail aufnehmen (parallel)**

Drei parallel Calls in einer `execute_code`-Batch (unabhängig voneinander):

1. **session_search(limit=10, query='<Date YYYY-MM-DD>')** — findet Sessions deren Inhalt
   das Datum erwähnt
2. **mnemosyne_recall(limit=15, query='<Date>, <Wochentag>, Hauptthemen', temporal_weight=0.7)** —
   temporal_weight=0.7 lässt jüngere Memories stärker durchschlagen als reine FTS5-Scores
3. **session_search()** (browse mode, no args) — chronologisch letzte Sessions,
   erkennt welche IDs tatsächlich am gesuchten Tag stattfanden

**Schritt 3 — Session-IDs dem Tag zuordnen**

Aus Schritt 2.3 hast du Session-IDs + Timestamps. Filtere die, deren `when`
auf den gesuchten Tag fallen (z.B. `July 15, 2026`). Das sind deine
Primärquellen.

Für jede relevante Session den bookend_start lesen:
- `session_search(session_id='<id>', around_message_id=<match_id>, window=2)`

**Schritt 4 — Mnemosyne-Konsolidierung des Tages abrufen**

`mnemosyne_recall(query='<Datum> <Projekt-Keywords>', limit=10-15, temporal_weight=0.7)`

Die Sleep-Consolidation um 04:00 am Folgetag erzeugt Episodic-Tier-Memories mit
Timestamp `YYYY-MM-DDT02:30:00` (nächster Tag) — diese enthalten die kompakten
Tagesfakten. Präferiert `source='sleep_consolidation'`-Einträge.

**Schritt 5 — System-Artefakte cross-referenzieren**

Prüfe parallel:
- `search_files(pattern='YYYY-MM-DD', path='~/.hermes/docus/handoffs/', target='files')` —
  Handoff- oder Runbook-Dateien
- `search_files(pattern='YYYY-MM-DD', path='~/10-Projekte/', target='files')` —
  Projekt-Artefakte (falls relevant)
- `cat ~/.hermes/tool-calls.log 2>/dev/null | grep '<YYYY-MM-DD>' | tail -20` —
  Tool-Call-Volumen-Einschätzung (optional)

**Schritt 6 — Synthese + Ausgabe**

Aus den Quellen destillierst du:
1. **Sessions chronologisch** — aus Session-IDs (Schritt 3)
2. **Hauptthemen & Ergebnisse** — aus Bookends + Mnemosyne (Schritt 3+4)
3. **System-Geschehen** — Cron-Ausführungen, Hintergrund-Jobs (Schritt 5)
4. **Pitfalls / Learnings** — aus Self-Improving-Memories
5. **Carry-Over** — offene Punkte für den nächsten Tag

**Format:** Der Bericht wird als `/home/bratan/.hermes/docus/handoffs/<YYYY-MM-DD>-<wochentag>-tagesbericht.md`
gespeichert. Struktur siehe `references/makeup-briefing-template.md`.

#### 0.5.2. Die drei Quell-Patterns (wichtig!)

| Quelle | Call-Pattern | Liefert |
|--------|-------------|---------|
| Session-Trail | `session_search(query='2026-07-15', limit=10)` | FTS5-Treffer im Kontext des Datums |
| Mnemosyne | `mnemosyne_recall(query='2026-07-15 <topics>', temporal_weight=0.7, limit=15)` | Strukturierte Tages-Fakten |
| System-Handoffs | `search_files(pattern='2026-07-15', path='~/.hermes/docus/')` | Fertige Artefakte |

#### 0.5.3. Wenn wenig gefunden wird

- Nur 1-2 Sessions → trotzdem Bericht schreiben, ehrlich markieren: „Rekonstruktion basiert auf N Sessions"
- Mnemosyne leer (Tag war ruhig) → „Keine nennenswerten Memories für diesen Tag"
- Weder Sessions noch Memories → „Keine Daten für diesen Tag gefunden. War wahrscheinlich ein Off-Tag."

#### 0.5.4. Pitfalls

- ❌ `session_search(limit=10)` ungefiltert liefert auch Sessions die das Datum nur
  erwähnen (z.B. in Snippets aus dem Morgen-Briefing). Immer per `when`-Feld
  der Session-IDs auf den richtigen Tag eingrenzen.
- ❌ `mnemosyne_recall` ohne `temporal_weight` rankt nach FTS5-Score, nicht nach
  Datum. Immer `temporal_weight=0.7` setzen für datums-spezifische Abfragen.
- ✅ Verifiziertes Pattern aus der 15.07.2026-Rekonstruktion (Yuno, 16.07.2026):
  6 Sessions, 12 Mnemosyne-Einträge, 3 Handoff-Checks → synthetisierter Bericht
  mit 9 Sektionen in 8.8 KB.

#### 0.5.5. Cross-Referenz

- `references/makeup-briefing-template.md` — Vorlage für Rekonstruktions-Berichte
- `weekly-insights-synthesis` — andere Metrik (Wochen-Destillation statt Tages-Rekonstruktion)
- `session-handoff` — für Modellwechsel-Handoffs, nicht Tagesberichte

### 0.9. Daily-Note Health Check — Session-Start Gate (NEU 2026-07-16)

**Wann:** Als ALLERERSTES nach Skill-Loading, vor §1. Diese Prüfung ist nicht-verhandelbar — sie läuft bei jedem Session-Start.

**Warum:** Basti's Wunsch (16.07.2026) — "vergiss bitte die tages berichte nicht mehr". Statt fixer Cron-Zeiten soll der Reminder an Session-Start hängen. Leise, sanft, ein Satz.
mehr". Statt fixer Cron-Zeiten soll der Reminder an Session-Start hängen. Leise,
sanft, ein Satz.

**Workflow:**

1. **Detection-Script ausführen:**

```bash
python3 ~/.hermes/scripts/daily-note-health.py --json 2>/dev/null || echo '{"status":"MISSING"}'
```

2. **Status interpretieren und Reminder-Verhalten wählen:**

| Status | Bedeutung | Reminder-Verhalten |
|--------|-----------|-------------------|
| `HEALTHY` | Daily hat echten Inhalt | **Still** — kein Reminder, keine Zeile |
| `PARTIAL` | Addenda vorhanden, Hauptteil leer | **Ein Satz** unten im Briefing: `📝 Daily heute hat Addenda aber kein Hauptinhalt — update ich später.` |
| `STUB` | Template-Kopie, <1000 Bytes | **Ein Satz** unten im Briefing: `📝 Daily für heute ist noch leer — kommt wenn wir fertig sind.` |
| `MISSING` | Keine Datei | **Ein Satz** unten im Briefing: `📝 Keine Daily für heute — erstelle ich wenn du willst, oder auto bei Session-Ende.` |

3. **WICHTIG — Verhaltensregeln:**

- **NIEMALS** ungefragt die Daily erstellen oder stub-heilen beim Session-Start.
  Der Reminder ist passiv — Basti entscheidet.
- **NIEMALS** mehr als einen Satz dazu sagen. Kein Aufdrängen.
- Der Reminder steht ganz UNTEN im Briefing (nach "Bin bereit!"), als leiser Footer.
- Wenn Basti direkt mit einer konkreten Aufgabe kommt (nicht "was gibt's Neues?"),
  den Reminder **überspringen** — er will arbeiten, nicht erinnert werden.
- Bei `HEALTHY`: komplett still. Keine Zeile, kein Wort.
- Die eigentliche Daily-Erstellung/Heilung passiert beim **Session-Close**
  (§2.9) oder auf explizite Anfrage — NIEMALS beim Session-Start.

4. **Edge-Case-Toleranz (documented):**

- Eine Daily kann <1000 Bytes haben und trotzdem HEALTHY sein, wenn der
  "Was lief"-Section echten Text enthält (ruhiger Tag, kurzer Eintrag).
- Eine Daily kann >3000 Bytes haben und PARTIAL sein, wenn Cron-Addenda
  die Datei aufblähen aber der Hauptinhalt leer bleibt (2026-07-16 Fall).
- Das Script prüft **Section-Content**, nicht nur Bytesize.
- Marker-Strategie: das Script matcht Header case-insensitive als Substring
  gegen mehrere Marker (`was lief`, `erkenntnisse`, `lessons learned`,
  `hauptaufgaben`, `hauptphase`). Dadurch werden Varianten wie
  `## Was lief (vermutet aus Mnemosyne-Recall)` oder
  `## Was lief am 2026-07-04` korrekt als HEALTHY erkannt.

5. **Fallback wenn Script fehlt:**

Wenn `daily-note-health.py` nicht existiert oder fehlschlägt:
- `ls -la ~/Dokumente/Obsidian\ Vault/06\ Daily\ Notes/$(date +%Y-%m-%d).md`
- Wenn Datei <1000 Bytes oder fehlt → gleicher Reminder wie oben
- Fehler nicht eskalieren — Briefing läuft normal weiter

**Cross-Reference:**
- Memory `b14b658422f017aa` — Stub-Heuristik (<1000 Bytes)
- §0.5 — Reconstruction Mode für vergangene Tage (nicht HEUTE)
- §2.7b — Root-level stub detection (misfiled dailies)
- §2.8 — Daily-Note-Sync-Discipline & Quality Gate
- §2.9 — Session-Close Workflow (wo die Daily geschrieben wird)
- `references/daily-note-health-algorithm.md` — Interna des Detection-Scripts (Multi-Marker-Strategie, Edge-Cases, Real-Vault-Testing) (Multi-Marker-Strategie, Edge-Cases, Real-Vault-Testing)

### 0.9.1 Quality-Gate-Pflicht (vor write_file)

**Regel:** Bevor eine Daily-Note finalisiert wird (Modus A: neu schreiben; Modus B: bestehende humanisieren), MUSS das Quality-Gate-Script laufen. Bei RED-Status: NICHT speichern, erst fixen.

**Aufruf:**
```bash
python3 ~/docs/system/quality-gates/daily-addendum-gate.py <daily-file>
```

**Die 5 Gates (Targets):**

| Gate | Ziel | Pitfall |
|------|------|---------|
| EmDashes | ≤ 1 | Em-Dashes brechen Markdown-Rendering, klingen unnatürlich auf Deutsch |
| Boldface | 0 | Mid-line Bold wird zu Pseudo-Headern, nur Start-of-Line-Emphasis |
| InlineHdr | 0 | `###` im Body, Sektion-Struktur nutzen statt Inline-Formatierung |
| NegParallel | 0 | Negativ-Parallelsmüssen raus (z.B. „kein X nötig") |
| WikiLink-Count | ≥ 3 | Mindestens 3 [[WikiLinks]] zu berührten Notes |

**Pitfall #5 Mitigation (Self-Verify):** Das Gate-Script hat einen `--verify-self` Modus, der die Original-Implementation gegen eine unabhängige Re-Implementation kreuz-verifiziert. So wird verhindert dass ein fehlerhafter Check selbst zum Bug wird (Lesson 2026-07-13).

**Siehe auch:**
- Daily-Patterns Resource `~/Dokumente/Obsidian Vault/05 Ressourcen/Daily-Note-Patterns - Vault-Format.md` § WikiLink-Discipline
- Mnemosyne-Memory `5ad5291037b6cb39` — Pattern „Daily-Quality-Gate ist Pflicht-Schritt (5 Gates)"
- §2.8 — Volle Daily-Note-Sync-Discipline & Quality Gate Spec

### 1. Letzte Session abrufen

Nutze `session_search(limit=2, query="")` (browse-Modus) um die letzten 1-2 Sessions zu finden. Lies die bookend_start + bookend_end der aktuellsten Session um zu sehen was zuletzt gemacht wurde und ob was offen blieb.

#### 1.0. 5-Sec-Warmup: User-Profile-Recall (NEU 2026-07-13)

Vor dem Briefing oder direkt nach dem Skill-Loading, einmalig das User-Profile laden — gibt schnellen Kontext zu Bastis Identität, Präferenzen, Working Agreement und aktiven Projekten. Verwendet die Skill `user-profile-memory`:

- Direktabruf: `skill_view(name='memory/user-profile-memory')` und Code-Snippet ausführen
- Oder semantisch: `mnemosyne_recall(query='Basti preferences working agreement', importance_weight=0.5)`
- **Trade-off:** Vollständiger Bucket-Recall kostet 1 Tool-Call + ~3-5s Lesezeit. Bei Sessionen wo Basti direkt mit konkreter Frage kommt, überspringen und nur bei Bedarf laden.

#### 1.1. Context-Gap nach Modellwechsel (WICHTIG)

Wenn der User nach einem Modellwechsel einen **spezifischen Begriff/eine Version/ein Feature** nennt (z.B. "V6", "Option 1+2+3", "Phase 4"), das du nicht in der Session-History oder im Briefing findest:

1. **Max 2 gezielte session_search-Queries** — einen Discovery-Call mit dem Begriff, ggf. einen zweiten mit Synonym
2. **Memory/Mnemosyne prüfen** — `memory(action='list', target='memory')` oder `mnemosyne_recall(query='...')`
3. **Schnelle System-Checks** — `grep -ri "V6" ~/relevant/path/` (1-2 max, nicht tief)
4. **Nicht gefunden → FRAGEN.** Sofort `clarify(choices=[...])` mit 2-4 Optionen. Kein weiteres Session-Scrollen.
5. **NIEMALS:** große Session-Transcripts (>50KB) scrollen um einen Begriff zu finden. Das kostet >5000 Tokens pro Scroll-Call und produziert selten Treffer. Lies stattdessen bookend_start + bookend_end der letzten relevanten Session — da stehen Goal + Resolution drin.
6. **NIEMALS:** `session_search(limit=10)` — 5 ist die Obergrenze. Bei 10 kommen Sessions die nichts mit dem Thema zu tun haben.

**Warum:** Diese Session hat 10+ session_search- + 8 terminal-Calls + Hunderttausende Bytes Output verbraucht, nur um einen Begriff ("V6") zu finden den es nicht gab. Ein clarify() nach 2 Minuten hätte das verhindert.

### 2. Cron-Jobs prüfen
Nutze `cronjob(action='list')` um den Status der aktiven Cronjobs zu prüfen. Achte auf:
- Fehlgeschlagene Läufe (last_status)
- Bevorstehende Läufe (next_run_at)
- Ob einer kürzlich gelaufen ist und Ergebnisse hatte
- `delivery_error` Feld — auch wenn `last_status=ok`, kann die Telegram-Delivery fehlschlagen!
- **⚠️ no_agent=true Scripts:** `last_status=ok` bedeutet **nicht zwingend** erfolgreiche Ausführung. Der Cron-Scheduler sieht nur `exit 0` (Shell-Exit-Code), nicht interne Step-Ergebnisse. Validierter Fall 2026-07-13: `orch-weekly-pipeline` zeigte `ok` aber alle 4 Steps hatten "⚠ had issues" wegen toter Skill-Pfade in den Scripts. **Bei Script-Crons immer `last_output` mitloggen oder RUNS_DIR-Logs prüfen.**

**⚠️ WICHTIG:** Die nachfolgende Tabelle ist ein SNAPSHOT — NIE als aktuell behandeln! IMMER live prüfen.

**Basti's aktive Cronjobs (Stand 2026-07-03 nach Fix — IMMER live validieren!):**

| Job | Zeit | Modus | Deliver | Status |
|-----|------|-------|---------|--------|
| `yuno-morning-briefing` | 08:00 täglich | LLM (daily-briefing) | origin | ✅ |
| `yuno-mittags-check` | 12:00 täglich | LLM (daily-briefing) | **local** | ⚠️ error → fixed |
| `yuno-abend-wrapup` | 18:00 täglich | LLM (daily-briefing) | **local** | ⚠️ error → fixed |
| `gateway-watchdog` | stündlich | Script | local | ✅ |
| `hermes-network-monitor` | alle 15 Min | Script | local | ✅ |
| `mnemosyne-sleep` | 04:00 täglich | Script | local | ✅ |
| `mnemosyne-backup` | stündlich | Script | local | ✅ |
| `gmail-organizer` | 08:00 sonntags | Script | telegram | ✅ |
| `orch-hourly-audit` | stündlich | Script | telegram | ✅ |
| `24h-audit` (NEU 2026-07-13, `8605cc063747`) | 08:00 täglich | Script (no_agent) | local | ✅ |
| `orch-weekly-pipeline` | 05:00 sonntags | Script | local | ✅ (Refactor 2026-07-13) |
| `greyhack-ci-watch` (MaxClaw) | stündlich | LLM (greyhack) | telegram:7222661188 | ⚠️ Model-Error #44585 |
| `greyhack-tool-builder` (MaxClaw) | alle 2h | LLM (greyhack) | telegram:7222661188 | ✅ |
| `github-pr-monitor` (MaxClaw) | 09:00 + 17:00 täglich | LLM | telegram:7222661188 | ✅ |
| `greyhack-mobil-watchdog` (NEU 2026-07-04) | alle 2h | LLM (skill-navigator) | telegram:7222661188 | ✅ |
| Todoist Weekly Review | Mo 09:00 | LLM (daily-briefing) | **local** | ⚠️ error → fixed |

### 2.2. Cron Delivery "Chat not found" Detection

Wenn `last_status=ok` UND `last_delivery_error="Telegram send failed: Chat not found"` (oder ähnlich):
- **Bedeutung:** Cron lief durch, Inhalt wurde generiert, aber Gateway konnte nicht in den Home-Channel senden.
- **Häufigste Ursache:** `~/.hermes/.env` (`TELEGRAM_HOME_CHANNEL=@username`) überschreibt `config.yaml` (`home_channel: <numerische_id>`). **.env gewinnt immer.** Bei Username-Versand via Bot kann das Home-Channel-Mapping fehlschlagen, selbst wenn `allowed_chats` korrekt gesetzt ist.
- **Diagnose-Schritte (read-only zuerst):**
  1. `grep -E "TELEGRAM_HOME_CHANNEL|home_channel|TELEGRAM_ALLOWED_USERS|allowed_chats" ~/.hermes/.env ~/.hermes/config.yaml` — vergleichen, Mismatch suchen
  2. **Direkttest mit curl** (entscheidet, ob Token + Chat-ID überhaupt ok sind):
     ```bash

set -euo pipefail
     TOKEN=$(grep ^TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
     curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
       -d "chat_id=<numerische_id>" -d "text=test"
     ```
     → `{"ok":true,...}` heißt: Token + Chat-ID funktionieren direkt. Dann liegt's an der Hermes-Gateway-Home-Channel-Logik (= meist .env-Override).
  3. **Gateway-Log checken**: `journalctl --user -u hermes-gateway --no-pager -n 50 | grep -A1 "home-channel\|Chat not found"` — bestätigt, ob Gateway selbst die .env-Einstellung nutzt.
- **Fix (nur nach Bestätigung des Mismatch):**
  ```bash

set -euo pipefail
  # Numerische Chat-ID in .env setzen (BEIDE Felder, nicht nur home_channel!)
  sed -i 's/^TELEGRAM_HOME_CHANNEL=@.*/TELEGRAM_HOME_CHANNEL=<numerische_id>/' ~/.hermes/.env
  sed -i 's/^TELEGRAM_ALLOWED_USERS=@.*/TELEGRAM_ALLOWED_USERS=<numerische_id>/' ~/.hermes/.env
  systemctl --user restart hermes-gateway.service
  ```
- **Verify:** `cronjob(action='run', job_id=<id>)` triggert Job manuell, prüft `last_delivery_error`.
- **Cross-Reference:** Basti's Memory hält das gleiche Pattern fest: _"Telegram Config: `telegram.allowed_chats` AND `telegram.home_channel` in config.yaml are PRIMARY. .env can override config.yaml — check BOTH."_

**Pitfall:** Nicht nur `home_channel` fixen — auch `allowed_chats` und `TELEGRAM_ALLOWED_USERS` müssen als numerische ID vorliegen, sonst greift der DM-Filter und blockt weiter.

**Letzte Änderungen (chronologisch):**

**2026-07-04:**
- `greyhack-mobil-watchdog` (job_id `6003e431dad7`, alle 2h) NEU
  LLM-watchdog für yuno_mobil-Setup-Bundle: checkt greyhack-tools + hermes-v7
  auf neue Files, meldet nur bei Änderung via Telegram
- `greyhack-ci-watch` (MaxClaw, job_id `6732ae8278ce`) Model-Error → pausiert
  Yuno's Duplikat-Cron `a167de38428d` pausiert um Doppel-Sends zu vermeiden.
  Lesson: **Immer `hermes cron list` VOR `cron create`** — Cron-Namen sind global

**2026-07-03:**
- `yuno-mittags-check` (job_id `14b4ed9fbc42`, 12:00 täglich): `deliver` → `local`
  LLM-generierter Mittags-Check, Output > 10KB → Telegram-Send-Timeout
- `yuno-abend-wrapup` (job_id `e7f24d9bb484`, 18:00 täglich): `deliver` → `local`
  LLM-generierter Wrap-up, gleiches Timeout-Problem
- Todoist Weekly Review (job_id `08ff393b7004`, Mo 09:00): `deliver` → `local`
  LLM-generierter Todoist-Review, Output > 10KB
- **Pattern:** Alle 3 sind **LLM-Cronjobs** (kein `no_agent=true` Script!) mit
  großen Reports. Telegram-Timeout trifft sowohl Skript- als auch Agent-Output.
  → Fix identisch: `deliver='local'`, Output landet in `~/.hermes/cron-output/`

**2026-06-28:**
- `orch-weekly-pipeline`: `deliver` von `telegram:7222661188` → `local`
  Pipeline lieferte ~14KB stdout → Telegram-Send-Timeout (30s).
  Fix: Nur lokales Logging. Logs unter `~/.hermes/orchestrator-*.log`.

**Script-Pfade (Stand 2026-06-28):**
- Live-Skripte: `/home/bratan/.hermes/scripts/` (NICHT `/home/bratan/scripts/`)
- Orchestrator: `/home/bratan/.hermes/scripts/orchestrator-*.sh`
- Mnemosyne-Logs: `/home/bratan/.hermes/orchestrator-*.log`

**Deprecatete/entfernte Jobs:**
- `esl-tech-news`, `greyscripts-daily-status`, `greyhack-daily-scan`, `greyhack-daily-fix` — existieren nicht mehr

### 2.1. Cron Delivery Error Detection

Wenn `last_status=ok` ABER `last_delivery_error` gesetzt ist — oder ein
Cron-Job schlicht nicht ankommt — immer **drei Patterns** checken:

| Pattern | Error-Stichwort | Diagnose | Detail |
|---|---|---|---|---|
| 1 | `Telegram send failed: Chat not found` | `TELEGRAM_HOME_CHANNEL`/`ALLOWED_USERS` auf `@username` statt numerischer `chat_id` | `references/telegram-delivery-errors.md` |
| 2 | `Telegram send failed: Timed out` | Output (Script ODER LLM-Agent) > ~10KB → Gateway-Send-Timeout (30s) | siehe unten |
| 3 | `Provider authentication failed` / `HTTP 401` | API-Key in `.env` tot | `references/telegram-delivery-errors.md` |

**Volle Diagnostic-Befehle + Fix-Schritte:** `references/telegram-delivery-errors.md`

**Pattern 2 (Timed out) — Kurzfassung:**
- **Ursache:** Job lief erfolgreich, aber Output > ~10KB verursacht Gateway-Send-Timeout
- **Fix:** `cronjob(action='update', job_id=..., deliver='local')` — Output bleibt lokal
- **Alternative:** Script/Job umbauen auf "silent on success" Pattern (nur bei Alerts output generieren)
- **Relevante Jobs:** Alle Jobs (Script ODER LLM-Agent) mit `deliver=telegram` die >5KB Output produzieren

### 2.5. Tech/Cybersecurity News (optional)
Wenn aktuell relevant oder Basti fragt:
- `curl https://www.bleepingcomputer.com/news/security/` für Security-News
- ODER: `web_search("cybersecurity news today", limit=3)` für aktuelle Incidents
- Nur einfließen lassen, wenn Basti explizit nach fragt oder Bedeutendes passiert


### 2.6. Cron DRIFT-PROTECTION (#44585) — IMMER PRÜFEN bei Briefing

**⚠️ Critical Lesson (08.07.2026):** Nach jedem Provider-Switch brechen **alle unpinned LLM-Crons** mit identischem Error-Text. Drift-Protection ist by-design als Spend-Schutz, nicht behebbar.

**Symptom im Log:**
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'X' -> 'Y'; model 'A' -> 'B'), and this job is unpinned.
```

**Detection-Schritt (IMMER Teil des Briefings):**
Vergleiche alle aktiven LLM-Crons gegen aktuelle Global-Config (`model.provider` / `model.default` in `~/.hermes/config.yaml`):
- **Job ohne `provider`/`model` → 🔴 DRIFT-RISK bei nächstem Switch
- Job mit explizitem Pinning → ✅ safe

**Audit-Befund 2026-07-10 (Basti):**
Nach Provider-Switch sind **alle 8 LLM-Crons gepinnt** ✅. Frühere Drift-Opfer:
- `multi-agent-master-workflow-8h` (`76039d75e57d`) — Pinning auf minimax/MiniMax-M3 → fixed
- `orch-weekly-pipeline` (`eef0630309b9`) — war früher als `orch-weekly-improve` (`b1381735ce35`) dokumentiert, war ein Doku-Fehler. Echtes Script nach dem Refactor: `~/.hermes/scripts/orchestrator-pipeline.sh`.

**Sonderfall `yuno-mittags-check` (`14b4ed9fbc42`):** Pin = `minimax-oauth`, NICHT `minimax`. Absichtlich anderer Billing-Pfad (OAuth statt API-Key). Achtung: Bei Switch von `minimax`/`minimax-oauth` kann das einen neuen Drift auslösen, aber das ist by-design (OAuth-Konto).

**Fix pro Job:**
```bash
cronjob action=update job_id=<id> provider=<provider> model=<model>
# BEIDE Felder müssen gesetzt sein, sonst greift die Protection NICHT
```

**Wann triggern:**
- Nach jedem `hermes config set model.provider` / `model.default`
- Vor jedem Provider-Switch (Bestandteil der Migration)
- Wöchentlich in der Sonntags-Pipeline (verhindert forgotten-Drift)

**Script-Crons (`no_agent=true`)** sind safe — kein Model involviert.

### 2.6.1. DNS-Temp-Failure vs. Drift unterscheiden (NEU 2026-07-13)

Mehrere Crons scheitern am gleichen Zeitpunkt mit `httpx.ConnectError: Temporary failure in name resolution` oder `api.<provider>.io not reachable`. Bevor du `cronjob action=update` feuerst, prüfe:

1. `journalctl --user -u hermes-gateway --no-pager -n 30` lesen. Kommen alle Errors vom gleichen Provider-HTTP-Call?
2. `date` der ersten Errors checken. Wenn alle vier bis sechs Crons im Zeitfenster von plus/minus zwei Minuten scheitern, ist es ein Provider-Outage, kein Drift.
3. `ping -c 1 api.<provider>.io` oder `curl -m 5 https://api.<provider>.io/v1/models`. Geht es jetzt, war es Transient.

Was dann?

- Transient (DNS oder Provider-Outage): kein `cronjob action=update`. Die Crons laufen beim nächsten Tick von allein wieder grün.
- Drift (Config-Provider weicht vom Job-Provider ab): `cronjob action=update job_id=<id> provider=<provider> model=<model>` mit aktuellen Werten.
- Permanent über mehrere Tage: erst DNS und Netzwerk-Hardware checken, dann die Provider-Status-Seite.

Beleg: heute Nacht um 01:33 sind vier LLM-Crons am gleichen DNS-Temp-Failure gestorben, alle gegen `api.minimax.io`. Kein Drift, weil alle Jobs gepinnt waren. Nach Provider-Recovery liefen sie automatisch wieder grün, ohne dass ich was tun musste.

### 2.7. Container/Docker-Awareness (NEU V1.1)
Wenn Hermes in einem Docker-Container läuft (Working directory = `/root`, Home = `/root`):
- `sysdoctor check` zeigt CONTAINER-Metriken, nicht Host!
- Cron-Jobs kommen vom HOST (werden via Hermes API injected, nicht via Dateisystem)
- `search_files` im Host-Pfad zeigt nicht die Host-Dateien
- Platten-Check zeigt Container-Overlay, nicht Host-SSD
→ **Bei System-Werten IMMER prüfen: Ist das der Container oder der Host?**
→ **Für System-Status besser:** `df -h /`, `free -h`, `uptime` statt `sysdoctor check`

### 2.7b. Daily-Note-Routing-Stale-Stubs Pitfall (NEU 2026-07-10, +Plugin-Discovery 2026-07-13, +Session-Close 2026-07-13)

**⚠️ Symptom:** Stubs (0–711 Bytes) im Vault-Root statt in `06 Daily Notes/`. Eine Daily-Datei, die entdeckt wird:
- am Vault-Root mit 0–711 Bytes = automatischer Stub, **kein echtes Logbuch**
- im `06 Daily Notes/`-Folder mit 711 Bytes = Stub, gleich behandeln

**Diagnose im Briefing:**
```bash
ls "/home/bratan/Dokumente/Obsidian Vault/" | grep -E '\.md$' | grep -v 'MOC -\|CHANGELOG\|Knowledge' | head -5
ls -la "/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/" | head -5
```

**Falls Stub gefunden:** Aktive Heilung = Daily mit echtem Inhalt überschreiben (≈7+ KB: Was lief, Erkenntnisse, Wiki-Links, Verifikation). Nicht löschen ohne User-Confirm (Plugin könnte nachschreiben).

**Werkstatt-Tag-Pattern (2026-07-10 validiert):** Daily-Stub → Daily mit echtem Inhalt überschreiben in Phase 4 (Schwester-Notes aus Phase 2 SOLL + Phase 3 Gap cross-linken).

**Langfrist-Fix — Plugin-Discovery (Validiert 2026-07-13):** Bevor du „Templater installieren" empfiehlst, prüfe read-only welche Plugins tatsächlich installiert sind:

```bash
ls "/home/bratan/Dokumente/Obsidian Vault/.obsidian/plugins/" 2>&1
cat "/home/bratan/Dokumente/Obsidian Vault/.obsidian/community-plugins.json"
cat "/home/bratan/Dokumente/Obsidian Vault/.obsidian/core-plugins.json"
```

Falls `templater-obsidian` und `periodic-notes` NICHT installiert sind, werden Stubs vom **Obsidian-Core-Plugin `daily-notes`** erzeugt — nicht von Templater. Korrekter Fix: zwei Config-Files schreiben, KEIN Plugin installieren:

```bash
mkdir -p "/home/bratan/Dokumente/Obsidian Vault/_templates"  # falls leer
cat > "/home/bratan/Dokumente/Obsidian Vault/.obsidian/daily-notes.json" <<'JSON'
{
  "folder": "06 Daily Notes",
  "format": "YYYY-MM-DD",
  "template": "",
  "autorun": false,
  "newFileAutomation": true
}
JSON
cat > "/home/bratan/Dokumente/Obsidian Vault/.obsidian/templates.json" <<'JSON'
{
  "folder": "_templates",
  "dateFormat": "YYYY-MM-DD",
  "timeFormat": "HH:mm"
}
JSON
# Stub im Vault-Root löschen (war Fehl-Ablage):
rm -f "/home/bratan/Dokumente/Obsidian Vault/2026-07-11.md"  # oder betroffenes Datum
```

Vorher `clarify(choices=[...])` — User-Confirm für Files in `.obsidian/` ist Pflicht (Vault-Config ist Bastis Heiligtum). Template-Files für `_templates/` sind low-risk und können direkt nach `_templates/Daily Note.md` geschrieben werden, falls ein User-Template dahinter soll.

Vollständiger Workflow: `references/stub-reconstruction-workflow.md`.

### 2.8. Daily-Note-Sync-Discipline & Quality Gate (Basti-Vision 2026-07-10, +Gate 2026-07-13, +Self-Test 2026-07-13)

**Regel:** Der Vault (`~/Dokumente/Obsidian Vault/06 Daily Notes/`) ist der **Sync-Buffer** zwischen Realität und Dokumentation. Drift > 48 h = Knowledge-Hygiene-Problem.

**SOLL:** Bei nennenswerten Session-Erkenntnissen innerhalb von 24 h (max 48 h) Daily-Note schreiben oder aktualisieren:

- Was lief (Emojis: ✅🟡🔴)
- Erkenntnisse (2-5 mit Wiki-Links zu verwandten Notes)
- Offene Punkte
- Wiki-Links zu mindestens 3 berührten Notes

**Quality Gate (zwei Modi — NEU-Write UND Humanisieren von bestehenden Dailies):**

Der Gate hat zwei Modi. Beide landen im selben bash-Check.

**Modus A — Nach Daily-Write:** Wie bisher — schreiben, dann prüfen, ggf. humanisieren und neu prüfen. Nicht durchwinken.

**Modus B — Nach Humanisieren einer bestehenden Daily:** Vor dem Fix den IST-Zustand mit den gleichen Checks analysieren, dann fixen, dann neu prüfen. Erst wenn alle Targets grün sind, den Self-Report ausliefern.

**Das bash-Check-Skript (für beide Modi):**
```bash
F="/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/$(date +%Y-%m-%d).md"
echo "EmDashes:  $(grep -c '—' "$F")"                 # Ziel ≤ 1
echo "Boldface:  $(grep -c '\*\*[^*]*\*\*' "$F")"     # Ziel: 0
echo "InlineHdr: $(grep -c '^- \*\*' "$F")"            # Ziel: 0
echo "NegParall: $(grep -cP 'kein \w+ (nötig|erforderlich)' "$F")"  # Ziel: 0
echo "WikiLinks: $(python3 -c \"import sys,re; print(re.findall(r'\[\[([^\]]+)\]\]', open('$F').read()).__len__())\")"  # Ziel ≥ 3
echo "Größe:     $(wc -c "$F")"
```

Wenn eines der Ziele verfehlt wird: humanisieren (Bold raus, Em-Dashes ersetzen, Inline-Header auflösen), neu prüfen. Nicht durchwinken.

**Self-Report-Format (Modus B):** Nachdem alle Tests grün sind, lieferst du den Report als prägnante Tabelle:

```
## Self-Report — <Aufgabenname>

**Self-Tests:**
| Test | Ziel | Ergebnis |
|---|---|---|
| Em-Dashes | ≤ 1 | 0 PASS |
| Mid-sentence Boldface | 0 | 0 PASS |
| Inline-Header Listen | 0 | 0 PASS |
| Neg-Parall | 0 | 0 PASS |
| WikiLinks | ≥ 3 | 14 PASS |

**Maßnahmen:**
- 5 Em-Dashes → 1 (nur H1)
- 6 Boldface-Blöcke geräumt
- 2 Inline-Header-Listen aufgelöst
- 3 WikiLinks korrigiert (Plain-Text → echte [[WikiLinks]])

**Datei:** <Pfad>
**Finale Größe:** <bytes> Bytes (<vorher> → <nachher>, ± X)
```

**Wichtig:** Self-Tests laufen vor dem Self-Report. Kein Report ohne ausgeführte Tests. "Ich würde jetzt testen" ist kein Test — führ das bash-Skript aus.

Hintergrund: In der 2026-07-13 Session wurden beide Dailies auf 22 Em-Dashes, 65 Boldface-Stellen und 25 Inline-Header-Listen erwischt. Der Humanizer-Skill listet 29 AI-Patterns. Die 5 Top-Patterns decken 90% der Fehler ab — die anderen (emphatic adverbs, AI-Vokabeln, bullet consistency) sind sekundär.

**IST-Drift-Detection im Briefing:**
- Zähle zuletzt geschriebene Dailies: `ls -lat "/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/" | head -5`
- Wenn letzte substanzielle Daily (≥500 Wörter) > 2 Tage her → warnen + anbieten, eine zu schreiben
- Wenn Daily-Stub (≤1000 Bytes) ohne Inhalt → täglich als Cron erzeugt, aber nicht gefüllt → Daily-Note-Cron checken

**Werkstatt-Phasen-Disziplin:** Wenn Basti "IST/SOLL evaluieren" sagt → Vault-Edits erst in Phase 4 (nach IST-Audit + SOLL-Definition + Gap-Evaluation). Phase 1-3 = reine Inspektions-Phase. Verhindert Drift-Inflation.

→ Volle Daily-Note-Format-Spec: `05 Ressourcen/Daily-Note-Patterns - Vault-Format.md` (Pflicht-Sektionen, Stimmungs-Vokabular, Wiki-Link-Minimum).

### 3. System-Schnellcheck
Führe `df -h /`, `free -h`, `uptime` aus und fasse in EINEM Satz zusammen:
- Plattenbelegung (relevanteste Partition)
- RAM-Auslastung
- Load average

**Optional: Service-Status** — Wenn Basti kürzlich gezockt hat oder Services auffällig sein könnten, prüf kurz ollama + tokentelemetry via `systemctl --user is-active`. Details und Toleranzen: `references/system-services-check.md`.

Nur erwähnen wenn etwas AUFFÄLLIG ist (Platte >80%, RAM >80%, >10 Updates).

### 4. Briefing ausgeben

Formatiere das Briefing als:

```

set -euo pipefail
╔══════════════════════════════════════╗
║   ☕ YUNO'S DAILY BRIEFING          ║
║   <DATUM>                           ║
╚══════════════════════════════════════╝

📋 LETZTES MAL:
<was wir gemacht haben, 2-3 Zeilen>
<offene Punkte>

⏰ CRONS:
<Status der Cronjobs, wenn auffällig>
(optional: "Nichts auffälliges" wenn alles läuft)

🖥️ SYSTEM:
<ein Satz, nur bei Auffälligkeiten>

───
Bin bereit! Was steht an?
```

### Wichtige Regeln
- Das Briefing muss KURZ sein — max 10-15 Zeilen Text
- Nicht jede Kleinigkeit erwähnen, nur Relevantes
- Den Yuno-Ton wahren (kreativ/humorvoll, (kappa))
- Wenn System unauffällig, den System-Teil ganz weglassen
- Cron-Teil weglassen wenn keine Cronjobs existieren oder alle grün sind
- Bei vielen offenen Punkten aus letzter Session: den wichtigsten nennen, dann fragen ob sie den Faden aufnehmen wollen

### Telegram Morning Briefing (Cron Job, delivery: "origin")

Für das `yuno-morning-briefing` und ähnliche Telegram-Cron-Jobs mit `delivery: "origin"`:
Das Format hat **drei feste Sektionen** (ESL/CS2, Tech & Security, Gaming) mit strikten Constraints
(~2500 Zeichen, Deutsch, Yuno-Ton, keine offenen Fragen, kein `send_message`).

**Volle Spezifikation:** `references/telegram-morning-briefing-format.md`

Quick pattern:
1. Run MorphReader: `python3 /home/bratan/scripts/morphreader_summary_v6.py --no-cve-ids --days 1`
2. Fallback-Datei: `/home/bratan/scripts/morphreader-briefing.md`
3. Web-Recherche wenn MorphReader leer: `curl` zu HLTV RSS + BleepingComputer
**Volle Spezifikation:** `references/telegram-morning-briefing-format.md`

### Delivery-Probleme (BadRequest, last_delivery_error)

Wenn Crons `last_delivery_error: "Telegram send failed: Chat not found"` oder ähnliches zeigen, ist die Troubleshooting-Tabelle in **`references/cron-delivery-patterns.md`** (Sektion "Troubleshooting") der schnellste Weg zur Lösung. Deckt u.a.:

- `.env` überschreibt `config.yaml` (`.env` wins)
- `@username` vs numerische `chat_id` in `TELEGRAM_HOME_CHANNEL`
- Gateway-Restart-Ordering (erster Restart nach `.env`-Patch kann noch alten Wert laden)
- `cronjob(action='update')` ohne Feld-Updates gibt "No updates provided"

### Esports / Tech News Briefing (Cron Job)

For the dedicated `esports-tech-briefing` cron job, use the resilient multi-source fallback chain. Key principle: **never rely on a single source** — HLTV and Liquipedia are frequently Cloudflare-blocked.

Full fallback recipes and source-specific curl commands: see `references/hltv-liquipedia-esports-research.md` in the `research-tools` skill.

Quick pattern:
1. Try `web_search` + `web_extract` first
2. If blocked → `curl` to **HLTV RSS** (`https://www.hltv.org/rss/news`) for esports titles (works without Cloudflare!)
3. If security news needed → `curl` to **BleepingComputer** (`https://www.bleepingcomputer.com/news/security/`)
4. If all fail → read local cache `~/Schreibtisch/wichtigsten Nachrichten.md` for last known state
5. Always note which sources were unavailable in the output

### Efficiency Notes

- **System check:** `sysdoctor check` is the preferred tool. It does disk/RAM/temp/GPU/cache/kernel/updates in one call. Fallback: manual `df -h`, `free -h`, `sensors`.
- **Gmail check:** Use server-side SEARCH (FROM/BEFORE/SUBJECT via IMAP), NOT one-by-one header fetch. Example:
  ```python
  conn.search(None, '(FROM "noreply")')     # instant
  conn.fetch(msg_id, '(BODY.PEEK[...])')     # slow - avoid for bulk
  ```
  Server-side SEARCH is ~100x faster than fetching headers individually.
- **Cron job check:** Always use `cronjob(action='list')`. Check `last_status` and `last_run_at` to see if jobs ran.
- **⚠️ web_search Firecrawl-Fallback:** `web_search` kann mit `'NoneType' object has no attribute 'status_code'` fehlschlagen (Firecrawl-Backend offline). **Sofort auf `curl` umsteigen** — HLTV RSS und BleepingComputer sind direkt per curl erreichbar und oft zuverlässiger als die Such-API. `web_extract` generiert zudem manchmal kaputte URLs (`/v2/scrape` statt voller URL) — für RSS/HTML immer direkt `curl` nutzen.

**Stub-Heilung bei Daily-Note-Stubs:** `references/stub-reconstruction-workflow.md` — 4-Phasen-Workflow (Quellen-Sammel, Synthese, Schreiben, Quality-Gate-Verifikation). Anwenden wenn Templater/Plugin einen leeren Stub produziert hat, aber eine Session stattfand.

### 2.9. Session-Close Workflow — Memory-Triple-Write + Daily-Addendum (NEU 2026-07-13)

**Gegenstück zum Session-Start-Briefing.** Wenn eine Session abgeschlossen ist
(Basti sagt "okay", "passt", "tagesabschluss", oder du bist durch mit den Tasks),
führe diesen Workflow durch. Synchronisiert drei Orte:

1. **Daily Note (Vault)** — das Logbuch des Tages aktualisieren
2. **Mnemosyne private Memory** — task-tracking/selbstverbesserung Fakten speichern
3. **Mnemosyne shared Memory** — Nutzer-Präferenzen persistieren

#### 2.9.1. Daily-Addendum Pattern (Multi-Phase-Tag)

Wenn ein Tag mehrere Arbeitsphasen hat (z. B. morgens Vault-Reparatur, mittags
Mission-B, abends Audit), **nicht die komplette Daily umschreiben**, sondern ein
Addendum anhängen.

**Format:**
```markdown
## <Tageszeit>-Addendum: 🅲️ <Phase-Titel>

Stand <Uhrzeit> Berlin, <Kurzbeschreibung>.

**Ablauf in Zahlen:** <Zahlen, Fakten, Dauer>

**Wichtigste Befunde:** <Bulletpoints, was rauskam>

**Dinge NICHT gemacht:** <Scope-Limits, warum> (wichtig für nächste Session)

**Dinge die bleiben:** <Offene Punkte, nächste Schritte>

## Mood / Energy (Update)

<Vorherige Mood> → Nach der Phase: <neue Mood>. <Begründung>.

## Wiki-Links (Ergänzungen <Phase>)

- <Link 1> — <Kontext>
- <Link 2> — <Kontext>
```

**Regeln:**
- Mood/Energy mit **Timestamp** — vorher vs. nachher, nicht nur Endzustand
- Wiki-Links: dedizierter Block pro Addendum, nicht in den Haupt-Block mergen
- "Dinge NICHT gemacht" ist **genauso wichtig** wie "Was lief" — verhindert Scope-Creep
- Header am Ende (`---` + `> Diese Datei ist das Logbuch.`) bleibt erhalten — nicht duplizieren
- Tags im YAML-Frontmatter um neue Phasen ergänzen

**Anker-Patch:** Verwende `patch()` mit `---\n\n> Diese Datei ist das Logbuch.` als
`old_string`, und ersetze durch Addendum + `---\n\n> Diese Datei ist das Logbuch.`

**Pitfall:** Wenn die Daily schon ein Addendum hat, nicht überschreiben — ein
zweites Addendum darunter hängen.

#### 2.9.2. Memory-Triple-Write

Nach dem Daily-Addendum drei Memory-Writes:

| Ziel | Importance | Source | Inhalt |
|------|-----------|--------|--------|
| **Mnemosyne private** | 0.85–0.90 | `task-tracking` | Session-Ergebnisse: was gemacht, was nicht, Skill-Updates, offene Punkte. Prägnant. |
| **Mnemosyne shared** | 0.80 | `preference` | Nutzer-Präferenz aus dieser Session (z. B. "bei sudo-Blockern Runbook statt Bypass"). |
| **Mnemosyne private** | 0.90 | `task-tracking` | **Doppelter Tagesabschluss**: Verbindung beider Phasen in einem Memory. |

## 3. Deep Audit — Daily-Tracking-Vollständigkeit

**Wann anwenden:** Wenn Basti fragt "sind alle Tage getrackt?" / "bitte tiefer" / "daily-briefing audit" — explizite Audit-Anfrage, kein Routine-Vorgang.

**Ziel:** Vollständigkeits-Check über alle 4 Track-Systeme — Vault Daily-Notes, Hermes Handoffs, Cron, Mnemosyne — plus Inhalts-Mining (Größen-Drift, Wiki-Link-Vernetzung, Mood/Energy, Section-Header-Inventur).

### 3.1. Systematischer Audit — 4-Schichten-Check

**Schritt 1 — Vault Daily-Notes (primäre Quelle):**
```bash
ls -la "/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/"
```
Prüfe: lückenlose Coverage (jeder Tag seit 2026-06-28 hat ein File), keine Stubs unter 1000 Bytes.

Referenz: `references/daily-notes-deep-audit-reichweite.md` (Stand: 2026-07-16, 19 Tage 100%).

**Schritt 2 — Hermes Handoffs (formale Tagesberichte):**
```bash
ls ~/.hermes/docus/handoffs/ | grep -E '2026-'
```
Handoffs sind **nicht** für jeden Tag nötig — nur für besondere Abschlüsse (Themen-Patches, Closings, große Swarm-Operationen). Erwartete Dichte: ~4-6 über 3 Wochen.

**Schritt 3 — Crontab Daily-Tracking-Jobs:**
```bash
crontab -l | grep -iE "daily|tagesbericht|weekly-digest"
```
Erwartet: daily-note-cron.sh (06:00 täglich) + weekly-digest (Sonntag 22:00). Der Session-Start-Trigger (§0.9) ergänzt die fixen Cron-Zeiten.

**Schritt 4 — Mnemosyne Daily-Track Memories:**

Mnemosyne hostet 3 critical-importance Memories für Daily-Discipline:
- `b14b658422f017aa` (importance 0.60, recall_count 32+) — Daily-Discipline Regel
- `38633f3e32adc109` (importance 0.85, aktuell) — Session-Start Trigger Pattern
- `4845ce726ddace4a` (importance 0.88, recall_count 16+) — Quality-Gate Pflicht

Mnemosyne Stats check: `mnemosyne_stats()` via Tool-Call (kein CLI verfügbar).

### 3.2. Deep Mining — Inhalts-Analyse

Führe Python-Mining über alle Daily-Notes durch (via execute_code, nicht Terminal):

```python
# 5 Mining-Schritte:
# 1. Größen-Drift (chronologisch, mit Visualisierung █ pro 500B)
# 2. Wiki-Link-Vernetzung (Top-Targets, Unique-Count)
# 3. Frontmatter Mood/Energy-Inventur (unique Values)
# 4. Section-Header-Inventur (alle ## und ### Header, Top 25)
# 5. Trigger-Klassifikation (health-check.py --date auf jeden Tag)
```

Referenz: `references/2026-07-16-deep-audit-findings.md` für Baseline-Zahlen.

### 3.3. Interpretation — was die Zahlen bedeuten

| Messung | Erwartung | Warnsignal |
|---|---|---|
| Vault-Coverage | 100% (jeder Tag seit 28.06.) | Lücke > 3 Tage |
| Avg. Größe | ~7 KB (bimodal: 3-5 KB Setup / 8-17 KB Arbeits-Phase) | Unter 1000 B = Stub |
| Wiki-Links/Daily | ≥10 im Durchschnitt | Unter 3 = zu wenig vernetzt |
| Unique Targets | 80-100 | Unter 50 = Wiki-Isolation |
| Unique Section-Header | 15-25 | Unter 5 = kein Struktur-Wachstum |
| Trigger Reminder | 95% still | Feuert bei HEALTHY = False Positive |
| Mood-Coverage | ≥50% der Tage | Unter 30% = Stimmungsblindheit |

### 3.4. Bekannte Edge-Cases (aus 2026-07-16 Audit)

1. **`2026-07-05 - Phase 2 Final.md`** — Kein Tagesjournal sondern Cluster-Phase-Doku im falschen Ordner. Vom Trigger als PARTIAL klassifiziert aber keine echte Lücke.
2. **Multi-File-Dailies** — Manche Tage haben Zusatz-Files (`- Abend.md`, `- Phase 2 Final.md`). Der Trigger prüft NUR das Haupt-File (ohne Suffix) gegen die Marker-Liste.
3. **Periodic-Notes Plugin** — Erstellt Template-Stubs unter 1000 B. Trigger klassifiziert korrekt als STUB → Reminder.

### 3.5. Wenn der Audit eine Lücke findet

1. Stub-heilen per Reconstruction Mode (§0.5) — session_search + mnemosyne_recall, ~7 Min
2. Quality-Gate laufen lassen (siehe §2.8)
3. Memory Triple-Write (§2.9.2)
4. Bei Bedarf: Handoff in `~/.hermes/docus/handoffs/` schreiben
5. Wenn die Lücke strukturell ist (z.B. Cron tot) → system-documentation Skill

**Referenz:** `references/2026-07-16-deep-audit-findings.md` enthält die Baseline-Zahlen vom 16.07.2026 Audit.


**Kein Memory-Write für:**
- Session-Status ("Bin fertig") — transient
- Datei-Pfade die sich ändern — Session-Kontext
- Transiente Fehler — nächstes Mal nicht mehr da

#### 2.9.3. Skill-Version-Bump bei Session-Close

Wenn du während der Session einen Skill gepatcht hast, **bump die Version im
Frontmatter** als letzten Schritt. `patch` = Pitfall-Ergänzung, neue Sektion;
`minor` = neuer Workflow; `major` = Rewrite. Nur den geänderten Skill bumpen,
nicht alle.

#### 2.9.4. Was NICHT in Session-Close gehört

- MOC-Updates (weekly, nicht daily)
- AGENTS.md / CLAUDE.md Updates (nur auf explizite Anfrage)
- Obsidian-Vault-Restrukturierung (Inbox-First-Regel)
- Cron-Job-Anpassungen ohne konkreten Fehler

### Referenzen
- `references/briefing-template.md` — Vorlage zum Kopieren, Session-Such-Guide, Cron-Checkliste, System-Schwellwerte
- `references/telegram-morning-briefing-format.md` — Telegram Morning Briefing: 3-Sektionen-Format, Datenquellen-Reihenfolge, Parsing-Pitfalls
- `references/telegram-delivery-errors.md` — Drei Diagnostic-Patterns für Cron-Delivery-Fehler (Chat-not-found, Timed-out, Provider-401) + Provider-Switch-Workflow + Ollama-Cloud-vs-Local Klärung
- `references/morphreader-data-source.md` — MorphReader v6 CLI-Optionen, Format-Details, Fallback
- `references/gmail-server-search.md` — IMAP server-side SEARCH patterns
- `references/cron-delivery-patterns.md` — Cron output delivery conventions + Missing-Script Detection
- `references/cron-job-validation.md` — Validierungs-Checkliste nach Merges, Recovery-Flow für fehlende Skripte
- `references/system-services-check.md` — ollama/tokentelemetry service status
- `research-tools/references/hltv-liquipedia-esports-research.md` — Resilient esports/news source fallback chain
