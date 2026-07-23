---
name: skill-creator
description: >-
  Use when user asks for creating a new Hermes skill, modifying an existing skill, saving a successful workflow for reuse, extracting a skill from conversation history, or installing a marketplace skill. NOT for writing ordinary project documentation or capturing a trivial one-off action. Defines Hermes-native skill structure, progressive disclosure, frontmatter, validation, and safe lifecycle management.
version: 2.0.6
changelog:
- '2.0.6 (2026-07-03): Initial conversion from MiniMax Hub'
author: Toqsick + Yuno (Hub→Hermes conversion)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    source: minimax-hub
    hub_skill_id: skill-creator
    category: skill-creator
    domain: meta
    converted_at: '2026-07-03T23:19:32.985044'
  tags:
  - hub
  - conversion
  - workflow
triggers:
- skill-creator
agent: Yuno
routing_hint: 'Meta-Skill: erstellt/patcht andere Skills. Pair mit skill-install-workflow
  (skills.sh Imports). Wenn 3x derselbe Workflow → Skill extrahieren.'
trigger_keywords: ['skill', 'skill-creator', 'creating', 'new', 'hermes']
keywords: ['skill', 'hermes', 'user', 'asks', 'creating']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-agent-skill-authoring', 'skill-install-workflow']
---



> **Hub Origin:** Convexed from MiniMax Hub skill `skill-creator` (version 2.0.6). Original Hub-SKILL.md is preserved at `scripts-originals/SKILL.md.hub`, original meta.yaml at `scripts-originals/meta.yaml.hub`. All Hub-specific paths (e.g. `~/.hub-global/skills/skill-creator/`) translated to Hermes-equivalent references in `references/`.
# Skill Creator & Manager

Create, modify, install, and manage Skills. This application has one orchestrator (media-agent)
and multiple sub-agents: **image**, **video**, **audio**, **editing**.
Most Skills coordinate these agents to produce creative outputs.

## Directory Structure (Hermes-native, discovered 2026-07-16)

| Directory | Purpose | Managed By |
|-----------|---------|------------|
| `~/.hermes/skills/<category>/<name>/` | **User-created Skills** — category subdir IS REQUIRED | `skill_manage(action='create')` |
| `~/.hermes/skills/<name>/` | **Root-level: legacy/fallback** — works but category is `null` in index | Avoid; category drives discoverability |

**CRITICAL: Category Subdirectory required.** Skills placed in `~/.hermes/skills/<name>/` get `category: null` and DON'T appear in category-filtered `skills_list()`. Always use `~/.hermes/skills/<category>/<name>/SKILL.md`.

### Legacy Hub Directory Structure (archive only — old ecosystem, do NOT use for Hermes)

| Directory | Purpose | Managed By |
|-----------|---------|------------|
| `~/.hub/skills/` | **Market-installed Skills** | Automatically managed by the app; do not modify manually |
| `~/Movies/Hub/skills/` | **User-created/edited Skills** | Full user control |

## Installing Skills from the Marketplace

Guide users through the in-app Skill Plaza page:

1. Open the app → go to the "Skill Plaza" page
2. Browse available Skills in the Market tab
3. Click the "Install" button
4. Enable the Skill in the Skill list after installation

Installed Skills are stored in `~/.hub/skills/`, managed by the app, with automatic updates.

---

## Skill Creation Workflow

```
1. Capture Intent   --  Understand the workflow
2. Write SKILL.md   --  Author the Skill
3. Review & Iterate --  User feedback loop
4. Validate         --  Trigger tests + workflow walkthrough
5. Save & Reload    --  Save to user directory + trigger reload
6. Iterate (optional) -- Improve based on actual usage
```

### Three Usage Scenarios

**Scenario A: Save Current Conversation Workflow**
A workflow has already been completed in the conversation, and the user wants to solidify it as a Skill for reuse.
→ Extract the workflow from conversation history, proceed to STEP 1.

**Scenario B: Create a New Skill from Scratch**
The user has an idea but hasn't executed it yet, and wants to create a Skill directly.
→ Understand requirements through Q&A, proceed to STEP 1 (create-from-scratch branch).

**Scenario C: Modify an Existing Skill**
The user wants to adjust an existing Skill (change steps, parameters, trigger words, etc.).
→ Read the existing SKILL.md, understand modification intent, jump directly to STEP 2.

