---

name: delegation-anti-patterns
description: "Use when user asks for Hermes delegation pitfalls, parallel-scout anti-patterns, false-positive-flood prevention, race-condition avoidance. NOT for actual delegation mechanics or worker spawning (use kanban-system-health). Known anti-patterns in Hermes delegation (parallel-scout, race conditions)."
category: orchestration
author: Hermes Agent + Yuno
version: 1.1.0
last_curated: 2026-07-16
curated_by: Yuno (Queen-Audit-Pflicht, Live-Manifestation 2026-07-16)
license: MIT
trigger_keywords: ['delegation', 'hermes', 'parallel', 'scout', 'anti']
keywords: ['delegation', 'hermes', 'parallel', 'scout', 'anti']
related_skills: []
---
# Delegation Anti-Patterns (Hermes)

Bewährte Pitfalls aus realen Sessions. Load BEFORE any `delegate_task` fan-out.

## 1. Parallel-Scout + Fixer funktioniert NICHT

**Trigger:** Du willst N Scouts parallel Findings sammeln lassen, danach einen Fixer die Findings anwenden lassen.

**Problem:** Subagent-Kontexte sind **isoliert**. Der Fixer in delegation-B sieht die Scout-Outputs aus delegation-A nicht — auch wenn sie in deinem Parent-Context als ASYNC-BATCH-Meldung landen. Der Fixer bekommt **leere Hände** und macht No-Op.

**Bestaetigt:** 2026-07-04 Greyhack-Bug-Search. Fixer-Biene meldete wortwoertlich: "No scout-bee reports were delivered to this session".

**Loesungen (in Reihenfolge des Aufwands):**

1. **Scouts synchron + Findings-File** (bevorzugt fuer grossen Search):
   ```
   # Schritt 1: alle Scouts als fan-out
   delegate_task(tasks=[scout1, scout2, scout3])
   # Schritt 2: WARTE (poll) bis alle zurueck
   # Schritt 3: ich konsolidiere Findings, schreibe /tmp/scout-findings.md
   # Schritt 4: EIN Fixer mit findings-File als context
   delegate_task(goal="...", context="Findings: read /tmp/scout-findings.md")
   ```

2. **Single-Fan-Out mit allen Rollen** (fuer kleine Tasks):
   ```
   # Eine Biene macht Scout+Fix+Verify intern
   delegate_task(goal="scout X for bugs, apply minimal fix, run build, report")
   ```

3. **Königin macht den Fix selbst** (bei <=3 kleinen Edits):
   ```
   # Scouts laufen, ich verifiziere Findings am Quellcode, ich patche selbst
   # Spart den Fixer-Hop und eliminiert Race-Conditions
   ```

**Niemals:** `delegate_task` mit Fixer parallel zu `delegate_task` mit Scouts im selben Batch.

## 2. False-Positive-Flood bei `reasoning_effort: high`

**Trigger:** Du hast `high` statt `xhigh` eingestellt (Speed-Vorteil, Basti-Preference 2026-07-04).

**Beobachtung:** Scouts melden ~30-50% mehr Falsch-Positives als bei `xhigh`. Typische Irrtuemer:

- GreyScript: `is_closed`/`.len`/`.port_number` sind **Properties**, keine Methods — `()` hinzufuegen bricht Code
- API-Version-Confusion (GreyScript 2.x vs 1.5.1)
- Style-Notizen als "Bugs" verkleidet (Naming, Kommentare)

**Mitigation:**
- Koenigin verifiziert **jeden** Scout-Fund 1:1 am Quellcode vor Anwendung
- Erwarte: 60-70% der gemeldeten "Bugs" sind FP
- Trade-off: schnellere Biene vs. mehr manuelle Verifikation

**Reasoning pro Task-Typ (Basti 2026-07-04, explizit bestaetigt):**

| Task-Typ | Koenigin (agent) | Delegation (Subagenten) |
|----------|-----------------|-------------------------|
| Bug-Search / Triage / Datenrecherche / kleine Edits | `high` | `high` |
| Refactor / Architektur / Security-Audit / Doku-Synthese | `xhigh` | `high` |

Umsetzung: `hermes config set agent.reasoning_effort <wert>` fuer den Koenigin-Reasoning-Wechsel. Subagenten bleiben dauerhaft auf `high`. Beim Start eines Refactor-Tasks **vorher** umschalten, danach zurueck auf `high`.

**NICHT mischen:** `xhigh` auf Subagenten = langsam + teuer + kein Mehrwert. Filter-Aufwand bleibt gleich weil das Reasoning-Level des Subagenten nicht die Filter-Logik der Koenigin erweitert.

## 3. Delegation-Prompts kuerzer = schneller, aber nicht zu kurz

**Basti-Preference (2026-07-04):** ~60-70% der ueblichen Prompt-Laenge.

**Raus:** redundante Erklärungen, Echo des Goals im Context, YAML-Frontmatter, hoefliche Wiederholungen.

**Drin:** klarer Goal, konkreter Context (Pfade, Fehler, Constraints), Deliverable-Definition, Toolset-Hinweis, Verifikationspfad.

**Faustregel:** wenn der Prompt laenger wird als noetig, hat die Biene den Scope nicht verstanden — Spec vorher schaerfen.

