# 🅲️ Rolling-Wave Live-Test-Pickup — Spec v1.5.0

**Origin:** 2026-07-13, Hermes-V7 Idempotenz-Key Mission-B (Basti).
**Status:** Pattern 11 ist im TEST/EVALUATION-MODE. Erster echter Live-Test lief 2026-07-13 (Hermes-V7 Mission-B, Phase 3 Welle 1 abgeschlossen). Diese Spec ist die **post-Eval-Version** mit den Lessons aus dem ersten echten Run.

Wenn der nächste **echte Bau-Auftrag** kommt (Code schreiben, Skript bauen, Hermes-Patch, Feature liefern), fährt die Königin **explizit** im 🅲️-Modus. Das heißt: Plan-Biene ernennen, Anforderungs-Liste dokumentieren, Worker gestaffelt, Diff-Bericht am Ende. Danach evaluieren.

---

## 🌳 Decision-Tree: Welcher Modus für diesen Auftrag?

```
Neuer Auftrag kommt rein
        │
        ▼
   Ist Scope klar definiert (Bau-Auftrag: "bau X mit Y")?
        │
   ┌────┴─────┐
   JA          NEIN
   │           │
   ▼           ▼
  Scope       Scope
  ≥ 3 Sub-    vage /
  Tasks?      Suche nach Vision
   │           │
   ┌─┴─┐       └──► 🛠️ Werkstatt-Methodik
   JA  NEIN           (User-Echo Phase 2,
   │   │               Visions-Klärung)
   ▼   ▼              ▼
  🅲️  🅱️         Später wenn Vision klar:
  Rolling  Standard    🅲️-Mode starten
  Wave     (3 Bienen    als Phase 1-4
  (4 Phasen parallel)   mit dem Plan)
  Auto-Plan)
```

**Faustregel:** "Weißt du schon WAS du willst?" → **JA** = 🅲️. **NEIN** = Werkstatt.

**Hybrid erlaubt:** Werkstatt als Phase 0 → 🅲️ als 1-4 wenn Vision klar ist. Die Modi sind kein Dogma.

---

## 📋 Phase 0.5 — Königin-Vor-Scout (ERLAUBTE Königin-Arbeit)

**Bevor 3 Bienen gefeuert werden:** Königin prüft Setup-Zustand. NICHT die Antworten suchen — nur die Existenz der Datenquellen.

**Erlaubte Vor-Scout-Aktionen:**
- `ls / pwd / git status` — Pfad existiert? Branch-Stand?
- `cat package.json | head` — Stack-Version? Test-Scripts?
- `find . -maxdepth 3 -name "*.ts"` — File-Layout?
- `git log --oneline -5` — letzter Commit als Anker?

**NICHT erlaubt im Vor-Scout:**
- Volltexte lesen (`cat` ganzer Files)
- Eigene Interpretationen / Findings
- Vorab-Anforderungs-Liste schreiben

**Output:** Working-Memory-Notiz mit den Fakten (Pfad, Branch, Stack, letzter Commit, Schreibbar-Status). Mehr nicht.

**Pitfall-#17 (NEU v1.4.0):** Ohne Vor-Scout feuert die Königin 3 Bienen die alle "nichts da" reporten. Zeitverlust + Memory-Burn.

---

## 📋 Phase 1 — Scout-Worker (3 Bienen parallel) ⏱️ 5-15 Min

**Was passiert:** 3 Bienen scouten die Realität VOR dem Planen. Jede Biene kriegt einen anderen Scope.

