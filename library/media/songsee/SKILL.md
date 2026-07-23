---
name: songsee
description: "Use when user asks for audio spectrograms, mel/chroma/MFCC feature extraction via CLI, audio visualization. NOT for music generation or DAW-level audio engineering. Audio spectrograms/features (mel, chroma, MFCC) via CLI."
version: 1.0.0
author: community
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Audio
    - Visualization
    - Spectrogram
    - Music
    - Analysis
    homepage: https://github.com/steipete/songsee
prerequisites:
  commands:
  - songsee
lane: worker-vision
reasoning_effort: xhigh
trigger_keywords: ['audio', 'spectrograms', 'chroma', 'mfcc', 'user']
keywords: ['audio', 'spectrograms', 'chroma', 'mfcc', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'audio-instructions']
---

# songsee

Generate spectrograms and multi-panel audio feature visualizations from audio files.

## Prerequisites

Requires [Go](https://go.dev/doc/install):
```bash

set -euo pipefail
go install github.com/steipete/songsee/cmd/songsee@latest
```

Optional: `ffmpeg` for formats beyond WAV/MP3.

## Quick Start

```bash

set -euo pipefail
# Basic spectrogram
songsee track.mp3

# Save to specific file
songsee track.mp3 -o spectrogram.png

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice (start at 12.5s, 8s duration)
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

## Visualization Types

Use `--viz` with comma-separated values:

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

Multiple `--viz` types render as a grid in a single image.

## Common Flags

| Flag | Description |
|------|-------------|
| `--viz` | Visualization types (comma-separated) |
| `--style` | Color palette: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Output image dimensions |
| `--window` / `--hop` | FFT window and hop size |
| `--min-freq` / `--max-freq` | Frequency range filter |
| `--start` / `--duration` | Time slice of the audio |
| `--format` | Output format: `jpg` or `png` |
| `-o` | Output file path |

## Notes

- WAV and MP3 are decoded natively; other formats require `ffmpeg`
- Output images can be inspected with `vision_analyze` for automated audio analysis
- Useful for comparing audio outputs, debugging synthesis, or documenting audio processing pipelines
