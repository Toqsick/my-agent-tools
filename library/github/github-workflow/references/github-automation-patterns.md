# GitHub Automation Patterns

Reusable Python automation scripts for GitHub workflows.

## Structure

```bash
scripts/
  hermes-automation.py    # Main CLI: issue, branch, build, pr, status, etc.

# Typical commands:
python3 scripts/hermes-automation.py issue --title "Bug: X" --label bug --milestone v1.0.0
python3 scripts/hermes-automation.py branch --issue 42 --name feature/toolname
python3 scripts/hermes-automation.py pr --issue 42 --title "feat: tool Closes #42" --body "..."
python3 scripts/hermes-automation.py status --json > results/status.json
```

## Key Patterns

1. **Single script, multiple subcommands** — use `argparse` with subparsers for `issue`, `branch`, `build`, `pr`, `status`, etc.
2. **`gh` CLI as primary interface** — all GitHub API calls through `gh api`, `gh issue`, `gh pr`
3. **Clean JSON output for cron jobs** — when `--json` is passed, output ONLY valid JSON (no status text, no progress logs). Put human-readable output in the non-JSON path.
4. **Build verification** — for code repos, add a `verify-all` command that builds/tests all source files and writes results to `results/`.
5. **Cron integration** — schedule daily status checks with `hermes cronjob create`. Use `[SILENT]` protocol when nothing changed.
6. **Shell escaping** — when passing multi-line strings to `gh pr comment --body`, wrap in single quotes or write body to a temp file to avoid shell interpreting backticks and `$`.

## Cron Monitoring

```bash
set -euo pipefail
# Daily status check
hermes cronjob create \
  --schedule "0 9 * * *" \
  --name "repo-daily-status" \
  --prompt "Check git status, open issues, open PRs. If nothing changed: [SILENT]"
```

## Pitfalls

- **Backticks in shell strings**: `gh pr comment --body "Text with `code`"` will execute `code`. Use single quotes or `gh pr edit --body-file` / `gh pr create --body-file`.
- **JSON pollution**: If `--json` outputs anything before the JSON object, downstream parsers fail. Gate all print statements with `if not json_output`.
- **Subagent rate limits**: When using multi-agent orchestration for GitHub tasks, subagents may hit API rate limits. Parent should verify claims and complete critical fixes directly.
- **Working tree cleanliness**: Before JSON status reports, clean `__pycache__/` and other generated artifacts to avoid false "dirty" reports.
- **Duplicate PR cleanup**: When creating PRs programmatically across multiple branches, check for stale duplicate PRs before reporting status. Close duplicates with `gh pr close <num> --comment "Duplicate of #<target>"`.