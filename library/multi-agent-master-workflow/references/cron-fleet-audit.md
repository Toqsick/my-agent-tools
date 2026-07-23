# Cron-Fleet Audit — Playbook & Lessons Learned

**Quelle:** Multi-Agent Master Workflow (Phase-1-Inventur) über Hermes-Cron-Fleet.
**Erste Validierung:** 2026-07-10, 13 Jobs (10 ok, 2 error, 1 ungetestet).
**Pattern-Klasse:** Single-Queen-Audit (kein Subagent-Dispatch nötig — Datenmenge ≤50 Jobs).

## Zweck

Systematischer Audit aller Hermes-Cron-Jobs als wiederkehrender Self-Check.
Liefert pro Slot (z.B. alle 8h) einen priorisierten Maßnahmen-Katalog mit
copy-paste-fertigen Fix-Commands.

## Schritt 1: Baseline-Inventur

```bash
# Variante A: hermes CLI
hermes cron list

# Variante B: direkt aus der JSON-DB
python3 -c "
import json
with open('/home/bratan/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for j in data['jobs']:
    print(f\"{j['id'][:8]} {j['name']:35} {j.get('schedule_display'):14} {j.get('last_status')} provider={j.get('provider') or '-':10} model={j.get('model') or '-':15} provider_snap={j.get('provider_snapshot') or 'unpinned'}\")
"
```

**Pro Job erfassen:**
- `id` (für Fix-Commands)
- `name` (lesbar)
- `enabled`, `state`
- `schedule` (Cron-Expression)
- `last_status` (ok / error / None)
- `last_error` (vollständig, **nicht abschneiden**)
- `repeat.completed` (Run-Counter)
- `last_run_at` vs. `next_run_at` (Drift-Erkennung)
- `deliver` (telegram / local)
- `model`, `provider` (welche Lane?)
- `provider_snapshot`, `model_snapshot` (gepinnt?)

## Schritt 2: Schedule-Density-Map (DOW × Hour Matrix)

Hour-of-Day-Histogramm reicht NICHT — wenn Cron-Expression z.B. `0 4 * * 0` ist
(Sonntag 04:00), wird der Lane-Konflikt mit anderen Sonntags-Jobs vom
reinen Hour-View verschluckt. **Immer 2D-Matrix bauen** (Wochentag × Stunde).

**Empfohlene Implementierung** (regex-basiert, deckt `*`, `*/n`, `a-b`, `a-b/n`,
`a,b,c` korrekt ab — die simple Split-Variante unten crasht bei `*/2` und `*`):

```python
import re
from collections import Counter

def expand(spec, lo, hi):
    """Cron-Feld expandieren. Beispiele:
       '8'      → {8}
       '0,8,16' → {0,8,16}
       '*/2'    → {0,2,4,...,22}
       '8-18/3' → {8,11,14,17}
       '*'      → {0..23} (bzw. 0..6 für DOW)
    """
    out = set()
    for token in spec.split(','):
        m = re.match(r'^\*/(\d+)$', token)
        if m:
            for v in range(lo, hi+1):
                if v % int(m.group(1)) == 0: out.add(v)
            continue
        m = re.match(r'^(\d+)/(\d+)$', token)
        if m:
            for x in range(int(m.group(1)), hi+1, int(m.group(2))): out.add(x)
            continue
        m = re.match(r'^(\d+)-(\d+)(?:/(\d+))?$', token)
        if m:
            a, b, step = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
            for x in range(a, b+1, step): out.add(x)
            continue
        if token == '*':
            out.update(range(lo, hi+1)); continue
        if token.isdigit():
            out.add(int(token))
        else:
            out.update(range(lo, hi+1))  # MON/TUE/... → konservativ
    return out

# DOW × Hour füllen
slot = Counter()
slot_jobs = {}
for j in jobs:
    parts = j['schedule'].split()
    if len(parts) != 5: continue
    for h in expand(parts[1], 0, 23):
        for d in expand(parts[4], 0, 6):
            slot[(d, h)] += 1
            slot_jobs.setdefault((d, h), []).append(j['name'])

# Matrix ausgeben
print("       " + " ".join(f"{h:02d}" for h in range(24)))
for d in range(7):
    dow = ['So','Mo','Di','Mi','Do','Fr','Sa'][d]
    cells = [f" {slot.get((d,h),0)}" if slot.get((d,h),0) else " ." for h in range(24)]
    print(f"  {dow}  " + "".join(cells))

# Overlap-Slots >= 2 Jobs
for (d, h), names in sorted(slot_jobs.items()):
    if len(names) >= 2:
        dow = ['So','Mo','Di','Mi','Do','Fr','Sa'][d]
        print(f"  {dow} {h:02d}:00  {len(names)} jobs: {names}")
```

**Trigger für Lane-Konflikt:** 3+ Jobs auf identischem (DOW, Hour)-Slot.
**Trigger für Sonntags-Stau:** mindestens ein Sonntags-Slot mit 3 Jobs UND
ein LLM-Job in der Liste (sonst ist es nur statistisches Rauschen).

