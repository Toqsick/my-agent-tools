---

name: tiktok-design-assistant
description: "Use when user asks for TikTok brand systems, Canva CSV exports, TikTok pitch variants, TikTok creator assets. NOT for YouTube/Instagram assets or full marketing strategy. Generate TikTok brand systems, Canva CSVs, pitch variants."
version: 0.6.0
author: Hermes
metadata:
  hermes:
    tags: [Design, TikTok, Canva, Branding, Content]
license: MIT
trigger_keywords: ['tiktok', 'brand', 'systems', 'canva', 'pitch']
keywords: ['tiktok', 'brand', 'systems', 'canva', 'pitch']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['tiktok-slideshow-design', 'tiktok-business-self-improve']
---
# TikTok Design Assistant

Generates complete design kits for anonymous TikTok content businesses: brand system JSON, Canva bulk-create CSVs with 10-20 ready posts, pitch variants JSON with 20 psychology-typed alternatives per niche, and step-by-step Canva setup instructions. All output is German-language (DACH audience), algorithm-friendly (no "Link in Bio"), and structured for Canva Premium Bulk Create workflow. Captures the four-file pattern proven in `~/10-Projekte/10-active/yuno-anon-tiktok-business/` over multiple 2026-07-15 sessions.

## When to Use

- User asks for a "design assistant", "TikTok design kit", or "content design package"
- User wants a brand system (colors, fonts, voice) for an anonymous content niche
- User requests a Canva bulk-create CSV with 10-20 ready-made slideshow posts
- User needs pitch variants for slide 8 (algorithm-friendly CTA cards)
- User says "build me a complete [niche] content kit" or "make me a design assistant"
- User wants a **single post planned** (thumbnail, music, caption) — distinct from the bulk-create pipeline

## Prerequisites

- Nische defined or brainstorm via Nischen-Prompt from `config/prompts.yaml`
- Zielgruppe described (age, problem, schmerzpunkt)
- Project root expected at `~/10-Projekte/10-active/yuno-anon-tiktok-business/`
- No API keys required (pure content generation, no paid services touched)
- Working example to mirror: `config/design/brand-system-kreditkarten.json`

## How to Run

Invoke from chat with a trigger phrase. The assistant generates or extends four files in the project:

1. `config/design/brand-system-{nische}.json` — colors, fonts, voice, logo direction
2. `data/canva-bulk-create-{nische}.csv` — 10-20 posts with 8-slide structure each
3. `config/design/pitch-variants.json` — 20 psychology-typed pitch variants per niche
4. `docs/design/canva-{nische}-anleitung.md` — step-by-step Canva setup guide

If a file already exists, extend with `patch` rather than overwrite. Use `read_file` first to confirm current state.

## Quick Reference

| Output | Path | Schema anchor |
|---|---|---|
| Brand-JSON | `config/design/brand-system-{nische}.json` | `brand_name_vorschlaege`, `color_palette`, `fonts`, `voice`, `logo_direction`, `konsistenz_regeln` |
| Posts-CSV | `data/canva-bulk-create-{nische}.csv` | Columns: `post_id,card_1_title,card_2,card_3,card_4,card_5,card_6,card_7,pitch,nische,bild_keyword` |
| Pitch-JSON | `config/design/pitch-variants.json` | `niches.{nische}.variants[]` with id/type/text/psychology/best_for/expected_ctr |
| Anleitung-MD | `docs/design/canva-{nische}-anleitung.md` | Phase 1 Template-Build → Phase 2 Bulk Create → Phase 3 Magic Switch |

Validation script: `scripts/validate-design-kit.py <nische>` (Python, CSV-quoting-safe via `csv` module, checks all 4 files, JSON syntax + schema, CSV columns + non-empty pitch, anleitung size + headings). Bash wrapper at `scripts/validate-design-kit.sh` preserves backward-compat.

## Procedure

### 1. Nischen-Discovery (when not provided)

**External research pre-flight — run BEFORE committing to a niche.** Invest 1-2h of Perplexity Deep Research to avoid 2-4 weeks of wrong-direction content. Load `references/perplexity-research-framework.md` for the 4-phase methodology with 13 reusable question templates and decision-trigger cheat-sheet.

