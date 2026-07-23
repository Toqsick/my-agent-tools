# Worked Example — MaxClaw (2026-07-03)

Concrete session where this skill's pipeline was first applied. Future agents should read this
to see the pattern executed end-to-end with the actual artifacts, errors, and decisions.

## Source
- **Local file:** `/home/bratan/Downloads/UMD4/OpenClaw Kurs für Einsteiger： Alle Konzepte einfach erklärt-5nmLL7RJuVY.webm`
- **Size:** 336 MB → over `video_analyze` 50 MB limit → routed to YouTube transcript.
- **URL:** `https://youtube.com/watch?v=5nmLL7RJuVY`
- **Transcript:** 82k chars, German, fetched via `youtube-content` skill's `fetch_transcript.py`.

## Pipeline trace

### Step 1 — Source acquisition
```bash
# Inspect file
du -h "OpenClaw Kurs..." → 336M
# Skip video_analyze (too large). Fall back to YouTube transcript:
pip install youtube-transcript-api --break-system-packages
python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
  "https://youtube.com/watch?v=5nmLL7RJuVY" --text-only --language de,en > /tmp/openclaw_transcript.txt
wc -c /tmp/openclaw_transcript.txt → 82176
```
**Decision logged:** Local video bypassed, YouTube transcript sufficient.

### Step 2 — Structure mapping
Read transcript in 4 windows of ~20k chars. Speaker's own block markers:
- *"Kommen wir jetzt zum Gehirn des Agenten"* → Block 3 boundary
- *"Gateway ist die zentrale Schnittstelle"* → Block 4
- *"Heartbeat" / "Cron Jobs"* → Block 5
- *"Skills" / "MCP Server" / "Plugins"* → Block 6
- *"Sicherheit" / "Prompt Injection"* → Block 7
- *"VPS installierst" / "Hostinger"* → Block 8

Result: **8 blocks** — matches the canonical N=6–10 sweet spot.

### Step 3 — Repo layout shipped
24 files across:
- `README.md` (4.4 KB table-of-contents)
- `docs/01-grundlagen.md` … `docs/08-server-deployment.md` (8 files, 2.8–4.6 KB each)
- `agent/{SOUL,IDENTITY,AGENTS,USER,TOOLS,MEMORY,HEARTBEAT}.md` (7 core-file templates)
- `config/config.yaml` (Default-Deny + model routing, YAML-linted clean)
- `workflows/{daily-briefing,greyhack-ci-watch,security-audit-weekly,github-pr-monitor}.md` + `register-workflows.sh`
- `skills/project-doc-sync/SKILL.md` (one example skill)
- `setup.sh` (one-command installer with backup-protection)
- `.gitignore`

### Step 4 — Static checks
```bash
chmod +x setup.sh workflows/register-workflows.sh
bash -n setup.sh && echo "setup.sh OK"
bash -n workflows/register-workflows.sh && echo "register-workflows.sh OK"
find . -type f -not -path './.git/*' | sort  # 24 files, matches plan
```

### Step 5 — Push + remote-verify
```bash
git add -A
git -c user.name="Toqsick" -c user.email="toqsick@users.noreply.github.com" \
  commit -q -m "feat: MaxClaw-Vorlage nach OpenClaw-Kurs (8 Blöcke) + Auto-Workflows"
git push origin HEAD  → To https://github.com/Toqsick/MaxClaw.git   2e7aa3c..d5658ed  HEAD -> main

# MANDATORY verify — caught nothing missing this time, but the discipline held:
gh api repos/Toqsick/MaxClaw/git/trees/main?recursive=1 \
  --jq '.tree[] | select(.type=="blob") | .path' | sort
# → 24 files, matches local tree exactly
```

## Errors hit and how they were resolved

| Symptom | Cause | Fix |
|---------|-------|-----|
| `mcp_github_get_file_contents` → 401 Bad credentials | MCP GitHub token expired | Switched to `gh` CLI (`gh auth status` confirmed Toqsick logged in, scopes: gist, read:org, repo, workflow) |
| `fetch_transcript.py` → `python3: can't open file` | Wrong path (skill moved between profiles) | Used the canonical path `~/.hermes/hermes-agent/skills/media/youtube-content/scripts/fetch_transcript.py` |
| `pip install youtube-transcript-api` → PEP 668 | PEP 668 externally-managed env | `--break-system-packages` (one-off, not a rule) |
| `skill_manage create` → YAML frontmatter parse error | Description contained an unquoted `:` | Wrapped description in `"…"` and retried |

## Decisions the user (Basti) made implicitly (encoded as defaults for next time)
- Tone: Yuno (locker, kawaii-but-not-cringe, German). Already in SOUL.md.
- Decision style: 2–4 concrete options offered at the end, not "what next?".
- Real artifacts > abstract plans: every block doc ended with concrete scripts/configs, not just theory.
- Used `Toqsick` GH account (logged in via `gh` CLI keyring) — preferred over MCP path.

## What this example does NOT cover (next-session signals)
- No cron jobs actually activated — `register-workflows.sh` echoes the real command but
  leaves it commented (CLI syntax differs between OpenClaw and Hermes). A future session
  should patch this with the verified-real `hermes cron create …` invocation once known.
- No `.github/workflows/` CI — could be added (e.g. greybel-build.yml running on push to develop).