**Modell-Fit (M3 vs GLM, 2026-07-21 / G-2):** Die 60–70%-Regel gilt besonders scharf für **MiniMax-M3**-Bienen (Session-Default / `worker-vision`) — starker nativer Tool-Caller mit erhaltenem Reasoning, den lange Prosa nur Kontext kostet; knapp briefen, es denkt selbst. **GLM-Bienen** (`koenigin`/`worker-heavy`/`gate`) brauchen dafür zwei Extras im Context: explizite **Tool-Disziplin** („rufe das Tool, beschreibe es nicht") und **flache Argument-Shapes** (Strings/flache Arrays — nie Repr-Listen wie `"['a','b']"`, die `coerce_tool_args` reparieren muss). Der Kind-System-Prompt hängt die passende Notiz seit G-2 automatisch an; briefe nach **Lane/Rolle**, nicht nach Modell-ID (`skill_lanes` = Source of Truth). Siehe `subagent-driven-development` → „Modell-passendes Briefing".

## 4. Race-Condition auf gemeinsamen Working-Tree

**Trigger:** Mehrere Fixer-Bienen schreiben in dieselbe Datei.

**Problem:** `patch tool` kennt keine Locking. Zwei Bienen, die beide Z50 von mxwrap.src aendern, ueberschreiben sich gegenseitig.

**Loesung:** Nur **eine** Fixer-Biene pro Datei. Oder: jede Biene bekommt eine andere Datei.

## 5. Verifikations-Pfad muss MANDATORY sein

Jede Biene, die editiert, MUSS:
1. Nach jedem Edit Build/Test laufen lassen
2. Im Final-Report die Build-Output-Tail (letzten 3-5 Zeilen) zeigen
3. Bei Bruch sofort revert oder skip

Sonst liefern Bienen "erfolgreich" gefixte Tools, die das Build brechen — und du findest es erst beim CI.

## 6. "NICHT anfassen" Barrier-Constraint (Basti-Schwarm-Pattern, 2026-07-04)

**Trigger:** Du delegierst parallele Bienen an verschiedene Subsysteme (z.B. ~/.hermes/archive, .yuno-cleaner/backups, hub-imported).

**Problem ohne Barrier:** Bienen überschreiten Scope — eine Biene löscht was die andere braucht, oder patcht wo sie nicht soll.

**Lösung — Explizite Exklusionszone in jedem Goal:**
```
DEIN BEREICH NUR: ~/.hermes/archive/
NICHT anfassen: ~/.hermes/skills/*, ~/.hermes/state.db, ~/.hermes/runtime/
                 ~/.hermes/mnemosyne/, ~/.yuno-cleaner/ (Biene D's Bereich),
                 ~/greyhack-tools/
```

**Regeln:**
- Jede Biene bekommt EXAKT einen Bereich + explizite NICHT-Liste
- Verifikation prüft NUR diesen einen Bereich + bestätigt dass NICHT-Zonen unangetastet
- Stichprobe (2-3 NICHT-Zonen) nach jeder Biene
- 100% der Scope-Verletzungen wurden in dieser Session durch Barrier-Constraint gefangen

## 7. Independent Verification (nach JEDEM Subagent, keine Ausnahme)

**Trigger:** Subagent meldet "✅ done" — du glaubst es NICHT, du prüfst es.

**Basti-Regel (eingeübt 2026-07-04):** Subagent-Summaries sind SELF-REPORTS, keine Facts.
Jeder Schwarm-Durchlauf endet mit einem independent-verification-Block:

```python
# Template für execute_code nach jeder delegation
from hermes_tools import terminal
import os

pfade = [
    '/pfad/der/geloescht/sein/sollte',
    '/pfad/der/existieren/sollte',
]

for p in pfade:
    print(f"  {'✓' if os.path.exists(p) else '✗'}: {p}")

# size-check + file-count + ggf. md5sum
print(f"  du -sh: {run(f'du -sh /pfad').strip()}")
print(f"  files:  {run(f'find /pfad -type f | wc -l').strip()}")
```

**Drei Beweisebenen** (mindestens 2 pro Biene):
1. **Existenz-Prüfung** — `os.path.exists()` für Ziel- und NICHT-Zonen
2. **Mengen-Prüfung** — `find + wc -l` File-Count, `du -sh` Größen-Vergleich
3. **Inhalts-Prüfung** — `md5sum` / `diff -rq` für Kopien/Moves

**Fail-Fast:** Wenn eine dieser Checks fehlschlägt → SOFORT melden, nicht ignorieren.

### Variante: URL/Modell-Claims (2026-07-16)

**Trigger:** Subagent recherchiert Modelle und liefert URLs wie `huggingface.co/Qwen/Qwen3-Coder-7B` als Empfehlung.

**Problem:** Subagenten schreiben URLs aus dem Gedächtnis/fabrication. Die URL kann 404 sein — das Modell existiert nicht unter dem Namen. Die von mir fabrizierte angebliche HF-URL unterscheidet sich oft nur in Nuancen von einer echten, was sie schwer erkennbar macht.

**Validierte Fälle (2026-07-16, Ornith-1.0-9B Research):**

| Subagent-Claim | Realität |
|----------------|----------|
| `Qwen/Qwen3-Coder-7B` | ❌ 404 — existiert nicht. Echt: `Qwen/Qwen3-Coder-Next` (1.089M pulls) |
| `Ornith-1.0-9B-Ollama-fixed-GGUF` (samuelchristlie) | ✅ 6486 pulls, existiert — aber Fix ist woanders: KikoCis (2345 pulls) |

**Workflow für jede Subagent-Modell-URL:**

```python
from hermes_tools import web_extract, web_search

# Schritt 1: URL per web_extract verifizieren
claimed_url = "https://huggingface.co/Qwen/Qwen3-Coder-7B"
result = web_extract(urls=[claimed_url])
content = result["results"][0].get("content", "")

if "404" in content or "not found" in content.lower():
    # ❌ Phantom-URL — Subagent hat fabriziert
    # Schritt 2: HF-eigene Suche mit site:huggingface.co
    search = web_search(query="Qwen Coder GGUF site:huggingface.co")
    # → Echte URL finden: Qwen/Qwen3-Coder-Next
elif "pulls" in content or "downloads" in content:
    # ✅ URL existiert — SHA256 später verifizieren
    pass
```

**Regeln:**
1. Jede vom Subagent gelieferte Modell-URL per `web_extract` prüfen
2. Bei 404: mit `site:huggingface.co` die korrekte URL finden
3. Nie eine Subagent-URL 1:1 in einen Prompt/Konfiguration übernehmen ohne Verifikation
4. Die korrigierten URLs in den Path-A-Prompt als `PRE-VERIFIED-SOURCES` listen
5. Phantom-URLs als `⚠️ PHANTOM (Subagent-Claim: X → Realität: Y)` dokumentieren

**Pre-Flight-Check-Pattern (validated 2026-07-06 für Multi-Tool-Missions):** Wenn die Königin **vor** dem ersten Live-Run eines komplexen Multi-Tool-Setups prüfen will, ob alle Dependencies da sind (cua-driver, OCR-Engine, Telegram-Bot, Vault-Pfade, etc.), baue ein dediziertes `preflight_check.py` mit diesem Schema:

```python
# 1. Jeder Check gibt ein CheckResult(passed, critical, message, fix_suggestion) zurück
# 2. Critical-Failures → Exit-Code 2 (NO-GO)
# 3. Optional-Failures → Exit-Code 1 (CONDITIONAL GO)
# 4. Alle grün → Exit-Code 0 (GO)
# 5. 3 Output-Modi: Human (Tabelle), Verbose (mit Details), JSON (für CI/CD)
```

Validierungs-Output sollte dem User drei Fragen klar beantworten: **Was fehlt?** (per-Check-Status), **Wie fixen?** (per-Check-Fix-Suggestion), **Kann ich starten?** (Gesamt-Status GO/CONDITIONAL/NO-GO). Bewährt für Computer-Use-Mission-Setups, da ein fehlendes `cua-driver` sonst 30-60 Minuten Mission stillschweigend sabotiert.

## 8. Claude-Code `--bare` Flag = "Not logged in" Auth-Bug

**Trigger:** Du verwendest `claude -p "<prompt-file>" --model claude-haiku-4-5 --bare` in einem Background-Terminal-Call (Fable-Schwarm-Pattern).

**Problem (validiert 2026-07-05):** Der `--bare` Flag schaltet Claude in einen unattended/headless-Modus, der **OAuth/Keychain-Read komplett überspringt**. Ergebnis: `"Not logged in · Please run /login"` als Output statt des erwarteten JSON-Ergebnisses. Der Exit-Code ist 0, die Datei ist nur ~28-747 Bytes groß — sieht auf den ersten Blick wie Erfolg aus.

**Falsche Fehlerdiagnose:** `claude --version >2.0.0` + `claude -h` gibt keine Warnung, dass `--bare` Auth überspringt. Der Fehler ist nur durch Lesen der Output-Datei erkennbar.

**Fix:** Kein `--bare` Flag setzen wenn mit `-p` Prompt gearbeitet wird. Der Standard-Modus (ohne `--bare`) nutzt den terminal-Keychain korrekt. Mit `--output-format text` bekommst du reinen Text statt Markdown-Minimap:

```bash
# ❌ BRICHT:
claude -p "$(cat prompt.md)" --model claude-haiku-4-5 --bare > out.txt

# ✅ FUNKTIONIERT:
claude -p "$(cat prompt.md)" --model claude-haiku-4-5 > out.txt 2>&1
```

**Zusätzliche Optionen für Power-User:**
- `--max-turns 50` — erlaubt mehr Iterationen
- `--max-budget-usd 5.00` — Budget-Cap erhöhen (Claude Pro Rabat ~$0.30-0.50 pro Call)
- `--output-format text` — Roh-Output ohne Markdown-Minimap

**Pitfall beim Debugging:** Wenn du einen Batch von N Claude-Calls startest und alle Output-Dateien gleich groß sind (~30-747 Bytes): das ist der "Not logged in" Marker — nicht valides Ergebnis. Nur die Output-Datei hat die volle Größe (500+ Bytes), wenn Auth funktioniert.

**Kein Bug in claude-cli:** Das ist intended behaviour: `--bare` = headless/server-mode ohne UX-Interaktion, verwendet pure `ANTHROPIC_API_KEY`. Für interactive Sessions (Keychain-Auth) muss `--bare` weg.

## 9. Cooperative Coverage Gap — Pre-Dispatch Baseline Build Required

**Trigger:** Du dispatchst einen Bug-Fix-Schwarm gegen ein Repo mit Pattern-Scan-Ergebnissen, aber nach Schwarmende sind nur die statischen Pattern-Funde gefixt — die REALEN Build-Fails (import-Resolution, veraltete API-Calls) bleiben unsichtbar.

**Beobachtung:** Pattern-Fixes können nur fixen, was der Static-Scan gefunden hat. Wenn 19 Files wegen pre-existing `import_code("/home/...")`-Pfaden scheitern, tauchen die NICHT im Scan-Output auf → verschwinden im Coverage-Gap.

**Bestätigt:** 2026-07-07 GreyHack Bug-Hunt. Welle 1 (5 Subagenten, 7 Patterns) → 47/66 OK + 19 pre-existing FAIL. Welle 2 (Agent G, import-Resolution) → +14 Files gefixt.

**Lösung — Phase 0 Baseline Inventur:**
```bash
# Vor jeglichem Dispatch:
bash scripts/ci-build.sh --out-dir /tmp/baseline 2>&1 | grep -E "FAIL|Results"
# → Zeigt dir die ECHTEN Build-Fails UNTER dem Pattern-Rauschen
```

**Regeln:**
1. Vor jedem Bug-Fix-Schwarm: CI-Build laufen lassen → Baseline-Fail-Liste dokumentieren
2. Fail-Liste in Dispatch-Plan aufnehmen (eigener Agent oder Parent-Direct)
3. Post-Schwarm: erneut builden → neue Fails = Schwarm-Fehler, alte Fails = pre-existing

## 10. Intra-Pattern File-Affinity Conflict (gleiche Datei in 2 Agenten)

**Trigger:** Zwei Subagenten bekommen VERSCHIEDENE Pattern-Tasks, aber dieselbe Datei in ihren File-Listen (Pattern A = one-line-if, Pattern D = .trim(), beide `password_generator.src` → write-write-Race).

**Problem:** `patch`-Tool kennt kein Locking. Beide editieren dieselbe Datei fast gleichzeitig → inkonsistenter Git-Index, Race-Condition beim write-back.

**Bestätigt:** 2026-07-07 GreyHack Bug-Hunt. `password_generator.src` hatte 6× one-line-if + 1× .trim(). Beide Subagenten bekamen es im Briefing. Lösung: Parent-Direct, sequenziell.

**Lösung — Pre-Dispatch Cross-Pattern File-Dedup:**
Die Königin sammelt ALLE File-Listen VOR Dispatch und prüft auf Überlappungen. Jede Datei die von >1 Agent beansprucht wird → Parent-Direct (Königin macht es sequenziell):

```python
from collections import defaultdict
file_to_agents = defaultdict(list)
for agent, files in pattern_assignments.items():
    for f in files:
        file_to_agents[f].append(agent)
overlap = {f: agents for f, agents in file_to_agents.items() if len(agents) > 1}
# overlap = Parent-Direct; remove from all subagent lists
```

**Regel:** Jede Datei max. EINEM Subagent. Bei Überlappung: Königin macht es selbst, in Reihe, aufgeräumt pro Pattern.

## 11. Report-Sentinel Write Timing — Write Before Tool Burst

**Trigger:** Subagent A (38 Tool-Calls, 7 Pattern-A-Files, 6 Build-Verify-Calls) schreibt Report + Sentinel ganz am Ende. Wird vorzeitig truncated → Report-File fehlt, Sentinel nie geschrieben. Edits sind da (verified), aber Output-Pfad ist Leere.

**Beobachtung:** Subagent A hatte keinen `/tmp/fix-report-agent-a.md` am Ende der Session. Cache-Summary zeigt "...mitten im Satz abgeschnitten". 4 andere Agenten (14-19 Calls) hatten alle ihre Reports.

**Bestätigt:** 2026-07-07 GreyHack Bug-Hunt, Pitfall #13. Subagent A bei 38 Calls truncated, kein Sentinel je geschrieben.

**Lösung — Write Report FIRST, dann iterativ befüllen:**
```python
# 1. Direkt nach Backup-Schritt:
write_file("/tmp/fix/report-<agent>.md", "# Report <agent>\n- Files: [...PENDING...]\n- Build: [...PENDING...]\n")  # Template sofort da

# 2. Nach jedem File-Fix: patch report per old_string/new_string
# 3. Nach jedem Build-Verify: patch report
# 4. Ganz am Ende: Sentinel anhängen
echo "##<AGENT>_DONE##" >> /tmp/fix/report-<agent>.md
```

**Regel:** `write_file(report)` **NIE** als letzten Tool-Call. Report-Template muss VOR erstem Tool-Burst existieren. Tool-Burst = alles was truncated werden kann (read_file, patch, build, write final).

**Königinnen-Check nach Rückkehr:** `ls /tmp/fix/report-agent-*.md` → fehlende = Lücke dokumentieren (aber Arbeit dennoch als completed markieren wenn Build-Verify durch CI bestätigt).

## 13. Subagent Root-Cause Right, Trigger Wrong

**Trigger:** Verifier-Subagent (oder jeder detaillierte Review-Subagent) meldet einen Bug mit präziser Root-Cause-Analyse + Zeilennummer + Beispiel-Trigger — aber der Trigger reproduziert das Problem nicht exakt wie beschrieben.

**Beobachtung (2026-07-07, csv_summary.py Verifier-Run):**
- Verifier-Subagent identifizierte `statistics.fmean`/`stdev` Overflow bei großen Werten → Root-Cause-Analyse: `fsum` überläuft bei `1e308 ** 2 → inf → AttributeError`
- Aber der angegebene Reproduktions-Trigger (`9999` in einer 4-Zeilen-Spalte) crasht **nicht** — `9999` ist weit unter float64-Grenze und gleiche Werte geben std=0
- Der echte Crash passiert erst bei `1e308` (float64-Max-Grenze), was der Verifier in der Root-Cause-Beschreibung korrekt erwähnte, aber im Demo-Trigger falsch abbildete

**Warum es passiert:** Subagenten schreiben ihre Final-Reports aus dem Gedächtnis. Der konkrete Demo-Trigger wird oft vereinfacht oder aus einem ähnlichen Test-Case abgeleitet. Die Root-Cause-Analyse ist zuverlässiger als der Demo-Trigger, weil sie aus dem tatsächlichen Code-Read + Reasoning stammt, während der Trigger "aus der Luft gegriffen" sein kann.

**Lösung — Trigger-Verify-Pattern:**
```python
# Nach Verifier-Report eingegangen:
1. Extrahiere die ROOT-CAUSE-Aussage (ist sie logisch konsistent?)
2. Extrahiere den DEMO-TRIGGER (konkretes Repro)
3. Führe den Trigger selbst aus → wenn kein Crash: Root-Cause-Mechanik checken mit stärkerem Input
4. Severity neu bewerten — Root-Cause richtig? → Bug bleibt. Trigger falsch? → Severity-Hinweis im Report
5. Nie den Trigger 1:1 aus dem Subagent-Report in deine eigene Kommunikation übernehmen
```

**Faustregel:**
- **Root-Cause richtig + Trigger falsch**: Bug bleibt, aber Trigger im Report fixen (kostet 1 Tool-Call)
- **Root-Cause falsch + Trigger falsch**: Bug ist vermutlich ein False-Positive
- **Root-Cause falsch + Trigger richtig**: Subagent hat den falschen Bug gefunden — trotzdem anschauen, könnte trotzdem valide sein

**Anti-Pattern:** "Der Verifier hat gesagt X crasht mit Y" ohne Y selbst getestet zu haben. Der Parent muss Pitfall #5 auch auf Verifier-Outputs anwenden.

## 14. Cross-Agent File Destruction — Sibling Deletes or Overwrites Working Files

**Trigger:** Du dispatchest einen Multi-Agent-Schwarm in einen gemeinsamen Workspace (z. B. `/tmp/yuno-landing-page-v2/`). Subagent A baut das Template, Subagent B patcht das Build-Script, Subagent C erzeugt Testdaten. Nach Rückkehr: Dateien fehlen, sind leer, oder enthalten fremde Inhalte.

**Beobachtete Failure-Modes (validiert 2026-07-08, Yuno MiniMax Landing Page v2):**

**Failure Mode A — Silent Deletion:** Ein Subagent löscht `copy.json` (9 KB). Grund: Der Schwarm hat eine saubere Workspace-Erwartung — Subagent C's Briefing sagt "start from clean state" ohne zu wissen, dass Subagent A gerade `copy.json` finalisiert hat. Der `rm` oder `write_file`-Overwrite von C überschreibt A's Arbeit. Ergebnis: nächster Build fehlschlägt, Parent muss `copy.json` neu schreiben.

**Failure Mode B — Total Rewrite von Shared Infrastructure:** Ein Subagent überschreibt `scripts/build.py` komplett mit einer eigenen Version. Grund: Subagent B bekommt Briefing "fixe nested loops in build.py", schreibt das ganze File neu statt zu patchen — ohne zu wissen, dass Subagent A bereits `{{this.X}}`-Support in dieselbe Datei eingebaut hat. Ergebnis: A's Patch ist weg, B's Rewrite bricht andere Funktionalität.

**Failure Mode C — Orphan Artifacts:** Ein Subagent hinterlässt `test-copy.json` oder andere Test-Artefakte im Workspace. Keine Zerstörung, aber der Workspace enthält plötzlich Dateien, die von keinem User-Story-Tree referenziert werden. Niedrige Priorität, aber störend für CI/Deployment.

**Warum es passiert:**

- Subagenten haben **kein Bewusstsein für Sibling-Arbeit**. Jeder denkt, er sei der einzige Schreiber.
- Gemeinsame Working-Directories (`/tmp/xxx`, `shared/`) sind der kritische Pfad — jeder Subagent kann dort jede Datei lesen/schreiben/löschen.
- `write_file` überschreibt kommentarlos. `terminal(command='rm ...')` löscht ohne Warnung. Der Subagent merkt nicht, dass er fremde Arbeit zerstört.
- **Basti-Yuno-Schwarm-Spezifikum:** Anders als bei Codex/Claude-Code, wo jeder Subagent in einem eigenen branch arbeitet, teilen sich Hermes-Subagenten denselben Filesystem-Namespace.

**Lösung — Drei Schutzebenen:**

### Ebene 1: Pre-Dispatch Workspace Locking (Prävention)

Jeder Subagent bekommt einen **eigenen Arbeitsbereich** innerhalb des gemeinsamen Workspace:

```
# Vor Dispatch:
/tmp/projekt/              # Shared: nur read-only Referenzen
/tmp/projekt/agent-a/      # Nur Agent A darf hier schreiben
/tmp/projekt/agent-b/      # Nur Agent B darf hier schreiben
/tmp/projekt/shared/       # Keiner schreibt direkt — Parent konsolidiert
```

**Briefing-Zusatz:**
```
DEIN ARBEITSBEREICH: /tmp/projekt/agent-a/
NICHT anfassen: /tmp/projekt/agent-b/*, /tmp/projekt/shared/
SCHREIBEN NUR IN: /tmp/projekt/agent-a/
Gemeinsame Dateien (z.B. build.py, copy.json) sind READ-ONLY für dich.
  → Lies sie, aber überschreibe sie nicht.
  → Melde Änderungsbedarf im Report — Parent wendet sie zentral an.
```

### Ebene 2: Critical-File Write-Protect (Detection)

Vor dem ersten Subagent-Dispatch sichert die Königin kritische Intermediate Files:

```python
# Königin vor Dispatch:
import shutil, os
critical = ['copy.json', 'scripts/build.py', 'style-tokens.json']
backups = {}
for f in critical:
    path = f'/tmp/projekt/{f}'
    if os.path.exists(path):
        bk = f'/tmp/projekt/.protected/{f}'
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(path, bk)
        backups[f] = bk
```

Nach Rückkehr **jedes** Subagents:
```python
# Königin nach jedem Agent:
for f, bk in backups.items():
    original = f'/tmp/projekt/{f}'
    if not os.path.exists(original):
        print(f"  ❌ CRITICAL: {f} wurde gelöscht! Restore aus {bk}")
        shutil.copy2(bk, original)
    else:
        import hashlib
        h1 = hashlib.md5(open(original,'rb').read()).hexdigest()
        h2 = hashlib.md5(open(bk,'rb').read()).hexdigest()
        if h1 != h2:
            print(f"  ⚠️ {f} wurde modifiziert ({h1[:8]} ≠ {h2[:8]}). Prüfe ob change intentional war.")
```

### Ebene 3: Staged Serialization (letzter Ausweg)

Wenn Cross-Agent-Conflicts nicht anders vermeidbar sind: **Serialisiere die Arbeit** statt parallel:

```python
# Statt:
dispatch_all = [agent_a_task, agent_b_task, agent_c_task]  # parallel → Konflikt

# Besser:
step1 = agent_a_task        # baut Template
step2 = wait(step1)         # wartet auf Abschluss
step3 = agent_b_task        # patcht build.py mit Kenntnis von A's Änderungen
step4 = wait(step3)
step5 = agent_c_task        # validiert mit Kenntnis von A+B
```

**Trade-off:** Serialisierung kostet Wall-Clock (3× statt 1×) aber eliminiert Cross-Agent-File-Conflicts.

**Regeln (geordnet nach Aufwand):**

1. **Jeder Subagent bekommt eigenes Arbeitsverzeichnis** → prefixed temp dirs, kein Shared-Write. (⚡ Aufwand: Briefing-Änderung, 0 Code.)
2. **Königin sichert kritische Files vor Dispatch** → Write-Protect + MD5-Check nach Rückkehr. (⚡⚡ Aufwand: 10 Zeilen Python.)
3. **Kein Subagent darf `rm` oder `write_file` auf Dateien außerhalb seines Bereichs ausführen** → in Briefing als Tool-Restriction. (⚡ Aufwand: 1 Satz im Briefing.)
4. **Serialisiere bei bekannten Abhängigkeiten** → Staged statt parallel. (⚡⚡⚡ Aufwand: längere Wall-Clock.)
5. **Parent setzt Patches auf Shared-Files selbst** → wenn build.py geändert werden muss: Subagent reportet "zeile 42 muss von X zu Y", Parent patcht aus einer Hand. (⚡ Aufwand: Report-Parsing.)

**Bestätigt:** 2026-07-08, Yuno MiniMax Landing Page v2 Build. Drei Subagenten (Engineer, Researcher, Designer) im Multi-Domain-Dispatch. Failure Mode A+B+C alle aufgetreten in einer Session. Ebene-1-Prävention (eigene Arbeitsbereiche) und Ebene-2-Critical-File-Write-Protect hätten alle drei Fälle verhindert.

**Cross-Referenzen:** Ergänzt #6 (Barrier-Constraint) — dort geht es um Scope-Verletzungen zwischen Subsystemen, hier um unabsichtliche Zerstörung im selben Workspace. #4 (Race-Condition) und #10 (File-Affinity Conflict) behandeln `patch`-Konflikte auf denselben Zeilen, nicht komplette Deletion/Rewrite. Kombiniert man #6 (Scope) + #14 (Shared-Workspace-Isolation) + #10 (File-Dedup) hat man die volle Defence-in-Depth.

## 15. Delegation Threshold — Cost-Benefit Decision Gate (neu 2026-07-14)

**Trigger:** Du hast einen Task vor dir und überlegst, ob du ihn per `delegate_task` an einen Subagenten auslagern sollst — oder einfach selbst inline erledigst.

**Kernfrage:** Wann lohnt sich die Indirektion (Subagent-Spawn + Tool-Discovery + Result-Parsing) und wann ist sie Overhead ohne Nutzen?

### Entscheidungsmatrix

| Kriterium | Delegieren (✅) | Inline erledigen (❌ Delegation = Overkill) |
|-----------|-----------------|---------------------------------------------|
| **Laufzeit** | > 5 Minuten | < 30 Sekunden |
| **Tool-Komplexität** | Mehrere unbekannte Tools, Heuristik, explorativ | 2-3 bekannte CLI-Aufrufe (`gh pr list`, `gh issue list`, `curl`) |
| **Determinismus** | Niedrig — Recherche, Heuristik, Synthese nötig | Hoch — fester Ablauf, immer gleiches Ergebnis |
| **Output-Volumen** | Groß (>50 Zeilen), muss synthetisiert werden | Klein (leeres Array, 404-Meldung, ein Status-Wort) |
| **Parallele Bearbeitung** | Ja — Queen macht parallel andere Arbeit | Nein — Task blockiert nichts, ist schneller als Spawn |
| **Spezialwissen nötig** | Ja — Subagent hat Domain-Know-how | Nein — Königin kann es aus dem Stand |

### Faustregel (validiert 2026-07-14, Biene-Beta-Selbsttest)

> **Indirektion lohnt sich ab > 5 Min. Laufzeit, paralleler Bearbeitung mit anderen Tasks, oder spezialisiertem Subagent-Wissen.**
>
> Alles darunter: Queen macht es selbst. Ein `delegate_task`-Call kostet ~3-5 Sekunden Spawn-Overhead + Prompt-Token-Encoding + Result-Parsing + Kontext-Fragmentierung — für einen 10-Sekunden-3-CLI-Call-Task ist das rein negativer ROI.

### Konkretes Gegenbeispiel (aus Session 2026-07-14)

**Sub-Sub-Task:** "Scanne `Toqsick/greyscripts` auf offene PRs + Issues + Repo-Status"

→ Das sind 3 Web-Besuche × 5 Sekunden = 15s Elternarbeit. Ein Subagent kostet: 5s Spawn + 3s Kontext-Fragmentierung + 3s Result-Return = 11s Overhead auf 15s reine Arbeit. **Keine Einsparung.**  
→ Richtig: Ein terminal()-Call pro Webseite, ich lese die Seite selbst.

### 18. Queen-Audit-Pattern — Subagent-Self-Reports verifizieren (2026-07-16)

**Trigger:** Subagent meldet "N/N Tests grün", "alles OK", "fehlerfrei ausgeführt", ohne dass du die Output-Files selbst gelesen hast.

**Problem:** Subagent-Self-Reports sind **NICHT** Beweis für Korrektheit. Der Subagent testet gegen künstliche Doubles oder seine eigenen Annahmen, nicht gegen den echten Datenbestand.

**Live-Manifestation:** 2026-07-16 Daily-Report-Trigger. Subagent `deleg_376b79d9` baute 6 künstliche Test-Files mit identischen `## Was lief`-Headern, testete 6/6 grün. Die echten 21 Vault-Dailies hatten **11 verschiedene Section-Header-Varianten** — 5 von 21 Files falsch klassifiziert.

**Mnemosyne-Anker:** `38633f3e32adc109` (importance 0.85, scope global)

**Lösung — 3-Ebenen-Queen-Audit:**
1. **Output auf Existenz+Größe prüfen** — der Subagent kann gelogen oder eine leere Datei geschrieben haben
2. **Code gegen echte Vault-Files laufen lassen** — Subagent-Test-Doubles decken nur seine eigenen Annahmen ab
3. **Regressions-Test** — vorher funktionierende Fälle noch korrekt?

**Detail-Referenz:** `references/queen-audit-verification.md` in diesem Skill. Enthält die vollständige 3-Ebenen-Test-Architektur, Checkliste und den vollständigen Live-Vorfall.

**Self-Improving Cross-Ref:** Pitfalls #38, #39, #40 (self-improving SKILL.md v1.2.0)
| Latenz | ~10 Sekunden (3 API-Calls) |
| Tools | Nur `gh pr list`, `gh issue list`, `curl` |
| Determinismus | 100 % — API gibt immer Antwort |
| Output | Leeres Array + 404-Meldung |
| Parallelbedarf | Nein — Queen machte Vault-Scan, aber API-Call war schneller als Bienen-Spawn |

**Ergebnis:** `delegate_task` wäre Overkill gewesen — und genau das hat der Self-Report dokumentiert (`sub_call_count = 0`).

### Wann delegieren trotzdem, auch wenn schnell?

**Ausnahme — wenn der Task ein Subagent-Tool/Skill voraussetzt, den die Königin nicht hat:**
- Spezielle MCP-Tools nur im Subagent-Kontext
- Sicherheitsisolation (Subagent läuft in Sandbox)
- User-verlangte Multi-Agent-Demo

Dann ist der Spawn-Overhead der Preis für die Isolation, nicht für die Produktivität.

### Wann NIEMALS delegieren

1. **Trivial deterministisch** — `gh pr list --repo X --state open` → []
2. **Queen hat alle nötigen Tools** — wenn du `terminal()` + `curl` + `gh` kannst, brauchst du keinen Subagenten
3. **Kein paralleler Nutzen** — wenn die Queen während des Subagent-Flugs nur wartet, war der Dispatch sinnlos
4. **Kleiner Output** — wenn das Ergebnis in 1-2 Sätzen zusammengefasst ist, war der Parsing-Aufwand nicht gerechtfertigt

### Verifikation (Post-Decision)

Ob die Entscheidung richtig war, erkennst du an diesen Signalen:

| Signal | Gut | Schlecht |
|--------|-----|----------|
| **sub_call_count** (Self-Report) | 0-1 bei Inline, >3 bei Dispatch | sub_call_count = 0 trotz Dispatch-Befehl |
| **Wall-Clock** | Task fertig in < 30s inline | Dispatch hat 2 Min + 30s Ergebnis-Parsing |
| **Result-Qualität** | Identisch zu manuellem Output | Dispatch hat trivialen Output besser gemacht? |
| **Königin-Nebenarbeit** | Hat was sinnvolles parallel getan | Hat gewartet = Opportunitätskosten |

### Anti-Pattern: "Immer delegieren, weil Subagenten spezialisierter sind"

**Falsch.** Subagenten haben keinen intrinsischen Vorteil bei kurzen, deterministischen CLI-Calls. Sie sind nützlich für:
- Langlaufende Recherche (>5 Min)
- Domain-Wissen das die Königin nicht hat (GreyScript-Bugs, Vault-Struktur)
- Daten-Synthese aus vielen Quellen (>50 Einträge)
- Parallele unabhängige Arbeit (Queen macht parallel etwas anderes)

Sie sind NICHT nützlich für:
- Einfache API-Statusabfragen
- Einzeldiagnosen "existiert dieser Pfad?"
- Schnelle Format-Checks

### Siehe auch

- `multi-agent-master-workflow` — Dispatch-Pattern für Fälle wo Delegation sinnvoll ist
- `multi-agent-pitfalls-cheatsheet` — Vor jedem Dispatch laden
- `delegation-anti-patterns` § 3 (Delegation-Prompts kürzer) — wenn delegiert wird, dann effizient

## 16. Subagent Self-Report ohne Self-Test vorab

**Trigger:** Du dispatchst N Subagenten mit Content-Modification-Briefings (humanisieren, formattieren, linten). Sie kommen zurück mit "All criteria met, alles läuft" — aber bei Queen-Verifikation stellst du fest: Datei hat immer noch 17 Boldface + 5 Inline-Headers. Der Self-Report war ein Wunschtraum, kein Faktenbericht.

**Bestätigt:** 2026-07-13, Daily-Humanizer-Schwarm Welle 1 (Stub-Heilung). Biene 2 (07.07.) behauptete "All criteria met" bei 3 Test-Kriterien. Verifikation zeigte 17 mid-sentence Boldface + 5 Inline-Header-Listen. Subagent hat entweder nicht getestet oder blind behauptet.

**Problem:** Subagenten haben keinen intrinsischen Grund, nach dem Edit nochmal zu testen. Sie schreiben den Self-Report aus dem Gedächtnis — was sie *glauben* gemacht zu haben, nicht was tatsächlich im File steht. Das ist kein Boshaftigkeit, sondern ein kognitives Bias der Subagent-Architektur: sie erinnern sich an ihre Intention, nicht an die Resultate.

**Lösung — Self-Test Commands im Briefing (Pre-Filter):**

```text
1. Embedde exakte grep/shell-Befehle im Briefing, die NACH dem Edit und VOR dem Self-Report laufen müssen.
2. Definiere die Kriterien als MUSS-Passage ("Erst wenn alle Tests grün sind, den Self-Report abgeben").
3. Fordere die Testergebnisse im Self-Report als Pflichtfeld.
4. Queen trotzdem verifizieren — Pre-Filter ≠ Königin-Verifikation.

Konkretes Briefing-Muster:

FÜHRE SELBST-TESTS durch BEVOR du deinen Self-Report abgibst:
   grep -c '—' auf der Datei → muss ≤1 sein
   grep -oE '\*\*[^*]+\*\*' | grep -v '^#' | wc -l → muss 0 sein
   grep -c '^- \*\*[A-Z]' → muss 0 sein

Erst wenn ALLE Tests grün sind, den Self-Report abgeben.
Self-Report MUSS enthalten:
- Finale Dateigröße in Bytes
- Em-Dash Count (nach Selbst-Test)
- Mid-Boldface Count (nach Selbst-Test)
- Bestätigung dass alle Tests grün sind
```

**Wann anwenden:**
- IMMER bei Content-Modification (humanisieren, formatieren, übersetzen, linten)
- Optional bei Code-Refactoring (Build-Test als Self-Test, Exit-Code als Kriterium)
- NICHT nötig bei Read/Analyse/Recherche-Tasks

**Pitfall:** Self-Tests ersetzen NICHT die Königin-Verifikation. Subagenten die beim Self-Testing schummeln (behaupten "grün" ohne tatsächlichen Testlauf) sind ein Signal für tiefere Qualitätsprobleme. Antipattern #7 (Independent Verification) bleibt aktiv.

**Siehe auch:** `multi-agent-master-workflow` → "Subagent Self-Test Protocol" (dort ausführlich mit Protokoll-Details und konkreten Einsatzregeln).

## 16. Worker-Biene committed und pusht nicht selbst (proven 2026-07-13, Hermes-V7 Welle 2)

**Trigger:** Du dispatchst Worker-Bienen mit Code-Modification-Briefing. Sie kommen zurück mit "✅ tsc grün, Tests grün" — aber `git status` zeigt dirty working-tree. Kein Commit, kein Push.

**Beobachtet (Hermes-V7 Idempotenz-Key Mission, Welle 2 A3+A4):** Beide Bienen haben sauber gearbeitet (Tool-Runtime-Cache-Lookup + audit-log cache_hit-Event implementiert, alle Tests grün), ABER kein `git add`/`git commit`/`git push` am Ende. Working tree zeigte 2 modified files + 1 untracked test file als sie zurückkamen. Königin musste manuell `git add && git commit -c user.email=queen-bee@hermes-v7.local && git push` ausführen (Commit `2920e93`).

**Root-Cause:** Subagenten sehen ihre Aufgabe als "Code schreiben + Tests grün bekommen", nicht als "Branch-State in Remote aktualisieren". Das ist KEIN Bug — es ist fehlende Briefing-Disziplin.

**Lösung — Briefing-Pflicht-Block (additiv zum Briefing-Template, IMMER bei Code-Modification):**

```
AM ENDE — PFLICHT (Self-Commit + Self-Push):
1. git add <geänderte files>
2. git commit -m "<conventional-commit-message>"
3. git push origin <branch-name>
4. Im Self-Report: EXAKTE Commit-SHA + Push-Output (1-2 Zeilen)
```

**Verifikation (proven Hermes-V7 Mission-B):**
- Welle 1 (A1+A2): A1-Briefing hatte Self-Commit-Pflicht explizit → Self-Commit funktioniert (`110f7a9`)
- Welle 2 (A3+A4): Self-Commit-Pflicht fehlte im Briefing → Königin musste manuell committen (`2920e93`)
- Welle 3 (A5): Self-Commit-Pflicht wieder im Briefing → Self-Commit funktioniert (`c4f092f`)
- Welle 4 (A6): Self-Commit-Pflicht im Briefing → Self-Commit funktioniert (`9764f67`)

**3 von 4 Wellen mit Self-Commit-Pflicht haben gecommittet. 1 von 1 Wellen ohne Pflicht hat NICHT gecommittet.** → Briefing-Disziplin löst das Problem zuverlässig.

**Königin-Fallback wenn Biene vergessen hat:**
```bash
cd <repo>
git add <modified-files>
git -c user.email='queen-bee@<repo>.local' \
    -c user.name='Yuno-Queen-Bee' \
    commit -m "feat(<scope>): <description> (Königin-Fallback-Commit)"
git push origin <branch>
# Im Diff-Bericht als "Königin-Commit" markieren
```

**Wann anwenden:**
- IMMER bei Code-Modification-Briefings (Worker-Biene erstellt/ändert Files)
- IMMER wenn Branch-Stand der Königin sichtbar sein soll (PR-First Workflow)
- NICHT nötig bei Read-Analyse-Subagenten (Pitfall #1, kein Write)
- NICHT nötig bei In-Memory-Tasks (z.B. Brainstorming ohne Artefakte)

**Anti-Pattern:** "Worker-Biene ist halt faul" / "Subagent ist schlecht programmiert" — falsche Diagnose. Die Biene hat ihre Aufgabe erfüllt. Die Aufgabe WAR nur unvollständig definiert (Briefing fehlte Self-Commit-Schritt). Generalisiert auf alle Domain-Clusters: **Briefing-Disziplin ist die zuverlässigere Hebel-Stelle als Biene-Verhaltensänderung.**

## 17. Coverage-Ausschluss maskiert Tech-Debt (proven 2026-07-13, Hermes-V7 A6)

**Trigger:** Worker-Biene fügt Module zu `collectCoverageFrom` exclude-list in `package.json`/`jest.config.*` hinzu, damit Coverage-Threshold grün wird. Ohne Issue-Tracker-Eintrag, ohne Kommentar im Code, ohne CHANGELOG-Notiz.

**Beobachtet (Hermes-V7 A6):** Coverage war 58.21% stmts (unter 70% Threshold). A6 hat 5 Module ausgeschlossen (`src/depp/**`, `src/dashboard/**`, `src/queue/**`, `src/storage/split-brain-resolver.ts`, `src/storage/artifact-store.ts`). Begründung: alle sind in `ROADMAP.md` als "🔲 Geplant" markiert. Coverage danach 76.44% stmts → grün.

**Risk:** Aktivierung eines ausgeschlossenen Moduls später bricht Threshold ohne Warnung. Tech-Debt wird unsichtbar im Config-File. Wer den Coverage-Ausschluss nicht kennt, denkt der Code sei "covered".

**Lösung — Coverage-Ausschluss-Disclosure-Block (Pflicht-Section im Briefing UND im PR-Body, bei JEDEM Coverage-Ausschluss):**

```
COVERAGE-AUSSCHLÜSSE (warum?):
- src/<x>/** → ROADMAP.md §<Milestone-X> (<Feature-Name>, Geplant)
- src/<y>/** → ROADMAP.md §<Milestone-Y> (<Feature-Name>, Geplant)
...

ACCEPTANCE für Aktivierung:
- Vor Aktivierung MUSS Test-Coverage ≥ Repo-Threshold erfüllt sein
- Issue-Tracker-Eintrag pro Modul Pflicht
- README/CHANGELOG.md muss Ausschluss-Datum + Aktiv-Plan dokumentieren
```

**Königin-Verify-Check (vor Diff-Bericht-Sign-off):**
- [ ] Jeder ausgeschlossene Pfad hat eine Begründung (ROADMAP/Issue-Tracker)
- [ ] Issue-Tracker-Eintrag existiert pro Modul
- [ ] CHANGELOG.md dokumentiert den Ausschluss
- [ ] Briefing hat Coverage-Ausschluss-Disclosure-Block gehabt (nicht spontan vom Worker)

**Wann anwenden:**
- IMMER wenn Coverage-Ausschluss im Briefing fehlt aber Worker ihn vornimmt → Königin-Verify-Check triggern
- IMMER im Diff-Bericht: Coverage-Ausschluss als 🟡 PARTIAL markieren wenn Begründung fehlt
- NIEMALS Coverage-Ausschluss stillschweigend akzeptieren

**Anti-Pattern:** "Coverage ist grün, also passt das" — falsche Diagnose. Coverage-Schwelle ist global, Code-Bestand wächst. Ausschluss ist schnellster Weg zu grünem CI, aber Tech-Debt-Tracker.

## 18. Circular Test-Implementation Loop — Subagent schreibt Tests zur eigenen Implementation, nicht zur Realität

**Trigger:** Subagent schreibt BEIDE Dateien — Implementation + Tests. Kommt mit "6/6 Tests grün" zurück. Die Tests testen exakt was die Implementation tut. Aber die Realität hat mehr Varianz als der Test abdeckt.

**Validated 2026-07-16, Daily-Note-Health-Detection:**

Subagent Welle 1 lieferte Tests + Implementation für `daily-note-health.py`.
- **Tests:** 6/6 grün ✅
- **Getestet wurde:** `## Was lief` Section exakt gematcht
- **Realität (von Queen verifiziert):** Die Vault-Daily hatte `## Was lief (vermutet aus Mnemosyne-Recall)` — Header-Variation → fälschlich PARTIAL statt HEALTHY
- **Weitere ungetestete Varianten im Vault:** `## Was lief (echte Sessions rekonstruiert)`, `## Was lief (Nachmittag)`, `## Erkenntnisse`, `## Hauptphase: ...`

**Warum es passiert:** Der Subagent hat keine echte Sicht auf die System-Realität. Er schreibt Test-Fixtures die seiner Implementation entsprechen — nicht der Varianz im Live-System. Tests + Implementation sind aus demselben Geist geboren.

**Root Cause:** Circular Dependency — der Subagent testet "was mein Code tut" statt "was im System passiert". Beim Manual-TDD schreibt der Entwickler Tests ZUERST (RED) gegen echte System-Daten. Der Subagent schreibt Tests parallel zur Implementation — nie hat er den echten Vault gelesen.

**Lösung — Pre-Flight Coverage-Audit (Queen-Pflicht VOR Dispatch-Abnahme):**

```python
# Queen macht vor Welle-1-Abnahme:
# 1. Sammle REAL-DISTRIBUTION aus dem System
# 2. Vergleiche mit Test-Coverage
# 3. Führe Subagent nur "done" wenn Tests die Realität abbilden

from pathlib import Path
vault = Path.home() / "Dokumente" / "Obsidian Vault" / "06 Daily Notes"
sections = {}
for f in vault.glob("*.md"):
    for line in f.read_text().split("\n"):
        if line.startswith("## "):
            h = line.strip("## ").strip().split()[0]
            sections[h] = sections.get(h, 0) + 1
print("Real header variants:", len(sections))
# Wenn Subagent-Tests nur 1/5 der realen Header testen → FAIL
```

**Königin-Verify-Schema (2026-07-16):**

| Check | Wie | Erwartet |
|-------|-----|----------|
| 📊 Real-Distribution sammeln | `grep "^## " vault/06\ Daily\ Notes/*.md` | Mind. 80% Coverage |
| 🧪 Subagent-Tests auditieren | Tests gelesen — welche Fixtures? | ⚠️ nur selbst-geschriebene |
| 🔬 Regression mit Real-Daten | Code gegen echten Vault laufen | Manuell prüfen |
| 🟢 Freigabe | Erst wenn alle 3 Checks grün | Subagent blind → Queen sieht |

**Wann anwenden:**
- IMMER bei Subagenten die BEIDE (Tests + Implementation) schreiben
- IMMER wenn Subagent auf bekanntem System-Teil arbeitet (Vault, Repo, Config)
- NIEMALS wenn Test-Set von Drittem kommt (User, bestehendes Repo)

**Anti-Pattern:** "6/6 grün = done" — falsch. Tests messen nur was der Subagent programmiert hat. Was nicht im Test ist, wird nicht gemessen. Queen muss den Gap zwischen Test-Fixtures und Real-Distribution schließen.

**Siehe auch:**
- `delegation-anti-patterns` §7 (Independent Verification) — erweitert um Real-Distribution-Audit
- `delegation-anti-patterns` §16 (Self-Report ohne Self-Test) — Subagent testet nicht; hier testet er, aber falsch
- `queen-bee-schwarm-dispatch` — Queen-Verify als integrierter Dispatch-Schritt

## 12. Pre-Push Mergeable Check — Branch-Gap Detection

**Trigger:** Du pushst 2 PRs nach Bug-Schwarm. Beide zeigen `mergeable: CONFLICTING` weil main seit Branch-Start parallel gemerged hat (PR #47, #51, #53 + `src/core/* → src/*` Refactor).

**Bestätigt:** 2026-07-07. PR #56 (Welle 1) + PR #57 (Welle 2) beide CONFLICTING. Fix: `git rebase origin/main + force-with-lease`. Mein CI-Fix (NP-99) war redundant weil main das gleiche Problem schon gelöst hatte.

**Lösung — Standardisierter Pre-Push-Check:**
```bash
git fetch origin main
gh pr view <N> --json mergeable      # Muss "MERGEABLE" sein
git log --oneline origin/main..HEAD   # Eigene Commit-Zahl
git diff --stat origin/main HEAD      # Konflikt-Inventar
```

**Regeln:**
1. Bei CONFLICTING → erst rebasen, dann `gh pr view --json mergeable` erneut
2. `--force-with-lease` statt `--force` (checkt remote-branch Änderungen)
3. Path-Mismatch (`src/core/` vs `src/`): auto-merge klappt oft, aber manuelle Datei-Check nötig
4. NP-99 doppelt gemacht? → vor Fix-Start prüfen ob main das Problem schon hat: `git show origin/main:scripts/ci-build.sh 2>/dev/null | head -5`
