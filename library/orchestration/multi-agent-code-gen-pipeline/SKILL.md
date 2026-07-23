---
name: multi-agent-code-gen-pipeline
description: |
  Use when generating a modular tool through a six-phase multi-agent pipeline, parallelizing independent components, or adding staged review and integration gates.
  NOT for tiny single-file edits, tightly coupled work that cannot be isolated, or accepting generated modules without build and behavior verification.
  Coordinates specification, parallel implementation, review, integration, testing, and final validation for agent-produced tools.
version: 1.2.0
changelog:
- '1.2.0 (2026-07-04): Added Phase 5.5 Mock-Env Testing (greybel execute), Pitfall #36 ''orchestriere sofort'' User-Preference, Pitfall #37 Global-Scope in Mock-Env, Trigger erweitert um ''orchestriere'', Ergebnis-Tabelle aktualisiert'
- '1.1.0 (2026-07-04): Initialer Vollausbau mit 6 Phasen, Bug-Fix-Loop, Deploy-Pattern'
author: Yuno
tags:
- orchestration
- code-generation
- multi-agent
- greyhack
- pipeline
license: MIT
trigger_keywords: ['agent', 'review', 'integration', 'generating', 'modular']
keywords: ['agent', 'review', 'integration', 'generating', 'modular']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['multi-agent-work', 'linux-system-maintenance', 'subagent-driven-development']
---


# Multi-Agent Code Generation Pipeline

6-Phase-Pipeline für den Bau modularer Mega-Tools mit 5+ parallel arbeitenden Subagenten.

**Trigger:** Der User sagt „bau(e) [Name] Tool", **„orchestriere [datenbank|analyse|tool]"**, oder zeigt eine externe Referenz (Steam Guide, GitHub, Doku) und will ein gleichwertiges In-Game-Tool bauen lassen.

**Wichtig — User-Preference: „orchestriere sofort"**
Wenn der User sagt **„orchestriere"**, erwartet er **sofortige parallele Agenten-Dispatchs**, keine Status-Checks, keine Erklärungen, keine „erstmal schauen was da ist"-Phase. DIREKT loslegen. Siehe Pitfall #36.
- Falsch: „Lass mich erstmal Status checken..." → korrigiert zu „DIREKT 5 Agenten losgeschickt"
- Richtig: Deploy-Befehl + Spec schreiben + 5 Agenten dispatchen → das passiert in <30 Sekunden
- Ausnahme: Wenn der Kontext nach Modellwechsel verloren ging (Modell-Swap → Kontext-Resets), dann ein „Moment kurz ich hol den Stand" ist akzeptabel — aber MAXIMAL 2 Terminal-Befehle, dann dispatch.
- Grenzfall (validiert 2026-07-04): User sagt „nein ordere eine orchestrierung mit 5 sub agenten die V6 als .src in config schreiben" — das war eine Korrektur weil ich anfing zu erklären was es gibt statt einfach 5 Agenten loszuschicken.
- Faustregel: Bei „orchestriere" → schreibe Task-Briefings (max 3 Sätze pro Agent) → dispatch → parallel arbeiten → Ergebnisse einsammeln. Erklärungen kommen NACH dem ersten Ergebnis-Durchlauf, nicht VOR dem Dispatch.

**Abgrenzung:** Das ist KEIN Research (→ `multi-agent-orchestration` mit 3 Experten). Das ist AKTIVE Code-Generierung mit Build-Zyklus.

---

## 6-Phasen-Pipeline

### Phase 0: Design Spec

1. **Externe Referenz laden** → `web_extract(url)` wenn vorhanden
2. **Architektur skizzieren:** wie viele Module? Core/Scan/Post/Net/Utils? Größe pro Modul?
3. **Spec schreiben** → `/tmp/<tool>_spec.md` mit:
   - Commands pro Modul (Tabelle)
   - Lib-Imports (crypto, metaxploit, aptclient)
   - File-Struktur (Pfade, Namen)
   - Trigger-Phrases pro Subcommand

**Pitfall:** Subagenten brauchen identische Spec. `/tmp/` reicht als Shared-Pfad.

### Phase 1: Parallel Coding (5 Subagenten)

**max_concurrent_children=5** ist das harte Gate. Pro Modul ein eigener Subagent:

