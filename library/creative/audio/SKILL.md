---
name: voice-clone
description: |
  Use when you need to use the audio workflow and its documented procedures.
  NOT for unrelated tasks outside the audio workflow.
  Provides focused guidance for audio.
version: 0.4.5
changelog:
- '0.4.5 (2026-07-03): Initial conversion from MiniMax Hub'
author: Toqsick + Yuno (Hub→Hermes conversion)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    source: minimax-hub
    hub_skill_id: voice-clone
    category: audio
    domain: multimedia
    converted_at: '2026-07-03T23:19:32.986009'
  tags:
  - hub
  - conversion
  - multimodal
triggers:
- voice clone
- clone voice
- 音色克隆
- 声音克隆
- 克隆音色
- 克隆声音
- 复刻音色
- 复刻声音
trigger_keywords: ['audio', 'workflow', 'need', 'documented', 'procedures']
keywords: ['audio', 'workflow', 'need', 'documented', 'procedures']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-workflow', 'hermes-admin', 'multi-agent-pitfalls-cheatsheet']
---



> **Hub Origin:** Convexed from MiniMax Hub skill `voice-clone` (version 0.4.5). Original Hub-SKILL.md is preserved at `scripts-originals/SKILL.md.hub`, original meta.yaml at `scripts-originals/meta.yaml.hub`. All Hub-specific paths (e.g. `~/.hub-global/skills/voice-clone/`) translated to Hermes-equivalent references in `references/`.
# Voice Clone

Clone a voice from reference audio and return a `voice_id` for use with `audios_generation`.

**Language rule**: Always interact with the user in the same language they use. If they speak Chinese, respond in Chinese. If they speak English, respond in English.

## STEP 1: Legal Compliance Confirmation

Before any audio processing, you **must** ask the user to confirm the legal disclaimer. Abort the flow if not confirmed.

Use the exact text below based on user language. **Do not paraphrase or summarize.**

**Chinese (when user speaks Chinese):**
```
question: "音色克隆需要您确认以下声明，请确认后继续:"
options:
  - label: "确认并继续"
    description: "我确认并保证: 1）我拥有该音频的合法使用权并已获得音频中说话人的授权，从而有权继续进行音色克隆操作；2）克隆生成的结果仅用于合法用途"
  - label: "取消"
    description: "我不确定是否有授权，取消操作"
```

**English (when user speaks English):**
```
question: "Voice cloning requires you to confirm the following statement before proceeding:"
options:
  - label: "Confirm and continue"
    description: "I confirm and guarantee: 1) I have the legal right to use this audio and have obtained authorization from the speaker, thereby having the right to proceed with voice cloning; 2) The cloned results will only be used for lawful purposes"
  - label: "Cancel"
    description: "I am not sure if I have authorization, cancel the operation"
```

User selects "Cancel" or replies indicating non-confirmation --> Abort immediately with explanation.

**Cannot be skipped**, even if the user urges speed.

## STEP 2: Audio Metadata Check

Call `audio_meta` to get the reference audio's duration and format.

Checks:
- Format: must be mp3/m4a/wav; other formats require ffmpeg conversion first
- Size: must not exceed 20MB
- Duration: determine if preprocessing is needed (STEP 3)

## STEP 3: Audio Duration Preprocessing

| Condition | Action |
|-----------|--------|
| < 10s | Loop the audio with ffmpeg until >= 10s. E.g. 4s audio looped 3 times = 12s. Command: `ffmpeg -stream_loop 2 -i input.wav -c copy output.wav` |
| 10s - 5min | No processing needed, use as-is |
| > 5min | Use ffmpeg `silencedetect` to find the last silence before 5min, cut at that silence start. If no silence found within 5min, hard-cut at 4min55s with fade-out |

**> 5min trimming flow:**

```bash
# 1. Detect silence (threshold -30dB, min duration 0.5s)
ffmpeg -i input.wav -af silencedetect=noise=-30dB:d=0.5 -f null - 2>&1 | grep silence_start

# 2. Find the last silence_start before 300s (5min)
# 3. Cut at that point
ffmpeg -i input.wav -t <silence_start> -c copy output.wav
```

If no silence detected within 5min:
```bash
# Fade-out at 295s for 5s, total 300s
ffmpeg -i input.wav -t 300 -af "afade=t=out:st=295:d=5" output.wav
```

## STEP 4: Noise Reduction & Volume Normalization

Ask the user separately whether noise reduction and volume normalization are needed:

```
question: "Does the reference audio need noise reduction?"
options:
  - label: "No noise reduction needed"
    description: "The audio is clean speech with no background noise"
  - label: "Yes, apply noise reduction"
    description: "The audio has noise, background music, or other interference"
```

```
question: "Is volume normalization needed?"
options:
  - label: "No"
    description: "The audio volume is normal"
  - label: "Yes, normalize volume"
    description: "The audio is too loud or too quiet, auto-adjust to appropriate level"
```

Set parameters based on user choices:
```
need_noise_reduction: <based on user choice>
need_volume_normalization: <based on user choice>
```

## STEP 5: Language Detection & Demo Text

### 5a. Language Detection

