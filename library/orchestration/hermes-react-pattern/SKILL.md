---
name: hermes-react-pattern
description: |
  Use when making a Hermes tool loop explicitly follow ReAct, adding structured Thought-Action-Observation cycles, or inserting reflection and gate decisions into agent workflows.
  NOT for exposing private chain-of-thought, simple one-step tool calls, or replacing Hermes native tool execution with a separate reasoning framework.
  Defines an observable ReAct control pattern that integrates reflection, Queen and worker roles, verification gates, and concise state summaries.
version: 1.0.0
author: Yuno for Basti (evaluiert aus Context-Engineering-Literatur)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - react
    - reflexion
    - agent-loop
    - reasoning
    - self-correction
    related_skills:
    - multi-agent-master-workflow
    - critic-gate
    - hermes-agentic-patterns
    - hermes-context-budget
    lane: koenigin
    reasoning_effort: high
trigger_keywords: ['tool', 'hermes', 'react', 'thought', 'reflection']
keywords: ['tool', 'hermes', 'react', 'thought', 'reflection']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-mcp-integration', 'multi-agent-master-workflow']
---


# Hermes ReAct Pattern

Hermes Tool-Loop ist nativ ReAct-kompatibel. Dieser Skill macht das Pattern **explizit** — mit klaren Labels (Thought/Action/Observation), strukturierter Reflexion und nahtloser Integration in Queen/Worker/Gate.

## Trigger

Dieser Skill feuert automatisch bei:
- "react" / "reasoning loop" / "agent loop"
- "reflexion" / "self-check" / "self-correction"
- Einem Task der **voraussichtlich >5 Tool-Calls** braucht (längere Recherche, Debugging-Ketten, mehrstufige Builds)
- Vor jedem `delegate_task`-Dispatch (damit Subagenten das Pattern vom Queen geerbt bekommen)

## Das ReAct-Etikett

Statt des rohen Tool-Loops wird jeder Durchlauf so etikettiert:

```
Thought: [Reasoning — was weiss ich, was brauche ich, welches Tool passt?]
Action: [Tool-Name und Parameter]
Observation: [Tool-Ergebnis — vom Orchestrator / Queen eingesetzt]
Thought: [Analyse des Observations — nächster Schritt]
...
Final Answer: [Abschluss des Teil-Tasks]
```

**Wichtig**: Bei Hermes kommen `Observation` und der nächste `Thought` in den gleichen Turn — die Tool-Rückgabe ist Observation, dann antwortest du mit dem nächsten Thought.

### Template-Snippet (aktiv beim Task-Start)

```
╔═══════════════════════════════════════════╗
║  ReAct-Loop aktiv — etikettiere jeden     ║
║  Schritt als Thought → Action → Obs       ║
║  ⚠ Kein Action ohne voriges Thought      ║
║  ⚠ Kein Obs ohne voriges Action-Result   ║
╚═══════════════════════════════════════════╝
```

## Reflexion (Self-Correction) — optionales Upgrade

Nach jedem **grösseren Schritt** (3-5 Tool-Calls oder vor einem Gate) reflexionieren:

```
╔═══════════════════════════════════════════╗
║  REFLEXION-SLOT                           ║
║  [ ] Adressiert der Output vollständig    ║
║      das ursprüngliche Ziel?              ║
║  [ ] Gibt es Behauptungen ohne Beleg?     ║
║  [ ] Fehlen Constraints aus der Aufgabe?  ║
║  [ ] Würde ein Reviewer das so abnehmen?  ║
║  → Wenn Lücke: korrigieren + dokumentieren║
╚═══════════════════════════════════════════╝
```

Reflexion lohnt sich für:
- **Analyse- & Research-Tasks** (Qualitätssteigerung ~30%)
- **Reports & Doku** (verhindert Halluzinationen)
- **Gate-Vorbereitung** (Reviewer A/B simulieren)
- Bei **Time-Pressure** (kurze Tasks) kann Reflexion übersprungen werden

## Integration mit Hermes-Komponenten

| Hermes-Komponente | Rolle im ReAct-Loop |
|---|---|
| **Queen** (Yuno) | Startet ReAct, setzt Reflexion-Slots, führt Gate aus |
| **Worker** (Subagent via `delegate_task`) | Bekommt ReAct-Muster ins Briefing → arbeitet im selben Loop |
| **Gate** (Verifier / critic-gate) | Prüft Reflexion-Output, besteht auf vollständiger Kette |
| **Tool-Loop** (nativ Hermes) | Liefert Observations — kein eigener Code nötig |

## Wann NICHT

- **Single-Step-Tasks** (echo, date, einfache read_file) — Overkill
- **User will Speed** — Reflexion deaktivieren, ReAct-Labels optional
- **Nur Konversation** (kein Tool-Einsatz) — Labels stören den Fluss

## Pitfalls

1. **Thought überspringen**: Direkt Action ohne Thought → Tool-Auswahl ratlos. Hermes' eigener Tool-Loop verhindert das teilweise, aber bei `delegate_task`-Briefings explizit fordern.
2. **Reflexion-Schleife**: Mehrere Reflexion-Durchgänge ohne Fortschritt → nach 2. Reflexion harter Cut und Entscheidung (weiter mit bestem Stand).
3. **Observation-Halluzination**: Nie Observation selbst schreiben — das Feld ist dem Tool-Output vorbehalten. Bei Hermes nativ abgesichert (Tool-Result = Observation).
4. **Labels in Subagent-Briefings**: `delegate_task` bekommt andere Format-Konventionen — im Briefing ReAct als "Arbeite in Thought→Action→Observation" beschreiben, nicht als ASCII-Art.
