---
description: Plant einen neuen Meilenstein-Zyklus (Plan-Mode) mit Issues, Gates und Bruchstellen
argument-hint: "[Thema/Scope]"
allowed-tools: Bash(gh issue list:*),Bash(gh issue create:*),Bash(gh issue view:*),Bash(gh api:*),Bash(git:*),Read,Write,Edit,Grep,Glob,Agent,Skill,AskUserQuestion,EnterPlanMode,ExitPlanMode
---

Plane einen neuen Meilenstein-Zyklus. Lade zuerst den Skill:

Skill(skill="dev-loop-toolkit:plan-dev-loop")

Anlass/Scope: $ARGUMENTS (leer: nach dem Ziel fragen, bevor du loslegst).
Dann dem 7-Schritte-Ablauf des Skills folgen — insbesondere: verifizierte
Ausgangslage messen (nur eigene Zahlen), grill-4x4-Mining für offene
Entscheidungen, Akzeptanzkriterien als ausführbare Befehle, Bruchstellen-Rezepte
für die riskantesten Tasks. Emission (Milestones/Issues) erst nach Plan-Freigabe.
