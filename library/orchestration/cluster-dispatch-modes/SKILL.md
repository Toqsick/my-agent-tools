---
name: cluster-dispatch-modes
title: "Cluster Dispatch Modes + 8 Core Patterns"
description: "Use when choosing dispatch mode (parallel/sequential/hybrid) or implementing core cluster patterns: read-patch-retry, additive-patches, anti-halluzination-tripwire, themen-MOC-hierarchy, subagent-spec, backlink-audit, verwaiste-notes, cluster-phase-reporting. NOT for queen-side patterns (use cluster-queen-patterns)."
category: orchestration
version: '1.0'
created: '2026-07-23'
author: Yuno (split from multi-agent-cluster-patterns)
lane: koenigin
agent: universal
trigger_keywords: ['dispatch', 'parallel', 'sequential', 'hybrid', 'pattern', 'read-patch', 'additive', 'halluzination', 'moc', 'backlink', 'verwaist']
keywords: ['dispatch', 'mode', 'pattern', 'cluster', 'parallel', 'sequential', 'multi-agent']
related_skills: ['cluster-queen-patterns']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from multi-agent-cluster-patterns 2026-07-23)'

license: MIT
---

# Cluster Dispatch Modes + 8 Core Patterns

_Extracted from multi-agent-cluster-patterns on 2026-07-23._

## Proven-Mission Status (v1.5.2, 2026-07-13)

