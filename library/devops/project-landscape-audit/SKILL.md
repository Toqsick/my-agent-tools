---
name: project-landscape-audit
description: |
  Use when inventorying projects across a home directory or workspace, checking repository health, mapping duplicates or forks, or planning archival and consolidation.
  NOT for auditing a single known repository, deleting or moving projects during reconnaissance, or treating directory names as proof of project relationships.
  Builds an evidence-backed project inventory with Git activity, content summaries, relationship mapping, and prioritized recommendations.
version: 1.2.0
author: Hermes Agent (Yuno)
license: MIT
metadata:
  hermes:
    tags:
    - repo-audit
    - landscape
    - project-inventory
    - cleanup
    - consolidation
    - git-audit
    related_skills:
    - hermes-maintenance
    - codebase-inspection
    - system-documentation
    - session-state-audit
lane: worker-heavy
reasoning_effort: xhigh
prerequisites:
  commands:
  - git
  - du
  - stat
  - diff
trigger_keywords: ['projects', 'directory', 'repository', 'mapping', 'project']
keywords: ['projects', 'directory', 'repository', 'mapping', 'project']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['directory-structure-audit']
---


# Project Landscape Audit — Methodology

> **Class-level skill:** Scanning a directory of projects (repos, workspaces, data-drops) to produce a structured inventory with relationship mapping, health indicators, and consolidation recommendations.

## When to Use

- User asks for "Scout", "Landschaftsanalyse", "Repo-Review", "Projektübersicht", "Was liegt wo?"
- Before a cleanup / consolidation sprint
- After a migration (new machine, new OS) — validate that all projects survived
- When onboarding to a user's machine for the first time
- When the user says "Ich hab viel rumprobiert, sag mir was wichtig ist"

## When NOT to Use

- Single-repo deep-dive → use `codebase-inspection` (LOC metrics) or `system-documentation` (build docs)
- Session-state evaluation → use `session-state-audit`
- Hermes-specific maintenance triage → use `hermes-maintenance`
- General system cleanup → use `yuno-cleaner`

## The Scan Pipeline (6 phases)

### Phase 1 — Inventory Scan

Build a master table of all candidate directories using a shell pipeline:

```bash
# Identify project-like directories at the home level
# Look for: .git/, src/, *.py, *.js, package.json, README.md, Makefile
# Exclude: .snap, .cache, .config, .local, .steam, .wine, node_modules/

# Quick scan for all directories that look like projects:
for d in *; do
  if [ -d "$d" ]; then
    sz=$(du -sh "$d" 2>/dev/null | cut -f1)
    has_git=$(test -d "$d/.git" && echo "git" || echo "no-git")
    lastmod=$(stat -c '%y' "$d" 2>/dev/null | cut -d. -f1)
    echo "$d | $has_git | $sz | $lastmod"
  fi
done
```

**Output:** Flat table of `dirname | git-status | size | last-modified`.

**Key:** At this stage, include *all* project-like dirs even if they look redundant. Filtering happens in Phase 4.

### Phase 2 — Git Remote & Activity Deep-Dive

For each Git repo, collect:

```bash
# Remote URL
git -C "$dir" remote get-url origin 2>/dev/null

# Current branch
git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null

# Last commit
git -C "$dir" log -1 --format='%cd %s' --date=short 2>/dev/null | head -c 100

# Commit count
git -C "$dir" rev-list --count HEAD 2>/dev/null

# Uncommitted changes
git -C "$dir" status --short 2>/dev/null | wc -l
```

**Output:** Extended table with remote-url, branch, last-commit, commit-count, dirty-files.

### Phase 3 — README & Content Scan

For each project (git and no-git alike), peek at the contents:

```bash
# README headline
head -15 "$dir/README.md" 2>/dev/null | grep -o '^# [^#].*'

# Top-level structure
ls -la "$dir" 2>/dev/null | head -15

# Detect common markers:
# - package.json → Node/TS project
# - Cargo.toml → Rust project
# - go.mod → Go project
# - setup.py/pyproject.toml → Python project
# - Dockerfile → Container-based project
# - .src files → GreyScript project
```

**Output:** Per-project one-paragraph description with technology markers.

### Phase 4 — Relationship Mapping (Critical)

