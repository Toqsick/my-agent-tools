---
name: clip-export
description: |
  Use when rendering or pushing a completed video-editing project into JianyingPro or CapCut, selecting export targets and presets, or diagnosing draft compatibility.
  NOT for storyboarding, raw-footage editing, music generation, or exporting from unrelated nonlinear editors.
  Provides Python-driven direct and portable export workflows with target detection, project-draft generation, format selection, and verification.
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['editing', 'project', 'export', 'draft', 'generation']
keywords: ['editing', 'project', 'export', 'draft', 'generation']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Clip Export — Video Project Push Tool

You are a video editing AI assistant. You programmatically create video project drafts via Python scripts, supporting one-click push to JianyingPro or CapCut:

- **Direct mode** (`direct=True`): Creates project files directly in the JianyingPro/CapCut draft directory — open the app to preview and edit

## Supported Targets

| Target | Details |
|--------|---------|
| JianyingPro (Chinese edition) | `app_source: "lv"`, `app_id: 3704` |
| CapCut (International edition) | `app_source: "cc"`, `app_id: 359289` |

## Prerequisites

- Python 3.8+
- `pip3 install pyJianYingDraft` (v0.2.6 installed)
- **JianyingPro or CapCut must be installed locally**

## Output Mode

### Direct Mode (Recommended for JianyingPro/CapCut)

**CRITICAL — Distinguish between JianyingPro Chinese edition and CapCut International edition:**

| User says | App version | Draft directory |
|-----------|------------|----------------|
| **"Push to JianyingPro"** | JianyingPro (Chinese) | `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/` |
| **"CapCut" / "capcut"** | CapCut (International) | `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/` |

Rules:
- User says **"Push to JianyingPro"** → Use JianyingPro Chinese edition path (`JianyingPro`)
- User says **"CapCut" / "capcut"** → Use international edition path (`CapCut`)
- **If not specified → must ask the user**: Push to JianyingPro (Chinese) or CapCut (International)?

When the user wants to open in their local JianyingPro/CapCut, use `direct=True`. The draft is created directly in the app's draft directory — no manual import needed.

```python
project = JyProject("My Video", direct=True, overwrite=True)
# ... add assets ...
project.save()  # Appears directly in the CapCut draft list
```

- Auto-detects JianyingPro/CapCut draft directory (macOS / Windows)
- Auto-adapts format and platform fields for JianyingPro or CapCut

## Core API

All operations are performed through the `JyProject` class. Script path: `.claude/skills/clip-export/scripts/jy_wrapper.py`

### Create Project

```python
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), ".claude/skills/clip-export/scripts"))
from jy_wrapper import JyProject

# Direct mode: draft appears directly in CapCut (recommended)
project = JyProject("My Video", direct=True, overwrite=True)

# Portrait 1080x1920 + direct
project = JyProject("Portrait Video", width=1080, height=1920, direct=True, overwrite=True)

# Package mode: output zip (for distribution or other software)
project = JyProject("Distribution Video", overwrite=True)
```

### Add Video

```python
# Basic import
project.add_video("/absolute/path/video.mp4", start_time=0, duration="5s")

# Specify source start position (extract 5 seconds starting from the 10th second of the video)
project.add_video("/path/video.mp4", start_time="5s", duration="5s", source_start="10s")

# PiP picture-in-picture (independent track + scaling)
from jy_wrapper import ClipSettings
pip_seg = project.add_video(
    "/path/video.mp4",
    start_time="1s", duration="4s",
    track_name="PiP_Layer",
    clip_settings=ClipSettings(scale_x=0.3, scale_y=0.3),
)
```

### Add Audio

```python
# BGM
project.add_audio("/path/bgm.mp3", start_time=0, volume=0.6, track_name="BGM")

# Voiceover
project.add_audio("/path/voice.wav", start_time="2s", duration="10s", track_name="Narration")
```

### Add Text

```python
# Title text
project.add_text(
    "Big Title",
    start_time="1s", duration="3s",
    font_size=15.0,
    color_rgb=(1.0, 0.8, 0.0),  # Gold
    transform_y=0.4,             # Upper position
    bold=True,
)

# Subtitle (preset bottom position transform_y=-0.8)
project.add_subtitle("This is a subtitle", start_time="0s", duration="3s")

# Import SRT subtitle file
project.import_srt("/path/to/subtitles.srt", track_name="Subtitle Track")
```

### Filters

```python
# Add by name (supports Chinese/English + fuzzy matching)
project.add_filter("VHS_III", start_time=0, duration="10s")
project.add_filter("Retro Film", start_time=0, duration="10s", intensity=80.0)
```

### Scene Effects

```python
project.add_effect("CCD Flash", start_time="2s", duration="3s")
project.add_effect("Shake", start_time="5s", duration="2s")
```

