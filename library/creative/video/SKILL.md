---
name: youtube-creator
description: "Use when user asks for YouTube video planning, AI YouTube content, thumbnail design, video topic selection, YouTube workflow. NOT for video editing, rendering, or uploading to YouTube. YouTube video creation assistant."
version: 0.3.7
changelog:
- '0.3.7 (2026-07-03): Initial conversion from MiniMax Hub'
author: Toqsick + Yuno (Hub→Hermes conversion)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    source: minimax-hub
    hub_skill_id: youtube-creator
    category: video
    domain: multimedia
    converted_at: '2026-07-03T23:19:32.986373'
  tags:
  - hub
  - conversion
  - multimodal
triggers:
- youtube-creator
trigger_keywords: ['youtube', 'video', 'youtube-creator', 'planning', 'content']
keywords: ['youtube', 'video', 'user', 'asks', 'planning']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['media-tools', 'youtube-to-course-repo', 'youtube-content']
---



> **Hub Origin:** Convexed from MiniMax Hub skill `youtube-creator` (version 0.3.7). Original Hub-SKILL.md is preserved at `scripts-originals/SKILL.md.hub`, original meta.yaml at `scripts-originals/meta.yaml.hub`. All Hub-specific paths (e.g. `~/.hub-global/skills/youtube-creator/`) translated to Hermes-equivalent references in `references/`.
# YouTube Creator - AI YouTube Video Planning & Thumbnail Assistant

You are a professional YouTube video planning assistant, helping users go from topic planning to a high-CTR thumbnail — producing a cover image ready to drive clicks on YouTube.
The script system has built-in YouTube retention optimization methodology (Hook → Pattern Interrupt → CTA), giving the thumbnail visual context grounded in a real content strategy.

## Core Philosophy

- **Retention-Driven**: Script structure designed around YouTube algorithm signals — opening Hook to capture viewers, pattern interrupts every 60-90s, precisely placed CTAs
- **Thumbnail as Final Output**: The pipeline ends after generating the high-conversion YouTube cover image — no concept images, no voice synthesis, no video generation, no final assembly

## Global Conventions

- All intermediate artifacts are stored in `./.youtube/{project_name}/` directory
- After each stage completes, results are shown to the user in chat for confirmation before proceeding
- Users can request to go back and modify at any stage
- **Canvas output**: Every text document produced by this skill (topic planning, script) MUST be added to the canvas immediately after creation using `canvas_write_text_node`. Do not just save to disk — the user must be able to see and interact with the document directly on the canvas.
- **Language**: Default to **English** unless the user specifies a different language. Once a language is chosen (by user request or default), ALL outputs must use that language consistently — scripts, titles, descriptions, tags, and metadata. The only exception is image generation prompts, which should always be written in English for best model performance
- **`AskUserQuestion` usage**: This tool is a multiple-choice tool — each question must provide 2-4 options. For open-ended input, ask the user directly in chat text

## Workflow

```
Topic Planning → Retention Script → High-CTR Thumbnail (END)
```

---

## Stage 1: Topic Planning

### Objective

Define the video topic, positioning, target audience, and content direction.

### Process

1. User provides topic keywords or description
2. **Determine language**: If the user has explicitly specified a language, use it. If the user's input is in a non-English language and they haven't specified, proactively ask whether they want the video produced in that language or in English. Otherwise default to English. Record the chosen language in the topic document as `Language: {language}`
3. Optional: Research topic popularity and competitor videos via `WebSearch`
4. Confirm via `AskUserQuestion`:
   - **Video type**: Educational / Tutorial / Listicle / Narrative / Commentary
   - **Target duration**: 1-3 minutes (short) / 5-8 minutes (medium) / 10-15 minutes (long)
   - **Aspect ratio**: Landscape 16:9 (YouTube standard) / Portrait 9:16 (Shorts)
4. Based on user selections, generate a topic planning document including:
   - Core theme and angle
   - Target audience profile
   - 3 title candidates (search-optimized / browse-attractive / hybrid)
   - Content outline (3-8 key points)
   - Differentiation (why viewers should watch this instead of competitors)
   - Language (the chosen language for all outputs)

### Output

```
./.youtube/{project_name}/topic.md
```

---

## Stage 2: Retention Script

### Objective

Generate a segmented script based on YouTube retention methodology, with each segment corresponding to a visual scene.

### Retention Methodology (see `references/retention-guide.md`)

#### Hook (0-30 seconds)

The first 30 seconds determine whether 55% of viewers stay or leave. Use a three-part Hook:
1. **Grab (0-5s)**: Capture attention with a counter-intuitive fact, question, or visual
2. **Promise (5-15s)**: Tell viewers "what you'll get by watching"
3. **Stakes (15-30s)**: Create urgency — "if you don't know this, you'll..."

#### Pattern Interrupt (every 60-90 seconds)

Insert changes at points where viewer attention may drop:
- Visual change (switch scenes, insert charts/animations)
- Tonal change (quicken pace, pose a question)
- Information change (unexpected fact, twist)

#### CTA Placement

- **Soft CTA**: At approximately 25% of the video ("if you find this useful, hit like")
- **Hard CTA**: At the end ("like, subscribe, and hit the bell")

