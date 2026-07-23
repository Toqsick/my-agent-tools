---

name: task-weight-routing
description: Use when user asks for task weight routing, Task-Weight Routing — Orchestrator Model- & Budget-Policy, Konzept, Einsatzkontext. NOT for unrelated tasks, simple questions. Routes coding tasks to cloud agents based on task weight and budget policy.
version: 1.2.0
author: Yuno (Basti's Assistant)
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - Model-Routing
    - Budget-Control
    - Orchestration
    - Claude-Code
    - Task-Routing
    related_skills:
    - claude-code
    - codex
    - opencode
    - model-selector
    - autonomous-ai-agents
    scope: companion to bundled 'claude-code' skill (which cannot be edited); this
      skill captures Basti-specific routing rules the bundled skill cannot hold
trigger_keywords: ['task', 'weight', 'routing', 'budget', 'policy']
keywords: ['task', 'weight', 'routing', 'budget', 'policy']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['board-policy']
---



# Task-Weight Routing — Orchestrator Model- & Budget-Policy

## Konzept

Routing-Policy für den Orchestrator: basierend auf **Task-Gewicht** (Heavy/Medium/Light) + **User-Trigger** entscheidet Yuno:

- **Welches Modell** (`--model`)
- **Welches Budget** (`--max-budget-usd`)
- **Wieviele Turns** (`--max-turns`)
- **Batch oder Einzel-Delegation**

## Einsatzkontext

Dieser Skill ergänzt die Bundled-Skills `claude-code`, `codex`, `opencode` mit einer **Orchestrator-Policy-Schicht**.  
Der Bundled-Skill sagt *wie man das CLI bedient*. Dieser Skill sagt *wann/wie viel Budget/welches Modell*.

## Signal-Definition

### Task-Gewichtung

| Gewicht | Typische Tasks | Max-Budget | Max-Turns | Modell-Strategie |
| ------------- | ---------------- | ----------- | -------------- | -- |
| 🔴 Heavy | Multi-File Refactor, Security-Audit, Big-Coding | **Fable 5: KEIN Limit** (Rabat) / Sonst $0.80-$2.00 | **Fable 5: KEIN Limit** / Sonst 15-30 | Rabat-Modell priorisieren wenn verfügbar |
| 🟡 Medium | Single-File Refactor, Code-Review, Test-Writing | $0.50 | 10 | Sonnet 5 (Default) |
| 🟢 Light | Mini-Edit, Bug-Search, Lookup | $0.20 | 5 | Haiku 4.5 |

### User-Trigger → Routing (Basti-spezifisch)

| Basti sagt | Yuno routet | Budget/Turns | Begründung |
|------------|-------------|--------------|------------|
| "mit Fable" / "mit Fable 5" | Fable 5 (Rabat) | **KEIN Limit** — Basti will Volle Power | 50% Rabat bis 7.7. — nutzen solange Fenster offen |
| "mit Sonnet" / "Sonnet 5" | Sonnet 5 | $0.50 / 10 Turns | Standard für normale Refactor-Aufgaben |
| "mit Opus" / "Opus 4.8" / "OPUS high" | Opus 4.8 | $2.00 / 30 Turns (high reasoning) | Critical/Architecture, sparsam verwenden |
| "nicht geizig" / "hau rein" / "kein limit" | **Alle Modelle: KEIN Budget-Limit** | KEIN `--max-budget-usd`, KEIN `--max-turns` (oder 15 Min) | Override für Speed — Basti will Ergebnisse, nicht Sparsamkeit |
| "Rollout!" / "Vollgas!" / "GO" | Priorisiere Speed + Parallelität | KEIN Vorab-Limit | Unmittelbare Aktion — keine Klärungsrunde |
| (kein Trigger) | Auto-Route | Auto | Yuno entscheidet anhand des Task-Texts |

## Implementierung

### CLI-Aufruf-Bauplan (für jeden Coding-Agent-CLI)

**Generelle Struktur (Sonnet/Haiku/Opus — immer mit Limits):**
```python
cmd = (
    f"claude -p '{task_description}' "
    f"--model {model_alias} "
    f"--max-turns {budget_policy.max_turns} "
    f"--max-budget-usd {budget_policy.max_budget}"
)
terminal(command=cmd, workdir=workdir, timeout=timeout)
```

**Fable 5 Rabat-Sonderfall (KEINE Limits — Basti's Anweisung):**
```python
if model_alias == "fable" and RABAT_AKTIV:
    # KEIN --max-turns, KEIN --max-budget-usd
    cmd = f'claude -p "$(cat /tmp/briefing.txt)" --model fable'
    terminal(background=True, notify_on_complete=True,
             command=cmd, timeout=300)
```

### Policy-Definition als Dict (zur Laufzeit)

```python
POLICY = {
    "fable": {"budget": None, "turns": None,
              "desc": "Heavy — Rabat-Modell (KEINE Limits laut Basti)"},
    "sonnet": {"budget": 0.50, "turns": 10,
               "desc": "Medium — Normale Refactors"},
    "opus": {"budget": 2.00, "turns": 30,
             "desc": "Heavy+ — Critical/Architecture (sparsam)"},
    "haiku": {"budget": 0.20, "turns": 5,
              "desc": "Light — Mini-Edits"},
}
}

## Fable 5 Briefing-Format (80% Output-Fokus)

Wenn Fable 5 delegiert wird, das Briefing **output-zentriert** halten (nicht Kontext-heavy):

```
## TASK: <Eindeutiger Titel>
INPUT: <Scope, Pfade, Tiefenbeschränkung>
OUTPUT-FORMAT (max N Zeilen, Markdown):
  | Spalte | Spalte | Beschreibung |
  | ...    | ...    | ...          |
CONSTRAINTS:
  - Read-only (KEIN rm/mv/mkdir) wenn angezeigt
  - Deutsch antworten
  - KEIN Limit — Basti will volle Rabat-Power
```

**Pattern:**
```bash
# Briefing vorbereiten, dann direkt delegieren
claude -p "$(cat /tmp/briefing.txt)" --model fable 2>&1 | tee /tmp/result.txt

# Background mit notify (fuer >30s Tasks)
terminal(background=true, notify_on_complete=true,
         command='claude -p "$(cat /tmp/brief.txt)" --model fable', timeout=180)
```

**Anti-Pattern (live gescheitert am 2026-07-04):**
- ❌ `cat briefing.txt | claude -p ...` — Self-Pipe-Bug, Budget verbrannt ohne Output
- ❌ `--max-budget-usd 0.50` bei N-skalierten Tasks (298 Skills) — Sprengt Budget
- ❌ `--max-turns 3` bei File-Scan-Tasks — Zu wenig für read-heavy Analyse

## Trigger-Resolutions-Regeln

1. **Basti sagt "mit <Alias>"** → Yuno wählt `POLICY[alias]` und setzt Budget + Turns (Fable: KEINE)
2. **Kein Trigger** → Yuno analysiert Task-Text auf Gewicht:
   - Enthält "refactor", "audit", "security", "multi-file", "architect" → Medium (präferiert)
   - Enthält "fix", "edit", "change" (single-line/scoped) → Light
   - Enthält "critical", "architecture", "big" → Heavy+
3. **Rabat-Aktionsfenster aktiv** → Falls ein Modell Rabat hat, **priorisieren** für alle Heavy-Tasks. Fable 5 bekommt KEINE Limits.
4. **Budget-Exceptions:** Sonst gilt "Immer `--max-budget-usd` und `--max-turns`" — aber Fable 5 (Rabat) hat **gegenteilige Regel**: KEIN Budget, KEIN Limit, auf Basti's Anweisung.

### OPUS: Reasoning-Level beachten

| Basti sagt | Yuno setzt | Budget/Turns | Begründung |
|---|---|---|---|
| "OPUS high" | `claude --model opus` (ohne `--reasoning`) | $2.00 / 30 Turns | **NIE `--reasoning xhigh`** — Basti will "high", nicht xhigh |
| "OPUS xhigh" | `claude --model opus --reasoning xhigh` | $2.00 / 30 Turns | Nur bei explizitem "xhigh" |

Standard bei `--model opus` ist bereits `reasoning high`. `xhigh` vervierfacht die Kosten bei marginalem Qualitätsgewinn.

### Fable vs OPUS: Audit-Depth-Comparison

Bei Analyse-Aufgaben mit leseintensiven Scans (Skill-Library, Dateisystem, Codebase):

| Aspekt | Fable 5 (Rabat) | OPUS 4.8 high |
|---|---|---|
| Geschwindigkeit | ~2-5 Min | ~8-17 Turns / ~5-15 Min |
| Kosten | ~$0.30-0.50 | ~$0.55-0.75 |
| Claims | Heuristisch — übersieht Nuancen | Präzise — validiert Aussagen |
| False-Positives | **Höheres Risiko** (z.B. 78% falsche "Dead Skills") | **Niedrig** (bestätigte 0% Dead Skills) |
| Wann wählen | Erste Inventur, Übersicht, 80%-Lösung | Deep-Dive, Risk-Bewertung, Entscheidungsbasis |

**Verifiziert 2026-07-04:** Fable behauptete "394 tote Skills" nach Skill-Inventur. OPUS widerlegte: 0 tote Skills, alle haben aktive Nachfolger. Die Extra-Kosten (~$0.25 mehr) verhinderten fehlerhafte Löschungen.

**Faustregel:** Für Skill-Audits / Library-Hygiene / Deep-Analysis → OPUS 4.8 high (nicht xhigh). Für schnelle Inventur / Überblick → Fable 5 reicht.

## User-Konfiguration speichern

Da die Bundled-Skills (`claude-code`) nicht editierbar sind, landen User-spezifische Policy-Regeln entweder:
- In diesem Skill (wenn es ums Model-Routing geht)
- Im Memory (wenn es um temporäre Aktionsfenster geht, z.B. Rabat)
- In `yuno-user-preferences` (wenn es um Arbeitsstil-Präferenzen geht)

**Wichtigste User-Correction (2026-07-04):**
- Fable 5 am Anfang **KEIN Budget-Limit** vorselektieren (Basti: "sei nicht geizig", "gib kein limit vor")
- GitHub-Repos sind Basti's Territorium — NICHT in Fable-Delegationen einbeziehen
- GreyHack-bezogene Tasks bleiben separat (vorherige Absprache)
- Home-Audits und .hermes-Audits sind Fable-5-Würdig

## Pitfalls

1. **Fable 5 Budget NICHT im Voraus capen** — Basti will Rabat-Volle-Power. Nur `--model fable`, KEIN `--max-budget-usd`, KEIN `--max-turns`. Ausnahme: Basti sagt explizit "sparsam" oder "budget X".
2. **Zu viele Small-Tasks einzeln** → Jeder Aufruf hat Mindestkosten (~$0.05). Batchen reduziert Overhead massiv. Aber Fable 5 für Einzel-Smoke-Tests ist OK (Rabat-Power).
3. **Rabat-Fenster ignorieren** → Nach 7. Juli 2026 steigen Fable-Kosten. Dann wieder Limits setzen.
4. **False sense of "bundled skill is enough"** → Bundled Skills enthalten keine User-spezifischen Policy-Regeln. Dieser Skill ergänzt sie.
5. **Opus für Medium-Tasks** → 4x Kosten bei gleicher Qualität. Nur für Critical/Architecture.
6. **Fable Delegations-Briefing per cat-Pipe** → `cat brief.txt | claude -p` verbraucht Budget ohne Output. Immer via `claude -p "$(cat /tmp/brief.txt)"`.
7. **GitHub-Repo-Bereich in Fable-Tasks einbeziehen** → NICHT machen. Basti hat eigenen Plan für Repo-Sync und Refactor.
8. **Session-Limit vs Weekly-Limit verwechseln** → "Exceeded budget" heisst meist Session-Limit (Reset in 3h), nicht Weekly-Limit (Reset Mi 17:00). Tool: `claude` zeigt Limits bei Session-Nähe.
9. **"Nicht geizig" nur auf Fable anwenden** → **FALSCH.** Wenn Basti "nicht geizig" sagt, gilt das für ALLE Modelle — auch Sonnet/Opus bekommen dann KEIN Limit. NICHT auf Fable beschränken.

## Verknüpfte Skills

- `autonomous-ai-agents/claude-code` — bundled, enthält CLI-Referenz und Quick-Start
- `autonomous-ai-agents/codex` — für Codex-CLI-Alternative
- `orchestration/multi-agent-orchestration` — für parallele Worker-Delegation
- `model-selector` — für Modell-Auswahl auf Nous-Portal-Seite (anderer Scope)