## Schritt 3: Fehler-Klassen

### Klasse A — Drift-Guard-Block

**Symptom in `last_error`:**
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'zai' -> 'minimax'; model 'glm-5' -> 'minimax-m3'),
and this job is unpinned.
```

**Ursache:** Job wurde mit altem Provider/Model erstellt, globaler Default ist
inzwischen ein anderer. Hermes' Drift-Guard blockiert um ungewollte Spend zu
verhindern.

**Diagnose:**
- `provider_snapshot=None` und `model_snapshot=None` in jobs.json → Job ist **nie gepinnt** worden.
- Fehler-Text enthält direkt den CLI-Fix-Command.

**Fix-Optionen (alle 3 im Report auflisten):**

```python
# Programmatisch via cron.jobs (Stand 2026-07-11 validiert; CLI hat keine Pinning-Parameter)
import sys
sys.path.insert(0, '/home/bratan/.hermes/hermes-agent')
from cron import jobs as jobs_mod

# A1: Auf aktuelle Defaults pinnen
jobs_mod.update_job('<job_id>', {'provider_snapshot': '<current_provider>', 'model_snapshot': '<current_model>'})

# A2: Auf alte Free-Lane zurück pinnen (wenn verfügbar)
jobs_mod.update_job('<job_id>', {'provider_snapshot': 'zai', 'model_snapshot': 'glm-5'})

# A3: Job pausieren wenn nicht mehr gebraucht — MIT dokumentiertem Grund
jobs_mod.update_job('<job_id>', {
    'enabled': False,
    'state': 'paused',
    'paused_reason': '<Warum + was zur Wiederbelebung nötig ist>',
})
```

**CLI-Lücke (relevant):** `hermes cron update` existiert NICHT; `hermes cron edit` setzt
kein `provider_snapshot`/`model_snapshot`; `hermes cron pause` setzt keinen Grund.
Pinning geht nur programmatisch.

**Im Bericht:** Drift-Guard ist **by design**, nicht Bug. Spend-Entscheidung
transparent machen.

### Klasse B — Dead Hardcoded Path

**Symptom in `last_error`:**
```
Script exited with code 1
stdout:
[2026-07-08 18:49:26] === Self-Improvement Run Started ===
[2026-07-08 18:49:26] Skill: /home/bratan/.hermes/skills/orchestration/hermes-orchestration
[2026-07-08 18:49:26] Runs: /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs
[2026-07-08 18:49:26] ERROR: Runs directory missing: /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs
```

**Ursache:** Script (z.B. `~/.hermes/scripts/orchestrator-self-improve.sh`)
hat einen hardcoded Pfad auf ein Skill-Verzeichnis, das umbenannt/gelöscht wurde.

**Diagnose (immer VOR dem Fix):**
```bash
# 1. Pfad verifizieren
test -d <hardcoded_path> && echo EXISTS || echo MISSING

# 2. Wurde das Skill umbenannt?
ls <parent_dir>/ | grep -i <skill_name>

# 3. Existiert eine Alternative?
find ~/.hermes/skills -name 'SKILL.md' -path '*<keyword>*'
```

**Fix-Optionen:**
- **(B1) Pfad im Script korrigieren** — wenn das Skill umbenannt wurde, neuen Pfad einsetzen
- **(B2) Job entfernen** — `hermes cron remove <id>`, wenn das Skill komplett tot ist
- **(B3) Skill rekonstruieren** — wenn historisch wichtig, `mkdir -p <expected_path>` als Stub

### Klasse C — Silent-Stale (noch nie gelaufen)

**Symptom:** `last_run_at=None`, `last_status=None`, `repeat.completed=0`,
aber Job ist seit Tagen "scheduled".

**Diagnose:**
```bash
# 1. Script-Pfad prüfen
ls <script_name> 2>/dev/null

# 2. Dry-run VOR nächstem geplanten Lauf
bash ~/.hermes/scripts/<script>.sh 2>&1 | head -20

