# Fix-Plan Verification: Greyscripts (2026-07-04)

> Konkreter Befund aus der Session — als Referenz für das
> "Verifying Fix-Plan / Artifact Claims Against Live Sources"-Pattern.

## Ausgangslage

Fix-Plan (`hermes-greyscripts-fixplan-zusammenfassung.md`) behauptete:

1. Cluster 1 (20× negativer Index) und Cluster 2 (10× inline-if) sind offen → Issue #31
2. CI-Build schlägt bei 13 von 15 aktiven Dateien fehl
3. Issues #30, #31, #43, #48 müssen nach CI-Fix geschlossen werden
4. Keine Erwähnung eines Merge-Gaps zwischen main und develop

## Live-Check (git)

```bash
# Issue-Referenzen prüfen
git log --all --oneline --grep="#31"      # → 0 Treffer
git log --all --oneline --grep="#42"      # → 129dd63 fix: negativer Index ... closes #42
git log --all --oneline --grep="#41"      # → 1b0e53d fix: Cluster 2 ... closes #41
git log --all --oneline --grep="#30"      # → 62f0371 ci: add ci-build.sh ... addresses #30

# Fix-Existenz prüfen
git log main --oneline --grep="index|inline|50a0ddc" -5
# → Fixes bereits auf main!

# Merge-Gap prüfen
git merge-base --is-ancestor main develop && echo "merged" || echo "gap"
# → gap! (Fixes nicht in develop)

# CI-Check
git show develop:.github/workflows/ci.yml | head -3
# → CI-YAML existiert (workflow lint + greybel build)
```

## Discrepancies: Claims vs Reality

| Claim | Reality | Severity |
|---|---|---|
| Cluster 1 offen (Issue #31) | Fix auf main (129dd63, closes #42) | 🔴 |
| Cluster 2 offen (Issue #31) | Fix auf main (1b0e53d, closes #41) | 🔴 |
| #43, #48 müssen geschlossen werden | Nicht im Git-Log | 🟠 |
| Kein Merge-Gap | gap! Fixes main, Tools develop | 🔴 |
| CI schlägt pauschal fehl | CI existiert, aktueller Status unklar | 🟠 |

## Korrigierte Prioritäten

Nach Verifikation:

1. **P0**: Merge main→develop (holt Cluster-1 + Cluster-2 + Docs)
2. **P0**: CI-Rerun auf develop → echten Ist-Stand messen
3. **P1**: Cluster 3/4/5 nur falls nach CI noch rot
4. **P2**: Fix-Plan-Dokument korrigieren (Issue-Nummern auf #41/#42)

## Lessons

- Plan-Autoren vertauschen oft Issue-Nummern (z.B. #31 ↔ #41/#42)
- Ein "großer Fix" kann mehrere Cluster auf einmal abdecken
- Merge-Gaps sind das häufigste übersehene Problem in Fix-Plänen
- CI-Existenz ≠ CI-Grün — immer Nachmessung nach Merge einplanen