### What's Worth Saving as a Skill

Not every workflow is worth saving. Recommend saving only when at least two of the following apply:

- **Complexity**: More than 3 steps, involves multiple agents, or has branching logic
- **Reusability**: The user may repeat the same process with different inputs
- **Tacit knowledge**: Contains non-obvious techniques — model selection, parameter tuning, failure recovery strategies, creative techniques
- **Error correction history**: The user made corrections during the process that apply to future executions

If the workflow is a simple one-off operation (e.g., "generate one image"), suggest the user just describe it again next time.

---

## STEP 1: Capture Intent

### Scenario A: Extract from Conversation History

The conversation likely already contains the complete workflow. Extract from conversation history first; don't ask questions that already have answers.

#### Obtaining Conversation History

If the current context doesn't contain the complete workflow (it happened in a previous session),
use the agent's own conversation history capability to query previous session records.

**Skill Nesting**: Skills cannot nest-call other Skills. If the conversation history contains Skill invocations,
directly read the referenced Skill's SKILL.md to understand what it did — don't attempt to re-invoke it.

#### Extract from Conversation History:

1. **What happened**: Which capabilities were used, in what order
2. **Media flow**: Input (audio, images, text) → intermediate artifacts → final output
3. **Creative purpose**: Core intent
4. **Key decisions the user made**: Model selection, parameter adjustments, style direction
5. **Where things went wrong and were corrected**: Failures, retries, parameter changes — these are the most valuable knowledge
6. **What the user didn't change**: Default values working correctly is also information, indicating these parameters can remain flexible

#### Confirm Understanding

> "Here's what I extracted from the conversation: [summary]. Is this correct?"

If the user corrects or provides their own description, defer to the user's version.

### Scenario B: Create from Scratch

If there's no existing workflow, understand requirements through Q&A:

- What are the inputs? What's the final output?
- Rough sequence of steps?
- Any specific model or technical requirements?
- Any constraints (aspect ratio, duration, resolution, style consistency)?
- What's the hardest part — where does the agent tend to make mistakes?

### Scenario C: Modify an Existing Skill

1. Read the target Skill's SKILL.md
2. Understand what the user wants to modify
3. Jump directly to STEP 2 to make modifications

---

## STEP 2: Write the SKILL.md

### Directory Structure

```
skill-name/
├── SKILL.md           (required — Skill definition: name + description + system prompt)
├── meta.yaml          (required — display metadata: display-name-zh / version / tag / summary / desc)
├── scripts/           (optional — reusable scripts)
└── references/        (optional — reference docs loaded on demand)
```

### Three-Layer Loading Mechanism

1. **Metadata** (name + description) — always in agent context, used for trigger matching
2. **SKILL.md body** — loaded after Skill is triggered, keep under 500 lines
3. **Attached resources** — loaded on demand. Large docs go in `references/`, executable scripts in `scripts/`

### SKILL.md Frontmatter

SKILL.md only retains fields essential for agent runtime:

```yaml
---
name: my-skill                    # kebab-case, matches directory name
description: |
  Detailed description, first line is the summary.
  Includes trigger words for agent matching.
  Trigger words: keyword1, keyword2.
trigger-words: [keyword1, keyword2, keyword3, keyword4]
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | kebab-case, matches directory name |
| `description` | ✅ | **Hermes index: ~60 chars** (Hub meta.yaml: 200-500 chars in `desc-en`/`desc-cn`) |
| `trigger-words` | Optional | Trigger word list |
| `allowed-tools` | Optional | Required MCP tool names |

#### Yuno Convention (active — Yuno/Basti profile)

Skills created under Basti's profile use a richer frontmatter with 13 keys. This convention is used by `daily-briefing`, `self-improving`, `daily-report-trigger`, and all current Yuno skills:

```yaml
---
name: my-skill                    # lowercase-hyphens, matches directory name
description: |                    # ~60-120 chars, compact trigger phrase
  One-line summary for skill index.
version: 1.0.0                    # SemVer
author: Yuno
license: MIT
lane: koenigin                    # routing lane (koenigin/worker)
agent: Yuno                       # agent identity
trigger_keywords:                 # list of trigger phrases (lowercase)
  - keyword 1
  - keyword 2
keywords:                         # search/filter tags
  - category-tag
  - domain-tag
