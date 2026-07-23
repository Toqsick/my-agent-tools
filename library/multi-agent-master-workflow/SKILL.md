---
name: multi-agent-master-workflow
description: >-
  Use when user asks for designing a master-controller and subagent workflow, parallelizing independent workstreams, coordinating cross-repository cleanup, or auditing a cron fleet with workers. NOT for a deterministic single-worker task or a request that only needs a written plan. Provides reusable phases, scope verification, briefing templates, ReAct reflection, conflict controls, and queen-side synthesis.
version: 1.7.0
author: Yuno for Basti
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - workflow
    - orchestration
    - multi-agent
    - queen-worker-gate
    - planning
    related_skills:
    - workflow-template
    - subagent-driven-development
    - critic-gate
    - delegation-anti-patterns
    - hermes-react-pattern
    - hermes-context-budget
    - hermes-agentic-patterns
    - sub-sub-workflow
    lane: koenigin
    reasoning_effort: high
trigger_keywords: ['and', 'multi-agent-master-workflow', 'designing', 'master-controller', 'subagent']
keywords: ['user', 'asks', 'designing', 'master', 'controller']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['workflow-template', 'hermes-react-pattern']
---


# Multi-Agent Master Workflow

Master-Controller/Subagent-Pattern für systematische Analyse- und Umsetzungsaufgaben.
Dies ist das **Orchestrierungs-Pattern**; domänenspezifische Ausprägungen liefert der
Skill `workflow-template` (5 fertige Templates + Decision-Tree).

## Rollen (Mapping auf Hermes)

| Generisch | Hermes-Rolle | Aufgabe |
|---|---|---|
| Subagent A–E (3–6, parallel) | Worker | Je ein abgegrenzter Scope; Output: Kurzbefund, Lücken/Probleme, Verbesserungsvorschläge, Priorität, markierte Annahmen |
| Master-Controller | Queen | merge_results, deduplicate, resolve_conflicts, unify_priorities, decompose_into_tasks, define_execution_order |
| QA-/Abnahmeprüfung | Gate | Vollständigkeit, Konsistenz, Nachvollziehbarkeit, Risiken benannt — **verpflichtend** bei Security, Produktionscode, öffentlicher Doku |

## Phasen

0. **Vor-Inventur (Baseline Build)** — Vor jedem Dispatch: CI-Build laufen lassen (`bash scripts/ci-build.sh 2>&1 | grep FAIL`). Die Baseline-Fail-Liste dokumentieren. Später gegen Endzustand vergleichen — Coverage-Gap Detection. Ohne Phase 0 sind pre-existing Fails unsichtbar im Pattern-Rauschen.

1. **Inventarisierung** — Elemente erfassen, Kategorien zuordnen
2. **Analyse** — je Element: behalten | überarbeiten | neu | teilen | zusammenführen | entfernen
3. **Priorisierung** — kritisch | hoch | mittel | niedrig (🟥🟧🟨🟩)
4. **Umsetzung** — je Maßnahme: Titel, Kategorie, Begründung, Dringlichkeit, Aufwand (S/M/L), Abhängigkeiten
5. **QA/Gate** — Gate-Prüfung vor Freigabe

## Constraints

- Keine unbelegten Annahmen; jede Empfehlung beruht auf einem konkreten Befund
- Bei Unsicherheit markieren statt raten
- Kleine, reviewbare Schritte — keine Monolithen
- Gib nur das Ergebnis aus (kein Preamble)

### ReAct + Reflexion (eingebettet)

Nutze **explizites ReAct** im Queen-Loop: jeden Worker-Schritt als `Thought → Action → Observation` etikettieren. Nach jedem Subagent-Batch oder grösseren Schritt **Reflexion-Slot** einlegen (Self-Check gegen Ziel, Vollständigkeit, Belege).

📘 Siehe: `hermes-react-pattern` (Labels + Template-Snippet)
📘 Siehe: `hermes-context-budget` (85%-Compaction-Trigger bei >10 Worker-Calls)

## Domain-Spezifisch: Cross-Repo GitHub Cleanup

Bewährtes Dispatch-Pattern aus der M3 Bienen-Schwarm-Session (2026-07-07) für
"Geh alle offenen GitHub-Issues/PRs an" über 3+ Repos.