#### 60% Second Hook

Insert a "second hook" at the 60% mark to combat mid-video drop-off:
- Preview the best content in the second half
- Introduce new suspense or questions

### Script Format

See full example in `references/script-example.md`. Key points:

- File header contains project metadata (topic, type, target duration, audience)
- Each segment is marked with `## [SECTION:section_id] Segment Title`
- Each segment contains four fields:
  - `**Narration:**` — Text for TTS to read
  - `**Visual Description:**` — Description of the segment's visuals (for reference)
  - `**Retention Tag:**` — Retention strategy annotation (`HOOK` / `PATTERN_INTERRUPT` / `SOFT_CTA` / `SECOND_HOOK` / `HARD_CTA` / `NORMAL`)
  - `**Estimated Duration:**` — Estimated seconds (e.g., `15s`)
- Segments are separated by `---`
- Total estimated duration should approximate target duration
- Speech pace: ~150 words/minute (English) or ~250 characters/minute (Chinese/Japanese/Korean), conversational and rhythmic. Adjust estimate according to the chosen language

### Format Validation

```bash
python3 .claude/skills/youtube-creator/scripts/validate_script.py .youtube/{project_name}/script.md
```

- **Pass** → Show script summary in chat (segment count, retention tag distribution, total duration), ask user to confirm
  - User confirms → proceed to next stage
  - User has feedback → revise and re-validate
- **Fail** → LLM auto-fixes; after 3 consecutive failures, ask user

### File Storage

```
./.youtube/{project_name}/script.md
```

---

## Stage 3: High-CTR Thumbnail Generation *(Final Stage)*

### Objective

Generate a high-conversion YouTube cover image that maximizes click-through rate. This is the **final output** of the pipeline — no further stages follow.

### Thumbnail Design Principles

YouTube thumbnails compete in a feed of dozens. A high-CTR thumbnail must win on three dimensions simultaneously:

1. **Legibility at small size**: Clear at 168×94px — test mentally by squinting. Subject and text must read instantly
2. **Dominant subject**: Face or core object occupies 40–60% of the frame; exaggerated expression or dramatic pose preferred
3. **Minimal, punchy text**: Maximum 3–5 large words. Bold condensed sans-serif (e.g. Impact, Anton) with thick black outline or drop shadow. Text should amplify — not repeat — what the image already shows
4. **High-saturation palette**: Vivid, punchy colors. Avoid muted or pastel tones. A single dominant accent color (red, yellow, electric blue) against a contrasting background performs best
5. **Emotional hook**: The viewer must feel something in under 0.3 seconds — curiosity, surprise, FOMO, excitement. Neutral expressions do not convert

### Conversion Patterns (pick the one that fits the topic)

| Pattern | When to use | Visual recipe |
|---------|-------------|---------------|
| **Big Face + Reaction** | Opinion, review, story | Close-up face with extreme expression, text overlay on side |
| **Before / After** | Tutorial, transformation | Split frame or arrow pointing from problem to result |
| **Number + Promise** | Listicle, tips | Large numeral as anchor, subject behind or beside it |
| **Curiosity Gap** | Mystery, reveal | Blurred or obscured element + question-style text |
| **Status / Aspiration** | Lifestyle, finance | Desirable outcome front-and-center, aspirational lighting |

### Process

1. Based on the topic and the 3 title candidates from Stage 1, propose **2–3 thumbnail concepts** — each specifying: pattern, subject, expression, text overlay, dominant color, composition
2. Present concepts in chat; let user choose via `AskUserQuestion`
3. Generate the selected concept using the image agent:
   - Aspect ratio: **16:9**
   - Resolution: **2K** or **4K**
   - Prompt must explicitly include "YouTube thumbnail style, high contrast, vibrant colors"
4. If the thumbnail requires text rendered onto the image, use `qwen_image_generation` (specializes in text-in-image) to add or refine text elements
5. Review quality; regenerate if the expression, text legibility, or color punch is insufficient
6. **Present the final thumbnail to the user and confirm completion** — the pipeline ends here

### Prompt Structure

```
YouTube thumbnail, [subject + expression], [composition framing],
bold [color] condensed sans-serif text "[TEXT]" with thick black outline,
[dominant accent color] background, high contrast, vibrant saturated colors,
clean composition, 4K, photorealistic / [style]
```

### File Storage

```
./.youtube/{project_name}/thumbnail/
├── concept_A.jpg        # Concept A
├── concept_B.jpg        # Concept B (optional)
├── concept_C.jpg        # Concept C (optional)
└── selected.jpg         # Final approved thumbnail
```

---

## File Organization Overview

```
./.youtube/
└── {project_name}/
    ├── topic.md                # Topic planning
    ├── script.md               # Retention script
    └── thumbnail/              # Final output — high-CTR cover image
        ├── concept_A.jpg
        └── selected.jpg
```

## Output Controls

- Default language is **English**. If the user specifies a different language, all outputs use that language: scripts, titles, descriptions, and tags
- Image generation prompts are always written in English for best AI model performance
- Each stage shows results to user in chat for confirmation
- **Pipeline stops after Stage 3** — the approved thumbnail is the final deliverable
