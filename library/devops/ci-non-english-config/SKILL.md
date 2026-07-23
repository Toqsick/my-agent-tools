---
name: ci-non-english-config
description: "Use when user asks for CI linter configuration in non-English projects, typos.toml extend-words, spell-checker for German/French/etc., TOML pitfalls. NOT for English-only projects or non-CI tooling. CI linter configuration for non-English projects (typos, spell-checker, extend-words, TOML pitfalls)."
version: 1.0.0
author: Yuno (2026-07-19)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags:
      - CI
      - linter
      - typos
      - non-english
      - german
      - i18n
      - devops
    lane: worker-flash
    reasoning_effort: high
trigger_keywords: ['english', 'projects', 'toml', 'linter', 'configuration']
keywords: ['english', 'projects', 'toml', 'linter', 'configuration']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# CI Linter Configuration — Non-English / I18N Projects

Configuring and debugging CI linters (`typos`, spell-checkers, etc.) for projects
that contain non-English content — German docs, i18n strings, mixed-language
codebases, technical jargon not in English dictionaries.

## When to Use This Skill

- A CI linter flags "errors" that are actually legitimate non-English words
- A `typos` or `codespell` CI job fails on German/French/Spanish content
- You need to configure `extend-words` for a multilingual project
- You need to download a Rust binary from GitHub releases (architecture-aware)

## Core Pattern: `typos.toml` with `extend-words`

`typos` (crate `crate-ci/typos`) has no built-in knowledge of non-English
orthography. Fix via configuration:

```toml
# typos.toml (at repo root — typos scans upward from scanned file)
[default]
extend-identifiers = []
extend-words = { }
```

### ⚠️ TOML Pitfalls

| Pitfall | Wrong | Right |
|---|---|---|
| **Inline comments** | `"alle" = "alle"  # comment` | Move comment above or to separate line |
| **Case sensitivity** | Only `"alle"` but code has `"Alle"` | Add both: `"alle" = "alle"` + `"Alle" = "Alle"` |
| **extend-identifiers vs extend-words** | Using identifiers for natural language | `extend-identifiers` = code symbols; `extend-words` = comments/commits |

## Step 1: Local reproduction

Before modifying CI config, reproduce the failure locally.

### Download `typos` Binary

`typos` is a Rust binary distributed via GitHub releases. Download
architecture-aware:

```python
import json, urllib.request, platform, tarfile

ARCH_MAP = {
    ("x86_64", "Linux"): "x86_64-unknown-linux-musl",
    ("aarch64", "Linux"): "aarch64-unknown-linux-gnu",
    ("arm", "Linux"): "arm-unknown-linux-gnueabihf",
    ("x86_64", "Darwin"): "x86_64-apple-darwin",
    ("arm64", "Darwin"): "aarch64-apple-darwin",
}

triple = ARCH_MAP.get((platform.machine(), platform.system()))
req = urllib.request.Request(
    "https://api.github.com/repos/crate-ci/typos/releases/latest",
    headers={"Accept": "application/vnd.github.v3+json"}
)
data = json.loads(urllib.request.urlopen(req).read())
tag = data['tag_name'].lstrip('v')
asset_name = f"typos-v{tag}-{triple}.tar.gz"
asset_url = next(a["browser_download_url"] for a in data["assets"]
                 if a["name"] == asset_name)

urllib.request.urlretrieve(asset_url, "/tmp/typos.tar.gz")
with tarfile.open("/tmp/typos.tar.gz") as tar:
    tar.extract("typos", path="/tmp")
```

### Run Locally

```bash
/tmp/typos .                               # scan entire repo (exit code = pass/fail)
/tmp/typos --dump-config 2>&1 | grep -A30 "\[default.extend-words\]"  # verify whitelist
/tmp/typos . 2>&1 | grep -c "error:"       # count errors (0 = clean)
```

### ⚠️ CLI Version Trap

`typos` v1.48.0 **removed** `--no-progress`, `--format`, and similar flags. If
the CI workflow passes flags the local binary doesn't support, it will error.
Fix: use the CI action instead: `crate-ci/typos-action@v1` with `files: .`

## Step 2: Populate `extend-words`

Identify flagged words from local output, add each as `"word" = "word"`.

### Strategy for German Projects

Collect words in these categories:
- **Articles/prepositions:** der, die, das, ein, eine, auf, mit, von, zu, bei...
- **Common verbs:** ist, war, wird, kann, hat, sein, haben, werden...
- **Technical terms:** Prozess, Initial, initialisiert, Status, Syntax, Code...
- **UI labels:** Einstellungen, Dokument, Name, Art, Teil...
- **English words/names in code:** tag, foo, USER, LANG, SETTINGS, Inline...

Target: 0 errors from typos after `extend-words` configuration.

## Step 3: CI Verification

```bash
# Push typos.toml
git add typos.toml && git commit -m "fix(ci): whitelist German words for typos linter"
git push

# Monitor CI
gh run list -R OWNER/REPO --limit 1 --json status,conclusion
gh run view <run-id> -R OWNER/REPO --log-failed

# Verify ONLY the typos-specific job passed (not confused by other CI failures)
gh run view <run-id> -R OWNER/REPO 2>&1 | head -10
# Look for: ✓ Typos (or similar job name)
```

## Step 4: Related Failures That Are NOT Your Problem

| CI Failure | Cause | Action |
|---|---|---|
| `Nothing matches org.freedesktop.Sdk.Extension.llvm18` | Flatpak runtime upstream issue | Ignore — unabhängig vom typos-Fix |
| `Cannot find 'npx'` | Missing Node deps | `npm ci` or `npm install` in CI |
| `golangci-lint timeout` | Resource limits | Bump timeout, not your config |

## Known Limitations

- `typos` has no `--language` flag. It's always English-first. `extend-words` is the only mechanism.
- The word list must be maintained as the project grows. New German words in new files will be flagged until added.
- Different `typos` versions may have different built-in word lists. The config is version-stable (TOML schema hasn't changed across major versions).
