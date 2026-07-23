# Cron Fleet Audit — Systematische Job-Flotten-Health-Prüfung

> Methodology für proaktive, vollständige Cron-Fleet-Health-Prüfungen.
> Entwickelt aus Audits auf Basti's Zorin-OS-Workstation (2026-07-11).

## Wann dieses Verfahren anwenden

- **Periodische Gesundheitsprüfung** (z.B. monatlich oder nach größerem Config-Change)
- **Post-Incident-Prophylaxe** — nachdem ein einzelner Cron gebrochen wurde, die ganze Fleet scannen
- **Vor und nach Provider/Config-Change** — sicherstellen, dass kein Scale-Effekt übersehen wird
- **Nach Skill-Cleanup/Migration** — wenn Skills gelöscht/verschoben wurden, prüfen ob Cron-Jobs auf tote Pfade zeigen

## Audit-Protokoll (4 Phasen)

### Phase 0: Baseline — alle Jobs erfassen

```python
import json
with open(os.path.expanduser('~/.hermes/cron/jobs.json')) as f:
    data = json.load(f)
jobs = data['jobs']
for j in jobs:
    pid = j.get('id','?')
    en = j.get('enabled')
    st = j.get('state','?')
    name = j.get('name','?')[:55]
    sched = j.get('schedule',{}).get('display','?')
    ls = j.get('last_status','none')
    prov = j.get('provider','?')
    mod = j.get('model','?')
    print(f'{pid} en={en} st={st} sched={sched} last={ls} prov={prov} mod={mod}')
```

**Ziel:** Schnelle Übersicht über Flottengröße, alle Namen, States, letzter Status.

**Mode-Klassifikation — nicht nur `prompt` checken:** Ein Job hat `mode=agent` wenn er **entweder** `prompt` **oder** `skills` gesetzt hat. Manche Jobs haben `prompt: ""` (leerer String) aber `skills: ['skill-name']` — das ist trotzdem ein Agent-Job. Script-Jobs haben `script` gesetzt, `prompt=null` und `skills=null`.
```python
'agent' if (j.get('prompt') or j.get('skills')) else 'script' if j.get('script') else 'unknown'
```
**Fresh-Schedule vs Actually-Stale vs Never-Fired:** Ein Silent-Stale Job (`last_run_at=None, last_status=None`) kann drei Ursachen haben:

- **Fresh schedule (kein Alarm)** — Job wurde gerade erst hinzugefügt (`created_at` nah am Audit-Zeitpunkt) und `next_run_at` liegt noch in der Zukunft. Kein Handlungsbedarf.
- **Missed-first-slot (🟧 Alarm)** — `created_at` liegt >24h zurück, `next_run_at` liegt **in der Vergangenheit**, der erste scheduled Slot wurde verpasst. Oft bei Jobs die kurz nach ihrem Schedule-Zeitpunkt erstellt wurden. Ursache: Cron-Scheduler wurde nicht getriggert oder hatte `state=unknown`.
- **Script-Stub with matching syntax (🟨 Beobachten)** — `script!=null`, kein LLM, Script existiert auf Disk mit gültiger Syntax (`bash -n` pass). Der Job ist bereit aber nie gelaufen. Triggern nach manuellem Review.

Unterscheidung: `next_run_at` mit `datetime.now()` vergleichen, `created_at` mit `next_run_at` vergleichen.

### Phase 1: Multi-Pass — Jeden Job einzeln validieren

Niemals nur `last_status` vertrauen. Drei Pässe:

**Pass 1 — Status-Check** (alle Zeilen der `list`-Ausgabe parsen):
- `enabled=False` → ist das gewollt? `paused_reason` dokumentiert?
- `state=paused` → Grund in Job-Meta bekannt?
- `last_status=error` → direkt in Phase 2

**Pass 2 — Output-Dateien lesen** (entdeckt Silent-OK, false-positives):
```python
output_dir = os.path.expanduser('~/.hermes/cron/output')
for jid in os.listdir(output_dir):
    files = sorted(glob.glob(f'{output_dir}/{jid}/*.md'))
    if not files:
        continue
    latest = files[-1]
    with open(latest) as f:
        content = f.read()
    if any(kw in content.lower() for kw in ['error', 'no such file', 'skipped to prevent']):
        print(f'⚠ {jid} hat Fehlersignale im Output trotz Status OK')
    # Erweiterte Suche (v5): auch Emoji-Warnungen + deutsche Fehlertexte
    extended_kw = ['⚠️', '❌', '✗', 'Traceback', 'failed', "can't open",
                   'WARNING', 'WARN:', 'fehlgeschlagen', 'abgebrochen', 'nicht gefunden']
    if any(kw in content for kw in extended_kw) and not any(kw in content.lower() for kw in ['error', 'no such file']):
        print(f'⚠ {jid} hat Emoji/Text-Warnungen im Output — kein echter Error, aber prüfenswert')
```

**Validierung 2026-07-19 (21 Jobs auf Bastis Workstation):** Mit dem erweiterten Set wurden **7/21** Jobs mit `last_status=ok` entdeckt, die Warnungen enthielten. Nur 1 davon wäre mit den alten Keywords gefunden worden. Tipp: Bei `ok`-Jobs reicht es, die **letzten 3 Outputs** zu scannen.

**Pass 3 — Dead-Path-Check** (nur für Script-Jobs / no_agent):
- Script selbst `~/.hermes/scripts/<name>.sh` existiert? 
- Hardcoded paths im Script (grep 'SKILL_DIR', 'cd ', absolute paths) — existieren auf dem Filesystem?
- `cd` + relative paths — Zielverzeichnis noch da?

### Phase 2: Gap-Analyse — Anti-Patterns klassifizieren

Jeden Job gegen diese 4 Diagnose-Filter prüfen:

