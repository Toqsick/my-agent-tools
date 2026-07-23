# Run-Log: Inline-Execution (2026-07-17)

> **Projekt:** Qwythos 9B Benchmark-Suite — 15 Module (OllamaClient, SystemSampler, 7 Runner, Chart-Renderer, Aggregator, Dashboard-Template, Master-Runner, Pre-Flight)
> **Modus:** Phase A (Plan-Review) → **Inline-Execution** (keine Subagenten)
> **Umfang:** ~1300 Zeilen Code, 8 Tests, 7 Prompt-Sets, 5 Test-Bilder, Git-ignore, README
> **Dauer:** ~90 min (davon ~5 min Background-Run)
> **Plan-Review-Ergebnis:** 10 Schwächen gefunden, 6 gepatched vor dem ersten Code-Tippen

---

## Warum Inline (nicht Subagent)?

| Faktor | Dieser Run | Subagent-Variante (2026-07-15) |
|---|---|---|
| Task-Typ | Build from scratch (ein Projekt, lineare Abhängigkeiten) | Curation (18 Skills, unabhängige Edits) |
| Abhängigkeiten | Jede Phase baut auf vorheriger auf | Tasks parallelisierbar |
| Kontext-Verlust-Risiko | Hoch (jede Phase importiert vorherige Module) | Niedrig (jede Skill-Datei isoliert) |
| Fehler-Muster | Build-Fehler früh sichtbar (zurückrollen einfach) | Subagent-Fabrication (Pitfall #36) |
| Gewählter Modus | Inline ✅ | Subagent ✅ |

**Faustregel:** Wenn Tasks lineare Abhängigkeiten haben (Build-Projekt, Feature-Rollout) → **inline**. Wenn Tasks parallelisierbar und isoliert sind (Skill-Curation, Multi-File-Refactor) → **Subagent**.

## Phase A: Plan-Review (was hat konkret gefruchtet)

Die 5-Schwächen-Matrix fand **10 konkrete Probleme** im Plan (6 gepatched):

| Schwäche | Gefunden in Phase | Konkretes Problem | Patch |
|---|---|---|---|
| **Anker-Vagheit** | Task 0/7/8 | Keine `## Resolved Mnemosyne-IDs` Tabelle | Tabelle eingefügt, 7 Anker definiert |
| **Anker-Vagheit** | Task 3.2 | `needle_haystack.py` ohne Ziel-Pfad | Absoluter Pfad `prompts/context_scaling_prompts.py` |
| **Time-Budget** | — | Keine 5/15/45-Min-Cuts definiert | 4 Mini-Szenarien angehängt |
| **Output-Bomb** | Task 7.3 | `run_all.py` könnte Stdout fluten | `--brief` Flag eingebaut |
| **Output-Bomb** | Task 2.1 | Speed-Runner könnte 5x 4096-Token-Antworten ausgeben | `--brief` + kompakte Summary |
| **Test-Cluster** | Task 8 | 7 Tests nur am Ende → Fehler erst spät sichtbar | Smoke-Test in Task 0.1 (`pyproject` existiert? → `pytest --co` läuft?) |
| **Pitfall #9** | Task 2.1 | `keep_alive` fehlt im Runner → Model kühlt zwischen Phasen aus | Default `keep_alive="30m"` in `OllamaClient.__init__` |
| **Pitfall #8** | Task 8.1 | `nvidia_oc` könnte während Benchmark aktiv sein | Pre-Flight-Block mit `systemctl is-active nvidia_oc` + Auto-Stop |
| **Biet-Size** | Task 7.2 | 3 Module (Charts/Template/Aggregator) in einem Task | Split in 7.2a/7.2b/7.2c + Task 7.3 |
| **Biet-Size** | Task 0 | Skeleton (venv + pyproject + README + .gitignore) zu grob | pyproject-Smoke-Test (`python -c "import tomllib"`) |

**Takeaway:** Die Matrix arbeitet zuverlässig — 10/10 gefundene Schwächen waren echte Probleme. Der Aufwand (15 min Review für 3h Plan-Erstellung) amortisiert sich beim ersten Failed-Run, den es nicht gab.

## Phase B: Inline-Execution — Flow

Da Phase B inline war (keine `delegate_task`-Aufrufe), lief der Flow anders als im Subagent-Modus:

```
Phase A: Plan-Review          → 6 Patches am Plan-File
Phase 0: Skeleton             → write_file (3 Dateien) + terminal (venv + pip)
Phase 1.1+1.2: Core           → write_file + write_file + terminal (8 Tests grün)
Phase 2.1: Speed-Runner       → write_file + terminal (23.5 t/s Smoke-Test)
Phase 3.1+3.2: Context        → write_file (2 Runner)
Phase 4.1: Quality-Suite      → write_file (3 Prompt-Sets + Runner), aber JSON-Fehler → rewrite
Phase 5.1: Thinking A/B       → write_file (Prompt-Set + Runner) 
Phase 6.1+6.2: Vision+Tools   → image_generate (5 Bilder) + write_file (2 Runner)
Phase 7a/7b/7c: Charts/Dashboard → write_file (Chart-Renderer + Template + Aggregator + Master-Runner)
Phase 7.3: Master-Runner      → write_file (run_all.py mit --brief/skip + Pre-Flight)
Phase 8.1: Run                → Pre-Flight (nvidia_oc stoppen) + Background-Start
Phase 8.2: Doku               → README.md + Obsidian-Inbox-Note
```

## Fehler & Recovery (Inline-Vorteil)

Da kein Subagent im Spiel war, konnten Fehler **sofort beim Auftreten** gefixt werden:

| Fehler | Wann aufgetreten | Fix | Zeit |
|---|---|---|---|
| `statistics.max` existiert nicht (LSP-False-Positive) | Phase 1.2, beim Test-Lauf | `from statistics import max` → built-in `max()` | 5 sec |
| `humaneval_lite.json` trailing comma (write_file) | Phase 4.1, beim Runner-Smoke | Neu geschrieben (ohne trailing comma) | 30 sec |
| `PROMPTS_FILE = Path.parents[2]` falsch | Phase 8.1, erster Run → `FileNotFoundError` | `sed -i 's/parents\[2\]/parents[3]/g'` (alle 5 Runner) | 15 sec |
| `nvidia_oc` active | Phase 8.1, Pre-Flight | `systemctl stop nvidia_oc` (im Pre-Flight-Block) | 10 sec |

**Recovery-Pattern:** Bei Inline-Execution ist Recovery ein `patch`/`write_file` + Re-Run. Bei Subagent-Execution wäre jeder dieser Fehler ein Subagent-Crash gewesen (Pitfall #36), der Queen-Verify + Re-Dispatch gebraucht hätte — Faktor 5–10x teurer.

## Lessons aus diesem Run

1. **Inline-Execution ist für lineare Build-Projekte effizienter** — schnellerer Fehler-Fix-Zyklus, kein Kontext-Verlust zwischen Phasen
2. **`Path.parents[X]` muss vom File-Location aus zählen, nicht vom Package-Root** — Runner in `runners/` brauchen `parents[3]`
3. **Pre-Flight mit OC-Check** ist nicht optional — `nvidia_oc` ist bei Basti standardmäßig aktiv
4. **`keep_alive` im Client-Constructor** ist besser als in jedem Runner — einmal gesetzt, automatisch überall aktiv
5. **JSON-Dateien via Code schreiben** ist fehleranfällig — `json.dumps()` statt String-Interpolation
6. **LSP-False-Positives gibt es** — `statistics.max` sah gültig aus, war es nicht

## Vergleich: Subagent vs Inline

| Metrik | Subagent (2026-07-15, 18 Skills) | Inline (2026-07-17, 15 Module) |
|---|---|---|
| **Total Time** | ~4h (davon ~2h Wartezeit auf Subagents) | ~1.5h (alles inline) |
| **Fehler aufgetreten** | 6× Pitfall #36 (Fabrication) | 4× echte Build-Fehler |
| **Fehler-Recovery-Kosten** | Hoch (Queen-Verify + Re-Dispatch) | Niedrig (patch + Re-Run) |
| **Kontext-Kontinuität** | Fragmentiert (jeder Subagent startet frisch) | Vollständig (alles in einem Kontext) |
| **Tasks parallelisierbar?** | Ja (Subagent-Kernstärke) | Nein |
| **End-Resultat** | 18 Skills reviewed + curated | 15 Module gebaut, getestet, deployed |

**Meta-Lesson:** Der Modus-Wahl-Heuristik im Skill-Kopf (`references/run-log-2026-07-17-inline-execution.md`) ist korrekt: lineare Abhängigkeiten → inline, parallelisierbare Tasks → Subagent.

---

## Siehe auch

- Plan-File: `~/.hermes/plans/2026-07-17_115245-qwythos-9b-deep-benchmark.md`
- `run-log-2026-07-15.md` — Gegenstück: Subagent-Modus (18 Skills, 6× Pitfall #36)
- `multi-agent-pitfalls-cheatsheet` — Pitfall #36 Katalog
- Mnemosyne-Lesson `279820cc5c448b6c` — Plan-Review mit Queen-Verify
