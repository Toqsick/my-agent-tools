# Veo3 Video Generation - Prompting Guide

## Model Overview

| Attribute | Value |
|-----------|-------|
| Tool Name | `veo3_video_generation` |
| Duration | 8s (fixed) |
| Resolution | 720p, 1080p |
| Aspect Ratio | 16:9, 9:16 |
| Input Modes | T2V, I2V (first/last frame) |
| Special Features | **Built-in audio generation** (dialogue, ambient sound, sound effects), first frame + last frame transitions |

## Core Principles

### 1. Five-Section Prompt Structure

Veo3 responds best to the following five-section structure:

```
[Cinematography/Camera] + [Subject description] + [Action/Behavior] + [Scene/Environment] + [Style and Atmosphere]
```

Each section flows naturally into the next, forming a smooth descriptive passage.

### 2. Audio Is the Core Advantage

Veo3 **automatically generates audio that matches the visuals**, including:
- Dialogue and voices (write dialogue directly in the prompt)
- Ambient sound effects (wind, footsteps, city noise)
- Emotional music (atmospheric music, background score)

**Dialogue format**: Describe what characters say in natural language:

```
A woman turns to the camera and says "I've been waiting for this moment."
```

Or use quotation marks to indicate dialogue:

```
Two friends sitting at a cafe, one says "Did you hear about the news?" and the other responds with a surprised expression "No way, tell me everything."
```

### 3. First Frame + Last Frame Transitions

Veo3 supports specifying both first and last frame images simultaneously — the model will automatically generate a transition animation between the two frames. Ideal for:
- Time lapse (day → night)
- Seasonal changes (spring → winter)
- Aging effects
- Scene transitions

### 4. Fixed 8-Second Duration

All Veo3 videos are 8 seconds. Plan content complexity accordingly:
- 1-2 main actions/events
- 1 camera movement
- Suitable for a single plot point or atmospheric segment

## Best Practices

### Leverage Audio Fully

Veo3's biggest differentiator is audio. Actively describe sounds in your prompt:

```
✓ "The sound of rain pattering on the window, a piano melody plays softly in the background"
✓ "Birds chirping in the morning, leaves rustling in the gentle breeze"
✓ "The bustling noise of a Tokyo street market, vendors calling out prices"

✗ Don't assume the model will automatically generate the sound you want — be explicit
```

### Cinematography Terms

Veo3 has excellent understanding of professional cinematography terminology:

```
Anamorphic lens        → Widescreen anamorphic lens
Rack focus             → Shifting focus between subjects
Dutch angle            → Tilted composition
Steadicam              → Stabilized tracking shot
Whip pan               → Fast pan
Pull focus             → Pulling focus
Depth of field f/1.4   → Shallow depth of field
35mm / 50mm / 85mm     → Lens focal lengths
```

### Dialogue Scenes

Veo3 is the only model that can reliably generate dialogue — take full advantage:

```
A documentary-style interview. A weathered fisherman sits on his boat at golden hour,
looking directly at the camera. He speaks with a gravelly voice: "The sea doesn't care
about your plans. You either learn her rhythm, or she teaches you the hard way."
Waves lap gently against the hull. Shot on 16mm film, warm color grading.
```

### Excluding Unwanted Elements

Veo3 has no negative_prompt parameter. Exclude elements by **describing the desired state**:

```
✗ "no people in the scene"
✓ "an empty, deserted street with no pedestrians visible"

✗ "no text or watermark"
✓ "clean frame, pure cinematic imagery"
```

## Common Pitfalls

1. **Duration is not adjustable**: Fixed at 8s — don't try to specify "10 second clip" in the prompt
2. **Don't neglect audio description**: No audio description = random audio that may not match expectations
3. **Don't overload**: Don't cram too much plot into 8s
4. **Character consistency**: Characters may swap features in multi-person scenes — limit to 1-2 people
5. **Text rendering**: On-screen text is unreliable

## Example Prompts

### Cinematic Dialogue (8s, T2V)

```
Medium shot, a detective in a dark trench coat stands in a dimly lit alley. Rain pours down around him. He takes a long drag from a cigarette, the ember glowing orange, then exhales slowly and says in a low voice: "She was already gone by the time I got there." Noir lighting with harsh shadows from a single streetlamp. The sound of rain and distant sirens. Shot on 35mm film, desaturated color palette, neo-noir style.
```

### Nature Documentary (8s, I2V first frame)

```
Extreme close-up macro shot of a monarch butterfly emerging from its chrysalis. The wings slowly unfurl, revealing vibrant orange and black patterns still glistening with moisture. Soft morning light illuminates translucent wing membranes. The subtle sound of the membrane stretching and the ambient forest soundscape with distant bird calls. National Geographic quality, shallow depth of field, awe-inspiring nature documentary.
```

### First Frame → Last Frame Transition (8s, first + last frame)

```
Time-lapse transition of a city intersection. The scene smoothly transforms from a bustling daytime rush hour with honking cars and pedestrians crossing, to a quiet midnight scene with empty streets reflecting neon signs. Street lights flicker on as the sky transitions through sunset colors to deep blue. The audio shifts from chaotic city noise to serene nighttime ambiance with distant music from a bar.
```

### Vertical Short Video (8s, 9:16)

```
Vertical format, POV shot of hands opening an old wooden jewelry box. Inside, a golden locket catches the light. Fingers carefully lift the locket and open it, revealing a faded black-and-white photograph inside. A soft gasp is heard. Warm, intimate lighting from a bedside lamp. The gentle creak of the box hinge and a nostalgic music box melody begins to play. Vintage, sentimental, ASMR-quality close-up.
```