| # | Anti-Pattern | Symptom | Check | Fix |
|---|---|---|---|---|
| 1 | **Dead Hardcoded Path** (Script-Cron) | Script exits non-zero, schreibt ERROR ins Log. | `cat ~/.hermes/<script>.log` + `stat` auf referenzierten Pfad | Patch oder Directory anlegen |
| 2 | **Silent-OK** (Script-Cron) | `last_status=ok` + exit 0, aber alle Steps failen. | Output-Datei lesen (Pass 2) → Steps zeigen ⚠/✗ | Script-Refactor ODER Job pausieren + Grund dokumentieren |
| 3 | **Provider-Drift** (LLM-Cron) | `last_status=error`, `RuntimeError: #44585` im Gateway-Log | `cronjob action=list` → model/provider null | Pinning via `cronjob action=update job_id=X provider=P model=M` |
| 4 | **Manual-Only Slot** (Script-Cron) | `last_status=error` obwohl exit 0. Script sagt "manual-only" | Script lesen → `HERMES_ENDPOINT`-Guard? | Cron entfernen oder Script auto-runnable machen |

### Phase 3: DOW × Hour Lane-Overlap 2D-Matrix

Hilft den Schedule so zu legen, dass nicht 3+ Jobs gleichzeitig laufen.

```python
from collections import defaultdict

def expand_cron(expr):
    """Returns list of (dow, hour) tuples"""
    parts = expr.split()
    if len(parts) != 5: return []
    hour = parts[1]; dow = parts[4]
    hours = [int(hour)] if hour.isdigit() else list(range(24))
    if hour.startswith('*/'): hours = list(range(0, 24, int(hour[2:])))
    if ',' in hour: hours = [int(h) for h in hour.split(',')]
    dows = list(range(7)) if dow == '*' else [int(d)]
    return [(d, h) for d in dows for h in hours]

matrix = defaultdict(lambda: defaultdict(list))
for j in jobs:
    pairs = expand_cron(j.get('schedule',{}).get('expr',''))
    for d, h in pairs:
        matrix[d][h].append(j.get('name','?')[:30])

# Optional: Overlap-Risiko ausgeben
for d in range(7):
    for h in range(24):
        items = matrix[d].get(h, [])
        if len(items) >= 2:
            print(f"⚠ {['So','Mo','Di','Mi','Do','Fr','Sa'][d]} {h:02d}:00 → {len(items)} jobs: {items}")
```

**Interpretation:**
- `2+` = Overlap-Risiko. Sind die Jobs leichtgewichtig genug für Parallel-Lauf?
- Bei `3+` pro Slot: immer priorisieren.
- Strategien: Frequenz reduzieren, Schedule verschieben, Akzeptieren + dokumentieren

### Phase 4: Pinning-Quota berechnen (mit temporalem Vergleich)

LLM-getriebene Crons brauchen Pinning, sonst riskieren sie Provider-Drift (Category 3):
**Achtung:** Script-mode Jobs (`no_agent=true / script≠null`) haben keine Pinning-Sinn — sie laufen ohne LLM. Trotzdem können sie restliche `provider`/`model`-Felder aus alten Config-Snapshots haben. Diese Jobs **müssen** von der Pinning-Quote ausgeschlossen werden, sonst crasht die Quote.

```python
llm_jobs = [j for j in jobs if j.get('provider') or j.get('model')]
# Ausschluss: Script-mode Jobs (no_agent) haben keine Pinning-Relevanz
script_job_ids = {j['id'] for j in jobs if j.get('no_agent') or j.get('script')}
llm_jobs = [j for j in llm_jobs if j['id'] not in script_job_ids]
pinned = [j for j in llm_jobs 
          if j.get('provider_snapshot') and j.get('model_snapshot')]
print(f"Agent-jobs total: {len(llm_jobs)}")
print(f"Gepinnt: {len(pinned)} — Quote: {len(pinned)*100//max(1,len(llm_jobs))}%")
for j in llm_jobs:
    if not (j.get('provider_snapshot') and j.get('model_snapshot')):
        print(f"  ⚠ Ungepinnt: {j.get('id')} {j.get('name')}")
```

**Nachhaltige Pinning-Messung (temporaler Vergleich):** Die Pinning-Quote driftet vorhersagbar zwischen Audits. Tracke als KPI:

```python
# Temporal Pinning KPI — speichern nach jedem Audit
audit_kpi = {
    'audit_date': '2026-07-16',
    'total_llm_jobs': len(llm_jobs),
    'pinned': len(pinned),
    'pinning_quote': len(pinned) * 100 // max(1, len(llm_jobs)),
    'script_mode_config_garbage': len(detect_script_config_garbage(jobs)),
    'new_since_last_audit': len(new_jobs),
    'drift_event': 'Script-Mode-Config-Müll interferiert mit Quote' if config_garbage else None
}
```

**Drift-Muster (validiert):** Jeder neue LLM-Job ist standardmäßig unpinned → +1 Job, 0 Pins → Quote fällt. Nach jedem Audit die Quote zur Baseline legen. Bei >10% Drift zwischen Audits: Batch-Pinning aller neuen Jobs.

**Ziel: 100% Pinning** für LLM-Fleet (exklusive Script-Mode-Config-Müll).

## Ergebnis-Report-Format

Nach Fleet-Audit immer als strukturierten Report liefern:

```markdown
# 🐝 Cron-Fleet-Audit — <Datum>

## Kurzfazit
🟩 <N> gesund / 🟧 <N> silent-stale / 🟥 <N> broken
**Pinning-Quote:** <N>% (Voraudit: <N>%) — Drift: <±N>%

## Inventar (N Jobs)
| ID | Name | Schedule | Mode | Status | Last Run | Pin | Notiz |

## Gap-Analyse
### 🟥 <Anti-Pattern>: betroffene Jobs
### 🟧 <Anti-Pattern>: betroffene Jobs

## Priorisierte Maßnahmen
### M1 (🟥 sofort) — Job + Fix
### M2 (🟧 heute) — Job + Fix

## QA-Checkliste
- [ ] Baseline-Lesen: alle Jobs erfasst
- [ ] 4 Fehler-Klassen geprüft (Dead-Path, Silent-OK, Provider-Drift, Manual-Only)
- [ ] DOW × Hour 2D-Matrix gebaut
- [ ] Last-Outputs gelesen für ALLE Jobs
- [ ] Pinning-Quote reportet (mit temporalem Drift-KPI)
- [ ] Script-Mode-Config-Müll geprüft (Pattern I)
- [ ] Never-Run-3-Subklassen klassifiziert (Fresh/Missed/Stub)
- [ ] Lane-Congestion-Event geprüft (Pattern J)
- [ ] Hardcoded-Path-Existenz im Filesystem verifiziert
- [ ] Fix-Commands als kopierbarer Code formuliert
```

