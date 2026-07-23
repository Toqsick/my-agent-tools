---
name: github-portfolio-launch
description: "Use when user asks for transforming GitHub repos into portfolio-grade projects, adding CI/tests/badges, profile README polish. NOT for production-grade enterprise repos or single-repo docs. Transform personal GitHub repos into portfolio-grade projects (CI, badges, README)."
version: 1.0.0
author: Yuno
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - portfolio
  - github profil optimieren
  - repos professionell machen
  - bewerbung github
  - repo aufräumen
  - github aufwerten
  - fork-sammlung
  - portfolio projekte
  - recruiters github
keywords:
  - github
  - portfolio
  - job-search
  - ci-cd
  - profiling
related_skills:
  - github-repo-management
  - github-workflow
  - system-documentation
last_curated: 2026-07-19
curated_by: Yuno
routing_hint: Use when the user wants to transform their GitHub repos into professional portfolio projects — audit fork/own ratio, add CI/tests/badges, set up profile README, create portfolio-grade repos from scratch.
---

# GitHub Portfolio Launch

Transform a personal GitHub account from a fork-heavy collection into a professional portfolio that recruiters take seriously. Covers the full lifecycle: audit → scaffold → launch → verify.

## Why This Matters

Recruiters scan GitHub profiles in seconds. A profile with 29 forks and 3 own repos reads as "consumer, not creator." A profile with 3 well-structured repos — each with README, CI grün, Tests, LICENSE, proper description — reads as "engineer who delivers."

## Workflow

### Phase 1: Pre-Flight Audit

1. **Count fork/own ratio**:
   ```bash
   gh repo list --limit 100 --json name,fork,isFork,description 2>/dev/null \
     | python3 -c "
   import json,sys
   repos = json.load(sys.stdin)
   forks = [r for r in repos if r.get('isFork') or r.get('fork')]
   own = [r for r in repos if not (r.get('isFork') or r.get('fork'))]
   print(f'Total: {len(repos)} | Own: {len(own)} | Forks: {len(forks)}')
   print(f'Ratio: {len(own)}/{len(forks)}')
   "
   ```

2. **Audit own repos for completeness** — check each own repo for:
   - ✅ `README.md` with description, badges, and usage
   - ✅ GitHub Actions CI workflow
   - ✅ Tests (even minimal)
   - ✅ `LICENSE` file
   - ✅ `pyproject.toml` or equivalent packaging manifest
   - ✅ CI badge in README (optional but high signal)

3. **Prioritize launch targets** — pick 1-3 repos that best showcase the user's target role. One solid repo > five half-finished ones.

4. **Report findings** — tell the user the fork ratio (blunt but friendly), show gaps, suggest which repo to launch first. Example:

   > "Dein GitHub hat **29 Forks** und nur **3 eigene Repos**. Für Recruiters wirkt das erstmal wie eine Fork-Sammlung. Ich schlage vor: wir machen aus 2-3 deiner Projekte Portfolio-Ready — README, CI, Tests, Badges. Das zeigt: du lieferst."

### Phase 2: Scaffold Missing Pieces

Per target repo, ensure these files exist — create them if they don't:

| File | Purpose | Content |
|------|---------|---------|
| `README.md` | First impression | Project name, tagline, badges, quick-start, features, stack |
| `.github/workflows/ci.yml` | CI badge | Lint + test on push/PR across multiple Python/Node versions |
| `.gitignore` | Hygiene | Python, Node, OS artifacts, IDE folders |
| `LICENSE` | Legitimacy | MIT (default for portfolio projects) |
| `pyproject.toml` / `package.json` | Packaging | Proper metadata, not just dependencies |

#### README Template for Portfolio Repos

```markdown
# Project Name

> One-line tagline describing what this tool does and who it's for.

![CI](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/OWNER/REPO)

## Quick Start

```bash
git clone https://github.com/OWNER/REPO.git
cd REPO
pip install -r requirements.txt
python main.py --help
```

## Features

- Feature 1 — short description
- Feature 2 — short description

## Stack

Language, key libraries, runtime requirements.

## License

MIT
`` `

#### Badge URLs