This is where the real value lives. Three **distinct** relationship types that look the same but have different merge semantics:

#### A. Identical remote, different branch (Worktree/Fork-in-place)
```bash
# Check if two repos point to the same remote URL
# If yes → they are branches of the same upstream, NOT independent repos
# Decision: merge via git worktree or git submodule, not via deletion
cmd="git -C \"$dir1\" remote get-url origin"
cmd="git -C \"$dir2\" remote get-url origin"
```

**Resolution:**
- Same remote, different branch → **Worktree candidate** (keep one master, `git worktree add` the others)
- Same remote, same branch, different HEAD → **Outdated clone** (delete, re-clone)
- Same remote, identical content but different remotes with tokens → **Auth-variant** (keep cleaner, discard token-embedded)

#### B. Shared remote, fork lineage
```bash
# Compare remotes — if they share a base repo but are different forks
# e.g. github.com/nesquena/hermes-webui vs github.com/franksong2702/hermes-webui-desktop-companion
# Decision: independent repos with separate upstreams
```

**Resolution:** Keep separate, note upstream relationship.

#### C. Content overlap without shared remote
```bash
# Same README header → fork/split
diff <(head -20 "$dir1/README.md") <(head -20 "$dir2/README.md")

# Duplicate filenames
comm -12 <(ls "$dir1" | sort) <(ls "$dir2" | sort)

# Same CHANGELOG structure
# Decision: merge via git history transplant or manual consolidation
```

**Resolution:** Merge into master repo (older → newer), keep history via `git remote add` + `fetch` + `merge --allow-unrelated-histories`.

#### D. Cross-project code duplication
```bash
# Same helper files in different projects
# e.g. telegram_helper.py in both yuno-voice-bot/ and yuno-cleaner/
# Decision: extract into shared/ package
```

**Resolution:** Extract shared helpers into `shared/` or `lib/` subdirectory.

#### E. Clone Depth Analysis — When multiple repos share the same remote

When Phase 2 reveals that 2+ repos point to the **same** remote URL, don't stop at
"they're related." Run a structured depth analysis to quantify divergence, detect
credential leaks, and produce a specific consolidation plan.

```bash
# --- STEP 1: Branch divergence quantification ---
REMOTE_REPO=https://github.com/owner/repo.git  # from remote get-url origin

for CLONE in /path/to/clone1 /path/to/clone2 /path/to/clone3; do
  echo "=== $CLONE ==="
  git -C "$CLONE" fetch origin main --depth=1 2>&1 | tail -2

  # Ahead/behind main (two numbers: ahead behind)
  git -C "$CLONE" rev-list --left-right --count origin/main...HEAD 2>&1

  # Unique commits (not on main)
  git -C "$CLONE" log --oneline origin/main..HEAD 2>&1 | head -10

  # File-level diff vs main
  git -C "$CLONE" diff --name-only origin/main..HEAD 2>&1 | head -30

  # Last commit date
  git -C "$CLONE" log -1 --format='%ci %s'
done
```

**Interpretation:**
- `0 ahead, N behind` → clone is at main, **N commits old** (outdated — re-clone or pull)
- `N ahead, 0 behind` → clone has **N unique commits** on this branch (feature work)
- `N ahead, M behind` → **diverged branch** (both unique work + stale base — rebase needed)
- Different clones, same HEAD SHA → **true duplicates** (one can be deleted)
- Same files changed in different clones → **conflict risk** (two branches touch the same code)

```bash
# --- STEP 2: CI configuration comparison ---
for CLONE in /path/to/clone1 /path/to/clone2; do
  echo "=== $(basename $CLONE) ==="
  ls "$CLONE/.github/workflows/" 2>/dev/null || echo "(no CI)"
  cat "$CLONE/.github/workflows/ci.yml" 2>/dev/null | head -20
done

# Check if CI triggers for the branches in question
# Common pitfall: CI runs only on main/develop, NOT on feature branches
# → local feature work won't be tested by CI until a PR is opened
```

