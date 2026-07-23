# Phase 4 — CI-Workflow-Vergleich Commands

```bash
# Arbeitsbäume
ls -la /pfad/zu/klonA/.github/workflows/ 2>/dev/null
ls -la /pfad/zu/klonB/.github/workflows/ 2>/dev/null

# ci.yml Volltext-Diff
diff -u \
  /pfad/zu/klonA/.github/workflows/ci.yml \
  /pfad/zu/klonB/.github/workflows/ci.yml

# Build-Script
diff -u \
  /pfad/zu/klonA/scripts/ci-build.sh \
  /pfad/zu/klonB/scripts/ci-build.sh \
  2>/dev/null || echo "Nur in einem Klon"
```

**Checkliste:**
- [ ] Anzahl Jobs
- [ ] greybel-build-Job vorhanden?
- [ ] Build-Script: greybel-CLI-Subcommand korrekt? (3.6.x: `-o`, 3.7.x: `build`)
- [ ] Artifact-Upload konfiguriert?
- [ ] Trigger-Branches identisch?

## Cross-Branch CI Job Drift

Die Workflow-Datei kann auf verschiedenen Branches **unterschiedliche Jobs** enthalten.

```bash
# Job-Namen pro Branch extrahieren
grep '^  [a-z].*:$' /pfad/zu/klonA/.github/workflows/ci.yml
grep '^  [a-z].*:$' /pfad/zu/klonB/.github/workflows/ci.yml

# Job-Anzahl zählen
grep -c '^  [a-z].*:$' /pfad/zu/klonA/.github/workflows/ci.yml
grep -c '^  [a-z].*:$' /pfad/zu/klonB/.github/workflows/ci.yml

# LOC-Vergleich als Proxy für Komplexität
wc -l /pfad/zu/klonA/.github/workflows/ci.yml
wc -l /pfad/zu/klonB/.github/workflows/ci.yml
```

**Drift-Checkliste:**
- [ ] Job-Anzahl identisch? (Differenz = Hinweis auf CI-Upgrade in einem Branch)
- [ ] Welcher Branch hat MEHR Jobs? → MoT-Kandidat für CI
- [ ] Fehlt ein Build-Job im anderen Branch? → Build-Verifikation nur im vollständigen Branch
- [ ] Build-Script-Inhalt unterschiedlich? (CLI-Subcommand, scan-Tiefe, exclusions)
- [ ] Zusätzliche Workflow-Dateien in einem Branch? (pr-reminder, auto-label, etc.)