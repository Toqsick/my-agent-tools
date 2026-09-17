---
id: dev-lens-swarm
name: dev-lens-swarm — RepoLens-inspirierte Multi-Agent-Development-Pipeline
when_to_use: Feature/Refactor/Review/Bugfix-Arbeit mittlerer bis großer Tragweite, bei der parallele Lens-Analyse + Verifikation Mehrwert bringen; NOT für triviale Einzel-Edits
agents: [zc-general, zc-coder, zc-verify, zc-gate, zc-impact, zc-selftest, general-purpose]
skills:
  - dev-lens-swarm
  - grill-4x4
  - schwarm-ohne-barriere
phases:
  - phase: Grill
    owner_agent: Haupt-Agent (Session)
    skills: [grill-4x4]
    exit_criteria: Frontier leer + shared understanding bestätigt.
    failure_modes: Nutzerrunde erwidert nichts Neues → Task-Definition einfrieren und weiter.
  - phase: Triage
    owner_agent: zc-general (GLM-5.3/max je Tier-Matrix — Planung = Denker-Tier)
    skills: [dev-lens-swarm]
    exit_criteria: Codemap + Lens-Auswahl + swarm.py-Plan initiiert (Run-Dir + Ledger).
    failure_modes: "Scope nicht partitionierbar → zurück zur Grill-Phase (max 1 Rücklauf; danach Annahme dokumentieren und weiter)."
  - phase: Lens-Rounds
    owner_agent: zc-coder (Worker-Schwarm; Architektur-/Security-Lenses je tier-matrix auf GLM-5.3/max)
    skills: [schwarm-ohne-barriere]
    exit_criteria: NO_FRESH_ANGLES oder rounds_max erreicht.
    failure_modes: Requeue-Budget erschöpft → Task eskaliert (escalated im Ledger).
  - phase: Meta-Orchestrator
    owner_agent: zc-general
    skills: [dev-lens-swarm]
    exit_criteria: "Decision je offener Round-Hypothese (re-dispatch|saturiert|escalate)."
    failure_modes: Zykklus-Verdacht (State-Hash) → escalate.
  - phase: Verify
    owner_agent: zc-verify (konkurrierende Spur)
    skills: [schwarm-ohne-barriere]
    exit_criteria: "Alle verify-briefs mit verdict PASS/RETRY → bei RETRY: Requeue mit finding."
    failure_modes: Verify-Rückstau (2 Slots) → Worker-Dispatch drosseln.
  - phase: Synthesize
    owner_agent: general-purpose (Session-Modell, aktuell GLM-5.3-Flash; effort high je Tier-Matrix)
    skills: [dev-lens-swarm]
    exit_criteria: final/manifest.json + Report dedupliziert.
    failure_modes: Cluster zu grob → zweite Synthese-Iteration.
  - phase: Report
    owner_agent: Haupt-Agent
    skills: [dev-lens-swarm]
    exit_criteria: Metriken (swarm.py metrics) + Flowdiagramm + offene-Posten-Liste.
    failure_modes: "Metriken inkonsistent (Makespan < kritischer Pfad) → Warnung ausgeben (bekanntes Edge)."
---

# dev-lens-swarm — RepoLens-inspirierte Multi-Agent-Development-Pipeline

**Grill → Triage → Lens-Rounds → Meta-Orchestrator → Verify → Synthesize → Report.** RepoLens-inspirierte
Runden-Pipeline: der Master-Skill `dev-lens-swarm` (`~/.zcode/skills/dev-lens-swarm/`)
orchestriert Modi (`feature`/`bugfix`/`refactor`/`review`/`greenfield`/`discover`) und Lens-Auswahl über
12 Domänen, `grill-4x4` (`~/.zcode/skills/grill-4x4/`) leert vor dem Plan die Frontier
(max. 4 Runden à 4 Fragen, harte Regel: kein Handeln vor Bestätigung), `schwarm-ohne-barriere`
(`~/.zcode/skills/schwarm-ohne-barriere/`) stellt mit `swarm.py` DAG-Scheduling, Ready-Queue,
append-only Ledger, Requeue-Governance und den
6er-Fan-out-Deckel (4 Work- + 2 Verify-Slots). Die Verify-Spur läuft konkurrierend zu den Lens-Rounds
(MiniMax M3 verboten); der Meta-Orchestrator entscheidet je Runde `re-dispatch | saturiert (NO_FRESH_ANGLES)
| escalate`, terminiert über DONE×N-Streaks (review: N=3, sonst N=2) und das `rounds_max`-Ceiling (Soll: 3).

Modell-/effort-Zuordnung je Rolle steht in der Tier-Matrix des Master-Skills
(`~/.zcode/skills/dev-lens-swarm/references/tier-matrix.md`): GLM-5.3 (max) für Meta-Orchestrator,
Architektur-Lenses, Gate-/Security-Rollen und Triage (Agent zc-general — Planung = Denker-Tier);
GLM-5.3-Flash (high) für Implementierung und Verify; Synthesizer via general-purpose auf dem
Session-Modell (aktuell GLM-5.3-Flash, high); effort `low` nur für rein mechanische Extraktion.

**Route in:** "Feature/Refactor/Review/Bugfix mit parallelen Lenses / lens-swarm / review this repo."
Nicht für triviale Einzel-Edits oder Aufgaben unter der ~5-Minuten-Delegationsschwelle — dafür
[`superpower-10x-pipeline`](superpower-10x-pipeline.md) bzw. `schwarm-ohne-barriere` direkt ohne Lenses.
