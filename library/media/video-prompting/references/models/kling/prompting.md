# Kling Video Generation - Prompting Guide

## Model Overview

| Attribute | Value |
|-----------|-------|
| Tool Name | `kling_omni_video_generation` |
| Available Models | kling-v1-6, kling-v2-master, kling-v2-5-turbo, kling-v2-6 (default) |
| Duration | 5s or 10s |
| Modes | std (standard), pro (professional, supports sound) |
| Input Modes | T2V, I2V (`first_frame_image_path`) |
| Special Features | Pro mode can generate video with sound (`enable_sound: true`) |

## Core Principles

### 1. Prompt Style: Director's Instructions

Kling responds best to **structured, directorial commands**. Organize prompts in this order:

```
[Camera setup] + [Subject description] + [Action directives] + [Environment/Scene] + [Lighting] + [Emotion/Atmosphere] + [Technical parameters]
```

### 2. Pro Mode and Sound

When sound is needed in the video, you must set:
- `mode: "pro"`
- `enable_sound: true`

Sound type is automatically inferred from the visual content — audio cannot be precisely controlled via prompt. Works well for ambient and natural sound effects, not suitable for dialogue or music.

### 3. Negative Prompt

Kling supports `negative_prompt` to exclude unwanted elements:

```
negative_prompt: "blurry, distorted faces, extra fingers, deformed hands, low quality, watermark, text overlay"
```

## Best Practices

### Character Generation

Kling excels in **character consistency and facial quality**:

- Describe facial features and expressions in detail
- Specify clothing details to maintain consistency
- Facial expression changes are a Kling strength — use them confidently
- In I2V mode, the face quality of the first frame directly determines video quality

### Motion Control

- **Simple repetitive actions** work best: walking, turning head, waving, nodding
- **Complex full-body movements** (dance, fighting) require lower expectations
- Use **temporal adverbs** to control pacing: slowly, gradually, suddenly, gently
- Schedule 1 main action within 5s, 2-3 actions within 10s

### Camera Movement

Kling understands camera movements with high precision:

```
Static shot          → Fixed camera, ideal for character performance
Slow pan right       → Slow lateral movement, ideal for environment showcase
Dolly zoom           → Hitchcock zoom, dramatic effect
Low angle shot       → Looking up, adds grandeur
Over-the-shoulder    → Over-shoulder shot, conversation scenes
Bird's eye view      → Overhead view, grand scenes
```

### Style Control

Kling responds well to these style keywords:

```
cinematic, film noir, anime style, watercolor painting,
oil painting, photorealistic, vintage film, documentary,
music video style, fashion editorial, slow motion
```

## Common Pitfalls

1. **std mode has no sound**: Sound requires pro mode
2. **Don't mix contradictory styles**: e.g., "realistic anime style"
3. **Don't describe desired elements in negative_prompt**: Negative prompt is for exclusion only
4. **Character count**: More than 2 characters tends to cause confusion — limit to 1-2 people
5. **Text generation**: On-screen text is unreliable — avoid requesting text in prompts

## Example Prompts

### Character Close-up + Sound (5s, pro, T2V)

```
prompt: "Close-up portrait shot of a young woman sitting by a rainy window. She slowly lifts a cup of coffee to her lips, steam rising from the cup. Rain droplets streak down the glass behind her. Warm interior lighting contrasts with the cool blue exterior. Intimate, contemplative mood. Cinematic shallow depth of field."

negative_prompt: "blurry, distorted face, extra fingers, low quality, watermark"

mode: pro, enable_sound: true  → Automatically generates rain and indoor ambient sounds
```

### Dynamic Scene (10s, I2V)

```
prompt: "Medium shot, a martial artist in traditional white robes performs slow tai chi movements in a misty bamboo forest at dawn. The camera slowly orbits around him as morning light filters through the bamboo canopy. Leaves gently fall around him. Serene, meditative atmosphere. Cinematic, anamorphic lens flare."

negative_prompt: "fast motion, blurry, distorted body, modern clothing"
```

### Natural Landscape + Sound (10s, pro, T2V)

```
prompt: "Establishing wide shot of a volcanic coastline at sunset. Waves crash against black lava rocks, sending spray into the golden light. The camera slowly pushes forward toward the horizon. Dramatic clouds streak across the sky. Epic, cinematic scale, National Geographic quality, HDR lighting."

negative_prompt: "people, text, watermark, low resolution"

mode: pro, enable_sound: true  → Ocean waves and wind sounds
```

### Emotional Performance (5s, I2V)

```
prompt: "Close-up shot, a man receives an unexpected phone call. His expression transitions from surprise to overwhelming joy as tears well up in his eyes. He covers his mouth with one hand. Soft natural light from a nearby window. Shallow depth of field, intimate documentary style."

negative_prompt: "exaggerated expression, cartoon, anime, blurry"
```
