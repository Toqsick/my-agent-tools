---
name: deployment-landing-zone
description: |
  Use when controlling where multi-agent deliverables are written or deployed, choosing the output directory for a swarm run, or enforcing a shared workspace layout for a multi-agent cluster.
  NOT for single-agent file outputs, ephemeral scratch writes, or runtime config — those don't need a landing zone.
  Control the write/deploy destination for multi-agent deliverables.
version: 1.1.0
changelog:
- '1.1.0 (2026-07-04): Git-Commit-Splitting (Basti-Preference 3-4 Sub-Commits), fixe-alles
  Protocol, Verifikation durch Ausführen, Push-Verifikation nach Deploy'
- '1.0.0 (2026-07-04): Initial — Pattern aus Bastis ''A1 B1 nur in repo C2'' Korrektur
  (MaxClaw v3.0 Session)'
author: Yuno
license: MIT
platforms:
- linux
triggers:
- registrieren
- deploy
- live schalten
- branch
- landing zone
- fixe alles
- commit split
- sub-commit
- fix everything
- verify
trigger_keywords: ['agent', 'multi', 'deliverables', 'controlling', 'where']
keywords: ['agent', 'multi', 'deliverables', 'controlling', 'where']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['multi-agent-cluster-patterns', 'workflow-template']
---


# Deployment Landing Zone

Steuert, wo Multi-Agent-Outputs landen: **git branch first** (default), **live system** (opt-in).

## Die Grundregel — Branch-First

**Default:** ALLE Multi-Agent-Deliverables (Skills, Workflows, Config-Änderungen, Cron-Jobs) landen als **git commits auf einem Feature-Branch**.

**Ausnahme:** System-weite Anwendung (Cron-Registrierung via `hermes cron create`, Live-Config-Patching, Service-Restarts) passiert NUR nach **explizitem Go** vom User:
- "mach live", "schalt an", "registrier jetzt" → direkt anwenden
- ALLE anderen Formulierungen = erst in den Branch committen

**Begründung (Basti-Korrektur 2026-07-04):** Basti sagte "A1 B1 registrieren nur in repo C2" — er wollte Artefakte im Repo, nicht live. Der Branch ist der Lieferkanal, der User entscheidet wann live.

## Cron-Registration via Script

Wenn Subagenten neue Cron-Jobs produzieren, nutze dieses Muster:

### Schritt 1: JOBS-Array im Script
```bash
#!/bin/bash
set -euo pipefail

JOBS=(
  "my-cron-job|0 */2 * * *|main|telegram:7222661188"
  "heavy-cron-job|0 22 * * 0|heavy|local"
)

for job in "${JOBS[@]}"; do
  IFS='|' read -r name schedule model deliver <<< "$job"
  echo "Register: $name ($schedule, $model, $deliver)"
done
```

### Schritt 2: Modell-Pinning (Pitfall #10 Workaround)
**`hermes cron create` akzeptiert KEIN `--model` Flag.** Das Modell wird nach der Erstellung gepinnt:
```bash
hermes cron create --name "$name" --schedule "$schedule" --prompt "$prompt" $deliver_arg
cronjob action=update job_id=$JOB_ID model=$model provider=nous
```

### Schritt 3: Deliver-Override Decision Tree
| Output-Größe | Deliver | Grund |
|---|---|---|
| < 1KB | telegram (default) | Kurzmeldung |
| 1-5KB | telegram | Passt noch |
| 5-10KB | telegram oder local | Risikozone — ab 5KB prüfen |
| > 10KB | **local** (zwingend) | Telegram 30s Timeout (Pattern 2) |

### Schritt 4: Verifikation durch Ausführen

Nach jeder Cron-Registrierung oder Config-Änderung: **laufen lassen, nicht nur angucken.**

```bash
# 1) Den Job aktiv auslösen und auf grünen Status prüfen
cronjob action=run job_id=$JOB_ID
# → execution_success: true + last_status: ok = grün

# 2) Bei Config-Änderungen:
hermes config check          # Validierung
hermes config show | grep KEY # Wert lesen

# 3) Bei Scripts/Services:
bash -n script.sh            # Syntax-Check
script.sh --dry-run          # Trockentest
systemctl --user is-active service  # Laufzeit-Check
```

**Warum nicht nur `hermes cron list` glauben:** Die List-Darstellung zeigt oft den falschen Provider (Display-Bug) — z.B. `zai` statt des tatsächlich gepinnten `ollama-cloud`. Nur der Run-Log beim tatsächlichen Ausführen wird geschrieben und ist autoritativ.

## Git Commit Splitting (Basti-Preference)

Wenn Orchestrierungs-Output in ein Repo gepusht wird, Änderungen in **3-4 logische Sub-Commits** aufteilen. Jeder Commit ist unabhängig reviewable:

```
# Typische Splits für v3.0-Upgrade-Arbeit:
git commit -m "feat(skills):  <neuer Skill + Index-Update>"
git commit -m "feat(tools):   <Tools-Scripte ins Repo>"
git commit -m "docs(v3.0):   <README + Changelog + Reports>"
```

**Konventionelle Commit-Scopes (Basti-Stil):**
| Scope | Wann | Beispiel |
|-------|------|---------|
| `feat(skills):` | Neue Skills oder Skill-Index-Update | `feat(skills): hermes-cli-quirks + INDEX/INSTALL auf 9` |
| `feat(tools):` | Tools/CLI-Scripte | `feat(tools): 4 Ops-Scripte + .gitignore` |
| `feat(agent):` | Persona/IDENTITY/AGENTS | `feat(agent): MaxClaw v3.0 GreyHack-Arbeiter` |
| `feat(workflows):` | Cron-Registrierungen | `feat(workflows): 5 neue autonome Crons` |
| `feat(security):` | Security-Audit, Härtung | `feat(security): Self-Audit + GreyHack-Pattern` |
| `fix(crons):` | Cron-Cleanup, Duplikate | `fix(crons): 11 stale cron jobs entfernt` |
| `docs(v<version>):` | README, Architektur-Docs | `docs(v3.0): Verifikations-Doku-Layer` |

**Push-Verifikation** — nach dem Push prüfen ob der Remote-HEAD dem lokalen HEAD entspricht:
```bash
gh api repos/<owner>/<repo>/branches/<branch> --jq '.commit.sha'
```
Weicht der Remote-HEAD ab (paralleler Merge), `git fetch origin` und rebasen statt force-pushen. Beide HEAD-SHAs dokumentieren.

## Referenzen

- Siehe `orchestration/multi-agent-orchestration` Phase 4.1 (Artifact Landing Zone) + 4.2 (Cron Registration Pattern)
- Siehe `orchestration/multi-agent-pitfalls-cheatsheet` Pitfall #36 (Artifact landing zone correction)
- Siehe `yuno-user-preferences` (Repo-Branch Landing Zone Preference)
