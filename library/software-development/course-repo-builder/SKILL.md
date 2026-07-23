---
name: course-repo-builder
description: "Use when user asks to turn a YouTube video, lecture, or course into a real runnable repository with structured docs, templates, scripts, tests, and remote verification. NOT for a transcript dump or an arbitrary repository refactor. Acquires the source, maps learning structure, builds the repo, runs checks, pushes, and verifies the remote result."
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['the', 'repository', 'and', 'remote', 'course-repo-builder']
keywords: ['repository', 'remote', 'user', 'asks', 'turn']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['youtube-to-course-repo', 'skill-install-workflow', 'youtube-content']
---


# course-repo-builder

## What this skill does
Convert a video-based course or tutorial into a **real, runnable repository** — not a transcript dump. The repo becomes a working artifact: docs/ as a structured N-block course, agent/config/templates as copy-pasteable boilerplate, scripts that lint cleanly, and remote-verified after push.

## When to load
Trigger when the user:
- Pairs a video file or YouTube URL with words like *Kurs*, *Vorlage*, *Tutorial*, *course*, *repo for X*
- Asks to "build a repo from this video" / "this tutorial as starter"
- Drops a downloaded `.webm/.mp4` from a learning playlist and says "mach daraus…"

## Pipeline (5 steps)

### Step 1 — Source acquisition
- **Local video file** (>50 MB?): skip `video_analyze`, fetch the YouTube transcript instead via the
  `youtube-content` skill's `fetch_transcript.py` script. YouTube transcripts are 100x cheaper than
  local re-transcription and usually available.
- **Just a URL**: same — `python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py "URL" --text-only --language de,en > /tmp/transcript.txt`
- **Verify non-empty**: `wc -c /tmp/transcript.txt`. Empty → retry without `--language` → if still empty, fallback to local whisper.

### Step 1.5 — Optional transcript polishing

Before mapping structure, consider a **proper-name correction pass** on the raw transcript. ASR auto-transcripts consistently mangle tool names, platform names, and technical terms (`Cloud Code→Claude Code`, `Gitub→GitHub`). A cleaner transcript makes block-boundary detection more reliable.

- Extract ground truth from the video description first.
- Use targeted regex replacements (not LLM) — deterministic and cheap.
- Handle semantic disambiguation: "Cloud Code" is a product name, "in der Cloud" is cloud computing.

**Full technique:** `media-tools` skill → `references/transcript-polishing.md`

### Step 2 — Map structure, don't dump
Read the transcript in 4 windows of ~20k chars. Identify the **natural block boundaries** the speaker already uses (most tutorials say "jetzt kommen wir zu X", "Block N", "nächster Punkt"). Typical N = 6–10. **Never** ship the raw transcript as a doc — restructure it.

### Step 3 — Repo layout (canonical)
```
repo-root/
├── README.md              ← table-of-contents linking every block
├── docs/01-<topic>.md     ← one block per file, N files
├── agent/                 ← (if relevant) core files as templates
├── config/                ← (if relevant) config.yaml with lint-clean YAML
├── workflows/             ← (if relevant) cron/heartbeat specs + register.sh
├── skills/<name>/SKILL.md ← (if relevant) one example skill
├── setup.sh               ← one-command installer with backup-protection
├── .gitignore             ← secrets/, runtime memory/, OS junk
└── register-*.sh          ← CLI-registration scripts (echo + commented real call)
```
Each file: docs on Deutsch, code comments auf Deutsch, concrete commands/paths/templates, not abstract theory.

### Step 4 — Static checks before commit
- `bash -n *.sh` for every shell script — fix before commit.
- YAML lint via write_file auto-check (if it surfaces errors, fix).
- Markdown files: no lint, but verify structure manually.
- Check `find . -type f -not -path './.git/*' | sort` matches your mental tree.

### Step 5 — Push + REMOTE-VERIFY
This is the load-bearing step. Don't claim success until you've fetched the remote tree.
```bash
git add -A && git commit -m "feat: <one-line summary>" && git push origin HEAD
# MANDATORY verification — never trust the push exit code alone:
gh api repos/OWNER/REPO/git/trees/BRANCH?recursive=1 --jq '.tree[] | select(.type=="blob") | .path' | sort
```
The remote tree list MUST equal your local file list. If anything's missing → investigate before claiming success.

## Style rules (Basti's preferences — encoded, not assumed)
- **German docs**, English code identifiers. Code-Kommentare auf Deutsch.
- **No archaisch, no überformell.** Yuno tone in README + skill files.
- **Concrete > abstract.** "Führe X aus" not "du könntest X erwägen". Real config, real scripts, real defaults.
- **Decisions as 2–4 options**, never open-ended questions.
- **Trade-offs explicit** (e.g. "OAuth billiger aber rate-limited, API-Key flexibel aber unkalkulierbar").
- After build: offer the user 2 concrete next-step options, not "what do you want?"

## Pitfalls
- ❌ **Dumping the raw transcript** as docs/ — always restructure into blocks.
- ❌ **Trusting `git push` exit code** as proof of success. ALWAYS `gh api .../git/trees` to verify.
- ❌ **Trying `video_analyze` on a 336 MB local file** — over the 50 MB limit. Use YouTube transcript instead.
- ❌ **MCP GitHub token 401** → fall back to `gh` CLI (logged in as Toqsick). Don't stop on MCP failure.
- ❌ **Skipping `bash -n`** on shell scripts — syntax errors in setup.sh are silent until first run.
- ❌ **Auto-overwriting existing config files** — backup or prompt first.
- ❌ **Shipping secrets in config.yaml** — only templates with `SecretRef` placeholders.
- ❌ **Forgetting .gitignore** for `out/`, `secrets.yaml`, `*.key`, `daily/` memory files.

## Reference
- `references/example-maxclaw-2026-07-03.md` — end-to-end worked example: OpenClaw video → MaxClaw repo (336 MB local video bypassed via YouTube transcript, MCP-token 401 fallback to gh CLI, 8-block structure, remote-verified push, errors-and-fixes table).

## Verification checklist before declaring done
- [ ] `bash -n` clean on every `.sh`
- [ ] YAML lint clean on every `.yaml`
- [ ] Remote tree list equals local file list (Step 5)
- [ ] README links every block doc
- [ ] At least one runnable artifact (script, config, or skill), not just docs
- [ ] After completion: 2 concrete follow-up options offered to user