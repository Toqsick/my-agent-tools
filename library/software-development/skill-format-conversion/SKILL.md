---
name: skill-format-conversion
description: "Use when user asks to convert, migrate, import, or export skill libraries between Hermes, Claude Code, MiniMax Hub, Codex CLI, OpenCode, or another agent format. NOT for application-data migration or editing only one skill body. Discovers source format, maps frontmatter, prevents namespace collisions, preserves originals, filters platforms, and packages the result safely."
version: 1.0.0
author: Hermes Agent (Hub-Hermes conversion 2026-07-03)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - skills
    - authoring
    - conversion
    - migration
    - cross-system
    - yaml
    - format-discovery
    related_skills:
    - hermes-agent-skill-authoring
    - bash-script-audit
    - github-workflow
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['skill', 'format', 'skill-format-conversion', 'convert', 'migrate']
keywords: ['skill', 'format', 'user', 'asks', 'convert']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Skill Format Conversion — Hermes ↔ Other Agents

## Overview

Different agent ecosystems (Hermes, Claude Code, MiniMax Hub, Codex CLI, OpenCode) all use variants of the SKILL.md + assets layout with slightly different frontmatter, naming, and storage paths. Converting between them is a recurring class of work — a future session hits this whenever the user says 'make Yuno's skill work in Claude Code' or 'bring Hub's skills into Hermes'.

This skill covers the **method** (the specific converters are templates below): discover source format, write a minimal converter, use flat-id namespaces to avoid destination collision, preserve provenance with scripts-originals of the originals, and reject secrets leaking into source.

## When to Use

- 'Convert these skills to Hermes' / 'make Hub skills work for Claude'
- 'Import the X-pack from skills.sh'
- 'Mirror skill X as Y but tweaked for our use-case'
- Bulk-conversion: 'convert all of them at once'
- Trigger phrases: convert skills, migrate skills, import skills, export skills, skill format, hub skills, claude skills, codex skills, 'make these work in X'

## When NOT to Use

- One-skill install: that's skill-install-workflow or hermes-agent-skill-authoring
- Authoring from scratch: hermes-agent-skill-authoring
- Push to a git repo unchanged: github-workflow

## Source-Format Discovery (Step 1, always)

Before writing the converter, inventory the source. From observation:

| System | Where | Format |
|--------|-------|--------|
| Hermes | `~/.hermes/skills/<cat>/<name>/SKILL.md` OR in-repo `skills/<cat>/<name>/SKILL.md` | YAML frontmatter + body + optional references, templates, scripts |
| MiniMax Hub | `~/.hub-global/skills/<name>/SKILL.md` + `meta.yaml` + `scripts/` + `references/` + `html/` | YAML frontmatter with `trigger-words`, `description:` block-scalar, sidecar `meta.yaml` (display-name, version, tags) |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | Markdown frontmatter (`name`, `description`), `scripts/` allowed |
| Codex CLI | `~/.codex/skills/<name>/SKILL.md` | Same SKILL.md format as Claude Code (Agnostic Agents Standard) |
| skills.sh zip | `skills/<name>/SKILL.md` + optional `DESCRIPTION.md` | SKILL.md + assets |

Investigation commands:

```
find ~/.hermes/skills -name SKILL.md | head -10   # Hermes
ls ~/.hub-global/skills/<name>/                    # MiniMax Hub
ls ~/.claude/skills/ ~/.codex/skills/              # CLI installables
find <pack>/ -name "SKILL.md"                      # Generic pack
```

## Pitfall #1 — Strip Secrets Before Touching Source

If source skills reference `~/.hermes/auth.json`, `os.environ['API_KEY']`, hardcoded tokens, or bearer strings in docs, strip them first. Always run this pre-flight scan:

```
grep -rEn "(api[_-]?key|secret|password|bearer|token)[^[:space:]]{0,5}[:=]['\"]?[A-Za-z0-9_-]{16,}" <skill-dir>/ 2>&1 | head -20
```

Confirm any hits with user before pushing. Don't assume — they might intentionally document secrets they want carried over.

## Pitfall #2 — Multi-line YAML `description:` block-scalar

Many systems (MiniMax Hub especially) use block scalars:

```
---
name: audiobook
description: |
  Audiobook creation assistant. Converts book text into multi-character narrated audio,
  supporting audiobook production, multi-character voiceover, novel narration, TTS voiceover.
  Trigger phrases: audiobook, read aloud, TTS book.
---
```

Naive parsers (line.split(":")) return the pipe character as the value. Always write a block-scalar-aware parser:

```python
def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    header = text[4:end]
    body = text[end + 5:].lstrip()
    fm, i = {}, 0
    lines = header.split("\n")
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            # Block scalar indicator: pipe = literal, gt = folded
            if value in ("|", ">"):
                block, i = [], i + 1
                while i < len(lines):
                    inner = lines[i]
                    if inner.startswith("  ") or inner.startswith("\t"):
                        block.append(inner[2:] if inner.startswith("  ") else inner[1:])
                        i += 1
                    elif not inner.strip():
                        block.append("")
                        i += 1
                    else:
                        break
                fm[key] = "\n".join(block).strip()
                continue
            fm[key] = value
        i += 1
    return fm, body
```

## Pitfall #3 — Flat-id Namespace, NOT Category Mapping

Catastrophic mistake: a first version of `hub-to-hermes` overwrote existing Hermes skills because both shared category paths (e.g. `creative/audio/`). After the run, all Hub audio skills landed in the same dir and only one survived.

Fix: flatten destination namespace under one umbrella. Don't try to merge Hub categories into Hermes categories — they don't align.

```python
# Bad: src.name = "audiobook" -> dst "creative/audio/audiobook"
#   (collides with existing creative/audio/<skill>)
#
# Good: flat hub-id under one umbrella
DEST_ROOT = HERMES / "hub-imported/<hub_skill_name>"  # no category intermixing
```

Use a single umbrella dir name (e.g. `hub-imported/`) so provenance is at-a-glance. Put `scripts-originals/` inside each skill for traceability of the unmodified source.

## Pitfall #4 — Preserve Originals via `scripts-originals/`

After conversion, save the unmodified source as `scripts-originals/SKILL.md.source` and `scripts-originals/meta.yaml.source` (using the source-format suffix). Three benefits:

1. Traceability: user diffs `SKILL.md` vs `scripts-originals/SKILL.md.hub`
2. Re-conversion: stable origin if source format updates
3. Audit: tool audits work without needing the raw source tree

## Pitfall #5 — Don't `gh repo create` on Populated Repos

User's first instinct: 'create new repo, push all skills'. Often wrong:

1. `gh repo create <name>` silently fails if the repo exists — `gh` returns 'Name already exists' only sometimes. Check with `gh repo view <name> --json name` before creating.
2. Clone+add, don't create. `gh repo clone <name> ~/worktree` then `git add skills/<ns>/`
3. Never `git push -u origin main` blindly on a populated repo — merge or PR instead
4. If repo has existing skills in `.hermes/.agents/skills/<name>/`, don't push to that path — use `skills/hub-imported/<hub-id>/` as the namespace

## Pitfall #6 — Hub-internal Absolute Paths Leak Through

Hub skill scripts often reference `/app/...` or `~/.hub-global/skills/<name>/...` literally. After conversion, replace with relative or generic paths:

```bash
# Bad: python3 ~/.hub-global/skills/audiobook/scripts/build_plan.py
# Good: cd "$(dirname "$0")/.." && python3 scripts/build_plan.py
# OR: use an env-var like $HUB_SKILLS_HOME
```

Or note in converted SKILL.md: 'this skill assumes MiniMax Hub is running locally'. A reader later should know context-requirements.

## Pitfall #7 — ZIP Packaging as Delivery Alternative

Not all conversion results need to go to git. For one-shot imports (into MiniMax.io, ChatGPT Custom GPTs, etc.), ZIP is lighter:

```bash
cd /tmp/build-output
zip -r yuno-skills-bundle-$(date +%F).zip . -x "*.DS_Store"
```

Companion artifacts (CHEATSHEET, README, MANIFEST) go **inside** the ZIP so the recipient has context:

| Inside ZIP | Purpose |
|---|---|
| `hub-skills/<name>/SKILL.md` | The actual skills |
| `CHEATSHEET.md` | Slash-command reference, user reads first |
| `README.md` | Upload instructions per target platform |
| `MANIFEST.json` | Machine-readable inventory for integrity check |
| `build.sh` | Reproducibility — rebuild command |
| `extract_meta.py` | Standalone parser for meta.yaml generation |

