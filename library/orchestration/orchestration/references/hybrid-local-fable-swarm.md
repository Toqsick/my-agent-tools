# Hybrid Local + Fable 5 Swarm Pattern

Kombiniert lokale Subagenten (Messung, free) mit Fable 5 Calls (Judgment/Triage, ~$0.30/Call)
für optimale Kosten/Nutzen-Verhältnisse in Analyse-Aufgaben.

Basti verwendet "Fable 5" als Namen für Claude Haiku im Triage-Modus.

## Das Muster (5-Phasen)

```
Phase 0:   Inventur (read-only, selbst) → Ist-Zustand erfassen
Phase 0.5: User-Entscheidungsmatrix (A/B/C/D Optionen aus Phase 0)
Phase 1a:  Lokale Subagenten (delegate_task, terminal+file toolsets, Messung)
Phase 1b:  Fable 5 Calls (via Claude CLI, structured markdown briefing, Judgment)
Phase 2:   Cross-Check (Subagent-Messung vs Fable-Judgment validieren)
Phase 3:   Synthese + Masterplan (Queen konsolidiert)
Phase 4:   Execution mit Basti-Freigabe pro Schritt
```

## Kostenmatrix

| Worker | Kosten | Stärke | Einsatz |
|--------|--------|--------|---------|
| Lokaler Subagent (MiniMax M3) | Free/API | Messung (Diffs, Listings, File-Scans, Status) | Read-only Analyse |
| Fable 5 (Claude Haiku via Pro) | ~$0.30/Call | Judgment (Klassifikation, Priorisierung, Empfehlung) | Triage, Entscheidungsvorlage |
| Queen (aktuelles Modell) | Kontextgebunden | Synthese, Cross-Check, Finaler Plan | Koordination |

## Wann verwenden

- **Duplikat-Resolution**: 2+ lokale Clones des gleichen Remote-Repos analysieren
- **Fork-Cleanup**: 20+ Forks nach KEEP/ARCHIVE/DELETE sortieren
- **Bestandsaufnahmen**: Repo-Inventur → User-Entscheidungsmatrix → Execution
- **Jeder Task wo Judgment + Messung getrennt werden können**

## Dispatch-Pattern

```python
# Phase 0: Inventur (selbst machen)
# → Repo-Liste, Dirty-Status, letzte Commits erfassen

# Phase 0.5: User-Entscheidungsmatrix
# → A1/A2/A3, B1/B2/B3, C1/C2/C3 Optionen → Basti wählt

# Phase 1a: Lokale Subagenten (Messung) — parallel
delegate_task(tasks=[
    {"goal": "Read-only Analyse", "context": "...", "role": "leaf"},
])

# Phase 1b: Fable 5 Calls (Judgment) — via Background-Terminal, parallel
write_file(path="fable-brief.md", content="""# Fable 5 Triage: ...

## Input
... (Daten, Fakten, Limits)

## Aufgaben
1. ...
2. ...

## Output-Format
- Empfehlung (1 Satz)
- Aufwand (Min/Std/Tage)
- Nutzen (⭐ 1-5)
- Risk (niedrig/mittel/hoch)
""")

terminal(
    command='claude -p "$(cat fable-brief.md)" --model claude-haiku-4-5 --max-turns 3 --max-budget-usd 0.30 --output-format json --bare > out.json',
    background=True, notify_on_complete=True
)

# Cross-Check: Subagent-Messung vs Fable-Judgment validieren
# Synthese: Alle Outputs → MASTERPLAN.md
```

## Pitfalls

1. **Fable bekommt KEINEN Dateizugriff** — nur das Briefing als Input.
2. **Fable parallel starten** — 3× $0.30 parallel in einen Batch.
3. **Immer `--bare` setzen** — sonst $0.05 Cache-Kaltstart extra.
4. **Budget $0.30 für 3-Turn Triage** — Deep-Dive >$0.50.
5. **Cross-Check Pflicht** — Subagent misst, Fable schätzt. Beide validieren.
6. **Struktur-Output** — `--output-format json` für parsebare Resultate.
7. **⚠️ `claude models` ist KEIN CLI-Subcommand** — `claude models list` startet einen interaktiven Dialog. Claude Code hat keinen `models` Subcommand. Modelle per `--model` setzen. Infos: `claude --help` oder Anthropic-Docs.
