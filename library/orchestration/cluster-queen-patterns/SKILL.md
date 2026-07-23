---
name: cluster-queen-patterns
title: "Cluster Queen Patterns (Briefing, Self-Commit, Fallback)"
description: "Use when implementing queen-side cluster patterns: briefing-disciplin-self-commit, self-push, or königin-fallback-commit. NOT for dispatch modes (use cluster-dispatch-modes)."
category: orchestration
version: '1.0'
created: '2026-07-23'
author: Yuno (split from multi-agent-cluster-patterns)
lane: koenigin
agent: universal
trigger_keywords: ['queen', 'briefing', 'self-commit', 'self-push', 'fallback', 'commit']
keywords: ['queen', 'briefing', 'self-commit', 'fallback', 'cluster', 'queen-side']
related_skills: ['cluster-dispatch-modes']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from multi-agent-cluster-patterns 2026-07-23)'

license: MIT
---

# Cluster Queen Patterns (Briefing, Self-Commit, Fallback)

_Extracted from multi-agent-cluster-patterns on 2026-07-23._

## Briefing-Disziplin-Self-Commit (NEU v1.5.1, proven Hermes-V7 Welle 2-4)

**Lesson:** 3 von 4 Wellen haben korrekt self-committed. Welle 2 nicht. **Briefing-Verstärkung funktioniert besser als Biene-Disziplin-Erwartung.**

**Generalisierbare Regel:** Jedes Worker-Briefing das zu git-Operationen führen könnte MUSS enthalten:

```
## PFLICHT: Self-Commit + Self-Push (am Ende)
- git add <modified files>
- git commit -m "<konventionelle Message>"
- git push origin <branch>
- Im Self-Report: EXAKTE Commit-SHA
- Falls git-Operationen nicht möglich: MELDEN statt überspringen
```

**Verifikation:** Königin prüft nach jeder Welle mit `git status --porcelain` ob working tree clean ist. Falls nicht → Königin-Fallback-Pattern.

**Generalisierungs-Lesson (NICHT Hermes-V7-spezifisch):** Dies ist ein generisches **delegate_task-Briefing-Disziplin**-Pattern, sollte in `multi-agent-pitfalls-cheatsheet` als Top-20-Eintrag.

**Origin:** 2026-07-09 23:23 Berlin, Basti-Feedback nach Greytrix-Phase-A: "wenn die plan-biene den plan schreibt mit den gesamt-anforderungen im kopf und dann nach plan worker für worker abgeht die infos sammelt mit zum schluss bericht anforderung und gemachte arbeit 1:1 gegenübersteht dann musst du weniger im nach hinein forschen"

---

## Königin-Fallback-Commit-Pattern (NEU v1.5.2, proven Hermes-V7 Welle 2)

**Symptom:** Worker-Biene ist zurück, hat `tsc grün` und `Tests grün` gemeldet, ABER `git status --porcelain` zeigt dirty working-tree. Kein `git commit` durch die Biene. Biene hat Briefing-Pflicht nicht befolgt (oder Briefing hatte es nicht explizit gefordert).

**3-Schritte-Königin-Reproducible-Pattern** (proven 2026-07-13 Mission-B Welle 2, Commit `2920e93`):

```bash
# 1. Working-Directory: cd <repo> und Working-Tree-Status verifizieren
cd <repo>
git status --porcelain
# Erwartung: Modified files + evtl. untracked test files (NICHT committed)

# 2. Files stagen + commit mit Königin-Author-Marker
git add <modified-files> <untracked-test-files>

git -c user.email='queen-bee@<repo>.local' \
    -c user.name='Yuno-Queen-Bee' \
    commit -m "feat(<scope>): <description> (Königin-Fallback-Commit)"

# Königin-Author-Marker ist WICHTIG:
# - Spätere Audits können Königin-Commits von Worker-Commits unterscheiden
# - Im Diff-Bericht muss "Königin-Commit" explizit markiert sein
# - User-Email-Domain "<repo>.local" macht klar, dass dies nicht der echte User-Author ist

# 3. Push + Diff-Bericht-Update
git push origin <branch>
# Im Diff-Bericht in der "Königin-Pitfall-Funde"-Section (Pitfall-#26 Trigger) eintragen:
# - Welche Biene hat nicht committed
# - Welche Commit-SHA hat die Königin manuell gesetzt
# - Welche Anforderung war betroffen
```

