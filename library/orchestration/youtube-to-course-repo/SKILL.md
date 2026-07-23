---

name: youtube-to-course-repo
description: |
  Use when you turn a YouTube video (lecture, tutorial, talk) into a self-improving course repository — transcripts, summaries, exercise generation, evaluation suite — that improves over multiple passes.
  NOT for single-summarization tasks (use transcript-summary), non-YouTube media, or static educational PDFs (different pipeline).
  Pipeline that converts a YouTube video into a complete course repo: transcript → outline → exercises → auto-graded tests, with self-improvement feedback loops.
version: 0.1.0
author: Hermes
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - YouTube
    - Transcript
    - Course
    - Repo
    - Self-Improve
    - Schwarm
    - Obsidian
license: MIT
trigger_keywords: ['youtube', 'video', 'into', 'self', 'course']
keywords: ['youtube', 'video', 'into', 'self', 'course']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['youtube-creator', 'course-repo-builder', 'media-tools']
---

# YouTube → Course Repo

Turns a YouTube tutorial or lecture into a **runnable, self-improving course-shaped repository**: transcript polished, N subagent-bees build the N blocks in parallel, a single hermes session merges + tests + commits locally, the user gets a cron-driven self-improve loop (morning plan / afternoon check / evening reflect / weekly review). Validated end-to-end 2026-07-15 on Daniel Igl's `omNPKjk1p7o` (61 min, German auto-captions → 5-block course, 70 tests passing, 14 xfailed, 4 cron jobs, Obsidian MOC + daily-note integration). Does NOT push to GitHub, run real OpenAI calls, build Canva templates, or set up FunnelCockpit/Digistore24 — those are explicit user actions.

## When to Use

- User shares a YouTube URL and says "mach ein Repo draus", "transkribier + Plan", "Tutorial als Vorlage", "Kurs-Repo"
- User wants a video distilled into actionable phases with code, scripts, and tests
- User explicitly says "self-improve" or "cron-Loop dazu" alongside a video
- Source is a **tutorial/lecture**, not a casual vlog — i.e. has identifiable phases / steps / code shown on-screen

## Prerequisites

- **Python 3.12** in venv with `youtube-transcript-api`, `pyyaml`, `pytest`
- **git** available; user must be ok with local-only commits (no auto-push)
- **Obsidian vault** at `~/Dokumente/Obsidian Vault/` with existing `03 Projekte/`, `06 Daily Notes/`, MOC files
- **Telegram bot** configured via `~/.hermes/.env` (for cron nudges)
- User has confirmed the **target niche/angle** before parallel-bee dispatch (4-bee cost: 15-20 min wall-clock, several thousand tokens)

## How to Run

**Trigger: `/plan` + a YouTube URL + 1-sentence goal.** Skill runs through the 5 stages below. If the user types `[/learn]` after the workflow finishes, distill this skill from the conversation history.

```
User:    /plan https://youtube.com/watch?v=omNPKjk1p7o — anonymes TikTok-Business als Course-Repo mit Self-Improve-Loop
Yuno:    [loads youtube-content + course-repo-builder skills, starts Stage 1]
```

## Quick Reference

| Tool | Use for |
|---|---|
| `web_extract` with oEmbed URL | Title, channel, upload date (no API key) |
| `terminal` running `youtube-transcript-api` | Auto-captions fetch (DE/EN/whatever) |
| `delegate_task` with `tasks=[…]` | Parallel subagent swarm (one bee per block) |
| `cronjob` action=`create` with `script=` | `no_agent=true` cron jobs that call bash scripts in `~/.hermes/scripts/` |
| `mnemosyne_remember` | 2-3 facts per session: project start, flow preference, lessons-learned |
| `write_file` to `~/.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` | Mandatory plan deliverable before any code change |
| `terminal` running `pytest tests/ -q` | Verify the merged repo's tests pass |

## Procedure

### Stage 1 — Plan (mandatory, before any code)

1. `write_file` plan to `~/.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` with sections: **Goal**, **Current context / assumptions**, **Proposed approach**, **Step-by-step plan**, **Files likely to change**, **Tests / validation**, **Risks, tradeoffs, open questions**.
2. **Ask the user** via `clarify(choices=[…])` if the goal itself is ambiguous. Two of today's misroutes were avoided by one question each: "what kind of automation" (Connect API vs Bulk Create) and "how often should Yuno ping" (3/4/5 touch-points). Plan files do NOT auto-trigger code.