# 3. Telegram-Deliver? Spam-Risiko vor erstem Lauf prüfen!
```

**Fix-Optionen:**
- Dry-run + manuell triggern, dann beobachten
- Falls Spam-Risiko: `hermes cron pause <id>` bis verifiziert
- **Korrekte Re-Trigger-Sequenz (validiert 2026-07-11):**
  ```python
  from cron import jobs as jobs_mod
  jobs_mod.trigger_job('<id>')   # schedulet den Run, setzt NICHTS an Status
  # Dannach: shell out
  ```
  ```bash
  hermes cron tick   # führt due jobs aus, setzt last_run_at + last_status
  ```
  `trigger_job` alleine reicht NICHT — der Job muss danach wirklich laufen, damit
  `last_run_at` und `last_status` gesetzt werden.

### Klasse F — Silent-OK (maskierte Failures) — *neu 2026-07-11*

**Symptom:** `last_status="ok"`, Exit Code 0, aber Run-Output enthält ⚠ Warnings
und Step-Failures. Beispiel aus echtem Run:

```
[2026-07-08 18:49:26] === Weekly Pipeline Started ===
[2026-07-08 18:49:26] --- Step 0: Heuristic Extractor ---
python3: can't open file '/home/bratan/.hermes/scripts/scripts/heuristic_extractor.py': [Errno 2] No such file or directory
⚠ Heuristic extraction had issues (see log)
[2026-07-08 18:49:26] --- Step 1: Heuristic Aggregator ---
python3: can't open file '/home/bratan/.hermes/scripts/scripts/heuristic_aggregator.py': [Errno 2] No such file or directory
✗ Heuristic promotion failed
[2026-07-08 18:49:26] === Weekly Pipeline Complete ===
```

**Ursache:** Script hat einen falschen CWD-relativen Pfad (z.B. `cd scripts/` der
nach Skill-Umzug nicht mehr stimmt → `scripts/scripts/`-Doppelung). Warnings
werden nicht zu Errors promotet, Pipeline markiert sich selbst grün obwohl die
eigentlichen Heuristik-Schritte ins Leere laufen.

**Diagnose (immer zusätzlich zu `last_status`):**
```bash
# Letzten Run-Output lesen
ls -t ~/.hermes/cron/output/<job_id>/ | head -1
cat ~/.hermes/cron/output/<job_id>/<latest>.md | head -60
```

**Fix:** Relativen CWD-Pfad im Script prüfen, oft nach Skill-Konsolidierung
(`hermes-orchestration/` → `orchestration/`) verschoben. **Niemals nur auf
`last_status` vertrauen** — immer Output inspizieren, besonders bei `no_agent`-Jobs
die ihre eigene Erfolgslogik definieren.

### Klasse D — Schedule-Overlap (Lane-Throttling)

**Symptom:** Hour-of-Day-Map zeigt 3+ Jobs auf identischer Stunde
(z.B. 22:00 mit yuno-self-improve-PINNED + greyhack-knowledge-distiller).

**Diagnose:**
- Welche Jobs laufen parallel?
- Welche Provider/Modelle nutzen sie? (Lane-Konflikt-Risiko)
- Bestehen Abhängigkeiten zwischen ihnen?

**Fix-Optionen:**
- Schedule auf andere Stunde verschieben (`hermes cron update <id> schedule=...`)
- Akzeptieren wenn sequenzielle Ausführung gut getestet ist

**Wichtig (DOW-Dimension):** Hour-Only-View verschluckt Sonntags-Staus mit
Jobs die `0 X * * 0` (Sonntag-only) sind. Immer 2D-Matrix ausgeben
(siehe Schritt 2 oben) — typisches Bild: So 04:00 / 08:00 / 22:00 mit je
3 Jobs parallel.

### Klasse E — Pinning-Latenz (präventiv, 0/0-Symptom)

**Symptom:** Aktuell **kein** Job gebrochen, `last_error` überall `null`,
`last_status="ok"` für alle LLM-Jobs. **ABER:** `provider_snapshot=null` für
alle N LLM-Jobs, also 0% Pinning-Quote.

**Warum trotzdem reporten:** Beim nächsten globalen Provider/Model-Switch
fliegt die **gesamte LLM-Flotte gleichzeitig** auf den Drift-Guard. Statt
eines Cron-Fehlers pro Tag hat Basti plötzlich 8 Crash-Reports auf einmal.
Das ist eine Latenz-Landmine, kein akuter Fehler.

**Diagnose (immer ausführen, auch im "alles grün"-Fall):**
```python
# Pinning-Quote berechnen
llm_jobs = [j for j in jobs if j.get('provider')]
pinned   = [j for j in llm_jobs if j.get('provider_snapshot')]
unpinned = [j for j in llm_jobs if not j.get('provider_snapshot')]
print(f"Pinning-Quote: {len(pinned)}/{len(llm_jobs)}  "
      f"({100*len(pinned)//max(1,len(llm_jobs))}%)")
if unpinned:
    print("🟧 Unpinned LLM-Jobs (Lane-Switch-Risiko):")
    for j in unpinned:
        print(f"   {j['id'][:8]}  {j['name']:35}  "
              f"provider={j['provider']:18} model={j['model']}")
```

**Fix-Optionen (alle 3 dem Operator zur Auswahl stellen):**

```python
# E1: Bulk-Pin auf aktuelle Defaults (alle unpinned LLM-Jobs)
import sys
sys.path.insert(0, '/home/bratan/.hermes/hermes-agent')
from cron import jobs as jobs_mod

# IMMER zuerst den Audit-Cron selbst pinnen (Self-Audit-Blind-Spot!)
audit_jobs = [j for j in jobs if 'multi-agent-master-workflow' in j['name']]
for j in audit_jobs:
    jobs_mod.update_job(j['id'], {
        'provider_snapshot': j['provider'],
        'model_snapshot': j['model'],
    })

# Dann der Rest (in einer Schleife, alle in EINEM Bulk-Schritt)
llm_jobs = [j for j in jobs if j.get('provider') and not j.get('provider_snapshot')]
for j in llm_jobs:
    jobs_mod.update_job(j['id'], {
        'provider_snapshot': j['provider'],
        'model_snapshot': j['model'],
    })