**🅲️ Rolling-Wave ist live-validiert.** Erste echte Mission (Hermes-V7 Idempotenz-Key Patch, 2026-07-13) lief mit 4 Commits auf `feat/idempotency-key-patch` (HEAD `136336b`), 14 files, +1501/-10, 181 Tests grün, 5/6 Anforderungen DONE, 1 🟡 PARTIAL (A3 Hierarchie-Implizitheit), EVAL-OK-Status. Drei GitHub-Issues (#12, #13, #14) auf `Toqsick/hermes-v7` offen, PR-Body im Branch. **Nächster Test:** Greytrix-Mission als 🅲️-Test #2. Nach 3 echten Missionen wird Pattern von "Arbeitshypothese" zu "Default für große Bau-Aufträge" (Spec-Regel).

**Pitfall-#5-Disziplin bewährt:** Alle 3 Scout-Bienen und die Plan-Biene haben Lücken ehrlich zugegeben (audit-log-Pfad unklar, Feature-Flag-Ort unklar, etc.). Königin hat sie in Phase 2.5 vor Phase 3 geschlossen. **Lesson:** Pitfall-#5 zahlt sich aus — Plan-Biene-Unknowns früh admitted = Worker-Bienen arbeiten mit resolved Constraints statt zu raten.

**Wichtigste Live-Findings in v1.5.2 dokumentiert:**
- Pitfall-#22 (Welle-2-Self-Commit-Fail) → Briefing-Update hat Welle 3+4 gerettet
- Pitfall-#24 (Plan-Biene "Hart kodieren" → Worker interpretiert als Reihenfolge) → Issue #14 als Follow-up
- Pitfall-#25 (Coverage-Ausschluss maskiert Tech-Debt) → Issue #13 als Follow-up
- Pitfall-#26 (Königin-Audit findet Live-Pitfalls) → Diff-Bericht-Section "Königin-Pitfall-Funde" als Pflicht
- **NEU v1.5.2: Königin-Fallback-Commit-Pattern** (siehe unten) — wenn Worker-Biene nicht selbst committed, hat Königin einen reproduzierbaren 3-Schritt-Workflow

## Trigger Conditions

Use this skill when:
- Eine **Cluster-Phase** mit 2+ Subagents geplant wird (Vault, Code, Configs, Docs)
- Pattern-Wissen aus realen Erfahrungen anwendbar gemacht werden soll
- Cluster-Reporting (Phase-Abschluss) benötigt wird
- Anti-Patterns aus Multi-Agent-Setups diskutiert werden

**Cluster-Beispiele, die das abdeckt:**
- Obsidian-Vault-Erweiterung (Kern-Anwendungsfall)
- Code-Refactoring über Multi-Repo
- Migrations-Run (mehrere Services gleichzeitig)
- Doc-Generation aus mehreren Codebases

Nicht für: Single-Agent-Operationen → keine Cluster-Patterns nötig.

## Pattern-Übersicht (13 Patterns)

| # | Pattern | Zweck | Domain | Vor | Während | Nach |
|---|---|---|---|---|---|---|
| 1 | Read→Patch-Retry | Konflikt-Recovery | ✅ alle | ✓ | ✓ | |
| 2 | Additive Patches + Verify | Cluster-Disziplin + Verify-Biene | ✅ alle | ✓ | ✓ | |
| 3 | Anti-Halluzinations-Tripwire | Datenintegrität | ✅ alle | ✓ | ✓ | ✓ |
| 4 | Themen-MOC Hierarchie | Struktur-Design | Vault/Docs | ✓ | | |
| 5 | Subagent-Spec-Disziplin | Briefing-Qualität | ✅ alle | ✓ | | |
| 6 | Backlink-Roundtrip-Audit | Verlinkungs-Health | Vault/Docs | | | ✓ |
| 7 | Verwaiste-Notes-Detection | Isolation-Health | Vault/Docs | | | ✓ |
| 8 | Cluster-Phase-Reporting | Abschluss-Reporting | ✅ alle | | | ✓ |
| 9 | Subagent-Improvisation-Permission | Spec-Abweichungs-Erlaubnis | ✅ alle | ✓ | ✓ | ✓ |
| 10 | MERGER Worker (Konsolidierungs-Biene) | Königin dispatched N parallel Bienen → MERGER fasst zusammen | ✅ alle | | | ✓ |
| 11 | Rolling-Wave mit Plan-Biene (Anforderungs-Tracking-Diff) | Große Tasks: 3-Worker+Verify parallel → Plan-Biene schreibt Anforderungs-Liste → Worker gestaffelt → Diff-Report | ✅ alle | ✓ | ✓ | ✓ |
| 12 | Sub-Sub-Dispatch (verifizierbare 2-Level-Delegation) | Eltern-Biene spawns Sub-Sub-Biene mit Side-Effect-File als Beweis — role='orchestrator', max_spawn_depth>=2 | ✅ delegierbare Tasks | ✓ | ✓ | ✓ |
| **13** | **Analytical-Dimension Fan-Out** (Daten-Analyse-Pattern) | **N Subagents kriegen DENSELBEN Input, aber JEDE eine ANDERE analytische Frage — für Logs/Dumps/Captures wo File-Chunking nicht geht** | **✅ Daten (Logs, Dumps, Captures)** | ✓ | ✓ | ✓ |
---

## 🅰️🅱️🅲️ Dispatch-Mode Selection Guide\n\n**Wähle den Modus basierend auf Task-Größe, nicht auf Domain.** Diese 3 Modi sind die Taktik-Ebene über den 12 Patterns:

| Modus | Wann | Bienen | Königin-Rolle | Verwendete Patterns |
|---|---|---|---|---|
| **🅰️ Mini-Fix** | 1-2 kleine Tasks, klarer Scope, kein Gesamt-Report nötig | 1-2 parallel, kurz | Quick-Ack, keine Plan-Phase | 1 (Read→Patch), 3 (Anti-Halluz.) |
| **🅱️ Standard** | 3-5 verwandte Sub-Aufgaben, mittlere Komplexität, klare Deliverables | **3 Worker + 1 Verify-Biene** parallel (2x3-Wave ist Legacy: 1 Welle = 3 Worker + 1 Verify) | Quick-Fixes zwischen Wellen, kein Gesamt-Plan nötig | 2 (Fan-Out), 5 (Briefing), **6 (Verify-Biene)**, 8 (Reporting) |
| **🅲️ Rolling-Wave** | 5+ Sub-Anforderungen ODER Schluss-Bericht-Qualität kritisch ODER nachträgliches Forschen vermeiden | Phase 1: 3 Worker + 1 Verify parallel → Phase 2: 1 Plan-Biene → Phase 3: Worker gestaffelt | Buchhalterin, nicht Detektivin: tracked 1:1-Mapping Plan ↔ Done | 11 (vollständig, siehe Pattern 11) |

### Entscheidungs-Regeln

1. **Zähle die Anforderungen.** Gehe den Task durch und zähle eigenständige Sub-Anforderungen (nicht Arbeitsschritte)
2. **≤ 2** → **🅰️** Mini-Fix. Quick inline, keine Plan-Phase, keine Verify-Biene. Wenn trotzdem Schluss-Bericht gewünscht → Pattern 8.
3. **3–5** → **🅱️ Standard. 3 Worker parallel + 1 Verify-Biene gleichzeitig dispatched. Königin macht Quick-Fixes während Bienen laufen. **Verify-Biene ist PFLICHT** (Pattern 6), nicht optional.
4. **5+ ODER "nachher forschen" ist aufwändig** → **🅲️** Rolling-Wave (Pattern 11). Plan-Biene schreibt Anforderungs-Liste, Worker gestaffelt, Bericht = Diff.
5. **Wenn unsicher → 🅱️ Standard.** Einfach skalieren: bei zu vielen Findings in Verify in 🅲️ wechseln (keine Scham).
6. **Hybrid erlaubt:** 🅲️ Plan-Phase → 🅱️ Worker-Phase → 🅲️ Reporting. Die Modi sind kein Dogma.

### Anti-Patterns Dispatch-Selection
- ❌ Alle Tasks automatisch mit 🅲️ starten (Overkill für 2 Sub-Aufgaben, killed Momentum)
- ❌ Verify-Biene bei 🅱️ vergessen (führt zu fehlerhaften Outputs, Retouren in Phase C)
- ❌ 🅲️ Phase 3 doch parallel machen (Lock-Conflicts, Plan-Mapping wird undicht)
- ❌ Aus "sicherheitshalber" 6 parallel statt 3+Verify (Context-Overflow, Token-Waste)

### 🅲️ vs. Werkstatt-Methodik — die Meta-Abgrenzung (NEU v1.4.0)

**Verwechslungs-Gefahr:** Beide Pattern haben 4 Phasen, parallele Bienen vorne, sequentielle Phasen hinten, priorisieren zum Schluss. **Aber sie lösen fundamental verschiedene Probleme.**

| Aspekt | 🛠️ Werkstatt-Methodik | 🅲️ Rolling-Wave |
|---|---|---|
| **Antwortet auf** | "Was IST vs. was SOLL — und was fehlt?" | "Bau/liefere X mit definierten Acceptance-Criteria" |
| **Trigger** | Audits, Inventuren, Refactor-Planung, Vault-Cleanup, RAM/Cron/Skill-Diagnose | Echte Build-Missionen: Code-Patches, Skripte, Hermes-Features, Content |
| **Output-Typ** | Inventur-Report + priorisierte Edits (oft read-only) | Konkrete Artefakte (Code, Content, Skripte) |
| **Mensch-Rolle** | **AKTIV in Phase 2** (User-Echo, Visions-Klärung) | **PASSIV** — läuft autonom durch |
| **Phase-1-Output** | **IST-Snapshot** (was ist da?) | **Scout-Findings** (was muss ich wissen bevor ich baue?) |
| **Phase-2-Charakter** | Dialogisch — Königin fragt, User antwortet, Vision wird klar | Auto-Plan — Plan-Biene generiert Anforderungs-Liste A1-A8 |
| **Edit-Charakter** | Klein, sicher, oft dokumentarisch | Größere Worker-Outputs, gestaffelt, riskanter |
| **Diff-Bericht** | Optional (Audit-Trail via Daily+Reports) | **PFLICHT** — Buchhalterin statt Detektivin |
| **Pitfall-#5-Risiko** | Niedrig (Edits klein und dokumentiert) | Hoch (große Worker-Outputs ohne strikte Verification) |
| **Stop-Punkt** | Nach Audit/Refactor — Abschluss | Nach Liefergegenstand — Delivery |

**Phase-für-Phase-Vergleich:**

```
Phase 1          Phase 2              Phase 3              Phase 4
─────────        ──────────           ──────────           ──────────
Werkstatt:  3× Biene ─────────►  USER-ECHO  ─────────►  Priorisierte  ─────────►  P0 Edits
             Inventur            "Was willst           Edits (klein,    sequentiell
             parallel            du wirklich?"         dokumentiert)    mit Audit-Trail
                                 
                                 ↕ MUSS                 ↕ Oft reine
                                   klären               Doku-Edits

Rolling-Wave: 3× Biene ─────────►  PLAN-BIENE  ─────────►  Welle(n) von  ─────────►  DIFF-BERICHT
              Scout parallel       generiert A1-A8        Worker-Bienen    Plan ↔ Done 1:1
              (Reality-Check)      + Acceptance-Criteria   gestaffelt       Buchhalterin-Modus
              ↕ Auto                  ↕ Größere
                                  ↕ generiert             ↕ Code/Content
```

**Drei Insight-Knoten der Abgrenzung:**

1. **Phase 2 ist der ECHTE Bruch:** Werkstatt = Human-in-the-Loop VISION-Klärung (User + Königin ringen um "was soll werden"). 🅲️ = Auto-Plan-Generierung (Plan-Biene schlägt A1-A8 vor, Königin reviewt/genehmigt).
2. **User-Eingriff definiert das Pattern:** 🅰️ wartet nie. 🅱️ Quick-Fixes ZWISCHEN Wellen = Mikro-Eingriffe. Werkstatt = Phase-2-Blocker — User MUSS Stellung nehmen. 🅲️ Phase 2 ist auto.
3. **Risk-Profile sind gegensätzlich:** Werkstatt kann nicht scheitern weil Edits klein sind. 🅲️ KANN scheitern an Pitfall-#5 (große Worker-Outputs ohne Verification) — deswegen Diff-Bericht als Buchhalterin.

**Faustregel für die Wahl:**

> **"Weißt du schon WAS du willst?"**
> - **Ja, klar definiert** → 🅲️ Rolling-Wave (4 Phasen, auto-Plan)
> - **Nein, vage, Suche nach Vision** → 🛠️ Werkstatt-Methodik (4 Phasen, User-Echo)
> - **Mix**: Werkstatt als Phase 0 → 🅲️ als 1-4 wenn Vision klar ist

**Synthese-These:** Werkstatt-Methodik IST 🅲️-Phase-0 in Kleinkram-Szenarien. Die Meta-Frage "Werkstatt vs 🅲️" ist also nicht "entweder/oder" sondern "in welcher Reihenfolge?"

**Origin der Abgrenzung:** 2026-07-13 Hermes-V7 Idempotenz-Key Mission (Basti stellte Meta-Frage "was ist eigentlich der Unterschied zwischen Werkstatt-Methodik und 🅲️ Rolling-Wave?").

### 🅲️ Live-Test-Pickup-Spec (NEU v1.4.0)

Wenn der nächste **echte Bau-Auftrag** kommt, explizit im 🅲️-Modus fahren. Decision-Tree + 4-Phasen-Checklisten + Eval-Loop. **Vollständige Spec in `references/rolling-wave-live-test-pickup.md`** — diese Spec gehört in jede Phase-0-Diskussion "wie starten wir den nächsten Bau-Auftrag".

**Kurzfassung Decision-Tree:**
```
Neuer Auftrag → Scope klar definiert (Bau-Auftrag)?
  ├─ NEIN (vage/Vision-Suche) → 🛠️ Werkstatt
  └─ JA → Scope ≥ 3 Sub-Tasks?
        ├─ NEIN → 🅱️ Standard
        └─ JA → 🅲️ Rolling-Wave
```

**Kurzfassung 4 Phasen:**
1. **Scout-Worker** (3 Bienen parallel: Domain-Scout, Tech-Inspector, Risk-Auditor)
2. **Plan-Biene** (1, sequentiell: destilliert A1-A8+ mit Acceptance-Criteria)
3. **Worker-Welle(n)** (gestaffelt: jede Biene kriegt ihre Plan-Items + Plan-Context)
4. **Diff-Bericht** (Königin als Buchhalterin, NICHT Detektivin — null Nachforschung)

**Vollständige Spec in:** `references/rolling-wave-live-test-pickup.md` (Briefing-Templates, Plan-Output-Schema, Worker-Briefing-Must-Haves, Diff-Bericht-Schema, 5-Punkte-Eval-Loop).

### Herkunft
Dieser Guide entstand 2026-07-09 23:23 Berlin aus Basti's Feedback nach Greytrix-Phase-A. Der User wollte eine klare Trennung: Mini-Fix (🅰️) für schnelle 1-2er, Standard (🅱️) mit 3+Verify als Default, Rolling-Wave (🅲️) für die großen Brocken mit Plan-Biene (siehe Pattern 11). Kern-Insight: "weniger im Nachhinein forschen" = Plan ist Source-of-Truth, Bericht ist Diff.

---

## Pattern 1: Read→Patch-Retry bei Sibling-Konflikten

**Symptom 1 — Patch failed:** `patch`-Tool meldet "file modified since you last read" — typisch wenn mehrere Subagents (oder async-write-Prozesse) dieselbe Datei anfassen.

**Symptom 2 — Patch succeeded WITH `_warning`:** Der Patch liefert `success: true` zurück, aber enthält ein `_warning`-Feld wie `file was modified by sibling subagent 'sa-...'`. Dies ist der **häufigere Fall** (2/7 Files in Phase D2, 2026-07-05). Der Patch landete gegen eine veraltete Version — dein Edit ist strukturell drin, aber der Sibling-Edit könnte orphant, dupliziert oder überschrieben sein.

**Beide Symptome erfordern Nachverifikation.** Im Symptom-1-Fall: re-read + retry. Im Symptom-2-Fall: re-read + verify (Section-Header-Check, Line-Count, Frontmatter-Duplikate). Siehe `vault-architecture` → `_warning` field für die Case-Table.

**Lösung (Python-Pseudo):**
```python
result = patch(path, old, new)
if result.warning:
    # Sibling conflict — verify even if patch succeeded
    content = read_file(path)
    assert content.count("---") == 2, "Frontmatter duplicated!"
    # Check section headers haven't been merged/removed
```

**Wann 2 Retries nötig:** wenn parallel writes während des retry-Intervalls durchkommen.

**Verifikation:** Patch erfolgreich UND keine andere Stelle zerstört → vor Final-Report ganzes File nochmal lesen.

**Generalisiert:** Alle Write-Tools (File-API, Datenbank-Update, Git-Push) können das brauchen.

## Pattern 2: Additive Patches als Cluster-Disziplin

Wenn N Subagents parallel dieselbe Datei patchen — z. B. eine zentrale Index-Datei (MOC, registry.json, README), die mehrere Sektionen hat:

**Regel:** Jeder Subagent patcht eine **disjunkte Sektion**. Reihenfolge egal, weil Patches kontextuell unabhängig sind.

**Anti-Pattern:** Alle Subagents patchen dieselbe Index-Sektion → "letzter gewinnt"-Race-Condition, vorherige Edits verschwinden.

**Best Practice:** Königin definiert vor Cluster-Start eine **Cluster-Section-Map**, in der pro Subagent seine erlaubten Sektionen stehen.

**Generalisiert:** Funktioniert für MOCs, README, registry.json, navigation.md, INDEX.md, etc.

**Konkrete Variante: Append-at-End (Siehe-auch-Addendum)**

Wenn zwei Subagents unterschiedliche Sektionen in derselben Datei patchen sollen (z. B. einer füllt den Body, einer fügt Cross-Links hinzu), ist die **sicherste additive Strategie**: füge eine neue Sektion am **Ende** der Datei an, statt inline zu patchen.

```python
# Additive: append new section at end (sicher)
patch(path, old="<letzte existierende Zeile>", new="<letzte Zeile>\n\n## Siehe auch\n\n- [[Link1]]\n- [[Link2]]")
```

**Warum das funktioniert:** Ein Patch am Dateiende hat nur ein einziges Anchor-Paar (die letzte Zeile). Selbst wenn ein Sibling den Body mittendrin umstrukturiert, bleibt die letzte Zeile stabil. Der `patch`-Tool-Warning wird zwar trotzdem gefeuert (Sibling hat Datei modifiziert), aber der Patch ist strukturell safe, weil disjunkt.

**Proven 2026-07-05:** 7 Dateien mit Append-at-End-Patches, 2 mit Sibling-Warnings, 0 Korruptionen.

**Anti-Pattern:** Alle Subagents patchen inline in dieselbe Sektion → "letzter gewinnt" und Sibling-Edits gehen verloren.

## Pattern 3: Anti-Halluzinations-Tripwire

**Problem:** Subagent soll Inhalte aus Datenquellen einfüllen, hat aber keinen Read-Zugriff.

**Lösung: Explizite Fallback-Regel im Briefing:**
> Wenn Datenquelle nicht lesbar → schreibe "Status: ungeprüft (Quelle nicht zugreifbar am <Datum>)" und lasse Felder leer oder TODO.

**Anti-Pattern:** Subagent erfindet plausible Tech-Details (Dependencies, Befehls-Flags, Versionsnummern).

**Best Practice:**
- Königin gewährt **Read-Zugriff** auf Quelldaten wenn möglich
- Königin definiert **explizite Fallback-Regel** im Briefing
- Königin prüft im Post-Cluster-Report auf "ungeprüft"-Markierungen

**Generalisiert:** Gilt für ALLE Cluster mit Foreign-Source-Reads.

## Pattern 4: Themen-MOC Hierarchie (3-stufig)

```
L1: Root-Hub (einzige Entry-Point)
       ↓
L2: Themen-Hubs (~3–5)
       ↓
L3: Folder- oder Domain-spezifische MOCs (~8)
```

**Vorteile:**
- Wiki-Links arbeiten auf 3 Ebenen
- Dataview-Queries können auf jeder Ebene filtern
- Klare mentale Karte beim Dispensieren neuer Subagent-Clusters

**Anti-Pattern:** Alle Notes hängen direkt am Root-Hub → wird unleserlich.

**Generalisiert:** Funktioniert überall, wo hierarchische Aggregation nötig ist (Doc-Hierarchie, Folder-Strukturen, Modul-Registry).

## Pattern 5: Subagent-Spec-Disziplin

Jeder Subagent-Briefing MUSS diese 6 Sektionen haben:

1. **File-Scope** — exakt welche Files lesen/schreiben (KEINE Überschneidung)
2. **Anti-Pattern** — was NICHT tun
3. **Output-Format** — was am Ende reportet wird
4. **Anti-Halluzinations-Regel** (Pattern 3)
5. **Patch-Konflikt-Hinweis** (Pattern 1+2)
6. **Wiki-Link-/Reference-Syntax** — formatspezifisch (z. B. Dataview-Encoding)

**Spec-Größe:** 800–1500 Wörter pro Briefing.

**Anti-Pattern:** "Mach mal den Bereich besser." → Subagent tut, was er will.

**Best Practice:** Spec ist Template-getrieben (siehe `obsidian-subagent-briefing-template` Skill).

**Generalisiert:** Funktioniert für Code-Refactoring-Briefings, Migrations-Briefings, Doc-Generation-Briefings.

## Pattern 6: Backlink-Roundtrip-Audit

**Definition:** Prüfe, ob neue Nodes aus existierenden Nodes rückverlinkt sind.

**Methode (Dataview-Beispiel):**
```dataview
LIST FROM "<scoped-area>"
WHERE contains(this.file.outlinks, this.file.name)
```

**Wenn 0 Backlinks pro Note:** Sackgassen-Detection → Link-Spread nötig.

**Generalisiert:**
- Für Code: Import-Graph-Analyse
- Für Docs: Reference-Check (welche Docs verweisen auf welche)
- Für Vaults: Wikilink-Density-Check

## Pattern 7: Verwaiste-Notes-Detection

**Definition:** Note/Node mit 0 In-Links UND 0 Out-Links = komplett isoliert.

**Methode (Dataview):**
```dataview
LIST FROM ""
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
SORT file.mtime DESC
```

**Empfohlene Aktionen:**
- Verschieben, löschen, anreichern oder als Template markieren

**Best Practice:** Nach jedem Cluster Verwaiste-Liste prüfen und auflösen.

**Generalisiert:**
- Für Code: Unreferenced-Modules-Detection
- Für Docs: Orphan-Page-Check
- Für Vaults: Verwaiste-Notes (siehe `obsidian-vault-quality-audit`)

## Pattern 8: Cluster-Phase-Reporting

**Nach Cluster-Abschluss (alle N Subagents fertig):**

1. **Inventur** — Notes/Items erstellt, Links gesetzt, Avg-Links/Item
2. **Per-Cluster-Stats** — welcher Subagent was gemacht hat
3. **Konflikte dokumentiert** — welche Files, wie gelöst
4. **Lessons extrahiert** — was hat funktioniert, was nicht
5. **Telegram-Bericht** vorbereitet für Basti (falls Reporting erwünscht)

**Pattern:** "5-Punkte-Report" als Default. Königin füllt ihn IMMER aus — auch wenn Cluster klein ist.

**Generalisiert:** Funktioniert für jeden Cluster-Phase-Abschluss.

---

### Pattern 9: Subagent-Improvisation-Permission

**Problem:** Das Briefing sagt "erstelle 2 neue Items" — aber der Subagent erkennt, dass das zu Duplikation führt, weil die Inhalte besser in ein bestehendes Item passen.

**Lösung:** Subagent DARF von der Spec abweichen, wenn die Abweichung strukturell BESSER ist als die Anweisung.

**Drei Bedingungen (alle MÜSSEN erfüllt sein):**
1. **Keine existierenden Daten werden zerstört** — bestehende Inhalte bleiben erhalten oder werden angereichert, nie gelöscht
2. **Task-Abdeckung wird nicht reduziert** — alle Informationen, die in den geplanten neuen Items stehen sollten, landen trotzdem im Ziel (nur in einer anderen Datei/an einem anderen Ort)
3. **Abweichung wird im Summary dokumentiert** — der Final-Report sagt explizit: "Spec sagte X, aber ich habe Y gemacht, weil Z"

**Konkretes Beispiel (Vault-Phase-4, 2026-07-05):**
- **Spec:** Erstelle 2 neue Vault-Notes
- **Bessere Wahl:** Bestehende Note (2,8 KB) mit Install-Anleitungen + Live-Status anreichern (→ 7,6 KB)
- **Warum besser:** Keine Fragmentierung des Wissens auf 3 Notes, weniger "Siehe auch"-Verweise, Nutzer findet alles an einem Ort
- **Siehe auch:** `obsidian-vault-cluster-operations` → `references/subagent-improvisation-pattern.md` für vollständige Worked-Examples

**Signal für Improvisation:** Wenn der Subagent im "Read"-Schritt merkt, dass ein bestehendes Item perfekt den Ziel-Content aufnehmen kann, OHNE die existierende Struktur zu zerstören.

**Generalisiert:** Der Subagent darf immer vom Buchstaben der Spec abweichen, wenn der Geist erhalten bleibt. Die drei Bedingungen gelten für CODE (extend module statt neues File), CONFIG (merge into existing statt neues Config-File), DOCS (extend existing doc), und VAULT (extend existing note).

---

### Pattern 10: MERGER Worker (Konsolidierungs-Biene)

**Problem:** Die Königin hat N parallele Worker-Bienen dispatched (z.B. Inhalt, Stil, Faktencheck) und braucht jetzt EINE Biene, die alle Outputs zu EINEM polierten Artefakt zusammenführt. Ohne klare Merger-Methodik entstehen 3 Klassen von Fehlern:

1. **Briefing-Claims blind angewendet** — die Königin schreibt ins Briefing "Worker X hat Bug Y eingeführt" → MERGER wendet den Fix überall an, OHNE zu prüfen, ob Worker X den Bug überhaupt hat.
2. **Substring-False-Positives** — heuristische Verifikation nutzt `grep "Cloud\b"` und matched auch `Claude Code` (weil `\b` nach `Cloud` + `Code` matchen kann in manchen Kontexten).
3. **Über-Fixes bei unklaren Findings** — Faktencheck listet "könnte X oder Y sein" → MERGER rät und produziert kaputten Text.

**Lösung: 4-Schritte-Merger-Methodik** (proven 2026-07-09 auf Transkript-Polishing-Schwarm, 4905 Wörter, 23 Minuten-Marker, 0 Drift):

#### Schritt 1: Basis-Wahl + Begründung
Wähle EINEN Worker-Output als Basis und dokumentiere WARUM (z.B. "Worker 2 hat die meisten Eigennamen-Korrekturen gemacht, daher als Basis"). Die anderen Worker-Outputs werden NICHT gemergt im Sinne von Concatenation, sondern punktuell für spezifische Fixes konsultiert.

#### Schritt 2: Briefing-Claims verifizieren (CRITICAL)
Bevor du einen im Briefing erwähnten Bug fixen willst, verifiziere ihn im tatsächlichen Worker-Output:
- `grep -c "claimed_bug_pattern" worker_output_file`
- Wenn der Bug NICHT existiert (Count = 0) → dokumentiere das im Final-Report und überspringe den Fix.
- Wenn der Bug EXISTIERT → wende den Fix an, aber stelle sicher, dass du ALLE Vorkommen findest (nicht nur die im Briefing erwähnten).

**Proven:** Briefing sagte "Worker 2 hat 'Claudee' eingeführt" → `grep -c "Claudee" output_worker2_stil.md` ergab 0. Hätte ich den Fix angewendet, hätte ich aus "Claude" → "Claudee" → "Claude" → "Claudee" eine Endlosschleife produziert.

#### Schritt 3: Punktuelle Fixes aus anderen Workern übernehmen
Gehe Worker-1-Fixes durch und prüfe gegen Worker-2-Basistext: ist der Fix schon drin? Wenn nein, übernimm ihn punktuell (keine globale Ersetzung, sondern pro Befund).

**Reihenfolge der Fixes** (priorisiert):
1. **Worker 3 Faktencheck-Findings** (kritischste zuerst, weil Faktenfehler das Ergebnis entwerten)
2. **Worker 1 Sprachliche Verfeinerungen** (Satzzeichen, Absatz-Struktur, Wortbrüche)
3. **Konservativ-Skip für alle Findings, die "könnte X oder Y sein" ohne Bestätigung** — dokumentiere jedes Skip im Final-Report mit Begründung.

#### Schritt 4: Post-Merge Verification Gate (PFLICHT)
Bevor du das gemergte Artefakt schreibst, prüfe mit **Word-Boundary-Regex** gegen die Heuristik-Liste:

```bash
# FALSCH: substring-match (false positives)
grep -c "Cloud" merged.md  # matcht auch "Cloud Code", "Cloud-Computing", etc.

# RICHTIG: word-boundary match (semantisch korrekt)
grep -cE "\bCloud\b" merged.md  # matcht nur standalone "Cloud"

# Noch besser: explizit die Compound-Variante ausschließen
grep -oE "(?<![\w-])Cloud(?![\w-])" merged.md  # nur standalone
```

**Proven:** `grep -c "erknüpfen"` matcht 1x in einem 4905-Wort-Transkript — aber der tatsächliche Match war `verknüpfen` (Substring). Erst `\berknüpfen\b` zeigte 0 echte Vorkommen.

**Verification-Matrix (Pflicht vor Final-Write):**

| Check | Methode | Acceptance |
|---|---|---|
| Minuten-Marker count | `grep -cE '^## \[[0-9][0-9]:[0-9][0-9]\]'` | muss = N Marker sein |
| Wort-Drift | `wc -w merged` vs. `wc -w baseline` | muss in ±2% Range sein |
| Eigennamen-Korrekturen | `grep -cE "\bClaudee\b\|\bCloud\b"` (word-boundary) | muss = 0 sein |
| Heuristik-Reste | `grep -cE "<jeder pattern aus skill>"` (word-boundary) | muss = 0 sein |
| Strukturtreue | `grep -c "^## \[ "` (Anzahl Minuten-Marker unverändert) | muss = baseline sein |

**Wenn ein Check fails → fixen BEVOR du den Final-Write machst.** Niemals "mache ich später".

#### Scope-Disziplin: Was der MERGER schreibt (und was nicht)
- ✅ Schreibt: lokaler Output-File (`output_worker<N>_merger.md`) mit Wrapper-Format
- ✅ Schreibt: detaillierter Final-Report (Wort-Count, gefixte Liste, Drift, Acceptance-Checks)
- ❌ Schreibt NICHT: Einbau ins Original-Artefakt (Königin's job, nicht MERGER's)
- ❌ Erfindet KEINE Inhalte, fasst nicht zusammen, ändert keine Reihenfolge

**Briefing muss das explizit sagen** ("Du schreibst NUR den Transkript-Block, den Einbau in den Original-Markdown-File übernehme ich") — sonst neigt der MERGER dazu, mehr zu schreiben als nötig (Scope-Creep).

#### Worked Example (real, 2026-07-09)
- **Inputs:** 3 Worker-Outputs (Inhalt/Stil/Faktencheck) + Baseline + Raw-Caption
- **Briefing-Claim verifiziert:** "Worker 2 hat 'Claudee' eingeführt" → 0 Vorkommen → SKIP
- **Echte Bugs gefunden:** `closed starten` (1x), `Impressummatte` (1x), `DDatei` (1x), `Anmoldeformular` (1x), `züllen` (1x), `debugen` (1x), `erknüpfen` (1x — Substring-Match, false positive), `Modis` (1x), `blaulen` (1x), `Das heiß` (1x), `ca. Eine` (1x)
- **Konservativ geskippt:** `Textag` (1x — unklar), `Resent` (1x — könnte Resend sein), `KFM2` (1x — könnte KVM 2 sein), `[musik]` (1x — explizit als UI-Element erwähnt, kein Caption-Artefakt)
- **Ergebnis:** 4905 Wörter, -0.02% Drift, 23/23 Marker, 0 Heuristik-Reste, alle Worker-3-kritischen Findings adressiert

#### Wann NICHT als MERGER-Worker arbeiten
- **N=1 Worker** → kein Merge nötig, normale Single-Worker-Pipeline
- **Worker-Outputs widersprechen sich fundamental** → Königin muss klären, nicht MERGER raten
- **Merge-Logik erfordert domänenspezifisches Wissen** (z.B. medizinisch-rechtliche Cross-Checks) → MERGER ist nicht der richtige Worker dafür, sondern ein Validator-Subagent mit Domain-Wissen

**Generalisiert:** Funktioniert für jeden N-Worker-zu-1-Output-Konsolidierungs-Task: Polishing-Schwärme, Multi-Perspektiven-Reports, Ensemble-Voting-Systeme.

---

### Pattern 11: Rolling-Wave mit Plan-Biene (Anforderungs-Tracking-Diff)

**Problem:** Bei großen Tasks mit vielen Sub-Anforderungen (5+) entsteht der typische Königin-Schmerz: Schluss-Bericht wird **rekonstruiert** aus Erinnerung, jede Anforderung muss **nachgeforscht** werden, manche Findings verschwinden im Hive-Memory. Standard-Pattern 10 (MERGER) fasst Worker-Outputs zusammen, aber löst nicht das "Plan-vs-Done-Diff"-Problem.

**Lösung: 4-Phasen-Workflow** (proven für komplexe Multi-Anforderungs-Missionen):

#### Phase 1: Parallel-Initial-Recon (3 Worker + 1 Verify-Biene)
- 3 Worker-Bienen dispatched parallel (Pattern 1+2), typische Rollen: Domain-Scout, Tech-Inspector, Risk-Auditor
- 1 Verify-Biene **gleichzeitig** dispatched (Pattern 6) — validiert die Worker-Outputs während sie reinkommen
- Königin sammelt erste Findings in Mnemosyne-Working-Memory

#### Phase 2: Plan-Biene schreibt Gesamt-Anforderungs-Liste
- **Kern-Innovation:** Eine dedizierte Plan-Biene konsolidiert die Findings aus Phase 1 zu einer **strukturierten Anforderungs-Liste** mit ALLEN Anforderungen im Kopf
- Format: Nummerierte Liste A1, A2, A3... mit Sub-Items, Dependencies, Acceptance-Criteria
- **Wichtig:** Plan-Biene ist KEIN Worker — sie produziert KEINE Implementation, NUR Plan
- Königin reviewed Plan-Entwurf bevor Phase 3 startet (Inline-Gate, kein Telegram nötig wenn nur Spec-Validation)

#### Phase 3: Worker gestaffelt (1 nach dem anderen)
- **NICHT parallel!** Worker werden sequentiell dispatched, jede Biene bekommt:
  - Ihre spezifischen Plan-Items (z.B. "Bearbeite A1, A2, A7")
  - Plan-Context (die volle Anforderungs-Liste)
  - Deliverable-Format mit 1:1-Mapping zur Anforderung
- Vorteil: Königin kann nach JEDER Biene das Mapping updaten
- **Nachteil:** Langsamer als Parallel — nur bei großen Tasks gerechtfertigt

#### Phase 4: Schluss-Bericht = Diff Plan ↔ Done
- Bericht wird **automatisch aus dem Plan abgeleitet**, nicht rekonstruiert:
  ```
  A1: Biene-1 → ✅ Done (deliverable: xyz.md)
  A2: Biene-2 → ✅ Done (deliverable: abc.py)
  A3: Biene-3 → ⚠️ Partial (60%, Grund: Token-Limit, follow-up nötig)
  A4: nicht angefangen → ❌ (Grund: Priorität nach Biene-3-Review verschoben)
  A5: ✅ Done
  ```
- **Null Nachforschung** nötig — Königin ist Buchhalterin, nicht Detektivin
- Alle offenen Items landen in Mnemosyne mit `valid_until` für Follow-up-Tracking

#### Wann Pattern 11 vs. Pattern 1-10
- **Pattern 11 lohnt sich ab:** 5+ Sub-Anforderungen ODER Schluss-Bericht-Qualität ist kritisch ODER Königin muss später nachvollziehen können "was war geplant vs. was wurde gemacht"
- **Pattern 11 NICHT nutzen bei:** 1-2 Sub-Tasks (Pattern 1 Mini-Fix), reinen Implementations-Tasks ohne Bericht-Pflicht (Pattern 2 Standard), Polishing-Schwärmen (Pattern 10 MERGER besser)
- **Hybrid:** Pattern 11 für Plan-Phase, dann Pattern 2 für Worker-Phase, dann Pattern 8 für Reporting

#### Anti-Patterns bei Rolling-Wave
- ❌ Plan-Biene schreibt nebenbei Implementation (verliert den Single-Purpose-Fokus)
- ❌ Plan-Items ohne Acceptance-Criteria → Biene rät
- ❌ Phase 3 doch parallel ausführen (Lock-Conflicts auf geteilten Files)
- ❌ Phase 4 ohne Plan-Referenz schreiben (zurück zu Rekonstruktion)
- ✅ Königin tracked Mapping nach JEDER Biene, nicht erst am Ende
- ✅ Plan-Biene-Output ist **Single-Source-of-Truth** bis Phase 4 abgeschlossen

**Proven-Pattern-Variante (Anforderungs-Tracking-Diff):** "Der Plan ist SoT, der Bericht ist Diff." Eliminiert die häufigste Königin-Schmerz-Quelle: nachträgliches Zusammensuchen was eigentlich gemacht wurde.

---

### Pattern 12: Sub-Sub-Dispatch (verifizierbare 2-Level-Delegation)

**Problem:** Eine Aufgabe splittet sich in N Sub-Tasks, aber jeder Sub-Task hat einen Teil, der von einem isolierten Sub-Agenten besser bearbeitet wird (z. B. Verifikation, Hash-Check, Extraktion). Subagenten mit `role='leaf'` (Default) können NICHT delegieren.

**Lösung: role='orchestrator' + max_spawn_depth >= 2**

Die Königin dispatched Eltern-Bienen mit `role='orchestrator'` statt `role='leaf'`. Jede Eltern-Biene kriegt im Briefing zwei Side-Effect-File-Pfade: ihren Deliverable-Pfad UND einen Sub-Sub-Deliverable-Pfad. Das Sub-Sub-File ist der Beweis, dass Delegation stattgefunden hat.

**Drei Komponenten für den Erfolg:**

1. **Config-Voraussetzung:** `delegation.max_spawn_depth >= 2` in `~/.hermes/config.yaml`. Ohne das schlägt Nested-Delegation fehl, auch mit `role='orchestrator'`.

2. **Role-Wahl:** `role='orchestrator'` im `delegate_task`-Tasks-Array. `role='leaf'` (Default) strippt `delegate_task` aus dem Child-Toolset an Position `tools/delegate_tool.py:705` — der Parent läuft clean durch, spawnt aber nie einen Sub.

3. **Side-Effect-File als Beweis:** Jedes Parent-Briefing definiert zwei deterministische Pfade (`/tmp/<prefix>/<ts>.<ext>` und `/tmp/<prefix>/<ts>-sub.<ext>`). Nach dem Batch-Callback checkt die Königin: `ls /tmp/<prefix>/<ts>*` — count muss `2 * N` sein.

**Verifikation (PFLICHT nach Dispatch):**
```bash
ls /tmp/<prefix>/<TS>* | wc -l          # count = 2*N
sha256sum /tmp/<prefix>/<TS>-sub.txt    # compare hash against parent-recompute
```

**Proven 2026-07-14:** 3 Parents (Alpaca, Bumble, Cicada) mit `role='orchestrator'` dispatched. Alle 3 spawnen erfolgreich Sub-Subs. Side-Effect-Files existieren (2 Files pro Parent = 6 total). Hash-Cross-Check: 5/5 Hashes von Cicada's Sub-Sub byte-genau verifiziert. Fehlversuch davor mit `role='leaf'`: 3 Parents liefen clean durch, 0 Sub-Subs gespawnt, 0 Erkennung ohne Side-Effect-File-Check.

#### Wann Pattern 12 vs. Pattern 1-11
- **Pattern 12 lohnt sich bei:** Tasks die N Eltern-Bienen brauchen, wobei jede Eltern-Biene einen isolierten Sub-Task hat (Verifikation, Hash-Check, Datenextraktion, Diagnose)
- **Pattern 12 NICHT nutzen bei:** Reinen Fan-Outs (Pattern 2 reicht), Single-Level-Delegation (kein Sub-Sub nötig), oder wenn die Sub-Task rein mechanisch ist (30-90s dispatch Overhead lohnt sich nicht)
- **Overhead bewusst:** Jeder Sub-Sub-Spawn kostet 30-90s Boot-Zeit + Prompt-Token. Lohnt sich nur wenn die Sub-Task Reasoning braucht (Diagnose, Klassifikation) oder genug Output-Volumen produziert um den Parent-Kontext zu entlasten.

#### Anti-Patterns bei Sub-Sub-Dispatch
- ❌ `role='leaf'` dispatcht → Sub-Sub wird nie gespawnt, Parent meldet "fertig", nur der fehlende Side-Effect-File verrät den Fehler
- ❌ `max_spawn_depth=1` → Nested-Delegation blockiert, unabhängig von role
- ❌ Kein Side-Effect-File → Königin merkt nicht, dass Sub-Sub nicht gespawnt wurde
- ❌ Sub-Sub für reine I/O-Aufgaben (sha256sum, cp, ls) → 30-90s Overhead vs. ms inline
- ❌ `max_concurrent_children` unterschätzt → N Parents + N Subs = 2N Slots, bei Budget 6 = 3 Parents + 3 Subs ist EXAKT am Limit

#### Vollständige Referenz
Skill `orchestration/sub-sub-workflow` mit Briefing-Template (`references/sub-sub-briefing-template.md`) und verify-Skript (`scripts/verify-sub-sub.sh`).

**Source-of-truth: Spec v1.5.1** (`references/rolling-wave-live-test-pickup.md`) für die 🅲️-spezifischen Pitfalls. Diese Skill-Index-Tabelle ist ein **Inhalts-Index über alle 11 Patterns + 🅲️-spezifische Funde**, nicht widersprüchlich zur Spec — sie aggregiert Pitfalls aus mehreren Quellen.

| Pitfall-# | Description | Quelle / Wo dokumentiert | Generalisierbar? |
|---|---|---|---|
| #20 | Tech-Inspector schreibt ins read-only-Repo (`.hermes/phase1-*-report.md` ins Repo) | SKILL.md + Spec v1.5.1 OUTPUT-PFAD-Section | ✅ → `multi-agent-pitfalls-cheatsheet` (Top-20) |
| #21 | `process(action='wait', session_id='deleg_X')` schlägt fehl — delegation-IDs ≠ process-IDs | SKILL.md only (NICHT in Spec v1.5.1) | ✅ → `multi-agent-pitfalls-cheatsheet` (Top-20) |
| #22 | A1+A2 parallel dispatcht obwohl A2 von A1 abhängt (Wave-Composition) | SKILL.md + Spec v1.5.1 | ✅ → `multi-agent-pitfalls-cheatsheet` (Top-20) |
| #23 | Phase 3 ohne Phase 2.5 (Königin-Lücken-Resolution) | Spec v1.5.1 (Spec-only — in SKILL Pitfall-#25 genannt) | ✅ → `obsidian-subagent-briefing-template` |
| #24 | A3 Hierarchie implizit statt hart kodiert (Plan-Biene vs Worker-Interpretation) | SKILL.md + Spec v1.5.1 | ✅ → `obsidian-subagent-briefing-template` |
| #25 | A6 Coverage-Ausschluss ohne Issue-Tracker (Coverage-Tech-Debt) | SKILL.md + Spec v1.5.1 | 🟡 Hermes-V7-spezifisch, in Spec v1.5.1 |
| #26 | Welle-2-Worker-Bienen Self-Commit fehlt (Briefing-Disziplin > Biene-Disziplin) | SKILL.md + Spec v1.5.1 | ✅ → `delegation-anti-patterns` (Bereits #16, 2026-07-13) |
| Königin-Fallback-Commit | Reproducible technique für wenn Worker-Biene nicht selbst committed | SKILL.md (NEU v1.5.2) + `delegation-anti-patterns` #16 | ✅ Königin-Reproducible-Pattern |

**Nummerierungs-Konflikt-Resolution (v1.5.2):** Die Spec v1.5.1 listet Pitfalls #22/#24/#25/#26 als die **4 NEUEN** Findings der Mission-B. Die SKILL.md listet zusätzlich #20/#21/#23 als Pre-Mission-Findings, plus das neue Königin-Fallback-Commit-Pattern. Beide Zahlen-Sätze sind korrekt in ihrem jeweiligen Scope — Spec zählt die NEUEN, SKILL zählt die KUMULIERTEN. Kein Widerspruch mehr.

**Generalisierbare Patterns (NICHT Hermes-V7-spezifisch, gehören in andere Skills):**
- **#20 (Output-Pfad read-only-Heimat)**, **#21 (process()-wait schlägt fehl)**, **#22 (Wave-Composition mit Dependency)** → `multi-agent-pitfalls-cheatsheet` als Top-20-Einträge (Skill existiert noch nicht — Curator-Opportunity)
- **#23 (Phase 2.5 Königin-Lücken-Resolution)** und **#24 (Hierarchie-Hart-Kodieren)** → `obsidian-subagent-briefing-template` als Pitfall-Block (Skill existiert, Update-Pending)
- **#25 (Coverage-Tech-Debt)** bleibt Hermes-V7-spezifisch in Spec v1.5.1 — NICHT generalisieren
- **#26 (Self-Commit-Disziplin)** und **Königin-Fallback-Commit** → `delegation-anti-patterns` #16 (Bereits gemerged am 2026-07-13)