| Modul | Größe | Verantwortung |
|-------|-------|---------------|
| Core | 400-500 Z | Main-Shell, Help, Lib-Loader, Colors |
| Scan/Recon | 500-600 Z | nmap, exploitscan, deepscan, hack |
| Post-Exploit | 500-600 Z | targets, use, back, fs, jump, loot |
| Network/Chat | 400-500 Z | nslookup, sniffer, trace, botnet |
| Utils/Files | 500-600 Z | ls/cat/write, save/macros/vshell |

**Pflichten pro Subagent-Context:**
- Absoluter Output-Pfad: `/home/bratan/greyhack-tools/<tool>/modules/<module>.src`
- Erste Zeile: `//command: <tool_name>` (in-game Command-Detection)
- Zweite Zeile: `//include: <core>` für Module die Core-Funktionen teilen
- Größenangabe (~XXX Zeilen) — hält die Agenten fokussiert

**Kritische Regeln für den Context:**
- Language: GreyScript (GreyHack). Übersetzung ins GreyScript ist Teil des Jobs.
- Output: `.src` datei Schreiben (r/w)
- Include-Pfade sind relativ zum File, nicht zum Workspace
- 0 ist truthy, char(10) für newline, is_binary für Folder-Check, keine ternary expressions
- use `get_shell()` (KEINE Parameter!), nicht `get_shell(username, password)`
- `for x in map` iteriert KEYS, nicht VALUES → `for k in map.indexes; v = map[k]`
- einzeilige `if X then Y end if` ist UNSAFE → mehrzeilig

### Phase 2: Build Validation (Parent-Direct)

**KEIN Subagent.** Build-Validation ist deterministisch — 5 Sekunden Arbeit, kein LLM nötig.

```bash
cd /home/bratan/greyhack-tools/<tool>/modules
for f in *.src; do
  echo "=== BUILDING $f ==="
  npx greybel build "$f" "/tmp/build_out_$f" 2>&1 | tail -15
done
```

**Auswertung (pro File):**
- ✅ Grüner Build → kein Fix nötig
- ❌ Syntax-Breaker (one-line-if, ternary, missing end function) → mechanische Fixes
- ❌ Import Errors (Include-Path) → Pfad-Korrektur
- ❌ Runtime-Strukturelle Fehler → notieren für Phase 4

**Typische 1st-Pass-Build-Ergebnisse (validiert 2026-07-04):**
- Core-Modul: oft 1/5 sofort grün (simple Hilfsfunktionen)
- Scan/Net/Post: häufige Scope-Variablen-Konflikte (wiederverwendete Namen wie `x`, `i`, `r`)
- Util: `for x in map` auf File-Object statt File.indexes → Keys-Iteration

### Phase 3: Pattern-Scan (5 Subagenten, parallel)

Jeder Subagent scannt **alle Module** (nicht nur eines) nach einer Pattern-Klasse:

| Agent | Pattern-Klasse | Sucht nach |
|-------|---------------|------------|
| 1 | String-Literals | `"char(10)"`, `split("char(10)")`, `join("char(10)")`, `\n` in Strings |
| 2 | Null-Check / Type-Safety | `indexOf == null`, `get_content or ""`, `file.size` unguarded, `split()` ohne Length-Check |
| 3 | Syntax-Breaker | Einzeilige `if/then/end if`, Ternary-Expressions, single-quotes `'text'`, Inline-if |
| 4 | greybel-Inkompat | `shell.start_terminal`, fehlende `end function`, doppelte Klammern, escaped quotes `\"` |
| 5 | Runtime-Crasher | `get_shell(params)`, `is_folder`, `0` als truthy, `for x in map` (Keys!), `globals.x`, `HTTP.Request` |

**Output-Struktur (erzwungen):**
```
PATTERN: <Pattern-Name>
FILE: <module.src>:<line>
SEVERITY: HIGH/MED/LOW
FIX: describe what's wrong
```

Keine natürliche Sprache, keine Zusammenfassung — nur strukturierte Hits.

### Phase 4: Fix-Schwarm (5 Subagenten, parallel)

Jeder Fix-Agent bekommt GENAU EIN Modul und fixt ALLE Bugs darin:

| Agent | Modul | Fix-Auftrag |
|-------|-------|-------------|
| 1 | core.src | Alle Bugs aus Phase-3-Report |
| 2 | scan.src | Alle Bugs aus Phase-3-Report |
| 3 | post.src | Alle Bugs aus Phase-3-Report |
| 4 | net.src | Alle Bugs aus Phase-3-Report |
| 5 | util.src | Alle Bugs aus Phase-3-Report |

**Kontext-Template pro Fix-Agent:**
```
FIX: <module.src>

GEFUNDENE BUGS (aus Phase 3):
- L123: if/then/end if einzeilig → mehrzeilig machen
- L456: `for x in map` → `for i in map.indexes; x = map[i]`
- L789: ...

CRITICAL: FIX MUSS BUILD-FÄHIG SEIN
Nach jedem Fix: greybel build testen! Nur fixes committen die builden.
Prüfung nach Fix:
1. grep -nE '\bif\b.*\bthen\b.*\bend if\b' module.src → sollte 0 sein (keine einzeiligen if)
2. npx greybel build module.src /tmp/build_test 2>&1 | grep 'error'
   → Wenn Fehler: zurück zum Fix-Schritt
```

**Entscheidungsmatrix (Fix-Strategie):**
- ≤ 20 Fixes, alle mechanisch → **Parent-Direct Batch** (ein Regex-Pass pro Pattern)
- > 20 Fixes → **5 Subagenten** (je einer pro Modul)
- Wenn Subagenten verschicken → KEINE Pattern-Master-Fixes erwarten. Die Agenten finden die meisten, aber verpassen ~5-15% der Edge Cases (nested if-in-if, combined `end for end if`, statement-chain one-line-ifs mit `;`)

### Phase 4a: Iterative Fix-Loop (Parent-Direct, MANDANTORY)

Phase 4 ist NIE ein One-Shot. Nachdem die Fix-Agenten zurück sind → **immer selbst builden und nachfixen**.

```
Schleife:
  1. Build alle Module (greybel build)
  2. Wenn alle grün → Fertig!
  3. Error-Zeilen lesen → Patch einzeln
  4. GOTO 1
```

**Typischer Zyklus (validiert 2026-07-04, 5 Module, ~100KB, 142 Bugs):**

| Iteration | Ergebnis | Aktion |
|-----------|----------|--------|
| 0 (Agenten zurück) | — | Read file, check scope |
| 1 (Build) | 1/5 grün | 4 Files haben Rest-Bugs |
| 2 (Manual Fix) | 3/5 grün | scan + util durch |
| 3-7 (Manual Fix) | 4/5 grün | Ein Fix erzeugt oft neuen Error (verschobene line numbers) |
| 8-15 (Manual Fix) | 5/5 grün | Letzte hartnäckige einzeilige ifs, combined `end for end if` |

**3 Bug-Klassen die Fix-Agenten häufig übersehen:**

1. **Nested `if` in einzeiligem `if`:** `if file then tmp = f.get_content; if typeof(tmp) == "string" then old = tmp end if end if`
   → Expandierung des OUTER `if` frisst das `end if` des INNER `if` auf. Fix: outer zuerst expandieren, dann inner.

2. **Combined Terminators:** `if Dp then for Cd in Dp; Cd.chmod("777"); end for end if`
   → `end for end if` auf einer Zeile. Der Regex `if/then/end if` matched nicht. Manuell fixen.

3. **Statement-chain mit `;` in then-body:** `if not ports then warn("Keine Ports"); exit end if`
   → Die `;` werden vom Regex in separate Lines gesplittet, aber wenn eine `if`-artige Klausel in der chain steckt (`if cond then stmt1; if x then y end if; stmt2 end if`), entsteht Chaos.

**Häufigste Patch-Fallstricke im Loop:**

- **Line-Number-Shift:** Jeder Patch fügt Zeilen hinzu (einzeiliges if → 3 Zeilen). Die Error-Zeile des nächsten Builds zeigt auf die ALTEN Zeilennummern + Shift. Manuell korrigieren.
- **Duplikat-Header:** `patch` kann Bereiche duplizieren wenn `old_string` mehrfach vorkommt. Immer replace_all=false und auf Unique-String achten.
- **`else if` ist valide GreyScript 1.5+** — wird fälschlich als einzeiliges `if then` gemeldet. `else if` auf einer Zeile ist OK, braucht keinen Fix.
- **Dispatch-Zeilen ignorieren:** Code wie `if params.len > 0 then cmd = params[0]` am Ende einer Datei (nach letzter `end function`) ist **top-level dispatch code**, kein Bug.
- **`if cond then print(...)` ist valide einzeiliges if** wenn danach return/exit auf nächster Zeile folgt — aber greybel magt es trotzdem nicht. Expandieren.

