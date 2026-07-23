---
name: github-workflow
description: |
  Use when you need to use the github-workflow workflow and its documented procedures.
  NOT for unrelated tasks outside the github-workflow workflow.
  Provides focused guidance for github-workflow.
version: 1.2.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - GitHub
    - Git
    - Pull-Requests
    - Code-Review
    - Issues
    - Repositories
    - CI/CD
    - Automation
    related_skills:
    - coding-agents
    lane: worker-flash
    reasoning_effort: high
    agent: Engineer
    routing_hint: '**Agent-Scope:** Code-Tasks (build / fix / refactor / debug / review).
      Off-scope: visual design, long-form copy, data modeling — say ''this is Designer/Writer/Analyst''s
      territory'' and return to Yuno.


      Routing-Spec: `yuno-team-routing`.

      '
trigger_keywords: ['workflow', 'github', 'need', 'documented', 'procedures']
keywords: ['workflow', 'github', 'need', 'documented', 'procedures']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'hermes-admin', 'multi-agent-pitfalls-cheatsheet']
---

---
# GitHub Workflow — Cheatsheet

End-to-end GitHub operations: auth, PRs, code review, issues, and repo management. Each section shows `gh` first, then `curl` fallback.

## Auth Setup

See `references/github-auth.md` for full guide. Quick reference:
- **gh CLI:** `gh auth login` or `echo "<token>" | gh auth login --with-token`
- **HTTPS:** `git config --global credential.helper store`
- **SSH:** `ssh-keygen -t ed25519` → add key at https://github.com/settings/keys
- **API:** `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/...`

### MCP GitHub vs gh CLI Fallback

Hermes uses two separate auth paths — credentials are NOT shared. MCP GitHub 401s? Switch to `gh` CLI immediately. See `references/mcp-github-quirks.md` for full details including MCP response traps (sentinel SHA, "already exists" lies, cooldown behavior).

### ⚠️ Wenn ALLE drei GH-Tools gleichzeitig tot sind — `git clone` über HTTPS rettet dich

**Symptom (verifiziert 2026-07-10):** `gh auth status` → "token in keyring is invalid" · GitHub-MCP-Tool (search_repositories, list_repositories, search_code) → "401 Bad credentials" · Firecrawl/managed web tools → nicht konfiguriert.

**Du brauchst aber nur Public-Repo-Read für Recon** (z.B. Repo-Architektur prüfen, README lesen, Stack analysieren, bevor du entscheidest ob du es clonen willst). `git clone` über HTTPS braucht **keinen Auth**:

```bash
# Funktioniert IMMER für Public-Repos, auch wenn gh/MCP/Firecrawl alle tot sind
git clone --depth 1 https://github.com/OWNER/REPO.git /tmp/recon-REPO

# Danach normal weiterreisen mit lokalem Git + read_file:
cat /tmp/recon-REPO/README.md
find /tmp/recon-REPO -name "*.yaml" -path "*/config/*" | head -5
```

**Wann dieser Fallback greift (Mental-Notiz):** Wenn du ein fremdes Repo analysieren sollst und alle 3 Tool-Pfade 401/nicht-konfiguriert zurückgeben, **erst `git clone` versuchen** bevor du "kann ich nicht" sagst. Bei Private-Repos brauchst du weiterhin einen Token — dann entweder `gh auth refresh` (interaktiv, braucht User) oder die `gh api` Fallback-Kette aus `references/mcp-github-quirks.md`.

**Push-Authenticated-Work:** Für alles was **schreibt** (issues, PRs, push) brauchst du zwingend einen funktionierenden Auth-Pfad. `git clone` HTTPS ist Read-Only-Helden-Fallback, kein Workaround für Push.

### "Was wurde kürzlich gepusht?" Research

Use `git ls-remote origin` as ground truth. See `references/push-audit-research.md` for full verification matrix.

## PR Lifecycle

See `references/github-pr-workflow.md` for full guide.

Quick pattern:
```bash
git checkout -b feat/description
git add . && git commit -m "feat: description"
git push -u origin HEAD
gh pr create --title "feat: description" --body "Summary\n\nCloses #42"
gh pr checks --watch
gh pr merge --squash --delete-branch
```

## Code Review

See `references/github-code-review.md` for full guide.

Quick patterns:
```bash
git diff main...HEAD --stat              # scope
git diff main...HEAD                     # full diff
gh pr view 123                            # PR details
gh pr diff 123                            # PR changes
gh pr review 123 --approve --body "LGTM"  # approve
```

## Issue Management

See `references/github-issues.md` for full guide and pitfalls (missing `number` field, read-only vs mutating triage).

Quick commands:
```bash
gh issue create --title "Bug: X" --body "..." --label "bug" --assignee "@me"
gh issue list --state open --label "bug"
gh issue edit 42 --add-label "priority:high"
gh issue comment 42 --body "Investigated — working on fix"
gh issue close 42
```

## Repository Management

See `references/github-repo-management.md` for full guide.

Quick commands:
```bash
gh repo clone owner/repo
gh repo create my-project --public --clone
gh repo fork owner/repo --clone
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh secret set API_KEY --body "value"
gh run list --limit 10
```

### Documentation Health Audit

See `references/documentation-health-audit.md` for 10-phase audit pattern.

