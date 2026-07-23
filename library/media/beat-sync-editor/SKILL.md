---
name: beat-sync-editor
description: "Use when user asks for beat-sync video editing, music-driven cuts, audio beat detection for video sync. NOT for non-music video editing or audio engineering. Beat-sync video editing skill."
trigger-words:
- music beat sync
- beat-sync editing
- beat-sync video
- rhythm editing
- auto beat sync
- beat sync
- beat detection
- music sync edit
- edit to the beat
- sync to beat
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['video', 'beat', 'sync', 'editing', 'music']
keywords: ['video', 'beat', 'sync', 'editing', 'music']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ascii-video', 'youtube-creator', 'comfyui']
---


# Beat-Sync Editor — Music Beat-Synced Editing

Use this Skill when the user wants to "take a batch of images/video clips, set them to music, and auto-switch on the beat."
Core pipeline: **Music source confirmation → Energy-tension analysis → Target duration trimming → Beat detection → Timeline planning → Asset allocation → ffmpeg concatenation → Final output**.

---

## STEP 0: Collect Input

Confirm these three inputs — ask the user for any that are missing:

### 0a. Music Source (Choose one of three)

| Type | Action |
|------|--------|
| HTTP/HTTPS URL | Download to session directory using `curl -L -o music.ext <url>`, record local path |
| Local file path | Use directly, call `save_file_to_session` to register in session |
| AI-generated music | Call **audio agent**, specify style/BPM/duration requirements, get the generated local path |

> **Note**: After downloading, verify file duration with `ffprobe`, record `total_duration` (seconds).

### 0b. Asset List

Supports three types (can be mixed):

- **Images** (jpg/png/webp): Each image will be processed into a static video segment
- **Video clips** (mp4/mov): Used directly — trimmed by timeline or used in full
- **AI-generated image supplements**: If the user's assets are fewer than the beat count, inform the user and ask whether to call image agent for auto-generated supplementary images

Record local paths for all assets.

### 0c. Beat-Sync Parameters

Ask the user (if not specified):

| Parameter | Default | Description |
|-----------|---------|-------------|
| Detection mode | `beat` | `beat` = standard beat tracking / `onset` = onset detection (more sensitive) / `segment` = auto segmentation |
| Switch every N beats | `1` | `2` means switch assets every 2 beats, creating a more relaxed rhythm |
| Manual keypoints | None | User can provide additional time points (seconds) to force asset switches at those moments |
| Output aspect ratio | `9:16` | Portrait short video / `16:9` landscape / `1:1` square |

---

## STEP 0.5: Energy-Tension Analysis + Target Duration Trimming

> **Trigger condition**: Audio duration > user's expected final video duration, or user hasn't specified duration but audio exceeds 60s.
> If audio is already short (≤ 30s) or user explicitly says "use the whole song," skip this step and go directly to STEP 1.

### 0.5a. Run Energy-Tension Analysis Script

Use the built-in script `scripts/energy_analyze.py` to analyze the audio's energy distribution and find the segments with the highest emotional tension:

```bash
python scripts/energy_analyze.py <local_music_path> \
  --targets "15,30,60" \
  --out json
```

Script output:
- `energy_peak`: Timestamp of the global energy peak (seconds)
- `sections`: Sections ranked by energy score (high → low)
- `trim_options`: **Optimal trim windows** for each target duration (15s / 30s / 60s) with start, end, energy_score, and description

> **Script path**: `scripts/energy_analyze.py` (in the same directory as SKILL.md)

### 0.5b. Present Trimming Options to the User

Organize analysis results into options and **present them to the user using a question component**:

Display format example:
```
🎵 Total audio duration: 202s | BPM: 143 | Energy peak: 87.3s

Choose your final video duration:

  ① 15s  ▎from 80.1s → 95.1s  ▏Tension ★★★★★  Covers the strongest burst, highest emotional tension
  ② 30s  ▎from 72.0s → 102.0s ▏Tension ★★★★☆  Complete chorus section
  ③ 60s  ▎from 62.0s → 122.0s ▏Tension ★★★☆☆  Includes intro lead-in + complete chorus
  ④ Use full audio (202 seconds)
  ⑤ Custom time range (manually input start/end)
```