**Wann anwenden:**
- **IMMER** wenn nach Phase 3 / nach Welle die `git status --porcelain` nicht leer ist und die Worker-Biene bereits als "fertig" zurückgemeldet hat
- **NIE** als Standard-Workflow — Self-Commit der Biene ist immer vorzuziehen (Pitfall-#26 Fix: Briefing-Verstärkung)
- **NACH** Briefing-Update für die nächste Welle (Pitfall-#26 Lesson: Self-Commit-Disziplin löst das zuverlässig)

**Verifikation der Reproduzierbarkeit:**
- Welle 2 (A3+A4) der Hermes-V7-Mission brauchte Königin-Fallback → Commit `2920e93`, Biene-Output war tsc grün, Diff-Bericht dokumentiert
- Welle 3 (A5) und Welle 4 (A6) der selben Mission mit aktualisiertem Briefing → Self-Commit funktioniert, kein Fallback nötig
- 3 von 4 Wellen mit Self-Commit-Pflicht im Briefing: 3 erfolgreich, 1 Fallback (= 25% Fallback-Rate, akzeptabel)

**Anti-Pattern:**
- "Ich committe einfach unter dem User-Namen" → verbirgt, dass die Biene nicht committed hat, macht zukünftige Audits schwerer
- "Ich warte auf die nächste Welle und hoffe dass die es fixt" → dirty working-tree zwischen Wellen → Mapping-Update wird unzuverlässig
- "Ich committe nichts und sage dem User 'fast fertig'" → versteckt Pitfall vor dem Eval-Loop

**Bezug zu anderen Skills:**
- `delegation-anti-patterns` #16 (Worker-Biene Self-Commit fehlt) — gleicher Symptom-Komplex, aber dort als "Briefing-Verstärkung muss es lösen" formuliert
- Hier als **Königin-Reproducible-Technique** formuliert, weil es in der Praxis eine zuverlässige 3-Schritt-Routine ist

**Generalisiert:** Funktioniert für jeden Workflow, in dem Subagents an git-Repositories arbeiten — Code-Missionen, Doc-Missionen (wenn Docs in git), Config-Missionen.

---

### Pattern 13: Analytical-Dimension Fan-Out (Daten-Analyse)

**Problem:** Eine große einzelne Datenquelle (Log-Datei, Wire-Capture, Dump) soll analysiert werden, aber **File-Chunking** (Aufteilen auf N Subagents pro Chunk) funktioniert nicht, weil jede Analyse-Dimension die **gesamte Datei** sehen muss (z. B. für Unique-Counts, Lifecycle-Analyse, Zeitreihen). Die Quelle ist ein einzelnes Artefakt, nicht N unabhängige Files.

**Lösung: Analyse-Dimension statt File-Chunk.** Alle N Bienen kriegen das **gleiche komplette Input-File**, aber jede bekommt eine **andere analytische Frage** — z. B. "Analysiere Talker-Prozesse", "Analysiere Remote-Destinations", "Analysiere Zeitsequenz". Die Dimensionen müssen disjunkt genug sein, dass Findings sich ergänzen statt widersprechen.

**Kern-Prinzip: Was steckt im Briefing?**
- Jede Biene bekommt den **gleichen absoluten Pfad** zur Quelldatei
- Briefing sagt explizit: "read-only, NIE ändern — DU liest sie nur, DU schreibst sie nie"
- Jede Biene bekommt eine **einzige Dimension** (eine Frage) — keine Vermischung
- Output-Format: Markdown mit ~80 Zeilen pro Biene

**5-Schritte-Consolidation-Methodik:**
1. **Findings-Matrix** bauen (Finding × Biene × Queen-Urteil)
2. **Overlap erkennen + deduplizieren** — gleiches Finding von 2 Bienen einmal nennen
3. **Konflikte auflösen** — bei Widerspruch: Queen-Quick-Count via `grep -c` gegen die Quelldatei
4. **Top-Findings priorisieren + live-verifizieren** — `ss -tupn | grep <ip>` für Netze, `ps aux | grep <pid>` für Prozesse
5. **Bewertungs-Bias notieren** — jede Biene alamiert durch ihre Dimension anders

**Output-Struktur:**
- Konsolidierte Hauptnotiz (3-7 KB) — Findings, Prioritäten, Live-Verifikation, nächste Schritte
- Raw-Reports als `.raw-<dimension>-<date>.md` — Beweissicherung, nicht löschen

**Abgrenzung zu Pattern 10 (MERGER):**
- Pattern 10: Alle Bienen bearbeiten denselben **Text** — MERGER konsolidiert konkurrierende Edits (ein Output)
- Pattern 13: Alle Bienen lesen dieselben **Daten** — jede beantwortet eine andere Frage (komplementäre Outputs)

**Proven 2026-07-15:** 17,6 MB Wire-Capture-Log (3091 ss-Snapshots / 104,7 Min), 3 Bienen parallel in 245s Gesamtlaufzeit (Talker 202s, Destinations 245s, Sequenz 151s). 0 leere Snapshots, 0 Konflikte zwischen Bienen (Dimensionen waren disjunkt genug). 5 Findings extrahiert, 4 live-verifiziert, 1 🔴+2 🟡+2 🟢 priorisiert. Vault-Note mit 3 Raw-Reports.

**Vollständige Referenz in:** `references/analytical-dimension-fan-out.md` — Briefing-Template, Generalisierung auf Code-Review/Server-Logs/DB-Dumps/Configs, Worked-Example mit Findings-Matrix, Pitfalls.

---

## Cluster-Phase-Template (5 Phasen)

```
Phase 0: Inventur (READ-ONLY, Pattern 0 nicht in Note, aber Praxis)
   → Welche Files/Notes existieren schon? Was ist Cluster-Scope?

Phase A: Spec-Splitting (Königin, Pattern 5)
   → file_scope_table, anti_pattern_list, output_format pro Subagent

Phase B: Fan-Out (parallel, Pattern 2 + Pattern 1)
   → delegate_task, niemals Fixer parallel zu Scouts

Phase C: Konsolidierung (Königin, Pattern 1+3)
   → Per-Cluster-States sammeln, Halluzinations-Markierungen prüfen

Phase D: Verifikation (Pattern 6+7)
   → Backlink-Roundtrip, Verwaiste-Liste

Phase E: Reporting (Pattern 8)
   → 5-Punkte-Report, Lessons
```

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Konflikt-Race-Conditions auf geteilten Files | Pattern 1+2 anwenden, Cluster-Section-Map |
| 2 | Subagent erfindet Tech-Details | Pattern 3 explizit im Briefing |
| 3 | Subagent-Briefing <500 Wörter → Spec zu vage | Briefing-Gerüst aus `obsidian-subagent-briefing-template` |
| 4 | Cluster-Reporting fehlt → keine Lessons-Lernkurve | Pattern 8 immer ausführen |
| 5 | Verwaiste Notes sammeln sich über Cluster hinweg | Pattern 7 nach JEDEM Cluster ausführen |
| 6 | Fixer parallel zu Scouts im selben Batch | delegation-anti-patterns #1 lesen |
| 7 | Reasoning-Effort zu niedrig → False-Positive-Flood | delegation-anti-patterns #2 lesen |
| 8 | Improvisation ohne Dokumentation → Königin versteht nicht warum Spec ignoriert wurde | Pattern 9 Bedingung 3: Abweichung im Summary dokumentieren |
| 9 | MERGER wendet Briefing-Claims blind an, ohne im Worker-Output zu verifizieren | Pattern 10 Schritt 2: `grep -c "<claim>" worker_output` VOR dem Fix; wenn 0, dokumentieren und SKIP |
| 10 | MERGER nutzt substring-match für Heuristik-Verifikation → false positives | Pattern 10 Schritt 4: word-boundary regex `\b...\b` oder `(?<![\w-])...(?![\w-])` |
| 11 | MERGER rät bei unklaren Faktencheck-Findings ("könnte X oder Y sein") und produziert kaputten Text | Pattern 10 Schritt 3: konservativ skippen, im Final-Report mit Begründung dokumentieren |
| 12 | Rolling-Wave: Plan-Biene schreibt nebenbei Implementation → Single-Purpose-Fokus verloren | Pattern 11: Plan-Biene produziert NUR Plan, KEIN Implementation; Königin reviewed Plan-Entwurf bevor Phase 3 startet |
| 13 | Rolling-Wave: Plan-Items ohne Acceptance-Criteria → Biene rät | Pattern 11: Jede Anforderung MUSS messbares Acceptance-Criterion haben (Datei-Pfad, Test-Result, Spec-Wert) |
| 14 | Rolling-Wave: Phase 3 doch parallel ausführen → Lock-Conflicts auf geteilten Files | Pattern 11: Phase 3 ist IMMER sequentiell (1 Worker nach dem anderen), nur Phase 1 darf parallel sein |
| 15 | Rolling-Wave: Phase 4 ohne Plan-Referenz → zurück zu Rekonstruktion | Pattern 11: Schluss-Bericht MUSS strukturiertes 1:1-Mapping Plan-Items ↔ Done-Items enthalten, "anecdotal report" ist Anti-Pattern |
| 16 | 🅲️ vs. Werkstatt verwechseln — User-Echo-Phase-2 als "nervig" abtun | NEU v1.4.0: Klare Decision-Tree "Weißt du WAS du willst?" → 🅲️ vs. Werkstatt; User-Eingriff in Phase 2 ist Feature, nicht Bug |
| 17 | 🅲️ Live-Test-Pickup ohne Repo-Layout-Check starten — Phase 1 läuft ins Leere | NEU v1.4.0: Phase 0.5 = Königin-Vor-Scout (ls/find/git status), BEVOR 3 Scout-Bienen gefeuert werden. Vermeidet "nichts da"-Reports |
| 18 | Königin scouted selbst statt auf Bienen zu warten — Detektivin-Modus statt Königin-Modus | NEU v1.4.0: Königin bereitet Setup vor, NICHT die Antworten. Königin-Vor-Scout ist Setup, Bienen-Ergebnisse sind Antworten |
| 19 | 🅲️-Patch in fremden Feature-Branch (z.B. `feat/security-kernel`) statt eigenem Branch | NEU v1.4.0: Eigener Branch pro Mission. Live-Tests nie in aktive Feature-Branches patchen |
| 20 | **Scout-Biene schreibt Report in read-only-Heimat** (NEU v1.4.0, proven 2026-07-13 Hermes-V7 Mission) | Briefing MUSS absoluten Output-Pfad **außerhalb** der read-only-Heimat vorgeben: `/tmp/scout-<mission>-<biene>.md` oder `~/.hermes/cache/delegation/`. Default-Pfade des Subagent-Tools landen oft im CWD — wenn das ein read-only-Repo ist, schreibt die Biene ins `.hermes/phase1-<rolle>-report.md` und produziert AGENTS.md-Konventionsbruch. Briefing-Must-Have-Sektion: `OUTPUT-PFAD: /tmp/scout-hermes-v7-domain.md — NICHT im Repo schreiben, NICHT in ~/.hermes/skills/.` Verifikation in Königin-Vor-Scout: `ls <repo>/.hermes/phase1-*` muss nach Phase 1 **leer** sein. |
| 21 | **`delegate_task` IDs sind KEINE process-IDs** (NEU v1.4.0, proven 2026-07-13) | `process(action='wait', session_id='deleg_X')` schlägt fehl mit `not_found` — delegation-IDs gehören nicht zur process-Layer. Königin MUSS auf Async-Message warten (kommt automatisch als neue Tool-Result-Message wenn Batch fertig). **Anti-Pattern:** `process(action='poll')` pollen = Detektivin-Modus. **Korrekt:** Königin bereitet Phase-2/3-Setup vor, während Bienen laufen — keine aktive Warte-Aktion. |
| 22 | **Phase 3 Wave 1 mit A1→A2-Dependency trotzdem beide parallel dispatcht** (NEU v1.4.0, proven 2026-07-13) | A1 (Branch-Creation) und A2 (Schema-Patch) wurden parallel gefeuert weil Dependency-Sequenz scheinbar parallelisierbar war. **Aber:** A2-Biene braucht den Branch den A1 erstellt. Risk: A2 committed auf falschen Branch, oder A2-Biene verwirft weil Branch noch nicht existiert. **Fix:** Wave-1-Default = sequentiell wenn A→B-Dependency existiert. Nur A3∥A4 (zwei Files, beide nur A2-abhängig) parallel. Wave-1 mit Dependency = **immer sequentiell**, auch wenn 2 Bienen schneller wären. |
| 23 | **Plan-Biene disclosed Lücken + Königin schließt sie** (NEU v1.4.0, proven 2026-07-13) | Pitfall-#5-Disziplin der Plan-Biene: sie sagt ehrlich "audit-log-Pfad unklar, Feature-Flag-Ort unklar, 100%-Coverage kein Repo-Standard". Königin MUSS diese Lücken vor Phase 3 schließen — sonst arbeiten Worker-Bienen ins Blaue. **Königin-Workflow nach Phase 2:** (1) Plan-Biene-Output lesen, (2) Lücken/Widersprüche identifizieren, (3) jede Lücke via 1-3 fokussierte terminal-Calls schließen (NICHT Worker-Biene dafür — das wäre Detektivin-via-Subagent), (4) Plan-Constraints mit Lösungen anreichern, (5) erst dann Phase 3 dispatchen. |
| 24 | **Off-by-one bei "unversionierten Files"** (NEU v1.4.0, proven 2026-07-13) | Plan-Biene sagte "2 unversionierte Files" (memory-provider.ts/.test.ts), Königin fand 3 (`.hermes/phase1-tech-inspector-report.md` zusätzlich). **Fix:** Phase-1-Briefing MUSS sagen: "Behandle ALLE `git status --porcelain`-Outputs, nicht nur die im Briefing erwähnten." Königin-Vor-Scout verifiziert mit `git status --porcelain` selbst und ergänzt die Liste im Phase-3-Briefing. |
| 25 | **TaskCard ≠ LaneTask** (NEU v1.4.0, proven 2026-07-13) | User/Briefing sagt "LaneTask", Code hat `TaskCard`. Domain-Scout Biene hat den Pitfall-#5 sauber gefangen und korrigiert: "TaskCard ≠ LaneTask". **Fix:** Briefing-Templates nutzen `TaskCard` als kanonischen Namen, oder fragen "Was ist der echte Type-Name im Code?". Domain-Scout Biene MUSS im Output den ersten Satz haben: "Der Typ heißt X (nicht Y)" wenn der Briefing-Name falsch ist. |
| 26 | **Worker-Biene committed nicht selbst** (NEU v1.5.1, proven 2026-07-13 Hermes-V7 Welle 2) | A3+A4 Bienen in Welle 2 haben gearbeitet (tsc grün, Tests grün), ABER `git status` zeigte dirty working-tree als sie zurückkamen. Bienen committen NICHT selbst wenn nicht explizit gefordert. **Fix:** Briefing-Must-Have ab Welle 2: "AM ENDE — PFLICHT: git add <files>, git commit -m '...', git push origin <branch>" + "Im Self-Report: EXAKTE Commit-SHA". Welle 3 (A5) hat das befolgt → Self-Commit funktioniert wenn Briefing es explizit fordert. **Generalisiert:** Die Lösung ist Briefing-Verstärkung, NICHT Biene-Disziplin-Erwartung. **Königin-Fallback:** Wenn Biene nicht committed hat → manuell `git add && git commit -c user.email=queen-bee@hermes-v7.local -c user.name=Yuno-Queen-Bee && git push`, im Diff-Bericht als "Königin-Commit" markieren. |

## Connecting Skills

- **`obsidian-vault-cluster-operations`** — Pattern 1–5 als Vault-Workflow
- **`obsidian-subagent-briefing-template`** — Pattern 5 als ausfüllbares Template
- **`obsidian-vault-quality-audit`** — Pattern 6+7 als automatisierter Audit
- **`subagent-driven-development`** — Subagent-Workflow generisch (Code)
- **`delegation-anti-patterns`** — Hermes-spezifische Pitfalls
- **`orchestration`** — Phase-0-Inventur + Fable-Swarm-Pattern
- **`orchestration/multi-agent-pitfalls-cheatsheet`** — TRIGGER-WATCHLIST
- **`orchestration/sub-sub-workflow`** — Pattern 12 Detail-Skill mit Briefing-Template + verify-Skript

## Reference Files (für Deep-Dive)

- **`references/analytical-dimension-fan-out.md`** — Pattern 13 deep-dive: Dimension-Split-Strategie, 5-Schritte-Consolidation-Methodik, Briefing-Template, Worked-Example Wire-Capture 2026-07-15 (17.6 MB, 3 Bienen, 245s), Pitfalls, Generalisierung auf andere Domänen (Code-Review, Server-Logs, DB-Dumps, Configs).
- **`references/merger-worker-pattern.md`** — Pattern 10 deep-dive: Briefing-Template, Word-Boundary-Regex-Patterns, Worked-Example (Transkript-Polishing-Schwarm 2026-07-09), häufige Fehler.
- **`references/dispatch-mode-guide.md`** — 🅰️🅱️🅲️ Selection Guide worked context: Basti's Original-Feedback (2026-07-09), Pattern-Zuordnung pro Dispatch-Phase, Greytrix-Beispiel, Legacy-2x3-Abgrenzung und Probleme.
- **`references/rolling-wave-live-test-pickup.md`** — v1.5.1: 🅲️ Live-Test-Pickup-Spec mit Decision-Tree, 4-Phasen-Checklisten (Scout/Plan/Worker/Diff), Briefing-Templates, Plan-Output-Schema, Diff-Bericht-Schema, 5-Punkte-Eval-Loop, Pitfall-#22/#24/#25/#26.
- **`references/live-test-2026-07-13-hermes-v7.md`** — ABGESCHLOSSENE Proven-Mission: Hermes-V7 Idempotenz-Key Patch (2026-07-13). Commit-History, Plan-Done-Matrix, Eval-Status, Time-Metriken, Folge-Aktionen.

## Source

- Vault: `Skill-Ableitung - Vault-Phase-2-3.md` (05 Ressourcen, 2026-07-05)
- 8 Patterns dokumentiert aus Phase-2 + Phase-3-Erfahrungen
- Pattern 9 dokumentiert aus Phase-4 (Subagent K + L Improvisationen, 2026-07-05)
- Generalisierung über Obsidian hinaus: ja (Vault-Clustering ist ein Spezialfall von Multi-Agent-Clustering)
- v1.4.0: 🅲️ vs Werkstatt Abgrenzung + Live-Test-Pickup-Spec (2026-07-13, Hermes-V7 Idempotenz-Key Mission-B)
- v1.5.0: Pitfalls #20-25 aus erstem echten 🅲️-Live-Test (2026-07-13, Hermes-V7 Mission-B Welle 1)
- v1.5.1: Pitfall #26 (Worker-Biene Self-Commit fehlt) + Königin-Fallback-Pattern + Dual-Layer-Feature-Flag-Pattern (proven Welle 2+3, 2026-07-13)
- v1.5.2: Pitfall-Index-Resolution (Spec v1.5.1 als 🅲️-SoT, SKILL.md als kumulativer Index); Königin-Fallback-Commit als reproducible technique; Proven-Mission-Status-Header nach Hermes-V7 Mission-B complete (4 Commits gepusht, 3 GitHub-Issues offen, EVAL-OK, 5/6 Anforderungen DONE, Spec v1.5.1 unchanged) + v1.5.3: Pattern 12 (Sub-Sub-Dispatch) + Pitfall #27 (role=leaf strippt delegate_task) + Cross-Ref zu orchestration/sub-sub-workflow (2026-07-14, Sub-Sub-Workflow Live-Test v1/v2, max_spawn_depth=2). Skill `multi-agent-pitfalls-cheatsheet` existiert noch nicht — wenn angelegt, sollten Pitfalls #20/#21/#22 dort rein.