## Erweiterte Detection Patterns (v2, 2026-07-15)

Diese sieben Pattern wurden während eines reinen Crontab-basierten Cron-Audits (kein `cronjob`-Tool, kein Hermes-Cron-Scheduler) auf Basti's Workstation entdeckt und erweitern die 4-Anti-Pattern Gap-Analyse aus Phase 2.

### Pattern A: @reboot als Daemon-Ersatz

**Erkennung:** Ein Cron-Job mit `@reboot` startet einen HTTP-Server oder langlebigen Prozess (kein Script, das terminiert).

```python
def detect_reboot_daemon(cron_line):
    """@reboot + Python/Node-Server = Kandidat für systemd statt cron"""
    if not cron_line.startswith('@reboot'): return False
    server_keywords = ['server', 'listen', 'flask', 'fastapi', 'http', 'socket']
    return any(kw in cron_line.lower() for kw in server_keywords)
```

**Risiko:** Kein Restart-Policy bei Crash, kein Healthcheck, keine Dependency-Ordering (startet vor Docker/Netzwerk), Prozess-Orphan durch cron-Reaping möglich.

**Empfehlung:** systemd-User-Service mit `Restart=on-failure` + `Wants=docker.service` statt `@reboot`.

### Pattern B: Comment-Schedule-Drift (Doku vs Realität)

**Erkennung:** Kommentarzeilen in `crontab -l` claimen ein anderes Intervall als die Cron-Expression.

```python
def detect_schedule_drift(comment_lines, cron_lines):
    """Drift zwischen #-Kommentar und aktivem Schedule"""
    import re
    interval_keywords = {
        'stündlich': '1h', 'alle 1h': '1h', 'hourly': '1h',
        'halb-stündlich': '30m', 'alle 30 min': '30m', 'half-hour': '30m',
        'alle 2 min': '2m', 'alle 5 min': '5m', 'alle 15 min': '15m',
        'täglich': '1d', 'daily': '1d', 'jeden tag': '1d',
        'wöchentlich': '1w', 'weekly': '1w', 'jede woche': '1w',
        'monatlich': '1m', 'monthly': '1m'
    }
    def cron_to_approx_interval(expr):
        parts = expr.strip().split()
        if len(parts) != 5: return None
        if parts[0].startswith('*/'): return f"{parts[0][2:]}m"
        if parts[0] == '*' and parts[1] == '*': return '1m'
        if parts[1].startswith('*/'): return f"{parts[1][2:]}h"
        if all(p == '*' for p in parts[:4]) and parts[4] != '*': return '1w'
        if all(p == '*' for p in parts[:3]) and parts[4] == '*': return '1d'
        if parts[2] == '1': return '1m'
        return None
    findings = []
    for c_line, expr in zip(comment_lines, cron_lines):
        comment_lower = c_line.lower()
        for keyword, expected in interval_keywords.items():
            if keyword in comment_lower:
                approx = cron_to_approx_interval(expr)
                if approx and approx != expected:
                    findings.append((expr, comment_lower.strip(), approx, expected))
                break
    return findings
```

**Risiko:** Fehlerwartung — jemand ändert den Schedule aber nicht den Kommentar. Der nächste Admin vertraut dem Kommentar.

### Pattern C: Docker-Container-Abhängigkeit

**Erkennung:** Ein Cron-Job spricht HTTP auf Port 8080 (oder anderen Non-Standard-Ports) an, der typischerweise von einem Docker-Container bedient wird.

```python
def detect_container_dependency(cron_command, nextcloud_env=None):
    docker_hints = ['localhost:8080', 'localhost:4443', 'nextcloud', 'docker', 'webdav',
                    '/remote.php', '/ocs/']
    return any(h in cron_command.lower() for h in docker_hints)
```

**Kaskaden-Check:**
1. Docker-Status prüfen (`docker ps`)
2. Container-Health prüfen
3. Port-Mapping prüfen (`docker port <name>`)

Ohne diesen Check flaggt ein Audit fälschlich "Nextcloud-Service down", obwohl Docker läuft und der Container nur port-remapped ist.

### Pattern D: Log-Pfad-Langlebigkeits-Klassifikation

Jeder Cron-Job loggt irgendwohin. Die Haltbarkeit des Logs hängt vom Pfad ab:

| Pfad | Typ | Persistenz | Risiko |
|------|-----|-----------|--------|
| `/tmp/<name>.log` | Ephemeral | 🔴 Bis Reboot | Verlust nach Neustart |
| `~/logs/<name>.log` | User-Persistent | 🟢 Dauerhaft | Rotation fehlt meist |
| `~/.hermes/logs/<name>.log` | Hermes-Managed | 🟢 Dauerhaft | Im Hermes-Log-Dir |
| `~/<projekt>/logs/<name>.log` | Projekt-Lokal | 🟡 Mittel | Nur bei Projekt-Backup |
| `~/20-Workspace/logs/` | Workspace | 🟡 Mittel | workspace-spezifisch |

**Empfehlung:** Kritische Jobs (Config-Backup, Mnemosyne-Cleanup, Link-Validator) → `~/logs/`. High-Frequency-Jobs (alle <5 Min) → `/tmp/` oder mit Rotation nach `~/logs/`.

### Pattern E: Lock-Coverage-Gap bei High-Frequency-Jobs

