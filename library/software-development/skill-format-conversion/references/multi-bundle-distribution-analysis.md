# Multi-Bundle Distribution Analysis — Hermes → MiniMax.io (2026-07-07)

**Session context:** 247 Hermes skills → 5 themed bundles for MiniMax.io M3 Agent Team.
**Method:** Free-assign all skills to domain bins → tally → discard domain-local bins → merge trivial bins → estimate overlap with platform built-ins → finalize bundle count.

## Step 1: Free-Assign Skills to Domain Bins

Source: `~/.hermes/skills/<category>/<subcategory>/<name>/` — 247 skills across 10+ categories.

### Category Distribution

```text
software-development/   — 31 skills  (coding, debugging, git, TDD, agents, orchestration)
creative/               — 28 skills  (design, anime, diagrams, audio, video, ASCII)
productivity/           — 17 skills  (office, project-mgmt, maps, daily-briefing)
research/               — 9 skills   (arxiv, notebooklm, llm-wiki, bioinformatics)
security/               — 7 skills   (audit, 1password, attestation, code-check)
devops/                 — 9 skills   (docker, linux-setup, hermes-admin)
gaming/                 — 8 skills   (greyhack, minecraft, cp77)
mlops/                  — 5 skills   (llama-cpp, vllm, axolotl, sam, audiocraft)
mcp/                    — 3 skills   (native-mcp, mcp-server-authoring)
social-media/           — 2 skills   (xurl)
orchestration/          — 7 skills   (multi-agent, subagent, kanban)
github/                 — 6 skills   (pr-workflow, code-review)
note-taking/            — 5 skills   (obsidian, system-documentation)
computer-use/           — 5 skills   (cua-driver, greyhack-automation)
... misc                — ~105 skills (meta, memory, pdf, creative-suite, etc.)
```

### User Preferences Applied

Aggressive filters based on Basti's known working style:
- ✅ **Include:** Tools that work in a cloud agent sandbox (HTTP, file I/O, code execution, MCP)
- ❌ **Exclude by category:** `gaming/`, `computer-use/`, `desktop-window-reconnaissance/`, `note-taking/` (obsidian=local-only)
- ❌ **Exclude by name pattern:** linux-*, nvidia-*, docker-*, obsidian-*, hermes-admin*, hermes-gateway*, apple-*, greyhack-*, mcp-server-*
- ❌ **Exclude specific skills:** `node-inspect-debugger`, `python-debugpy`, `touchdesigner-mcp`

## Step 2: Tally Each Bin

| Bin | Raw count | After category exclusion | After name-pattern exclusion | Final (Layer-3 adjusted) |
|---|---|---|---|---|
| **CODE** (sw-dev, github, agents, orchestration, mlops/hosting, meta) | 60+ | 60 | ~55 | **90** (expanded with +6 ML skills) |
| **DESIGN** (creative, architecture, motion, audio, media) | 35+ | 35 | 35 | **35** |
| **PRODUCTIVITY** (office, project-mgmt, email, messaging) | 22 | 22 | 22 | **22** |
| **SECURITY** (audit, 1password, code-check) | 9 | 9 | 9 | **9** |
| **RESEARCH** (research, arxiv, notebooklm, pdf) | 12 | 12 | 12 | **9** (3 built-in dedup) |

## Step 3: Discard Domain-Local Bins

These bins are pure workstation/native/gaming — worthless on MiniMax.io:

| Bin | Reason to discard |
|---|---|
| **GAMING** (8 skills) | Needs local Steam, GreyHack game, computer-use, Wine/Proton |
| **COMPUTER-USE** (5 skills) | MiniMax.io M3 is a cloud sandbox — no background desktop control |
| **NOTE-TAKING/OBSIDIAN** (5 skills) | Vault is local-only; MiniMax has no Obsidian connector |
| **DEVOPS** (9 skills) | Docker, linux-setup, nvidia, hermes-admin — all workstation-only |
| **MCP** (3 skills) | native-mcp (Hermes internal), mcp-server-authoring (needs local server) — MiniMax has its own MCP client |

## Step 4: Merge Trivial Bins

Some small bins are better merged into existing themed bundles:

| Small bin | Merge into | Reason |
|---|---|---|
| **SOCIAL-MEDIA/xurl** (2 skills) | Productivity (or skip) | Posting workflow, not core bundle |
| **META** (2-3 skills) | Code | Self-improving, skill-creator — meta is code-adjacent |
| **MEMORY** (2 skills) | Code | Hermes-memory, mnemosyne — infra-adjacent |
| **MLOPS/HOSTING** (5 skills) | Code (ML extension) | llama-cpp, vllm, axolotl — ML Engineer tasks |
| **PDF** (2 skills) | Research | PDF extraction is research-adjacent |

## Step 5: Estimate Overlap with Platform Built-ins (Layer 1)

Check against MiniMax.io built-in skills for each bundle candidate:

