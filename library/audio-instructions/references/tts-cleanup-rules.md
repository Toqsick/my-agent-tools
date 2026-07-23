# TTS-Cleanup Rules (German + English technical content)

Reference examples for cleaning up technical content before TTS generation. This file was written based on the Reckhorn DSP-6 mini audiobook created 2026-07-09 (11 chapters, MiniMax speech-2, German, ~10 min total).

## General principle

**TTS engines read what you give them.** If your Markdown has a code block, TTS will try to read it as words. If it has a URL, TTS will read every character. The job of TTS-Cleanup is to convert technical Markdown into flowing spoken prose that the listener can act on.

## Specific transformations (German)

### Code → prose

| Original | Cleaned (spoken) |
|---|---|
| `cd ~/projects/foo` | "open a terminal and change to your projects folder" |
| `chmod +x install.sh` | "make the install script executable with chmod plus x" |
| `sudo apt install bottles` | "install Bottles via apt with sudo" |
| `tar --zstd -xf bundle.tar.zst` | "extract the bundle archive with tar and zstd" |
| `ls -lh Reckhorn-DSP-6/` | "list the Reckhorn DSP-6 directory contents" |

### Tool/Product names

| Original | Spoken as | Reason |
|---|---|---|
| `Bottles` | "Bottles" | Brand name, no special reading |
| `Flatpak` | "Flatpak" | Brand name |
| `Brave` | "Brave" | Brand name |
| `Wine` | "Wine" | Pronounced like the drink, not "ween" |
| `Reckhorn DSP-6` | "Reckhorn DSP 6" | Spell out numbers |
| `Hermes` | "Hermes" | Greek god, simple |
| `Telegram` | "Telegram" | Brand |
| `Claude` | "Claude" | Brand |
| `HailuoAI` | "Hailuo A-I" or "Hai Luo A I" | Mixed-case Chinese brand |
| `MiniMax` | "MiniMax" or "Z-A-I" | Brand — provider-quirky |
| `SiLabs` | "S-I Labs" or "Silicon Labs" | Mixed |
| `Wine 11.11` | "Wine 11 point 11" | Spell out dot-decimals |

### Acronyms pronounced as letters (use spaced letters)

| Original | Spoken |
|---|---|
| `USB` | "U-S-B" |
| `GPU` | "G-P-U" |
| `API` | "A-P-I" |
| `URL` | "U-R-L" |
| `MFC` | "M-F-C" |
| `X11` | "X 11" or "X-one-one" |
| `DPI` | "D-P-I" |
| `PCI` | "P-C-I" |
| `JSON` | "J-S-O-N" (rare) or "Jason" (typical) |
| `VPN` | "V-P-N" |
| `SID` | "S-I-D" |
| `CAB` | "C-A-B" |

### Acronyms pronounced as words

| Original | Spoken |
|---|---|
| `Docker` | "Docker" |
| `Linux` | "Linux" |
| `Git` | "Git" (rhymes with "it") |
| `Discord` | "Discord" |
| `Telegram` | "Telegram" |
| `Nginx` | "Engine-X" |

### Code-style file references

| Original | Spoken |
|---|---|
| `Reckhorn-DSP-6.exe` | "Reckhorn DSP 6 dot exe" |
| `laut.sh` | "laut dot s h" |
| `~/.bashrc` | "tilde slash dot bashrc" |
| `$HOME` | "dollar sign H-O-M-E" |
| `/dev/ttyUSB0` | "slash dev slash t t y U S B 0" |
| `DIESE-ANLEITUNG.md` | "D-I-E-S-E Anleitung dot m d" |
| `kron4ek-wine-11.11-amd64` | "kron 4 e k dash Wine 11 point 11 dash a m d 64" |

### Numbers and symbols