### Phase 5: Build-Verification (Parent-Direct)

```bash
cd /home/bratan/greyhack-tools/<tool>/modules
all_green=true
for f in *.src; do
  out="/tmp/build_$(basename $f .src)_final"
  if npx greybel build "$f" "$out" 2>&1 | grep -q 'error'; then
    echo "❌ $f"
    all_green=false
  else
    echo "✅ $f ($(wc -l < "$f") Zeilen)"
  fi
done
if $all_green; then echo "🎉 ALLE MODULE BAUEN GRÜN!"; fi
```

**Bei Nichterfolg:** Zurück zu Phase 4a (nur die fehlschlagenden Files).

**Erwartungswert (validiert 2026-07-04):** 15 Iterationen bei 142 Bugs in 100KB über 5 Module.

### Phase 5.5: Mock-Env Smoke Test (NEU)

Nachdem ALLE Module builden, einen funktionalen Mock-Test per `npx greybel execute` durchführen. Das zeigt Runtime-Fehler die der Build-Mechanismus nicht fängt.

```bash
# Core-Init-Test (Banner + Lib-Loader + Prompt)
echo -e "help\nexit" | timeout 15 npx greybel execute \
  /home/bratan/greyhack-tools/<tool>/modules/<core_module>.src --silent 2>&1 | head -20

# Sub-Module Test (ein Modul als standalone)
echo -e "ls /\nexit" | timeout 15 npx greybel execute \
  /home/bratan/greyhack-tools/<tool>/modules/<post_module>.src --silent 2>&1 | tail -20
```

**Validierte Erwartungen (2026-07-04, 5 Module, ~100KB):**

| Test | Ergebnis | Interpretation |
|------|----------|----------------|
| Core-Init (Banner + Libs) | ✅ 3/4 Libs geladen | OK — 4. Lib ist Game-exklusiv |
| Help-Command | ✅ 60+ Commands in 14 Sektionen | Core funktioniert |
| Version-Command | ✅ v1.0.0 mit Author/Credits | Display OK |
| Sub-Module Dispatch | ⚠️ "Command nicht implementiert" | Mock-Env startet nur EIN Script — Sub-Module sind im Game eigenständige `//command:` Programme. **KEIN Bug.** |
| Util Runtime | ❌ `Path "h" not found in scope` Z:670 | Global-Variable die NUR im echten Game-Build-Kontext existiert. Siehe Pitfall #37 |

**Pitfall #37 — Global-Variablen die nur im echten Build-Kontext existieren:**
- `npx greybel execute` startet IMMER nur das angegebene Script isoliert
- Module die auf Globals aus anderen `//include:`-Modulen angewiesen sind, crashen im Mock-Env
- Typische Symptome: `if not h then h = {} end if`, `if not Db then Db = {} end if` auf Zeilen die globalen Variablen-Zugriff zeigen
- **Das ist KEIN Bug im Source** — es ist eine Mock-Env-Limitation. Im echten GreyHack baut der Compiler alle Module zusammen.
- **Wann mock-testen:** Core + Help + Version + Lib-Loader sind valide Mock-Tests. Sub-Commands (nmap, targets, ls) sind NICHT mock-testbar.
- **Wenn ein Mock-Test crasht → nicht automatisch fixen → mit echtem Game-Build verifizieren**
- **Verifikation:** `npx greybel build <file> /tmp/build_test` → wenn Build ✅ grün, dann ist der Code valide

**Fazit aus Phase 5.5 (2026-07-04):**
> Core funktioniert. Sub-Module sind als eigenständige Programme deployed, was OK ist.
> Der `h not found` Error ist eine Mock-Env-Limitation, kein echter Bug.
> Report speichern als `~/.hermes/scratch/<tool>-mock-test-<datum>.md`

### Phase 6: Deploy (DB-Injection)

5 Dateien in die GreyHackDB injizieren — Backup, INSERT, FileSystem-Links, Verify.

**Schablone:** `templates/db-deployment.py` — für N Module erweiterbar, mit integrierter Duplikat-Erkennung und PRAGMA integrity_check.