### Keyframe Animation

```python
from jy_wrapper import KeyframeProperty

# First get a video segment reference
seg = project.add_video("/path/video.mp4", start_time=0, duration="4s")

# Scale animation: 1.0 → 1.5
JyProject.add_keyframe(seg, "uniform_scale", "0s", 1.0)
JyProject.add_keyframe(seg, "uniform_scale", "4s", 1.5)

# Position animation: left to right
JyProject.add_keyframe(seg, "position_x", "0s", -0.5)
JyProject.add_keyframe(seg, "position_x", "4s", 0.5)

# Rotation
JyProject.add_keyframe(seg, "rotation", "0s", 0.0)
JyProject.add_keyframe(seg, "rotation", "4s", 360.0)

# Opacity fade
JyProject.add_keyframe(seg, "alpha", "0s", 0.0)
JyProject.add_keyframe(seg, "alpha", "1s", 1.0)
```

Available properties: `position_x`, `position_y`, `rotation`, `scale_x`, `scale_y`, `uniform_scale`, `alpha`, `saturation`, `contrast`, `brightness`, `volume`

### Save & Export

```python
# Direct mode (project created with direct=True)
project.save()  # Automatically created in JianyingPro/CapCut draft directory, open the app to see it
```

Direct mode outputs to the draft directory — refresh the app to open it.

## Time Formats

All time parameters support multiple formats:

| Format | Example | Description |
|--------|---------|-------------|
| Seconds (float) | `2.5` | 2.5 seconds |
| Microseconds (int) | `2500000` | 2.5 seconds |
| String with unit | `"3s"`, `"500ms"`, `"1m30s"` | Auto-parsed |
| Colon format | `"01:30"`, `"00:01:30"` | min:sec or hr:min:sec |

## CLI Tools

### Asset Search

```bash
# Search all categories
python3 .claude/skills/clip-export/scripts/asset_search.py "retro"

# Search within a specific category
python3 .claude/skills/clip-export/scripts/asset_search.py "fade" -c transitions

# List asset overview
python3 .claude/skills/clip-export/scripts/asset_search.py --list
```

## Asset Library

| Category | Count | Data File |
|----------|-------|-----------|
| Filters | 1052 | `data/filters.csv` |
| Transitions | 453 | `data/transitions.csv` |
| Scene Effects | 1097 | `data/effects.csv` |
| Text Intro Animations | 155 | `data/text_animations.csv` |
| Text Outro Animations | 124 | `data/text_animations.csv` |
| Keyframe Properties | 11 | `data/keyframe_properties.csv` |

## Important Rules

1. **File paths must use absolute paths**
2. **Scripts must call `project.save()` at the end**
3. **Resolution must match**: Landscape 1920x1080 (default), portrait requires explicit `width=1080, height=1920`
4. **Do not guess asset names**: Use `asset_search.py` to search and confirm first
5. **Keyframe times are offsets relative to the segment start**, not absolute timeline times
6. **Always add `overwrite=True` in direct mode**: CapCut encrypts the JSON after opening a draft — regenerating requires overwrite
7. **User wants to open in JianyingPro/CapCut → use direct mode** (`direct=True`), other software → package mode. Distinguish versions: says "push to JianyingPro" → Chinese edition; says "CapCut" → International edition

## CapCut Test Verification Record

The following use cases have been tested and verified on CapCut 8.4 (macOS):

| Test | Content | Result |
|------|---------|--------|
| Minimal text | `add_text()` text only, no media | ✅ Opens normally |
| Single video | `add_video()` one 15s mp4 | ✅ Displays normally, no missing media |
| Complex mashup | 7 video/image clips + BGM + title + subtitles, 33s | ✅ Opens normally, all assets intact |

**Key fixes** (compared to earlier versions):
- `_copy_media_into_draft()` copies all external assets into the `Resources/` directory, resolving "missing media" caused by CapCut's sandbox
- `_patch_for_capcut78()` auto-detects CapCut path and injects correct `platform.app_source="cc"` + `app_id=359289`
- `_create_capcut_scaffold()` creates all auxiliary files required by CapCut (draft_agency_config / draft_biz_config / timeline_layout etc.)

## Pitfall Notes

### 1. Duration cannot exceed actual asset length

`add_video()`'s `source_start + duration` cannot exceed the source file's duration, otherwise it throws `ValueError: The extracted material time range exceeds the material duration`.

```python
# ✗ Wrong: 001.mp4 is only 1.5s, but duration is set to 3s
p.add_video("001.mp4", duration="3s")

# ✓ Correct: Confirm duration first, don't exceed
p.add_video("001.mp4", duration="1.5s")
```

