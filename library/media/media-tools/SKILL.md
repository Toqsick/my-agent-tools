---
name: media-tools
description: "Use when user asks for YouTube transcripts, media-to-summary conversion, transcript-based blog/thread generation. NOT for video editing or non-media content. Media content tools — YouTube transcripts to summaries/threads/blogs."
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - media
    - youtube
    - gif
    - audio
    - music
    - songsee
    - heartmula
lane: worker-vision
reasoning_effort: xhigh
trigger_keywords: ['media', 'youtube', 'transcripts', 'content', 'user']
keywords: ['media', 'youtube', 'transcripts', 'content', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['youtube-creator', 'youtube-to-course-repo', 'youtube-content']
---


# Media Tools

Covers: YouTube transcripts, GIF search, audio analysis, music generation.

## YouTube Content
```bash

set -euo pipefail
# Get transcript
yt-dlp --write-auto-sub --sub-lang en --skip-download "URL"
# Convert to summary, thread, blog post
```

### Transcript Polishing (optional pre-processing)

Raw ASR transcripts systematically mangle proper names (tool names, platform names, technical terms). Before formatting the transcript into a summary/thread/blog, run a **proper-name correction pass** if the transcript will be used for quality-sensitive output:

1. Extract ground truth from the video description (every tool, platform, named entity).
2. Run targeted regex replacements in multiple passes.
3. Handle semantic disambiguation: "Cloud Code" → "Claude Code" vs "in der Cloud" → keep.
4. Track ambiguous terms in an "UNSICHER" section rather than guessing.
5. Verify statistically (count remaining occurrences of each mangled term in context).

**Full technique with workflow, examples, and verification snippets:** `references/transcript-polishing.md`

## GIF Search (Tenor)
```bash

set -euo pipefail
curl "https://tenor.googleapis.com/v2/search?q=cat&key=$KEY&limit=10"
```

## Audio Analysis (Songsee)
```bash

set -euo pipefail
# Spectrograms, mel, chroma, MFCC
songsee spectrogram audio.wav
songsee features audio.wav
```

## Music Generation
```bash

set -euo pipefail
# HeartMuLa (Suno-like)
# See references/heartmula.md

# Suno AI prompts
# See references/songwriting.md
```
