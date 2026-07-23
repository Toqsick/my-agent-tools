# Codex CLI — Full Reference

Extracted from the `codex` skill. Complete guide for OpenAI Codex CLI.

## Prerequisites
- **Install:** `npm install -g @openai/codex`
- **Auth:** `OPENAI_API_KEY` or Codex OAuth (`~/.codex/auth.json`)
- **Requires git repository** — Codex refuses to run outside one
- **pty=true required** — Codex is an interactive terminal app

## One-Shot Tasks
```bash
codex exec "Add dark mode toggle"  # exits when done
```

For scratch work:
```bash
cd $(mktemp -d) && git init && codex exec "Build snake game in Python"
```

## Background Mode (Long Tasks)
```bash
terminal(command="codex exec --full-auto 'Refactor auth'", workdir="~/project", background=true, pty=true)
# Returns session_id — monitor with process(action="poll"|"log")
```

## Key Flags
| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution |
| `--full-auto` | Sandboxed, auto-approves file changes |
| `--yolo` | No sandbox, no approvals |
| `--sandbox danger-full-access` | No Codex sandbox (for service contexts) |

## Hermes Gateway Caveat
In gateway/service contexts, `workspace-write` sandboxing may fail (bubblewrap/user-namespace errors). Use:
```bash
codex exec --sandbox danger-full-access "<task>"
```

## PR Reviews
```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main
```

## Parallel Issue Fixing with Worktrees
```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
codex --yolo exec "Fix #78. Commit when done." workdir=/tmp/issue-78 background=true pty=true
# After: git push -u origin fix/issue-78 && gh pr create ...
```

## Batch PR Reviews
```bash
git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'
codex exec "Review PR #86. git diff origin/main...origin/pr/86" background=true pty=true
```

## Rules
1. **Always use `pty=true`**
2. **Git repo required** — use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots**
4. **`--full-auto` for building**
5. **Background for long tasks**
6. **Don't interfere** — monitor with poll/log
7. **Parallel is fine** — multiple Codex processes for batch work
