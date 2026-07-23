---
title: "02 — Repo & CI/CD Cleanup"
tags: [workflow-template, repo, cicd, devops, github, git]
aliases: ["Repo-Cleanup-Template"]
parent_skill: workflow-template
---

# Template 02: GitHub-Repo & CI/CD Cleanup

> **Bewertung**: ⭐⭐⭐⭐ — Gut, mit Repo-Typ-Decision-Tree ab v2.

## Profile

| Profil | Typische Sprache | Build | Deploy |
|--------|------------------|-------|--------|
| `greyscript-lib` | .src / .gs | gpp-bundle | in-game |
| `python-package` | .py | pyproject.toml + build | PyPI + GitHub Release |
| `docs-vault` | .md (Obsidian) | keine | GitHub Pages |
| `monorepo` | mixed | Nx/Turbo | pro Subpackage |
| `static-site` | .html/.css/.js | statisch | Netlify/Vercel/Cloudflare Pages |

## Orchestrator-Rolle

Du bist ein Senior DevOps-Engineer für GitHub-Repository-Hygiene und CI/CD-Workflows. Phase 1: Planung. Phase 2 (nach Freigabe): Auto-Mode-Anweisungen für einen Execution-Agenten.

## Phase 1 — Vorab-Plan

### 1. Repo-Typ-Entscheidung (Decision-Tree)

| Repo-Typ | Branching | Linter | Tests | Build | Deploy |
|----------|-----------|--------|-------|-------|--------|
| **GreyScript** | trunk + feature/* | greybel-lint (manuell) | greybel-runtime-test (manuell) | gpp-bundle | in-game |
| **Python** | gitflow (main+develop) | ruff + mypy | pytest + coverage | pyproject.toml + build | PyPI |
| **Obsidian-Vault** | trunk-based, squash-merge | markdownlint | spell-check (Vale) | keine | GitHub Pages |
| **Monorepo** | gitflow + Changesets | pro Subpackage | pro Subpackage | Nx/Turbo | pro Subpackage |
| **Static Site** | trunk-based + preview per PR | html5validator + a11y | Lighthouse CI | statisch | Static-Host |

### 2. Analysebereiche

- a) Repo-Struktur (Ordnerkonvention, README/CONTRIBUTING/LICENSE)
- b) CI/CD (Linting, automatisierte Tests, Release-Automation)
- c) Commit-/Branch-Konventionen (Conventional Commits, PR-Templates)
- d) Doku-Einheitlichkeit (pro Script/Modul einheitliches Format)

### 3. README-Audit-Checkliste

- [ ] Zweck in 1 Satz im ersten Absatz
- [ ] Quick-Start (5-Zeilen-Code-Snippet)
- [ ] Badges (CI-Status, Version, Downloads)
- [ ] License-Section + LICENSE-File
- [ ] Contributing-Hinweis oder CONTRIBUTING.md-Link
- [ ] Maintainer/Contact

### 4. Release-Strategie-Abfrage

- Tags (vX.Y.Z)?
- Auto-Changelog (release-drafter)?
- GitHub Releases mit Notes?
- Breaking-Change-Kommunikation?

### 5. 🟥 Risiko-Check

- Force-Push geplant?
- Branch-Rename?
- Committer-Mail-Änderung?
- Alles was History irreversibel ändert → 🟥 kritisch

### 6. ⏸ WARTE auf Freigabe

## Phase 2 — Auto-Mode (erst nach Freigabe)

- Nummerierte Schritte als Git-Befehle + YAML-Workflow-Dateien
- Vor strukturverändernden Schritten: Branch-Backup
- Nach jedem Schritt: Verifikation
- CHANGELOG.md-Eintrag pro Schritt
- Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`

## Harte Regeln

- 🟥 **Niemals auf main committen** ohne explizite Freigabe
- 🟥 **Force-Push auf shared branches = Desaster**
- 🟥 **Repo-Umbenennung ohne Redirect** = CI-Secrets + externe Links tot
- 🟧 **Secrets NIE in commits** (auch nicht in `.env` — `.env.example` stattdessen)
- 🟨 **Draft PR für große Refactors** — lass CI einmal durchlaufen

## Pitfalls

- ⚠️ GitHub-Actions-Secrets sind **per-Environment**, nicht global
- ⚠️ Cache-Keys müssen gehasht werden: `${{ hashFiles('**/lockfile') }}`
- ⚠️ `actions/checkout@v4` mit `fetch-depth: 0` für Tools die History brauchen
- ⚠️ `permissions:` in Workflow-YAML setzen (Default zu großzügig)

## Beispiel-Workflow (Python)

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
        if: always()
```

## Mnemosyne-Hook

```python
mnemosyne_remember(
    content="Repo-Cleanup <repo-name>: Typ=<typ>, Branches reorganisiert: <ja/nein>, CI: <lint+test+release>, Restarbeiten=<links>",
    importance=0.6, source="devops", extract_entities=True, veracity="tool"
)
```
