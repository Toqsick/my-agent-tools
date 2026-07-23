# GitHub PR Workflow (Reference)

This topic is covered by the standalone skill `github/github-pr-workflow`.

**Load that skill directly** via `skill_view(name="github-pr-workflow")` when the
task is specifically about the PR lifecycle (branch → commit → open → CI → merge).

This file exists only as a routing pointer from the umbrella `github-workflow` skill.
The full content (7 sections, `gh` + `git+curl` fallbacks, CI auto-fix loop) lives in
the dedicated skill to keep this umbrella skill scannable.

## Quick reference (for in-context lookup without loading the full skill)

| Action | gh | git + curl |
|--------|-----|-----------|
| Create PR | `gh pr create --title "..." --body "..."` | `curl -X POST .../pulls -d '{...}'` |
| Check CI | `gh pr checks --watch` | `curl .../commits/$SHA/status` |
| Merge | `gh pr merge --squash --delete-branch` | `curl -X PUT .../pulls/N/merge` |
| View logs | `gh run view <id> --log-failed` | `curl .../runs/<id>/logs` → unzip |

For branch naming, conventional commits, auto-fix loop, and full code samples,
load `github-pr-workflow`.