related_skills:                   # cross-references to other skills
  - skill-a
  - skill-b
last_curated: YYYY-MM-DD          # date of last review
curated_by: Yuno                  # who curated
routing_hint: >                   # one-liner for dispatch decisions
  Use when <trigger condition>.
---
```

| Key | Required | Description |
|-----|----------|-------------|
| `name` | ✅ | lowercase-hyphens, ≤64 chars, matches directory name |
| `description` | ✅ | ~60-120 chars, first ~60 visible in `skills_list` |
| `version` | ✅ | SemVer `MAJOR.MINOR.PATCH` |
| `author` | ✅ | Originator name |
| `license` | ✅ | SPDX identifier (MIT, Apache-2.0, etc.) |
| `lane` | ✅ | `koenigin` for orchestrators, `worker` for executors |
| `agent` | ✅ | Agent identity that owns the skill |
| `trigger_keywords` | ✅ | List of user-phrased triggers (lowercase, natural language) |
| `keywords` | ✅ | Category/domain tags for filtering |
| `related_skills` | ✅ | Cross-references to other skill names |
| `last_curated` | ✅ | ISO date of last review (`YYYY-MM-DD`) |
| `curated_by` | ✅ | Who performed the curation |
| `routing_hint` | ✅ | One-line dispatch rule, starts with "Use when..." |

**Key differences from Hub convention:** No `trigger-words` (use `trigger_keywords`), no `meta.yaml` (frontmatter is the only metadata source), required tracking fields (`last_curated`, `curated_by`), and explicit routing fields (`lane`, `agent`, `routing_hint`). All 13 keys are required for Yuno skills — omitting any makes a skill look half-finished in this profile.

#### Description Writing Guidelines

**Two-tier length rule (Hermes vs Hub):**

| Platform | Field | Length | Purpose |
|---|---|---|---|
| **Hermes** | SKILL.md `description:` (YAML) | **~60 chars** (max) | Index display in `available_skills` — must be a compact trigger phrase. Longer descriptions are silently truncated and lose keywords. |
| **Hub** | `meta.yaml` `desc-en:` / `desc-cn:` | 200-500 chars | Marketplace display, full elaboration. |

The Hermes `description:` field is the FIRST thing another agent sees when deciding whether to load this skill. It must fit the compact listing. Keep trigger-worthy keywords near the START — that's all that's guaranteed visible. The SKILL.md body (and Hub meta.yaml) handles the full elaboration.

**Examples:**

```yaml
# ✅ Good Hermes description (58 chars):
description: "Kanban playbook: health, dispatch, swarms, auto-decompose."