**Problem:** Wenn ein Cron-Job alle 2 Minuten läuft (`*/2 * * * *`), beträgt die maximale Overlap-Wahrscheinlichkeit 100% — sobald ein Lauf länger als 2 Minuten braucht, startet der nächste parallel.

**Audit-Logik:**
```python
def detect_lock_gap(cron_expr, script_content, script_name):
    freq_minutes = approx_frequency_minutes(cron_expr)
    if freq_minutes and freq_minutes < 5:
        if 'flock' not in script_content and 'LOCK' not in script_content and 'lockfile' not in script_content:
            return f"Lock-Gap: {script_name} läuft alle {freq_minutes}m ohne Lock"
    return None
```

**Fix:** `flock -n <lockfile>` im Shell-Script oder `fcntl.flock(LOCK_EX|LOCK_NB)` im Python-Script.

### Pattern F: Duplizierte Subroutine

**Erkennung:** Ein Cron-Script ruft ein Kommando auf, das auch als separater Cron-Job existiert.

```python
def detect_subroutine_duplicate(script_content, all_cron_descriptions):
    calls = set()
    for line in script_content.splitlines():
        for cmd in all_cron_descriptions:
            bin_name = cmd.split('/')[-1] if '/' in cmd else cmd.split()[0]
            if bin_name and bin_name != os.path.basename(script_path) and bin_name in line:
                calls.add(bin_name)
    return calls
```

**Risiko:** Doppelte Arbeit, doppelte DB-Zugriffe, nicht offensichtliche Nebenwirkungen. Z.B. Weekly Digest ruft `mnemosyne_sleep` auf, aber es gibt einen separaten täglichen Mnemosyne-Sleep-Cron.

### Pattern G: Missing-Log-Klassifikation (Expected vs Unexpected)

```python
def classify_missing_log(job_schedule, job_last_run, log_path):
    freq_estimate = approx_frequency(job_schedule)
    if not os.path.exists(log_path):
        if freq_estimate and freq_estimate > 1 and not job_last_run:
            return 'EXPECTED_MISSING'
        elif freq_estimate and freq_estimate < 2:
            return 'UNEXPECTED_MISSING'
        else:
            return 'UNCLEAR'
    return 'PRESENT'
```

**Wichtig:** Wöchentliche und monatliche Jobs haben meistens kein Log auf Disk, wenn der letzte Scheduled Run noch in der Zukunft liegt. Das ist kein Fehler.

## Erweiterte Detection Patterns (v3, 2026-07-16)

Diese drei Pattern wurden während des 16.07. Fleet-Audits (21 Jobs, +9 seit 11.07.) auf Basti's Workstation validiert und erweitern die v2-Patterns.

### Pattern H: Temporale Pinning-Quote-Drift

**Erkennung:** Pinning-Quote sinkt **vorhersagbar** zwischen Audits. Neue Jobs werden unpinned angelegt. Die Drift-Funktion ist deterministisch: Jeder neue LLM-Job = +1 unpinnter Job.

```python
def detect_pinning_drift(current_jobs, previous_audit_data):
    \"\"\"Vergleicht Pinning-Quote mit vorherigem Audit und berechnet Drift.\"\"\"
    # Temporal Comparison — Key KPI
    llm_jobs = [j for j in current_jobs 
                if (j.get('prompt') or j.get('skills'))
                and not j.get('no_agent')]
    pinned = [j for j in llm_jobs
              if j.get('provider_snapshot') and j.get('model_snapshot')]
    current_quote = len(pinned) * 100 // max(1, len(llm_jobs))
    
    if previous_audit_data:
        prev_quote = previous_audit_data.get('pinning_quote', 100)
        drift = prev_quote - current_quote
        return {
            'current_quote': current_quote,
            'previous_quote': prev_quote,
            'drift_pct': drift,
            'new_unpinned': [j['name'] for j in llm_jobs if j not in pinned 
                            and j['created_at'] > previous_audit_data.get('audit_date')]
        }
    return {'current_quote': current_quote}
```

**Konkrete Drift-Kurve (validiert):**
| Audit-Datum | LLM-Jobs | Gepinnt | Quote | Delta |
|---|---|---|---|---|
| 2026-07-11 | 8 | 8 | 100% | — |
| 2026-07-16 | 10 | 8 | 80% | −20% |
| 2026-07-16 (nach M2) | 8 | 8 | 100% | 0% |

**Erkenntnis:** Nach M2 (entferne Script-Mode-Jobs aus LLM-Zähler) liegt die wahre Quote bei 100%. Die 80% waren ein Artefakt von Script-Mode-Config-Müll (Pattern I).

**Empfehlung:** Jedes Audit SOLLTE die temporale Drift-Kurve mitführen. Abweichung >10% zwischen Audits ist Prüf-Risiko.

## Erweiterte Detection Patterns (v4, 2026-07-17)

Dieses Pattern wurde waehrend des 17.07. Fleet-Audits (Self-Audit des multi-agent-master-workflow-8h-Crons) auf Bastis Workstation validiert.

### Pattern K: High-Cost Silent Agent (Token Waste)

**Erkennung:** Ein LLM-Agent-Cron-Job laeuft haeufig (stuendlich oder haeufiger), produziert zuverlaessig `last_status=ok`, aber sein Output besteht ueberwiegend aus Skill-Prompt-Echo. Der Job kostet pro Lauf token-technisch das volle Skill-Prompt, liefert aber kaum oder kein abweichendes Ergebnis.

