---
name: harness-bootstrap
version: 0.1.0
author: Basti
license: MIT
description: "Use when ein Repo dev-loop-fähig gemacht werden soll („mach das Repo loop-fähig“, „bootstrap governance“, „richte den Dev-Loop ein“) — Governance-Grundausstattung, Labels, agent-log, Verify-Befehl, merge-probe. NOT for Repos, die bereits WORKFLOW.md/AGENTS.md-Canon haben (nur Lücken prüfen), oder für das Abarbeiten von Milestones (dev-loop)."
metadata:
  hermes:
    tags: [bootstrap, governance, dev-loop, onboarding, github]
    related_skills: [dev-loop, agent-md-management, github-repo-management]
---

# harness-bootstrap — Governance-Grundausstattung für den dev-loop

dev-loop braucht im Ziel-Repo einen lesbaren Canon: benannten Verify-Befehl,
Branch-/Commit-/Issue-Konventionen, Gate-Protokoll, agent-log. Dieser Skill
installiert die Mindestausstattung — **überschreibt niemals Bestehendes ohne
Rückfrage** (bei Konflikten gewinnt das Bestehende; Lücken werden ergänzt und
gemeldet).

## Ablauf

1. **Bestandsaufnahme** (read-only): AGENTS.md/CLAUDE.md, WORKFLOW.md, DECISIONS.md,
   PROGRESS.md, CI-Workflows, Test-Befehle, Labels, offene Milestones, `.gitignore`.
   Ergebnis: Tabelle vorhanden/fehlt/konfligiert.
2. **Verify-Befehl festnageln** (die wichtigste Lücke): der strengste lokal
   lauffähige Check (Test-Suite + Build; Format/Lint wenn vorhanden). Wenn nichts
   existiert: Minimum = Tests-Ordner mit einem echten Smoke-Test — ein Loop ohne
   Verify lügt grün. Befehl + Baseline-Variante in WORKFLOW.md dokumentieren.
3. **Dokumente ergänzen** (Skelette: → `references/governance-templates.md`):
   AGENTS.md (Regeln+Loop-Referenz), WORKFLOW.md (Branch-Modell, PR-Flow, Verify-Loop,
   Issue-/Commit-Konventionen), DECISIONS.md (append-only, D-n), PROGRESS.md,
   HANDOFF.md, docs/TASKS.md (Spiegel der GitHub-Issues).
4. **GitHub-Seite**: Labels anlegen (`agent`, `gate`, `idea`, `blocked`), ein
   `agent-log`-Status-Issue anlegen, merge-probe ausführen und Ergebnis
   (native-auto vs. agent-side + Grund) in WORKFLOW.md verewigen.
5. **Housekeeping**: `.dev-loop/` und `.worktrees/` in `.gitignore` aufnehmen.
6. **Abschlussbericht**: was angelegt/ergänzt/gemeldet wurde + erster
   dev-loop-Start-Hinweis („/dev-loop" bzw. Skill-Aufruf mit erstem Milestone).

## Regeln

- Ein einziger Bootstrap-Commit (`chore(gov): dev-loop-bootstrap`) — es sei denn,
  der Mensch will anders; Inhalte vorher zeigen
- Vorhandene Konventionen werden **adaptiert, nicht ersetzt**: nutzt das Repo
  `feat/JIRA-123`-Branches, übernimmt der Loop das
- Keine CI-Änderungen ohne Rückfrage (nur Vorschlag + Begründung notieren)
- Der Bootstrap erzeugt **keine** Milestones/Issues — das macht plan-dev-loop

## Es läuft gut, wenn

- dev-loop danach ohne offene Fragen startet: Verify-Befehl genannt, Merge-Modus
  dokumentiert, Labels + agent-log existieren
- Keine bestehende Datei ohne Rückfrage verändert wurde
- Der Bootstrap-Commit das Ganze in einem rückrollbaren Stück hält
