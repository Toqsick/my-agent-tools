# Parallele Subagenten mit Hidden Dependency — Race Condition Pattern

> **Beobachtet:** 2026-07-04 (Hermes-v7 SecurityKernel PR #7)
> **Kontext:** Biene A fixte `orchestrator.ts` + `tool-profiles.ts`, Biene C schrieb PR-Body parallel
> **Problem:** Biene C reportete **bevor** Biene As Fix fertig war → PR-Body enthielt "4/5 Tests grün" statt finalem "21/21"

## Kernproblem

`delegate_task(tasks=[...])` dispatched alle Subagenten **gleichzeitig**.
Wenn Subagent B inhaltlich von Subagent A abhängt (B's Deliverable referenziert A's Output),
gibt es zwei ungelöste Koordinationsprobleme:

1. **Race:** B wird **vor oder gleichzeitig mit A** fertig → B's Report basiert auf dem **Pre-Fix-Zustand**
2. **Kein Wait-Mechanismus:** Subagenten können nicht auf andere Subagenten warten — sie sehen nur den initialen Context

## Erkennung

Du hast einen Hidden-Dependency-Race wenn:
- Zwei delegate_task-Ergebnisse dicht beieinander eintreffen
- Ein Subagent referenziert etwas, das ein anderer Subagent fixen sollte
- Der schnellere Subagent ist VOR dem langsameren fertig → schnellerer hat den alten Stand
- Subagent sagt transparent: "basierend auf Annahme dass Fix X durch ist"

## Lösungsstrategien

### Strategie A: Sequentialisierte Wellen (empfohlen)

```python
# Welle 1: Unabhängige Tasks parallel
tasks_wave1 = [
    {"goal": "Fix orchestrator.ts: PHASE_ROLE_MAP + tool-profiles.ts ergänzen",
     "context": "...",
     "toolset": ["terminal", "file", "code_exec"]},
    {"goal": "Unabhängige Recherche zu Thema Y",
     "context": "..."},
]

# Welle 2 (nachdem Welle 1 zurück ist):
tasks_wave2 = [
    {"goal": "PR-Body schreiben basierend auf Welle 1 Output",
     "context": "A hat orchestrator.ts gefixt (21/21 Tests grün). Schreib PR-Body mit korrektem Endstand."},
]
```

**Vorteile:**
- Jede Welle baut auf der letzten auf
- Parent kann Zwischenergebnisse checken
- Klarer Audit-Trail
- Kein post-hoc Merge nötig

### Strategie B: Post-hoc Cross-Verification (wenn parallel bereits dispatched)

Wenn dispatch schon passiert ist und du Races bemerkst:

1. **Beide Berichte sammeln** — sie kommen asynchron als separate Nachrichten
2. **Timeline checken:** Wer kam wann? Wer referenziert wessen Output?
3. **Merge:** Parent kombiniert A's Fix + B's (korrigierten) PR-Text
4. **Verifikation:** `ls <output_path>` + Inhalt auf Korrektheit checken

### Strategie C: Transparenz-Marker im Subagent-Briefing

Zum Context jedes Subagenten hinzufügen, der von anderen abhängt:

```
WICHTIG: Dieser Task läuft parallel zu anderen Subagenten. 
Wenn du unsicher bist ob ein abhängiger Fix schon existiert,
markiere deine Annahmen explizit als "⚠️ ANNAHME: ...".
Der Parent merged die Ergebnisse nach Abschluss.
```

## Der Fall aus der Praxis (2026-07-04)

**Dispatch:** Biene A + Biene C parallel (2 Tasks im selben `tasks=[...]` Call)

**Timeline:**
1. Biene C wird fertig (ca. 2 Min) — schreibt PR-Body mit "[...] 4/5 Tests fallen noch um"
2. Biene A wird fertig (ca. 3 Min) — hat `PHASE_ROLE_MAP` gefixt, `tool-profiles.ts` erweitert → **21/21 Tests grün**
3. 🚨 PR-Body in C's Output ist **stale** — basiert auf dem Stand BEVOR A's Fix deployed war

**Lösung (post-hoc):**
- Biene C hatte transparent ihr "4/5" Dilemma dokumentiert → sofort erkennbar als pre-Fix-Zustand
- Parent hat C's PR-Body-Entwurf + A's Fix-Summary kombiniert → korrekter PR-Text
- Final: **PR #7 mit "21/21 Tests grün"** — post-hoc korrigiert

**Lessons:**
1. Biene C hat gut gearbeitet (transparente Berichterstattung) — Problem war die **Parallel-Order**, nicht C's Qualität
2. Die Transparenz ("ich nehme an dass...") machte den Race sofort erkennbar
3. Hätte ich sequentiell dispatched (Welle 1: A allein → Welle 2: C), wäre der Fehler nie passiert

## Anti-Patterns

| Anti-Pattern | Warum schädlich |
|---|---|
| C einfach nochmal dispatchen | Gleicher Input → gleicher Output |
| Beide Outputs 1:1 mergen | Übernimmt C's pre-Fix-Daten ungeprüft |
| C nach A erneut dispatchen mit "korrigier deinen PR-Body" | doppelter Token-Verbrauch + Inkonsistenz-Risiko |
| Annahme dass `tasks=[...]` sequentiell dispatched | **Tut es nicht** — die Reihenfolge ist nicht deterministisch |

## Workflow-Integration

### In `multi-agent-code-gen-pipeline`:
- **Phase 1 (Coding) → Phase 4 (Fix) → Phase 3 (Pattern-Scan):** Die Reihenfolge ist bereits korrekt sequentiell (1→2→3→4→5), kein Race-Problem
- **Innerhalb Phase 1 (5 Coding-Agenten parallel):** Keine Abhängigkeiten untereinander → kein Race-Problem
- **Aber:** Wenn Phase 4 (Fix) einen PR-Body schreiben soll der Phase-5 (Build)-Ergebnisse referenziert → **sequentialisieren!**
- **Faustregel:** Innerhalb einer Phase → parallel (= keine Dependencies). Phasenübergreifend → sequentiell (= Dependencies möglich)

### Dispatch-Entscheidungsmatrix

| Task-Typ | Dispatch | Grund |
|---|---|---|
| Unabhängige Recherche/Scans parallel | `tasks=[...]` parallel | Keine Dependencies |
| Fix + PR-Body für denselben Fix | **Nacheinander** | PR-Body braucht Fix-Ergebnis |
| Research + Deploy | parallel | Research ist read-only, Deploy kann warten |
| Pattern-Scan + Fix | Nacheinander | Fix braucht Scan-Ergebnisse |
| Build + Report | Nacheinander | Report braucht Build-Ergebnisse |
