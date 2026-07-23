# Multi-Agent Master Workflow (Skill)

Dieser Skill implementiert das Master-Controller/Subagent-Pattern für systematische Analyse- und Umsetzungsaufgaben.

## Installation
Die Skill-Definition liegt in `SKILL.md` (seit 2026-07-06 — der Loader lädt ausschließlich
`SKILL.md`; die ältere `SKILL.yaml` wurde nie geladen und bleibt nur als historische Spec liegen).
Wird automatisch beim Hermes-Start geladen.

## Usage
Einfach im Chat sagen:
- "multi-agent master workflow: prüfe [thema]"
- "Master-Workflow: analysiere [thema]"
- Trigger-Phrasen aus der YAML: "prüfe systematisch", "analysiere und priorisiere", "erstelle einen umsetzungsplan"

## Architektur
| Generisch          | Hermes-Rolle |
|--------------------|--------------|
| Master-Controller   | Queen        |
| Subagent A–E        | Worker       |
| QA-/Abnahmeprüfung  | Gate         |

## Quelldokumentation
- `~/Downloads/Github/docs-refresh-master-workflow.md` (Original-Spec)
- `~/Downloads/Github/master-workflow-ai-agenten-template.md` (Template)
- Diese Skill-Spec: `skill-multi-agent-master-workflow.yaml`

## Automatisierung
- Wrapper: `~/.hermes/scripts/run-master-workflow.sh`
- Cron: alle 8 Stunden via `hermes cron create`
- Bei Hermes TUI lokal only — deliver=origin (Output wird im Cron-Log gespeichert)