Load `prompts.niche` from `config/prompts.yaml`, ask user for candidates, recommend one based on **CPM + Save-Rate + visual repeatability**. Decision criteria: highest Save-Rate (conversion potential) AND template-ability (consistent visual language across 20+ posts).

### 2. Brand-System generieren
JSON with `color_palette` (primary + secondary + accent + neutral_dark + neutral_light + `usage_rules`), `fonts` (headline + body + fallback + `sizes_canva`), `voice` (tone + do/dont + `example_caption`), `logo_direction`, `konsistenz_regeln`. Max 3 colors for primary palette. Recommended pairings: trust niches → Anton + Inter on Navy/Gold, productivity niches → Montserrat Black + IBM Plex Sans on Black/Orange.

### 3. Headlines brainstormen
10-20 post-ideen, each pattern-typed:
- `listen` ("5 X die jeder Y macht")
- `umkehr` ("Du schaffst X nicht weil...")
- `contrarian` ("Stop doing X. Here is what works.")
- `myth-vs-reality` ("X Mythen die dich Y kosten")
- `before-after` ("Wie ich 0 auf 3000 in 4 Monaten")

Each headline ≤12 words, no question marks, German A2-B1 readability, no clickbait.

### 4. Card-Texte generieren
For each headline, produce exactly 7 cards (8th = pitch, handled separately):
- Card 1 = headline in caps (rendered large on darkened background image)
- Cards 2-7 = max 18 words each, single sentence, "Du"-form, active verbs
- Card 8 = pitch from `pitch-variants.json` rotation

### 5. Pitch-Varianten ausarbeiten
20 variants per niche with: `id`, `type` (one of 20 types), `text`, `psychology`, `best_for`, `expected_ctr`. Type catalog: `direct-offer, loss-aversion, curiosity-question, social-proof, fomo-quantified, shortcut, revelation, question-empathy, milestone, problem-solution, contrast, specificity, time-saving, anti-status-quo, identity, concrete-list, personal-story, objection-handler, urgency-soft, free-value`. Always use "Mehr in meinem Profil" or approved variants — NEVER "Link in Bio" / "Swipe up" / "Klick hier".

### 6. CSV kompilieren
Columns EXACTLY: `post_id,card_1_title,card_2,card_3,card_4,card_5,card_6,card_7,pitch,nische,bild_keyword`
- UTF-8 encoding required
- Replace umlauts in card text (ae/oe/ue/ss) to avoid encoding issues in some Canva versions
- **Pitch column MUST NOT be empty** — Canva bulk-create silently skips slide 8 if empty (verified bug 2026-07-15)
- Default pitch: `Mehr in meinem Profil`, rotate per-post from pitch-variants.json

### 7. Anleitungs-Markdown
Three-phase structure: Phase 1 = Master-Template-Build (15-20 Min, once), Phase 2 = Bulk Create with CSV (5-10 Min), Phase 3 = Magic Switch + Schedule. Include Canva-Font-Availability (Anton, Montserrat Black, Inter, IBM Plex Sans sind Free). Reference-Doc: `docs/design/canva-master-template-anleitung.md` (universal version).

### 8. Output-Validation
Invoke the Python validation script via `terminal` tool (CSV-quoting-safe, schema-checking):
```bash
python3 ~/.hermes/skills/creative/tiktok-design-assistant/scripts/validate-design-kit.py {nische}
# OR backward-compat:
bash ~/.hermes/skills/creative/tiktok-design-assistant/scripts/validate-design-kit.sh {nische}
```
Confirms: 4 files exist, JSON syntax valid + schema-required fields present, CSV has 11 columns + ≥10 data rows + no empty pitch cells + consistent row widths, anleitung has ≥500 bytes + markdown headings, encoding is ASCII (Umlauts correctly replaced).

### 9. Test-Driven Polish Workflow (Basti-Preferred)

Basti's preferred approach for iterating on this skill or its validator:

**Phase 1 — Test before you fix**
Load the edge-case matrix (`references/edge-case-test-matrix.md`) and run ALL 30 self-tests first. If any fail, you are regression-testing, not bug-hunting — fix the failure and understand why it changed before adding new features. If all 30 pass, you are ready for exploration.

