---

name: audio-instructions
description: Use when user asks for audio instructions, Audio Instructions (TTS Walkthrough), When to use this skill, When NOT to use this skill. NOT for video content, music generation. Converts technical step-by-step instructions into TTS audio walkthroughs.
version: 1.0
author: Hermes Agent
license: MIT
trigger_keywords: ['audio', 'instructions', 'skill', 'step', 'user']
keywords: ['audio', 'instructions', 'skill', 'step', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'songsee', 'edge-tts-german-voices']
---

# Audio Instructions (TTS Walkthrough)

## When to use this skill

A user has a **technical step-by-step guide** (installation, setup, troubleshooting, how-to) and wants the **same content available as audio** for an end-user. Typical cases:

- Sending an install guide to a friend who is hands-busy / driving / on-the-go
- Workshop where attendees follow along by listening
- Accessibility: visually impaired user needs the same instructions
- Retention: people often remember spoken walkthroughs better than text
- "Mach das als Audio" / "Hörleitfaden" / "schritt für schritt als audio"

**Distinct from `audiobook` skill:** that one is for narrating prose books with character voices and a 5-phase pipeline. This skill is for **technical content** — single voice, single pass, per-chapter MP3s, no character mapping, no plot structure.

## When NOT to use this skill

- Book or long-form prose narration → use `audiobook` skill
- Single 1-sentence reminder → just use `text_to_speech` directly
- Generated audio is the primary output (music, podcast) → use `heartmula` or `audiobook`

## Workflow (Single-Session)

### Step 1: Inventory the source material

Before generating audio, gather the existing step-by-step content. Sources in priority order:

1. **Existing Markdown manual** (e.g. `DIESE-ANLEITUNG.md`) — split into chapters
2. **Existing skill with steps** — copy the workflow phases
3. **Raw notes** — turn into numbered steps first
4. **Improvise** from session memory — for "no docs exist yet" cases

**Best practice:** Reuse the existing text. Don't rewrite. The same words that read well also narrate well (after a few TTS-isms cleanup).

### Step 2: Plan chapter boundaries

Each chapter = one logical unit of work the listener does. Rules:

- **30-90 seconds per chapter** (60-180 words) — long enough to be useful, short enough to remember
- **1 chapter = 1 user action** (install X, run command Y, click button Z)
- **First chapter = context** ("This is a guide for X, you'll need Y, it takes Z minutes")
- **Last chapter = summary** ("You're done, here's what to do if it doesn't work")
- **5-15 chapters total** for typical install/setup guides

Output: a list of chapter titles, each with a 1-line description of what the user does.

### Step 3: Rewrite each chapter for TTS (TTS-Cleanup)

TTS engines are bad at: code blocks, URLs, markdown formatting, abbreviations, symbols. **Strip all of that** before recording. The output should be read as flowing prose.

**TTS-Cleanup rules:**

| Don't read | Read as |
|---|---|
| `cd ~/projects/foo` | "open a terminal and change to your projects folder" |
| `Bash` | "Bash" or "Bash terminal" |
| `GitHub` | "Git Hub" |
| `--no-sandbox` | "with the no-sandbox flag" |
| `Bottles 64.1 Flatpak` | "Bottles 64.1 from Flatpak" |
| `laut.sh` | "laut dot s h" (spell out dot and dash) |
| Tables | Convert to a sentence: "step 1 does X, step 2 does Y" |
| Numbered lists | Keep, but spell out "step 1" not "1." |
| Currency/prices | Spell out: "thirty-nine ninety-five" or "forty dollars" |
| Acronyms pronounced as letters (API, URL, USB) | "A-P-I", "U-R-L", "U-S-B" |
| Acronyms pronounced as words (Docker, Linux) | "Docker", "Linux" |

**Run the cleanup** mentally once per chapter. Don't over-engineer: if a chapter reads fine as-is, leave it.

### Step 4: Generate TTS

Use the `text_to_speech` tool with explicit `output_path`:

```python
text_to_speech(
    text="<chapter text>",
    output_path="/path/to/audiobook/01-einleitung.mp3"
)
```

**Best practices:**

