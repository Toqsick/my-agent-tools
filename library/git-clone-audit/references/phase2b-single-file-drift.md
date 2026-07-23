# Phase 2b — Single-File Deep Drift Analysis

Wenn der Cross-Clone-Diff zeigt, dass eine bestimmte Datei Änderungen enthält,
und beide Klone auf dasselbe Remote zeigen, reicht `diff -u` allein nicht aus.
Die Datei kann auf Git-Ebene **mehrere Revisionen durchlaufen haben**, die im
Working-Tree eines Klons angekommen sind, im anderen nicht. Diese Phase klärt
**welche** Version wann wo liegt und warum.

## Schritt 1 — Git-History beider Klone für diese Datei

```bash
# History in Klon A: welche Commits haben diese Datei verändert?
cd /pfad/zu/klonA
git log --all --oneline -- pfad/zur/datei.src   # Alle Commits in diesem Repo

# History in Klon B — gleiche Datei
cd /pfad/zu/klonB
git log --oneline -- pfad/zur/datei.src         # Nur im aktiven Branch
```

**Wichtig:** Der Unterschied zwischen `--all` und ohne `--all` ist der kritische
Befund:
- `git log -- pfad/src.x` → Commits die im **aktuellen Branch** die Datei betrafen
- `git log --all -- pfad/src.x` → **ALLE** Commits im Repo, die die Datei betrafen

Wenn `git log --all -- file` 3 Einträge zeigt, aber `git log -- file` nur 1
(in Klon B), dann existieren die Fix-Commits zwar im Repo-History, wurden aber
**nie in den Working-Tree dieses Klons übernommen** (nicht gemerged,
Merge-Konflikt übersehen, falscher Branch).

## Schritt 2 — MD5-Cross-Validation (Der kritische Beweis)

```bash
# MD5 des Working-Trees beider Klone
md5sum /pfad/zu/klonA/pfad/zur/datei.src   # Ergebnis A
md5sum /pfad/zu/klonB/pfad/zur/datei.src   # Ergebnis B

# MD5 jedes relevanten Commit-Inhalts in Klon B (oder A)
git show <commit-hash>:pfad/zur/datei.src | md5sum

# Vergleichstabelle:
echo "Working-Tree A:    $(md5sum A/path | awk '{print $1}')"
echo "Working-Tree B:    $(md5sum B/path | awk '{print $1}')"
echo "Commit featha:  $(git show featha:path | md5sum | awk '{print $1}')"
echo "Commit fixb:    $(git show fixb:path | md5sum | awk '{print $1}')"
```

**Interpretation:**
- Wenn Working-Tree A MD5 = Commit `featha` MD5 → Klon A hat Fix featha
- Wenn Working-Tree B MD5 ≠ Commit `fixb` MD5 → Klon B hat Fix NICHT übernommen
- Wenn beide MD5 unterschiedlich → Drift bestätigt, Ursache durch Commit-History klärbar

## Schritt 3 — Bugfix-Kategorisierung

Dokumentiere welche Art von Änderung die Datei durchlaufen hat:

| Kategorie | Pattern in Commits | MoT-Impact |
|-----------|-------------------|------------|
| Syntax-Fix | `fix typo`, `remove invalid char` | Niedrig |
| Logic-Fix | `fix null pointer`, `handle edge case` | Hoch |
| API-Change | `update function signature`, `deprecate` | Kritisch |
| Feature-Add | `add new function`, `extend capability` | Mittel |

## Schritt 4 — Funktions-Inventar (optional)

Bei komplexen Dateien kann es hilfreich sein, die Funktions-Signaturen zu
extrahieren um zu sehen welche Funktionen hinzugefügt/geändert wurden:

```bash
# Funktions-Definitionen extrahieren (GreyScript)
grep -E '^(function |proc )' pfad/zur/datei.src | sort -u
```

**Outcome:** Klare Antwort auf "welche Version liegt wo" und "warum sind sie unterschiedlich".