| Bundle | Built-in overlap (estimated) | Unique value (Layer 3) |
|---|---|---|
| **Code** | Medium — `mini-coder-max`, `senior-software-engineer`, `app-builder` cover full-stack but not debug/testing/git | High — systematic-debugging, TDD, critic-gate, pr-workflow are Hermes-unique |
| **Design** | High — `ui-ux-pro-max`, `landing-page-builder`, `image-craft`, `icon-maker`, `minimax-pdf/docx/xlsx`, `pptx-generator` cover standard design needs | Medium — anime-design, ascii-art, excalidraw, architecture-diagram are unique; ui-factory orchestrator > individual tools |
| **Productivity** | Very high — `prd-assistant`, `minimax-docx/xlsx/pdf`, `knowledge-digest` cover docs and project needs | Low — mostly wrapper skills around APIs (notion, linear, airtable) that MiniMax can call directly |
| **Security** | None — MiniMax.io has no security-specific built-in skills | High — unique tooling for 3-layer audit, code-security check, attestation patterns |
| **Research** | Medium — `deep-research-agent`, `knowledge-digest`, `industry-research-report-writer` cover core research | Medium — notebooklm-bridge, arxiv, llm-wiki are additive; research-paper-writing overlaps with built-in |

## Step 6: Finalize Bundle Count

After analysis, 5 bundles approved by user:

```text
1. CODE    — 90 skills, 1.5 MB   (P0 — already built, expanded with +6 ML)
2. DESIGN  — 35 skills, 948 KB   (P0 — already built in previous step)
3. PRODUCTIVITY — 22 skills, 195 KB (P1 — user reviewed, approved despite low-unique overlap)
4. SECURITY — 9 skills, 100 KB   (P1 — user approved, read-only default)
5. RESEARCH — 9 skills, 142 KB   (P1 — user approved, notebooklm-pipeline unique value)
```

**Discarded during analysis (user-agreed):**
- macOS/Apple skill bundle (user: "nö macOS keinen")
- MCP/Server bundle (all need local Hermes runtime)
- Gaming bundle (pure workstation)
- Social-Media bundle (only 1 real skill)

## Per-Bundle Build Script Pattern

Each bundle gets its own `build.sh` sharing the same `extract_meta.py` but with a different `INCLUDE_NAMES` array:

```bash
#!/usr/bin/env bash
set -euo pipefail

# === DOMAIN CONFIGURATION (Change per bundle) ===
BUNDLE_NAME="code"               # design, productivity, security, research
INCLUDE_NAMES=(
    claude-coder systematic-debugging critic-gate
    # ... 90 code skills
)

# === SHARED EXCLUSIONS (All bundles) ===
EXCLUDE_CATEGORIES=("gaming" "computer-use" "desktop-window-reconnaissance" "note-taking")
EXCLUDE_WORDS=("linux" "nvidia" "docker" "obsidian" "hermes-admin"
               "hermes-gateway" "apple" "mcp-server" "greyhack")
EXCLUDE_SKILLS=("node-inspect-debugger" "python-debugpy" "touchdesigner-mcp"
                "yuno-cleaner")

# === DOMAIN-SPECIFIC EXCLUSIONS (Inverted: include-only approach) ===
# For security bundle: only include names matching security patterns
if [ "$BUNDLE_NAME" = "security" ]; then
    # Don't use INCLUDE_NAMES — use a dynamic filter
    for skill_dir in $(find "$SRC" -name "SKILL.md" -exec dirname {} \;); do
        name=$(basename "$skill_dir")
        [[ "$name" == *"security"* || "$name" == *"audit"* ||
          "$name" == *"1password"* || "$name" == *"attestation"* ||
          "$name" == *"code-check"* || "$name" == *"hygiene"* ||
          "$name" == *"perf-tun"* ]] || continue
    done
fi
```

## Companion Artifacts Per Bundle

| Artifact | Code | Design | Productivity | Security | Research |
|---|---|---|---|---|---|
| **CHEATSHEET.md** | 10 sections (debug, test, build, ML, etc.) | 8 sections + FAL/TTS limits | 7 sections (office, project, comms) | 7 sections, read-only default | 7 sections, notebooklm pipeline |
| **README.md** | Top-5 skills per category | 3 built-in refs | Google-auth setup guide | Read-only workflow | Deep-research-agent first |
| **MANIFEST.json** | Skill count + sizes | Same | Same | Same | Same |
| **build.sh** | Idempotent | Idempotent | Idempotent | Idempotent | Idempotent |

## Known Exclusion Pattern: Security Bundle Unique

The Security bundle is the only one where the user's read-only workflow preference applies — the CHEATSHEET MUST emphasize that:
> "Standard: Read-Only. Erst System-State erfassen, Report schreiben, Fixes nur nach expliziter Freigabe."

This is documented in the user's profile but needs explicit reminder in the CHEATSHEET because the bundle user may not know Basti's convention.

## Re-run Instructions

```bash
cd ~/10-Projekte/10-active/yuno-minimax-<bundle>-bundle
bash build.sh
zip -r yuno-minimax-<bundle>-bundle-$(date +%F).zip .
```

All build scripts are idempotent — they overwrite existing hub-skills/ without prompting.

---

**Session:** 2026-07-07
**Source corpus:** 247 Hermes skills → 5 bundles (165 skills in bundles, 82 excluded as domain-local)
**Target platform:** MiniMax.io M3 Agent Team (agent.minimax.io)