### Dispatch-Strategie

```
Welle 1 (3 Subagenten, parallel — unabhängige Repos):
  Biene A: Repo-1 — alle PRs + Issues
  Biene B: Repo-2 — das gleiche
  Biene C: Repo-3 — das gleiche

Welle 2 (nach Welle-1-Ergebnissen, 1–3 Subagenten):
  Biene D: merge_results + deduplicate + resolve_conflicts
  Biene E: feature-assessment (Security, Planning, Roadmap)
  Biene F: cross-repo issues (Tracking-Items, DMZ-Referenzen)
```

### Dispatch-Scope Verification (vor Aufruf von delegate_task)

**File-Affinity Check (Anti-Pattern #10):** Jede Datei darf max. EINEM Subagenten zugeordnet sein. Überlappungen = Königin macht es selbst (Parent-Direct, sequenziell).

```python
from collections import defaultdict
file_to_agents = defaultdict(list)
for agent, files in assignments.items():
    for f in files:
        file_to_agents[f].append(agent)
overlap = {f: a for f, a in file_to_agents.items() if len(a) > 1}
# → remove overlaps from all subagent lists, queen does them
```

**Baseline-Build Pre-Check (Anti-Pattern #9):** `bash scripts/ci-build.sh 2>&1 | grep FAIL` vor Dispatch — sonst sind pre-existing Fails unsichtbar.

**Report-Template Pre-Create (Anti-Pattern #11):** `write_file("/tmp/report-<agent>.md", "# <Agent>\n## Files\nNone yet\n## Build\nNone yet")` **VOR** erstem Tool-Burst — sonst fehlt bei Truncation der Report.

**Pre-Push Check (Anti-Pattern #12):** `gh pr view <N> --json mergeable` + `git fetch origin main` VOR Force-Push. `--force-with-lease` statt `--force`.

### Subagent-Briefing-Template

```
Goal: Schließe alte/irrelevante PRs + Issues in {repo}.

Prioritätsordnung:
1. Dependabot-PRs → sofort close (keine Zeit mit Bodies verschwenden)
2. Offene PRs → reviewen: diff + name-only + stat checken
3. Issues zu geschlossenen PRs → close oder redirect
4. Restliche Issues → labeln + priorisieren

PR-CI-Artifact-Detection: `gh pr diff N --name-only | grep -cE
'(coverage/|\.html|\.js\.map|\.nyc_output/)'`
Wenn NUR CI-Artifakte: close als not_planned + .gitignore fixen.

Output: Liste geschlossener Items mit Begründung
```

### Pitfalls

| Fehler | Fix |
|--------|-----|
| Dependabot-Bodies lesen | Direkt schließen — verschwendet Token |
| PR-Lines als echter Code | `--name-only` checken. 6.885 Zeilen können alles coverage/ sein |
| .gitignore vergessen | JEDER CI-Artifact-PR-Close braucht .gitignore-Fix |
| Alle 6 Bienen gleichzeitig | 3 repo-spezifisch (parallel), dann in Welle 2 kreuzend dispatchen |
| Issue ohne Redirect schließen | In Kommentar: "Verschoben nach → {ziel}" |

## Domain-Spezifisch: Cron-Fleet Audit

Bewährtes Pattern für "Systematischer Audit der eigenen Hermes-Cron-Fleet"
(Phase-1-Inventur ohne Subagent-Dispatches — Queen liest `~/.hermes/cron/jobs.json` direkt).
Validiert 2026-07-10 mit 13 Jobs (10 ok, 2 error, 1 ungetestet). Re-validiert
2026-07-11 mit 13 Jobs (10 ok, 1 paused mit Reason, 1 Silent-OK entdeckt, 8/8 gepinnt).

### Selbststart-Verhalten (Cron mit leerem Prompt)

**Wichtig:** Der Cron-Job `multi-agent-master-workflow-8h` (Schedule `0 0,8,16 * * *`)
hat einen **leeren Prompt**. Das bedeutet: die Skill-Definition IST der Prompt.
Wenn dieser Cron feuert, ist die **Standard-Aktion = Cron-Fleet-Audit** — 
nicht das Skill-Content-Echo.

**Anti-Pattern vermeiden:** Der Skill-Text darf NICHT die Antwort sein. 
Immer:
1. `jobs.json` lesen (Live-Daten)
2. Inventur + Gap-Analyse + Maßnahmen produzieren
3. Resultat als Cron-Output liefern (oder `[SILENT]` wenn nichts zu melden)

**Ausnahme:** `[SILENT]` ist erlaubt, wenn **alle** Bedingungen erfüllt sind:
- Pinning-Quote = 100% (keine neuen unpinnten Jobs)
- Keine Silent-OK-Anomalien (alle `last_status=ok` haben auch grüne Outputs)
- Pinning-Quote-Delta = 0 (keine Veränderung zum letzten Audit)
- Keine Never-Run-Jobs (die `last_run_at` haben sollten, aber nicht bekamen)
- Keine neuen Jobs seit letztem Audit

Wenn eines zutrifft → Report produzieren, nicht `[SILENT]`.

### Ablauf (5 Schritte)

1. **Baseline lesen** — `python3 -c "import json; print(json.dumps(json.load(open('/home/bratan/.hermes/cron/jobs.json'))['jobs'], indent=2))"` (oder `hermes cron list`).
   Erfasse pro Job: `id`, `name`, `enabled`, `schedule`, `last_status`, `last_error`,
   `repeat.completed`, `next_run_at`, `deliver`, `model`, `provider`,
   `provider_snapshot`, `model_snapshot` (gepinnt?).
2. **6+ Fehler-Klassen klassifizieren** (siehe Anti-Patterns Tabelle unten):
   - **Drift-Guard-Block** (unpinned Job + Provider/Model-Drift → `RuntimeError: Skipped to prevent unintended spend`)
   - **Dead Hardcoded Path** (script-mode Job mit Pfad auf gelöschtes Skill/Script)
   - **Silent-Stale** (Job existiert, ist enabled, hat aber `last_run_at=None` / `repeat.completed=0`)
   - **Pinning-Latenz** (präventiv — 0 von N LLM-Jobs gepinnt, noch kein Drift, aber Latenz-Risiko)
3. **Schedule-Density-Map bauen** — **DOW × Hour 2D-Matrix** der Job-Cron-Expressions
   (Regex-basiert expandieren für `*`, `*/n`, `a-b`, `a-b/n`, Comma-Listen). Deckt
   Overlaps auf (z.B. So 04:00/08:00/22:00 mit je 3 Jobs parallel — Hour-Only-View
   würde das verschlucken).
4. **Report-Format** (Queen-direkt, keine Subagents):
   - Kurzfazit mit Ampel-Legende (🟥🟧🟨🟩)
   - Inventar-Tabelle (alle 13 Jobs, eine Zeile pro Job)
   - Gap-Analyse mit Klassen-Buckets (Drift-Guard / Dead-Path / Silent-Stale)
   - Priorisierte Maßnahmen (M1–Mn) mit **copy-paste-fertigen Fix-Commands**
   - QA-Checkliste + offene Punkte
5. **Fix-Commands immer mitliefern** — Bei Drift-Guard immer die exakte CLI-Zeile angeben.
   ACHTUNG: `hermes cron update` existiert NICHT (Stand 2026-07-10). Die einzige
   funktionierende Pinning-Methode (validiert 2026-07-11) ist **programmatisch via Python**:

   ```python
   import sys
   sys.path.insert(0, '/home/bratan/.hermes/hermes-agent')
   from cron import jobs as jobs_mod

   # Pinning (provider_snapshot + model_snapshot auf aktuelle Werte setzen)
   jobs_mod.update_job('<job_id>', {
       'provider_snapshot': '<current_provider>',
       'model_snapshot': '<current_model>',
   })

   # Pause mit dokumentiertem Grund (CLI `hermes cron pause` setzt KEINEN Grund!)
   jobs_mod.update_job('<job_id>', {
       'enabled': False,
       'state': 'paused',
       'paused_reason': '<Warum + was zur Wiederbelebung nötig ist>',
   })

   # Never-Run triggern (nur scheduling, kein echter run → muss `hermes cron tick` folgen)
   jobs_mod.trigger_job('<job_id>')
   ```

   `hermes cron edit` setzt KEINEN `provider_snapshot`/`model_snapshot` (nur prompt/schedule/skills).
   CLI-Lücken-Befund (Stand 2026-07-11): kein `hermes cron pin`, kein Reason-Param bei `pause`.

### Anti-Patterns (Cron-Fleet-Audit)

| Fehler | Symptom | Fix |
|---|---|---|
| **Drift-Guard übersehen** | `last_error: RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'zai' -> 'minimax'; model 'glm-5' -> 'minimax-m3')` | Job ist **nicht kaputt** — Hermes' Pinning-Guard schützt vor ungewollter Spend. Fix via `cron.jobs.update_job(job_id, {'provider_snapshot': neu, 'model_snapshot': neu})` (validiert 2026-07-11) — **beide Felder in derselben Action** (Pinning ist binär, nicht additiv). **Immer alle 3 Optionen mitliefern** (neu pinnen / alt pinnen / pausieren). CLI-Lücke: `hermes cron edit`/`pause` bietet keine Pinning- oder Reason-Parameter. |
| **Dead Hardcoded Path ignorieren** | `last_error: ERROR: Runs directory missing: /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs` | Erst Pfad verifizieren: `os.path.isdir(<pfad>)`. Wenn tot → Skill wurde umbenannt/gelöscht. Fix: Script umschreiben ODER `hermes cron remove <id>`. |
| **last_run_at=None übersehen** | Job ist seit Tagen "scheduled" aber `repeat.completed=0` und kein Fehler | Silent-Stale: Script-Pfad prüfen, ggf. dry-run VOR nächstem geplanten Lauf. Telegram-Deliver-Jobs vorher testen — Spam-Risiko! **Fix-Pattern (validiert 2026-07-11):** `bash <script>` als Dry-Run → dann `cron.jobs.trigger_job(<id>)` für Scheduling + `hermes cron tick` für echten Run (setzt `last_run_at` und `last_status`). `trigger_job` alleine schedulet nur, ohne Run. |
| **Silent-OK übersehen** *(neu 2026-07-11)* | Script exit code 0, `last_status="ok"`, aber Output enthält ⚠ Warnings + Step-Failures (z.B. `python3: can't open 'scripts/scripts/heuristic_extractor.py'` — Doppel-Pfad nach Skill-Umzug). Pipeline markiert sich selbst grün, Heuristik-Schritte laufen ins Leere. | **Immer letzten Run-Output lesen** (`ls ~/.hermes/cron/output/<job_id>/ | tail -1` + `cat`), nicht nur `last_status` trauen. Bei ⚠-Zeilen trotz ok-Status: das ist ein Anti-Pattern. Fix = relativen CWD-Pfad im Script prüfen (oft `cd scripts/` der nach Skill-Umzug nicht mehr stimmt). |
| **Schedule-Overlap nicht erkennen** | 22:00 Uhr hat 3 Jobs (yuno-self-improve-PINNED, greyhack-knowledge-distiller, evtl. weitere) — Lane-Throttling möglich | Hour-of-Day-Map ausgeben. Wenn 3+ Jobs auf identischer Stunde → Lane-Konflikt-Risiko dokumentieren. |
| **Disabled Jobs vergessen** | 0 von 13 — aber wenn doch welche da: alle in Inventar-Tabelle aufnehmen mit `paused_reason` | Vermeidet "warum läuft X nicht?"-Rätsel. |
| **Pinning-Latenz übersehen** (Class E) | Kein akuter Crash, aber `provider_snapshot=null` für echte LLM-Jobs. Sobald globaler Default wechselt → alle unpinned LLM-Jobs gleichzeitig gedriftet → N Crash-Reports auf einmal. **Achtung:** `no_agent=true`-Jobs mit Provider-Feld sind **Provider-Relikte** (kein Drift-Risiko, dämpfen Quote künstlich) — aus der Berechnung ausschließen. | Immer die **echte Pinning-Quote** reporten: `sum(provider_snapshot IS NOT NULL) / sum(provider IS NOT NULL AND no_agent = false)`. Provider-Relikte (`no_agent=true + provider`) separat ausweisen. Quote < 100% → identifizieren welche LLM-Jobs wirklich unpinned sind (nicht welche nur ein Relikt haben). **Sonderfall:** der Audit-Cron selbst (z.B. `multi-agent-master-workflow-8h`) MUSS als erstes gepinnt werden — Self-Audit-Blind-Spot. |

### Pitfalls (Cron-Fleet-Audit-spezifisch)

- ❌ **Provider-Lane als technische Entscheidung framen** — Drift-Guard-Fix ist eine **Spend-Entscheidung** (`zai/glm-5` = free vs. `minimax/minimax-m3` = bezahlt). Im Report immer beide Optionen transparent auflisten.
- ❌ **Drift-Guard als Bug melden** — Es ist by design (Anti-Spend). Immer als Feature kennzeichnen.
- ❌ **last_error-String abschneiden** — Bei Drift-Guard-Fehlern steht die **exakte CLI-Fix-Zeile im Klartext** im `last_error`-Feld. Immer komplett zitieren.
- ❌ **Hardcoded Paths reparieren ohne Ursachenforschung** — Erst fragen: wurde das Skill umbenannt oder gelöscht? Vorher prüfen mit `find` oder `ls` auf den Parent-Dir. Sonst fixt man den falschen Pfad.
- ✅ **Bei `repeat.completed=0` aber `last_run_at != None`** — Job hat schonmal gelaufen, current_status ist `None`. Eigene Bucket-Klasse: **Never-Run-Since-Reset** (z.B. nach Schema-Migration).
- ✅ **Pinning-Quote präventiv reporten** — Wenn 0 von N LLM-Jobs gepinnt sind und heute kein Crash → trotzdem 🟧 markieren. Der nächste globale Lane-Switch killt dann **alle auf einmal**, nicht einzeln. Audit-Cron selbst ist die kritischste Pinnung (Self-Audit-Blind-Spot).
- ✅ **DOW × Hour 2D-Matrix statt Hour-Only** — `0 4 * * 0` (Sonntag 04:00) wird vom Hour-View verschluckt; alle Sonntags-Stau-Slots (typisch So 04:00/08:00/22:00) müssen sichtbar sein, sonst Lane-Throttling unentdeckt.
- ✅ **Pause immer mit `paused_reason` dokumentieren** — `hermes cron pause` setzt keinen Grund, daher immer direkt danach `cron.jobs.update_job(job_id, {'paused_reason': '...'})`. Sonst hat man in 3 Monaten Geisterjobs ohne Kontext. Grund-Format: "Was kaputt ist + was zur Wiederbelebung nötig wäre".
- ✅ **Diff-Verify nach Bulk-Pinning** — Vor/Nach-Backup von `jobs.json` machen (`cp jobs.json /tmp/jobs.bak-$(date +%H%M%S)`), dann `diff` ausführen. Sicherstellen dass nur die beabsichtigten Felder (`provider_snapshot`/`model_snapshot`/`paused_*`/`last_run_at`) sich ändern, NICHT `schedule`/`prompt`/`skills`.

📘 Vollständiges Playbook + Copy-Paste-Recipe: `references/cron-fleet-audit.md` |

## Domain-Spezifisch: Parallel Implementation Swarm (Bienen-Muster)

Gegenstück zu den Analyse/Audit- und Cleanup-Patterns. Einsatz bei
**Implementierungsaufgaben** (Skripte, Services, Cron-Jobs), die parallel
und unabhängig voneinander entstehen können. Die Queen steht nicht idle —
sie arbeitet an eigener Tech-Infrastruktur (Docker, Doku, Credentials, Cron).
Die Reference `references/parallel-implementation-swarm.md` enthält das volle
Briefing-Template, Phase-0-Readiness-Check, Anti-Patterns und Herkunft.

| Phase | Queen macht | Bienen machen |
|---|---|---|
| 0 — Readiness | Prüft API-Shapes, Imports, Disk, Ports gegen **Live-System** | — |
| 1 — Dispatch | Schreibt kompaktes Briefing pro Biene (60-70% Draft-Länge) | Führen jeweils vollständiges Skript in eigenem Scope aus |
| 2 — Independent Work | Docker aufsetzen, Cron-Installer, Doku, Credentials | Fliegen autonom (15-45 min) |
| 3 — Integration | Ergebnisse prüfen, Cron deployen, Memorys setzen | Gelandet |

### Dispatch-Regeln (Quick-Check)

- **Readiness vor Dispatch:** Queen prüft API-Shapes gegen Live-System, fixt offensichtliche Bugs selbst (1 min)
- **Kompaktes Briefing:** ~60-70% der Draft-Länge, kein "as you know"-Kontext
- **E2E-Test-Pflicht:** In Goal-Text als harte Anforderung ("muss E2E Exit 0 liefern")
- **Kein File-Overlap:** Jede Biene bekommt eigenen Scope, keine gemeinsamen Dateien
- **Queen idle verboten:** Plan für Queen-Arbeit bereithalten (Docker, Docs, Cron, Installer)
- **Bienen-Output prüfbar:** Biene muss verifizierbaren Output liefern (Exit-Code, File-Content, Port-Response)

### Subagent Self-Test Protocol (gelernt 2026-07-13)

**Problem:** Biene 2 im Daily-Humanizer-Schwarm behauptete "All criteria met", aber die Datei hatte noch 17 mid-sentence Boldface + 5 Inline-Header-Listen. Der Self-Report war ein Wunschtraum, kein Faktenbericht. Das geläufige "Queen verifies after" deckt das erst spät — teurer Override-Loop.

**Das Protokoll für Content-Modification-Briefings:**

1. **Embed self-test commands in the briefing itself.** Gib dem Subagent die exakten grep/shell/Kommandoaufrufe, die nach dem Edit laufen müssen, bevor er seinen Report schreibt:

   ```
   FÜHRE SELBST-TESTS durch BEVOR du deinen Self-Report abgibst:
      grep -c '—' auf der Datei → muss ≤1 sein
      grep -oE '\*\*[^*]+\*\*' | grep -v '^#' | wc -l → muss 0 sein
      grep -c '^- \*\*[A-Z]' → muss 0 sein

   Erst wenn ALLE Tests grün sind, den Self-Report abgeben.
   Wenn ein Test rot ist, fixen und neu testen.
   ```

2. **Definiere die Test-Kriterien im Briefing als MUSS-Passage** ("Erst wenn alle drei Tests grün sind, den Self-Report abgeben"). Das verhindert, dass der Subagent das Self-Testing als optional betrachtet.

3. **Lass den Subagent die Testergebnisse in den Self-Report einbetten:**
   ```
   Self-Report MUSS enthalten:
   - Finale Dateigröße in Bytes
   - Em-Dash Count (nach Selbst-Test)
   - Mid-Boldface Count (nach Selbst-Test)
   - Bestätigung dass alle drei Tests grün sind
   ```

4. **Queen trotzdem nicht blind vertrauen** — die Self-Tests sind kein Ersatz für Königin-Verifikation, sondern ein Pre-Filter. Subagenten, die beim Self-Testing schummeln (Behauptung "grün" ohne tests tatsächlich zu laufen), sind ein Signal für tiefere Briefing-Qualitätsprobleme (Pitfall #5 bleibt aktiv).

**Wann das Protokoll anwenden:**
- IMMER bei Content-Modification (humanisieren, formatieren, übersetzen)
- IMMER bei lint-/style-Regeln mit maschinenprüfbaren Kriterien (Boldface-Count, Em-Dash-Count, Line-Length)
- Optional bei Code-Refactoring (Build-Test als Self-Test)
- NICHT nötig bei reinen Read/Analyse/Recherche-Tasks

### Anti-Patterns

| Fehler | Fix |
|---|---|
| Drafts ungeprüft delegieren | Queen prüft Imports/API vor Dispatch |
| Biene bekommt Draft zum Lesen | Kompaktes Briefing schreiben, Draft-Inhalte abstrahieren |
| Queen wartet idle | Plan für Queen-Arbeit bereithalten |
| "alle Bienen gleich" | Jede Biene hat eigene Pitfalls |
| E2E-Test nicht verpflichtend | In Goal-Text als harte Anforderung |
| Bienen-Summary blind glauben | Biene muss verifizierbaren Output liefern |

### Verwandte Skills

- `references/parallel-implementation-swarm.md` — Vollständiges Pattern mit Briefing-Template
- `references/structured-parallel-dispatch.md` — Strukturierte Parallel-Dispatch-Variante
- `references/cron-fleet-audit.md` — Cron-Fleet-Audit-Spezialpattern (Inventur + Drift-Guard + Dead-Path-Detection), validiert 2026-07-10
- `subagent-driven-development/references/parallel-summary-staleness.md` — Staleness-Risiko (mitigiert durch E2E-Test-Commitment)
- `multi-agent-pitfalls-cheatsheet` — Vor jedem Dispatch laden
- `delegation-anti-patterns` — File-Affinity, Baseline-Build

## Domain-Spezifisch: Vault-Content-Generation Swarm (Content-Bienen)

Bewährtes Dispatch-Pattern aus der GreyHack-Vault-Vervollständigung (2026-07-14)
für **parallele Content-Produktion in Obsidian/Knowledge-Vaults** durch recherchierende
und schreibende Subagenten. Getestet mit 4 parallelen Bienen non-overlap Scope.

### Grundlegender Unterschied zum Implementation Swarm

| | Implementation Swarm | Content Swarm |
|---|---|---|
| Bienen-Tätigkeit | Code schreiben + E2E-Test | Web-Recherche + Vault-Lesen + Schreiben |
| Queen-Arbeit während Flug | Docker, Cron, Credentials | MOC-Anker updaten, Memory-Writes |
| Quality-Gate | Exit-Code, Port-Response | Em-Dash ≤1, Boldface=0, Wiki-Links ≥5 |
| Output | Ausführbare Skripte/Services | Markdown-Notes mit Frontmatter |

### Dispatch-Regeln (Quick-Check)

- **File-Affinity:** Jede Biene bekommt EXAKT EINEN neuen Dateipfad — existierende Notes werden nie überschrieben
- **Schritt 1 Web + Schritt 2 Lokal** — jede Content-Biene macht beides (web_search/web_extract + lokale Vault-Notes lesen)
- **Self-Tests im Briefing embedden** — die exakten grep-Befehle für das Quality-Gate (siehe Subagent Self-Test Protocol oben)
- **Drift-Biene bekommt Read-Only-DB-Zugriff** — JSON-Dumps nach `/tmp/`, nie ins Vault-Verzeichnis
- **Queen updated MOC-Anker parallel** — Wiki-Links in `04 Bereiche/` oder `09 System-Doku/` vorbereiten
- **Memory-Triple-Write Mid-Run** — Zwischenstatus + Final-Status in Mnemosyne sichern

### Quality-Gate Kriterien (hart)

| Kriterium | Grenzwert | Prüfbefehl |
|---|---|---|
| Em-Dashes | ≤ 1 | `grep -c '—'` |
| Mid-sentence Boldface | 0 | `grep -oE '\*\*[^*]+\*\*' \| wc -l` |
| Inline-Header (Listen) | 0 | `grep -c '^- \*\*[A-Z]'` |
| Wiki-Links ([[...]]) | ≥ 5 | `grep -c '\[\[.*\]\]'` |

### Reference

Volle Briefing-Vorlage + Phase-0-Baseline + Pitfalls + Vault-Layout-Beispiel:
`references/vault-content-generation-swarm.md`

### Anti-Patterns

| Fehler | Fix |
|---|---|
| Biene überschreibt existierende Note | Jede Biene bekommt NEUEN Dateinamen mit Datumssuffix |
| Biene verwendet Spielstand-Pfad für Dump | `/tmp/` für Zwischen-Dumps, nie ins Vault |
| Biene schreibt Klartext-Passwörter in Report | `[REDACTED]` oder Typ-Muster nutzen |
| Biene behauptet grün ohne Tests zu laufen | Self-Test-Kommandos MÜSSEN im Briefing embeddet sein |
| Wiki-Links zu nicht-existierenden Notes | Nur zu existierenden Vault-Notes verlinken |
| Audit-Biene schreibt in DB | Read-Only-Connection erzwingen |

## Domain-Spezifisch: Sub-Sub Vault-Patch Swarm (Cross-Model)

Bewährtes Dispatch-Pattern aus der Cross-Model Vault-Patch-Session
(2026-07-14) für **parallele Vault-Modifikation mit Sub-Sub-
Verifikation**. Getestet mit Queen=GLM 5.2 + Bees=M3 (pinned).

### Wann anwenden

Wenn Vault-Dateien **gleichzeitig gepatcht und verifiziert** werden
sollen: MOC-Updates, stale-count-fixes, Cross-Link-Vernetzung.
Jede Parent-Biene patcht, ihre Sub-Biene verifiziert unabhängig.

### Dispatch-Pattern (3 Parent + 3 Sub-Sub)

```
Welle 1 (3 Parent-Bienen, role='orchestrator', parallel):
  Alpha: MOC-Patch (Links, Frontmatter, Wartungs-Log)
         → Sub: Wiki-Link-Target-Verifikation
  Beta:  Stale-Count-Repair (deep-systems Datei)
         → Sub: Cross-Check in deep-intel Datei
  Gamma: Cross-Link-Matrix (7 Notes × 7 Notes)
         → Sub: Fehlende Links patchen + JSON-Log
```

### Lohnt-sich-Bewertung (aus 3 Sub-Subs)

| Sub-Task | Typ | Lohnt? | Grund |
|---|---|---|---|
| Wiki-Link-Verifikation | Reasoning | ja | fand 1 toten Pre-Existing Link |
| Cross-File-Drift-Check | Reasoning | ja | fand 10 weitere stale Werte |
| Cross-Link-Patching | Volume+Reasoning | ja | 38 Patches mit Backup+Verify |

### Cross-Model-Konfiguration

```yaml
#~/.hermes/config.yaml — Pinning vor Queen-Wechsel setzen
delegation:
  provider: minimax        # bleibt M3 auch bei GLM/Claude Queen
  model: MiniMax-M3
```

Validiert: GLM 5.2 Queen dispatcht M3-Bienen, M3-Bienen dispatchen
M3-Sub-Subs. Kein Budget-Burn durch Queen-Modellwechsel.

### Anti-Patterns

| Fehler | Fix |
|---|---|
| Stale counts ohne Sub-Verify patchen | Sub-Biene cross-checkt eine ANDERE Datei auf dieselben Drifts |
| Cross-Links nur in eine Richtung | Matrix ist N×N, nicht N×1. Beide Richtungen prüfen |
| Wiki-Link-Format Spaces vs Hyphens | Spaces in `[[]]` sind Obsidian-Aliases, Files haben Hyphens. Sub-Biene muss normalisieren |
| Sub-Biene schreibt ohne Backup | Gamma-Sub hat /tmp/vault-patch-gamma/backup/ erstellt vor jedem Patch |

## Ergebnisformat

Reihenfolge: Kurzfazit → Inventar → Gap-/Problem-Analyse → priorisierte Maßnahmen →
Umsetzungsworkflow → QA-Checkliste → offene Punkte.

Bei `[AGENT-MODE: AKTIV]`: striktes JSON-Schema
`{kurzfazit, inventar[], gap_analyse[], massnahmen[], workflow[], qa_checkliste[], offene_punkte[]}` — keine Erklärtexte.

## Wichtige Skills für Cross-Fork-PRs (Basti nutzt Toqsick-Fork)

- **`orchestration/pr-ship-pattern`** — End-to-End "Feature → gemergter PR" Blueprint
- `yuno-team-orchestrator` — Personas + Fix-Loop für Verifier-Phase
- `github-pr-workflow` — Rein mechanische PR-Steps
- `multi-agent-pitfalls-cheatsheet` — Vor jedem `delegate_task` laden
- `system-documentation` — Post-Merge-Doku in Vault + `~/docs/system/`

## Quellen & Verwandtes

- Historische Specs (eingefroren): `~/Downloads/Github/{docs-refresh-master-workflow.md, master-workflow-ai-agenten-template.md, skill-multi-agent-master-workflow.yaml}`
- Source-of-Truth-Index: `~/Downloads/Github/master-workflow-overview.md`
- Domain-Adapter: `orchestration/workflow-template` (5 Templates, Mnemosyne-Hooks, Farb-Legende)
- ReAct-Labels + Reflexion: `orchestration/hermes-react-pattern`
- Context-Budget & Compaction: `orchestration/hermes-context-budget`
- Pattern-Index & Outcome-Prompts: `orchestration/hermes-agentic-patterns`
