# Grok 4.5 — Modellevaluierung (MiroFish-Audit 2026-07-13)

Konkrete Bewertung basierend auf der MiroFish-Installations-Session
(Session `hermes_20260711_224811_a8d58a`), erstellt im Rahmen der Forensik
nach der Grok-Build-CLI-Leak-Meldung.

**Evaluierungs-Kontext:** Bastis Workstation, Hermes via Nous-Provider,
Modell `x-ai/grok-4.5`, kein direkter Grok-Build-CLI-Einsatz.

---

## Session-Daten (belegt aus `agent.log` + `state.db`)

| Metrik | Wert |
|--------|------|
| API-Calls | 60× `x-ai/grok-4.5` (über Nous) |
| Gesamt-Input-Tokens | ~7,2 Mio |
| Gesamt-Output-Tokens | ~34k |
| Session-Dauer | ~22:48–23:25 + Folgetag |
| Cache-Hit-Rate (frühe Turns) | ~86% |
| Cache-Hit-Rate (späte Turns) | 96–100% |
| Modellwechsel während Session | ja (Grok ↛ DeepSeek ↛ MiniMax) |
| Provider | `nous` / `https://inference-api.nousresearch.com/v1` |

## 5-Dimensionen-Bewertung

| Dimension | Note | Begründung |
|-----------|------|------------|
| **Coding-Kompetenz** | **8/10** | MiroFish-End-to-End autonom: Clone, `uv sync`, npm, Zep-Setup, chirurgischer Bugfix `simulation_runner.py` (PYTHONPATH-Isolation). Keine API-Halluzinationen. |
| **Tool-Disziplin / Sicherheit** | **7/10** | Bash-Hygiene: `set -a/eval` für Key-Expansion, `chmod 600 .env`, Gitignore-Check. Aber **keine proaktive Klärung** „der Key geht in den Chat/Modellkontext — ist das okay?" |
| **Kontext-Stabilität** | **9/10** | 7,2 Mio Tokens über 60 Turns ohne Drift. Cache-Hits steigen auf 100% — kein Kontext-Wildwuchs. |
| **Anbieter-Transparenz** | **4/10** | xAI hat kein Statement zum Leak-Vorfall veröffentlicht, keinen CVE, keinen Postmortem. `cereblab`-Report war von xAI-unabhängigen Forschern. |
| **Preis-Leistung (Nous)** | **8/10** | Cache-Effizienz (96–100%) drückt Token-Kosten. Für Cloud-Coding-Agenten konkurrenzfähig. |

**Gesamt: 7,5/10** für Bastis Workflow-Weiterverwendung.

## Was das Modell KANN (belegt)

- **Autonomer End-to-End-Workflow:** Git Clone → Deps installieren (`uv sync`, npm) → `.env` schreiben → Service starten → Testlauf → Report schreiben. Alle Schritte aus eigener Planung.
- **Key-Hygiene:** Zep-Key via Python in `.env` geschrieben (nicht in Chat-Ausgabe). MiniMax-Key aus `~/.hermes/.env` per Shell-Expansion. Beide `.env` auf Mode 0600.
- **Cache-Effizienz:** Ab zweitem Turn 96–100% Cache-Hits. Kein redundantes Neulesen gleicher Files.
- **Bugfix-Qualität:** `simulation_runner.py` Patch war chirurgisch — überflüssige PYTHONPATH-Erweiterung entfernt, keine unnötigen Refactors.

## Was das Modell NICHT KANN / caveats

- **Keine proaktive Sicherheitsabfrage bei Keys:** Wenn der User einen Key im Chat postet, sagt das Modell nicht „ist das sicher, dass der in den Chat kommt?" — es schreibt ihn einfach in `.env`.
- **Die 4/10 bei Anbieter-Transparenz sind systemisch, kein Modellproblem:** Jeder Provider, der keinen Transparenz-Report und kein Audit-Statement veröffentlicht, bekommt hier eine niedrige Bewertung — unabhängig vom Modell selbst.
- **Risiko-Δ:** Da `grok build` CLI nicht installiert war, ist der Whole-Repo-Upload-Mechanismus aus dem Audit lokal nie gefeuert. Das Risiko ist das des **Modellkontexts** (Keys im Chat), nicht des **Storage-Kanals** (Git-Bundle-Upload).

## Hygiene-Regeln (empfohlen für Grok-4.5-Sessions)

1. **Keine Prod-Keys in den Chat pasten.** Keys gehören in `.env` (gitignored, 0600). Der Agent kann sie via Tool lesen — das ist sicher. Ein Key im Chat-Text ist per Definition offengelegt.
2. **Working-Dir auf Projektverzeichnis beschränken.** Nie im Home-Root starten.
3. **`.gitignore` + `secrets.env` aus Working Tree** vor jeder Session prüfen.
4. **Diversifikation:** Claude/DeepSeek/MiniMax ergänzend nutzen (wie bereits Praxis).

## Verwandt

- `references/grok-build-cli-leak-2026-07-13.md` — Der vollständige Audit, auf dem diese Bewertung basiert
- SKILL.md Sektion "Proaktives Session-Monitoring" — Stufe 1-4 für sichere Cloud-Agenten-Sessions

## Wann aktualisieren

- Neue Grok-Modellversion (4.6, 5.0) → neue Evaluierung
- Wenn xAI ein Audit-Statement veröffentlicht → Anbieter-Transparenz neu bewerten
- Wenn Basti Grok 4.5 erneut intensiv nutzt → Daten aus dieser Session als Baseline nutzen