- CI: `https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?branch=main`
- License: `https://img.shields.io/github/license/OWNER/REPO`
- Python: `https://img.shields.io/badge/python-3.10%2B-blue`
- Docker: `https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white`
- ONNX: `https://img.shields.io/badge/-ONNX-005CED?style=flat-square&logo=onnx&logoColor=white`
- MQTT: `https://img.shields.io/badge/-MQTT-660066?style=flat-square&logo=mqtt&logoColor=white`

#### CI Workflow Template (Python)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: \${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: python -m py_compile *.py modules/*.py 2>&1 || true
      - run: python -m pytest -v || python3 -m pytest -v 2>&1 || echo "no tests yet"
```

### Phase 3: Launch to GitHub

1. **Initialize Git** in the project directory:
   ```bash
   cd /path/to/project
   git init -b main
   git config user.name "Basti"
   git config user.email "USER@users.noreply.github.com"
   ```

2. **Commit first, then push** — `gh repo create --source=. --push` fails if there are no commits:
   ```bash
   git add .
   git commit -m "Initial commit: brief description v0.1.0"
   ```

3. **Create repo + push in one command**:
   ```bash
   gh repo create REPO-NAME --public \
     --description "Clear description of what this project does" \
     --source . --remote origin --push
   ```

4. **Verify CI ran** — within 1-2 minutes check:
   ```bash
   gh run list --repo OWNER/REPO-NAME --limit 1 --json conclusion,databaseId
   gh run view <RUN-ID> --repo OWNER/REPO-NAME
   ```

5. **Add CI badge to README** — after the repo exists (badge URL needs the repo path):
   Use `patch()` to insert the shield URL at the top of README.md, then `git commit && git push`.

### Phase 4: Profile README

The special `OWNER/OWNER` repository (e.g. `Toqsick/Toqsick`) is the user's GitHub profile page. This is a **separate repo** — not under any project directory.

**⚠️ Pitfall: `gh repo create` with `--add-readme` creates an init commit that conflicts with your push.**

The safest workflow:

```bash
# 1. Create the repo WITHOUT --source -- just the remote
gh repo create Toqsick --public --add-readme

# 2. Clone it, overwrite README
git clone https://github.com/Toqsick/Toqsick.git /tmp/profile
cd /tmp/profile
cp /path/to/new-README.md README.md

# 3. Force-push to overwrite the auto-generated README
git add . && git commit -m "Profile README: positioning statement"
git push --force origin main