**Energy star rating conversion**: energy_score ≥ 0.85 = ★★★★★, ≥ 0.70 = ★★★★☆, ≥ 0.55 = ★★★☆☆, otherwise = ★★☆☆☆

**Default recommendation**: Highlight the option with the highest energy_score (usually the shortest duration, since smaller windows focus more easily on high-energy regions).

### 0.5c. Trim Audio Per User Selection

After user confirmation, trim audio to the target segment with ffmpeg. All subsequent steps (beat analysis, asset allocation, synthesis) are based on the trimmed audio:

```bash
ffmpeg -i <original_audio> -ss <start> -to <end> -c copy <audio_trimmed.mp3>
```

> **Why trim before beat analysis**: Beat analysis computation scales with audio duration;
> also, beat_times from trimmed audio directly correspond to the final video's timeline, eliminating offset conversion.

---

## STEP 1: Beat Detection

Use the built-in script `scripts/beat_detect.py` for beat detection:

```bash
# Install dependencies (first run)
pip install librosa soundfile

# Run detection
python scripts/beat_detect.py <local_music_path> \
  --mode <beat|onset|segment> \
  --every-n <N> \
  --manual "<t1,t2,...>" \
  --min-gap 0.25 \
  --out json > beat_result.json
```

Script output JSON contains:
- `bpm`: Detected BPM
- `total_duration`: Total music duration (seconds)
- `beat_count`: Number of valid beats
- `beat_times`: List of beat time points (seconds)
- `sections` (segment mode only): Segment analysis results

> **Script path**: `scripts/beat_detect.py` (in the same directory as SKILL.md)

Display detection summary to user: BPM, beat count, duration. Confirm it looks reasonable before proceeding.

---

## STEP 2: Timeline Planning

Based on beat analysis results, **compute each asset segment's time interval in the orchestrator**:

```
segments = []
for i in range(len(beat_times)):
    start = beat_times[i]
    end   = beat_times[i+1] if i+1 < len(beat_times) else total_duration
    duration = end - start
    segments.append({ "index": i, "start": start, "end": end, "duration": duration })
```

**Asset allocation rules**:
- Asset count ≥ beat count: Take the first N in order, discard extras
- Asset count < beat count: **Loop reuse** (`material_index = segment_index % len(materials)`), and inform the user about reuse
- If user doesn't accept reuse: Suggest calling image agent to generate supplementary images matching the shortfall

**Segment mode additional logic**:
- Intro/outro (`intro`/`outro`) has wider beat intervals — suggest allocating one asset per beat (slow cuts)
- Chorus/climax (labels containing "chorus") has narrower beat intervals — suggest maintaining original beat density (fast cuts)
- If user provided manual keypoints, these positions force switches regardless of the every-N parameter

Display a planning summary table to the user (first 5 rows + totals), confirm before proceeding.

---

## STEP 3: Asset Preprocessing

Call **editing agent** to batch-process all assets to uniform specs:

Instruct the editing agent:

> "Please process the following N asset files, converting each to these specifications:
> - Resolution: [target width x height, based on output ratio, e.g., 1080x1920]
> - Frame rate: 30fps
> - Codec: h264, pixel format yuv420p
> - For **images**: Convert to a [duration]s static video (duration from timeline planning)
> - For **videos**: Trim to the first [duration]s; if the clip is too short, loop to fill or pad with black frames
> - For **size mismatches**: Use scale+pad (maintain original aspect ratio, pad with black bars)
> Output file naming: `clip_001.mp4`, `clip_002.mp4` ..."

**Why preprocess**: ffmpeg concat requires all clips to have identical resolution, frame rate, and codec — otherwise synthesis will error or produce visual tearing.

---

## STEP 4: Preview Confirmation (Optional)

If the user explicitly requests a preview, or asset count > 20, **before synthesis** display:
- Timeline planning table (index / asset filename / start time / duration)
- Estimated total video duration

