# DMZ × GitHub Status-Sync YYYY-MM-DD

**Datum:** YYYY-MM-DD
**Kontext:** Session-Start mit [User-Anweisung]. System-Check + Cleanup + PR-Fix + Issue-Sync.
**Davor:** [Letzte Session-Referenz]

## Ziel

Drei Dinge in dieser Reihenfolge:
1. **C — DMZ-State synchronisieren:** [Was ist unversioniert?]
2. **A — PR #N grün bekommen:** [PR-Status]
3. **B — Findings nach GitHub syncen:** [Anzahl Findings]

## Vorgehen

### Schritt C — DMZ-State committen

```bash
cd ~/greyhack-tools
git add [pfade]
git -c user.name="Yuno" -c user.email="yuno@olympagent.bot" commit -m "chore(dmz): [beschreibung]"
git push origin master
```

**Ergebnis:** Commit [Hash], [+LOC]. Working Tree clean. Push OK.

### Schritt A — PR #N fixen

**Ist-Zustand:** [PR-Head, Branch, CI-Status]

**Diagnose:** [Welche Fehler aus gh run view --log-failed]

**Auto-Fix:** [Regex-Script + Counts pro File]

**Manuelle Fixes:** [Was der Auto-Fixer nicht fängt]

**Lokale Validierung:**
```bash
$ bash scripts/ci-build.sh --out-dir /tmp/ci-build-full
Build complete: N file(s) ok    # N/N ✅

$ bash .github/workflows/lint-workflows.sh
EXIT=0                            # ✅
```

**Commit + Push:** [Hash], [File-Count]

### Schritt B — Sammel-Issue nach GitHub

**Pattern-Cluster-Analyse:**

| Cluster | Anzahl | Severity | Davon in PR #N gefixt |
|---------|--------|----------|------------------------|
| ...     | ...    | ...      | ...                    |

**Entscheidung:** Ein Sammel-Issue statt N Einzel-Issues. Bessere UX für Maintainer.

**Label-Problem:** Custom-Labels brauchen Maintainer-Rechte. Nur `bug` Standard.

**Ergebnis:** https://github.com/[owner]/[repo]/issues/[N]

## Dateien & Pfade

- [Liste der geänderten Files]

## Ergebnis

**DMZ-Local:** [Status]
**PR #N:** [Status]
**Issue #N:** [Status]

## Entscheidungen

1. [Reihenfolge-Wahl + Begründung]
2. [Strategie-Wahl + Begründung]
3. [Sammel-Issue statt Einzel + Begründung]
4. [Label-Limitation Handling]

## Lessons Learned

1. [CLI-Versions etc.]
2. [Pattern-Checkliste Updates]

## Follow-up für nächste Session

1. [PR CI live beobachten]
2. [Pattern-Auto-Fix-Script persistieren]
3. [Bulk-Fix der restlichen Findings]
