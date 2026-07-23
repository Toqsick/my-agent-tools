---
name: ki-murks-verhindern
description: |
  Use when designing or reviewing AI-generated code workflows that need grounding, explicit implementation, automated verification, and evidence-backed acceptance gates.
  NOT for trivial prose tasks, skipping tests because output looks plausible, or declaring code fixed without reproducing and verifying the result.
  Applies a four-phase quality workflow to prevent hallucinated fixes, incomplete code, regressions, and unsupported success claims.
version: 1.2.0
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - quality-gates
    - agent-workflow
    - code-review
    - testing
    - ki-murks
    category: software-development
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['code', 'designing', 'reviewing', 'generated', 'workflows']
keywords: ['code', 'designing', 'reviewing', 'generated', 'workflows']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['writing-plans']
---

# KI-Murks-Verhindern

> Strukturierte KI-Agenten-Workflows mit Quality Gates.
> Basierend auf TheMorpheus' "KI am MURKSEN hindern!"-Methode.
>
> **Referenzen:**
> - `references/quality-gates-checklist.md` — Vollständige Checkliste
> - `references/fixplan-verification-greyscripts-2026-07-04.md` — Fix-Plan-Verifikation
> - `references/self-verifier-pattern.md` — Self-Verifier Pattern (Pitfall #5)
> - Video: https://www.youtube.com/watch?v=CEYDefSEDxY

## Das Problem

KI-Agenten (Claude Code, Codex, Cursor, etc.) produzieren oft:
- Halbfertigen Code der nicht kompiliert
- Fehlende Tests oder broken Tests
- Sicherheitslücken
- Verletzte Coding-Standards
- "Phantom-Fixes" die behauptet aber nicht umgesetzt wurden

## Die Lösung: 4-Phasen-Workflow

```

set -euo pipefail
┌────────────────────────────────────────────────────────────┐
│  GROUNDING AGENT                              │
│  • Recherche für Issue                         │
│  • Code identifizieren                         │
│  • Web-Suche / Docs lesen                      │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│  EXECUTION AGENT                              │
│  • Einarbeiten (Context sammeln)               │
│  • Implementieren                              │
│  • Tests schreiben                             │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│  EVALUATION AGENT                             │
│  • Code review                                 │
│  • Tests ausführen                             │
│  • Sicherheitscheck                            │
│  • Standards prüfen                             │
│                                              │
│  On Error ────────────────────────────┐│
│  └─────────────────────────────────────────────────┘│
│         Feedback ← Execution Agent               │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│  FINALIZING AGENT                             │
│  • Feedback akzeptiert?                        │
│  • git commit & git push                       │
│  • Manuelle Review (Human-in-the-Loop)         │
│  • PR erstellen                                │
└────────────────────────────────────────────────────────────┘
```

## Quality Gates (Checkliste)

### Mindestanforderungen
- [ ] **Min. 2 Reviews** — Code wurde von mindestens 2 Agenten/Instanzen geprüft
- [ ] **Tests vorhanden** — Neue Funktionen haben Tests, alte Tests laufen noch
- [ ] **Issue verlinkt** — Änderung löst ein konkretes Problem (Issue #x)

### Code-Qualitätskriterien (alle prüfen)
- [ ] **korrekt** — Löst das Problem, keine Regressionen
- [ ] **clean** — Kein toter Code, keine Debug-Prints
- [ ] **sicher** — Keine Injection, keine Secrets im Code
- [ ] **performant** — Keine offensichtlichen Bottlenecks
- [ ] **maintainable** — Verständlich, dokumentiert
- [ ] **testable** — Einzelne Units testbar
- [ ] **robust** — Fehlerbehandlung vorhanden
- [ ] **documented** — Komplexe Logik erklärt
- [ ] **compliant** — Folgt Projekt-Standards (Lint, Format)

## Anwendung in Hermes

### Für mich (als AI Agent)

Wenn ich Code schreibe, muss ich die 4 Phasen aktiv durchlaufen:

**1. Grounding** — Bevor ich anfange:
- Verstehe das Problem vollständig
- Lies relevante Dateien
- Recherchiere falls nötig (Web, Docs)

**2. Execution** — Implementieren:
- Schreibe den Code
- Schreibe Tests dazu
- Verifiziere Syntax

**3. Evaluation** — Selbst-Review:
- Lies den Code nochmal durch
- Prüfe: Habe ich alle Quality Gates erfüllt?
- Verifiziere mit tatsächlichen Tool-Calls (read_file, terminal)
- Nicht nur behaupten — nachweisen!

**4. Finalizing** — Abschluss:
- Zeige dem User den Code
- Erkläre was geändert wurde
- Frage bei Unsicherheit nach (Human-in-the-Loop)
- Dokumentiere in ~/docs/

### Beispiel: Code-Änderung

**Vorher (schlecht — MURKS):**
```

set -euo pipefail
User: "Fix den Bug in auth.py"
Ich: *patche die Datei*
Ich: "✅ Fixed!"
# → Phantom-Fix, nicht verifiziert, kein Test
```

**Nachher (mit Workflow):**
```

set -euo pipefail
User: "Fix den Bug in auth.py"

Grounding:
  Ich: Lies auth.py + zugehörige Tests
  Ich: Identifiziere den Bug

Execution:
  Ich: Patche auth.py
  Ich: Schreibe Regression-Test

Evaluation:
  Ich: Lies die gepatchte Datei → Verifiziere Syntax
  Ich: Führe Tests aus → Verifiziere Fix
  Ich: Prüfe Quality Gates

Finalizing:
  Ich: Zeige Diff
  Ich: "Hier ist die Änderung. Tests laufen. OK so?"
```

## Anti-Patterns (was MURKSEN bedeutet)

1. **Phantom-Fixes** — "✅ Fixed" ohne Verifikation
2. **Halbherzige Tests** — Tests geschrieben aber nicht ausgeführt
3. **Context-Blindness** — Code ändern ohne zu verstehen was drumherum passiert
4. **Security-Blindness** — Secrets, Injection, RCE-Risiken ignorieren
5. **Dokumentations-Lücke** — Komplexe Änderung ohne Erklärung
6. **Marketing-Pitches ungeprüft glauben** — Drittanbieter-Pitches (z.B. "98% Recall",
   "23 Tools", "0.8ms Latenz") ohne Code-Lesen + Test akzeptieren → Phantom-Vorteile,
   versteckte Trade-offs (siehe "Verifying Third-Party AI Tool Pitches" unten)

## Verifying Third-Party AI Tool Pitches (Grounding-Sub-Pattern)

Wenn User ein "Marketing-Pitch"-File für ein AI-Tool anhängt (z.B.
"Tired of X, hier ist Y, hat 23 Tools und 0.8ms Latenz"), NICHT direkt
installieren. Pitch-Texte übertreiben systematisch.

**Standard-Workflow (5 Stufen):**

### 1. Existence-Check (10 Sekunden)

```bash

set -euo pipefail
# PyPI: existiert das Package? Welche Version? Lizenz?
curl -sS "https://pypi.org/pypi/<package>/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Version:', d['info']['version'])
print('License:', d['info']['license'])
print('Python:', d['info']['requires_python'])
"

# GitHub: existiert das Repo? Aktiv?
curl -sS -o /dev/null -w "%{http_code}\n" "https://github.com/<user>/<repo>"
```

→ Wenn nichts existiert: STOPP, User informieren, fertig.

### 2. Code-Lese statt README-Glauben (5-10 Minuten)

```bash

set -euo pipefail
# Repo-Struktur holen
curl -sS "https://api.github.com/repos/<user>/<repo>/contents/" | jq '.[] | .name'

# Plugin-Manifest lesen (z.B. plugin.yaml)
# Stimmen die versprochenen Features (Tools, Hooks) mit dem Code überein?
```

**Häufige Pitch-vs-Realität Discrepancies:**
- "23 Tools in 5 Kategorien" → tatsächlich 17 Tools in plugin.yaml
- "Sub-millisecond writes" → 10ms mit Embedding, 0.076ms nur DB
- "Default supports German" → Default ist EN-Embedding
- "Honcho ist Hauptkonkurrent" → ist optional, user nutzt was anderes

**Dokumentiere die Diskrepanzen im Plan-Output**, nicht stillschweigend akzeptieren.

### 3. Phased Test-Strategy (4 Phasen, mit Go/No-Go Gates)

**Phase 1 — Read-only Test (isoliert, kein Risko):**
- Eigenes venv oder temp-dir
- pip install
- API direkt testen (nicht via Hauptpfad)
- Latenz, RAM, Recall messen
- Discrepancies zu Claims dokumentieren

**Phase 2 — Integration (mit 1-Zeilen-Rollback):**
- Backup der Config
- Plugin installieren
- Config-Switch
- End-to-End-Test (Use-Case realistisch)
- 1-Zeilen-Rollback bereithalten BEVOR Phase 3 startet

**Phase 3 — Production-Hardening:**
- Crons für Backup/Wartung
- Performance-Tests (mit/ohne Plugin)
- Edge-Cases

**Phase 4 — Doku:**
- Master-Doku (`~/docs/system/<tool>-setup.md`)
- README-Index
- Memory-Update

**Jede Phase hat ein explizites Go/No-Go** (User entscheidet). NIEMALS
alle 4 Phasen in einem Rutsch ohne Bestätigung.

### 4. Trade-offs explizit kommunizieren

Bevor User "go" sagt, MUSS klar sein:
- RAM/Disk-Impact (+x MB RAM, +y MB Disk)
- Performance-Overhead (z.B. Hook-Overhead)
- Migration-Aufwand (manuell vs auto)
- Vendor-Lock-in-Risiko (Datenformat, Cloud-Dependency)
- Was funktioniert NICHT (Edge-Cases, Limitationen)

**Beispiel Mnemosyne-Pitch-Discrepanzen (verifiziert 2026-06-08):**
| Pitch behauptet | Realität |
|---|---|
| 23 Tools in 5 Kategorien | 17 Tools in plugin.yaml |
| "pip install mnemosyne-hermes" reicht | Symlink `~/.hermes/plugins/mnemosyne/` manuell nötig |
| "Honcho ist Hauptkonkurrent" | ist optional, Basti nutzt eingebauten nous-Provider |
| 65.2% BEAM / 98.9% Recall | Code nicht verifizierbar, Author-Claims |
| 0.8ms writes | 10ms Median (mit Embedding) |
| "Sub-millisecond, fully private" | korrekt für DB-only, 10ms End-to-End mit Embedding |
| Multilingual out-of-the-box | Default ist EN-Embedding, Multilingual muss manuell gesetzt werden |

### 5. Skip-Patterns (RED FLAGS die Skepsis triggern)

Wenn der Pitch eines dieser enthält, **zweifle nach**:

- **Konkrete Benchmark-Zahlen ohne Methodik** ("98.9% Recall", "0.8ms Latenz")
- **"Cloud-free, but..."** mit "but" (= Cloud-call irgendwo)
- **"ICLR 2026 paper"** wenn die Konferenz noch nicht stattfand
- **Tools-Count ohne Quellenangabe** ("23 Tools" — wo definiert?)
- **Marken-Pitch-Stil** mit Logo und CTA ("Star us!")
- **Preisdetails fehlen** bei angeblicher "Free"-Lösung
- **Migration-Aufwand nicht erwähnt** bei "Drop-in Replacement"

### Worked Example: Mnemosyne-Verification (2026-06-08)

User hängte "Tired of your Hermes agent forgetting everything" Pitch-File an.
Statt direkt zu installieren:

1. **Existence-Check:** `mnemosyne-memory` 3.3.0 + `mnemosyne-hermes` 0.1.1
   existieren auf PyPI. GitHub HTTP 200. ✓ Real.
2. **Code-Lesen:** Plugin-Code analysiert via GitHub API. `plugin.yaml`
   zeigt 17 Tools (nicht 23 wie im Pitch). `__init__.py` hat 73KB — substantiell.
3. **Discrepancies dokumentiert** in Pitch-vs-Realität Tabelle.
4. **Phased Test:** Phase 1 (isoliert) → Phase 2 (Integration) → Phase 3
   (Production) → Phase 4 (Doku). Jede Phase mit explizitem Go/No-Go.
5. **Trade-offs vor Phase 2:** +450 MB RAM, +305 MB Disk, "Only one external
   memory provider at a time" Rule, EN-Embedding Default.
6. **Skip-Pattern check:** Pitch hatte "23 Tools" (count mismatch) und
   "98.9% Recall" (Benchmark ohne Methodik) — beide Red Flags. Aber Package
   existierte real und Code war substantiell → weiter mit Skepsis.

**Resultat:** Mnemosyne wurde installiert und funktioniert. Pitch-Discrepanzen
wurden in der Doku festgehalten, nicht in der Realität übersehen.

## Verifying Fix-Plan / Artifact Claims Against Live Sources (Grounding-Sub-Pattern)

> Generalisierung des Pitches-Patterns: Statt nur Marketing-Texten zu misstrauen,
> gilt derselbe Ansatz für **jedes Dokument, das externe State-Behauptungen
> aufstellt** — Fix-Pläne, Roadmaps, Audit-Listen, Issue-Referenzen, Branch-Zustände.
>
> **Referenz:** `references/fixplan-verification-greyscripts-2026-07-04.md` — Konkreter Befund

### Grundprinzip

Wenn ein Fix-Plan, Audit-Plan, Roadmap oder Dokument externe State-Behauptungen
aufstellt (z. B. "CI schlägt bei 13/15 Dateien fehl", "Issues #X, #Y sind offen",
"Branches sind ungefixt"), NICHT blind übernehmen. Immer gegen Live-Quellen
verifizieren — sonst werden Subagenten auf Basis falscher Annahmen gestartet.

### Worked Example: Greyscripts Fix-Plan (2026-07-04)

Fix-Plan für hermes-v7 + greyscripts behauptete:

| Behauptung im Plan | Realität im Repo |
|---|---|
| "Cluster 1 (neg. Index) offen, Issue #31" | Fix **bereits auf main** (129dd63, closes **#42**) |
| "Cluster 2 (inline-if) offen, Issue #31" | Fix **bereits auf main** (1b0e53d, closes **#41**) |
| "#31, #43, #48 müssen geschlossen werden" | Keine einzige Referenz im Git-Log |
| "CI schlägt bei 13/15 Dateien fehl" | CI-YAML existiert — Status unklar |
| Kein Merge-Problem erwähnt | Fixes auf main, CI+Tools auf develop — **keiner vereint beides** |

**Live-Check mit git:**
```bash
# Issue-Nummern prüfen
git log --all --oneline --grep="#31"      # → keine Treffer
git log main --oneline --grep="index"      # → 129dd63 fix: negativer Index ... closes #42
git log develop --oneline --grep="index"   # → keine Treffer (nicht gemerged!)

# Merge-Gap prüfen
git merge-base --is-ancestor main develop && echo "merged" || echo "gap!"
# → gap! Fixes nicht in develop

# CI-Existenz prüfen
git show develop:.github/workflows/ci.yml | head -5
# → CI-Konfiguration existiert
```

**Konsequenz:** Fix-Plan korrigiert: Merge main→develop als neuen P0-Schritt,
Issue-Nummern auf #42/#41 korrigiert, doppelten Aufwand vermieden.

### Standard-Workflow (4 Stufen)

#### 1. Claims extrahieren (aus dem Dokument)

Lies das Dokument und extrahiere alle verifizierbaren Claims:
- Issue-Referenzen (`#X`, `Closes #Y`)
- Branch-Zustände ("ist gemerged", "ist nicht in develop")
- CI/Build-Status ("13 von 15 Dateien fehlschlagend")
- Dependency-Aussagen ("Block hängt an Entscheidung Y")
- Commit-Zustände ("Fix existiert bereits", "Feature ist fertig")

#### 2. Claims gegen Live-Quellen prüfen

| Claim-Typ | Prüfmethode | Beispiel |
|---|---|---|
| Issue existiert/geschlossen | `git log --all --oneline --grep="#X"` | `git log --all --oneline --grep="#31" -5` |
| Branch-Zustand (merged?) | `git merge-base --is-ancestor A B` | `main → develop: merged? → ja/nein` |
| Fix existiert bereits | `git log <branch> --oneline --grep="fix\|cluster\|index"` | `git log main --oneline --grep="index"` |
| Datei existiert | `git show <branch>:path 2>/dev/null` | `git show develop:.github/workflows/ci.yml` |
| Issue-Refs in Commits | `git log --all --oneline --grep="closes #\|fix #\|ref #" -10` | Welche Issues sind WIRKLICH geschlossen? |
| Develop vs Main Gap | `git log main..develop --oneline` + reverse | Weicht der Branch ab? |

#### 3. Discrepancies dokumentieren (Claims vs Reality Tabelle)

| Behauptung im Plan | Realität im Repo | Schwere | Aktion |
|---|---|---|---|
| "Issue #31 ist offen" | #31 nicht im Git-Log; Fix = closes #42 | 🔴 Hoch | Issue-Referenzen korrigieren |
| "Cluster 1 ist ungefixt" | Fix auf main (129dd63) | 🔴 Hoch | Merge main→develop vor Plan-Ausführung |
| "CI schlägt fehl" | CI-YAML existiert `.github/workflows/ci.yml` | 🟠 Mittel | Nach Merge + CI-Rerun messen |
| "Kein Merge-Gap" | Fixes main, Tools develop — unvereint | 🔴 Kritisch | Merge als neuen P0-Schritt hinzufügen |

#### 4. Plan aktualisieren mit Korrekturen

- Entferne Claims die widerlegt sind
- Füge Merge-Gaps als separate Tasks hinzu
- Korrigiere Issue-Referenzen
- Passe Prioritäten basierend auf echtem State an

### Wann anwenden?

- Fix-Pläne die Issues/Branches/CI-Status referenzieren
- Roadmaps die "ungelöste" Probleme beschreiben
- Merge-Strategien die nicht prüfen ob Base-Branches aktuell sind
- Immer wenn ein Dokument Dinge über den aktuellen Stand einer externen Quelle behauptet
- Bevor Subagenten-Arbeit auf Basis eines Plans gestartet wird

### Pitfalls

- **Commit-Messages ≠ Issues** — "Closes #42" im Git-Log heißt nicht dass GitHub-Issue #42
  geschlossen ist. Zusätzlich via GitHub API prüfen.
- **main ≠ develop** — Fix auf main heißt nicht in develop. `git merge-base --is-ancestor` checken.
- **Nicht nur HEAD checken** — Der neueste Commit sagt nichts über ältere Fixes.
  `git log --all --oneline --grep` nutzen.
- **Issue-Nummern vertauschen** — Plan sagt #31, Realität sagt #41/#42. Immer Commit-Messages lesen.
- **Keine falsche Sicherheit durch CI-Existenz** — CI-YAML existiert ≠ CI ist grün.
  Tatsächlichen Build-Status prüfen.
- **Fix-Gruppen nicht übersehen** — Ein Commit kann mehrere Cluster auf einmal fixen.
  Commit-Body lesen, nicht Titel allein.

## Verifying Post-Fix Test Failures: Regression vs Stale Expectation (Evaluation-Sub-Pattern)

> Wenn eine Fix den Core-Behaviour ändert, können downstream Tests stale
> Expectations haben — geschrieben für den alten Broken-State, nicht für
> das korrigierte System. Dieses Pattern unterscheidet echte Regressionen
> von stale Tests.

### Problem

Fix angewandt → Tests laufen → 20/21 grün, 1 bleibt rot.

Das kann bedeuten:
1. **Echte Regression** — der Fix hat einen anderen Case kaputt gemacht
2. **Stale Expectation** — der Test erwartete einen Wert, der nur wegen des Bugs erreichbar war

Wenn du Fall 2 nicht erkennst, revertierst du einen korrekten Fix oder
schwächst Assertions — der Bug bleibt.

### Der Session-Befund (hermes-v7 orchestrator Fix, 2026-07-04)

**Situation:** `withKernel` in `orchestrator.ts` verwendete `task.owner` statt
der phasen-spezifischen Rolle → Security-Kernel blockierte mit ROLE-PROFILE-Error.
Fix: `PHASE_ROLE_MAP` eingeführt, jetzt läuft jede Phase mit korrekter Rolle.

**Nach dem Fix:** 20/21 Tests grün. Der letzte Fehler war ein Audit-Count-Test
der `before + 10` erwartete, aber `before + 12` erhielt.

**Ursache:** Der Test war nie durch den reparierten Pfad gelaufen. Vor dem
Fix scheiterte die `implement`-Phase am TOOL-PROFILE-Check, sodass der innere
`runAtomicToolCall`-Aufruf nie auditierte Events produzierte. Nach dem Fix
komplettiert die Phase korrekt → 2 zusätzliche Audit-Events (intent + result)
vom inneren Adapter-Call.

**Richtige Reaktion:** Test-Expectation von 10 auf 12 aktualisieren (nicht
den Fix revertieren). Kommentar im Test: "2 zusätzliche Events vom inneren
implementer-adapter-Call, der vor dem Fix nie durchlief."

### Standard-Workflow (4 Stufen)

#### 1. Symptom erkennen

Nach dem Fix:
```bash

set -euo pipefail
# Nur 1-2 Tests rot? Prüfe: sind das DIESELBEN Tests wie vor dem Fix?
# Oder sind es ANDERE?
npx jest --no-coverage 2>&1 | tail -5
```

Signal: Die ursprünglichen Fehler sind grün, aber ein **anderer** Test
(der vorher grün war) ist jetzt rot.

#### 2. Test-Expectation auf Herkunft prüfen

- **Woher kommt der erwartete Wert?** Ist es ein Count, ein Status-Code,
  eine State-Transition, ein Fehler-String?
- **War dieser Wert nur erreichbar, weil der Bug existierte?** Z.B.:
  - Event-Count, weil Phasen nie durchliefen
  - Status-Code, weil ein Fehler-Pfad nie getestet wurde
  - Error-Message, weil die Assertion nie matchte
  - State-Transition, die nur im Broken-State Sinn ergibt

#### 3. Datenfluss nachvollziehen

Tracing-Ansatz (terminal-basiert):

```bash

set -euo pipefail
# Bei Audit-Counts: Counte die Events die der Test jetzt sieht
# vs. was er vor dem Fix gesehen hätte
npx jest --verbose src/roles/__tests__/orchestrator.test.ts --no-coverage 2>&1 | grep "AUDIT"
```

Oder:
- **Lies den Test-Kommentar** — steht da "5 Phasen × 2 Events = 10"? Dann
  ist die Referenz die Theorie, nicht die tatsächliche Laufzeit.
- **Prüfe ob innere Aufrufe** (`runAtomicToolCall`, `invoke`, Adapter) selbst
  Events/Logs schreiben — diese sind im Fix vorher nie durchgelaufen.

#### 4. Entscheiden: Stale oder Regression

| Kriterium | Stale Expectation | Echte Regression |
|---|---|---|
| Fix-Change-Type | Core-Behaviour (neue Pfade erreicht) | Nebenwirkung |
| Vorher-Test | Rot (wegen Bug) | Grün (working) |
| Jetzt-Test | Neu rot (ANDERER Test) | Vorher grün, jetzt rot |
| Asserter Wert | Nur im Broken-State erreichbar | Unabhängig richtiger Wert |
| Andere Tests | Andere Tests mit identischem Assert sind grün | Alle Tests mit identischem Assert sind rot |
| Innerer Aufruf | Adapter/Sub-Call erzeugt jetzt Events | Nichts Neues |

**Stale → Expectation aktualisieren**, mit Kommentar:
```ts
// Vorher: 10 (5 Phasen × 2 Events)
// Jetzt:  12 (+2 vom inneren implementer-adapter-Call,
//          der vor dem Fix nie durch das TOOL-PROFILE kam)
```

**Regression → Fix überdenken** (zurück zu Phase 1 im
`systematic-debugging`-Workflow).

### Anti-Patterns

1. **Fix revertieren** weil ein Test rot wird — prüfe erst ob der Test stale ist
2. **Assertion schwächen** (`.toBe()` → `.toBeGreaterThanOrEqual()`) — deckt
   den echten Unterschied nicht auf
3. **Workaround im Production-Code** — "Wenn kein Kernel, skip event" als
   Workaround für korrekte Events → Bug bleibt
4. **"Das war vorher auch so"** — Warnsignal. Vorher war es kaputt, jetzt
   ist es richtig. Der Test muss zum korrigierten System passen, nicht zum
   kaputten.

### Wann anwenden?

- Nach einem Fix der den Core-Control-Flow ändert (neue Pfade erreicht,
  Security-Checks passiert)
- Wenn Tests plötzlich einen **höheren** Count/State-Wert erwarten müssen
- Wenn der Fix TOOL-PROFILE / Security-Checks repariert (diese blockieren
  oft komplette Phasen)
- Immer wenn ein Test sagt "erwarte X", der Fix aber Y produziert, und Y
  korrekt ist

### Verwandte Skills

- `systematic-debugging` — Für den vollständigen Debugging-Workflow
- `test-driven-development` — Für die Test-First-Mentalität
- `critic-gate` — Für automatisierte Output-Validierung

## Self-Verifier Pattern (Pitfall #5 Workaround: Code-Cross-Check)

> **Unabhängige Re-Implementierung von Zähl-/Prüffunktionen zur Bug-Erkennung.**
>
> Gelernt aus: `daily-addendum-gate.py` (2026-07-17) — 5 Quality-Gates für
> Obsidian Daily Notes mit Self-Verify Mode.
>
> **Referenz:** `references/self-verifier-pattern.md` — Vollständige
> Implementierungsdetails mit 3 Real-World-Beispielen.

### Problem

AI-Agenten schreiben oft Zähl- und Prüffunktionen, die **denselben
Denkfehler in mehreren Metriken reproduzieren**. Beispiel: `count_boldface()`
matcht `t** und das auch **` weil die Regex `**`-Paare ohne Token-Grenze
erfasst. Alle 5 Gates sehen "grün" — weil der Bug konsistent ist. Der Output
ist trotzdem falsch. Das ist **Pitfall #5**: Agenten-Code spiegelt Agenten-Bugs.
Tests, die mit demselben Verständnis geschrieben sind, finden diese Bugs nicht.

### Lösung: Jede Zählfunktion bekommt eine zweite, unabhängige Implementierung

```
evaluate_gates(text)                 run_self_verify(text)
├── count_emdashes(text)  [Regex]    ├── _verify_emdash_independent  [str.count]
├── count_boldface(text)  [Index]    ├── _verify_boldface_independent [re.finditer]
└── count_wikilinks(text) [re.find]  └── _verify_wikilink_independent [str.find]
                                             ↓
                                   orig == indep? → OK
                                   orig != indep? → WARN
```

### Wann anwenden?

- Jede Zählfunktion in einem Quality-Gate-Script
- Jede Prüffunktion deren Output boolesch oder numerisch ist
- **NICHT** für reine Transformationsfunktionen (Formatter, Renderer)
- **NICHT** für einfache Delegation (Wrapper ohne eigene Logik)

### Anti-Pattern

- **Identische Implementierung** → findet nichts (trivialer Fehler)
- **Self-Verifier als Test-Ersatz** → nein, Tests + Self-Verifier sind komplementär
- **Self-Verifier in Production** → nein, `--verify-self` ist ein Dev/Debug-Tool

Siehe `references/self-verifier-pattern.md` für vollständige
Implementierungsdetails, 3 Real-World-Beispiele aus daily-addendum-gate.py
(EmDash, Boldface, WikiLink), Exit-Codes, False-Alarm-Heuristik und
Algorithmen-Wahl-Tabelle.

---

## Post-Setup Bug-Hunt (Finalisierung-Phase 5, 2026-06-08)

Nach Abschluss eines Multi-Phasen-Setups ist es NICHT genug, nur die
End-to-End-Tests zu zeigen. Ein zweiter **struktureller Bug-Hunt** deckt
systematisch Probleme auf, die der initiale Test übersieht. Der initiale
"es funktioniert"-Test prüft nur den Happy-Path.

### Wann anwenden?

- Multi-Component-Setup (z.B. Plugin + Config + Crons + Scripts)
- Jeder Setup der > 2 Dateien modifiziert
- Wenn die Komponenten miteinander interagieren (Hooks, Fallbacks, Locks)

### Pattern (5 Schritte)

1. **Sub-Agent Code-Review der geänderten Scripts** (NICHT der Tests!)
   - `delegate_task(goal="Code-Review: find Bugs, Race-Conditions, Error-Handling", toolsets=['terminal', 'file'])`
   - Sub-Agent sieht mehr als manuelles Lesen (frischer Blick, kein Bias)
   - Beispiel 2026-06-08: 7 Findings in 3 Scripts gefunden (S1-S4, B1-B3)

2. **Manuelle Config-Inspektion** — schau YAML-Config nach JEDEM `safe_dump`/`yaml.dump`:
   - `grep -A 8 "^model:" ~/.hermes/config.yaml` — `model.default`/`model.provider` korrekt?
   - **BUG-Pattern:** Manche Tools resetten `model.default` auf Default-Werte.
   - Fix: `hermes config set model.default <X> && hermes config set model.provider ollama`

3. **System-Dependency-Audit** — Cron-Scripts die `sqlite3`, `jq`, `curl` brauchen:
   - `which sqlite3 || apt install sqlite3` (vor Cron-Setup prüfen)

4. **Log-File-Inspektion** der letzten Test-Runs:
   - **BUG-Pattern:** `set -e` killt Script VOR dem Error-Log → Log endet mit "started" ohne "FAILED"
   - Fix: `cd $DIR || { log "ERROR"; exit 1; }` VOR `set -e`-kritischen Operations

5. **Locking/Race-Test** für Cron-Scripts:
   - `flock(1)`-HOLDER (sleep 30) → Script sollte SKIPEN
   - **BUG-Pattern:** `flock(2)` (Python `fcntl.flock`) ist NICHT kompatibel mit `flock(1)` (Tool)

### Hermes-Config-Reset-Bug (KRITISCH, gefunden 2026-06-08)

**Symptom:** Nach `python3 yaml.safe_dump(cfg, ...)` oder anderen Config-
Mutationen (z.B. `mnemosyne-hermes install.py`) kann `model.default` auf
`moonshotai/kimi-k2.6` und `model.provider` auf `nous` zurückspringen.

**Detection:**
```bash

set -euo pipefail
grep -A 8 "^model:" ~/.hermes/config.yaml
```

**Fix:**
```bash

set -euo pipefail
hermes config set model.default "pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes"
hermes config set model.provider ollama
hermes config set model.api_key ollama
```

**NICHT nur `hermes status` trauen!** Der System-Switch-Model (z.B.
minimax-m3 via Nous Portal) kann den eigentlichen Config-Default ÜBERLAGERN.
Immer in den `agent.log` schauen, welcher Provider WIRKLICH für die letzte
Inference genutzt wurde:
```bash

set -euo pipefail
grep -aE "qwen3.5-9b|provider=custom" ~/.hermes/logs/agent.log | tail -3
# Sollte: model=pdurugyan/qwen3.5-9b-... provider=custom base_url=http://127.0.0.1:11434/v1
```

**Wichtigster Learn:** Der initiale "es funktioniert"-Test deckt NICHT
auf, dass die falsche Konfiguration läuft. Immer Bestätigung im **Log
des konkreten Workers** suchen, nicht nur in `hermes status`.

### Kritische Findings aus Mnemosyne-Bug-Hunt (2026-06-08)

| Finding | Severity | Skill-Verweis |
|---|---|---|
| `set -e` + side-effect kills success | HOCH | bash-script-audit #12 |
| `cp` als SQLite-Backup → korrupte DBs | KRITISCH | bash-script-audit #13 |
| Backup-Verifikation nur `[ -f ]` | KRITISCH | bash-script-audit #14 |
| flock-Pattern falsch (fcntl vs tool) | HOCH | bash-script-audit #15 |
| `$?` mit pipefail falsch | MEDIUM | bash-script-audit #16 |
| `cd` ohne Error-Check | MEDIUM | bash-script-audit #17 |
| System-Deps nicht in venv (sqlite3) | HOCH | bash-script-audit #18 |
| Critic-SKIPPED `gate_passed: true` | HOCH | critic-gate v2 |
| Hermes `model.default` Reset-Bug | KRITISCH | ki-murks-verhindern (oben) |

## Wann anwenden?

- Code-Änderungen > 5 Zeilen
- Neue Features / Skripte
- Bugfixes
- Konfigurations-Änderungen mit Seiteneffekten
- Alles was in Production geht

## User-Präferenz (Basti)

> "Wenn ich Videos/Content von Morpheus teile, will ich dass du daraus lernst
> und anwendest — nicht nur zusammenfasst."

Das bedeutet:
- Nicht nur "Hier ist eine Zusammenfassung"
- Sondern: Skill erstellen, Code schreiben, Workflow integrieren
- Direkt anwendbar machen, nicht nur theoretisch beschreiben

## Video-Inhalte verarbeiten

Wenn der User ein Video teilt (lokale Datei oder URL):
1. **Screenshots** an Schlüsselstellen ziehen (ffmpeg)
2. **Audio extrahieren** für Transkript (ffmpeg → mp3)
3. **Vision-Analyse** der Screenshots für Code/Diagramme/Text
4. **Skill erstellen** mit den gelernten Konzepten
5. **Nicht nur zusammenfassen** — extrahiere konkrete Workflow-Regeln, Guardrails und Prompt-Richtwerte, die in Skills oder Doku einfließen

Pitfall: `video_analyze` hat ein 50MB Limit. Videos müssen vorher
segmentiert oder komprimiert werden:
```bash

set -euo pipefail
ffmpeg -i video.webm -c copy -segment_time 300 -f segment seg_%03d.webm
```

## RAG als Grounding-Tool

Die RAG-Pipeline (Skill: `rag-pipeline-python`) ist die technische
Umsetzung der Grounding-Phase:

- **Grounding** → RAG: Suche aktuelle Dokumente/News
- **Execution** → Code schreiben + Tests
- **Evaluation** → Selbst-Review + Quellenverifizierung
- **Finalizing** → Diff zeigen + User bestätigen

Siehe `rag-pipeline-python/references/morpheus-rag-details.md` für
den vollständigen RAG-Workflow aus dem Morpheus-Video.

## Verwandte Skills

- `systematic-debugging` — Für die Evaluation-Phase
- `test-driven-development` — Tests vor Code
- `requesting-code-review` — Pre-commit Review
- `subagent-driven-development` — Multi-Agent Workflow
- `multi-agent-research` — Parallele Evaluation
- `rag-pipeline-python` — Für Grounding/Recherche-Phase

## Pitfalls

- **Evaluation ist kein Optional** — Der Feedback-Loop ist der wichtigste Teil
- **Grounding kostet Zeit, spart aber mehr** — 5 Min lesen spart 30 Min Debuggen
- **"Es kompiliert" ≠ "Es ist richtig"** — Syntax-OK heißt nicht Logik-OK
- **Human-in-the-Loop bei Unsicherheit** — Besser nachfragen als Murks bauen