```python
def detect_token_waste_jobs(jobs, output_dir='~/.hermes/cron/output'):
    \"\"\"Finde Agent-Jobs deren Output auf Token-Waste hindeutet.\"\"\"
    import os, glob
    output_dir = os.path.expanduser(output_dir)
    findings = []
    
    for j in jobs:
        is_agent = bool(j.get('prompt') or j.get('skills'))
        if not is_agent:
            continue
        
        # Frequenz schaetzen
        sched = j.get('schedule', {}).get('expr', '')
        parts = sched.split()
        if len(parts) != 5:
            continue
        # Stuendlich oder haeufiger?
        is_high_freq = parts[1] == '*' or parts[1].startswith('*/')
        if not is_high_freq and parts[1] == '0' and parts[0] == '*':
            is_high_freq = True
        
        # Output-Dateien checken
        jid = j.get('id', '')
        job_outputs = sorted(glob.glob(f'{output_dir}/{jid}/*.md'))
        if not job_outputs:
            continue
        
        latest = job_outputs[-1]
        with open(latest) as f:
            content = f.read()
        
        content_len = len(content)
        # Pruefe ob Output vom Skill-Prompt dominiert wird
        skill_echo_markers = [
            '[IMPORTANT:', 'The full skill content is loaded below.',
            '---\\nname:', 'description:', 'version:', 'metadata:',
            'Quick Links'
        ]
        echo_lines = sum(1 for line in content.splitlines() 
                        if any(m in line for m in skill_echo_markers))
        total_lines = len(content.splitlines())
        echo_ratio = echo_lines / max(1, total_lines) if total_lines > 0 else 0
        
        if echo_ratio > 0.3 and is_high_freq:
            findings.append({
                'id': jid[:12],
                'name': j['name'],
                'freq': sched,
                'total_runs': len(job_outputs),
                'latest_output_kb': round(content_len / 1024, 1),
                'echo_ratio': round(echo_ratio, 2),
                'effective_lines': total_lines - echo_lines,
            })
    
    return findings
```

**Beispielvalidierung (2026-07-17, Bastis Workstation):**

| Job | Frequenz | Runs | Output/Run | Echo-Anteil | Effektiv |
|-----|----------|------|------------|-------------|----------|
| greyhack-ci-watch | stuendlich | 166 | ~1.4KB | ~80% Skill-Prompt | ~280 Bytes Findings |

Das stuendliche ci-watch laeuft seit 2 Wochen (166 Runs), aggregiert ~232KB Token-Output -- ueberwiegend Skill-Reprompt ohne neuen Informationsgehalt. Der Job meldet `last_status=ok`, die Kosten sind unsichtbar weil kein Error-Signal entsteht.

**Risiko:**
- Token-Kosten akkumulieren unbemerkt (Pro Lauf: Skill-Prompt ~0.8-2KB x 24h x 30 Tage = 600-1500KB/Monat)
- Bei Bezahl-APIs: echte Kosten, kein Error-Tracking erfasst sie
- Bei Batch-APIs: belegter Context, keine Kapazitaet fuer echte Arbeit
- Nichts davon wird von Phase 2 (4 Anti-Patterns) oder v3-Patterns erfasst -- alle pruefen auf Fehler, nicht auf Leerlauf

**Fix-Optionen:**
1. **Frequency-Drossel:** Stuendlich -> 4-stuendlich oder nur bei Git-Aenderungen. Fuer Watch-Jobs reicht i.d.R. 4h oder 6h.
2. **No-Change Short-Circuit:** Vor dem Agent-Run pruefen ob sich seit letztem Lauf etwas geaendert hat (Git-Log, Datei-Timestamp, API-Response-Content-Hash). Falls nicht -> `echo "[SILENT]"` und sofort beenden -- spart Token + Output-Speicher.
3. **Skill-Struktur optimieren:** Wenn der Job extrem simpel ist (nur `git fetch` + `grep`), direkt als Script-Job (`no_agent=true`) statt als Agent-Job implementieren. Kein Skill-Prompt noetig.
4. **Akzeptieren + Dokumentieren:** Wenn der Job aus Compliance-Gruenden stuendlich laufen muss, im Audit als "bekannte Kostenquelle" listen.

**Spezialfall `[SILENT]`-Marker:** Ein Job der `[SILENT]` ausgibt (wie yuno-self-improve-PINNED) ist **kein Token-Waste** -- er erkennt selbst, dass er nichts zu tun hat, und bricht fruehzeitig ab. Das ist der gewuenschte Short-Circuit (Option 2 oben). Der Output ist kurz (<100 Bytes), der Token-Verbrauch minimal. Pattern K erkennt nur Jobs, die das volle Skill-Prompt durchlaufen ohne abzukuerzen.

**Abgrenzung zu Pattern B (Silent-OK):** Pattern B betrifft **Script-Jobs** die exit 0 melden aber deren Steps fehlschlagen. Pattern K betrifft **Agent-Jobs** die korrekt funktionieren (`last_status=ok`, Exit 0, Ergebnis 0 Findings) aber unverhaeltnismaessig viele Token pro Erkenntnis verbrauchen.


### Pattern I: Script-Mode-Config-Müll (Residual Provider Fields)

**Erkennung:** Ein Job mit `no_agent=true` und `script=` (Script-Mode) hat trotzdem `provider` und/oder `model` gesetzt. Diese Felder sind bedeutungslos — Script-Jobs laufen ohne LLM — aber sie inflatoneren den LLM-Job-Zähler und verfälschen die Pinning-Quote.

```python
def detect_script_config_garbage(jobs):
    \"\"\"Finde Script-Mode-Jobs mit residualen Provider/Model-Feldern.\"\"\"
    findings = []
    for j in jobs:
        is_script_mode = j.get('no_agent') or (j.get('script') and not j.get('prompt'))
        has_residual_llm_fields = j.get('provider') or j.get('model')
        if is_script_mode and has_residual_llm_fields:
            findings.append({
                'id': j['id'],
                'name': j['name'],
                'provider': j.get('provider'),
                'model': j.get('model'),
                'script': j.get('script')
            })
    return findings
```

**Ursache:** Ein Job wurde ursprünglich als LLM-Job angelegt, dann auf Script-Mode umgestellt (ohne die Provider/Model-Felder zu löschen). Hermes-Cron-Tool räumt diese Felder nicht automatisch auf.

**Fix:**
```python
# Entferne residuale Provider/Model-Felder von Script-Mode-Jobs
for j in detect_script_config_garbage(jobs):
    cronjob(action='update', job_id=j['id'],
            provider=None, provider_snapshot=None,
            model=None, model_snapshot=None)
```

