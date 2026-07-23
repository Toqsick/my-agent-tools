# Hermes Co-Pilot Workflow for GreyHack

Automation patterns for combining GreyHack development with GitHub workflow management.

## Architecture

```
Hermes Chat
    │
    ├── scripts/hermes-automation.py
    │       ├── issue     → gh issue create
    │       ├── branch    → git checkout/create/push
    │       ├── build     → greybel build
    │       ├── verify-all → all .src files
    │       ├── pr        → gh pr create
    │       ├── status    → daily status report
    │       └── roadmap   → ROADMAP.md parsing
    │
    └── Cron-Job (daily 09:00)
            └── greyscripts-daily-status
```

## Key Commands

```bash
# Issue creation
python3 scripts/hermes-automation.py issue \
  --title "tool: routerinfo" \
  --label "new tool" \
  --milestone v0.3.0

# Branch from issue
python3 scripts/hermes-automation.py branch --issue 5 --name feature/routerinfo

# Build with verification
python3 scripts/hermes-automation.py build --file tools/routerinfo.src --verify

# Verify all source files
python3 scripts/hermes-automation.py verify-all

# Create PR
python3 scripts/hermes-automation.py pr \
  --issue 5 \
  --title "feat: routerinfo Closes #5"

# Status report
python3 scripts/hermes-automation.py status --json > results/status.json
```

## Build Verification Checks

For each `.src` file:
- [ ] `greybel build` succeeds
- [ ] No raw `exit()` calls (use `fail()` instead)
- [ ] Return values are checked (`if result == null`)
- [ ] Header comment exists (license/purpose)
- [ ] Only double quotes in strings
- [ ] PR links issue (`Closes #X`)

## Cron Job Pattern

```bash
hermes cronjob create \
  --schedule "0 9 * * *" \
  --name "greyscripts-daily-status" \
  --prompt "Check git status, open issues, open PRs, milestone progress. If nothing changed: [SILENT]"
```

**Prompt template:**
```
1. cd /home/bratan/greyscripts
2. git status --short
3. python3 scripts/hermes-automation.py milestone --name v0.3.0
4. python3 scripts/hermes-automation.py milestone --name v0.4.0
5. python3 scripts/hermes-automation.py milestone --name v1.0.0
6. gh issue list --state open --limit 20 --json number,title,labels,milestone
7. gh pr list --state open --limit 10 --json number,title,author

If nothing changed: [SILENT]
If changes: report open issues by label, milestone progress %, open PRs, next step from ROADMAP.md
```

## Pitfalls

1. **Clean JSON output**: When `--json` is used, output ONLY JSON. No progress logs or status text before the JSON object.
2. **Shell escaping**: Backticks in `gh pr comment --body "..."` get executed. Use single quotes or `--body-file`.
3. **Subagent rate limits**: Multi-agent orchestration for GitHub tasks may hit HTTP 429. Parent should verify claims and complete critical fixes directly.
4. **Working tree cleanliness**: Clean `__pycache__/` before status reports to avoid false dirty reports.
5. **greybel import paths**: `greybel build` resolves `import_code` relative to `/root/`, not the actual source directory. Use the deploy script or fix paths with `sed`.
