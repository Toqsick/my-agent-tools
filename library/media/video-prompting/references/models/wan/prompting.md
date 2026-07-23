# Wan 2.6 Video Generation - Prompting Guide

## Model Overview

| Attribute | Value |
|-----------|-------|
| Tool Name | `wan_i2v_generation` (single) / `batch_wan_i2v_generation` (batch) |
| Duration | 5s, 10s, 15s |
| Resolution | 720P, 1080P |
| Input Modes | I2V (first frame image required) |
| Special Features | Audio-driven video generation (lip sync), multi-shot mode |

## Core Principles

### 1. Pure I2V Model

Wan 2.6 **requires a first frame image** (`image_path`) — pure text-to-video is not supported. The prompt's role is to guide how the first frame comes to life.

### 2. Basic Prompt Formula

```
[Subject] + [Action] + [Scene/Environment]
```

Advanced version:

```
[Subject] + [Action] + [Scene/Environment] + [Aesthetic control] + [Stylization]
```

### 3. Audio-Driven Generation (Core MV Scenario)

Provide an audio file via `audio_path`, and Wan will generate video driven by the audio's rhythm and vocal content:
- **Lip sync**: First frame of a speaking/singing character + corresponding audio clip
- **Rhythm matching**: First frame of dance/movement + music clip
- **Atmosphere linking**: Environment scene + background music

Batch generation (`batch_wan_i2v_generation`) supports up to 3 concurrent jobs — **the core tool for MV production**.

### 4. Single vs Multi Shot

- `shot_type: "single"` (default): Single shot — the entire video is one continuous shot
- `shot_type: "multi"`: Multi-shot — the model may switch between different angles/framings within the video

MV scenes typically use single, unless you need to simulate rapid editing.

## Best Practices

### Prompt Style: Concise and Direct

Wan works best with **short, direct prompts** — long descriptions are not needed:

```
✓ "A woman singing emotionally, close-up, tears in her eyes, soft lighting"
✗ "In this beautifully composed cinematic masterpiece, we see an incredibly talented young woman who appears to be in her late twenties, performing a deeply emotional song..."
```

### Action Verbs

Use **clear action verbs** to drive motion:

| Category | Example Verbs |
|----------|---------------|
| Character actions | walks, runs, turns, reaches, dances, sings, speaks |
| Camera movement | camera pans, camera zooms in, camera orbits, camera tilts up |
| Environment motion | wind blows, water flows, clouds drift, leaves fall, fire flickers |
| Lighting changes | light fades, sunlight breaks through, shadows shift |

### Camera Movement Modifiers

```
slow camera push in          → Slow push forward
smooth tracking shot         → Smooth tracking
handheld camera movement     → Handheld shake
static locked-off camera     → Completely static
gentle camera sway           → Subtle swaying (simulates breathing feel)
```

### Duration Planning

| Duration | Suitable Content | Action Complexity |
|----------|-----------------|-------------------|
| 5s | Single expression change, simple gesture, static atmosphere | 1 action |
| 10s | Complete action sequence, scene atmosphere, simple interaction | 2-3 actions |
| 15s | Full narrative segment, multi-step action sequences | 3-4 actions |

### Audio-Driven Best Practices (MV Scenarios)

1. **Cut audio clips precisely**: Use `audio_subclip_batch` to pre-split by timestamp
2. **Character's mouth slightly open in first frame**: Produces more natural lip sync
3. **Audio duration ≤ video duration**: Audio cannot be longer than the video
4. **Moderate-speed segments work best**: Very fast rap may not sync properly
5. **Unified resolution for batch generation**: Makes subsequent stitching easier

## Common Pitfalls

1. **First frame image is required**: Missing the first frame will cause an error
2. **Don't write overly long prompts**: Under 50 words works best
3. **Don't describe what's already in the first frame**: The model already sees it — focus on describing **changes and motion**
4. **Don't write contradictory actions with audio**: If the audio is a quiet piano piece, don't write "energetic dancing"
5. **Quality may drop in the second half of 15s videos**: Place important content in the first 10s

## Example Prompts

### MV Lip Sync (5s, I2V + audio)

```
image_path: [singer close-up first frame]
audio_path: [corresponding song clip]
prompt: "Close-up, a woman singing passionately, subtle head movements, emotional expression, cinematic lighting"
duration: 5
```

### Atmospheric B-Roll (10s, I2V)

```
image_path: [rainy city street first frame]
prompt: "Rain falling on empty street, reflections shimmering on wet asphalt, camera slowly moves forward, moody atmospheric lighting, neon signs flickering"
duration: 10
```

### Character Action (10s, I2V)

```
image_path: [woman in traditional dress standing first frame]
prompt: "Woman in traditional dress turns around gracefully, her long sleeves flowing in the wind, cherry blossoms falling around her, slow motion, ethereal atmosphere"
duration: 10
```

### MV Batch Generation Example

```python
# batch_wan_i2v_generation parameter example
image_paths: [scene1.jpg, scene2.jpg, scene3.jpg]
audio_paths: [clip1.wav, clip2.wav, clip3.wav]
prompts: [
    "Singer performing emotionally, close-up, tears rolling down, soft warm lighting",
    "Wide shot, figure walking alone on moonlit beach, waves crashing, melancholic atmosphere",
    "Two hands reaching for each other in slow motion, golden hour backlight, romantic"
]
durations: [5, 10, 5]
resolution: "1080P"
```