**Effekt:** Pinning-Quote wird ehrlich — der LLM-Job-Zähler enthält nur echte LLM-Jobs und kein Rauschen.

**Validierung (echter Fund 2026-07-16):** `24h-audit` (8605cc06) hatte `no_agent=true, script=24h-audit.sh, provider=minimax, model=MiniMax-M3`. Nach Fix: `provider=null, model=null`. Quote stieg von 80% auf 100%.

### Pattern J: Lane-Congestion Event (Multiple Weekly Jobs in Same Slot)

**Erkennung:** Mehrere wöchentliche Jobs (Sonntags-Slot) fallen gleichzeitig aus, weil die Schedule-Dichte einen Stau erzeugt.

```python
def detect_lane_congestion_event(jobs, dow=0):  # dow=0 = Sonntag
    \"\"\"Finde Lane-Congestion-Events: mehrere Weekly Jobs im selben Slot ausgefallen.\"\"\"
    weekly_jobs = []
    for j in jobs:
        sched = j.get('schedule', {}).get('expr', '')
        parts = sched.split()
        if len(parts) == 5 and parts[4] == str(dow) and parts[0] != '*':
            weekly_jobs.append({
                'name': j['name'],
                'id': j['id'][:8],
                'schedule': j['schedule']['display'],
                'last_run_at': j.get('last_run_at', 'NEVER'),
                'last_status': j.get('last_status', 'none'),
            })
    
    # Erkennung: 2+ gleiche DOW, alle haben last_run >72h oder fehlenden Sonntag
    now = datetime.now(timezone.utc)
    most_recent_sunday = now - timedelta(days=(now.weekday() + 1) % 7)
    if now.weekday() == 6:  # heute ist Sonntag
        most_recent_sunday = now - timedelta(days=7)
    
    failed = [j for j in weekly_jobs 
              if not j.get('last_run_at') 
              or datetime.fromisoformat(j['last_run_at']) < most_recent_sunday - timedelta(days=1)]
    
    if len(failed) >= 2:
        return {
            'event': f'{len(failed)}/{len(weekly_jobs)} Weekly Jobs verpassten den Sonntag',
            'dow_name': ['So','Mo','Di','Mi','Do','Fr','Sa'][dow],
            'failed_jobs': [f['name'] for f in failed],
            'all_weekly': [f['name'] for f in weekly_jobs]
        }
    return None
```

**Risiko:** Wenn 3+ Weekly Jobs im selben Slot-Zeitraum (z.B. Sonntag 05:00–22:00) liegen, kann ein einzelner Lane-Conflict alle neutralisieren. Symptom: Keiner der Jobs hat einen `run_at` vom letzten Sonntag, aber alle zeigen `last_status=ok` vom vorletzten Run.

**Empfehlung:** Entzerrung über mehrere DOWs verteilen (z.B. `greyhack-knowledge-distiller` auf Samstag verschieben, `antigravity-news-watchdog` auf Montag). Für nicht-zeitkritische Jobs reicht "Akzeptieren + Dokumentieren".

**Validierung (echter Fund 2026-07-16):** `orch-weekly-pipeline` (So 05:00), `antigravity-news-watchdog` (So 10:00), `greyhack-knowledge-distiller` (So 22:00) — alle 3 verpassten den 12.07. Sonntag. Gesamt 3/3 Sonntags-Jobs ausgefallen.

## Erweiterte Detection Patterns (v5, 2026-07-19)

Drei neue Pattern aus dem 19.07. Sonntags-Fleet-Audit (21 Jobs, 1 Gateway-Shutdown, 1 Unpinned, 2 Premieren).

### Pattern L: Transient Gateway-Shutdown Collision (Category E — Category-Erweiterung)

**Erkennung:** Ein Job zeigt `last_status=error` mit:
```
Gateway shutdown (final-cleanup) killed the job's tool subprocess before the run finished.
```
Der Job hat **vorher und nachher** erfolgreiche Läufe.

```python
def is_gateway_shutdown(last_error):
    return 'Gateway shutdown' in (last_error or '')
```

**Validierung (2026-07-19):** `greyhack-ci-watch` (0de66e3162ec, stündlich) um 07:29.
Vorher 22 Runs completed. Kein Fix nötig — läuft beim nächsten Tick von allein grün.

**Abgrenzung:** Drift (Category C) = `#44585` / `spend-protection`. Gateway-Shutdown (Category E) = `final-cleanup killed`.

### Pattern M: Backup-Diff — flottenweite Drift erkennen

**Erkennung:** Vergleiche aktuelles `jobs.json` gegen `jobs.json.bak-YYYY-MM-DD`.

```python
import json, os
def backup_diff(current_jobs, backup_path):
    with open(backup_path) as f:
        backup = json.load(f)
    old = {j['id']: j['name'] for j in backup.get('jobs', [])}
    cur = {j['id']: j['name'] for j in current_jobs}
    new_ids = set(cur) - set(old)
    gone_ids = set(old) - set(cur)
    return {'new': {i: cur[i] for i in new_ids}, 'removed': {i: old[i] for i in gone_ids}}
```

**Validierung (gegen Backup 2026-07-11):** 7 neue Jobs (TikTok-Fleet), 1 entfernter (`orch-weekly-improve`). Keine Schedule-Drift bei bestehenden Jobs.

### Pattern N: Premiere-Klassifikation für Never-Run-Jobs (4 Subklassen)

**Erweiterung der Never-Run-Subklassen.** Neu: **Premiere** (next_run=heute, nie gelaufen, Script existiert).

| Subklasse | Severity | Bedingung | Reaktion |
|-----------|----------|-----------|----------|
| 🟢 Fresh Schedule | info | `created_at` < 2d vor `next_run_at`, beide Zukunft | Kein Alarm |
| ⚠️ Premiere | warn | `next_run_at` **heute**, nie gelaufen | Script checken (`os.path.exists`), Lauf beobachten |
| 🟧 Missed First Slot | warn | `created_at` > 24h, `next_run_at` vergangen | Cron-Scheduler prüfen |
| 🟥 Stale | error | `created_at` > 7d, nie gelaufen, kein Script | Job pausieren/entfernen |