```bash
# --- STEP 3: Test coverage comparison ---
for CLONE in /path/to/clone1 /path/to/clone2; do
  echo "=== $(basename $CLONE) ==="
  echo "  Test files:"
  find "$CLONE" -path '*/node_modules' -prune -o -path '*/.git' -prune -o \
    \( -name '*.test.ts' -o -name '*.test.js' \) -print 2>/dev/null | wc -l
  echo "  src/ top-level:"
  ls "$CLONE/src" 2>/dev/null
  echo "  CHANGELOG snippet:"
  head -15 "$CLONE/CHANGELOG.md" 2>/dev/null | head -5
  echo "  package.json name+version:"
  grep -E '"name"|"version"' "$CLONE/package.json" 2>/dev/null | head -4
done

# Key insight: a clone with more test files + more src/ dirs = more complete.
# A clone with 0 test files but identical package.json = partial snapshot.
```

```bash
# --- STEP 4: Credential & hygiene audit ---
for CLONE in /path/to/clone1 /path/to/clone2 /path/to/clone3; do
  echo "=== $(basename $CLONE) ==="

  # Extract remote URL and flag any embedded credentials
  URL=$(git -C "$CLONE" config --get remote.origin.url)
  if echo "$URL" | grep -q '@'; then
    TOKEN=$(echo "$URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    if echo "$TOKEN" | grep -qE '^(gh[op]_|github_pat_)'; then
      echo "  🚨 TOKEN-EMBEDDED REMOTE! (${TOKEN:0:3}...${TOKEN: -4})"
    fi
  fi

  # .git/config file permissions
  PERMS=$(stat -c '%a' "$CLONE/.git/config" 2>/dev/null)
  echo "  .git/config mode: $PERMS"
  if [ "$PERMS" != "600" ] && [ "$PERMS" != "640" ]; then
    echo "  ⚠️  WARNING: .git/config is group-readable!"
  fi

  # Credential helper (should be set, NOT token-in-URL)
  HELPER=$(git -C "$CLONE" config --get credential.helper 2>/dev/null)
  echo "  credential.helper: ${HELPER:-(none)}"

  # Untracked files that should be gitignored
  UNTRACKED=$(git -C "$CLONE" ls-files --others --exclude-standard 2>/dev/null)
  if [ -n "$UNTRACKED" ]; then
    echo "  Dirty (untracked):"
    echo "$UNTRACKED" | head -5
  fi
done
```

**Credential leak detection cheatsheet:**

| Pattern found in URL | Risk | Action |
|---|---|---|
| `gho_*` token (classic OAuth) | 🔴 CRITICAL — langlebig, kein Auto-Expire | Sofort revoken auf github.com/settings/tokens |
| `ghp_*` token (classic PAT) | 🔴 CRITICAL — full API access often | Sofort revoken, fine-grained ersetzen |
| `github_pat_*` token (fine-grained) | 🟠 HIGH — scoped but still access | Revoken, on `.git/config` mode 600 setzen |
| No credential helper set (token-in-URL instead) | 🟠 HIGH — credentials in git history risk | `git config credential.helper libsecret` |

### Phase 5 — Health & Risk Assessment

For each project, flag:

| Indicator | Risk | Action |
|-----------|------|--------|
| No git, active (last 7d) | **HIGH** | Git init immediately |
| No git, inactive (>30d) | LOW | Document as archive |
| Git, dirty (uncommitted) | MEDIUM | Commit or stash |
| Git, 0 commits fetched ever | MEDIUM | Check remote connectivity |
| >1 GB with .git/ | MEDIUM | Check LFS / .git size |
| Empty directory | LOW | Remove |
| Duplicate content | HIGH | Merge resolution |
| Contains binary packages (.deb/.AppImage) | LOW | Note as installer artifacts |

### Phase 6 — Report Generation

Write a structured Markdown report to a path the user can easily find (e.g. `~/Schreibtisch/...` or `~/docs/reports/`):

**Required sections:**

1. **Master Table** — All projects: name, git?, last activity, one-sentence purpose, domain, recommendation
2. **Clone/Fork Family Map** — Per-family relationship diagram showing which repos share remotes, which are masters, which are worktrees
3. **Consolidation Candidates** — Concrete merge proposals with 3-phase breakdown (Sofort / Phase 2 / Phase 3)
4. **Git Init Candidates** — No-git projects sorted by activity (most active first)
5. **Cleanup Targets** — Empty/stale directories to delete
6. **Retain-As-Is** — What NOT to touch and why

