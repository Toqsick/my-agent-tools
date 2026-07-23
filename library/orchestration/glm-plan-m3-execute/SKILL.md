---
name: glm-plan-m3-execute
description: >-
  Use when user asks for planning and executing a complex multi-step task, using GLM as planner and M3 as worker, running reality checks before implementation, or executing work in verified waves. NOT for tasks of three or fewer deterministic steps or research-only requests. Enforces a five-phase planner-worker pipeline with path inventory, Queen review, quality gates, worker dispatch, and wave verification.
version: 1.0.0
author: Yuno for Basti
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags:
      - planning
      - execution
      - orchestration
      - glm
      - minimax
      - plan-execute-pipeline
      - queen-verify
    related_skills:
      - plan-glm
      - better-plan-strategy
      - subagent-driven-development
      - critic-gate
      - multi-agent-master-workflow
lane: koenigin
reasoning_effort: xhigh
trigger_keywords: ['and', 'executing', 'worker', 'glm-plan-m3-execute', 'planning']
keywords: ['worker', 'executing', 'planner', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['orchestration-glm-m3-swarm-pattern', 'plan-glm']
---

# GLM-Plan-M3-Execute: End-to-End Plan-Execute Pipeline

Verdrahtet `plan-glm` → `better-plan-strategy` → `subagent-driven-development` →
`critic-gate` zu einer durchgängigen Pipeline.

**Das Problem das dieser Skill löst:** 19 von 23 Plänen (83%) in Basti's
Hermes-Setup haben 0-1 von 6 Quality-Gates. GLM 5.2 schreibt exzellente Pläne,
aber die Pläne werden nicht gegen die Realität verifiziert, bevor M3 sie
ausführt. Subagent-halluzinierte Mnemosyne-IDs (4/4 in einer Session) und
28% falsch-klassifizierte Files (bewiesen 2026-07-16) sind die Folge.

**Die Lösung:** Ein Router-Skill der die vorhandenen Bausteine verdrahtet und
die Quality-Gates zur harten Pflicht macht — an 5 Stellen.

## When to Use

- Ein Task benötigt Planung + Ausführung (nicht nur "mach das schnell")
- Der Task ist komplex genug für mehrstufige Ausführung (≥3 Schritte)
- GLM 5.2 ist als Planer verfügbar (Session-Model oder via plan-glm-Subprocess)
- M3 ist als Arbeiter verfügbar (via `delegate_task` mit `delegation.model: MiniMax-M3`)
- Trigger: "plan and execute", "plan und ausführen", "baue X", "refactore Y",
  `/glm-plan-m3-execute`

**Nicht verwenden bei:**
- Trivialen Tasks (≤3 Schritte, 1 Datei, keine Heuristik) → direkter `delegate_task`
- Tasks die nur Recherche sind → `multi-agent-orchestration`
- Tasks ohne Code-Implementierung → `writing-plans` + manuelle Ausführung

## Rollen-Mapping

| Rolle | Modell | Skill-Kontext | Verantwortung |
|---|---|---|---|
| **Königin (Queen)** | Session-Model — live per Default **MiniMax-M3** (`model.default`); GLM 5.2 nur, wenn die Session bewusst darauf läuft | Dieser Skill | Orchestriert alle Phasen, entscheidet an Gates, führt Reality-Check aus, verifiziert zwischen Wellen |
| **Planer** | GLM 5.2 (via `plan-glm` subprocess) | `plan` + `better-plan-strategy` | Schreibt den strukturierten Plan mit Quality-Gates |
| **Arbeiter (Workers)** | MiniMax M3 (via `delegate_task`) | `subagent-driven-development` | Führt Tasks in Wellen aus, TDD, Self-Tests |
| **Reviewer** | Königin (in-Session) | `critic-gate`-Prinzipien | Verifiziert Subagent-Outputs gegen Spec + Realität |
| **Judge (optional)** | Lokaler DeepSeek R1:8b | `critic-gate` Script | Deterministisches Quality-Gate für kritische Outputs |

## Die 5 Phasen

```
Phase 1: REALITY-CHECK ─→ Phase 2: GLM PLAN ─→ Phase 3: QUEEN-VERIFY ─→ Phase 4: M3 EXECUTE ─→ Phase 5: REVIEW
(Queen)                  (GLM 5.2)            (Queen)                  (M3 Workers)           (Queen + Critic)
    ↑                                                                                              │
    └────────────────────────── REVIEW-LOOP (bei Bedarf) ──────────────────────────────────────────┘
```

### Phase 1: Pre-Plan Reality-Check (~2 Min, Königin)

**Ziel:** GLM 5.2 bekommt verifizierte Realität, nicht Annahmen.

Die Königin inventarisiert **vor** dem Plan-Write:

1. **Pfad-Existenz** jedes Files/Verzeichnisses das der Task berührt:
   ```bash
   # Für jeden Pfad:
   test -f <path> && echo "✅ exists" || echo "❌ MISSING"
   find <vault-root> -iname "<glob>" 2>/dev/null  # Duplikate finden
   ```

2. **Strukturelle Variation** (für Heuristik/Detection-Tasks zwingend):
   ```bash
   # Section-Header-Inventar:
   find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20
   ```

3. **Daten-Health** (für Status-basierte Tasks):
   ```bash
   # Wenn Health-Werte relevant sind, laufe die Detection auf ALLEN Files
   for f in $(find <target> -name "*.md" | sort); do
       python3 <detection-script> --date "$(basename "$f" .md)" --json 2>/dev/null
   done
   ```

**Output:** Eine Realitäts-Status-Tabelle. Siehe
`references/plan-brief-template.md` für das vollständige Template das in den
GLM-Brief eingefügt wird.

**Gate:** Mindestens 1 Pfad verifiziert. Wenn 0 Pfade verifizierbar → Task ist
zu vage, mit User klären.

### Phase 2: GLM 5.2 Plan (~3-5 Min, Planer)

**Ziel:** Ein strukturierter Plan mit allen 6 Quality-Gates.

Aufruf via `plan-glm` Skill (siehe dessen SKILL.md für den genauen Mechanismus).

**Der Brief MUSS enthalten:**

1. Task-Ziel (1 Satz)
2. **Realitäts-Status-Tabelle aus Phase 1** (nicht-verhandelbar)
3. Pflicht-Quality-Gates:
   - S1: Realitäts-Status-Tabelle oben im Plan
   - S2: SSOT-Audit-Tabelle (bei audit-driven Plänen)
   - S3: Konkrete Minuten-Schätzungen pro Task
   - S4: Atomic-Write Policy bei Single-File-Edits
   - S5: Risiko-Sektion R1-Rn mit Shell-Probes
   - S6: Wave-Strategie (welche Tasks parallel, welche sequentiell)
   - S7: Done-Kriterium Checkbox-Liste

**Brief-Template:** `references/plan-brief-template.md`

**Output:** `~/.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

**Gate:** Plan-File existiert und ist > 3KB. Wenn nicht → GLM kurz nachfragen.

### Phase 3: Queen-Verify (~1-3 Min, Königin)

**Ziel:** Plan hat alle Quality-Gates, bevor M3 anfängt.

Die Königin prüft den GLM-Plan gegen die `better-plan-strategy` S1-S7 Checklist.

**Verify-Befehle** (siehe `references/queen-verify-checklist.md` für die
komplette Liste):

```bash
PLAN="$HOME/.hermes/plans/<plan-file>.md"
PASS=true

# S1: Realitäts-Status-Tabelle?
cnt=$(grep -c "Realitäts-Status\|Reality-Check" "$PLAN") || cnt=0
[ "$cnt" -ge 1 ] || { echo "❌ S1 fehlt"; PASS=false; }

# S3: Konkrete Minuten?
cnt=$(grep -cE "[0-9]+ Min" "$PLAN") || cnt=0
[ "$cnt" -ge 1 ] || { echo "❌ S3 fehlt"; PASS=false; }

# S5: Risiko-Sektion?
cnt=$(grep -cE "^###? R[0-9]" "$PLAN") || cnt=0
[ "$cnt" -ge 1 ] || { echo "❌ S5 fehlt"; PASS=false; }

# S6: Wave-Strategie?
cnt=$(grep -cE "Welle|Wave" "$PLAN") || cnt=0
[ "$cnt" -ge 1 ] || { echo "❌ S6 fehlt"; PASS=false; }

# S7: Done-Kriterium?
cnt=$(grep -cE "^- \[ \]" "$PLAN") || cnt=0
[ "$cnt" -ge 1 ] || { echo "❌ S7 fehlt"; PASS=false; }

$PASS && echo "✅ ALL GATES GREEN" || echo "❌ GATES FAILED"
```

**Gate-Verhalten:**
- ✅ Alle Gates grün → **Phase 4** (M3 execute)
- ❌ Gates fehlen → **zurück zu GLM** mit spezifischem Feedback (nicht "Plan ist schlecht", sondern "S3 fehlt: keine Minuten-Schätzungen, bitte ergänzen")
- ⚠️ Nur SSOT (S2) oder Atomic-Write (S4) fehlen → Königin kann selbst patchen (~30 Sek)

### Phase 4: M3 Execute (~10-30 Min, Workers)

**Ziel:** Tasks werden in Wellen ausgeführt, mit Queen-Verify zwischen jeder Welle.

Follow `subagent-driven-development` workflow. Für jede Welle:

#### 4a. Dispatch Wave

```python
# Welle 1 — parallele Bienen (Tasks aus Plan)
delegate_task(
    tasks=[
        {"goal": "Implement Task 1: <from plan>", "context": "<full task text + ANCHOR-TABLE + verification commands>"},
        {"goal": "Implement Task 2: <from plan>", "context": "<full task text + ANCHOR-TABLE + verification commands>"},
        {"goal": "Implement Task 3: <from plan>", "context": "<full task text + ANCHOR-TABLE + verification commands>"},
    ],
    role="leaf",
)
```

**Kompaktes Briefing (~60-70% der Draft-Länge):** Core goal (1 Satz), File-Pfade
+ Zeilennummern, Toolset-Restrictionen, Verification-Command. CUT: redundante
Beschreibungen, "as you know"-Kontext.

#### 4b. Queen-Verify Gate (zwischen Wellen)

Nach jeder Welle, **bevor** die nächste Welle dispatched wird:

1. **File-Existenz** der behaupteten Outputs prüfen: `ls -la <file>`
2. **Mnemosyne-Anchor-Verify** (Pitfall #36-Mitigation, 4/4 halluziniert am 2026-07-17):
   ```python
   # Subagent behauptet "Anker gesetzt mit ID abc123"
   verify = mnemosyne_get(memory_id="abc123")
   if verify["status"] != "ok":
       # Halluziniert — Königin setzt den Anker selbst
       mnemosyne_remember(content="...", importance=0.7)
   ```
3. **Done-Kriterien-Check** für diese Welle: `grep -c` auf die relevanten Checkboxen
4. **Spec-Compliance-Check**: Falls ein Heuristik/Detection-Task in der Welle war,
   laufe die Heuristik gegen **alle echten Files**, nicht nur Test-Fixtures

**Gate:**
- ✅ Grün → nächste Welle
- ❌ Rot → Fix-Subagent dispatchen mit spezifischem Feedback, dann re-verify
- ⚠️ Spec-Compliance zweifelhaft → `critic-gate` Script aufrufen (deterministisches Review)

#### 4c. Real-World Cross-Check (Heuristik/Detection-Tasks)

Für Tasks die klassifizieren, detektieren, parsen oder analysieren — zwingend
zusätzlich zum Wave-Verify:

```bash
# Inventarisiere die echte Variation in den Daten
find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20

# Laufe die Detection auf ALLEN echten Files
for f in $(find <target-dir> -name "*.md" | sort); do
    python3 <detection-script> --date "$(basename "$f" .md)" --json
done
# Vergleiche Output mit erwarteter Klassifikation, zähle Mismatches
```

Wenn Mismatches >0 → Fix-Subagent dispatchen mit kompletter Gap-Inventur.

### Phase 5: Review & Close (~2-3 Min, Königin)

**Ziel:** Alle Done-Kriterien erfüllt, Anker gesetzt, Task abgeschlossen.

1. **Done-Kriterien-Check** (S7 aus dem Plan):
   ```bash
   PLAN="$HOME/.hermes/plans/<plan-file>.md"
   unchecked=$(grep -cE "^- \[ \]" "$PLAN")
   checked=$(grep -cE "^- \[x\]" "$PLAN")
   echo "Done: $checked checked, $unchecked unchecked"
   ```

2. **Mnemosyne-Anker setzen** (falls noch nicht in Phase 4 geschehen):
   ```python
   mnemosyne_remember(
       content=f"### [YYYY-MM-DD] {task_name} completed via glm-plan-m3-execute\n...",
       importance=0.7,
       source="self-improving",
       veracity="verified"
   )
   ```

3. **Optional: Critic-Gate** für kritische Outputs:
   ```bash
   export HERMES_CRITIC_ENABLED=true
   cat input.json | python3 ~/.hermes/skills/software-development/critic-gate/scripts/critic-gate-ollama.py
   # PASS → Task done. RETRY → Fix-Subagent. FAIL → Eskalation.
   ```

4. **Review-Loop-Entscheidung** (siehe `references/review-loop-protocol.md`):
   - Alle Done-Kriterien ✅ → **CLOSE** task, berichten
   - Tasks failed → Feedback an GLM 5.2, Plan revidieren, zurück zu Phase 2
   - Heuristik-Drift → Fix-Subagent, zurück zu Phase 4

## Decision-Trees

### DT-1: Wann Reality-Check (Phase 1) überspringen?

```
Task erwähnt konkrete File-Pfade? ──── JA ───→ Reality-Check PFlicht
         │
         NEIN
         │
Task ist "baue was Neues" (kein existierendes File betroffen)?
         │
         JA ───→ Reality-Check auf Parent-Dirs, nicht auf Files
         │
         NEIN ───→ Reality-Check überspringbar, aber empfohlen
```

### DT-2: Wann Wave-Verify-Gate überspringen?

```
Task-Typ?
├── Heuristik / Detection / Klassifikation → Wave-Verify + Real-World Cross-Check (PFlicht)
├── Code-Implementation (TDD) → Wave-Verify (File-Existenz + Test-Run)
├── Dokumentation / Content → Wave-Verify (File-Existenz + Size-Check + Quality-Gates)
├── Recherche / Analyse → Wave-Verify (nur Mnemosyne-Anchor-Verify)
└── Trivial (Rename, Move, Config) → Wave-Verify überspringbar
```

### DT-3: Wann zurück zu GLM (Review-Loop)?

```
Queen-Verify Gate nach Welle N:
├── ✅ Alle Files existieren, alle Tests grün, alle Anker verifiziert → nächste Welle
├── ❌ File fehlt (Subagent halluziniert) → Fix-Subagent (gleiche Welle, kein GLM nötig)
├── ❌ Tests rot (Subagent hat Fehler eingebaut) → Fix-Subagent
├── ❌ Mnemosyne-ID halluziniert → Königin setzt Anker selbst (kein Subagent nötig)
├── ❌ Spec-Drift (Subagent baute was anderes als im Plan) → zurück zu GLM (Plan passt nicht)
└── ❌ Real-World Drift (Heuristik missklassifiziert) → Fix-Subagent + Real-World Cross-Check
```

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **GLM-Quota-Burn** | GLM 5.2 in einer Stunde 20% des wöchentlichen Kontingents verbraucht | GLM nur für Phase 2 (Planung) nutzen. Reality-Check (Phase 1) macht die Königin (M3). Review (Phase 5) macht M3 + optionales `critic-gate`. |
| **Reality-Check-Scope-Creep** | Königin inventarisiert das halbe System für einen 10-Minuten-Task | Scope-Limit: nur Pfade die der Task konkret berührt. Max 10 `test -f` Probes. |
| **Wave-Verify-Paralyse** | Jeder Wave-Verify wird zu einem Mini-Audit und kostet 10 Min | Wave-Verify = 3 Befehle max (`ls`, `mnemosyne_get`, `grep`). Wenn ein Fix nötig ist → Fix-Subagent, nicht Königin-manuelle-Reparatur. |
| **Subagent-Briefing-Monolog** | Briefing ist 2000 Wörter lang und kostest mehr Token als die eigentliche Arbeit | Kompaktes Briefing: ~60-70% der Draft-Länge. Siehe `subagent-driven-development` Delegation Prompt Efficiency. |
| **Mnemosyne-Halluzination nicht abgefangen** | Subagent behauptet "Anker gesetzt mit ID abc123", Königin glaubt es | `mnemosyne_get(memory_id="abc123")` ist nicht verhandelbar. Siehe Pitfall #36 in `subagent-driven-development`. |
| **Atomic-Write ignoriert** | Task editiert Frontmatter und Body in zwei separaten `patch`-Calls, User editiert dazwischen | S4 Atomic-Write Policy: ein `write_file`-Call für die komplette Datei, nicht zwei `patch`-Calls. |
| **Heuristik-Subagent Self-Report blind vertraut** | Subagent meldet "6/6 Tests grün" aber Tests decken nur die Plan-Template-Variante ab | Real-World Cross-Check (Phase 4c) ist nicht verhandelbar für Heuristik-Tasks. Siehe Pitfall #39. |
| **Review-Loop ohne Fix-Subagent** | Königin versucht das Problem selbst zu fixen, context-pollution | Immer Fix-Subagent. Königin bleibt clean. |
| **Fallback-Cursor-Drift** | Die Pipeline startet auf Modell X (z.B. M3), aber ein Provider-Timeout während Phase 1 löst `try_activate_fallback()` aus — die Königin arbeitet plötzlich auf einem anderen Modell (GLM 5.2 oder lokal). Der Planer in Phase 2 wird dann nicht mehr via `plan-glm` (explizites GLM) sondern direkt von der Königin geschrieben. | Vor Phase 1 `_fallback_activated` prüfen. Wenn aktiv und das Modell unerwartet ist: kurz evaluieren ob die Pipeline noch korrekt läuft (Königin-Plan≠GLM-Plan kann Quality-Gates verlieren). Siehe `hermes-admin` → `references/hermes-fallback-chain.md`. |
| **Plan-Annahme-Drift bei mehrtägiger Ausführung** | Plan wurde am Tag 1 geschrieben, Filesystem hat sich bis Tag 3 geändert | Phase 1 Reality-Check vor JEDEM Dispatch neu laufen lassen, nicht nur beim ersten. Filesystem driftet. |

## Cross-References

| Baustein | Skill | Was er in dieser Pipeline macht |
|---|---|---|---|
| `plan-glm` | `software-development/plan-glm` | Phase 2: Spawnt GLM 5.2 als Subprozess, schreibt Plan nach `~/.hermes/plans/` |
| `better-plan-strategy` | `software-development/better-plan-strategy` | Phase 3: Die S1-S7 Quality-Gate Checklist |
| `subagent-driven-development` | `software-development/subagent-driven-development` | Phase 4: Wellen-Dispatch, 2-stage review, Mnemosyne-Verify |
| `critic-gate` | `software-development/critic-gate` | Phase 4b/5: Deterministisches JSON-Gate via lokalem Ollama |
| `post-plan-queen-verify` | `plan-glm/references/post-plan-queen-verify.md` | Phase 1+3: 3-Fragen-Regel + strukturierte Checkliste |
| `self-improving` | `meta/self-improving` | Pitfalls #36-#44 (Subagent-Halluzination, Self-Report, Heuristik-Drift) |

## Further Reading (load when relevant)

- `references/plan-brief-template.md` — Das erweiterte Brief-Template für GLM 5.2
- `references/queen-verify-checklist.md` — Konkrete `grep`/`ls`/`mnemosyne_get` Befehle
- `references/review-loop-protocol.md` — Wann zurück zu GLM, wann Fix-Subagent, wann Cross-Check