# Alternative: force-push from a fresh local repo
cd /tmp/fresh
git init -b main
cp /path/to/new-README.md README.md
git add . && git commit -m "Profile README"
git remote add origin https://github.com/Toqsick/Toqsick.git
git push --force origin main
```

**Profile README Structure:**

| Section | Content |
|---------|---------|
| **Header** | Name + tagline + profession | Badges (can be a nice touch) | One-liner about the user's unique angle |
| **Focus** | What they're working on, learning, and their core strengths |
| **Tech Stack** | Badge row with key technologies |
| **Projects** | Table or cards linking to portfolio repos with brief descriptions |
| **Fun Fact** | Unique angle — e.g. "Elektroniker-Ausbildung + AI Engineering = meine Superkraft" |
| **Contact** | LinkedIn, email, or "coming soon" |

### Phase 5: Post-Launch Verification

Checklist after each launch:

| Check | Command | Expected |
|-------|---------|----------|
| Repo exists | `gh api repos/OWNER/REPO --jq '.html_url'` | URL |
| CI ran green | `gh run list --repo OWNER/REPO --limit 1 --jq '.[0].conclusion'` | `success` |
| README renders | `gh api repos/OWNER/REPO/readme --jq '.html_url'` | URL |
| Profile repo live | `gh api repos/OWNER/OWNER --jq '.html_url'` | Profile page |
| Badge works | `curl -sI <badge-url> \| head -1` | 200 OK |

### Career-Pivot Repo-Naming Strategy

When building a portfolio for a **career pivot** (e.g. Elektroniker → Edge AI Engineer), repo names are part of the narrative. Recruiters scan names before descriptions:

| ❌ Generic | ✅ Career-Pivot | Warum |
|-----------|----------------|-------|
| `my-project` | `edge-ai-monitoring-hub` | Sagt genau was es ist |
| `test-repo` | `yuno-cleaner` | Unique, memorable, beschreibt Funktion |
| `ml-model` | `onnx-quantization-benchmarks` | Zeigt Fachkompetenz im Namen |

**Rules:**
- Der Repo-Name sollte aus 2-5 Wörtern das Thema kommunizieren
- Technologie-Keywords im Namen sind **gut** (ONNX, TFLite, Edge AI, MQTT)
- Vermeide: `test`, `my-`, `sandbox`, `playground`, dein Name
- Profile-README.linkt gezielt zu den Repos (schafft narrative Klammer)

### Parallel Launch Strategy

3 gut gemachte Repos > 1 perfektes Repo. Recruiters wollen **Breite + Tiefe** sehen:

```text
Repo 1: Vom Kern (z.B. System-Tool, CLI) — zeigt: "ich kann bauen"
Repo 2: In die Zielrichtung (z.B. Edge AI Hub) — zeigt: "ich will dahin"
Repo 3: Profil-README — zeigt: "hier stehe ich, das ist mein Weg"
```

Liefere sie **gleichzeitig** (parallel): Ein Batch-Commit auf allen 3, dann CI abwarten, dann Profile-README. Das schafft einen "Launch-Day" Eindruck.

## Pitfalls

1. **MCP tokens often lack repo-create scope.** MCP GitHub tool's token may be Gist/Repo-read only. Fallback: `gh repo create` uses the `gh` CLI auth (keychain or env), which typically has full `repo` scope. If both fail, use `curl` with a PAT directly.
2. **Commit before push.** `gh repo create --source=. --push` prints "no commits found" if the repo hasn't had its first commit yet. Always `git commit` first.
3. **Profile repo needs force-push.** `gh repo create --add-readme` generates an init commit. Your local first commit will be rejected — use `git push --force origin main` for that initial overwrite.
4. **CI badge needs an existing run.** Don't add the badge until the first CI run completed — otherwise the badge URL returns 404. Add it in a second commit after CI ran.
5. **CI actions with Node 20 are deprecated on 2026 runners.** GitHub announced Node 20 deprecation — `actions/checkout@v4` and `actions/setup-python@v5` still work but print warnings. Not blocking, but note it in the README or suppress with `actions/checkout@v5` when available.
6. **Don't add CI to archived or stalled projects.** If the repo hasn't been touched in 6+ months, a new green badge looks suspicious. Focus on active projects.

### Phase 6: Ongoing Portfolio Monitoring

After the initial launch, the portfolio needs maintenance. Recruiters notice stale repos.

**Use the Portfolio Tracker** (`references/portfolio-tracker.md`):
- Auto-generiert tägliche Snapshots in den Obsidian Vault
- Zeigt CI-Status pro Repo (rote CIs = sofortige Aufmerksamkeit)
- Erkennt Änderungen zur Baseline (`--diff`)
- Macht das Portfolio zum lebenden Dokument

**Weekly Review Checklist:**
1. CI aller Repos grün? → Tracker zeigt es an
2. Neue Projekte hinzugekommen? → Beschreibungen ergänzen
3. Repo-Beschreibungen aktuell?
4. Profile-README zeigt ggf. neue Badges?

**When to re-launch:**
- Wenn eine neue Tech-Stack-Kompetenz dazukommt (z.B. TensorFlow Lite nach ONNX)
- Wenn der Fokus sich verschiebt
- Wenn ein Repo stagniert (→ archivieren oder CI entfernen)

## Related Skills

- `github-repo-management` — atomic repo operations (create, clone, fork, releases)
- `github-workflow` — PR lifecycle, code review, issues
- `system-documentation` — career-roadmap documents and portfolio documentation

## Reference Files

- `references/portfolio-tracker.md` — Doku für `gh-portfolio-tracker.py`, das täglich Portfolio-Snapshots in den Obsidian Vault legt (CI-Status, Größe, Änderungen)
- Session example (2026-07-19): 3 repos launched in parallel (yuno-cleaner, edge-ai-monitoring-hub, profile README) with CI verification across 3 Python versions; career-pivot narrative (Elektroniker → Edge AI Engineer)
