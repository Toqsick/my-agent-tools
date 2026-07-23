# Batch File Push via Contents API

When the user wants the **same file** (e.g. `CONTRIBUTING.md`, `LICENSE`, `.github/CODEOWNERS`, a policy file) pushed to **multiple repos in one shot**, prefer the Contents API (`PUT /repos/{o}/{r}/contents/{path}`) over `git clone` × N: faster, no local working tree, atomic per-repo commit.

## Pattern (gh CLI, parallel across repos)

```bash
# Pre-encode once, reuse for every repo
CONTENT_B64=$(base64 -w0 /path/to/file)
COMMIT_MSG="docs: add CONTRIBUTING.md"

push_one() {
  local repo="$1" branch="$2"
  local body
  body=$(jq -n --arg m "$COMMIT_MSG" --arg c "$CONTENT_B64" --arg b "$branch" \
    '{message:$m, content:$c, branch:$b}')
  local resp
  resp=$(gh api -X PUT "repos/OWNER/$repo/contents/PATH" \
    -H "Accept: application/vnd.github+json" \
    --input - <<<"$body" 2>&1)
  if echo "$resp" | jq -e '.commit.sha' >/dev/null 2>&1; then
    echo "OK  $repo@$branch  commit=$(echo "$resp" | jq -r '.commit.sha' | head -c7)"
  else
    echo "FAIL $repo@$branch  $(echo "$resp" | head -c 200)"
  fi
}

push_one repo-a main
push_one repo-b main
push_one repo-c master   # some repos use master, some main
```

## 409 Conflict Pitfall - Retry Without SHA

**`409 Conflict` "is at <real-SHA> but expected <stale-SHA>":** `gh api PUT contents/` caches a stale HEAD-SHA from an earlier fetch in the same process. The repo HEAD moved (parallel worker, CI, web commit) but the request still carries the old expected blob SHA. **Fix:** retry **without** the `sha` field — the API then treats the request as a fresh Create-or-Update against current HEAD. To overwrite an existing file intentionally, fetch the current `sha` first and pass it explicitly.

```bash
# Retry without sha (Create path)
body=$(jq -n --arg m "$COMMIT_MSG" --arg c "$CONTENT_B64" \
  '{message:$m, content:$c, branch:"main"}')
gh api -X PUT "repos/OWNER/$repo/contents/PATH" --input - <<<"$body"

# Or with current sha (Update path)
CUR_SHA=$(gh api "repos/OWNER/$repo/contents/PATH" --jq .sha 2>/dev/null)
body=$(jq -n --arg m "$COMMIT_MSG" --arg c "$CONTENT_B64" --arg s "$CUR_SHA" \
  '{message:$m, content:$c, branch:"main", sha:$s}')
```

## MD5 Cross-Check Verification

**Push returning `200 OK` + `commit.sha` ≠ content-is-correct.** Verify byte-identicality after a batch push with an MD5 cross-check (catches CRLF/LF/BOM drift, truncation, accidental overwrites):

```bash
SOURCE_MD5=$(md5sum /path/to/file | awk '{print $1}')
for repo in repo-a repo-b repo-c; do
  remote_md5=$(gh api "repos/OWNER/$repo/contents/PATH" --jq '.content' 2>/dev/null \
    | base64 -d 2>/dev/null | md5sum | awk '{print $1}')
  [ "$remote_md5" = "$SOURCE_MD5" ] && echo "MATCH  $repo" || echo "DIFFER $repo"
done
```

## Other Pitfalls

- **Default branch matters.** `gh api repos/OWNER/REPO --jq .default_branch` is the source of truth — never trust user-supplied branch names in a batch task. Pushing to a non-existent branch returns 422, not 409.
- **Content field is base64-with-embedded-newlines.** GitHub inserts `\n` every 60 chars. `jq -r '.content' | base64 -d` works; `base64 -d` directly on the raw JSON string fails silently. Use `-w0` on encode side for round-trip determinism.
- **When NOT to use this pattern:** files > ~100 MB (Contents API truncates), repos with branch protection that block direct main commits (use a feature branch + PR), or files with merge-conflict potential (e.g. existing `CONTRIBUTING.md` with project-specific content — overwriting silently is destructive).
- **Domain-specific templates may not be reusable.** When copying a `CONTRIBUTING.md` / `LICENSE` / template from one repo, **read it first** and check that the language/structure fits the target repos. A GreyScript template with `importcode` / `fail()` / `shell` rules is useless in a TypeScript/React project. Fall back to a generic template if the source is too domain-specific. Verified 2026-07-07: greyscripts-`CONTRIBUTING.md` (38 lines, German, GreyScript conventions) was not reusable across 4 mixed repos (hermes-v7, MaxClaw, sse-dashboard, multi-agent-workflows) — fell back to a 14-line generic MIT-licensed template.