# ❌ Bad Hermes description (truncated at ~60 chars — happened 2026-07-15):
description: "Comprehensive multi-agent Kanban operations playbook — from health..."
# → Agent sees only "Comprehensive multi-agent Kanban operations playbook — from"
# → Useless for routing — none of the actual keywords visible.
```

- **Tone**: Describe user intent, not implementation details
- **Coverage**: Include multiple phrasings in the SKILL.md body, NOT the YAML description field
- **Boundaries**: Add brief disambiguation when similar Skills could be confused
- **Anti-pattern**: Don't write implementation steps in the description

### meta.yaml

Display metadata goes in a separate `meta.yaml`:

```yaml
display-name-zh: My Skill            # Chinese display name (≤10 characters)
version: 0.1.0                       # Semantic version
tag-en: "Visual Production / Image Generation"
tag-cn: "视觉创作 / 图像生成"
summary-en: "English UI summary, up to thirty words"
summary-cn: "中文摘要，不超过二十五个汉字"
desc-en: "English detailed description, 50-80 words..."
desc-cn: "中文详细描述，80-150 个汉字..."
```

| Field | Required | Description |
|-------|----------|-------------|
| `display-name-zh` | ✅ | Chinese display name (≤10 characters) |
| `version` | ✅ | Semantic version `MAJOR.MINOR.PATCH` |
| `tag-en` | ✅ | English category tag, format `"Domain / Stage"` |
| `tag-cn` | ✅ | Chinese category tag, format `"Domain / Stage"` |
| `summary-en` | ✅ | English UI summary (≤30 English words) |
| `summary-cn` | ✅ | Chinese UI summary (≤25 Chinese characters) |
| `desc-en` | ✅ | English detailed description (50-80 English words) |
| `desc-cn` | ✅ | Chinese detailed description (80-150 Chinese characters) |

Tags must be within a closed enum. Domains: Advertising / E-Commerce / Short Drama / Music Video / Documentary / Audio Content / Visual Production. Stages: Idea & Concept / Script Writing / Image Generation / Video Generation / Audio Generation / Post-Production / Prompt Engineering. Special: Platform Tooling (no stage).

### Quality Gates (Yuno Convention — mandatory for all new skills)

Yuno skills shipped in Basti's profile must pass these structural gates. They were derived from Basti's explicit spec for `daily-report-trigger` (2026-07-16) and apply to all new skills under this profile.

| Gate | Limit | Why |
|------|-------|-----|
| **Total size** | 4-7 KB (4096-7168 bytes) | Skills smaller than 4 KB lack substance; skills larger than 7 KB bloat session context. Target the middle (~5.5-6 KB). |
| **Em-dashes** | ≤1 | Em-dashes (—) break markdown rendering in some views and read as unnatural in German skill bodies. Replace with ":", "bis", "zu", or commas. |
| **Mid-line bold** | 0 | Bold tokens (`**text**`) that start mid-line become inline pseudo-headers. Keep bold for start-of-line emphasis only. |
| **Inline headers** | 0 | No `###` headers in paragraph body — use the section structure for hierarchy, not inline formatting. |
| **Code blocks** | Only for executable examples | Fenced code blocks in skill bodies are for demonstrable commands or JSON structures. Doku-only paths should be inline `` `code` `` references, not fenced blocks. |
| **Required keys (Yuno frontmatter)** | All 13 | `name`, `description`, `version`, `author`, `license`, `lane`, `agent`, `trigger_keywords`, `keywords`, `related_skills`, `last_curated`, `curated_by`, `routing_hint`. See Yuno Convention table above. |

#### Iterative Trimming Technique

When a skill exceeds the 7 KB ceiling, use this pattern to trim without losing content:

1. **Audit**: `wc -c SKILL.md` to get current size. Identify the fattest sections first (long paragraphs, wide tables, verbose examples).
2. **Collapse redundant qualifiers**: Replace `nicht vorhanden` → `fehlend`, `erkannt werden` → `zählen`, `nicht verfügbar` → `fehlt`, delete filler articles (`der/die/das` that aren't needed).
3. **Shorten multi-word intros**: `Aufruf von` → `via`, `liefert der Aufruf den Status` → `kommt ... als Default`, `wird ... übergeben` → active voice.
4. **Consolidate cross-references**: 3-sentence bullet lists → single comma-separated paragraph. Remove duplicated info (e.g. "skill" mentioned in both the name and the description).
5. **Trim tables**: Reduce column widths. Shorten header labels. Combine adjacent table cells.
6. **Re-verify**: Re-run `wc -c` and all quality gates after each trim pass. Target 10-15% reduction per pass to avoid overshooting.

This was demonstrated on 2026-07-16: a daily-report-trigger skill went from 9771 → 7037 bytes (~28% reduction) across 15+ iterative patches, removing 19 em-dashes in the process, while preserving all 8 required body sections and all 13 required frontmatter keys.

### Body Structure

1. `# Skill Name` — Title
2. Introduction paragraph — when to use, what media types are involved
3. Step-by-step — `## STEP N: Step Name`

Use `references/SKILL-TEMPLATE.md` as a starting template.

### Writing Principles

#### Describe Tasks, Not Routing

- Good: "Generate a 16:9 protagonist portrait — young woman in red dress, cinematic lighting"
- Bad: "Call image agent, use nano_banana model to generate..."

#### Only Mention Models When the User Explicitly Specifies

If the user says "use Kling for video generation," record it. Don't hardcode default values that the agent selects automatically.

#### Explain the Reasoning Behind Constraints

- Good: "Remove the audio track from lip-sync clips before final compositing, because the compositing step adds the original song and duplicate tracks cause audio overlap"
- Bad: "Must use the `-an` flag"

#### Capture the Creative Process, Not Implementation Details

- Good: "Analyze the music's emotional shifts, rhythm transitions, and vocal sections"
- Bad: "Call `read_media`, set the question parameter to..."

#### Batch Process, Don't Alternate

- Good: "Generate all scene images at once, then generate all videos at once"
- Bad: "For each segment: generate image first, then video, then move to the next"

#### Add User Confirmation at Creative Decision Points

Add confirmation steps before high-cost operations (video generation, final compositing). Don't confirm at every small step.

#### Encode User Error Corrections, Not Just the Happy Path

Retries and corrections are the most valuable knowledge.

#### Generalize from the Specific

- Good: "Analyze audio to determine section boundaries" (generic)
- Bad: "Split at 0:45, 1:30, 2:15" (file-specific)

#### All Outputs Go to the Session Project Directory

Don't hardcode output paths. Use file paths returned by tools for subsequent operations.

#### Keep Body Under 500 Lines

Move excess content to `references/`, extract executable patterns to `scripts/`.

---

## STEP 3: Review & Iterate

Present the complete SKILL.md to the user:

> "Here's the Skill I've written — anything you'd like to adjust?"

Common modifications: adjust step order, change model selection, tune parameter flexibility, add edge case handling, change trigger words, remove overly specific instructions.

---

## STEP 4: Validate

### 4a: Trigger Test

1. **Write 6 test queries** — 3 that should trigger, 3 that should not
2. **Self-test**: Looking only at name and description, ask yourself "would this trigger?"
3. **Show the user**: Present test queries and expected results

### 4b: Workflow Walkthrough

Using a hypothetical scenario different from the original conversation, walk through step by step:

- [ ] **Completeness**: Is each step's output the input needed for the next step?
- [ ] **Generality**: Are any steps bound to specific content from the original conversation?
- [ ] **Confirmation points**: Is user confirmation placed before high-cost operations?
- [ ] **Failure paths**: Does the Skill provide guidance when generation fails?
- [ ] **Batching strategy**: Are similar resources batch-processed or alternated individually?

---

## STEP 5: Save & Reload (Hermes-native)

After user confirmation, save to `~/.hermes/skills/<category>/<name>/` using the `skill_manage` tool:

### 1. Create the Skill

```python
# Hermes-native: use skill_manage(action='create') with category parameter
# This creates ~/.hermes/skills/<category>/<name>/SKILL.md automatically
```

Parameters:
- `action='create'` — creates a new skill directory + SKILL.md
- `name=<kebab-case-name>` — matches directory name
- `content=<full-SKILL.md-with-frontmatter>` — YAML frontmatter + markdown body
- `category=<str>` — REQUIRED (e.g. 'orchestration', 'meta', 'creative'). Without it, `skills_list` shows `category: null`

### 2. Add Support Files (after creation)

If references, templates, or scripts are needed, add them via:
```
skill_manage(action='write_file', name='<skill-name>', file_path='references/<topic>.md', file_content='...')
skill_manage(action='write_file', name='<skill-name>', file_path='templates/<name>.ext', file_content='...')
skill_manage(action='write_file', name='<skill-name>', file_path='scripts/<name>.ext', file_content='...')
```

### 3. Verify

After creation, confirm via `skills_list()` that the skill appears with its category. If it shows `category: null`, the skill was placed at the wrong path — move it to `~/.hermes/skills/<category>/<name>/`.

### 4. Inform the User

- Skill saved to `~/.hermes/skills/<category>/<name>/`
- Available in the current session immediately
- No manual reload needed (Hermes picks up changes live)

---

## STEP 6: Iterate & Improve (Optional)

The first version of a Skill is rarely the best. Come back to improve after actual usage.

### Observation Signals

| Signal | Meaning | Fix |
|--------|---------|-----|
| Agent doesn't trigger the Skill | Description is missing the user's phrasing | Expand trigger words |
| Triggers but executes poorly | Instructions unclear or ambiguous | Clarify steps, add examples |
| Triggers when it shouldn't | Description too broad | Add boundary descriptions |
| Agent writes similar scripts each time | Repeated work not packaged | Extract to `scripts/` |
| User always modifies the same step | Constraints too loose | Add explicit guidance with reasoning |
| Agent does unnecessary work | Instructions cause wasted effort | Remove or simplify |

### Improvement Process

1. Collect evidence from 2-3 usage sessions
2. Diagnose: trigger issue (description), execution issue (body), or missing resource?
3. Targeted fix: only change what's broken
4. Re-validate (run Step 4 checklist)
5. Use `skill_manage(action='patch')` for quick fixes, `skill_manage(action='edit')` for full rewrites
