# Style Derivation from Real Reference Tracks

> **Added:** 2026-07-04 · **Reason:** Cyberpunk OST deliverable showed that measuring real tracks with ffprobe produces dramatically better Suno-style matches than vibes-based guesses.

## What this is

Companion technique for `songwriting-and-ai-music` (which is bundled-protected and cannot be patched). Use whenever a user asks for "tracks in the style of X" and you have access to X's actual audio.

## The technique

When the user asks for "tracks in the style of X" and you have access to X's actual audio (soundtrack, album, user's own folder), derive the Suno/HeartMuLa Style field from **measured properties of real tracks** instead of guessing from vibes.

### What to measure (ffmpeg/ffprobe)

```bash
# Per-track metadata (duration, sample rate, bitrate)
ffprobe -v quiet -print_format json -show_format -show_streams "track.mp3" \
  | jq '.format.duration, .streams[0].sample_rate, .streams[0].bit_rate'

# Loudness (LUFS-ish)
ffmpeg -i "track.mp3" -af "ebur128=peak=true" -f null - 2>&1 \
  | grep -E "(Integrated loudness|Loudness range|Peak)"

# Spectral centroid (rough tonality — low = dark, high = bright)
ffmpeg -i "track.mp3" -af "astats=metadata=1:reset=2,ametadata=mode=print:key=fft_centroid" -f null -
```

### What to extract (and what to write into the Style field)

| Measurement | Suno Style-Field write-up |
|---|---|
| Duration range across album (e.g. 154–335s) | Target duration, plus loop-extension strategy if shorter than user wants |
| Sample rate + bitrate (44.1kHz/320kbps) | "Analog warmth, master-grade production" |
| Integrated loudness / peak (-0.0 dBFS) | "Wide dynamic range, vinyl-style mastering with subtle saturation" |
| Spectral centroid | Bright → "shimmer, glassy high-end" / Dark → "low staccato, sub-bass" |
| Track-name vibe | Mood derivation: "Extraction Action" → aggressive; "Cloudy Day" → melancholic |

### 5-track deliverable workflow

1. `ls` the soundtrack folder, get all track names + durations.
2. ffprobe 3–5 representative tracks (fastest, slowest, action-y, atmospheric, climactic).
3. Build a **Style Anchors table** at the top of the deliverable. Cross-reference each track name → which Suno prompt it inspired.
4. Pick a **continuity key** (e.g. all tracks in Dm/Cm/Am/Fm family → seamless crossfade).
5. Plan a **tempo arc** if it's a set/playlist (slow intro → mid-tempo → climactic finale).
6. Write each prompt's Style field with measurements baked in ("95 BPM in D minor", "320kbps analog warmth", "wet floor reflections").

### Loop-extension strategy for >4-min targets

Most generative music tools cap single-clip length (~4 min for Suno). To reach 5+ min per track:

1. Generate initial 3–4 min clip.
2. Click "Continue / Extend" in the provider's UI.
3. **Re-paste the SAME Style-Field text** (provider carries audio context; style re-injection prevents drift).
4. Repeat until target duration hit.
5. Trim/loop in DAW with crossfade to intro phrase for seamless extension.

`bb` Style-Field **end-phrase directives** like "end phrase identical to opening" keep multi-segment outputs coherent.

## Reference deliverable

**`/home/bratan/cyberpunk-suno-prompts.md`** (Basti, 2026-07-04) — 5-track × 5-min Cyberpunk 2077-style set, derived from real OST analysis at `/mnt/DATA/Programme/Steam/steamapps/music/Cyberpunk 2077 Bonus Content/soundtrack/`. Use as the canonical example of this technique in action.

## When NOT to use

- User wants total creative freedom / no reference at all.
- Reference folder is restricted / unreadable.
- User wants humor or absurd experimental style (then vibes-rule).
