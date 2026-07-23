# Hermes Automation for greyscripts — Session Notes

## What was built (2026-06-18)

Created `scripts/hermes-automation.py` in `/home/bratan/greyscripts/`:

- Python 3 script, 482 lines
- Uses `gh` CLI for GitHub API operations
- Uses `greybel` for GreyScript builds
- Supports: issue, branch, build, pr, milestone, roadmap commands

## Key implementation details

### Label colors
```python
LABELS = {
    "bug": "d73a4a",
    "enhancement": "a2eeef",
    "new module": "0e8a16",
    "new tool": "7057ff",
    "docs": "cfd3d7",
    "wontfix": "ffffff",
    "in progress": "fbca04",
    "security": "b60205",
    "help wanted": "008672",
}
```

### Milestones from ROADMAP.md
- `v0.3.0`: Phase 1 (decypher, metaxploit, list-lib, password-gen)
- `v0.4.0`: Phase 2 (lzw, progress-bar, routerinfo, hermes)
- `v1.0.0`: Phase 3+ (all core modules stable)

### Cron job created
```text
Name: greyscripts-daily-status
Schedule: 0 9 * * *
Job ID: 009b472a967f
```

The cron checks milestone progress, open issues, open PRs, and recommends next steps.

## Pitfalls discovered

1. **Local PDFs can't be read by web_extract**
   - Use `pdftotext` via terminal instead
   - `pdftotext "/path/to/file.pdf" -`

2. **gh CLI needs local git context**
   - If not in repo, use `--repo Toqsick/greyscripts`
   - Cron jobs should use explicit repo flags

3. **Current branch matters**
   - Was on `feature/ci-cd-workflow` when automation was added
   - After merge, switch to `develop` for new work

4. **Silent cron protocol**
   - Cron responds `[SILENT]` when nothing changed
   - Prevents notification spam

## Usage examples

```bash
# Create issue
python3 scripts/hermes-automation.py issue \
  --title "[BUG] safeBuild prüft bin-Pfad nicht auf leer" \
  --label bug \
  --milestone v0.3.0

# Create branch from issue
python3 scripts/hermes-automation.py branch --issue 5 --name feature/filecore

# Build GreyScript
python3 scripts/hermes-automation.py build --file src/filecore.src

# Create PR
python3 scripts/hermes-automation.py pr \
  --issue 5 \
  --title "feat: filecore Closes #5"

# Check milestone
python3 scripts/hermes-automation.py milestone --name v0.3.0

# List roadmap tools
python3 scripts/hermes-automation.py roadmap
```

## Natural language shortcuts for Hermes

| User says | Hermes does |
|---|---|
| "Erstell Issue: [BUG] ..." | Create issue with label + milestone |
| "Nimm Issue #5, erstell Branch" | Branch `issue-5` from develop |
| "Build filecore" | `greybel build src/filecore.src` |
| "PR für #5 fertig" | PR with `Closes #5` |
| "Status v0.3.0" | Milestone progress |
| "Roadmap zeigen" | List all planned tools |