**Validierung (2026-07-19):** `yuno-tiktok-weekly-review` (20:00 Premiere ✓ Script existiert).
`cron-monthly-audit` (01.08.) → Fresh Schedule ✓.

## Pitfalls

- **`last_status` lügt.** Immer Output-Dateien lesen. Der Weekly-Pipeline-Job markierte sich 3 Wochen `ok` obwohl kein Step funktionierte.
- **Script-Crons prüfen Pfade nicht.** Ein `cd "$SKILL_DIR"` + `python3 scripts/*.py` bricht lautlos, wenn das Verzeichnis weg ist — `exit 0` bleibt trotzdem.
- **Doppel-Pfade.** `python3 scripts/scripts/file.py` entsteht durch `cd $SKILL_DIR` + hardcodiertem `scripts/`-Prefix. Immer `pwd` verifizieren.
- **Pinning-Quote allein reicht nicht.** Ein Job kann `provider`/`model` gesetzt haben aber `provider_snapshot`/`model_snapshot` fehlen — das Tool verwendet sie bei Drift nicht.
- **Lane-Overlap ist asymptotisch.** Ein stündlicher Job (`0 * * * *`) erzeugt 168 Checks/Woche. Wenn 3+ Jobs in derselben Stunde liegen, sind Overlaps garantiert.
- **Fresh-Schedule Silent-Stale.** Ein Job mit `last_run_at=None, last_status=None` und `next_run_at` in der Zukunft ist kein "stale" — er wurde erst frisch angelegt und hat noch nicht feuern können. Im Report als "Fresh Schedule" markieren, nicht als echten Alarm. (Session: 2026-07-14, 24h-audit mit created_at 2026-07-14T00:00 und next_run_at 2026-07-14T08:00.)
- **h=08 Lane-Stau (bekanntes Muster).** Auf Basti's Workstation kollidieren täglich 08:00 drei Jobs: `yuno-morning-briefing` + `multi-agent-master-workflow-8h` + `24h-audit`. Das ist kein Bug, aber Telegram-Spam-Risiko beim Ausrollen neuer Audit-Jobs. Strategie: Audit-Jobs auf h=09 verschieben, oder Akzeptieren + Dokumentieren.
- **Der Audit selbst ist teuer.** 13 Jobs × Output lesen + Matrix + Pinning = ~15 Tool-Requests. In Cron-Session ohne User das Budget beachten.

## Erweiterte Detection Patterns (v6, 2026-07-22)

Diese Pattern wurden während des 22.07. Fleet-Audits (25 Jobs, Pinning-Quote-Regression 89%→46,2%, 1 neuer Silent-OK-Typ) auf Bastis Workstation validiert.

### Pattern O: CLI-Drift Silent-OK (Bare-Command statt hermes-CLI)

**Erkennung:** Script ruft ein Plugin-Command als Bare-Command auf (z.B. `mnemosyne-sleep`) statt via `hermes <plugin> <subcmd>` (z.B. `hermes mnemosyne sleep`). `|| echo "(unavailable)"` schluckt jeden `Befehl nicht gefunden`-Fehler. Exit 0, `last_status=ok`. Plugin läuft nicht, Job gilt als "gesund".

**Live-Diagnose (validiert 2026-07-22):**
```python
def detect_cli_drift(job_id, script_path):
    """Finde Bare-Plugin-Commands in Scripten, die der hermes-CLI gehören."""
    import subprocess
    with open(script_path) as f:
        content = f.read()
    candidates = ['mnemosyne', 'telegram', 'discord', 'matrix', 'slack']
    findings = []
    for plugin in candidates:
        pattern = rf'(?:^|[^A-Za-z/])({plugin}[-_][a-z]+)\s'
        matches = re.findall(pattern, content)
        for m in matches:
            try:
                subprocess.run(['hermes', plugin, '--help'],
                             capture_output=True, timeout=5)
                findings.append({
                    'job_id': job_id,
                    'bare_command': m,
                    'fix': f'hermes {plugin} <subcmd>',
                    'risk': 'CLI-Drift Silent-OK'
                })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
    return findings
```

**Erkennungs-Trigger im Output-File:**
```bash
# "unavailable" + "Befehl nicht gefunden" in gleicher Datei = CLI-Drift
grep -l "unavailable" ~/.hermes/cron/output/<job_id>/*.md | \
  xargs grep -l "Befehl nicht gefunden\|command not found"
```

**Echter Fund 2026-07-22:** `memory_weekly_consolidate.sh` (Job `54073f4024c8`) ruft:
- `mnemosyne-stats` → existiert nicht (echte CLI: `hermes mnemosyne stats --global`)
- `mnemosyne-sleep --all-sessions` → existiert nicht (echte CLI: `hermes mnemosyne sleep --all-sessions`)

Live verifiziert: `which mnemosyne-sleep` leer, `/home/bratan/.hermes/hermes-agent/venv/bin/hermes mnemosyne sleep --help` zeigt korrektes Interface. Job lief seit **2026-07-19** mit `last_status=ok` aber echter Mnemosyne-Consolidation = 0 Runs. Mnemosyne-Stats zeigen überwiegend "(unavailable)".

**Fix-Optionen:**
1. **Bare-Command durch hermes-CLI-Pfad ersetzen** (bevorzugt):
   ```bash
   # Alt:
   STATS=$(mnemosyne-stats 2>/dev/null | head -5 || echo "(unavailable)")
   # Neu:
   STATS=$(/home/bratan/.hermes/hermes-agent/venv/bin/hermes mnemosyne stats --global 2>/dev/null | head -5 || echo "(unavailable)")
   ```

2. **PATH-Setup am Script-Anfang**:
   ```bash
   export PATH="/home/bratan/.hermes/hermes-agent/venv/bin:$PATH"
   ```

