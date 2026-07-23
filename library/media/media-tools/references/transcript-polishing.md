# Transcript Polishing — Proper Name Correction

## When to use

Raw YouTube auto-transcripts (ASR) systematically mangle proper names — especially tool names, platform names, and technical terms. This reference covers the **proper-name correction pass**: cleaning a transcript while respecting actual semantic context.

## Prerequisites

- **Raw transcript** (text, with or without timestamps)
- **Video description / metadata** — this is your **ground truth** for proper names. Extract every tool, platform, technical term, and named entity from it before starting.
- **No LLM calls for correction** — this is a regex-based workflow to stay deterministic and cheap.

## Workflow

### Phase 1: Ground Truth Extraction

Read the video description first. Build a correction table:

| ASR Mangle → | Correct | Notes |
|---|---|---|
| Cloud Code | Claude Code | AI coding agent |
| Cloud Cowork | Claude Cowork | Collaborative coding |
| Gitub/Gitup/Gitab | GitHub | Platform name |
| ChatGT/ChatGBT | ChatGPT | AI chat |
| Hermis | Hermes | Agent framework |
| Superbase | Supabase | Database |
| Perlexity | Perplexity | AI search |
| Slag | Slack | Messaging |
| Zapia | Zapier | Automation |
| Excaly Draw | Excalidraw | Drawing tool |
| Notebook LM | NotebookLM | Note-taking AI |
| Anthopic | Anthropic | AI company |
| Tmax | tmux | Terminal multiplexer |

**Key insight:** ASR errors for proper names are *consistent* — the same word is mangled the same way every time. A single regex covers all occurrences.

### Phase 2: Semantic Disambiguation (Critical)

The hardest case: when a common English word sounds like a proper name in the context.

**Example:** "Cloud" vs "Claude"
- "Cloud Desktop App" → CORRECT (AWS/cloud computing context)
- "Cloud Code" → WRONG → "Claude Code" (Anthropic's product)
- "in der Cloud" → CORRECT (cloud computing)
- "Cloud Nutzung" → needs context: "meine Cloud Nutzung" could mean "Claude-Nutzung" (token stats for Claude)

**Disambiguation rules:**
1. **Confidence markers:** When Cloud is followed by a product name (`Cloud Code`, `Cloud Cowork`, `Cloud Desktop App`), check if the product is in the description's tool list.
2. **Verb context:** If Cloud is the SUBJECT of an action verb (`Cloud sagt`, `Cloud erklärt`, `Cloud kann`, `Cloud nutzt`), it's almost certainly Claude (the AI agent persona).
3. **Location context:** "in der Cloud", "in die Cloud", "aus der Cloud" → cloud computing, leave as-is.
4. **Compound words:** `Cloudnutzung` → ASR artifact, split to "Claude-Nutzung" if context is about Claude usage stats.
5. **Phrase-level patterns:** "in der Cloud Desktop App" → the "in der" phrase signals location (cloud computing context), so "Cloud Desktop App" stays. But "in der Cloud Desktop App öffnen" could mean either — check if the speaker is talking about a desktop app that runs in the cloud or about the Claude Desktop App.

### Phase 3: Pass Structure

Run corrections in **multiple passes**, each with a single focus:

```
Pass 1: Clear, unambiguous replacements (Gitub→GitHub, ChatGT→ChatGPT, Hermis→Hermes)
Pass 2: Context-dependent proper names (Cloud→Claude where appropriate)
Pass 3: Misspellings and ASR artifacts (Claud→Claude, Clotter→Claude)
Pass 4: Compound fixes (ausfühl führen→ausführen, zusammenfest→zusammenfasst)
Pass 5: Single-letter ASR noise (bin CLI Tool→ein CLI Tool)
Pass 6-N: Edge cases found in verification
```

### Phase 4: Verification

After all passes, do a **statistical check**:

```python
import re

with open(file_path) as f:
    text = f.read()

# 1. Count standalone instances of the common-word version
cloud_standalone = len(re.findall(r'\bCloud\b', text))

# 2. Count the proper-name version
claude_count = len(re.findall(r'\bClaude\b', text))

# 3. Verify in context — show each occurrence with surrounding text
for m in re.finditer(r'\bCloud\b', text):
    s = max(0, m.start() - 70)
    e = min(len(text), m.end() + 70)
    print(f"  ...{text[s:e]}...")
```

### Phase 5: Unsicher-Tracking

For ambiguous terms that cannot be resolved deterministically:

```
UNSICHER:
  - <term> (<count>x): possible mappings + why unclear
```

**Never** force a replacement when unsure — flag it explicitly. This gives a human reviewer (or a downstream LLM pass) the chance to decide.

## Common Pitfalls

- **Over-correction:** "Cloud Desktop App" is a real product name from Anthropic. But "in der Cloud" is cloud computing. The boundary depends on whether the speaker is talking about the product or the infrastructure.
- **Compound German words:** `Cloudnutzung`, `Claudenutzung` — ASR often fuses words. Split them before correcting.
- **Substring traps:** `Claud` matches `Claude` with a substring regex. Use `\bClaud\b` (word boundary) to avoid false positives.
- **Proper names that look like typos:** `Steel→Stil` (German for "style"), `TranT→Transcript` — these aren't English names but German context corrections.
- **`agentische Systeme`** — ASR often hears this as `identische Systeme` or `ische Systeme`. Common pattern in AI content.
- **Over-counting in verification:** `\bCloud\b` matches ALL standalone "Cloud" occurrences. After corrections, every remaining instance should be a genuine cloud-computing reference. Scroll through them with context to confirm.

## Automation Tips

1. **Use Python with `re.subn()`** — returns the replacement count so you can track progress.
2. **Write each pass to a new file** (`pass1.txt`, `pass2.txt`, …) so you can diff and roll back.
3. **Count fixes per pass** and report them in the output.
4. **Final verification:** run one last `re.findall()` search for every known ASR error pattern — print 0 matches as confirmation.