**Phase 2 — Hunt for new edge-cases**
Three directed search vectors, in order:
1. **Echte Daten angreifen** — Validator auf reale Nischen-CSVs laufen lassen. Echte Bugs sind wertvoller als hypothetische. (D9 entdeckte 23 kaputte Posts durch diesen Step.)
2. **Format-Grenzen** — Was passiert mit LATIN-1, CRLF, BOM, quoted fields, multi-line? (D1-D6 decken diese ab.)
3. **Schema-Asymmetrien** — Was prüft Validator auf einem File aber nicht auf einem anderen? (D3 + D9c: Pitch-Schema-Drift fehlte, Brand-JSON hatte es.)

**Phase 3 — Fix + verify (never fix blind)**
- Finde den Bug im Validator → patchen
- Synthetischen Test bauen der den Bug reproduziert
- Happy-Path gegen echte Daten validieren (0 Regressions)
- Doku in edge-case-matrix + SKILL.md updaten
- Memory mit findings updaten

**Phase 4 — Iteration loop**
"Wenn noch was geht und test" (Basti) = immer noch eine Runde mehr testen, bis du keinen einzigen neuen Edge-Case mehr finden kannst. Drei aufeinanderfolgende erfolglose Runs ohne neue Findings = Abbruchkriterium.

**Prinzip:** Falsche Exit-Codes (0 statt 1) und silent Passing (kein ERROR aber auch kein korrekter Check) sind schlimmer als fehlende Features. Jeder Check muss bei Fehlern Exit 1 liefern — niemals `tail | grep` maskieren lassen.

### 10. Single-Post Content Planning (one-off posts)

When Basti wants a **single post** planned — not a bulk-create kit — use this parallel workflow:

**Step 1 — Format-Frage (4 Optionen):**
| Option | Style | Wann |
|--------|-------|------|
| A) Motion-Graphics | Animierte Text-Overlays + Musik + Bild | Productivity, "3 Tools", Listen |
| B) Screen-Recording | Bildschirmaufnahme + Voiceover | Tutorials, How-To |
| C) Hybrid | Screen + Talking Head | Reviews, Vergleiche |
| D) Talking Head | Direkt in Kamera | Persönliche Geschichten, Meinungen |

**Step 2 — Thumbnail via image_generate (FAL FLUX 2 Klein):**
```python
from hermes_tools import image_generate  # not available in skill toolset — call via chat interaction

# Parameter für TikTok-Story (9:16)
image_generate(
    aspect_ratio='portrait',
    prompt='Modern productivity thumbnail for TikTok. Dark gradient background (deep blue to purple). Big bold white text: "3 TOOLS" on top line, "2 HOURS/DAY" in middle (larger, gold/yellow), "FREE" bottom line. ... Neon glow effects, cyberpunk-meets-minimal style. 9:16 vertical. No photos, purely graphic design.'
)
```
**Empfohlener Prompt-Stil:** `[Style] background. [Text-Overlay] bold text. [Color-Scheme] specific palette. 9:16 vertical. No photos, purely graphic design.` — Das Modell (FLUX) rendert Text gut, aber für finale Thumbnails sollte der User das Bild in Canva nachbearbeiten.

**Step 3 — Musik via Pixabay (kostenlos, kein Copyright):**
```bash
# Pixabay Lofi/HipHop-Suche
# https://pixabay.com/music/search/lofi/

# Top-Tracks für Productivity/Vibe-Content:
# - "Chillhop Jazz Coffee Shop" (alex-morgan) → 2:53, entspannt, professionell
# - "LoFi Beats Lofi Study" (APALONBeats) → 2:02, fokussiert, clean
# - "Corporate LoFi Flute Presentation" (alex-morgan) → 3:20, professionell
# - "Good Night - Lofi Cozy Chill Music" (FASSounds) → 2:27 (6.9K plays, beliebt)
# - "LoFi Beats" (MondaMusic) → 1:49, neutral
```
**Regel:** Pixabay-Tracks sind 100% Royalty-free, keine Attribution nötig. Download direkt vom Link, kein Login.