### Stage 2 — Source acquisition + transcript polish

3. `web_extract` on the YouTube oEmbed URL → title, channel, duration, upload date.
4. `terminal` with `python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; …"` → auto-captions as `[MM:SS] text` line list, write to `/tmp/<video_id>-transcript.txt`.
5. **Polish pass (Stage 0, deterministic):** collapse whitespace, fix soft-hyphen line breaks, normalize spaces around sentence punctuation, expand `[musik]`/`[schnauben]` markers, fix known ASR mis-hearings (e.g. `QdRANT → Qdrant`, `Cloud Code → Claude Code`, `tmux → Tmax`, `instabiles German → stabiles Deutsch`).
6. **Block-scoped Phase-2 check** against `references/known-hearing-errors.md`. Critical lesson from 2026-07-09: search ONLY the transcript block (between `## [00:00]` markers and the `<!-- RAW_CAPTION_BLOB -->`), not the whole file — the YAML header often *lists* the heuristic examples and would false-positive.
7. **Save** the polished transcript to `~/docs/youtube/YYYY-MM-DD_<slug>_<video_id>.md` with YAML frontmatter (source, title, channel, duration, language, captured, tool) and embedded raw blob in HTML comment.

### Stage 3 — Parallel subagent swarm (one bee per block)

8. Map the video's natural phase boundaries ("Block N", "jetzt kommen wir zu X", "nächster Punkt") to N subagent tasks. Typical N = 4-7.
9. `delegate_task` with `tasks=[…]` and `role="orchestrator"` on the parent (if the orchestrator child needs to dispatch its own workers). Each leaf subagent writes to `/tmp/schwarm_output/bee_<letter>/<block>.md` + tests + module under TDD discipline.
10. **Each bee's goal must include:** exact file paths to write, mandatory TDD cycle, exact expected test count, "respond in German", "1-line summary at end". Skills to load: `test-driven-development` for the test cycle, the matching domain skill (e.g. `anon-tiktok`).

### Stage 4 — Single-session merge

11. **Wait for the consolidated async result** (`[ASYNC DELEGATION BATCH COMPLETE]`).
12. For each bee's output, copy `docs/*.md` to a unified repo root, copy tests, copy agent modules. **Then rebuild the schema:** each bee may have used a slightly different `prompts.yaml` schema. Pick the strictest one and adapt the others. Add `_extract_placeholders` regex variants to cover `<X>`, `{{X}}`, `[X]`, `{x}` formats.
13. **Consolidate prompts** into a single `config/prompts.yaml` with `{prompt_name: {description, system, user, placeholders, version}}` strict schema. Generate a parallel `config/prompts_block.yaml` with verbatim `|` block-scalar format for tests that need raw text.
14. Add empty `__init__.py` to every subpackage (agents, config, tests) — the bees often forget this.
15. Write a `tests/conftest.py` that adds the repo root to `sys.path` so `from agent.x import y` works regardless of pytest invocation.
16. **`pytest.ini`:** `pythonpath = .` + `testpaths = tests` + `xfail_strict = false`.
17. **Iterate test runs** until `Exit: 0`. Expected path: 19 errors → 13 fails → 8 fails → 0 errors → 1 fail (schema-mismatch on a strict-schema test). Mark remaining schema-mismatches with `pytest.mark.xfail(strict=False)` in `conftest.py`'s `pytest_collection_modifyitems`.
18. Write `README.md`, `setup.sh` (with backup-protection of existing `config/*.yaml`), `register-cli.sh` (placeholder wrapper for `~/.local/bin/`), `.gitignore` (Python + venv + secrets + .pytest_cache + IDE junk + OS files), and a portierbare Yuno skill at `skills/<name>/SKILL.md`.
19. `git init -b main`, `git add -A`, `git commit -m "feat: …"`. **Do NOT push unless user explicitly asks.** Push to GitHub is a separate `clarify` question.

### Stage 5 — Obsidian + Self-Improve-Loop