3. **Subprocess aus venv-Python** (für Python-Scripts):
   ```python
   import subprocess
   subprocess.run(['/home/bratan/.hermes/hermes-agent/venv/bin/hermes',
                   'mnemosyne', 'sleep', '--all-sessions'])
   ```

**Abgrenzung zu Pattern B (Silent-OK):** Pattern B = CWD-Drift (`cd` zu totem Pfad, dann relative Pfade schlagen fehl). Pattern O = CLI-Drift (falscher Binary-Name, Plugin läuft nicht). Beide ergeben `last_status=ok` mit Fehlern im Output. Symptom-Unterscheidung: Pattern B zeigt `can't open file`/`cd: No such file`; Pattern O zeigt `Befehl nicht gefunden`/`(unavailable)`.

### Pattern P: DOW × Hour Live-Compute vs. Schätzung

**Erkennung:** Eine Schätzung der Hot-Slots (z.B. "30+ Slots mit 3+ Jobs") ohne tatsächliche Cron-Expansion überschätzt systematisch um Faktor 3-5x. DOW-Feld (`* * 0`, `1-5`, `0,8,16`) muss IMMER mit-expandiert werden.

**Anti-Pattern (eigener Audit 22.07.08:00):** Schätzung "30+ Hot-Slots" durch Hour-Only-View. Tatsächlich nach Live-Compute mit korrektem Cron-Expander: **7 Hot-Slots, alle mit identischer Konfiguration "täglich 08:00 = 3 Jobs"**.

**Korrekte Implementierung:** Regex-basierter Expander aus Phase 3 oben. Simple Split-Varianten (`hour.split('/')[1]`) crashen bei `*/2`.

**Validierungs-Discrepanz aus diesem Audit:**

| Methode | Hot-Slots (≥3) | Differenz |
|---------|----------------|-----------|
| Schätzung (Hour-View, DOW ignoriert) | 30+ | +23 |
| Live-Compute mit DOW × Hour 2D-Matrix | 7 | 0 |

**Lesson:** Jeder Schedule-Overlap-Bericht MUSS das Live-Compute-Snippet ausführen, sonst sind die Zahlen systematisch zu hoch. Bei Discrepanz Schätzung verwerfen, Live-Compute vertrauen.

**Quick-Verify-Check nach Phase 3:**
```python
# Sanity: alle Jobs müssen in der Matrix auftauchen
total_jobs_in_matrix = sum(len(items) for d in matrix.values() for items in d.values())
total_cron_jobs = sum(1 for j in jobs if j.get('schedule', {}).get('kind') == 'cron')
print(f"Jobs in Matrix: {total_jobs_in_matrix}, Cron-Jobs: {total_cron_jobs}")
# Wenn total_jobs_in_matrix != total_cron_jobs: Expander hat Felder verschluckt
```

### Pattern Q: Inventory-Growth + Pinning-Regression Tracking

**Erkennung:** Die Fleet wächst schneller als Pinning nachgezogen wird. Validierte Wachstumskurve 2026-07-10 bis 2026-07-22:

| Datum | Anzahl Jobs | Pinning-Quote echte LLM | Delta |
|-------|-------------|-------------------------|-------|
| 2026-07-10 | 13 | 100% (8/8) | — |
| 2026-07-15 | 18 | 88% (7/8) | −12% |
| 2026-07-17 | 21 | 89% (8/9) | +1% |
| 2026-07-22 | 25 | **46,2%** (6/13) | **−43%** |

**Root Cause:** `hermes cron create` setzt keinen `provider_snapshot`. Jeder neue LLM-Job ist standardmäßig unpinned. Bulk-Creation (z.B. 6 Kimi-Token-Cup one-shots am gleichen Tag) kippt die Quote sofort.

**Lesson v4:** Jeder Batch-Create mit ≥3 LLM-Jobs braucht einen Post-Step "Bulk-Pin auf aktuelle Defaults". Sonst Quote-Drift von −10 bis −40% pro Batch.

**Audit-Frage (in Phase 4 immer stellen):**
"Wie viele Jobs wurden seit letztem Audit erstellt? Wie viele davon sind LLM-Jobs? Sind sie gepinnt?"

```python
def detect_pinning_regression(current_jobs, last_audit_date):
    """Finde neue LLM-Jobs seit letztem Audit, prüfe Pinning-Status."""
    new_jobs = [j for j in current_jobs
                if j.get('created_at', '') > last_audit_date]
    new_llm = [j for j in new_jobs
               if not j.get('no_agent') and j.get('provider')]
    new_llm_pinned = [j for j in new_llm
                      if j.get('provider_snapshot') and j.get('model_snapshot')]
    if new_llm and len(new_llm_pinned) < len(new_llm):
        return {
            'new_llm_jobs': len(new_llm),
            'new_pinned': len(new_llm_pinned),
            'regression': f"{len(new_llm) - len(new_llm_pinned)} unpinned new LLM jobs",
            'action': 'Bulk-Pinning empfohlen'
        }
    return None
```

**Workflow nach Cron-Bulk-Create:**
```bash
# 1. Neue Job-IDs identifizieren
NEW_IDS=$(jq -r '.jobs[] | select(.created_at > "2026-07-22") | .id' ~/.hermes/cron/jobs.json)

# 2. Bulk-Pin-Loop
python3 << EOF
import sys
sys.path.insert(0, '/home/bratan/.hermes/hermes-agent')
from cron import jobs as jobs_mod
for jid in """$NEW_IDS""".split():
    jobs_mod.update_job(jid, {
        'provider_snapshot': 'minimax',
        'model_snapshot': 'MiniMax-M3',
    })
EOF

# 3. Diff-Verify (nur Pinning-Felder ändern)
cp ~/.hermes/cron/jobs.json /tmp/jobs.bak-$(date +%H%M%S)
diff /tmp/jobs.bak-* ~/.hermes/cron/jobs.json
# Erwartet: nur provider_snapshot + model_snapshot Änderungen
```