Never put ZIP in /tmp — move it to `~/10-Projekte/10-active/<project-name>/` so it persists across reboots.

## Pitfall #8 — Platform-Exclusion Filtering

Different target systems have different capabilities. A skill that works on Hermes (has access to cua-driver, X11/Wayland, NVIDIA, Hermes gateway, Obsidian vault) won't work on MiniMax.io, Claude Code, or ChatGPT.

**Before converting, filter skills by what the target can actually do:**

| Platform | Exclude |
|----------|---------|
| **MiniMax.io** (M3 Agent Team) | computer-use, greyhack-*, linux-*, nvidia-*, docker-*, hermes-admin, hermes-gateway, obsidian-*, apple/macOS-*, mcp-server-* |
| **Claude Code CLI** | computer-use (needs GUI), systemd/linux-service-*, greyhack-* |
| **Codex CLI** | Same as Claude Code + nvidia-*, docker-* |
| **OpenCode** | Same as Codex + greyhack-*, gaming-* |
| **ChatGPT GPTs** | Only skills with pure text/code output — no system access, no GUI |

Implement this as an array-based filter in the build script:

```bash
# Aggressive EXCLUDE — filter by platform cap
EXCLUDE_CATEGORIES=("gaming" "computer-use" "desktop-window-reconnaissance")
EXCLUDE_WORDS=("linux" "nvidia" "docker" "obsidian" "hermes-admin"
               "hermes-gateway" "apple" "mcp-server" "greyhack")
EXCLUDE_SKILLS=("node-inspect-debugger" "python-debugpy")
```

Then in the loop:

```bash
for exc in "${EXCLUDE_CATEGORIES[@]}"; do
    [[ "$cat" == "$exc" ]] && continue 2
done
for word in "${EXCLUDE_WORDS[@]}"; do
    [[ "$name" == *"$word"* ]] && continue 2
done
```

Double-check intersection with the user after they see what's excluded. They might want you to include something you filtered out.

## Pitfall #9 — Bash Heredoc with Inline Python Truncation

Inline Python via `python3 - << 'PYEOF'` inside a bash script causes **silent truncation** when the Python code contains multi-line f-strings with nested brace interpolation (`{...}`). The shell heredoc marker is consumed and f-string curly braces confuse bash in subtle ways depending on quoting.

**Symptom:** `python3 -` exits 0, output file is written partially or with missing lines, no error message.

**Fix:** Always extract the Python helper as a standalone `.py` file and call it from bash with positional args. The file is self-documenting and debuggable.

```bash
# BAD — inline heredoc (truncates silently on multi-line f-strings):
python3 - "$src_file" "$name" "$cat" "$src_dir" "$dest_dir" << 'PYEOF'
# ... potentially silently broken ...
PYEOF

# GOOD — standalone script:
python3 ./extract_meta.py "$src_file" "$name" "$cat" "$src_dir" "$dest_dir"
```

## Pitfall #10 — Field-Mapping Table

Capture the source→destination field mapping in the converter's docstring. From observation:

| Hermes | Hub | Claude Code | Codex |
|--------|-----|-------------|-------|
| `description` | `description` block-scalar | `description` | `description` |
| `triggers: []` | `trigger-words: []` | None (use description) | None |
| `version: 1.0.0` | `meta.yaml: version` | None | None |
| `metadata.hermes.tags` | `meta.yaml: tag-en, tag-cn` | None | None |
| `name` | `SKILL.md: name` + `meta.yaml` | `frontmatter: name` | `frontmatter: name` |
| Triggers via desc | `trigger-words` | Triggers via desc | Triggers via desc |
| License | None (Hub proprietary) | `license:` optional | `license:` optional |
| Author | `meta.yaml: author-en, author-cn` | None | None |

Always capture this table in your converter's docstring so future agents know the mapping assumptions.

## Pitfall #11 — 3-Layer Strategy: Don't Convert What Already Exists

**THIS IS THE #1 MOST COMMON MISTAKE** in skill conversion. The naive approach: "convert all Hermes skills to target format." That's wrong. Most target platforms already have built-in capabilities that overlap with your source skills.

**The 3-Layer Strategy (apply BEFORE converting):**