**Best practice**: Use ffprobe to confirm asset duration first; leave a tiny margin for duration (e.g., `int(dur * 1_000_000)` microsecond precision), or omit duration to let the wrapper auto-detect.

### 2. ffprobe Duration Precision Pitfall

ffprobe's reported duration (e.g., `35.875011s`) and pyJianYingDraft's internally calculated duration (`35875000μs`) may differ by microseconds. When `source_start + duration` exactly equals the ffprobe duration, rounding can cause overflow.

```python
# ✗ Dangerous: ffprobe=35.875011s → 35875011μs, but asset duration=35875000μs
p.add_audio("long.mp4", duration=35.875011)  # Exceeds by 11μs → error

# ✓ Safe: Explicitly specify a slightly shorter duration
p.add_audio("long.mp4", duration="35.8s")
```

### 3. Images Can Be Used as Video

PNG/JPG files can be added via `add_video()` with arbitrary duration (not limited by source file length). Great for product close-ups and static frame transitions.

```python
p.add_video("product.png", start_time="5s", duration="4s")
```

### 4. Video Files as Audio Source

When using a video file for BGM/sound effects, the wrapper automatically calls ffmpeg to extract audio to `.m4a`. In direct mode, extracted audio goes to the draft's `audio/` subdirectory, which CapCut recognizes directly.

```python
# Automatically extracts audio track, no manual ffmpeg needed
p.add_audio("video_with_music.mp4", volume=0.4, track_name="BGM")
```

### 5. CapCut 7.8 Draft Encryption

After CapCut opens a draft, it **encrypts** `draft_info.json`, causing:
- Manual editing of the draft JSON becomes impossible
- Regenerating a same-named draft requires `overwrite=True`

**During iterative debugging**: Use a new draft name each time or `overwrite=True` to avoid operating on encrypted JSON.

### 6. Reusing the Same Asset

When the same file appears multiple times on the timeline, just call `add_video()` multiple times with different `source_start` values — the wrapper automatically reuses the material:

```python
# Same example.mp4, different segments
p.add_video("example.mp4", start_time="0s", duration="6s", source_start="0s")
p.add_video("example.mp4", start_time="11.5s", duration="7s", source_start="20s")
```

### 7. Best Pattern for Mashup Projects

Recommended template for product mashups / ad creative editing:

```python
p = JyProject("Project Name", width=1080, height=1920, direct=True, overwrite=True)

# 1. Lay down the video track (in timeline order)
p.add_video(...)  # Opening
p.add_video(...)  # Product close-up
p.add_video(...)  # Highlight clip
p.add_video(...)  # End card

# 2. Add filter (covering full duration)
p.add_filter("VHS_III", start_time=0, duration="total_duration")

# 3. Add effects (punctuate at transitions)
p.add_effect("CCD Flash", start_time="transition_time", duration="1.5s")

# 4. Add title + subtitles
p.add_text("Title", ...)
p.add_subtitle("Subtitle 1", ...)

# 5. Add BGM
p.add_audio("bgm.mp3", volume=0.4, track_name="BGM")

# 6. Save
p.save()
```

## Typical Workflow

1. User provides asset file paths (video/audio/images)
2. Confirm resolution (landscape/portrait)
3. **Confirm target app**:
   - User says **"push to JianyingPro"** → Direct mode + JianyingPro Chinese edition path (`JianyingPro`)
   - User says **"CapCut" / "capcut"** → Direct mode + International edition path (`CapCut`)
   - **Not specified → must ask the user**: Push to JianyingPro (Chinese) or CapCut (International)?
4. Write Python script to create the draft
5. Run the script
6. User reviews in the corresponding app
7. Iterate based on feedback

## Import Notes

### JianyingPro / CapCut (Direct Mode)
Direct mode auto-detects paths. Target is determined by the app name the user mentions:
- **"Push to JianyingPro"** → JianyingPro Chinese edition path (`JianyingPro`)
- **"CapCut"** → International edition path (`CapCut`)
- **Not specified → must ask the user**: Push to JianyingPro (Chinese) or CapCut (International)?

**macOS Draft Directories:**
- JianyingPro: `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/`
- CapCut: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`

**Windows Draft Directories:**
- JianyingPro: `%LOCALAPPDATA%/JianyingPro/User Data/Projects/com.lveditor.draft/`
- CapCut: `%LOCALAPPDATA%/CapCut/User Data/Projects/com.lveditor.draft/`

## Full Example

See `references/full_feature_showcase.py`

## Limitations

- Cannot modify existing drafts (JianyingPro/CapCut encrypts draft_info.json after opening)
- Cannot access GPU effects (smart cutout, beauty filters, etc.)
- Direct mode requires locally installed JianyingPro or CapCut (macOS / Windows)
- CapCut encrypts after opening a draft — regeneration requires `overwrite=True`