Call `read` to analyze the reference audio's language:

```
file_path: <audio_path>
question: "Identify the language spoken in this audio. Choose the best match from: Chinese, Cantonese, English, Arabic, Russian, Spanish, French, Portuguese, German, Turkish, Dutch, Ukrainian, Vietnamese, Indonesian, Japanese, Italian, Korean, Thai, Polish, Romanian, Greek, Czech, Finnish, Hindi, Bulgarian, Danish, Hebrew, Malay, Persian, Slovak, Swedish, Croatian, Filipino, Hungarian, Norwegian, Slovenian, Catalan, Nynorsk, Tamil, Afrikaans. Reply with the language name only."
```

Confirm the detected language with the user:

```
question: "Detected language: <detected_language>. Please confirm:"
options:
  - label: "<detected_language>"
    description: "Language detection is correct"
  - label: "Incorrect"
    description: "Wrong detection -- type the correct language in the text box below"
```

### 5b. Demo Text

Look up the default demo text for the confirmed language from `references/demo-texts.json` (key = language name).

Confirm demo text with user:

```
question: "A demo audio will be generated after cloning. Please choose the demo text:"
options:
  - label: "Use default demo text"
    description: "<show first 20 chars of demo-texts.json entry for the language>..."
  - label: "Custom demo text"
    description: "Type your own text in the text box below (max 200 chars)"
```

If the demo text language differs from the reference audio language, warn the user it may affect demo quality.

## STEP 6: Execute Clone

Call `voice_clone`:

```
audio_path: <processed_audio_path>
need_noise_reduction: <STEP 4>
need_volume_normalization: <STEP 4>
demo_text: <STEP 5 confirmed demo text>
demo_model: "speech-2.8-hd"
```

### Sensitive Content Check

If `input_sensitive_type` is non-zero:
- Inform the user the reference audio was flagged as risky content (type meanings: 1=severe violation, 2=sexual, 3=advertising, 4=prohibited, 5=abuse, 6=terrorism, 7=other)
- Ask the user whether to continue using the cloned voice

## STEP 7: Post-Clone Metadata Collection

After successful cloning, collect voice metadata:

```
question: "Clone successful! Please name this voice:"
options:
  - label: "Use default name"
    description: "Auto-name as 'Cloned Voice <date>'"
  - label: "Custom name"
    description: "Type your voice name in the text box below"
```

After name confirmation, collect optional info:

```
question: "Would you like to add voice metadata? (optional, feel free to skip)"
options:
  - label: "Skip, finish cloning"
    description: "No additional info needed"
  - label: "Add metadata"
    description: "Add gender, language, voice description tags"
```

User selects "Add metadata" --> collect:
- Gender: Male / Female / Other
- Language: use STEP 5 detected language as default
- Voice description: free text, e.g. "warm deep male voice"

## STEP 8: Return Results

Present the complete clone results to the user:

```
## Voice Clone Complete

- **Voice Name**: <voice_name>
- **Voice ID**: `<voice_id>`
- **Language**: <language>
<if gender> - **Gender**: <gender>
<if description> - **Description**: <description>

### Demo
<if demo_audio> ![Demo](<demo_audio_url>)

### Usage
- Pass `voice_id` to the `voice_id` parameter of `audios_generation` to use this voice
```

## STEP 9: Save to Memory (Optional)

After presenting results, ask the user whether to save this voice for future use:

```
question: "需要记录这个音色吗？记录后在任何项目中都可以通过名称直接调用。"
options:
  - label: "记录音色"
    description: "保存 voice_id，后续可通过音色名称直接使用"
  - label: "不用了"
    description: "仅本次使用，不记录"
```

**English version:**
```
question: "Would you like to save this voice? Once saved, you can use it by name across all projects."
options:
  - label: "Save voice"
    description: "Save voice_id for future use by name"
  - label: "No thanks"
    description: "Use in this session only, don't save"
```

User selects "记录音色" / "Save voice" -->

Use `memory_write` with the following parameters:
- **scope**: `user`
- **name**: `voice-<voice_name>` (kebab-case, e.g. voice name "2" → `voice-2`, voice name "Alice" → `voice-alice`)
- **type**: `reference`
- **description**: 克隆音色"<voice_name>"的 voice_id，来源文件 <source_audio_filename>
- **body**:
```markdown
# 音色：<voice_name>

- **Voice ID**: `<voice_id>`
- **来源音频**: `<source_audio_path>`
- **语言**: <language>
<if gender> - **性别**: <gender>
<if description> - **描述**: <description>
- **克隆日期**: <date>

当用户提到"<voice_name>"时，使用此 voice_id 进行语音生成。
```

User selects "不用了" / "No thanks" --> Skip, finish the flow.

## Anti-patterns

- **Do not skip legal confirmation** -- STEP 1 is mandatory, even if the user says "hurry up"
- **Do not pass > 5min audio directly to voice_clone** -- the API will reject it, must trim first
- **Do not pass < 10s audio directly to voice_clone** -- the API will reject or produce poor quality, must loop first
- **Do not re-clone the same audio in the same task** -- voice_id can be reused within the session