print(f'Gepinnt: {len(llm_jobs)}/{len(llm_jobs)}')
```

- **(E2) Bulk-Pin auf Free-Lane** (`zai/glm-5`) — sparen, riskieren Quality-Drop
- **(E3) Akzeptieren + Cron-Watchdog aktivieren** — beim ersten Crash manuell reagieren

**Selbst-Referenzialer Sonderfall:** Der Audit-Cron selbst (z.B.
`multi-agent-master-workflow-8h`) MUSS **als erstes** gepinnt werden, weil er
das einzige Tool ist das beim Lane-Switch noch sichtbar macht was passiert.
**Self-Audit-Blind-Spot:** unpinned Audit-Cron = blind zur Lane-Switch-Zeit
genau dann wenn man's braucht. Im Bulk-Pin-Fix immer den Audit-Job zuerst
adressieren.

## Schritt 4: Report-Format (Queen-direkt)

```
## Kurzfazit
🟥 X harte Fehler, 🟧 Y Silent-Jobs, 🟨 Z Drift-Konflikte, 🟩 Rest gesund.

## 1. Inventar (Tabelle: name / schedule / status / runs / deliver / model)
## 2. Gap-Analyse
   ### Kritisch (Klasse A oder B)
   ### Hoch (Klasse C)
   ### Mittel (Klasse D, Overlaps)
## 3. Priorisierte Maßnahmen
   | Prio | Maßnahme | Aufwand | CLI-Command |
## 4. QA-Checkliste
## 5. Offene Punkte
```

**Goldene Regel:** Fix-Commands IMMER copy-paste-fertig mitliefern —
mit eingesetztem `<job_id>`. Operator soll nicht nochmal `jobs.json` öffnen müssen.

## Schritt 5: Bekannte Pitfalls

| Pitfall | Konsequenz | Mitigation |
|---|---|---|
| `provider_snapshot` und `model_snapshot` als `null` | Drift-Guard triggert beim ersten Lane-Switch | Beim Erstellen IMMER pinnen: `hermes cron create --provider X --model Y` |
| Hardcoded Skill-Pfade in `~/.hermes/scripts/*.sh` | Job bricht nach Skill-Rename silent | Script-Review: alle `SKILL_DIR=` und `RUNS_DIR=` Zeilen auf relative/auflösbare Pfade prüfen |
| `last_error`-String abschneiden | Drift-Guard-Fix-CLI geht verloren | Im Bericht immer ersten 500-800 Zeichen zitieren, Rest in Klammern |
| `repeat.completed=0` mit `last_run_at != None` | Eigene Klasse — "Never-Run-Since-Reset" | Separat dokumentieren, oft Schema-Migration |
| Provider-Lane als technische Frage framen | Falsche Erwartungshaltung | Drift-Guard ist **Spend-Entscheidung** — Lane-Kosten + Reliability gegenüberstellen |
| Pinning-Quote nicht reporten wenn 0/0-Symptom | Lane-Switch crasht 8 Jobs gleichzeitig statt 1 | Pinning-Quote **immer** ausgeben, auch im "alles grün"-Fall. 0/N unpinned = 🟧 Latenz-Risiko, nicht 🟩 OK |
| Audit-Cron nicht selbst pinnen | Self-Audit-Blind-Spot zur Lane-Switch-Zeit | Bulk-Pin-Reihenfolge: Audit-Cron zuerst (sonst sieht man den Crash-Cluster nicht) |
| Hour-Only Schedule-View | Sonntags-Stau mit `* * 0`-Jobs verschluckt | Immer 2D-Matrix DOW × Hour, sonst `0 4 * * 0`-Lane-Konflikte unsichtbar |
| Simple Split-Cron-Expander (`hour.split('/')[1]`) | Crasht bei `*/2`, `*`, `8-18/3` | Regex-basierten Expander aus Schritt 2 verwenden — deckt alle Cron-Syntax-Varianten |
| `last_status="ok"` vertrauen ohne Output zu lesen | Silent-OK: Script meldet grün obwohl Steps failed (⚠ warnings → exit 0). Heuristik-Pipelines / Aggregator-Scripts laufen oft "leise kaputt". | Immer letzten Run-Output inspizieren: `cat $(ls -t ~/.hermes/cron/output/<id>/ | head -1)`. Besonders bei `no_agent`-Jobs kritisch. |
| `hermes cron update` oder `hermes cron pin` suchen | Existiert beides nicht (Stand 2026-07-11). `hermes cron edit` setzt nur prompt/schedule/skills, KEINEN Provider/Model-Snapshot. | Pinning geht nur programmatisch: `cron.jobs.update_job(id, {'provider_snapshot': X, 'model_snapshot': Y})`. Dokumentation in dieser Reference. |
| `hermes cron pause` ohne `paused_reason` | Geisterjobs ohne Kontext — in 3 Monaten hat man 5 pausierte Jobs und weiß nicht mehr warum. | Immer direkt nach `pause` ein `update_job(id, {'paused_reason': '...'})` folgen lassen. Grund-Format: "Was kaputt ist + was zur Wiederbelebung nötig wäre". |
| `trigger_job` als "jetzt ausführen" missverstehen | `trigger_job` schedulet nur den nächsten Run, setzt KEINEN `last_run_at`. | Nach `trigger_job` immer `hermes cron tick` ausführen — DAS setzt `last_run_at` und `last_status="ok"`. |
| Bulk-Pin-Reihenfolge ohne Audit-Cron-First | Audit-Cron crasht beim Lane-Switch genau dann wenn man's am meisten braucht | Bulk-Pin IMMER mit dem Audit-Cron selbst starten (Self-Audit-Blind-Spot vermeiden). |

## Sample-Output (gekürzt, 2026-07-10 09:52 Run — Stand 2026-07-11 aktualisiert)

```
🟥 M1: multi-agent-master-workflow-8h pinnen (S, 1 Python-Import)
   # CLI hermes cron update existiert nicht. Stattdessen:
   python3 -c "import sys; sys.path.insert(0, '/home/bratan/.hermes/hermes-agent'); \
     from cron import jobs as j; \
     j.update_job('76039d75e57d', {'provider_snapshot': 'minimax', 'model_snapshot': 'MiniMax-M3'})"

