# Artifact-Specification Dispatch — Voll-Vorlage

Für strukturierte Buildout-Missionen mit 3–5 parallelen Lanes. Jede Lane liefert konkrete Artefakte an exakten Pfaden statt vager „Recherche-Ergebnisse".

## Dispatch-Context-Template

```
Du bist [LANE-NAME der] für [PROJEKT-BESCHREIBUNG].

KONTEXT:
- [Basis-Info: OS, Repo-Pfade, vorhandene Files]
- [Spezifische Details: welche existierenden Arbeitsdateien relevant sind]
- [Abhängigkeiten: was existiert bereits, was muss erhalten bleiben]

AUFGABE:
1. [Konkrete, messbare Aufgabe 1]
2. [Konkrete, messbare Aufgabe 2]
3. [Konkrete, messbare Aufgabe 3]

LIEFER-ARTEFAKTE (müssen real existieren + verifiziert sein):
- /tmp/project/pfad/datei1.md (Workflow-Definition für Cron, Watchdog-Pattern)
- ~/bin/script.sh (ausführbar, chmod +x, Shell-Skript mit set -euo pipefail)
- ~/bin/tool.py (Python, CLI mit argparse, getestet mit --help)
- ~/docs/system/NAME-YYYY-MM-DD.md (Vollständige Doku auf Deutsch)

WICHTIG:
- Watchdog-Pattern: silent on success, alert only on anomaly/anomaly
- Bash-Skripte mit set -euo pipefail, aussagekräftige Fehlermeldungen
- Code-Kommentare immer DEUTSCH
- Verifikation: ls -la + Dry-Run-Output am Ende jeder Artefakt-Gruppe
- Qualitäts-Gates: greybel build ohne -u, YAML-Frontmatter prüfbar
- KEIN git push main (Bastis Regel)

Gib am Ende eine Verifikationsliste zurück: welche Dateien existieren (mit ls -la) und Beispiel-Output bei Dry-Run/Tests.
Antworte auf Deutsch.
```

## Live-Vorlage aus der 5-Lane MaxClaw-Orchestration (2026-07-04)

### Lane 1: DB/Sandbox — Datenbank-Analyst
```
Du bist GreyHack-DB-Spezialist für MaxClaw.
KONTEXT:
- DB-Pfad: /mnt/DATA/.../GreyHackDB.db (~6.9 MB, 18 Computer, 56 Map-IPs, 1 Player-PC)
- MaxClaw-Repo: /tmp/maxclaw-clone/
LIEFER-ARTEFAKTE:
- /tmp/maxclaw-clone/workflows/greyhack-db-snapshot.md
- ~/bin/greyhack-db-snapshot.sh (ausführbar, chmod +x)
- ~/bin/greyhack-db-analyze.py (Python, argparse CLI)
- ~/docs/system/greyhack-db-snapshot-2026-07-04.md
```

### Lane 2: Config/Refactor — Tool-Builder
```
Du bist MaxClaw's Tool-Builder-Refactorer.
KONTEXT:
- 28 GreyHack-Scripts in /mnt/DATA/.../yuno-tools/ als Pattern-Quelle
- MaxClaw-Repo: /tmp/maxclaw-clone/agent/*.md + config/config.yaml
LIEFER-ARTEFAKTE:
- /tmp/maxclaw-clone/agent/IDENTITY.md (v3.0)
- /tmp/maxclaw-clone/agent/AGENTS.md, TOOLS.md, MEMORY.md (v3.0)
- /tmp/maxclaw-clone/config/config.yaml (v3.0)
- /tmp/maxclaw-clone/AGENT-UPGRADE-2026-07-04.md
```

### Lane 3: Workflows — Workflow-Architekt
```
Du bist MaxClaw's Workflow-Architekt.
KONTEXT:
- 5 bestehende Workflows in /tmp/maxclaw-clone/workflows/
- Ziel: 5 NEUE Workflows
LIEFER-ARTEFAKTE:
- /tmp/maxclaw-clone/workflows/greyhack-db-watcher.md (alle 30min)
- /tmp/maxclaw-clone/workflows/greyhack-mission-tracker.md (alle 4h)
- /tmp/maxclaw-clone/workflows/greyhack-tool-backup-watch.md (alle 6h)
- /tmp/maxclaw-clone/workflows/greyhack-knowledge-distiller.md (Sonntag 22h)
- /tmp/maxclaw-clone/workflows/greyhack-basti-checkin.md (Mo+Mi+Fr 20h)
- /tmp/maxclaw-clone/workflows/register-workflows.sh (UPDATE)
```

### Lane 4: Skills — Skill-Set-Autor
```
Du bist Skill-Autor für MaxClaw.
KONTEXT:
- MaxClaw-Repo: /tmp/maxclaw-clone/skills/
- Hermes-Skill-Format (YAML-Frontmatter + Pattern + Code)
LIEFER-ARTEFAKTE (8 Skills):
- /tmp/maxclaw-clone/skills/sandbox-snapshot/SKILL.md
- /tmp/maxclaw-clone/skills/sqlite-reader/SKILL.md
- /tmp/maxclaw-clone/skills/greyscript-linter/SKILL.md
- /tmp/maxclaw-clone/skills/github-ops/SKILL.md
- /tmp/maxclaw-clone/skills/bash-script-builder/SKILL.md
- /tmp/maxclaw-clone/skills/telegram-notifier/SKILL.md
- /tmp/maxclaw-clone/skills/knowledge-distiller/SKILL.md
- /tmp/maxclaw-clone/skills/maxclaw-session-manager/SKILL.md
- /tmp/maxclaw-clone/skills/INSTALL.md + SKILL-INDEX.md
```

### Lane 5: Security — Security-Auditor
```
Du bist MaxClaw's Security-Auditor.
KONTEXT:
- MaxClaw-Repo: /tmp/maxclaw-clone/ mit config/config.yaml (default-deny)
- GreyHack hardening_audit.src als Pattern-Vorlage
LIEFER-ARTEFAKTE:
- /tmp/maxclaw-clone/security-audit-2026-07-04.md (Audit-Report)
- /tmp/maxclaw-clone/security/policies.md
- /tmp/maxclaw-clone/security/hardening_audit_maxclaw.yaml
- /tmp/maxclaw-clone/security/key_rotation.md
- ~/bin/maxclaw-security-audit.sh (chmod +x)
- /tmp/maxclaw-clone/config/config.yaml (v3.1 mit Härtungen)
```

## Warum funktioniert das?

1. **Exakte Pfade** → Subagent kann nicht behaupten „✅ done" ohne eine Datei zu schreiben
2. **Qualitäts-Gates im Context** → „chmod +x" + „set -euo pipefail" sind KEINE Verhandlungssache
3. **Verifikation am Ende** → Subagent muss am Ende `ls -la` + Dry-Run zeigen
4. **Deutsch-Pflicht** → Code-Kommentare und Doku sind konsistent
5. **Kein git push main** → Bastis Regel wird nicht umgangen

## Anti-Patterns

- ❌ **Keine Pfade angeben** → Subagent liefert optimistische Zusammenfassung statt Dateien
- ❌ **Zu viele Artefakte pro Lane** → max 8-10 pro Lane, sonst Context-Rot/Auslassungen
- ❌ **Abhängige Lanes** → Lanes müssen parallelisierbar sein (keine Serialisierung nötig)
- ❌ **Kein Output-Format spezifizieren** → Markdown? JSON? Nicht spezifiziert = Chaos
