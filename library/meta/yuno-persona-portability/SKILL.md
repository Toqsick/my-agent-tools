---
name: yuno-persona-portability
title: Yuno Persona Portability — Cross-Agent Bundle Pattern
description: >-
  Use when user asks for packaging Yuno persona for another agent, porting Basti preferences across runtimes, building a chunked cross-agent context bundle, or delivering persona files to another environment. NOT for backing up an entire Obsidian vault or transferring model weights. Defines a compact five-file bundle, loader, transport paths, style rules, watchdog patterns, and portability checks.
version: 1.1.0
author: Yuno (for Basti)
license: MIT
platforms:
- linux
- macos
- windows
- android
- ios
metadata:
  hermes:
    tags:
    - yuno
    - persona
    - portability
    - cross-agent
    - bundle
    - maxclaw
    - maxhermes
    - mobile
    - delivery
    - drive
    category: meta
    requires_toolsets:
    - terminal
    - files
    - memory
    lane: worker-flash
reasoning_effort: medium
trigger_keywords: ['persona', 'another', 'agent', 'bundle', 'user']
keywords: ['persona', 'another', 'agent', 'bundle', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Yuno Persona Portability — Cross-Agent Bundle Pattern

Load this skill whenever Basti wants to deploy Yuno (or any persona-grounded
agent setup) to a **different LLM agent**, a **mobile device**, or a **fresh
Hermes install** — anywhere the persona + domain context needs to travel with
the agent.

## Why This Skill Exists

Yuno runs on Basti's desktop Hermes V7. But Basti also uses:
- **MaxHermes** on his phone (MiniMax Code app, same model family)
- **MaxClaw** (his OpenClaw / Nous Research instance — see memory note)
- Friends' setups when collaborating on shared projects
- Fresh VMs that need a quick Yuno-bootstrap

Without a portable bundle, every new instance starts cold. With this skill's
bundle pattern, the new agent has Yuno's voice, Basti's preferences, the
relevant skill index, and the domain context — in one shot.

## The 5-File Bundle Structure

Every persona-portability bundle follows the same shape. Adapt the *content*
but keep the *roles*:

| File | Role | Size target |
|------|------|-------------|
| **PERSONA.md** | Who is Yuno? Who is Basti? Style rules. Anti-patterns. Mini FALSCH/RICHTIG example. | ~8 KB |
| **ARCHITECTURE.md** | The runtime architecture the agent sits on (Hermes V7 modules, concurrency modes, healthcheck exit codes, what the agent actually needs to know). | ~3 KB |
| **SKILLS-INDEX.md** | Available skills with trigger-words + 3 load-mode strategy (Ultra-Lite / Standard / Full-Mirror). | ~5 KB |
| **DOMAIN.md** | Domain-specific content (e.g. GreyHack: 40 tools inventory, language quirks, mission workflow, watchdog cron). One file per domain. | ~12 KB |
| **MAXHERMES-SETUP-LOADER.md** | Chunked copy-paste loader — splits the bundle into ~4-7 KB chunks sized for token-limited mobile contexts, with explicit "send setup-befehl" at the end. | ~10 KB |

Optional: a `build-*.sh` script that rebuilds the combined bundle from source
repos with a single command.

Optional: a `YUNO-MOBIL-COMBINED.md` that concatenates PERSONA + ARCHITECTURE +
SKILLS-INDEX + DOMAIN into one file for one-shot upload where token limits
permit.

## Bundle Size Targets

- **Combined bundle** (4 files concatenated): **~30 KB** — fits a QR code as one
  image, fits most Telegram file uploads, fits one-shot context on most agents.
- **Individual file**: **3-15 KB each** — readable in one screen scroll.
- **Chunked loader chunks**: **3-11 KB each** — fits a single mobile paste into
  MiniMax Code / similar apps without hitting message size limits.

## The Chunked Loader Pattern

When token-limits or message-size-limits prevent one-shot bundle upload (this
is the common case for mobile agent apps), split the bundle into 5 chunks with
explicit ordering:

```
Chunk 1/5 — PERSONA + ARCHITECTURE    (~11 KB)
Chunk 2/5 — SKILLS-INDEX                (~5 KB)
Chunk 3/5 — DOMAIN-CONTENT              (~7 KB)
Chunk 4/5 — DOMAIN-BACKGROUND           (~6 KB)
Chunk 5/5 — SETUP-BEFEHL + TRIGGERS     (~3 KB)
```

Each chunk should be self-contained (pasteable as-is) and end with a brief
acknowledgment prompt so the receiving agent confirms ingestion before the
next chunk arrives.

The final chunk's `SETUP-BEFEHL` is critical: it explicitly tells the agent
"Übernimm Persona, lade Trigger-Index, antworte in Yuno-Vibe, bestätige mit
'<expected confirmation>'". Without it, the agent often acknowledges chunks
but doesn't actually adopt the persona.

## MaxClaw Watchdog Cron Pattern

Once the bundle is loaded, keep it fresh with cron-driven watchdogs. Pattern
from MaxClaw / `github-grayhack-workflow`:

```bash
# Inventory watch — every 2 hours, only report on change
hermes cron create "every 2h" \
  "Check ~/greyhack-tools/src/tools/ and ~/hermes-v7-wt/skills/hub-imported/
   for new files since last check. If new .src or SKILL.md: send compact list
   to Telegram. If nothing changed: respond with EXACTLY '[SILENT]'." \
  --name <domain>-mobil-watchdog \
  --deliver telegram

# CI status watch — every 1 hour, alert on failure only
hermes cron create "every 1h" \
  "Run cd ~/greyhack-tools && bash scripts/ci-build.sh. If exit code != 0:
   send error snippet to Telegram. If success: respond EXACTLY '[SILENT]'." \
  --name <domain>-ci-watch \
  --deliver telegram
```

The `[SILENT]` protocol is the key: a successful no-op must produce exactly
that literal token, which the cron runner recognizes and suppresses. This
keeps Basti's phone quiet on healthy runs and pings only on real change.

## Style Rules That Travel with the Bundle

These rules must appear verbatim in PERSONA.md (extracted from
`yuno-user-preferences`):

- German always. Never archaic German ("Euer", "Hochachtungsvoll", "mein lieber" = VERBOTEN).
- Emojis sparingly. (T ^ T) for apologies.
- 2-4 concrete options for decisions — NEVER open questions.
- Concrete artifacts, not descriptions of artifacts.
- Honest testing over claiming success (build OK ≠ tested in-game).

## Repo Placement

Bundle files belong in the **consumer repo** under a setup-guide path:

```
<repo>/setup-guide/yuno-<target>/
├── README.md                       (anatomy + usage)
├── PERSONA.md
├── ARCHITECTURE.md
├── SKILLS-INDEX.md
├── DOMAIN.md
├── MAXHERMES-SETUP-LOADER.md
├── build-bundle.sh                 (rebuild from source repos)
└── COMBINED.md                     (cat'd one-shot version)
```

Always on a **feature branch**, never on `main` directly (Basti's policy:
"main tabu ohne Info/Tests/Freigabe"). Update `docs/NAVIGATION.md` with a
one-line pointer to the new bundle so it stays discoverable.

## Delivery Paths — Bundle-to-Target Transportation

Once the bundle is built, **how** it reaches the target agent matters as much
as the bundle itself. The available paths, ranked by friction:

| Path | Friction | Tool required | When to use |
|---|---|---|---|
| **Local direct copy** | 0 | `cp` / `scp` | Target is same machine or LAN-reachable VM |
| **Telegram self-DM** | 0 | Hermes gateway | Same Basti, different device (phone ↔ desktop) |
| **Telegram to phone → drive** | 0 | Drive app on phone | When Basti wants file in Drive as canonical storage |
| **Google Drive upload** | OAuth setup (~10 min one-time) | `google-workspace` skill + OAuth flow | Frequent Drive uploads; worth the one-time cost |
| **QR code (≤30 KB)** | 0 | `qrencode` CLI | Bundle ≤ 30 KB, single-image transfer |
| **GitHub gist (private)** | 0 | `gh gist create --private` | Bundle versioning + easy URL paste |

### Pitfall: Don't promise Drive upload when `google-workspace` isn't set up

**Symptom:** User says "schieb das auf mein Google Drive". Agent offers
4 options including "direct upload", only to discover during execution that
the `google-workspace` skill has no `google_token.json` /
`google_client_secret.json`.

**Tools that look like they work but DON'T for personal Google Drive:**
- `gsutil` — uploads to **Google Cloud Storage**, NOT personal Google Drive.
  Common confusion: user sees `gcloud` authenticated as their Google account
  and assumes `gsutil cp` will reach Drive. It won't. `gsutil` has no concept
  of the user's Drive files.
- `gcloud auth list` showing their account — that's gcloud credentials for
  GCP APIs only. Cannot be used directly as Drive OAuth tokens.
- `rclone` without a configured remote — needs `rclone config` first.

**The honest fallback ladder** (use this when Drive-API upload isn't possible):
1. Build a ZIP on local disk (`zip -r bundle.zip dir/`)
2. Tell the user the exact local path + size + MD5
3. Provide 3 options: (A) manual drag-drop in Drive web UI, (B) Telegram
   self-DM, (C) QR code if ≤ 30 KB
4. Let user choose — never silently fail

**Lesson embedded 2026-07-04:** First "Drive upload" attempt failed across
3 tools (gsutil, gcloud-creds, rclone-unconfigured). User said "hau alles
was MaxHermes braucht hier rein dann route ich darauf
google-drive://bastick123@gmail.com/0AGou6bsAJkh6Uk9PVA" expecting auto-upload.
Wasted 2 tool calls discovering the gap. Now: **before promising Drive
upload, run `$GSETUP --check`** (or `which gws && gws auth status`). If
`NOT_AUTHENTICATED`, lead with the manual fallback options.

See `references/delivery-fallback-recipes.md` for copy-paste recipes.

## Verification Checklist

Before declaring a bundle "ready to ship":

- [ ] All 5 files exist and load without syntax errors
- [ ] Combined bundle ≤ 30 KB
- [ ] Each chunked-loader chunk ≤ 11 KB (token-limit safe)
- [ ] Trigger-words in SKILLS-INDEX match real skill frontmatter
- [ ] PERSONA.md has FALSCH/RICHTIG example showing the expected voice
- [ ] MAXHERMES-SETUP-LOADER ends with explicit SETUP-BEFEHL
- [ ] `build-bundle.sh` runs cleanly and reports source-repo commit SHAs
- [ ] Watchdog cron jobs reference real paths that exist
- [ ] Branch is `feature/...`, not `main`
- [ ] Delivery path confirmed with user (which of the 6 paths above?)

## Reuse Beyond Yuno

The same pattern works for any persona you want to deploy to multiple agents:

- **Yuno → MaxHermes** (mobile)
- **Yuno → fresh Hermes VM** (re-bootstrap after crash)
- **Yuno → friend's setup** (collaborating on shared GreyHack mission)
- **A domain expert persona** (e.g. "Security Auditor Basti" for security-only setups)

The structure (PERSONA / ARCHITECTURE / SKILLS-INDEX / DOMAIN / LOADER) stays
constant; only the contents change.

## Anti-Patterns (do NOT do)

- ❌ One mega-file with everything mixed together → unreadable, untestable.
- ❌ Chunked loader without explicit SETUP-BEFEHL → agent acknowledges but doesn't adopt.
- ❌ Watchdog cron without `[SILENT]` protocol → spams Basti's phone.
- ❌ Bundle on `main` branch directly → violates Basti's policy.
- ❌ Bundle > 50 KB combined → too large for QR / Telegram / mobile paste.
- ❌ Forgetting to update `docs/NAVIGATION.md` → bundle becomes unfindable.
- ❌ Re-creating the pattern from scratch each time → this skill exists.
- ❌ **Promising "I'll upload to Drive" without checking `google-workspace`
  auth state first.** Lead with manual fallback if OAuth isn't set up.

## Worked Example

The first deployment of this pattern (yuno → MaxHermes on Basti's phone,
2026-07-04) is captured at `references/yuno-mobil-bundle-example-2026-07-04.md`.
Use it as a template: copy the 5-file skeleton, swap the DOMAIN.md and
ARCHITECTURE.md contents, update the chunked loader, regenerate the combined
bundle.

## See Also

- `yuno-user-preferences` — the persona source-of-truth (load to verify the bundle matches)
- `skill-creator` — when the bundle pattern itself needs documenting as a skill
- `github-grayhack-workflow` — the existing `[SILENT]` cron protocol template
- `orchestration/multi-agent-orchestration` — when bundle needs to be dispatched across multiple agents at once
- `references/delivery-fallback-recipes.md` — concrete recipes for the 5 most common delivery-failure modes