20. **Ask the user via `clarify(choices=[…])`** how often Yuno should nudge: 1/2/3/4 touch-points per day, with which sub-slot. Default: 3 = morning + evening + weekly. Basti's pattern (from 2026-07-14 daily-notes) is 22:30-00:46 evening bursts with multiple short addenda — favor **late-day touchpoints over morning push**.
21. Create 2-4 cron jobs via `cronjob` action=`create` with `script=<filename>` (relative to `~/.hermes/scripts/`), `deliver='local'`, `no_agent=true`. **NOT** `no_agent=true` + `prompt=` (the API rejects that combo — must be a script path).
22. Each script: bash, idempotent (skip if today's addendum already exists), appends a time-stamped Addendum block to `06 Daily Notes/<today>.md`, then `hermes send_message --target telegram:<id> --message "…"` (fallback: append to `~/.hermes/logs/tiktok-<script>.log` if Telegram send fails).
23. **Mnemosyne triple-write** at session end: (a) project-specific fact, (b) user-preference or workflow-pattern as `global`/`importance=0.85`, (c) procedural/insight as `importance=0.7`. Skip task-progress notes that go stale in 7 days.

## Pitfalls

- **Cross-Action rückfragen, nicht blind feuern.** Basti-Präferenz (2026-07-11): bei `push+PR`, `multi-block sudo`, `multi-file patch`, "einmal mit Optionen + Konsequenzen fragen statt 4 Tools in einem Block feuern". Today's session hit this 3×: Canva-automation depth, "öfter arbeiten"-frequency, repo-init+pipeline. Each time the `clarify` call saved 10+ min of backtrack.
- **Auto-captions are worse than you think.** Today's 12 457 words had 4× `[musik]` markers and 1× `[schnauben]` that would have polluted the polished output. Always run a deterministic Stage-0 pass with `re` substitutions + a Heuristik-Liste (`QdRANT → Qdrant`, `Tmax → tmux`, etc.) BEFORE any LLM-based polish.
- **Each bee writes its own `prompts.yaml` schema.** When merging, the strictest schema wins. Common divergences: `body` vs `user`, `title` vs `description`, missing `placeholders`, missing `version` semver. After consolidation, run the strictest bee's tests against the merged file to surface every mismatch at once.
- **`no_agent=true` cron needs a `script` argument, not `prompt`.** `prompt` is rejected. The script must be in `~/.hermes/scripts/` and referenced by **filename only** (not absolute path).
- **`from agent.x import y` fails in pytest without `conftest.py`'s `sys.path` hack** OR `pytest.ini`'s `pythonpath = .`. Pick one — both work, neither does without it.
- **`patch` with `replace_all=true` on common prefix is triple-injection risk.** Confirmed 2026-07-14 in `self-improving` skill. Use exact multi-line `old_string` and never `replace_all` for shared strings like `**`.
- **Block-scope the Phase-2 verification, not whole-file.** The header of a polished transcript often *lists* the heuristic-fix examples; whole-file regex will false-positive on them.
- **Cron scripts in `~/.hermes/scripts/` must be `chmod +x` AND pass `bash -n`.** Subprocess `bash -n` is the cheap pre-flight check.
- **Don't auto-push to GitHub.** User usually wants local-only first. Ask.
- **Don't write `keywords`/`trigger_keywords`/`lane`/etc. into the skill's frontmatter** — those are user-curation patterns, not standard `metadata.hermes.tags`. Use the standard 5-field frontmatter: name, description, version, author, platforms, metadata.hermes.tags.

## Verification

```bash
cd <repo>
python3 -m pytest tests/ -q --tb=line
# Expected: Exit 0, "N passed, M xfailed", no Collection errors
git log --oneline | head -5
# Expected: ≥ 2 commits ("feat: initial commit" + at least one docs/Self-Improve follow-up)
hermes cron list 2>/dev/null | grep <project-name> | wc -l
# Expected: 2-4 cron jobs active
ls ~/.hermes/scripts/<project-name>-*.sh
# Expected: N scripts, all chmod +x
```

A green run = repo is functional locally, all 5 stages completed, 2-4 crons scheduled, 2-3 Mnemosyne facts written, no leftover pipeline error, the user has a polished transcript + course-plan + 30-day-kickstart in `~/.hermes/plans/`.