```
Layer 1: HOST BUILT-IN SKILLS
  ↓  Only convert if absent or inadequate
Layer 2: HOST MULTI-MODAL / CORE TOOLS
  ↓  Only convert if absent or inadequate  
Layer 3: CUSTOM SOURCE SKILLS (what you're packaging)
```

### Layer 1 — Host Built-in Skills

Many agent platforms ship their own skill libraries. Converting and re-shipping a skill that's already available on the target wastes bundle size, confuses the user (which version wins?), and may produce a worse experience than the native version.

**Always inventory the target's built-in skills first.** Methods:

| Platform | Discovery Method | Notes |
|---|---|---|
| **MiniMax.io** (M3 Agent Team) | Sidebar → Skills → Skill Hub; browse categories and note display names | ~50+ built-in skills. 21 design-relevant ones found (2026-07-07). See `references/platform-built-in-skills-minimax.md` |
| **Claude Code** | `~/.claude/skills/` + Claude docs | Built-in are documented, community ones in ~/.claude/skills/ |
| **Codex CLI** | `~/.codex/skills/` | Community skills only (no built-in) |
| **ChatGPT GPTs** | GPT Builder → Capabilities | TTS, DALL-E, Vision, Browser, Code Interpreter are built-in — no skill needed |
| **OpenCode** | Community registry | No built-in skills |

**Apply as exclusion filter, not just word-match:**

```python
# DON'T: just exclude by name-match
# DO: first build a set of platform built-in names, then skip those
PLATFORM_BUILT_INS = {
    "ui-ux-pro-max", "landing-page-builder", "pptx-generator",
    "mckinsey-presentation-generator", "html-presentation-generator",
    "visual-content-generator", "ui-ux-designer", "image-craft",
    "icon-maker", "minimax-pdf", "minimax-docx", "minimax-xlsx",
    "app-builder", "mini-coder-max", "senior-software-engineer",
    "prd-assistant", "seo-geo-optimization-expert",
    "deep-research-agent", "knowledge-digest",
    "industry-research-report-writer",
    "social-media-trend-search", "topic-tracker", "b2b-lead-generation",
}
```

Then in your conversion loop:

```python
if skill_name in PLATFORM_BUILT_INS:
    print(f"SKIP (built-in on target): {skill_name}")
    continue
```

### Layer 2 — Host Multi-Modal / Core Tools

Most cloud agent platforms (MiniMax.io, ChatGPT, Gemini) have core tools that aren't skills at all — they're platform primitives. Converting a skill that duplicates these is always wrong.

| Platform | Core Tools | Your Skill Equivalent to Skip |
|---|---|---|
| **MiniMax.io** (M3) | `image_generate` (FAL FLUX 2 Klein 9B), `video_generate` (PixVerse v6), `text_to_speech`, `vision_analyze`, Browser-Tools, Web Search/Extract | Skip: image-remix, comfyui (partially), all TTS/STT skills, web-tools, vision skills |
| **ChatGPT** | DALL-E, TTS, Vision, Browser, Code Interpreter, Python | Skip: image-gen, code-runner, STT |
| **Claude Codex CLI** | Local terminal only — no core tools | Keep all |
| **Gemini** | Imagen, Veo, TTS, Vision, Search | Skip: image-gen, video-gen, TTS, web-search |

### Layer 3 — Custom Source Skills (You Convert These)

Only skills that remain after applying Layer 1 and Layer 2 exclusions. These are your **additive value** — skills the target platform doesn't have natively and would benefit from.

**Valid design-to-MiniMax.io candidates** (from the 2026-07-07 design bundle):
- `ui-factory` (orchestrator — no built-in equivalent)
- `ui-color-system` (WCAG palette gen — unique)
- `ui-design-system` (token system — unique)
- `claude-design` / `html-artifact` (one-off HTML — unique)
- `popular-web-designs` (54 reference designs — unique)
- `anime-design` / `anime-style-forge` (14 sub-styles — no built-in equivalent)
- `film-shot` (8 cinematic styles — unique)
- `pixel-art`, `ascii-art`, `ascii-video` (retro style — unique)
- `architecture-diagram` / `excalidraw` (diagramming — unique)
- `humanizer` (AI-speech removal — unique)

### Bundle Naming Convention