**Step 4 — Caption + Hashtags:**
- Caption: 3-5 Zeilen, bullet-style, aktiv, "Du"-Form. Tools/Gegenstände aufzählen, CTA-Frage am Ende ("Welches nutzt du schon? 👇")
- Hashtags: 10-12 Tags, Mix aus generischen (#produktivität, #tiktoktips) + nischen-spezifischen (#fokusfabrik, #freeapps) + format-bezogenen (#studytok, #arbeitstok)

**Step 5 — Schedule:**
- Beste Upload-Zeiten DE-TikTok: **11:30** oder **19:30** 
- Für Erinnerung: Telegram-Reminder oder Hermes-Cron 15 Min vor Deadline

## Pitfalls

- **Empty pitch column** in CSV → Canva bulk-create skips slide 8 silently. Always fill (verified bug 2026-07-15).
- **Umlauts in CSV** can break Canva import. Replace ä→ae, ö→oe, ü→ue, ß→ss in card text.
- **Card 1 duplicate of caption** is forbidden. Caption (TikTok bio, ≤100 chars) must NOT repeat card_1_title.
- **Brand color >3** dilutes visual identity. Max 2 main + 1 accent.
- **Headline >12 words** doesn't fit Canva titelfolie with image overlay. Trim ruthlessly.
- **Pitch anti-patterns** (algorithm-penalized): NEVER use "Link in Bio", "Swipe up", "Klick hier". Always "Mehr in meinem Profil" or approved variants.
- **Card 7 must NOT contain CTA** — that is card 8's job (separated by intent for swipe-through tracking).
- **Anti-factual claims** in finance/health/legal niches: faktencheck-mandatory via `prompts.factcheck_review` before posting.
- **Subagent prompt length** per Basti preference (2026-07-04): 60-70% of full length, drop redundant explanations, keep only essentials.
- **pitch-variants.json Nischen-Vollständigkeit** (real bug 2026-07-15): `pitch-variants.json` kann Nischen enthalten die keine 20 Variants haben oder komplett fehlen. Vor jedem Kit-Build prüfen: existiert `niches.{nische}` im pitch JSON? Wenn nicht → 20 Variants generieren UND eintragen. Wenn nur 2 von 3 aktiven Nischen da sind (KK + Schulden, kein Produktivität) → die fehlende Nische vor dem CSV-Build ergänzen.
- **Self-Test-Discipline vor Polish-Claim** (v0.1.0 → v0.2.0): Nach jedem Polish-Run alle 16 Edge-Cases testen (siehe `references/edge-case-test-matrix.md`). Kein "das sollte jetzt funktionieren" ohne Testlauf. Happy-Path allein reicht nicht — die 4 gefundenen Bugs in v0.1.0 zeigten sich nur in Edge-Cases.

## Verification

After generation, run via `terminal`:
```bash
python3 ~/.hermes/skills/creative/tiktok-design-assistant/scripts/validate-design-kit.py {nische}
```

Expected output: 4 file-found ✅ + 6 brand-schema ✅ + 3 pitch-schema ✅ + 3 CSV-schema ✅ + anleitung-size ✅ + "Design kit for '{nische}' validated successfully."

Exit code: 0 on full pass, 1 if any check fails (no `tail | grep` masks!).

Manual smoke-test: open the CSV in Canva Bulk Create, map columns to slides 1-8, verify all 10+ posts render with non-empty pitch on slide 8.

### What the Validator Catches (Self-Test Coverage, v0.4.0)

| Failure | Detected | Impact | Edge-Test Date |
|---|---|---|---|
| Missing brand-system JSON | ✅ | Generator skipped step | 2026-07-15 |
| Missing pitch-variants JSON | ✅ | Cannot rotate slide 8 | 2026-07-15 |
| Missing CSV | ✅ | No bulk-create input | 2026-07-15 |
| Missing Anleitung-MD | ✅ | User has no Canva-Guide | 2026-07-15 |
| Brand-JSON missing required fields (color_palette etc.) | ✅ | Schema violation | 2026-07-15 |
| Brand-JSON with unknown fields (forward-compat) | INFO | Schema drift, not failure | 2026-07-15 |
| Pitch-JSON missing target nische | ✅ | Slide 8 cannot resolve | 2026-07-15 |
| Pitch-JSON < 10 variants for nische | ✅ | Insufficient rotation pool | 2026-07-15 |
| Pitch-JSON with unknown nische-level fields | INFO | Schema drift, not failure | 2026-07-15 |
| Pitch-JSON with unknown top-level fields | INFO | Schema drift, not failure | 2026-07-15 |
| Invalid JSON syntax | ✅ | Generator output corrupt | 2026-07-15 |
| CSV < 11 columns | ✅ | Schema-mismatch, Canva import fails | 2026-07-15 |
| CSV with inconsistent row widths (some 10, some 12) | ✅ | Silent data corruption | 2026-07-15 |
| CSV < 10 data rows | ✅ | Below minimum kit-size | 2026-07-15 |
| CSV with 0 data rows (header only) | ✅ | Empty kit | 2026-07-15 |
| Empty pitch cells | ✅ | **Critical**: Canva silently skips slide 8 | 2026-07-15 |
| CSV with quoted fields ("Caption, mit Komma") | ✅ | awk-bug-safe via `csv` module | 2026-07-15 |
| Quoted CSV + empty pitch (combination) | ✅ | Counter accurate | 2026-07-15 |
| Mixed valid+invalid rows (5 OK, 5 empty pitch) | ✅ | Counter accurate | 2026-07-15 |
| Naked umlauts (ä,ö,ü,ß) in CSV | ✅ | Canva-Import unsicher | 2026-07-15 |
| LATIN-1 encoded CSV (Windows-Excel export) | ⚠️ Accepted with INFO | Decode works, naked-umlaut check may miss | 2026-07-15 |
| UTF-8 BOM at file start (Excel-style) | INFO | Auto-stripped, Canva-import-safe | 2026-07-15 |
| CRLF line endings (Windows-style) | ✅ | `csv.reader` handles via `newline=""` | 2026-07-15 |
| Multi-line CSV fields (newline in caption) | ✅ | `csv.reader` handles via `newline=""` | 2026-07-15 |
| Very long CSV lines (10K+ characters) | ✅ | No truncation, no perf issue | 2026-07-15 |
| Large CSV (500 posts, 47KB) | ✅ | <50ms validation | 2026-07-15 |
| Symlinked files | ✅ | `Path.exists()` follows symlinks | 2026-07-15 |
| Concurrent reads (3 parallel processes) | ✅ | Idempotent output | 2026-07-15 |
| Anleitung-MD < 500 bytes or no heading | ✅ | Incomplete guide | 2026-07-15 |
| Anleitung-MD with only whitespace (size trick) | ✅ | Heading-check catches it | 2026-07-15 |

Re-run validator after any edit to a kit file — it is the canonical acceptance gate. Exit code 1 propagates correctly (no shell-pipe masking).

## References

| File | Inhalt |
|---|---|
| `references/edge-case-test-matrix.md` | **v0.4.0 2026-07-15:** Vollständige 30-Check-Test-Matrix mit D-Serie. 4 Bash→Python-Bug-Fixes, 7 D-Serie-Bug-Fixes (davon 2 reale Production-Bugs: Row-Width + Pitch-Schema-Drift), Exit-Code-Reliability, Entscheidungsmatrix für Bash→Python-Migration. Bei jedem Polish-Zyklus nutzen um Regression zu vermeiden. |
| `references/csv-encoding-edge-cases.md` | **2026-07-15:** Alle 13 CSV-Encoding-Edge-Cases dokumentiert (BOM, LATIN-1, Quoted-Fields, Empty-Files, Row-Width-Drift, CRLF, Multi-line). Awk→Python-Migration-Begründung, Detection-Code-Snippet, Pitfalls aus 3 separaten Polish-Runden. Load vor jedem CSV-basierten Import/Validation-Build. |\n| `references/perplexity-research-framework.md` | **2026-07-15:** 4-Phasen Research-Methodik für TikTok-Nischen-Validierung via Perplexity Deep Research. TL;DR-Version — **Companion Skill:** `perplexity-followup-plan` hat die Langfassung mit 13 einzelnen Prompt-Files + Anleitung + 6-Monats-Timing-Guide. Load vor der Nischen-Discovery (Step 1). |
| `references/pixabay-music-guide.md` | **2026-07-17:** Musik-Sourcing-Guide für TikTok-Content: Pixabay-URLs, Track-Empfehlungen pro Vibe (Lofi, HipHop, Corporate), Lizenz-Info (100% Royalty-free), und Integration in den Single-Post-Planning-Workflow. |
