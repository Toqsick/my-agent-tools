# Single-File Deep Drift Analysis — xmem.src Case Study

**Datum:** 2026-07-05  
**Datei:** `greyhack-tools/xmem/xmem.src` (GreyScript, 22 Funktionen)  
**Klone:** A = 30-Library (900 LOC) vs B = 10-Projekte (889 LOC)  
**Remote:** Beide `Toqsick/greyscripts`, aber unterschiedliche Branches

## Problem

Zwei Klone desselben Repos, dieselbe Datei, unterschiedliche LOC.  
Clone A hat `exit()` und korrigierte `list[-1]` → `parts[parts.len-1]`.  
Clone B hat `exit` (bare) und `list[-1]` (negativer Index).  
Wer ist canonical? Warum?

## Lösung — 4-Schritt-Methode

### Schritt 1 — Git-History mit `--all`-Dual-Scan

```bash
cd /pfad/zu/klonB
git log --oneline -- greyhack-tools/xmem/xmem.src
# → 1 Eintrag: 2359823 feat: add xmem.src

git log --all --oneline -- greyhack-tools/xmem/xmem.src
# → 3 Einträge: feat + 45e2735 + 129dd63
```

**Befund:** Die Fix-Commits existieren im Repo-History von Klon B, aber der
aktuelle Branch (`develop`) hat sie nie übernommen. `git diff HEAD` ist leer.

### Schritt 2 — MD5-Cross-Validation

```bash
# Working-Trees
md5sum A/path/xmem.src   # → 3787806bbcf60af80490c40feb50fe40
md5sum B/path/xmem.src   # → 03f0821c257e37937d968c0742396f2d

# Git-Commits (in Klon B ausgeführt)
git show 2359823:greyhack-tools/xmem/xmem.src | md5sum  # feat    → 03f0821c…
git show 45e2735:greyhack-tools/xmem/xmem.src | md5sum  # repair  → adfcaf48…
git show 129dd63:greyhack-tools/xmem/xmem.src | md5sum  # negIdx  → 3787806b…
git show HEAD:greyhack-tools/xmem/xmem.src      | md5sum  # HEAD    → 03f0821c…
```

**Kreuztabelle:**

| Quelle | MD5 | Entspricht |
|--------|-----|------------|
| Clone A Working-Tree | `3787806b…` | `git show 129dd63` |
| Clone B Working-Tree | `03f0821c…` | `git show 2359823` (feat) |
| Clone B HEAD (develop) | `03f0821c…` | feat (unverändert, trotz Fixes in History) |

**Befund:** Clone A = fix-Code (129dd63), Clone B = feat-Urversion (2359823).
Der Merge der Cluster-Fixes hat die xmem.src nie erreicht.

### Schritt 3 — Diff-Kategorisierung

`diff -u` → 61 geänderte Zeilen, 16 Hunks. Kategorisiert:

| # | Hunk-Bereich | Änderung | Kategorie |
|---|-------------|----------|-----------|
| 1 | Z. 9-15 | ASCII-Logo: `draw = draw +` vs direktes `print` | ⚪ Kosmetik |
| 2 | Z. 46 | `exit()` → `exit` | 🔴 Regression (B) |
| 3 | Z. 193-194 | `// shell.start_terminal` auskommentiert vs aktiv | 🔴 Regression (B) |
| 4 | Z. 193-194 | Fehlendes `end if` | 🔴 Bugfix (fehlt in B) |
| 5 | Z. 229 | `exit()` → `exit` | 🔴 Regression (B) |
| 6 | Z. 276-277 | 2× fehlendes `end if` | 🔴 Bugfix |
| 7 | Z. 374 | `exit()` → `exit` | 🔴 Regression (B) |
| 8 | Z. 500-502 | `item[-1]` → `parts[parts.len-1]` | 🔴 Bugfix (NP #42) |
| 9 | Z. 537 | `parentPath[0:-1]` → `parentPath[0:parentPath.len-1]` | 🔴 Bugfix (NP #42) |
| 10 | Z. 545-546, 563-566, 595 | 3× `exit()` → `exit` | 🔴 Regression (B) |
| 11 | Z. 602-605, 647, 654-655 | 3× `get_shell.host_computer` lokalisiert | 🟢 Refactor |
| 12-16 | Rest | 1–3 Zeilen Verschiebung | ⚪ Kosmetik |

**Gewichtung:** 5 Bugfixes (fehlen in B) + 2 Refactors + 5 Regressions (B)
+ 4 Kosmetik → **A ist Canonical.**

### Schritt 4 — Funktions-Inventar

```bash
grep -nE '^\w+\s*=\s*function\(' xmem.src
```

Beide Klone: **22 identische Funktionen** (gleicher Name, gleiche Parameter).
→ API-Vertrag stabil → einfaches `cp` ersetzt B, kein manueller Merge.

## Ergebnis

**Canonical = Clone A** (30-Library).  
Migrations-Schritte:
```bash
cp ~/30-Library/greyscripts/greyhack-tools/xmem/xmem.src \
   ~/10-Projekte/10-active/greyhack-tools/greyhack-tools/xmem/xmem.src
# Branch: fix/xmem-cluster-1-and-2 von develop
# Commit: "fix(xmem): apply cluster-1/2 fixes (NP #42, structural #41)"
```