Give bundles a **domain prefix** so the user knows what they're getting:

| Bundle | Contents | Layer-3 Skills | Companion |
|---|---|---|---|
| `yuno-minimax-skills-bundle-2026-07-07.zip` | 84 code skills | All coding tools | CHEATSHEET (coding) |
| `yuno-minimax-design-bundle-2026-07-07.zip` | 35 design/UI/creative/audio skills | All visual/design tools | CHEATSHEET (design) |

### Workflow Update — Add Step 0 and Step 0.5

The 3-layer strategy changes the Workflow:

```
0. Inventory TARGET built-in skills (web search, docs, platform explore)
0.5 Build PLATFORM_BUILT_INS + PLATFORM_CORE_TOOLS sets
1. Inventory source skills (unchanged)
2. Pre-flight secrets scan (unchanged)
3. Apply 3-LAYER EXCLUSIONS: skip Layer 1 + Layer 2 matches
   before even looking at source skills.
4-11. (unchanged)
```

### CHEATSHEET Variant — Layer-1-Aware

The CHEATSHEET should NOT just list converted skills. It should **cross-reference** the platform's built-in skills so the user knows what's already there:

```markdown
# Strategy: Built-ins First

## 🏆 Available Without Installation (MiniMax.io Built-in — 21 Skills)
| /skill | What it does |
|--------|-------------|
| /ui-ux-pro-max | 50+ styles, 97 palettes, 57 fonts |
| /landing-page-builder | High-end landing pages |

## 🎁 Custom Skills (35 Hermes Skills — Import These)
| /skill | Why import (not built-in) |
|--------|--------------------------|
| /ui-factory | Orchestrator — chains color→design→components→dashboard |
| /anime-design | 14 unique anime sub-styles — no built-in equivalent |
```

This tells the user: "I already know what the platform has. Here's only what's additive."

## Platform-Specific Built-in Skill Inventories

See reference files for per-platform discovery results:
- `references/platform-built-in-skills-minimax.md` — MiniMax.io M3 Agent Team built-in skills as of 2026-07-07 (21 design-relevant + ~30 code-relevant found via web research)

## Workflow

