# Official Hilo Video Generation - Prompting Guide

## Model Overview

| Attribute | Value |
|-----------|-------|
| Tool Name | `official_videos_generation` |
| Available Models | Official-Hilo-2.3-Fast, Official-Hilo-2.3, Official-Hilo-02 |
| Duration | 6s or 10s |
| Resolution | 768P, 1080P |
| Input Modes | I2V (first frame, recommended), I2V + last frame, pure T2V |
| Special Features | Background sound effects, automatic prompt optimization, lip sync (via `official_generate_video_based_on_image_and_audio`) |

## Core Principles

### 1. Always Use I2V Mode

**Always prioritize using a first frame image (`first_frame_images`) to drive generation**. Pure text-to-video quality is far inferior to image-to-video.

Workflow: Generate a high-quality first frame with an image model → Then generate video with Hilo.

### 2. Prompt Structure

Hilo prompts should read like **a natural language shot description**, not a keyword dump:

```
[Shot type and movement], [Subject and their action], [Environment details], [Lighting and atmosphere], [Style modifiers]
```

### 3. Automatic Prompt Optimization

`enable_prompt_optimize` is enabled by default — Hilo will automatically expand and optimize your prompt. If you've already written a very precise prompt, you can disable this feature for more precise control.

## Best Practices

### Camera Language

Explicitly specify shot types and camera movements:

| Shot Type | English Expression |
|-----------|-------------------|
| Close-up | Close-up shot, extreme close-up |
| Medium shot | Medium shot, waist-up shot |
| Wide shot | Wide shot, establishing shot |
| Long shot | Long shot, aerial view |
| Tracking | Tracking shot, following shot |
| Push/Pull | Dolly in / dolly out, zoom in / zoom out |
| Pan | Pan left / pan right |
| Crane | Crane shot, tilt up / tilt down |
| Orbit | Orbit shot, 360-degree rotation |
| Handheld | Handheld camera, shaky cam |
| Static | Static shot, locked-off camera |

### Action Description

- Use **progressive tense** for continuous actions: `A woman is walking through...`
- Use **action sequences** for changes: `She turns her head slowly, then breaks into a smile`
- Control action intensity: Only 1-2 actions within 6s, 2-3 actions within 10s
- Avoid overly intense full-body movements (e.g., running, dancing) — they tend to cause distortion

### I2V + Last Frame (Official-Hilo-02 exclusive)

`last_frame_images` is only supported by Hilo-02. Ideal for:
- Scene transitions (day → night)
- Expression changes (calm → smile)
- Object transformations (bud → bloom)

### Background Sound

Setting `enable_background_sound: true` automatically generates ambient sound effects matching the visuals (wind, water flow, city noise, etc.). Suitable for natural scenes that don't need music.

## Common Pitfalls

1. **Don't use negative statements**: The model cannot understand "no people" — describe what you want instead
2. **Don't overload adjectives**: 3-5 style words are enough; too many will conflict
3. **Don't cram too many actions into 6s**: One clear action beats three vague ones
4. **Don't skip the first frame**: Pure T2V quality is unreliable — always provide a first frame
5. **Text content**: The model cannot reliably generate on-screen text

## Example Prompts

### Character Close-up (6s, I2V)

```
Close-up shot, a young woman with long black hair slowly turns her head toward the camera, her expression shifts from contemplative to a gentle smile. Soft golden hour light illuminates her face from the side. Shallow depth of field, cinematic color grading, film grain.
```

### Aerial Landscape (10s, I2V)

```
Aerial drone shot slowly ascending over a misty mountain valley at dawn. Layers of fog drift between the peaks as the first rays of sunlight paint the ridges gold. The camera gradually tilts down to reveal a winding river below. Epic cinematic scale, 4K quality, nature documentary style.
```

### Scene Transition (6s, I2V + last frame, Hilo-02)

```
Smooth transition, the scene gradually shifts from warm afternoon light to cool blue twilight. Cherry blossom petals drift through the air as the lighting changes. The woman's silhouette remains centered in frame. Dreamy, ethereal atmosphere, soft focus background.
```

### Dynamic Action (10s, I2V)

```
Medium tracking shot, a street musician plays acoustic guitar on a rain-soaked city sidewalk at night. Neon reflections shimmer in puddles around his feet. Pedestrians with umbrellas pass in the background as bokeh lights create a dreamy atmosphere. Camera slowly orbits around the musician. Moody, cinematic, urban night photography style.
```