- **One tool call per chapter.** Serial, not parallel, if TTS provider has rate limits.
- **Use `output_path`** to write directly to a folder (avoids moving files later)
- **Naming convention:** `01-einleitung.mp3`, `02-bottles-installieren.mp3`, ... — zero-padded 2-digit prefix so the playlist sorts naturally
- **Each file should be self-contained** — listener should be able to play chapter 5 without hearing chapters 1-4 (TTS doesn't carry context between calls)
- **Track token usage** — TTS has hard per-call limits (OpenAI = 4096, xAI = 15000, MiniMax = 10000, ElevenLabs = 5k-40k). If a chapter exceeds it, **split the chapter into sub-chapters** rather than truncating

### Step 5: Bundle the deliverable

After all chapters are generated, package them for the end-user:

```bash
# 1. Create a playlist
cat > audiobook/playlist.m3u <<EOF
# <Title> — Audio walkthrough
# Created: <date>
# Duration: <approx total>
# 1 chapter per file, 1 action per chapter

01-einleitung.mp3
02-bottles-installieren.mp3
...
EOF

# 2. Copy the text version alongside (for users who prefer reading)
cp DIESE-ANLEITUNG.md audiobook/ANLEITUNG-LESEFASSUNG.md

# 3. Create a tar.zst (or zip) of the whole audiobook folder
tar -cf - audiobook | zstd -19 -o audiobook.tar.zst
# 281 MB → 51 MB ratio for technical audio
```

For end-user delivery, **also include the text manual** in the same package. Audio without the text means the listener can't copy-paste commands later.

### Step 6: Verify

```bash
# 1. Each MP3 plays
for f in audiobook/*.mp3; do
  ffprobe -show_streams "$f" 2>&1 | grep duration | head -1
done
# → each chapter should be 30-90s

# 2. Playlist is valid
vlc audiobook/playlist.m3u  # or any mp3 player
# → should play chapters in order, no gaps, no duplicates

# 3. Total runtime
echo $(($(find audiobook -name "*.mp3" -exec stat -c%s {} \; | paste -sd+ | bc) / 16000))" seconds"
# → typical install guide: 5-15 min
```

## Chapter-Length Guidelines

| Length | Time | Use when |
|---|---|---|
| Too short (< 20s) | < 50 words | Combine with next chapter or expand |
| Sweet spot | 60-180 words | One concrete action |
| Long (180-400 words) | 1-3 min | Multi-step subtask — split if it has 3+ actions |
| Too long (> 400 words) | > 3 min | Definitely split — listener loses focus |

## TTS-Provider Quirks

| Provider | Best for | Limits | Voice style |
|---|---|---|---|
| OpenAI `tts-1` | English narration | 4096 chars/call | Alloy/Echo/Nova/etc., all sound natural |
| xAI `grok-2-tts` | Fast batches | 15000 chars/call | Single voice, clear |
| MiniMax `speech-2` | Multilingual (incl. German) | 10000 chars/call | Many voice presets, natural prosody |
| ElevenLabs | Highest quality | 5k-40k chars/call (plan-dependent) | Voice-cloning capable |
| Edge TTS | Free, no API key | No hard limit | Many SSML options |

**For German technical content:** MiniMax and Edge TTS handle German umlauts and compound words best. OpenAI can be hit-or-miss with German.

## File-Naming Convention

```
audiobook/
├── 01-einleitung.mp3              # 1st chapter: context
├── 02-schritt-1-beschreibung.mp3  # 2nd chapter: first action
├── ...
├── 11-zusammenfassung.mp3         # last chapter: summary
├── ANLEITUNG-LESEFASSUNG.md       # text version for reference
└── playlist.m3u                   # m3u playlist for easy playback
```

Number prefix = playback order. Descriptive name = user can see what's inside without playing.

## Pitfalls

- ❌ **Long single call > 4096 chars** → OpenAI/minimax will error. Split into smaller chapters, don't truncate mid-sentence
- ❌ **Code blocks in TTS** → TTS reads backtick as "backtick", parens as "open paren". Always pre-process to prose
- ❌ **Same voice for all chapters** is fine for technical guides — this is NOT an audiobook with character voices. Don't add character variation unless explicitly asked
- ❌ **Background music / intro sound** — keep it pure. TTS-only audio. No music. No sound effects. Listener is at the workshop
- ❌ **Don't read the file paths** — "open the file DIESE-ANLEITUNG.md" instead of "open the file at slash home slash user slash D-I-E-S-E-..." 
- ❌ **Forgetting a final chapter** — always have an "Abschluss" / summary chapter that wraps up + gives fallback actions
- ❌ **Assuming user knows the target language** — German user gets German chapters. English user gets English. If unsure, ask before generating (3 options in `clarify`)

## Verification Checklist

- [ ] Each chapter is 30-90s (60-180 words)
- [ ] Each chapter is self-contained (no cross-references to other chapters by name)
- [ ] No code blocks / URLs / markdown formatting in spoken text
- [ ] First chapter is context + tools needed
- [ ] Last chapter is summary + fallback actions
- [ ] Playlist.m3u is valid and sorted
- [ ] Text manual is bundled alongside
- [ ] Total runtime is reasonable (5-15 min for typical install guide)
- [ ] All files played and verified by listening to at least 1 chapter end-to-end

## Integration with `system-documentation`

This skill is the **audio companion** to the `system-documentation` skill. When you finish a technical session and write a Markdown manual, **also offer to generate the audio version** using this skill. The user will often say yes — listening is faster than reading for many people.

## Skills-Linked-Files

- `references/tts-cleanup-rules.md` — Detailed before/after examples for German and English technical content cleanup
- `references/chapter-boundary-rules.md` — When to split a chapter vs. keep combined
- `scripts/chapter-planner.py` — Helper that takes a Markdown manual and proposes chapter boundaries with word counts

## See also

- `audiobook` skill — for prose-book narration with character voices
- `system-documentation` skill — write the source Markdown manual
- `text_to_speech` tool — the underlying TTS primitive
- `hermes-memory` skill — store the user's audio-deliverable preference
</content>
</invoke>