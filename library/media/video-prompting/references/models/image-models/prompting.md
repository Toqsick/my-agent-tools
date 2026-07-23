# Image Generation Models - Prompting Guide

This guide covers all available image generation models, helping you choose the right model and write optimal prompts.

## Model Selection Quick Reference

| Need | Recommended Model | Tool Name |
|------|-------------------|-----------|
| General text-to-image / image editing | Gemini (default) | `nano_banana_image_generation` |
| Batch image generation | Gemini Batch | `nano_banana_batch_image_generation_v2` |
| Text embedded in images | Qwen Wanxiang | `qwen_image_generation` |
| Style transfer / editing | FLUX Kontext | `kontext_image_generation` |
| Face / character reference | Kling | `kling_omni_image_generation` |
| Creative illustration / Logo / transparent background | OpenAI GPT-Image | `openai_image_generation` |
| Artistic quality | Midjourney | `midjourney_image_generation` |
| Many reference images (up to 14) | Seedream | `seedream_image_generation` |

---

## Gemini (nano_banana)

**Default image model** with the strongest overall capabilities.

### Model Variants

| Variant | Model ID | Features |
|---------|----------|----------|
| nano_banana | gemini-2.5-flash-image | Fast, good for iteration |
| nano_banana_2 | gemini-3-pro-image-preview | High quality |
| nano_banana_2_flash | gemini-3.1-flash-image-preview | Default, balances speed and quality |

### Prompt Style

Natural language descriptions, like talking to an artist:

```
A serene Japanese garden in autumn, with a wooden bridge over a koi pond.
Red and golden maple leaves float on the water surface. Soft morning mist
rises from the pond. Shot in the style of a landscape photograph, natural
lighting, shallow depth of field focusing on the bridge.
```

### Image Editing

Provide reference images via `image_paths`, then describe the desired changes in the prompt:

```
image_paths: [original.jpg]
prompt: "Change the background to a sunset beach scene, keep the person and their pose exactly the same"
```

### Resolution

Supports 1K / 2K / 4K, default 2K. 2K is sufficient for video first frames.

---

## Qwen Wanxiang (qwen)

**Best choice for embedding text in images**. Only supports image editing (reference image required).

### Use Cases

- Adding text titles to images
- Modifying existing text in images
- Poster / cover creation

### Prompt

```
image_paths: [background.jpg]
prompt: "Add the text 'Brightest Star in the Night Sky' in elegant calligraphy style at the center of the image, white text with subtle glow effect"
```

---

## FLUX Kontext (kontext)

**Best choice for style transfer and image editing**.

### Strengths

- Converting photos to specific art styles
- Changing art style while maintaining composition
- Multi-image reference fusion

### Prompt

```
image_paths: [photo.jpg]
prompt: "Transform this photo into Studio Ghibli anime style, maintain the same composition and character pose, soft watercolor textures, warm pastel colors"
```

### Aspect Ratios

Supports a rich set of aspect ratios: 1:1, 16:9, 9:16, 3:2, 2:3, 4:3, 3:4, 4:5, 5:4, 21:9, 7:4, 4:7

---

## Kling (kling)

**Best choice for face and character reference generation**.

### Reference Modes

| Mode | Use Case |
|------|----------|
| `subject` | Preserves overall appearance (clothing, pose, style) |
| `face` | Preserves facial features only (can change outfit, scene) |

### Prompt

```
# Face mode: Keep face, change scene
image_path: face_reference.jpg
reference_type: face
prompt: "A woman in a traditional red qipao standing in a lantern-lit ancient Chinese street at night, full body shot, elegant pose, cinematic lighting"

# Subject mode: Preserve overall appearance
image_path: character_reference.jpg
reference_type: subject
prompt: "The same person standing on a rooftop at sunset, wind blowing through their hair, dramatic sky background, cinematic wide shot"
```

### Batch Generation

`kling_omni_image_generation` supports independent prompt, reference image, reference mode, and aspect ratio for each image.

---

## OpenAI GPT-Image (openai)

**Best choice for creative illustrations, logos, and transparent backgrounds**.

### Special Capabilities

- Transparent background images (ideal for logos, stickers, UI elements)
- Creative concept visualization
- Abstract art

### Prompt

```
prompt: "A minimalist logo of a phoenix rising from flames, clean vector style, bold lines, gradient from deep red to bright gold"
size: "1024x1024"
quality: "high"
```

### Image Editing

```
image_paths: [original.jpg]
prompt: "Remove the background and make it transparent, keep only the main subject"
```

---

## Midjourney (midjourney)

**Best choice for artistic quality and stylization**.

### Version Selection

Append version flag at the end of the prompt:
- `--v 7`: V7 (default), realistic and general purpose
- `--niji 7`: Niji7, anime/manga style

### Core Parameters

| Parameter | Function | Example |
|-----------|----------|---------|
| `--ar` | Aspect ratio | `--ar 16:9` |
| `--sref` | Style reference URL | `--sref https://example.com/style.jpg` |
| `--cref` | Character reference URL | `--cref https://example.com/char.jpg` |
| `--cw` | Character reference weight (0-100) | `--cw 50` |

### Prompt Style

Midjourney favors **concise, evocative descriptions** — no need to be overly verbose:

```
prompt: "ancient samurai meditating under cherry blossoms, moonlit courtyard, atmospheric fog, cinematic lighting, dramatic shadows --ar 16:9 --v 7"
```

### Reference Images

Provide local reference images via `image_paths`:

```
image_paths: [reference.jpg]
prompt: "a warrior in similar armor style standing on a cliff overlooking a vast ocean, epic scale, golden hour --ar 16:9 --v 7"
```

---

## Seedream (seedream)

**Supports the most reference images** — version 4.5 supports up to 14 reference images.

### Model Selection

| Model | Features |
|-------|----------|
| doubao-seedream-4-0-250828 | Standard version |
| doubao-seedream-4-5-251128 | New version, supports up to 14 reference images |

### Ideal Use Cases

- Scenarios requiring many reference images to constrain style
- Multi-character consistency (provide multiple character reference images)
- Complex scene reconstruction

### Prompt

```
image_paths: [ref1.jpg, ref2.jpg, ref3.jpg, ...]
prompt: "A group photo of these characters together in a modern office setting, natural lighting, professional photography style, everyone is smiling and looking at the camera"
```

---

## General Prompting Tips

### 1. Optimizing for Video First Frames

When generating images intended as video first frames:

```
✓ Character's mouth slightly open (helps with lip sync)
✓ Pose suggests motion (e.g., mid-step, mid-turn)
✓ Leave room for motion in the frame (don't push subject to edges)
✓ Avoid extreme perspective (video models struggle to maintain it)
✗ Don't generate overly static "passport photo" compositions
```

### 2. MV First Frame Batch Generation Strategy

```
1. Determine art style → select primary image generation model
2. Use Kling face mode to lock character facial consistency
3. Batch generate first frames for each scene with the selected model
4. Use Kontext to unify style (if inconsistencies exist)
5. After confirmation, send to video model for generation
```

### 3. Style Consistency

Tips for maintaining unified style across a set of images:
- Use the same style keyword suffix
- Use Midjourney `--sref` to lock style
- Use Kling `face` mode to lock character appearance
- Use Kontext with the same style reference image for all images
- In batch generation tools (Gemini batch / Kling batch), use the same style description suffix for each image