0. **Inventory target built-in skills.** Before touching source, explore the target platform. Web search, docs crawl, or platform-sidebar browse for built-in skills. Build a `PLATFORM_BUILT_INS` set (Layer 1) and `PLATFORM_CORE_TOOLS` set (Layer 2). See Pitfall #11 for the full method.
0.5 **Apply 3-Layer exclusions.** Subtract Layer 1 and Layer 2 skills from your conversion target before writing any converter. The remaining set (Layer 3) is what you actually need to convert.
1. Inventory source. Confirm layout with `find` / `ls`. Don't trust user — half-set-up namespaces happen.
2. Pre-flight secrets scan. Confirm hits with user.
3. **Define exclusion filters.** Per target platform, decide which skill categories to skip (see Pitfall #8). Composes WITH Layer 1/2 exclusions.
3.5 **Multi-bundle distribution analysis.** When the source corpus is 100+ skills and the target has no single natural bundle size, factor the corpus into themed sub-bundles. The 2026-07-07 session split 247 Hermes skills into 5 bundles: Code (90 skills), Design (35), Productivity (22), Security (9), Research (9). Method: (a) free-assign all skills to domain bins by name/category, (b) tally each bin, (c) discard bins that are too small or too domain-local (e.g. greyhack*, linux*, obsidian*), (d) merge trivial bins into bigger ones, (e) for surviving bins, estimate overlap with platform built-ins (Pitfall #11 Layer 1), (f) finalize bundle count. Ask the user to approve or trim before building. Build scripts per bundle share the same extractor but have different INCLUDE_NAMES arrays — see `references/multi-bundle-distribution-analysis.md` for the exact method and session data.
4. Pick destination layout. Flat-id under one umbrella dir. Document in docstring.
5. Write a minimal converter. Reference pattern below. For bash+Python hybrid: write `extract_meta.py` as standalone file, don't inline it in a bash heredoc.
6. Run dry-run first. Print what would be written, don't actually write yet.
7. Execute, then verify. Spot-check 3+ converted skills: `cat SKILL.md`, `ls references/`, `ls scripts/`.
8. **Generate companion artifacts:** CHEATSHEET.md (skill × use-case mapping — MUST cross-reference platform built-ins!), README.md (upload instructions), MANIFEST.json (machine-readable inventory).
9. **Package delivery.** Either push to git repository (step 8) or build a ZIP archive (see Pitfall #7).
10. Push to git if user wants sync. `gh repo clone` first, commit on feature branch, PR or merge.
11. Write `references/conversion-manifest.md` with source→dest layout, field-mapping table, exclusions (secrets), re-run instructions.

## Reference Implementation Pattern

```python
import shutil
from pathlib import Path

SOURCE_DIR = Path("/path/to/source/skills")  # walk & discover
DEST_ROOT = Path("/path/to/dest/umbrella/")   # flat-id namespace

def convert_one(skill_dir):
    hub_id = skill_dir.name
    src_skill = skill_dir / "SKILL.md"
    if not src_skill.exists():
        return False
    fm, body = parse_frontmatter(src_skill.read_text())  # block-scalar aware

    dest = DEST_ROOT / hub_id
    dest.mkdir(parents=True, exist_ok=True)

    # 1) Provenance original
    original_dir = dest / "scripts-originals"
    original_dir.mkdir(exist_ok=True)
    (original_dir / "SKILL.md.source").write_text(src_skill.read_text())
    if (skill_dir / "meta.yaml").exists():
        shutil.copy2(skill_dir / "meta.yaml", original_dir / "meta.yaml.source")

    # 2) Converted SKILL.md in destination format
    dest_skill_md = render_dest_format(fm, body)
    (dest / "SKILL.md").write_text(dest_skill_md)

    # 3) Assets: scripts, references, html (per-system conventions)
    for src_asset, dest_asset in ASSET_MAP.items():
        src_path = skill_dir / src_asset
        if src_path.exists():
            (dest / dest_asset).mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_path, dest / dest_asset, dirs_exist_ok=True)

    return True
```

## Common Pitfalls (Recap)

1. **Secrets in source.** Always grep `api_key|secret|password|bearer|token` before pushing.
2. **Multi-line block-scalar.** Use the block-scalar parser above.
3. **Category-collision overwrite.** Use flat-id under one umbrella, never map categories.
4. **No provenance preservation.** Always save `scripts-originals/` with `.source` extension.
5. **Pushing to populated GitHub repo without clone+add.** Use `gh repo clone` first.
6. **Hub-internal absolute paths leaking through.** Replace with relative or env-var paths.
7. **ZIP in /tmp (volatile).** Move to `~/10-Projekte/10-active/<project-name>/`.
8. **No platform-exclusion filter.** Target can't use system/GUI/OS-specific skills — filter them.
9. **Inline Python heredoc in bash.** Inline `python3 - << 'PYEOF'` truncates on multi-line f-strings — use a standalone `.py` file.
10. **Field-mapping assumptions.** Document the mapping table in converter docstring.
11. **Ignoring host platform's built-in skills.** Always apply 3-Layer Strategy (Pitfall #11) first. Don't convert what already exists.
12. **Name-to-path resolution under nested categories.** When you have a flat skill-name list (`INCLUDE_NAMES`) but skills live under nested category dirs (`~/.hermes/skills/<cat>/<subcat>/<name>/` or `~/.hermes/skills/<cat>/<name>/`), a simple `ls "$SRC"/*/SKILL.md` won't find them. Use `find` with a double loop or a flat skill-to-path lookup map. Rule of thumb: iterate categories→subdirs, then match name against include/exclude lists — not the other way around. A `grep <name> | head -1` fallback after `find` is the safe pattern.
13. **Bundle-size-to-value mismatch.** Not all bundles are equally useful. The 2026-07-07 session produced 5 bundles ranging from 100 KB/9 skills (Security) to 1.5 MB/90 skills (Code). The Research bundle (142 KB/9 skills) is arguably more immediately useful than the Productivity bundle (195 KB/22 skills) because Research has unique high-value skills (arXiv, NotebookLM) while Productivity is mostly wrappers around platform built-ins. Before building, estimate per-bundle size and ask the user: 'Bundle X will be small but has high-value unique skills Y; Bundle Z will be larger but mostly overlaps platform built-ins — still build it?'
14. **Per-bundle companion artifact drift.** When producing multiple bundles, each CHEATSHEET.md and README.md must be structured differently for its domain. A coding CHEATSHEET organizes by debug/test/build categories; a design CHEATSHEET organizes by medium (UI, diagram, anime, video). Don't copy-paste the same template. Track companion artifacts in a matrix: `{bundle: code, cheatsheet_sections: [debug, test, build, frontend, agents], readme_focus: "top-5 skills per category"}`.

## Verification Checklist

- [ ] Target platform built-in skills inventoried (web search, docs, or UI browse) — see Pitfall #11
- [ ] 3-Layer exclusions applied: Layer 1 (built-ins), Layer 2 (core tools), Layer 3 (custom) — only Layer 3 converted
- [ ] Multi-bundle distribution analysis done: domain bins tallied, small/trivial bins discarded, bundle count approved by user — see references/multi-bundle-distribution-analysis.md
- [ ] CHEATSHEET cross-references platform built-ins (Layer 1) so user knows what's already available
- [ ] Each bundle has domain-specific CHEATSHEET structure (coding vs. design vs. security — not a copy-paste)
- [ ] Bundle sizes estimated before build; user warned about size-to-value ratio (Pitfall #13)
- [ ] Name-to-path resolution verified for nested categories (Pitfall #12) — use `find` + match, not `ls`
- [ ] Source layout inventoried with `find` / `ls` before writing converter
- [ ] Secret preflight scan run, hits confirmed with user
- [ ] Platform-exclusion filter applied per target (see Pitfall #8)
- [ ] Destination layout = flat-id under one umbrella, collision-free
- [ ] Python extractor is a standalone `.py` file, NOT inline heredoc
- [ ] Field-mapping table documented in converter docstring
- [ ] Multi-line block-scalar handling verified on representative input
- [ ] `scripts-originals/` directory created per skill with original unmodified files
- [ ] Spot-check 3+ converted skills: `cat SKILL.md`, `ls references/`, `ls scripts/`, `cat meta.yaml`
- [ ] Companion artifacts generated: CHEATSHEET.md, README.md, MANIFEST.json
- [ ] ZIP built and moved to persistent project directory (not /tmp)
- [ ] GitHub push (if applicable): `gh repo clone` first, never `gh repo create` on populated repo
- [ ] `references/conversion-manifest.md` written with: source format, destination layout, field-mapping table, exclusions (secrets), re-run instructions

## Templates & Scripts

- `templates/hermes-to-hub/converter.py` *(not yet created — see `references/hermes-to-minimax-cli-pattern.md` for the bash+Python hybrid alternative)*
- `templates/hub-to-hermes/converter.py` *(not yet created)*
- `templates/skill-format-discovery.sh` *(not yet created)*
- `templates/cheatsheet-design-bundle.md` — Richer CHEATSHEET template for design/creative bundles with 3-layer strategy, workflow combos, and Layer 1→Layer 3 cross-reference table. Copy + paste and fill in the {{DATE}}/{{SKILL_COUNT}}/{{BUILTIN_COUNT}} placeholders.
- `scripts/extract-minimax-meta.py` — Standalone Python block-scalar parser. Usage: `python3 scripts/extract-minimax-meta.py <src_skill.md> <name> <category> <srcdir> <dstdir>`. Handles YAML frontmatter with `|` / `>` block scalars, trigger-word extraction, provenance metadata. Returns a one-line build log per skill.
- `scripts/secrets-preflight.py` *(not yet created)*

## References

- `references/hermes-to-minimax-cli-pattern.md` — Full session transcript of a Hermes → MiniMax.io batch conversion (84 skills). Includes the bash orchestration build.sh, exclusion filter arrays, CHEATSHEET/READme generation pattern, and ZIP packaging workflow. Read this first when doing a bulk Hermes → third-party conversion.
- `references/platform-built-in-skills-minimax.md` — MiniMax.io M3 Agent Team built-in skill inventory (21 design-relevant + ~30 code-relevant skills) discovered during the 2026-07-07 design-bundle build. Use as Layer-1 exclusion filter. Snapshot — re-inventory before each session.
- `references/format-mapping-table.md` *(not yet created)*
- `references/secrets-preflight.md` *(not yet created)*
- `references/pre-existing-skill-conflicts.md` *(not yet created)*
