# Perplexity Research Framework — TikTok Niche Validation

> **Condensed 4-phase methodology** for validating anonymous faceless TikTok niches
> before committing content production. Created 2026-07-15 from real session output.
> Use as pre-flight checklist before firing the design-assistant pipeline.
>
> **🔄 Companion skill:** For the **full version** with 13 individual prompt-files
> (each with trigger checklist, data-input guide, pitfalls, and output-integration
> per phase), load `perplexity-followup-plan` from the skill library.
> This file is the TL;DR; the companion skill is the full reference library
> with step-by-step runbook, anti-pattern checklists, and 6-month timing guide.

## When to use this

- Before committing to a new niche (invest 1–2h of research, save weeks of wrong-direction content)
- When the 14-day test data is inconclusive (use Phase 2–3 patterns to diagnose)
- Before scaling from test to full launch (Phase 4 competitive audit)
- Whenever Basti says "schreibe mir einen prompt für perplexity" or "folge fragen plan"

## Phase A — Market Discovery (pre-niche, 1 run)

Goal: Find 15–20 candidate niches, narrow to top 3.

Research prompt template (adapt bold terms, keep structure):

```
You are a viral-content strategist and anonymous TikTok micro-CEO advisor.
Research the best niches for a faceless, German-language TikTok business selling
€10-40 digital PDFs via profile-link funnel.

FILTERS — must meet ALL:
- No face/voice required (text-overlay carousel format only)
- High CPM AND/OR high Save-Rate
- DACH audience large enough to reach 10k followers in 6 months
- Compliance-safe (no BaFin, no medical claims, no legal advice)
- Not saturated by mega-influencers
- Can be sold as €10-40 PDF (checklists, templates, swipe-files)

For each of 15-20 niches deliver:
| Niche (DE) | Format that wins | Est. CPM (€) | Save-Rate potential | Top 3 faceless @handles | 5 sample Card-1 hooks (DE) | Suggested product | Compliance flag | Est. time-to-1k followers |

END WITH: top-3 recommendations ranked by (a) probability of 10k followers in 6 months,
(b) best Save-Rate × CPM product value, (c) fit with existing @finanzfreiraum and @fokusfabrik.
```

### Phase A follow-ups (parallel)

| Run | Question | Wann |
|---|---|---|
| A1 | White-space audit of top-5 candidates from master — TikTok search volume, Reddit demand, Digistore24 supply, Google Trends DE. Score 1-10. | Directly after master |
| A2 | Visual trend audit 2026 Q2-Q3: top 10 color combos, font pairings, dark-vs-light data, the "AI-feel" avoidance pattern. | Parallel to A1 |
| A3 | German algorithm-safety wordlist: banned words (commercial intent), boost words (organic reach), neutral hashtags. "Mehr in meinem Profil" vs "Link in Bio" evidence. | Before first upload |

## Phase B — During-Test Diagnosis (days 1–14)

Goal: Read real performance data and correct course mid-test.

### B1 — Halftime Hook Audit (day 5–7)
Trigger: 5+ posts per account with real views.

```
Here is my actual 7-day data from 2 faceless German TikTok accounts:
[table: post_title | views_24h | likes | saves | completion%]

ANALYZE:
1. Which specific Card-1 hooks are working best? (which psychology pattern?)
2. Which topics within each niche overperform?
3. Clear niche winner yet?
4. What should change in posts 8-14?
5. Any German phrases correlating with high Save-Rate?
```

### B2 — Save-Rate Diagnosis (day 7–10)
Trigger: Views present but Save-Rate flat (0.5–1%).

```
Save-Rate is flat at ~0.5-1% despite 500-2000 views. Diagnose:
1. What does Save-Rate signal in TikTok's algorithm? (intent vs preference)
2. Which carousel arcs correlate with >3% Save-Rate?
3. Is my card-7 pitch card killing saves? Should pitch go to bio?
4. Give me 3 A/B-test variations for Card 1 + Card 7 to unlock saves.
```

### B3 — Comment Mining (day 8+)
Trigger: Comments arriving.

```
30 actual comments below. MINE for:
1. Top 5 questions → product idea gold
2. Pain points → missed sub-niche angles
3. Emotional language → amplify in next 10 posts
4. Negative objections → address in Cards 2-6
5. "wo finde ich das?" signals → product interest

[paste 30+ comments]
```

## Phase C — Post-Test Decision (day 14+)