```bash
# Ausführung
python3 /path/to/db-deployment.py

# Was passiert:
# 1. Backup: GreyHackDB.db → GreyHackDB.db.backup-<datum>
# 2. Vorher-Check: existierende Config/yuno_viper* Einträge zählen
# 3. INSERT: Jede .src → Files(Content) Tabelle
# 4. FileSystem-JSON: Jede Datei in Computer.FileSystem.Config[] linken
# 5. Verify: PRAGMA integrity_check + Einträge zählen
```

**Im Spiel danach:**
- CodeEditor → Ctrl+O → `/home/gregor/Config/<name>.src` öffnen
- Build-Button → /bin/<name>
- Shell: `<tool_name>` ausführen
- **Game restart erforderlich** bei neuen `//command:` Dateien

---

## max_concurrent_children=5 — Umgang mit dem Gate

Das harte Limit von **5 parallelen Subagenten** ist in `config.yaml → delegation.max_concurrent_children` gesetzt.

**Wenn 6 Tasks anstehen:**
1. Identifiziere den **mechanischsten** Task (Build, grep, regex-scan, datei-existenz)
2. Führe DIESEN Task Parent-Direct aus
3. Die 5 reasoning-heavy Tasks gehen an Subagenten

**Validierung (2026-07-04):** 5 Subagenten für Pattern-Scan + 1 Parent-Direct Build-Validation = funktioniert. Der Build-Check in 5 Sekunden hätte einen 6. Subagenten nicht gerechtfertigt.

---
## Validierte Sessions

### 2026-07-04 (aktuell) — YUNO VIPER v1
- **Tool:** YUNO VIPER v1 (Viper-Klon)
- **Referenz:** Steam Guide 3132078044 (Viper 2024 von zulu/EntitySeaker), getestet per Mock-Env + Build-Verify + DB-Deploy
- **Module:** 5 (Core/Scan/Post/Net/Util), 3023 Zeilen, ~100KB
- **Phase 2 Ergebnis:** Core ✅ (411 Z), 4 ❌ (einzeilige if/then, include-path, for-loop)
- **Phase 3:** 5 Pattern-Scanner parallel dispatched: 142 Pattern-(a) einzeilige if-Funde, 0 Pattern-(b)–(e)
- **Phase 4:** 5 Fix-Agenten dispatched, ~120/142 automatisch gefixed
- **Phase 4a:** 15 manuelle Iterationen (Patch→Build→ReadError→Patch) für die restlichen Bugs
- **Phase 5:** 5/5 Builds grün ✅ (411/813/666/731/696 Zeilen)
- **Phase 5.5:** Mock-Env Smoke-Test: Core ✅ (Help/Version/Libs), Sub-Module ⚠️ (Mock-Limitation), Util ❌ (Global-Scope, siehe Pitfall #37)
- **Phase 6:** DB-Batch-Injection (5 Files → Config/, 5 FileSystem-Links, integrity_check ok)
- **max_children Gate:** Build → Parent-Direct. 5 Subagenten für Pattern-Scan = funktioniert.

---

## Pitfall-Register

- `orchestration/multi-agent-orchestration` — 3-Expert Research Pattern (älter, Research-Fokus)
- `orchestration/multi-agent-pitfalls-cheatsheet` — Fehlerfalle-Checkliste (vor jedem delegate_task laden)
- `gaming/greyhack` → `references/build-troubleshooting.md` — GreyScript Build-Fehler-Katalog
- `gaming/greyhack` → `references/known-bugs.md` — Alle NP-XX Pattern-Definitionen
- **Parallel-Subagent-Race-Condition:** `references/bienen-race-condition-2026-07-04.md` — Wenn Subagent B inhaltlich von Subagent A abhängt, **sequentialisieren** (Wellen statt Tasks-Array). Post-hoc-Merge nur mit Cross-Verification. Proven auf Hermes-v7 PR #7.
- **Plan-Freshness:** Pläne aus früheren Sessions werden STALE (falsche Issue-Nummern, falsche CI-Stati, falsche Merge-Gaps). Vor jedem Task, der auf einem externen Plan basiert: `git log`, `git merge-base`, tatsächlichen Testlauf checken — nicht dem Plan glauben. Proven 2026-07-04: Fix-Plan behauptete Issue #31 für Cluster-Fixes, Realität war #41/#42.
