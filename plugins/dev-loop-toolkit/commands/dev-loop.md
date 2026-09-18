---
description: Fährt den autonomen Dev-Loop für einen Milestone (leer = aktiv offener Milestone)
argument-hint: "[milestone]"
allowed-tools: Bash(gh issue list:*),Bash(gh issue view:*),Bash(gh issue comment:*),Bash(gh issue close:*),Bash(gh issue create:*),Bash(gh pr create:*),Bash(gh pr checks:*),Bash(gh pr merge:*),Bash(gh pr view:*),Bash(gh api:*),Bash(git:*),Bash(python3:*),Bash(bash:*),Read,Write,Edit,Grep,Glob,TodoWrite,Task,TaskOutput,Agent,Skill,CronCreate,OffPeakCreate
---

Fahre den autonomen Dev-Loop aus. Lade zuerst den Skill:

Skill(skill="dev-loop-toolkit:dev-loop")

Meilenstein: $ARGUMENTS — leer gelassen: den aktiv offenen Milestone per
`gh api repos/<owner>/<repo>/milestones` ermitteln (jüngst bearbeiteter mit offenen
Issues) und kurz bestätigen. Dann dem Skill folgen: BASELINE → GATE → FRONTIER →
BRIEF → IMPL → VERIFY → LAND → LOG. Halte-Regeln (Gates, Entscheidungen, rote
Baseline, Lock) sind bindend — kein HALT wird übersprungen.