Goal: Data-driven kill / double-down / pivot decision.

### C1 — Decision Framework

```
14-day data in:
Account A: [total views | avg views | total saves | save-rate | follower delta]
Account B: [same]

Score each option on follower-projection (6mo), revenue (mo3), time-cost/week, risk:
(A) Double down on winner
(B) Kill both, pivot to new niche from Phase-A research
(C) Hybrid angle (e.g. "Finanzen für Selbstständige" crossover)
(D) Run both parallel for 30 more days

Give me a concrete 30-day rollout plan for recommended option.
```

### C2 — Winning Post Forensics (day 14–16)
Trigger: After decision.

```
My 3 best posts (full card text below). Reverse-engineer:
1. Which psychology pattern fires? (loss-aversion, curiosity, social-proof, FOMO)
2. Card 1→2 transition: what creates the swipe-pull?
3. Which specific card triggers saves?
4. How to make 20 more posts on this exact pattern?
5. What's the "fingerprint" to apply to ALL future posts?

Output: reusable post-template (Hook → Arc → Pitch) to hand to ChatGPT.
```

## Phase D — Scale (months 2–6)

### D1 — Content Multiplication
```
Need 10× content without burnout.
1. Generate 30 posts/week from 1 template without fatigue?
2. 7 sub-topic clusters to rotate for 6 months?
3. UGC hack: recycle comments/DMs into posts?
4. Trend-jacking without face (audio-only carousels)?
5. Evergreen vs trending ratio?
6. Min-viable weekly workflow for 14 posts in 1-2 days?
```

### D2 — Monetization Deep-Dive
Trigger: 5k+ followers, Save-Rate >2% stable.

```
1. Profile-to-PDF conversion benchmark (€10-40, DACH, faceless)?
2. 5 bio formulas that drive visits without "Link in Bio" penalty?
3. Pricing strategy: €9.90 impulse vs €29 anchor?
4. Product bundle timing for 2nd product?
5. Email-list vs direct PDF cannibalization?
6. Digistore24 vs FunnelCockpit vs custom — 2026 conversion data?
```

### D3 — Cross-Niche Pivot
```
Main account at X followers. Launch account #2.
1. Which niches share the audience but don't cannibalize?
2. Which use the SAME content template (no re-learning)?
3. Which are 2026 rising (TikTok Creative Center) but not saturated?
4. One account (mixed topics) vs two accounts (focused)? TikTok audience-graph penalty data?
```

### D4 — Risk Audit pre-Scale
Trigger: 10k+ followers, €500+/mo.

```
Scale-risk audit:
1. TikTok dependency: ban / algorithm change / faceless crackdown hedge?
2. Single-platform → IG Reels + YT Shorts? Cost vs benefit.
3. German law: at what revenue -> Gewerbe? Impressum? Datenschutz?
4. Structure: Selbstständig vs Gewerbe vs Kleinunternehmer at €500-2000/mo?
5. Burnout: sustainable 12-month calendar for a solo faceless operator?
6. Reference: 3 German faceless operators 0→€5k/mo — biggest mistakes months 6-12.
```

## Decision-Trigger Quick Reference

```
┌──────────────────────────────────────────────────────────────┐
│ Wann             │ Phase │ Use this                          │
├──────────────────────────────────────────────────────────────┤
│ Neue Nische?    │ A     │ Master prompt + A1/A2/A3 parallel  │
│ Tag 5-7 Test    │ B1    │ Halftime hook audit with real data │
│ Tag 7-10 flach  │ B2    │ Save-rate diagnosis                │
│ Comments da     │ B3    │ Comment mining → product ideas     │
│ Tag 14          │ C1    │ Kill-vs-double-down decision       │
│ Nische chosen   │ C2    │ Winning post perfect-reverse       │
│ Stabil läuft    │ D1    │ Content multiplication blueprint   │
│ 5k+ Followers   │ D2    │ Monetization deep-dive             │
│ Ready for Acc#2 │ D3    │ Cross-niche pivot                  │
│ €500+/mo        │ D4    │ Risk audit before quitting job     │
└──────────────────────────────────────────────────────────────┘
```

## Key Principle

External research is a **pre-flight check**, not a strategy. Each Perplexity run should produce exactly ONE actionable output (a niche decision, a hook change, a product idea) that you implement within 24 hours. If a research session generates insight but no action within a day, the research was wasted.