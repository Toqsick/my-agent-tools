---
name: plan-dev-loop
version: 0.1.0
author: Basti
license: MIT
description: "Use when ein neuer Meilenstein-Zyklus geplant werden soll („plane M9“, „plan the next milestone“, „neuer Milestone mit Issues“, „plan dev loop“) — im Plan-Mode: verifizierte Ausgangslage, Meilenstein-Graph, Issues mit ausführbaren Akzeptanzkriterien, Bruchstellen-Rezepte, QoL-Backlog, dann Emission via gh + Handoff an dev-loop. NOT for das Abarbeiten bestehender Milestones (dev-loop), allgemeines Planen ohne GitHub-Emission (plan/plan-glm, better-plan-strategy) oder reines Interviewen ohne Planziel (grill-me)."
metadata:
  hermes:
    tags: [planning, milestones, issues, github, plan-mode]
    related_skills: [plan, plan-glm, better-plan-strategy, grill-4x4, grill-me, github-issues, dev-loop]
---

# plan-dev-loop — Meilenstein-Planer für den dev-loop

Erzeugt den Tracker, den `dev-loop` danach Schritt für Schritt abarbeitet:
Milestones + Issues + Reihenfolge-Vertrag + Bruchstellen-Rezepte. Vorbild ist der
pokerogue-3ds-M9/M10/M11-Plan („rosy-lemon", 16.09.2026), aus dem in 44 h 19 PRs wurden.

## Der 7-Schritte-Ablauf

### 1. Intake + grill-4x4-Mining

`Skill(skill="grill-4x4")` — 7 Seeds (Goal, Done, Boundary, Constraints, Surface,
Edge, Unknown), adaptiv, früh stoppen. **Fakten selbst recherchieren, nur Entscheidungen
fragen.** Kalibrierung: Domainwissen, Festgezurrtheit, Härtegrad.

### 2. Verifizierte Ausgangslage (messen, nicht Doku glauben)

Bis zu 3 Explore-Agenten parallel: Repo-State (main-SHA, Verify-Stand, offene Branches),
Ist-Abgleich gegen das Ziel (echte Zahlen: „13,9 % der Species" schlägt „meistens
vorhanden"), Doku-vs-Zustand (stale Behauptungen sammeln — sie werden Bruchstellen oder
Aufräum-Tasks). Jede Zahl im Plan trägt ihren Messbefehl.

### 3. Scope-Fixierung zuerst (gov-Commit-Muster)

Widerspricht der neue Scope alten Entscheidungen (DECISIONS.md/MASTER-Plan)? Dann ist
**Task 1 des ersten Milestones** der `gov:`-Commit: DECISIONS-Eintrag (D-n), der die
alte Entscheidung ausdrücklich aufhebt, plus Regelwerks-Nachzug — im selben Commit.
Ohne den arbeitet jeder folgende Task gegen ein Regelwerk, das noch das Alte sagt.

### 4. Meilenstein-Graph

Struktur-Vorlage: → `references/milestone-template.md`. Kernregeln:

- Milestones als Kette mit **Gate-Issue je Meilensteinende** (`gate:` + Checkliste +
  erwartetem Approval-Text)
- Issues mit Task-ID (`T-<M>.<n>`), jedes mit Akzeptanz = ausführbare Befehle
  (→ `references/issue-authoring.md`)
- **Dep-Edges explizit** (`Depends-on: #N` im Issue-Body) + eigene Sektion
  „Reihenfolge ist nicht beliebig" mit Begründung je Edge
- Parallelisierbare Issues markieren (`parallel: file-disjoint`), Rest ist sequenziell

### 5. Bruchstellen-Rezepte

Pro identifiziertem Risiko ein Debug-/Verify-Rezept statt generischer
"gründlich testen"-Floskeln: → `references/bruchstellen.md`. Das sind die Stellen,
an denen der Standard-Loop erfahrungsgemäß nicht reicht.

### 6. Risiken, Wiederverwenden, QoL-Backlog

- Risiken mit beobachtbarem Auslöser („RNG-Verbrauch ändert sich" statt „kann brechen")
- „Wiederverwenden statt neu bauen": existierende Funktionen/Tests/Werkzeuge listen,
  die neue Tasks nur verdrahten müssen
- QoL/Nice-to-haves **nicht** in Milestones: als `idea:`-Issues parken
  (Scope-Creep-Bremse)

### 7. Emission + Handoff

Nach Plan-Freigabe (ExitPlanMode):

```bash
gh api repos/OWNER/REPO/milestones -f title="M9 — Titel" -f state=open   # je Milestone
gh issue create … --milestone "M9 — Titel"                                # je Issue + Gate
```

- docs/TASKS.md-Spiegel im selben Zug nachziehen (sonst driften Tracker und Doku —
  pokerogue-T-8.x-Präzedenz)
- Handoff-Contract an dev-loop: REIHENFOLGE-Liste (Issue-Nummern, sortiert nach
  Dep-Edges, Gate-HALTs markiert) als Block im Plan-Doc UND im letzten agent-log
- Plan-Doc ablegen (Repo-Konvention, z. B. `docs/plans/` oder `.claude/plans/`)

## QoL-Katalog (Auswahl, die jeder Plan prüfen sollte)

Resume-Freundlichkeit (State nach jedem Issue), agent-log-Disziplin, `idea:`-Parkplatz
angelegt, Verify-Befehl im WORKFLOW.md benannt, merge-probe-Ergebnis dokumentiert,
`.dev-loop/` + `.worktrees/` in .gitignore, Abnahme-Issues als eigene markiert.

## Es läuft gut, wenn

- Jede Akzeptanz der Issues ein Befehl ist, den dev-loop ausführen und zitieren kann
- Die Reihenfolge-Sektion jede nicht-triviale Kante begründet
- Der riskanteste Task ein Bruchstellen-Rezept hat (und der einfachste keins)
- Nach der Emission `frontier.sh` die Milestones exakt so sortiert zurückliefert,
  wie der Plan es vorsieht — das ist der automatisierte Abnahmetest dieses Skills
