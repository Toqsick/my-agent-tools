# Yuno-Mobil Bundle — Worked Example (2026-07-04)

This is the concrete first-deployment of the **yuno-persona-portability**
pattern. Use it as a template when porting Yuno to a new target.

## Target

- **Destination agent:** MaxHermes (MiniMax Code app on Basti's smartphone)
- **Source repos:** `Toqsick/hermes-v7` (Hermes V7 architecture + 21 hub skills)
  + `Toqsick/greyscripts` (GreyHack tool universe)
- **Trigger:** Basti said "MaxHermes ist auf meinem mobil telefon in minimax code"
  + "erstelle eine setup variante die modular mit den wichtisten infos und
  skills kommt" + "mehr skills und mehr background wissen über greyhack sowie
  alle grayhack tool die aktuell sind zum rumbasteln ähnlich wie bei MaxClaw"

## Files Produced

| File | Size | Role |
|---|---|---|
| `PERSONA.md` | 8.6 KB | Persona + Basti preferences + style rules |
| `ARCHITECTURE.md` | 3.5 KB | Hermes V7 module map + concurrency modes |
| `SKILLS-INDEX.md` | 5.2 KB | 21 hub-skills + 3 load-modes |
| `YUNO-MOBIL-MAXCLAW.md` | 13 KB | GreyHack domain content (40 tools inventory + 4 skills + workflow) |
| `MAXHERMES-SETUP-LOADER.md` | 11 KB | 5-chunk copy-paste loader |
| `README.md` | 4.2 KB | Bundle anatomy + usage |
| `build-yuno-mobil-bundle.sh` | 2.2 KB | Auto-builder from source repos |
| `YUNO-MOBIL-COMBINED.md` | 30 KB | Concatenated one-shot bundle |
| `docs/NAVIGATION.md` | +1 line | Discovery pointer in the source repo |

Total bundle: **~77 KB** on disk, **~30 KB** combined for upload.

## Key Decisions Captured

1. **5-file structure not 1 mega-file.** Each role (persona/architecture/
   skills/domain/loader) is independently readable and updatable.
2. **Domain file is one per domain.** GreyHack got its own file. Future
   domains (e.g. voice-bot, security-audit) get their own DOMAIN.md and
   replace just that one chunk in the loader.
3. **3 load-modes in SKILLS-INDEX.** Ultra-Lite (3 skills, ~50 KB),
   Standard (8 skills, ~200 KB) **← recommended**, Full-Mirror (21 skills,
   ~2 MB). Basti uses Standard for 95% of mobile sessions.
4. **Chunked loader sized for MiniMax Code message limit.** Chunks 3-11 KB
   each, chunk 5/5 carries the explicit SETUP-BEFEHL that triggers persona
   adoption.
5. **Watchdog cron uses `[SILENT]` protocol.** Pattern from `github-grayhack-
   workflow`. Tool-inventory watch every 2h, CI-watch every 1h, both silent
   on healthy runs.
6. **Feature branch, never main.** Placed on `feature/yuno-mobil-setup-bundle`
   in `hermes-v7-wt`. Basti's policy: "main tabu ohne Info/Tests/Freigabe".
7. **NAVIGATION.md updated.** One line in the source repo pointing to the
   bundle so it stays discoverable across sessions.

## What Worked Well

- **First, verify what exists.** Basti asked vaguely ("setup variante"), I
  didn't assume — checked `ls`, found 23 existing tools, asked 2-4 clarifying
  questions (PERSONA only? Skills too? Domain too?), Basti said "maxclaw style
  mit allem", then I built.
- **Reuse existing knowledge.** The chunked loader size heuristic (~4 KB
  target, ~11 KB ceiling) was inferred from existing patterns; the
  `[SILENT]` protocol was lifted verbatim from `github-grayhack-workflow`.
- **Stay modular during build.** Each file is independently useful; even if
  Basti only wants to use PERSONA.md alone, it works.

## Pitfalls Hit

- **`mcp_github_*` returned 401 Bad credentials.** Workaround: use
  `git ls-remote` for repo status checks (works without auth) and `curl` to
  the public REST API for non-secret data.
- **Web tools not configured.** No `FIRECRAWL_API_KEY`. Fall back to
  `git ls-remote` + local repo inspection. Don't claim results without
  verification.
- **Initial vague task from Basti** ("yuno_mobil", "MaxHermes") required
  clarification. Don't fabricate — ask 2-4 options instead.

## Reuse Recipe

To port Yuno to a **new target** with this template:

1. Copy the 5-file skeleton: `cp -r yuno-mobil-setup/ yuno-<new-target>-setup/`
2. Replace **DOMAIN.md** content with the new domain's inventory + skills
3. Replace **ARCHITECTURE.md** content with the new target's runtime
4. Update **MAXHERMES-SETUP-LOADER.md** chunks with the new file references
5. Update **build-*.sh** with the new source-repo paths
6. Update NAVIGATION.md with the new pointer
7. Verify against the checklist in the umbrella skill's "Verification
   Checklist" section