**Briefing-Must-Have für jede Biene:**
- Input-Verzeichnis + relevante Files/Repos/Skills
- Klare Frage (nicht offen — siehe Templates unten)
- Kontext: was an Mnemosyne/session_search zur Mission schon bekannt ist
- Output-Format: Markdown-Liste ≤ 50 Zeilen + 0 Halluzination (Pitfall-#5)
- **`OUTPUT-PFAD` (NEU v1.5.0, Pitfall-#20):** Absoluter Pfad **außerhalb** der read-only-Heimat. Default `/tmp/scout-<mission>-<rolle>.md` oder `~/.hermes/cache/delegation/`. KEIN `git add` oder `.hermes/phase1-*-report.md` ins Repo. Königin verifiziert nach Phase 1 mit `ls <repo>/.hermes/phase1-*` — muss leer sein.

**3 Standard-Scout-Templates:**

| Biene | Frage-Template | Output-Beispiel |
|---|---|---|
| **Domain-Scout** | "Was ist der Stand der Realität zum Thema X? Welche Files/APIs/Constraints existieren, was ist veraltet, was hat sich seit [Datum] verändert?" | Reality-Snapshot, Constraint-Liste, Verweis auf aktuelle Skills |
| **Tech-Inspector** | "Welche Libraries/Build-Tools/Patterns werden in [Repo/Skill/Codebase] für [Aufgabe] genutzt? Was sind die Imports/Dependencies/Code-Style-Konventionen?" | Tech-Stack-Map, Konventionen, Anti-Patterns die zu vermeiden sind |
| **Risk-Auditor** | "Was sind die Risiken/Edge-Cases/Breaking-Changes/Concurrency-Probleme wenn wir X machen? Welche bestehenden Systeme sind betroffen?" | Risk-Register, Betroffene-Systeme, Rollback-Strategie |

**Königin-Job in Phase 1:**
- 3 Bienen per `delegate_task(goal=..., role=leaf, toolsets=[...])` parallel feuern
- Output sammeln in Working-Memory (kein Schreiben ins Repo!)
- Bei Lücken eine 4. Biene nachschicken (z.B. "Risk-Auditor hat Lücke zu X — eine Biene scoutet tiefer")

**Pitfall-#18 (NEU v1.4.0):** Königin scouted selbst statt auf Bienen zu warten = Detektivin-Modus statt Königin-Modus. Königin-Vor-Scout ist Setup, Bienen-Ergebnisse sind Antworten.

---

## 📋 Phase 2 — Plan-Biene (1 Biene, KEIN Parallel) ⏱️ 5-10 Min

**Was passiert:** Plan-Biene destilliert die 3 Scout-Outputs in eine **Anforderungs-Liste A1-A8+ mit Acceptance-Criteria**.

**Briefing-Must-Have für die Plan-Biene:**
- Alle 3 Scout-Outputs als Input
- Formatvorgabe: Strukturiertes Markdown mit Sections
- Constraints: Jede Anforderung braucht (1) ID, (2) Ziel, (3) Acceptance-Criteria, (4) Zugewiesene Lane-Type, (5) Geschätzte Komplexität (XS/S/M/L)
- KEIN Auto-Write — Plan-Biene darf nur **planen, nicht ausführen**

**Plan-Biene-Output-Schema:**
```markdown
# Anforderungs-Liste [Mission-Name]

## Kontext
[1-2 Sätze aus Phase 1]

## Anforderungen

### A1: [Titel]
- **Ziel:** [was soll erreicht werden]
- **Acceptance:** [wie messen wir Erfolg — grüner Test, Output-Datei, manuelles Review-Kriterium]
- **Lane-Type:** [Verify|Research|Memory-Write|Coder]
- **Komplexität:** [XS|S|M|L]
- **Abhängigkeiten:** [A0, A2]

### A2: [Titel]
...

## Reihenfolge (Dependency-Order)
1. A1 (keine deps)
2. A2 + A3 (parallel nach A1)
3. A4 (nach A2+A3)

## Rollback-Strategie
[was tun wenn etwas crasht?]

## Pitfall-Watchlist
- [Pitfall-#5: verify-every-claim — keine Halluzination]
- [Pitfall-X: aus früheren Lessons]

## Diff-Bericht-Format
[welche Felder muss der finale Diff-Bericht haben?]
```

**Königin-Job in Phase 2:**
- Plan-Biene **NICHT parallel** — sie muss die 3 Inputs sequentiell verarbeiten
- Output reviewen, **gegebenenfalls ablehnen/neu** mit Begründung
- Mapping-Tabelle aufbauen: A1-A8 ↔ Lane-Type ↔ Komplexität
- **Plan-Biene ist KEIN Worker** — sie ist eine Denk-Biene, kein Schreib-Biene

---

## 📋 Phase 2.5 — Königin-Lücken-Resolution (NEU v1.5.0, Pitfall-#23) ⏱️ 2-5 Min

**Warum nötig:** Plan-Biene disclosed Lücken ehrlich (Pitfall-#5-Disziplin). Aber Worker-Bienen in Phase 3 können mit Lücken nichts anfangen — sie brauchen resolved Constraints im Briefing. Diese Phase ist die **Brücke zwischen "Plan ist ehrlich" und "Worker können loslegen"**.

**Königin-Workflow (5 Schritte):**

1. **Plan-Biene-Output lesen**, Sektion "Lücken explizit zugegeben" / "Pitfall-Watchlist" / "Offene Fragen" suchen
2. **Jede Lücke via 1-3 fokussierte terminal-Calls schließen** — `find`, `grep`, `cat <file>`, `git show`. **NICHT** dafür eine Worker-Biene dispatchen (das wäre Detektivin-via-Subagent = Königin delegiert ihre eigene Pflicht)
3. **Widersprüche** zwischen Scout-Outputs durch Code-Inspektion auflösen (z.B. "audit-log.ts vs audit-log.js — welche wird aktiv genutzt?")
4. **Plan-Constraints im Working-Memory anreichern** mit den Resolution-Ergebnissen. Format: `RESOLVED: <original-Lücke> → <Antwort> | Quelle: <file:line>`
5. **Erst DANN Phase 3 dispatchen** — die Worker-Briefings müssen die resolved Constraints enthalten, nicht die offenen Lücken

**Output:** Working-Memory-Notiz mit dem Resolution-Block, der vor jedem Phase-3-Briefing als verbindliche Constraint-Liste reinkopiert wird.

**Königin-Vor-Scout-Synergie:** Der Vor-Scout (Phase 0.5) lieferte Fakten zur Setup-Existenz (Branch, Stack, File-Layout). Phase 2.5 liefert die **semantischen Antworten** auf Plan-Lücken (welche von 3 audit-log-Dateien ist aktiv, wo kommt das Feature-Flag hin, welche Coverage-Asymmetrie besteht). Beide zusammen = vollständiges Bild.

**Pitfall-#23 (NEU v1.5.0):** Phase 3 ohne Phase 2.5 = Worker-Bienen arbeiten mit ungelösten Widersprüchen. Sie raten, was die Königin selbst in 2 Minuten via `find`/`grep` lösen könnte. Ergebnis: Worker-Outputs divergieren oder sind halb-falsch.

---

## 📋 Phase 3 — Worker-Welle(n) gestaffelt ⏱️ variable, oft 30-120 Min

**Was passiert:** Eine oder mehrere Wellen von Worker-Bienen arbeiten die Anforderungen sequenziell/parallel ab. Jede Biene kriegt **ihre** Plan-Items + Plan-Context.

**Wave-Regeln:**
- **Default:** 1 Welle mit 3-6 parallelen Bienen (je nach Anforderungs-Anzahl)
- **Bei > 6 Anforderungen:** mehrere Wellen gestaffelt (z.B. Welle 1 = A1-A3, Welle 2 = A4-A6, ...)
- **Zwischen Wellen:** Königin updated Mapping, ggf. Plan-Refinement
- **Pitfall-#5 in jeder Biene:** SELBST-TESTS vor Self-Report mit grep/pytest/output-check

**Briefing-Must-Have pro Worker-Biene:**
- Genau eine Anforderung (oder kleine Gruppe wenn eng verwandt)
- Kontext: relevante Plan-Items + was die Scout-Bienen gefunden haben
- **Phase-2.5-Resolution-Block** (NEU v1.5.0): alle Widersprüche/Lücken aus Plan-Biene-Output, von Königin aufgelöst mit Quelle. Worker darf diese als verbindlich annehmen, nicht selbst nachprüfen
- Output-Format: Code/Diff + Tests + Verifikation der Acceptance-Criteria
- **`OUTPUT-PFAD`** (Pitfall-#20): absoluter Pfad **außerhalb** des Repos für Self-Reports (`/tmp/worker-<mission>-<anforderung>.md`)
- **Strenge Anweisung:** "Wenn Tests rot, fixen + nochmal testen BEVOR du Self-Report schreibst"

**Königin-Job in Phase 3:**
- Bienen per `delegate_task` feuern (MiniMax M3 oder GLM-Worker je nach Sprache/Komplexität)
- **Mapping-Update nach jeder Biene**: was hat sie geliefert, was fehlt, was muss nachjustiert werden?
- Bei Blocker: Plan-Refinement (Anforderung ändern, zusätzliche Biene scouten, Pause)
- Wellen-Break bei Quality-Issues (nicht alles in einer Welle durchpeitschen)

**Pitfall-#19 (NEU v1.4.0):** 🅲️-Patch in fremden Feature-Branch (z.B. `feat/security-kernel`) statt eigenem Branch. Live-Tests nie in aktive Feature-Branches patchen.

---

## 📋 Phase 4 — Diff-Bericht (Königin alleine) ⏱️ 5-15 Min

**Was passiert:** Königin ist **Buchhalterin, nicht Detektivin**. Sie gleicht Plan ↔ Done 1:1 ab.

**Diff-Bericht-Schema:**
```markdown
# 🅲️-Mission [Name] — Diff-Bericht

## Plan ↔ Done Matrix

| Anforderung | Ziel | Acceptance | Status | Evidenz |
|---|---|---|---|---|
| A1 | [Ziel] | [AC] | ✅ DONE / 🟡 PARTIAL / ❌ MISSED | [Pfad/Commit/Test-Output] |
| A2 | [Ziel] | [AC] | ✅ DONE | [Pfad/Commit/Test-Output] |
| A3 | [Ziel] | [AC] | 🟡 PARTIAL | [was fehlt] |

## Summary
- Total: 8 Anforderungen
- ✅ DONE: 6 (75%)
- 🟡 PARTIAL: 1 (12.5%) — [Begründung]
- ❌ MISSED: 1 (12.5%) — [Begründung]
- Halluzinations gefunden: [X / 0]

## Pitfall-#5-Audit
- [Hat Worker [ID] etwas behauptet das nicht stimmt? — Verifikation der Outputs]

## Lessons
- [Was lief gut]
- [Was nicht]
- [Pattern-Anpassungen für nächste 🅲️]

## Artefakte
- [Liste der erstellten/geänderten Files mit Pfad]
```

**Königin-Job in Phase 4:**
- **Kein Nachforschen** — Diff ist was geplant war vs. was geliefert wurde
- Wenn etwas unklar: Vermerk + User-Echo (NICHT selbst detektivisch forschen)
- Diff-Bericht als Markdown in `~/.hermes/docus/reports/` oder als Inbox-Pickup

---

## 🔄 Eval-Loop (direkt nach jeder 🅲️-Mission)

**5-Punkte-Eval (Basti + Yuno, explizit):**

1. **Test durchgeführt?** — JA/NEIN
2. **Was lief gut?** — 2-3 konkrete Punkte mit Evidenz
3. **Was lief nicht?** — 2-3 konkrete Punkte mit Evidenz
4. **Was anpassen?** — Konkrete Skill-Patch-Vorschläge (Pattern 11 v2?)
5. **Fix werden oder zurück zu 🅱️?** — Entscheidung mit Begründung

**Regel:** Erst nach 3 echten 🅲️-Missionen kann das Pattern von "Arbeitshypothese" zu "Default für große Bau-Aufträge" werden.

---

## 🧪 Proven-Mission: Hermes-V7 Idempotenz-Key Patch (2026-07-13)

**Setup:**
- Repo: `/home/bratan/30-Library/hermes-v7/`
- Branch: `feat/security-kernel` (Patch in EIGENEM Branch, nicht hier patchen)
- Stack: Node.js/TypeScript, Jest 70% Coverage-Threshold, ESLint
- Issue-Tracking: GitHub `Toqsick/hermes-v7` (Issue #2 für Idempotenz-Key)

**Vor-Scout-Findings (Königin-Setup):**
- TaskCard Type existiert in `src/core/types.ts` (von Planner importiert)
- `runAtomicToolCall` in `src/runtime/tool-runtime.ts` hat bereits Intent-Hash-Logging
- `SplitBrainResolver` nutzt `toolName:task.id` als Dedup-Key
- `hashInput` in `src/security/audit-log.ts` (Z. 26 + 53) = bestehende Hash-Mechanik
- Idempotenz aktuell: nur Kommentar in `auto-discovery.test.js`, KEIN Code

**Geplanter 🅲️-Scope (4 Anforderungen A1-A4):**
- **A1**: TaskCard-Type um `idempotencyKey?: string` erweitern (in `core/types.ts`)
- **A2**: Pre-Execution-Check in `runAtomicToolCall` für Idempotenz-Key (in `runtime/tool-runtime.ts`)
- **A3**: CI-Gate in `package.json` (test:ci + skills:verify) für 100% Coverage retry-fähiger Tool-Calls
- **A4**: Schema-Test-Coverage ≥ 100% (idempotency_key in allen retry-fähigen Tasks)

**Status:** Phase 1 (3 Scout-Bienen) lief zum Zeitpunkt der Spec-Erstellung. Phase 2-4 folgen.

---

## 🎯 Zwei Kandidaten-Missionen für den nächsten Test

### Mission-A: Greytrix-NetRunner (Real-World Multi-File Bau)

**Status:** Plan existiert seit 2026-07-09 (`~/.hermes/plans/2026-07-09_220000-greytrix-netrunner-operation.md`, 21KB). 3-Phasen-Plan A+B parallel, C nachgelagert.

**Pro:** Echtes Multi-File-Coding mit GCP-VM-Deployment, hat reale Risiken (3rd-party-API), Plan existiert bereits.
**Con:** Komplex (Cloud + mehrere Skripte + Discord-Bot-Setup), könnte zu groß für ersten echten Test sein.

### Mission-B: Hermes-V7 Idempotenz-Key Patch (Inline Small-Bau)

**Status:** P0-Item #1 aus MiroFish-Werkstatt 2026-07-12.

**Pro:** Klein (passt in 1 Welle), selbst-verifizierbar (Schema-Tests sind deterministisch), direkter Code-Impact, P0-Wert.
**Con:** Braucht Zugriff auf `~/30-Library/hermes-v7/` Repo (vorhanden, aber Working-Convention prüfen).

### Empfehlung

**Mission-B zuerst** (Hermes-V7 Idempotenz-Key) — weil:
1. Klein → schneller Eval-Loop
2. Selbst-verifizierbar → Pitfall-#5 sofort sichtbar
3. Echter P0-Bau-Wert → nicht nur Pattern-Validierung
4. Greytrix dann als **zweiter** Test mit höherem Risiko-Profil

---

## 📌 Checkliste: "Ist diese Mission 🅲️-reif?"

Bevor du Phase 0.5 startest, prüfe:

- [ ] Scope ist klar definiert ("bau X mit Y", nicht "könnte man mal...")
- [ ] ≥ 3 eigenständige Sub-Anforderungen
- [ ] Outcome ist messbar (Tests, Files, Akzeptanzkriterien)
- [ ] Pitfall-#5-Risiko akzeptabel (große Worker-Outputs → Diff-Bericht als Buchhalterin)
- [ ] Repo/Codebase ist erreichbar + schreibbar
- [ ] Eigener Branch verfügbar (nicht in laufende Feature-Branches patchen)

**Wenn alle 6 ✅:** 🅲️ Rolling-Wave starten.
**Wenn 1-2 ❌:** Zurück zu 🛠️ Werkstatt oder 🅱️ Standard.

---

## 🔗 Verwandte Skills + Files

- **Haupt-Skill:** `multi-agent-cluster-patterns` (Pattern 11 + 🅰️🅱️🅲️ Selection Guide + 🅲️ vs Werkstatt Abgrenzung)
- **Bruder-Skills:**
  - `workflow-template` — Werkstatt-Methodik (Phase 0 der 🅲️-Pipeline)
  - `orchestration/multi-agent-pitfalls-cheatsheet` — TRIGGER-WATCHLIST (load BEFORE every delegate_task)
  - `obsidian-subagent-briefing-template` — Pattern 5 als ausfüllbares Template
- **Memory-Anker:** Mnemosyne-Items `[dispatch-pattern]` (id=abaa5f6309f05697) und `[evaluation-mode]` (id=8df2aa3bb2c52b7e)

---

---

## 🆕 v1.5.1 — Live-Test-Findings (Hermes-V7 Mission-B 2026-07-13)

**Spec-Version:** v1.5.1 (post-Mission-B Eval)
**Last-Updated:** 2026-07-13 (nach Hermes-V7 Idempotenz-Key 6-Wellen-Mission)
**Maintainer:** Yuno (Königin) — review nach jeder 🅲️-Mission

### Pitfall-#22 (NEU v1.5.1): Worker-Biene Self-Commit fehlt

**Symptom:** Welle 2 (A3+A4) der Hermes-V7-Mission: Worker-Bienen haben gearbeitet, tsc grün, Tests grün, ABER kein `git add`/`git commit`/`git push` am Ende. Working tree war dirty als sie zurückkamen. Königin musste manuell committen + pushen (Commit `2920e93`).

**Root-Cause:** Briefing hatte Self-Commit-Pflicht nicht explizit. Biene denkt "ich bin fertig, mein Job ist getan" → fühlt sich nicht zuständig für Commit.

**Fix (in v1.5.1 angewendet):**
- Jedes Worker-Briefing MUSS am Ende enthalten: "AM ENDE — PFLICHT: git add + git commit + git push origin <branch>. Im Self-Report: EXAKTE Commit-SHA."
- Welle 3+ (A5, A6) der Hermes-V7-Mission haben es befolgt → 2 von 2 mit Self-Commit ✅

**Verifikation:** Welle 3 (A5) Self-Commit c4f092f, Welle 4 (A6) Self-Commit 9764f67. Welle 2 (A3+A4) brauchte Königin-Commit 2920e93.

### Pitfall-#24 (NEU v1.5.1): A3 Concurrent-Hierarchie ist implizit statt hart kodiert

**Symptom:** Plan-Biene forderte "Hart kodieren: idempotencyKey > dedup_windowed > skip_if_running". A3 hat's **dokumentiert** aber nicht durch Override-Code für `dedup_windowed` durchgesetzt.

**Root-Cause:** Worker-Biene interpretiert "Hierarchie" als Reihenfolge der Checks, nicht als explizite Override-Logik.

**Fix (in v1.5.1 angewendet):**
- Plan-Biene-Output MUSS für Hierarchie-Anforderungen explizit "Override-Code in Modul X" spezifizieren
- Worker-Briefing muss Hierarchie-Anforderung mit "HART KODIEREN" markieren (Caps = Pflicht)
- Königin verifiziert im Diff-Bericht dass explizite Override-Logik existiert

**Verifikation:** Hermes-V7-Mission A3 hat Reihenfolge korrekt (idempotencyKey vor dedup_windowed), aber kein expliziter Override-Code. Status: 🟡 PARTIAL — funktional OK, code-review riskant.

### Pitfall-#25 (NEU v1.5.1): Coverage-Ausschluss maskiert Tech-Debt

**Symptom:** A6 der Hermes-V7-Mission hat 5 Module aus `collectCoverageFrom` ausgeschlossen (`src/depp/**`, `src/dashboard/**`, `src/queue/**`, `src/storage/split-brain-resolver.ts`, `src/storage/artifact-store.ts`), damit 70% Coverage-Threshold grün wird.

**Root-Cause:** Coverage-Schwelle ist global, aber Code-Bestand ist gewachsen. Ausschluss ist schnellster Weg zu grünem CI.

**Risk:** Aktivierung eines ausgeschlossenen Moduls später bricht Threshold ohne Warnung. Tech-Debt wird unsichtbar.

**Fix (in v1.5.1 angewendet):**
- Coverage-Ausschluss MUSS mit Kommentar versehen sein: `// excluded per ROADMAP.md#X — needs test before activation`
- README/CHANGELOG muss Ausschluss dokumentieren
- Issue-Tracker-Eintrag für jedes ausgeschlossene Modul Pflicht
- Königin-Check: ist Coverage-Ausschluss im Briefing als "modul-lokale Lösung" markiert? Wenn nein → Pitfall

**Verifikation:** Hermes-V7-Mission A6: Module sind alle in ROADMAP.md als "🔲 Geplant" markiert → Ausschluss **legitim**. Aber: Issue-Tracker-Eintrag fehlt im Diff-Bericht.

### Pitfall-#26 (NEU v1.5.1): Plan ↔ Done Mapping braucht Königin-Audit

**Symptom:** Im Hermes-V7-Diff-Bericht war Pitfall-#23 (Coverage-Ausschluss) ein Königin-Fund, nicht ein Plan-Biene-Output.

**Root-Cause:** Plan-Biene plant auf Wunschbarkeiten, Königin verifiziert auf Realität. Live-Findings entstehen erst bei Implementierung.

**Fix (in v1.5.1 angewendet):**
- Diff-Bericht MUSS Section "Königin-Pitfall-Funde (NEU, während Mission aufgetreten)" haben
- Jeder Fund mit Pitfall-#X-Name + Symptom + Königin-Verifikation + Skill-Update-Konsequenz
- Diese Funde werden zur Skill-Patch-Input für die nächste Mission

**Verifikation:** Hermes-V7-Diff-Bericht hat Pitfall-#22, #24, #25 dokumentiert → Skill-Update v1.5.1 abgeleitet.

---

## 🧪 Proven-Mission: Hermes-V7 Idempotenz-Key Patch — ABGESCHLOSSEN (2026-07-13)

**Resultate:**
- 4 Commits: 110f7a9 (A1+A2) → 2920e93 (A3+A4 Königin-Commit wegen Self-Commit-Pitfall) → c4f092f (A5) → 9764f67 (A6)
- 14 files changed, +1439/-10
- 6 Anforderungen A1-A6 (geplant) vs. 5 ✅ DONE + 1 🟡 PARTIAL (A3 Hierarchie-Implizitheit)
- tsc --noEmit exit 0; Jest 21 suites / 181 tests passed
- Coverage 76.44% stmts / 78.8% lines / 76.06% funcs / 70.74% branches — alle 70%-Thresholds ✅
- Pitfall-#5-Audit: 0 Widersprüche zwischen Bienen-Reports und Live-State
- 3 neue Königin-Pitfall-Funde (→ #22, #24, #25 in v1.5.1)

**Eval-Entscheidung (Basti 2026-07-13):** **EVAL-OK** — 🅲️ bleibt "stabil aber mehr Daten nötig" nach 1 Mission. Spec-Regel "erst nach 3 echten 🅲️-Missionen" wird respektiert. Greytrix-Mission als #2 ist der nächste Validierungs-Test.

---

## 📋 Nächste Schritte nach Eval-OK

1. **Skill v1.5.1 ist produktiv** für die nächste Mission — kein weiterer Patch nötig
2. **Greytrix-Mission als 🅲️-Test #2** vorbereiten (echtes Real-World Multi-File mit GCP-VM)
3. **Nach 2 weiteren Missionen** → v1.5.2 (Pattern 11 wird Default für große Bau-Aufträge)
4. **Issue #2 posten** im GitHub `Toqsick/hermes-v7` Repo (Vorlage in /tmp/issue-2-hermes-v7-idempotency-key.md)