## GitHub Automation Scripts

See `references/github-automation-patterns.md` for full automation script structure, cron integration, and pitfalls.

Quick structure:
```bash
scripts/
  hermes-automation.py    # Main CLI with subparsers

python3 scripts/hermes-automation.py issue --title "Bug: X"
python3 scripts/hermes-automation.py status --json > results/status.json
```

## Batch File Push via Contents API

See `references/batch-file-push-contents-api.md` for full pattern and pitfalls (409 stale-SHA, MD5 verification, template reusability).

When pushing same file to multiple repos:
```bash
CONTENT_B64=$(base64 -w0 /path/to/file)
COMMIT_MSG="docs: add CONTRIBUTING.md"

push_one() {
  local repo="$1" branch="$2"
  local body=$(jq -n --arg m "$COMMIT_MSG" --arg c "$CONTENT_B64" --arg b "$branch" \
    '{message:$m, content:$c, branch:$b}')
  gh api -X PUT "repos/OWNER/$repo/contents/PATH" --input - <<<"$body"
}

push_one repo-a main
push_one repo-b main
```

## Skill Conversion & Config-Sync Workflow

See `references/skill-conversion-config-sync.md` for full 7-step workflow.

When converting skills or pushing to populated repos:
1. Inventory target repo with `gh repo view`
2. Use atomic `gh repo create --source=. --push` with `init.defaultBranch main`
3. Use HTTPS-with-token from `gh auth token` for push
4. Use flat-id namespaces (`skills/hub-imported/<hub-id>/`)
5. Commit on feature branch if default branch is populated
6. Always run secrets-preflight before committing

## GreyHack/Greybel CI Pattern

See `references/greybel-ci-pattern.md` for full CI-first pattern.

For GreyHack repos with `greybel-js`:
- Create explicit CI issues before coding
- Branch from develop
- Update build script to scan active `.src` directories
- CI installs greybel-js, runs script, uploads artifact
- Quote `"on":` in workflow YAML to avoid yamllint warnings

See `references/greyhack-greybel-ci.md` for session-specific reference.

## Read-only CI Failure Diagnosis

See `references/ci-failure-diagnosis.md` for full workflow and pitfalls (empty 404s, JSONDecodeError, `needs:` skip chain, stale issue tables).

Quick pattern:
```bash
# 1. Find failing run
gh run list -R OWNER/REPO --limit 10 --json databaseId,status,conclusion

# 2. Get failed step log
gh run view <run-id> -R OWNER/REPO --log-failed | grep -E '##\[error\]|exit code'

# 3. Read workflow YAML
gh api 'repos/OWNER/REPO/contents/.github/workflows/<file>.yml?ref=main' \
  -H 'Accept: application/vnd.github.raw'

# 4. Verify file paths from issue actually exist
gh api 'repos/OWNER/REPO/git/trees/main?recursive=1' | jq '.tree[].path'
```

## Cron Monitoring

See `references/github-automation-patterns.md` for full cron prompt template.

Quick command:
```bash
hermes cronjob create \
  --schedule "0 9 * * *" \
  --name "repo-daily-status" \
  --prompt "Check git status, open issues, open PRs. If nothing changed: [SILENT]"
```

## References

- `references/github-auth.md` — Auth setup (HTTPS, SSH, gh CLI, API detection)
- `references/github-pr-workflow.md` — PR lifecycle (branch, commit, CI, merge)
- `references/github-code-review.md` — Code review (local, PR, inline)
- `references/github-issues.md` — Issue management
- `references/github-repo-management.md` — Repo management (clone, create, fork, releases, secrets, actions)
- `references/github-automation-patterns.md` — Automation scripts, clean JSON output, cron jobs, shell escaping
- `references/mcp-github-quirks.md` — MCP GitHub vs gh CLI Fallback, MCP response traps
- `references/push-audit-research.md` — "Was wurde kürzlich gepusht?"-Recherche
- `references/batch-file-push-contents-api.md` — Batch File Push via Contents API (409 stale-SHA, MD5 verification)
- `references/cross-repo-pr-flow.md` — Fork → Upstream cross-repo PR workflow (proven 2026-07-11 against NousResearch/hermes-agent #62526) — owner-qualified `--head`, reviewer-ping pitfall, `git rm -r` collateral-deletion recovery
- `references/worktree-hygiene-foreign-files.md` — Stash-before-push pattern for branches whose worktree carries unrelated untracked files left by other agents/sessions (validated 2026-07-13 with `feat/idempotency-key-patch`)
- `references/skill-conversion-config-sync.md` — Skill conversion & config-sync workflow
- `references/greybel-ci-pattern.md` — GreyHack/Greybel CI build verification patterns
- `references/greyhack-greybel-ci.md` — Session-specific GreyHack Greybel CI reference
- `references/documentation-health-audit.md` — Repo documentation audit (10 phases)
- `references/ci-failure-diagnosis.md` — Read-only CI-Diagnose (gh CLI workflow, pitfalls)
- `references/batch-contributing-md-push-2026-07-07.md` — Session-Referenz: Batch-Push via Contents API
- `references/mcp-github-quirks-batch-push-2026-07-07.md` — MCP-Tool-Antwort-Fallen: curl-Fallback