Ask the user if adjustments are needed:
- Swap an asset at a specific position
- Adjust the every-N parameter and re-plan
- Manually add/remove beat keypoints

If adjustments are made, return to STEP 2 for re-planning — no need to redo beat detection.

---

## STEP 5: ffmpeg Concatenation and Synthesis

Call **editing agent**, providing the following information:

> "Please concatenate the following clips in order and mix in the audio track:
>
> Clip list: `clip_001.mp4`, `clip_002.mp4`, ... `clip_N.mp4`
> (in the order generated by STEP 3)
>
> Audio track: `<local_music_path>`
>
> Requirements:
> - Use ffmpeg concat (no transcoding, direct stream merging)
> - After video synthesis, strip all original audio tracks from assets (-an) to avoid audio stacking
> - If music is longer than video, truncate (`-shortest`); if shorter, loop (`-stream_loop -1`)
> - Output file: `beat_sync_output.mp4`
> - Codec: h264 + aac, quality CRF 18"

**Why strip original asset audio**: The synthesis step overlays the music track — keeping original asset audio would produce doubled audio.

---

## STEP 6: Present Final Output

Show the user `beat_sync_output.mp4` with this summary:

```
✅ Beat-sync video generation complete

🎵 Music: <filename> | BPM: <bpm>
🎬 Assets: <N> total (X images + Y video clips)
⏱ Final duration: <duration>s
📐 Output ratio: <ratio>
🔄 Asset reuse: <yes/no>
```

If the user wants adjustments:
- **Swap asset**: Replace asset at specified position → Return to STEP 3 to reprocess only that asset, then back to STEP 5 for synthesis
- **Adjust rhythm** (change every-N) → Return to STEP 2 for re-planning
- **Change music**: Full pipeline restart (from STEP 1)
- **Add transitions** (fade in/out etc.): Instruct editing agent to add fade filters to each clip during synthesis

---

## Technical Notes

### Dependency Installation
```bash
pip install librosa soundfile  # Shared by both scripts
```

### energy_analyze.py Script Parameter Reference

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--targets "15,30,60"` | Target duration list to compute (seconds) | Adjust per scenario, e.g., `"30,45,90"` |
| `--out json` | Output format (json / text) | text for quick debugging |

**Energy analysis dimensions** (weighted composite):
- Loudness (RMS) × 0.5 — Most directly reflects volume intensity
- Beat impact strength (Onset Strength) × 0.3 — Reflects drum/beat burst intensity
- Timbral brightness (Spectral Centroid) × 0.2 — High-energy sections usually have richer high frequencies

### beat_detect.py Script Parameter Reference

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--mode beat` | Standard beat tracking (default) | Pop/electronic music |
| `--mode onset` | Onset detection, more sensitive to percussion | Rap/drum-heavy tracks |
| `--mode segment` | Segment analysis, auto-identifies intro/chorus | Pop songs with distinct sections |
| `--every-n 2` | Output one cut point every 2 beats | When assets are few, for a more relaxed rhythm |
| `--manual "8.5,32.0"` | Force cut points at 8.5s and 32.0s | User has specific keyframe requirements |
| `--min-gap 0.5` | Minimum 0.5s gap between adjacent cut points | Prevent overly rapid switching |

### Common Issues

**Q: The "high-energy segment" found by energy analysis doesn't feel accurate?**
→ Likely a strings/vocal-dominated song where energy characteristics aren't as obvious as percussion. Let the user choose "Custom time range" for manual input.

**Q: Too many beats detected, frames switch too fast?**
→ Increase `--every-n`, or increase `--min-gap`, or switch to `segment` mode

**Q: Beat detection is inaccurate for certain sections (e.g., strings, vocals)?**
→ Switch to `--mode onset`, or have the user manually provide keypoints via `--manual`

**Q: Far fewer assets than beats?**
→ Default is loop reuse; or ask user whether to call image agent to AI-generate images to fill the gap

**Q: ffmpeg synthesis errors with "Stream codec parameters not set"?**
→ A file in STEP 3 preprocessing may have failed conversion. Have the editing agent check and reprocess the failed assets