**Format:**
```markdown
# Home Scout — Project Landscape Audit
**Scan-Datum:** YYYY-MM-DD
**Scope:** ~/ (project directories only)
**Tabu:** <excluded paths>

## 1) Master Table
| Ordner | Git? | Letzte Aktiv | Zweck | Vorschlag |
|---|---|---|---|---|
...

## 2) Clone/Fork Families
...

## 3) Consolidation Proposals
...

## 4) Git Init Candidates
...

## 5) Cleanup Targets
...
```

## Pitfalls

1. **`git remote get-url origin` is NOT enough.** Two repos can share the same remote URL but be on *different branches* (worktree pattern) or *different commits on the same branch* (outdated clone). Always collect: remote URL + current branch + HEAD commit SHA + commit count.

2. **README similarity does not prove identity.** A copied README template (common in monorepo splits) doesn't mean the code is the same. Always verify by comparing actual source files, not just README headers.

3. **Don't assume "no git" means "new."** A no-git project with last-modified date >30 days ago is probably an abandoned experiment. A no-git project with last-modified date <7 days is a risk.

4. **Beware of Git repos with token-embedded remotes.** `git remote get-url origin` may expose tokens in the URL (e.g. `https://user:gho_xxx@github.com/...`). Handle with care:
   - **DO extract the token format** (first 3 + last 4 chars) to classify risk (`gho_*` = classic OAuth, `ghp_*` = classic PAT, `github_pat_*` = fine-grained)
   - **DO check `.git/config` file mode** — `stat -c '%a' .git/config` should be `600` or `640`. Mode `664` means group-readable.
   - **DO check credential helper** — `git config credential.helper`. If none is set AND there's a token in the URL, it means the token is the only auth mechanism — high risk of history leak.
   - **DO NOT test the token against GitHub API** during a read-only audit. The liveness check (`401 vs 200`) requires an outbound network call with the cleartext token, which crosses the read-only boundary. Document the format and recommend revocation instead.
   - **DO NOT transcribe the full token** into the report. Mask it: `gho_2X...Lz1g`.
   - **Immediate recommendation:** Token revoken on github.com/settings/tokens, then `git remote set-url origin` without credentials, set up `credential.helper libsecret` instead.

5. **Don't move or delete anything during the audit.** The scout is read-only. Write the report, present recommendations, let the user decide. Moving is the user's job after the audit.

6. **Parallel scanning saves time.** Independent reads (size, git status, README, remote URL) can be batched in a single shell loop. Don't serialize them.

7. **Tabu-Ordner respektieren.** If the user has specified exclusions (e.g. `~/.hermes/`, `~/docs/system/`), enforce them. If the report would cover them, mark them explicitly as excluded.

8. **Large projects (>1 GB) need size notation in the report** so the user can gauge disk impact at a glance. Especially important when consolidation involves moving or cloning.

9. **`.gitignore` hygiene matters — especially for runtime artifacts.** Check if any untracked files exist that SHOULD be ignored (e.g. `logs/audit.jsonl`, `.env.local`, `*.log`). If the audit finds dirty files that aren't in `.gitignore`, flag them in the report — a future `git add .` could commit secrets. Include the recommended `.gitignore` line.

10. **Credential helpers should exist, and token-in-URLs should not.** If a repo has NO credential helper set AND the remote URL contains credentials, that means:
    - The token is the ONLY way to authenticate
    - Every `git clone` / `git submodule update` replays the token into the new repo's `.git/config`
    - A `git push` that fails prints the full URL (with token) in the error message
    - **Fix:** `git config credential.helper libsecret` + `git remote set-url origin https://github.com/owner/repo.git`

11. **`.git/config` file permissions are a risk indicator.** Mode `664` means any process on the system can read it. Mode `777` would be catastrophic. The default for a fresh clone is `600` (user-only). Flag anything > `640` in the report. Fix: `chmod 600 .git/config`.

## Related Skills

- **`hermes-maintenance`** — For Hermes-specific multi-repo pitfalls (three V7 variants on same remote)
- **`codebase-inspection`** — For deep LOC/language breakdown of a single repo after the landscape scan identified it as interesting
- **`system-documentation`** — For documenting individual build/fix workflows discovered during the audit
- **`session-state-audit`** — For pausing mid-audit and resuming cleanly across model switches
