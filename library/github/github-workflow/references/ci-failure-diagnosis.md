# Read-only CI Failure Diagnosis (gh CLI workflow)

When the user reports "CI is red", "build fails", "issue #N says build broken", or asks to debug CI without committing anything — use this recipe. It is **read-only by design**: no commits, no workflow edits, no `--push`, no PR comments unless explicitly requested.

## Workflow

```bash
# 1. Find the failing run
gh run list -R OWNER/REPO --limit 10 --json databaseId,status,conclusion,name,headBranch,event,createdAt

# 2. Get the failed-step log (mixes labels + ANSI + real errors — filter)
gh run view <run-id> -R OWNER/REPO --log-failed 2>&1 | grep -E '##\[error\]|exit code [0-9]+|Process completed' | head -40

# 3. Read the workflow YAML that owns the failing job
gh api 'repos/OWNER/REPO/contents/.github/workflows/<file>.yml?ref=main' \
  -H 'Accept: application/vnd.github.raw'

# 4. Cross-reference with issue body (always read the actual issue body, not the summary)
gh issue view N -R OWNER/REPO --json title,body,labels

# 5. Verify every file path mentioned in the issue actually exists on main
#    (issue tables often cite stale paths after a rename or repo restructure)
gh api 'repos/OWNER/REPO/git/trees/main?recursive=1' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(e['path'] for e in d['tree'] if e['path'].endswith('.src')))"

# 6. Fetch each surviving file with raw endpoint + sed to the exact lines
gh api 'repos/OWNER/REPO/contents/<path>?ref=main' -H 'Accept: application/vnd.github.raw' | sed -n '20,32p'
```

## Output Shape

The deliverable is a Markdown report in `~/docs/system/<repo>-ci-diagnose-<date>.md` with these sections:

1. **TL;DR table** — CI-Workflow / Helper-Skript / Issue A / Issue B / real root cause
2. **Which jobs fail?** — full job graph + which step inside each failing job, distinguishing "skipped because `needs:`" vs "actually failed"
3. **Root-cause analysis** — split into "actual CI killer" + "outdated issues that name the wrong files"  
4. **Concrete fix proposals** — patch-style diff snippets for each, ranked P0/P1/P2
5. **Verification commands** — what to run after the fix to confirm green
6. **Issue comment drafts** (do NOT post unless asked) — wording the user can copy into the issue thread
7. **Repro commands** — copy-pasteable for next session

Always footer the report with `**Analyse-Modus:** read-only (gh-CLI + GitHub-API only, keine Code-Mutation)` so it's clear no writes happened.

## Pitfalls — these all bit on 2026-07-07 Toqsick/greyscripts triage

**`gh api …/contents/<path>?ref=main` with `Accept: application/vnd.github.raw` returns empty body for paths that don't exist** — looks like a successful empty response, not an error. Combine with `git/trees/main?recursive=1` to verify path existence first; if the tree lists the path, the empty body means a different branch or a renamed file. Verified pattern: `bin/ps.src` from Issue #43 was a stale path — the file lived under `greyhack-tools/ps/ps.src` (and had already been fixed). Tree-API before raw fetch = zero wasted fetches.

**`gh api …/contents/<path>` (no `Accept: raw` header) returns JSON with `content_base64` field — NOT `content`.** Earlier docs and Stack Overflow snippets say `base64.b64decode(d['content'])`. That field doesn't exist on the Contents API — it's `content_base64`. Piping JSON to `python3 -c "import json,sys,base64; print(base64.b64decode(json.load(sys.stdin)['content']))"` returns `KeyError`. Use `content_base64` or, better, switch to the raw endpoint to avoid the dance entirely.

**JSONDecodeError "Extra data: line 1 column 128" from `python3 -c "json.load(sys.stdin)"`** — means `gh api` output got piped into something and `gh` wrote two JSON-like blocks to stdout (the API response + a status/log line). Switch to the raw endpoint (`-H 'Accept: application/vnd.github.raw'`) to skip the JSON wrapper entirely. Do not try to "fix" the JSON parser — the problem is the wrapper.

**`needs:`-chain jobs are skipped, not failed.** When job 1 fails with exit 1, job 2 (which has `needs: job-1`) shows as "skipped" in the run summary. Don't trust "skipped" as a green signal — trace back to find which upstream job actually failed. The "real" CI killer is often job 1, not the job the issue title names. Verified: Toqsick/greyscripts issue #30 said "Greybel build failt" but the actual red job was `lint-yaml` (yamllint default rules vs. no override) → `greybel-build` was only skipped.

**Stale issue tables — verify before fixing.** Issue bodies often contain tables with `| Datei | Zeile |` listings. Before patching any file at the listed line, verify the file exists at the listed path on the current `main` and the line still contains what the issue claims. Repos rename directories, move files into `core/` or `lib/` subfolders, and earlier bug-sweep commits fix issues without closing them. Treat issue tables as **hypotheses** until verified against `git/trees/main?recursive=1` + raw file fetch. Verified: Issue #43 listed 5 `bin/ps.src:24`-style sites — none of those paths existed on `main` (`bin/` was reduced to `.gitkeep`). The real fixes lived under `greyhack-tools/` and were already applied.

**Read existing helper scripts before flagging "missing tooling".** A repo may already have a helper script (e.g. `lint-workflows.sh`) that the CI workflow simply doesn't call. The diagnosis is "wrong wiring", not "missing tool". Check `.github/workflows/lint-*.sh` and `scripts/ci-*.sh` first. Verified: Toqsick/greyscripts had `lint-workflows.sh` with the correct yamllint override — `ci.yml` just didn't invoke it.

**`exit_code: 2` at the end of `gh run view … --log-failed` is normal.** The run failed (that's why you're reading the log). Don't report this as a new error.

**`process.completed with exit code 1` ≠ test failures inside the job.** GitHub Actions reports the step exit code as the job exit code. Look for `##[error]` markers in the log to find which command actually returned non-zero.

## When the real cause is upstream tooling, not the issue

A common pattern: issue A says "X is broken", issue B says "Y is broken", but the CI run they both point to failed in a completely different job (`lint-yaml`, `setup-node`, `setup-python`). Steps to take:

1. State explicitly: "Issue #A beschreibt X. Realer Fail-Stand ist Y (anderer Job, andere Ursache)." — don't bury the lede.
2. For each cited issue, check whether the cited fix would even be observable in the failing CI run. Often the cited failure mode is downstream of an upstream block.
3. Propose P0 fix for the actual CI killer (usually a 1-line workflow edit), then P1+ for the issue's original concern.
4. Suggest the issue gets a comment with status update rather than being closed prematurely.