| Original | Spoken |
|---|---|
| `100%` | "one hundred percent" |
| `1.9 MB` | "1 point 9 megabytes" |
| `$0.05` | "5 cents" or "5 hundredths of a dollar" |
| `5-10 Min` | "5 to 10 minutes" |
| `Bash` | "Bash" (it's a word, not an acronym) |
| `~` | "tilde" (rare) or just omit |
| `=` | "equals" or "is set to" |
| `&` | "and" |
| `&&` | "and then" |
| `\|` | "pipe" |
| `>` | "redirect to" |
| `<` | "input from" |

### Markdown formatting

- `# Heading 1` → Don't read "hash", just say the heading text
- `**bold**` → Just say it with normal emphasis (TTS can't render bold anyway)
- `*italic*` → Same
- `` `code` `` → Spell it out as a code reference (see above)
- `[text](url)` → Read just the text, never the URL
- `![image](path)` → "image" or "screenshot"
- `---` (horizontal rule) → "next section"

### Lists and steps

| Original | Spoken |
|---|---|
| `1. First step` | "Step 1: first step" |
| `- bullet` | "bullet: ..." or just the content |
| `* bullet` | Same |
| `1. Step 1\n2. Step 2` | "Step 1: ... Step 2: ..." (no numbers) |

## German-specific quirks

German TTS engines (MiniMax speech-2, Edge TTS) handle these well. OpenAI sometimes doesn't:

- **Compound words** ("Installations-Anleitung"): TTS can struggle. Break up: "Installations Anleitung" (with space) or "die Anleitung für die Installation"
- **Umlauts (ä, ö, ü, ß)**: TTS reads them correctly with MiniMax, sometimes not with OpenAI
- **Quotation marks**: 'gerade' (English single quotes) is okay; "gerade" (English double) usually reads fine; „gerade" (German low-high) reads correctly
- **Dot-separated abbreviations**: "z.B." reads as "zum Beispiel" in good German TTS, "usw." as "und so weiter"
- **Code blocks in German** (e.g. `cd ~/Projekte`): Same as English, spell out the parts

## Hard limits I hit during Reckhorn audiobook

| Provider | Limit | What happened |
|---|---|---|
| MiniMax speech-2 | 10000 chars per call | Chapter 5 had 12200 chars, had to split into 2 sub-chapters (5a + 5b) |
| MiniMax speech-2 | 30-90s natural pacing | Some chapters came out 25s or 110s, had to add/trim content |
| xdg-open / xdg-mime | URL-scheme registration requires `update-desktop-database` after each edit | Forgot this once, took 10 min to debug |

## Working TTS-Cleanup script (Python snippet)

```python
def clean_for_tts(markdown: str) -> str:
    """Strip code blocks, URLs, and markdown formatting from a chapter."""
    import re
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '[code example omitted]', markdown)
    
    # Replace URLs with placeholder
    text = re.sub(r'https?://[^\s)]+', '[link in original]', text)
    
    # Replace file paths with descriptive
    text = re.sub(r'~/Documents/[\w/.-]+', 'your Documents folder', text)
    text = re.sub(r'/home/\w+/[\w/.-]+', 'the install path', text)
    
    # Remove markdown emphasis
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Spell out bullets
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    
    # Spell out numbers in steps
    text = re.sub(r'^(\d+)\.\s+', r'Step \1: ', text, flags=re.MULTILINE)
    
    return text.strip()
```

## Verification after TTS-Cleanup

```bash
# 1. Word count should be 60-180 per chapter
wc -w chapter_*.md
# 2. No code blocks remain
grep -l '```' chapter_*.md  # should be empty
# 3. No URLs
grep -E 'https?://' chapter_*.md  # should be empty
# 4. Reads as prose when spoken (manual test)
for f in chapter_*.md; do
  echo "=== $f ==="
  cat "$f" | head -5
done
```

## Common errors in TTS output

If you hear any of these, fix the source text:

- "open backtick cd tilde slash..." → Source has `cd ~` — change to "change directory to home"
- "running a sudo apt install" → Wrong reading of `sudo apt install`, should be "install with sudo apt"
- "...Git Hub dot com slash MiniMax-M3..." → URL was kept — remove
- "...enter press enter..." → Source has `\n\n` — convert to "next step" or "press enter"
- "...what is in your dollar sign P-A-T-H..." → Source has `$PATH` — change to "your shell path"

## Best practice: read aloud before generating

**Before you hit the TTS button, read the chapter aloud to yourself.** If you stumble, hesitate, or want to skip a part, the listener will too. Re-write until it flows naturally in spoken German (or English).

## See also

- SKILL.md (chapter-length guidelines, file-naming convention, TTS-provider quirks)
- `scripts/chapter-planner.py` — tool to split a Markdown manual into chapters
</content>
</invoke>