🟥 M2: orch-weekly-improve reparieren oder entfernen (S)
   ls ~/.hermes/skills/orchestration/hermes-orchestration 2>/dev/null
   # wenn tot: python3 -c "...j.update_job('b1381735ce35', {'enabled': False, 'state': 'paused', 'paused_reason': '...'})"

🟧 M3: antigravity-news-watchdog vor So 10:00 triggern (S)
   # Dry-run + echten Run auslösen:
   bash ~/.hermes/scripts/antigravity-watchdog.sh 2>&1 | head -20   # dry-run
   python3 -c "...j.trigger_job('79f08e78c5a6')"                    # schedule
   hermes cron tick                                                  # executes + sets last_run_at
```

## Lessons Learned v2 (2026-07-11)

Nach 2. Audit-Durchlauf mit 13 Jobs:
- **Pinning-Mechanismus ist programmatisch-only.** Keine CLI-Kurzform. Wer
  die Reference oder den Skill ohne Python-Import-Beispiel anwendet, wird
  30 Min damit verbringen die richtige Syntax zu suchen.
- **`trigger_job` ohne `cron tick` ist nutzlos für `last_run_at`-Reparatur.**
  Häufiger Anfängerfehler.
- **`pause` ohne `paused_reason` produziert Geisterjobs.** Immer beide
  Calls hintereinander.
- **Silent-OK (Klasse F) ist neu und tückisch** — vorher nur in der Theorie
  kannte. In der Praxis: `orch-weekly-pipeline` lief wochenlang mit 4
  kaputten Steps. Hätte man nur auf `last_status` geschaut, wäre es
  unsichtbar geblieben.
- **Diff-Verify vor/nach Bulk-Pinning ist Pflicht** — man könnte\n  versehentlich `prompt`/`skills`/`schedule` ändern wenn man `update_job`\n  mit einem zu großen Dict aufruft.\n\n## Run #4: 2026-07-17 — 21 Jobs, TikTok-Fleet, Pinning-Regression 100%>89%

**Modus:** Single-Queen-Audit (16. Audit-Lauf) · **Bilanz:** 0 `last_error`/`last_status=error`, 0 Drift-Blocked, aber 1 neue unpinned echte LLM + 1 Provider-Relikt + 6 neue TikTok-Jobs.

### Kennzahlen

| Kennzahl | Wert | Status |
|----------|------|--------|
| Jobs gesamt | 21 (+8 seit Run #3) | ✅ alle lauffaehig |
| Echte LLM-Jobs (`no_agent=false + provider`) | 9 | ✅ |
| Provider-Relikte (`no_agent=true + provider`) | 1 (24h-audit) | 🟧 bekannt seit Run #3 |
| Pinning-Quote (echte LLM) | 8/9 = **89%** | 🟧 **Regression** seit Run #3 (100%) |
| Unpinned echte LLM | 1: `yuno-tiktok-evening-reflect` | 🟧 neu seit Run #3 |
| Schedule-Overlap ≥3 | 3 Slots: So 04:00 (3), So/alle 08:00 (4), So 22:00/alle 21:00 (3) | 🟨 |
| Never-Run (Silent-Stale) | 3 (yuno-tiktok-weekly-review, memory-weekly-consolidate, cron-monthly-audit) | 🟡 alle created 2026-07-15 |
| Drift-Blocked | 0 | ✅ |
| Disabled | 0 | ✅ |

### Neue Job-Familie: TikTok-Business-Fleet

Seit Run #3 kamen **6 TikTok-Jobs** dazu — alle erstellt 2026-07-15, alle designiert `1-5` (Mo-Fr) oder Sonntag. Zusammen mit den 3 bestehenden Tages-Crons (`morning-briefing`, `mittags-check`, `abend-wrapup`) bilden sie die groesste Job-Familie der Fleet.

### Pinning-Regression-Analyse

**Letzter Stand (Run #3):** 8/8 echte LLM-Jobs gepinnt = 100%.

**Aktuell:** 8/9 echte LLM-Jobs gepinnt = 89%.

**Ursache:** `yuno-tiktok-evening-reflect` (erstellt 2026-07-15, `no_agent=false`) hat `provider=minimax`, `model=MiniMax-M3`, aber `provider_snapshot=null`. Der Job laeuft aktuell — weil der globale Default noch mit `minimax/MiniMax-M3` uebereinstimmt. Sobald die Lane wechselt → Drift-Guard-Crash.

**Parallel-Relikt:** `24h-audit` hat ebenfalls `provider_snapshot=null`, aber `no_agent=true` → Provider-Relikt (bereits in Run #3 erkannt, noch nicht bereinigt).

### Schedule-Overlap-Verschaerfung

**Neuer Hot-Spot: Mo-Fr 08:00 → 4 Jobs parallel** (morning-briefing + ci-watch + master-workflow + 24h-audit). In Run #3 waren es 3 Jobs — der 24h-audit kam mit Schedule `0 8 * * *` dazu.

**So 04:00 → 3 Jobs** (mnemosyne-sleep + ci-watch + memory-weekly-consolidate). Der memory-weekly-consolidate ist neu (created 2026-07-15) und **noch nie gelaufen**.

### Never-Run Status (3 Jobs)

| Job | Created | Schedule | Naechster Trigger | Status |
|-----|---------|----------|------------------|--------|
| yuno-tiktok-weekly-review | 2026-07-15 | So 20:00 | 2026-07-19 | Script existiert, erster Run am Sonntag |
| memory-weekly-consolidate | 2026-07-15 | So 04:00 | 2026-07-19 | Script existiert, erster Run am Sonntag |
| cron-monthly-audit | 2026-07-15 | 1. 09:00 | 2026-08-01 | Script existiert, erster Run am 01.08. |

Alle drei sind **keine Silent-Stale-Anomalie** — sie wurden erst <48h vor diesem Audit erstellt.

### Single-Lane-Throttling (neues Muster)

**So 22:00**: 3 Jobs alle auf `minimax/MiniMax-M3`:
- `greyhack-knowledge-distiller` (agent, pinned)
- `greyhack-ci-watch` (agent, pinned)
- `yuno-self-improve-PINNED` (agent, pinned)

Anders als Lane-Konflikt zwischen verschiedenen Providern (Drift-Guard) oder Ressourcen-Konflikt (Schedule-Overlap) ist dies ein **Same-Provider-Throttling** — alle 3 teilen sich dieselbe API-Rate-Limit und denselben Provider-Lane-Durchsatz. Risiko: Sequenzielle Abarbeitung durch den Cron-Scheduler puffert das, aber bei laengeren Runs kann Queue-Backpressure entstehen.

### Massnahmen aus Run #4

| Prio | Massnahme | Aufwand | Detail |
|------|----------|---------|--------|
| 🟧 | **yuno-tiktok-evening-reflect pinnen** | XS | `update_job('3b92e3103455', {'provider_snapshot': 'minimax', 'model_snapshot': 'MiniMax-M3'})` |
| 🟧 | **24h-audit Provider-Relikt bereinigen** | XS | `update_job('8605cc06', {'provider': None, 'model': None})` (bereits in Run #3 empfohlen) |
| 🟡 | **3 Silent-Stale vor So 04:00 triggern** | S | Dry-Run: `bash ~/.hermes/scripts/memory_weekly_consolidate.sh && bash ~/.hermes/scripts/yuno-tiktok-weekly-review.sh` |
| 🟨 | **Single-Lane-Throttling So 22:00 beobachten** | XS | Queue-Latenz nach So 22:00 pruefen |

### Pitfalls Run #4 (Ergaenzung zu Schritt 5)

| Pitfall | Konsequenz | Mitigation |
|---------|-----------|------------|
| **Job-Familie waechst ungepinnt** | TikTok-Fleet hat 1 echten unpinned LLM-Job + 5 Scripts. Die Scripts sind harmlos, aber `yuno-tiktok-evening-reflect` crasht beim naechsten Lane-Switch | Immer beim Erstellen pinnen: `hermes cron create --provider X --model Y`. Aktuell passiert das nicht (siehe 6 TikTok-Jobs ohne Snapshot). |
| **Never-Run-Jobs <48h alt faelschlich als Anomalie klassifizieren** | Silent-Stale-Detection schlaegt bei created < 2d immer an, obwohl der Schedule erst spaeter feuert. | Pruefen: wenn `created_at > now - 48h` und `last_run_at=None`, ist es **kein** Silent-Stale — es ist ein **Pending-First-Run**. Erst wenn created > 48h + last_run_at=None = echter Silent-Stale. Siehe Lessons Learned v3 unten. |
| **Pinning-Quote-Regression erkennen** | In Run #3 war die Quote 100%. Jetzt 89%. Wenn der Audit das Delta nicht reportet, entsteht das Gefuehl "alles wie immer". | Immer Delta zum letzten Audit berechnen. Eine Zeile: `Pinning-Delta: +/-X% seit letztem Audit`. |

## Lessons Learned v3 (2026-07-17)

Nach Run #4 mit 21 Jobs:

- **Pending-First-Run von Silent-Stale unterscheiden.** Jobs, die <48h alt sind und `last_run_at=None` haben, sind keine Anomalie. Ein "echter" Silent-Stale ist created > 48h ohne je gelaufen zu sein. Ohne diese Unterscheidung alarmiert jeder neue Job beim naechsten Audit.
- **Same-Provider-Throttling als eigene Klasse.** 3 Jobs auf demselben Provider zur selben Stunde teilen API-Rate-Limits. Bisher als "normal" abgetan — aber bei teuren Modellen (Opus, Claude) oder vielen parallelen Jobs kann Queue-Backpressure entstehen.
- **Pinning-Quote-Regression passiert schnell.** In 3 Tagen (Run #3 bis Run #4) von 100% auf 89%. Jeder neue LLM-Job, der ohne Pinning erstellt wird, senkt die Quote. Ohne Delta-Report unsichtbar.

## Run #3: 2026-07-14 — 13 Jobs, Pinning 88%, 1 Provider-Relikt, 2 neue Silent-OK Ursachen\n\n**Modus:** Single-Queen-Audit (13. Audit-Lauf) · **Bilanz:** 0 `last_error`, 0 `last_status=error`, aber 5+ 🟧/🟨 Befunde.\n\n### Kennzahlen\n\n| Kennzahl | Wert | Status |\n|----------|------|--------|\n| Jobs gesamt | 13 | ✅ alle lauffähig |\n| LLM-Jobs (echte) | 8 | ✅ |\n| no_agent-Scripts mit Provider-Relikt | 1 (24h-audit) | 🟧 kein Pinning nötig |\n| Pinning-Quote (echte LLM-Jobs) | 8/8 = **100%** | ✅ korrigiert |\n| Pinning-Quote (roh, inkl. Relikte) | 8/9 = 88% | 🟧 False Positive |\n| Schedule-Overlap ≥3 | 1 (So 22:00) | 🟨 |\n| Silent-OK maskeert | 1 (orch-weekly-pipeline) | 🟧 alter Output zeigt Bug |\n| Empty-Runs-Bypass | 1 (24h-audit hourly) | 🟧 keine Daten, immer gesund |\n| Drift-Blocked / Never-Run | 0 | ✅ |\n\n### 5 neue Erkenntnisse aus Run #3\n\n#### ① Silent-OK Doppel-Pfad — neue CWD-Ursache identifiziert\n\n**Bereits bekannt (Klasse F):** `orch-weekly-pipeline` meldet `last_status=ok` obwohl\n4 Heuristik-Steps seit Wochen kaputt sind (`scripts/scripts/heuristic_extractor.py`).\n**Neu entdeckter Mechanismus:**\n\n1. **cron-scheduler setzt `cwd=str(path.parent)`** = `~/.hermes/scripts/`\n2. **Script-interne `cd scripts/`** wird dann zu `~/.hermes/scripts/scripts/`\n3. Nach Skill-Löschung (`hermes-orchestration/` → gelöscht) fiel `cd` lautlos auf CWD zurück\n\n```\ncron-scheduler:      cwd = path.parent = ~/.hermes/scripts/\nno_agent script:     cd \"$SKILL_DIR\"  → (toter Pfad, cd scheitert lautlos, bleibt in ~/.hermes/scripts/)\n                     python3 scripts/heuristic_extractor.py → .../scripts/scripts/heuristic_extractor.py ✗\n```\n\n**Diagnose (Spezialfall Silent-OK):**\n```bash\n# Zeigt: wo landet das Script wirklich?\nbash -x ~/.hermes/scripts/<script>.sh 2>&1 | grep -E \"^\\\\+ cd \" | head -5\n\n# Wenn cron-scheduler den CWD setzt (no_agent, cwd=path.parent):\npython3 -c \"\nimport os\nos.chdir('/home/bratan/.hermes/scripts')\nos.system('python3 scripts/heuristic_extractor.py 2>&1')\n\"\n```\n\n#### ② Provider-Relikt bei no_agent Scripts — Pinning-False-Positive\n\nDer `24h-audit` Job (ID `8605cc06`) hat:\n- `no_agent=true` → reines Bash-Script, **kein** LLM-Call\n- Trotzdem `provider=minimax`, `model=MiniMax-M3` aus initialem Setup\n- `provider_snapshot=null` → Audit zählt ihn fälschlich als ungepinnten LLM-Job\n\n**Wirkung:** Drückt Pinning-Quote von 100% auf 88%. Ist ein False Positive.\n\n**Korrigierte Pinning-Quote-Berechnung:**\n```python\n# Provider-Relikte rausfiltern — nur Jobs die WIRKLICH LLM brauchen\nscript_jobs = [j for j in jobs if j.get('no_agent')]\nrelics    = [j for j in script_jobs if j.get('provider')]  # no_agent + provider = Relikt\nllm_jobs  = [j for j in jobs if not j.get('no_agent') and j.get('provider')]\npinned    = [j for j in llm_jobs if j.get('provider_snapshot')]\n```\n\n**Fix-Optionen:** (A) `provider: None` setzen — bereinigt jobs.json, keine Falschmeldung mehr.\n(B) Ignorieren — harmlos aber 88% Quote alarmiert jedes Audit 🟧.\n(C) Auf Defaults pinnen — sinnlos (kein LLM).\n\n#### ③ Empty-Runs-Bypass — Pipeline ohne Daten ist immer gesund\n\n`~/.hermes/orchestrator/runs/` enthält **keine** `metrics.json`. Die Pipeline läuft\nstündlich:\n```\nNo metrics.json files found — exiting silently\n```\n→ immer grün, null Wert. Klassifizierung: **Klasse F2 (Silent-Bypass)** — der Job existiert,\nläuft fehlerfrei, produziert keinen Telegram-Output, tut aber nichts.\n\n**Diagnose:**\n```bash\nfind ~/.hermes/orchestrator/runs -name 'metrics.json' 2>/dev/null | wc -l\n# 0 → Pipeline hat nie Daten gesehen\n```\n\n**Drei Fix-Wege:** (A) Pipeline auf Dashboard-only umstellen (hourly → memory_audit_dashboard\nmit Trigger bei `amnesie > 20 || orphans > 100`). (B) Job pausieren bis Subagent-Runs\n`metrics.json` schreiben. (C) Akzeptieren — Dashboard-Step (Step 4) funktioniert.\n\n#### ④ Memory-Dashboard — reale Werte\n\nDer einzige funktionierende Step der Pipeline:\n\n| Metrik | Wert | Trigger |\n|--------|------|--------|\n| `amnesie` | 15 | 🟩 (< 20) |\n| `orphans` | 83 | 🟧 (< 100, aber knapp) |\n| Dashboard HTML | 38.5 KB | ✅ läuft |\n| `total_errors` | 0 | ✅ |\n\n#### ⑤ Schedule-Overlap So 22:00 verifiziert\n\nRun #2 Befund bestätigt. Zusätzlich: `greyhack-knowledge-distiller` (läuft nur So 22:00)\nhat **letzten Run am 2026-07-05** (= 9 Tage her → 1-2 verpasste Sonntage).\n\n### Run #3 Maßnahmen-Katalog\n\n| Prio | Maßnahme | Aufwand | Detail |\n|------|----------|---------|--------|\n| 🟧 | **24h-audit Provider-Relikt bereinigen** | XS | `update_job('8605cc06', {'provider': None, 'model': None})` |\n| 🟧 | **orch-weekly-pipeline Live-Verifikation nach So 19.07.** | S | `cat ~/.hermes/cron/output/eef0630309b9/2026-07-19_05-00-06.md \\| grep -cE 'scripts/scripts|can.t open'` — muss 0 sein |\n| 🟨 | **greyhack-knowledge-distiller 9-Tage-Drift prüfen** | XS | `ls -lt ~/.hermes/cron/output/d4badeb9/ \\| head -5` |\n| 🟨 | **Empty-Runs-Bypass evaluieren** | M | Pipeline auf Dashboard-only umstellen oder pausieren |\n\n### Pitfalls aus Run #3 (Ergänzung zu Schritt 5)\n\n| Pitfall | Konsequenz | Mitigation |\n|---------|-----------|------------|\n| no_agent-Script mit Provider-Feld aus Setup | Pinning-Quote wird künstlich gedrückt (88% statt 100%) → jedes Audit ein 🟧 Alarm | `no_agent + provider` = Provider-Relikt erkennen und `provider: None` setzen. LLM-Jobs nur an `no_agent=False/None + provider` erkennen |\n| Pipeline tot weil Datenfeed nie befüllt | Job läuft stündlich, meldet immer „gesund", produziert null Wert — Cron-Overhead ohne Wirkung | `find <runs_dir> -name metrics.json \\| wc -l` VOR dem Report. Bei 0 → Klasse F2 (Silent-Bypass) ausweisen |\n| cron-scheduler `cwd=str(path.parent)` übersehen | CWD = Scripts-Verzeichnis, nicht User-Home. `cd scripts/` im Script = `scripts/scripts/` im Output | Bei no_agent-Scripts mit relativen Pfaden: CWD-Umgebung des Schedulers beachten. Kein `cd` ohne `pwd && pwd` Guard |\n\n## Herkunft / Source-of-Truth

- Erste Anwendung: 2026-07-10, 09:52-Cron-Slot, Job `76039d75e57d` (multi-agent-master-workflow-8h)
- Belege: `~/.hermes/cron/output/76039d75e57d/2026-07-10_09-52-50.md`,
  `~/.hermes/cron/jobs.json`, `~/.hermes/scripts/orchestrator-self-improve.sh`
- Verwandt: `hermes-admin` (Cron-Job-Verwaltung), `hermes-maintenance` Section 11 (Cron Provider-Drift)