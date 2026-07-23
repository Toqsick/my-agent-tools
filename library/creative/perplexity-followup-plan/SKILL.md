---
name: perplexity-followup-plan
description: |
  Use when converting a broad research goal into phased Perplexity Deep Research prompts, cross-validating claims, or planning evidence-backed follow-up questions.
  NOT for simple questions answerable directly, one-source lookups, or research tasks that do not justify multiple deep-research runs.
  Builds an English-language, four-phase prompt plan whose findings are synthesized into concise German insights and action items.
version: 2.5.0
author: Basti + Yuno (2026-07-16)
license: MIT
agent: Yuno
lane: koenigin
trigger_keywords:
- perplexity
- deep research
- prompt format
- deep research prompt
- folge-frage
- followup
- research prompt
- research workflow
- quellen triage
- 3-stufen evaluierung
- konsens triangulation
- source validation
- arxiv check
- general research
- ai research
- agent orchestration
- multi-agent research
- tech research
- nischen-research
- viral research
- tiktok research
- design research
- marktanalyse
- algorithmus-research
- white space
- save-rate
- halbzeit-check
- pre-research
- url verification
- subagent pre-research
- pre-verified sources
- dual-path
- cross validation
- cross-validate
- tier-1
- hidden gems
- tier-1 picks
keywords:
- perplexity
- deep-research
- prompt-template
- research-workflow
- source-validation
- 3-stage-evaluation
- tiktok
- niche-discovery
- viral-patterns
- design-benchmark
- anonymous-content
- faceless-tiktok
- dach
- save-rate
- algorithmus
related_skills:
- tiktok-design-assistant
- tiktok-business-self-improve
- tiktok-slideshow-design
- self-improving
- orchestration/agent-orchestration-patterns-2026
- orchestration/multi-agent-pitfalls-cheatsheet
- research-tools
- tech-fact-check
- deep-model-evaluation
last_curated: 2026-07-16
curated_by: "Yuno (v2.5.0 — Dual-Path Cross-Validation Strategy: Custom-Aware + Fresh-Prompt parallel, Tier-1/Hidden-Gem/Honorable-Mention Klassifikation, Cross-Validation Matrix Template, Print/Dependency-Phasen-Planning. Validierte auf 2 Perplexity-Runs + 1 Vault-File + Cross-Validation Matrix in Session 2026-07-16)"
routing_hint: 'Trigger wenn Basti "Perplexity-Frage" (egal zu welchem Thema) stellt,
  oder "Research-Prompt zu [TOPIC]", "3-Stufen-Evaluierung", oder "Phase A/B/C/D".
  Liefert sofort den passenden Prompt + Daten-Anforderungen. Für generische
  Research-Prompts: `templates/deep-research-prompt-template.md` kopieren + Variablen
  ersetzen. Für TikTok: existing Phase-A/B/C/D-Struktur. Pair mit tiktok-design-assistant
  für Brand-System-Output, research-tools für Quellen-Verifikation.'
---


# Perplexity Follow-Up Plan — 13 Fragen in 4 Phasen

> Strukturierte Deep-Research-Sequenz für das Yuno-Anon-TikTok-Business.
> Begleitet den 14-Tage-Test (`finanzfreiraum` + `fokusfabrik`) und die Skalierung danach.
> Alle Fragen sind auf **Englisch** verfasst (Perplexity-performt besser), aber jeder Phase-Block hat einen deutschen Wrapper für Trigger + Daten-Anforderungen.

## Wann diesen Skill laden

Trigger wenn Basti:
- "Perplexity-Prompt für TikTok" sagt
- "Folge-Frage A1 / B2 / C1 / D3" o.ä. referenziert (siehe Quick-Reference-Card)
- Nach Daten aus dem 14-Tage-Test fragt → Antwort braucht Phase-B- oder Phase-C-Prompt
- Vor Nischen-Pivot oder Skalierungs-Entscheidung steht
- Algorithmus-Wortliste oder Visual-Trend-Audit braucht

Nicht laden wenn: Eine direkte Chat-Antwort auf TikTok-Business-Frage reicht (kein Research nötig) → normales Wissen reicht.

## Wichtige Konventionen

1. **Prompts IMMER auf Englisch** an Perplexity schicken — performt nachweislich besser, breitere Datenquellen.
2. **Antwort auf Deutsch** an Basti liefern (mit TL;DR + den 3 wichtigsten Insights + Action-Items).
3. **Daten mitgeben wenn relevant**: Perplexity kann nicht raten — Views/Likes/Saves/Comments müssen in den Prompt pastet werden.
4. **Realistische Erwartungen**: Perplexity Deep Research = 2-5 Min pro Run. Phasen A+B+C+D sind NICHT alle an einem Tag sinnvoll.
5. **Validierung**: Perplexity-Antworten immer mit eigenen Daten (TikTok Creative Center, HypeAuditor, Statista) gegenchecken bevor Basti Entscheidungen darauf basiert.

---

## Generic Deep Research Prompt Format

Perplexity Deep Research Prompts folgen einem **wiederholbaren Format**, das für jede Domain funktioniert — nicht nur TikTok. Bewiesen durch 6 M1-M6 Agent-Orchestration-Prompts (siehe `templates/deep-research-prompt-template.md`), die das gleiche Format auf ein komplett anderes Themengebiet anwenden.

### Standard Prompt-Struktur

Jeder Deep-Research-Prompt hat diese 10 Blöcke:

1. **GOAL** — was du wissen willst in 1-3 Absätzen (Domain + Use-Case + Kontext)
2. **AUDIENCE & CONTEXT** — wer du bist, was du baust, dein Stack, deine Limits
3. **⚠️ CUSTOM-STACK-LISTE (Neu 2026-07-16)** — baut auf Block 2 auf, ABER explizit: liste ALLES auf was du SCHON hast (Tools, Library, Configs) + was Perplexity NIEMALS vorschlagen soll (z.B. "Skip spool holders, I have custom versions."). Macht 30-40 % mehr Hidden-Lücken-Empfehlungen, validiert bei 2 A1-Mini-Runs. Ohne diesen Block empfiehlt Perplexity generische Top-Picks die du schon hast.
4. **7-9 DELIVERABLES** — konkrete, nummerierte Items mit spezifischen Fragen
5. **OUTPUT FORMAT** — Länge, ASCII-Diagramme, Code, Citations-Format
6. **HARD CONSTRAINTS** — "2024-2026 sources", "verify arXiv IDs", Domain-Pitfalls
7. **SPECIAL NOTE** — ehrliche Erwartungen, Solo-Dev-Realität, "don't recommend overkill"
8. **3-STUFEN-EVALUIERUNG** (nach jedem Run) — Konsens-Triangulation → Quellen-Triage → Decision-Matrix (+ Optional: 4. Kategorie "MANUELL" bei Creator-Search-nötig)
9. **VORAB-HYPOTHESEN** — was der Session-Owner erwartet (für späteren Vergleich mit Realität)
10. **NEXT TRIGGER** — wann die nächste Phase / der nächste Prompt ansteht

Jeder Prompt endet mit: `"Cite real repos/papers/handles — I will verify."`

### Pre-Research: Subagent URL Verification (Neu 2026-07-16)

Bevor du einen Prompt an Perplexity lieferst, dispatche PARALLELE Subagents für PRE-RESEARCH + URL-VERIFIKATION. Dieses Pattern reduziert Halluzinationen drastisch, halbiert Post-Evaluierungszeit und liefert bessere Ergebnisse. **Validiert auf 3 Topics parallel in 144–158s.**

Das vollständige Pattern + Briefing-Template + Pitfalls + Performance-Notes + Beispiel: [`references/pre-research-subagent-pattern.md`](references/pre-research-subagent-pattern.md)

**Kurzfassung:**

1. **Prompt bauen** (Standard-Template + Custom-Stack-Listing)
2. **Subagent-dispatch** — 1 Subagent pro Topic (parallel), `role=leaf`, mit Briefing aus Pattern-Reference
3. **Verification** — Subagent bestätigt URLs per `web_extract`, markiert `[VERIFIED]`
4. **Konsolidierung** — PRE-VERIFIED SOURCES Block in den Prompt einbauen
5. **Cross-check:** Eigene `web_extract` auf TOP-3-URLs pro Kategorie (Subagent-Claims sind self-reports!)
6. **User feuert** den Prompt in Perplexity
7. **Post-Evaluation** — Perplexity-Antwort gegen PRE-VERIFIED SOURCES differenzieren + 3-Stufen-Evaluierung

**Wann überspringen:** Standard-Recherche zu bereits gut bekannten Topics (TikTok-Nischen-Check, Standard-Brand-Audit) — lade vorheriges `references/pre-research-*.md` als Template statt neu zu dispatchen.

### Dual-Path Cross-Validation Strategy (Neu 2026-07-16)

Nachdem der Pre-Research + Prompt bereit ist: **Feuere ZWEI Perplexity Deep Research Runs parallel** — einen Custom-Aware (mit Kontext + Pre-Verified URLs) und einen Fresh (Clean, ohne Kontext). Dann cross-validiere die Ergebnisse um robuste Tier-1-Picks von kontextabhängigen Hidden-Gems zu trennen.

**Warum:** Ein einzelner Perplexity-Run hat Blind Spots. Der Custom-Aware-Prompt übersieht generische Top-Picks (weil er auf Lücken fokussiert). Der Fresh-Prompt übersieht Nischen-Picks (weil er dein Custom-Wissen nicht hat). Dual-Path fängt beide.

**Das vollständige Runbook + Templates + Klassifikationsregeln + Pitfalls:** [`references/dual-path-cross-validation.md`](references/dual-path-cross-validation.md)

**Kurzfassung:**
1. **Path A (Custom-Aware):** Prompt mit Custom-Stack-Listing + Skip-Liste + allen PRE-VERIFIED SOURCES → findet Lücken
2. **Path B (Fresh):** Gleicher Prompt, OHNE Skip-Liste, OHNE Pre-Verified Sources → findet generische Top-Picks
3. **Cross-Validation Matrix** bauen: Items in BEIDEN Reports = Tier-1 (robust). Items nur in einem = Hidden-Gem (unique fündig, aber prüfen)
4. **RED FLAG Conflicts** erkennen: Wenn Path A empfiehlt und Path B sagt OBSOLETE → Path B hat Recht
5. **Vault-File mergen** mit 4 Sektionen: Tier-1, Hidden-Gems A, Hidden-Gems B, Honorable Mentions

**Wann überspringen:** Quick-Research (<3 Std Print oder <€3 Material) wo eine schnelle Entscheidung reicht.

**Validated:** 2026-07-16 auf A1-Mini-Workshop-STLs. 3 Tier-1 Picks aus 9 Modellen = 33% robust bestätigt. 6 Hidden-Gems gefunden die Single-Path übersehen hätte.

### How to create a generic Perplexity prompt

1. `skill_view('perplexity-followup-plan', 'templates/deep-research-prompt-template.md')` → Template laden
2. **Goal** konkretisieren — was genau soll erforscht werden? (1-3 Absätze)
3. **Audience** — Basti's aktuellen Stack + Use-Case beschreiben (siehe session context)
4. **Deliverables** — 7-9 Items die das Goal aufbrechen, jedes = 1 Output-Abschnitt
5. **Constraints** — Domain-spezifisch formulieren (DACH, GreyScript, Security, etc.)
6. **Evaluation** — 3-Stufen-Workflow aus diesem Skill übernehmen
7. `[PLACEHOLDER]`-Variablen durch echte Werte ersetzen
8. Prompt in Perplexity → Deep Research → warten → Antwort evaluieren

**Konkrete Beispiele:** Die 6 M1-M6 Prompts in `~/.hermes/docus/research-prompts/` zeigen das Format auf 6 Agent-Orchestration-Subdomänen.

### Trigger für generische Perplexity-Prompts

| User sagt | Aktion |
|---|---|
| "Research-Prompt zu [TOPIC]" | Template laden + mit Topic füllen |
| "Perplexity-Frage zu [THEMA]" | Template laden + anpassen |
| "3-Stufen-Evaluierung zu [REPORT]" | Stufe 1-3 anwenden |
| "Deep Research zu [DOMAIN]" | Template laden + Deliverables anpassen |

---

## Phase A — Pre-Launch Research (JETZT)

Diese Prompts starten **parallel zum Master-Prompt** oder direkt danach. Ziel: Lücken füllen die der Master-Prompt nicht abdeckt.

### A1 — Nischen-White-Space-Check

**Trigger:** Nachdem Master-Prompt die Top-15-Nischen geliefert hat
**Wann:** Sofort danach

```text
Given these 5 niches: [paste top 5 from master prompt], check each for "white space" — i.e. demand signals (search volume, rising TikTok hashtags, Reddit threads in r/Finanzen, r/Selbststaendig, r/productivity, etc.) BUT low supply of faceless German accounts in this exact sub-niche.

Use: TikTok Creative Center (Germany filter), Google Trends DE-AT-CH, Reddit search, Amazon DE bestseller lists in matching categories, Digistore24 vendor count.

For each:
- White-space score (1-10)
- 3 sub-niche angles that are UNDERSERVED (e.g. "Kreditkarten für Selbstständige" instead of generic "Kreditkarten")
- First-mover advantage timeline: how long before saturation?
```

**Output:** Top-3-Nischen mit konkretem White-Space-Vorteil + 3 Sub-Niche-Angles pro Gewinner.

### A2 — Visual Trend Audit 2026

**Trigger:** Direkt nach Master-Prompt, parallel zu A1
**Wann:** Parallel

```text
Audit the visual-design trends dominating TikTok in Q2-Q3 2026 specifically for faceless text-overlay carousel accounts. I need:

1. Top 10 color combinations used by accounts with >50k followers in this style
2. Top 5 font pairings (heading + body) that perform on small mobile screens
3. The "dark vs light" debate: what's the 2026 data showing for Save-Rate? Are dark-mode accounts still winning or has light-mode caught up?
4. New design movements I might be missing (e.g. Y2K revival, brutalist, neumorphism, AI-aesthetic)
5. The "AI-feel" problem: how do I avoid my Canva designs looking AI-generated? What human-touches convert best?

Reference real @ handles — I will inspect them.
```

**Output:** Brand-System-Updates für die aktuellen Test-Nischen (`finanzfreiraum` Navy+Gold, `fokusfabrik` Schwarz+Orange) — soll ich was ändern?

### A3 — Algorithmus-Wortliste DE-spezifisch

**Trigger:** Vor dem ersten Upload
**Wann:** ASAP (kann Phase B überschreiben wenn falsche Wörter schon gepostet)

```text
I need a German-language TikTok algorithm-safety audit. Compile:

1. BANNED-WORDS LIST (German): words/phrases that TikTok's 2026 algorithm flags as commercial intent and downranks. Include severity level (shadowban-risk vs reach-limit). Cross-reference with German UWG advertising law where relevant.

2. BOOST-WORDS LIST: phrases that get more reach in organic discovery (curiosity triggers, emotional hooks, save-prompt language).

3. NEUTRAL-BUT-USEFUL: hashtags that don't help but don't hurt vs hashtags that actively boost (German + English mix).

4. The "Mehr in meinem Profil" trick: is this actually safer than "Link in Bio"? Cite the 2026 evidence — TikTok has changed their commercial-language detection multiple times.

5. Case-study accounts: 3 German faceless accounts that got visibly shadowbanned, what they did wrong, what they changed to recover.
```

**Output:** Sofort anwendbare Wortliste für alle Card-1-Hooks in den Bulk-CSVs. Update der `pitch-variants.json` falls problematische Wörter drin sind.

---

## Phase B — During Test (Tag 1-14, daten-getrieben)

Diese Prompts **erst WENN** erste Performance-Daten vorliegen. Vorher raten wir nur.

### B1 — Halbzeit-Hook-Audit

**Trigger:** Sobald 5+ Posts pro Account mit echten Views da sind
**Wann:** Tag 5-7 (passt zum Halbzeit-Check im `14-Tage-Test-Tracking.md`)

```text
Here is my actual 7-day TikTok data from a faceless German test (2 accounts):

ACCOUNT 1 — `@finanzfreiraum` (Kreditkarten):
[paste: post title / views-24h / likes / saves / completion%]

ACCOUNT 2 — `@fokusfabrik` (Produktivität):
[paste same columns]

ANALYZE:
1. Which specific post titles (Card 1 hooks) are working best, and WHY (psychology pattern: loss-aversion? curiosity? listicle?)
2. Which specific topics are outperforming within each niche?
3. Are there signals that ONE niche is clearly winning, or is it still too early?
4. What should I change in posts 8-14 to maximize the winner?
5. Any specific German phrases in the Card-1 text that correlate with high Save-Rate?

Be brutally honest — if neither account is working, say so.
```

**Output:** Top-3-Hook-Patterns die skalierbar sind + konkrete Posts 8-14-Vorschläge.

### B2 — Save-Rate-Diagnose

**Trigger:** Views kommen aber Save-Rate flach (~0.5-1%)
**Wann:** Tag 7-10

```text
My Save-Rate is flat (~0.5-1%) despite getting views (500-2000 per post). The views prove the hook works, but people aren't saving. Diagnose:

1. What does Save-Rate actually signal in TikTok's algorithm? (Intent signal vs preference signal)
2. Which Carousel-Arc types correlate with high Save-Rate (e.g. checklists, swipe-files, step-by-step) vs low Save-Rate (e.g. pure entertainment, storytelling)?
3. For my two niches (Kreditkarten, Produktivität), what SPECIFIC post formats in these niches typically hit >3% Save-Rate? Give me 5 concrete examples in German.
4. Is my Card 7 (the pitch card) killing Save-Rate? Should I move the pitch to bio/profile and keep Card 7 purely value?
5. Quick experiment: give me 3 A/B-test variations of Card 1 + Card 7 that might unlock Save-Rate. I'll test them on posts 9-11.
```

**Output:** Diagnose + 3 konkrete A/B-Test-Varianten für Posts 9-11.

### B3 — Comment-Mining

**Trigger:** Sobald Comments kommen
**Wann:** Tag 8-10

```text
Here are 30 actual comments from my TikTok posts (paste them below):
[COMMENTS]

MINE these for:
1. Top 5 questions people are asking → product-idea gold (each question = a potential PDF)
2. Pain points mentioned → which sub-niche angles am I missing?
3. Emotional language used → which feelings should my next 10 posts amplify?
4. Negative comments / objections → how do I address these in Card 2-6 to remove friction?
5. Profile-visit signals → are comments like "wo finde ich das?" appearing? (means people want the product)

[paste 30+ German comments]
```

**Output:** 5 Product-Ideen direkt aus den Kommentaren + Pain-Point-Liste für nächste Posts.

---

## Phase C — Post-Test Decision (Tag 14+)

Diese Prompts entscheiden die Skalierungs-Strategie.

### C1 — Kill-vs-Double-Down Decision

**Trigger:** Tag 14 erreicht, alle Daten da
**Wann:** 30.07.2026 (Final-Decision-Datum laut Tracking-Sheet)

```text
FINAL 14-day test data:

ACCOUNT A (Kreditkarten):
- Total views / avg views / total likes / total saves / save-rate / follower delta: [NUMBERS]
- Top 3 posts (title + views): [LISTE]
- DM/Comment sentiment: [BESCHREIBUNG]

ACCOUNT B (Produktivität):
[same fields]

DECISION NEEDED: Should I
(A) Double down on the winning account,
(B) Kill both and pivot to a new niche (suggest top 3 from earlier research),
(C) Run a hybrid angle (e.g. "Finanzen für Selbstständige" crossover),
(D) Run both in parallel for another 30 days?

Score each option on: probability of 10k followers in 6 months, expected monthly revenue at month 3, time-cost-per-week, risk.

Give me a CONCRETE 30-day rollout plan for the recommended option, with weekly milestones and specific posts to create.
```

**Output:** Entscheidungs-Empfehlung + 30-Tage-Rollout-Plan mit Wochen-Meilensteinen.

### C2 — Winning-Post-Forensik

**Trigger:** Direkt nach C1-Entscheidung
**Wann:** 31.07.2026

```text
Here are my 3 best-performing posts from the 14-day test (titles + cards breakdown):
[PASTE TOP 3 FULL CAROUSEL TEXT]

Reverse-engineer WHY they worked:
1. What psychology pattern does each trigger? (loss-aversion, curiosity, social-proof, fomo, etc.)
2. What Card 1 → Card 2 transition creates the "swipe-pull"?
3. What's the "save-trigger" — the specific card that makes people save vs just like?
4. How can I create 20 MORE posts using the EXACT same pattern but different topics?
5. What's the "fingerprint" I should apply to ALL future posts in this niche?

Output: A reusable post-template (Hook-Pattern → Arc-Pattern → Pitch-Pattern) I can hand to ChatGPT to generate 30 posts in 1 hour.
```

**Output:** Wiederverwendbares Post-Template das mit ChatGPT in 1 Std 30 Posts generiert → direkt in `canva-bulk-create-{nische}.csv` einspeisen.

---

## Phase D — Scale Mode (Monat 2-6)

Diese Prompts kommen erst wenn eine Nische steht und skaliert wird.

### D1 — Content-Multiplikations-Strategie

**Trigger:** Nische bestätigt, 1-2 Posts/Tag konsistent
**Wann:** Anfang Monat 2

```text
I have a winning niche + a winning post-pattern. Now I need to multiply content 10× without burning out or losing quality. Build me a content-multiplication system:

1. How do I generate 30 posts/week from 1 winning template without audience fatigue?
2. The "topic-cluster" method: what are 7 sub-topic clusters in my niche that I can rotate through for 6 months without overlap?
3. User-Generated Content hack: how do I ethically recycle comments, DMs, and questions from my audience into new posts?
4. Trend-jacking without face/voice: how do I jump on trending TikTok sounds/audio without showing face? (audio-only carousels work?)
5. The "evergreen vs trending" balance: what % of my posts should be evergreen (always-relevant) vs trending (time-sensitive)?
6. Batch-production workflow: what's the minimum-viable weekly workflow to produce 14 posts in 1-2 days?

Reference faceless German accounts that scaled from 0 to 100k — what did their content calendar look like?
```

**Output:** 7 Topic-Cluster für 6-Monats-Rotation + Wochen-Batch-Workflow (kann Yuno in Cron packen).

### D2 — Monetization-Deep-Dive

**Trigger:** 5k+ Follower, Save-Rate stabil über 2%
**Wann:** Bei erstem Conversion-Druck (Monat 2-3)

```text
I'm hitting 2% Save-Rate and 5k+ followers. Now I need to convert attention to €€€. Audit my funnel:

1. Profile → PDF conversion: what's the realistic conversion rate from profile-visit to PDF-purchase for low-ticket €10-40 products in DACH? (industry benchmark)
2. Bio optimization: 5 bio-formulas for faceless accounts that drive profile-visits without triggering "Link in Bio" algorithm penalty.
3. PDF product pricing: should I start at €9.90 (impulse buy) or €29 (anchor high)? What does the data say for faceless accounts?
4. Product-bundle strategy: at what follower-count should I introduce a 2nd product, and what type (upsell, downsell, cross-sell)?
5. Email-list capture: when does it make sense to add an email funnel (e.g. free PDF → email → pitch sequence)? And does it cannibalize direct PDF sales?
6. Digistore24 vs FunnelCockpit vs custom: which German-friendly platforms have the best conversion-rate for low-ticket faceless PDFs in 2026?

Reference real case studies (German faceless accounts that went 0 → €1k/month) — I want the actual numbers.
```

**Output:** Funnel-Optimierungs-Checkliste + Pricing-Empfehlung + Platform-Vergleich.

### D3 — Cross-Niche-Pivot-Test

**Trigger:** Erste Nische stabilisiert sich
**Wann:** Monat 3-4 (wenn bereit für Account #2)

```text
My main account `@[winner]` is at [X] followers, [Y] monthly revenue. Now I want to launch account #2 in a complementary niche.

Help me pick the 2nd niche using this decision-tree:
1. Which niches share the SAME audience as my first (so I can cross-promote) but DON'T cannibalize the first niche?
2. Which niches use the SAME content template I've already mastered (so I don't re-learn)?
3. Which niches are 2026 up-and-coming (TikTok Creative Center "rising" filter) but NOT yet saturated?
4. Should I run a 2nd faceless account, or run 2 niches on the SAME account? (TikTok's audience-graph algorithm — does it penalize topic-mixing?)

Give me 3 concrete "niche-pair" recommendations where the math compounds (cross-promo, shared audience, shared production workflow).
```

**Output:** 3 Nische-Pair-Empfehlungen mit Cross-Promo-Strategie.

### D4 — Risk-Audit vor Skalierung

**Trigger:** 10k+ Follower, €500+/Monat
**Wann:** Monat 4-6 (vor "Kündige-meinen-Job"-Entscheidung)

```text
I'm scaling to potentially quit my day job. Audit my risk surface:

1. TikTok dependency risk: what's the realistic scenario where TikTok bans my account / changes algorithm / removes faceless content? Build a hedge strategy.
2. Single-platform fragility: should I be on Instagram Reels + YouTube Shorts in parallel from day 1? Cost vs benefit.
3. Legal compliance (German law): at what revenue/month do I need a Gewerbe, Kleinunternehmerregelung, Impressum, Datenschutzerklärung on my landing page?
4. Tax prep: how should I structure the income (Selbstständig vs Gewerbe vs Kleinunternehmer) for someone at €500-2000/month target?
5. Burnout prevention: what does a sustainable 12-month content calendar look like for a faceless German TikTok business? Days off, batch weeks, creative slumps — how do successful operators handle these?

Reference: 3 German faceless TikTok operators who went 0 → €5k/month and what their biggest mistakes were in months 6-12.
```

**Output:** Risiko-Matrix + konkrete Compliance-Checkliste + Burnout-Prevention-Plan.

---

## Quick-Reference-Card

```
┌─────────────────────────────────────────────────────┐
│ PERPLEXITY FOLLOW-UP — 13 Fragen, 4 Phasen         │
├─────────────────────────────────────────────────────┤
│ PHASE A (JETZT) — Pre-Launch                       │
│   A1 White-Space-Check         — nach Master       │
│   A2 Visual-Trend-Audit       — parallel zu A1     │
│   A3 Algorithmus-Wortliste DE — vor erstem Upload  │
├─────────────────────────────────────────────────────┤
│ PHASE B (Tag 1-14) — Daten-getrieben               │
│   B1 Halbzeit-Hook-Audit      — Tag 5-7            │
│   B2 Save-Rate-Diagnose       — Tag 7-10           │
│   B3 Comment-Mining           — Tag 8-10           │
├─────────────────────────────────────────────────────┤
│ PHASE C (Tag 14+) — Entscheidung                   │
│   C1 Kill-vs-Double-Down      — Tag 14             │
│   C2 Winning-Post-Forensik    — Tag 14-16          │
├─────────────────────────────────────────────────────┤
│ PHASE D (Monat 2-6) — Skalierung                   │
│   D1 Content-Multiplikation   — Monat 2            │
│   D2 Monetization-Deep-Dive   — Monat 2-3          │
│   D3 Cross-Niche-Pivot-Test   — Monat 3-4          │
│   D4 Risk-Audit vor Scale     — Monat 4-6          │
└─────────────────────────────────────────────────────┘
```

## Referenzierte Dateien (linked_files)

Wenn du nur eine bestimmte Frage brauchst, lade die jeweilige Datei direkt:

| Datei | Wann laden |
|---|---|
| [`references/00-ANLEITUNG.md`](references/00-ANLEITUNG.md) | **Erst hier starten** — Schritt-für-Schritt-Anleitung |
| [`references/01-phase-a-pre-launch.md`](references/01-phase-a-pre-launch.md) | Phase A Übersicht + Workflow |
| [`references/A1-niche-white-space.md`](references/A1-niche-white-space.md) | Konkreter A1-Prompt |
| [`references/A2-visual-trend-audit.md`](references/A2-visual-trend-audit.md) | Konkreter A2-Prompt |
| [`references/A3-algorithmus-wortliste.md`](references/A3-algorithmus-wortliste.md) | Konkreter A3-Prompt |
| [`references/02-phase-b-during-test.md`](references/02-phase-b-during-test.md) | Phase B Übersicht + Workflow |
| [`references/B1-halbzeit-hook-audit.md`](references/B1-halbzeit-hook-audit.md) | Konkreter B1-Prompt |
| [`references/B2-save-rate-diagnose.md`](references/B2-save-rate-diagnose.md) | Konkreter B2-Prompt |
| [`references/B3-comment-mining.md`](references/B3-comment-mining.md) | Konkreter B3-Prompt |
| [`references/03-phase-c-post-test.md`](references/03-phase-c-post-test.md) | Phase C Übersicht + Workflow |
| [`references/C1-kill-vs-double-down.md`](references/C1-kill-vs-double-down.md) | Konkreter C1-Prompt |
| [`references/C2-winning-post-forensik.md`](references/C2-winning-post-forensik.md) | Konkreter C2-Prompt |
| [`references/04-phase-d-scale-mode.md`](references/04-phase-d-scale-mode.md) | Phase D Übersicht + Workflow |
| [`references/D1-content-multiplikation.md`](references/D1-content-multiplikation.md) | Konkreter D1-Prompt |
| [`references/D2-monetization-deep-dive.md`](references/D2-monetization-deep-dive.md) | Konkreter D2-Prompt |
| [`references/D3-cross-niche-pivot.md`](references/D3-cross-niche-pivot.md) | Konkreter D3-Prompt |
| [`references/D4-risk-audit-pre-scale.md`](references/D4-risk-audit-pre-scale.md) | Konkreter D4-Prompt |
| [`05-reports-synthese-2026-07-15.md`](05-reports-synthese-2026-07-15.md) | **Konsolidierte Synthese der 3 Perplexity-Reports** mit Action-Items für laufenden Test |

---

## Wie ich diesen Skill nutze (für Yuno selbst)

### Trigger-Wort → Prompt-Mapping

| User sagt | Phase-Prompt |
|---|---|
| "Perplexity A1" / "White-Space-Check" | Phase A → A1 |
| "Visual-Trends" / "Design-Trends 2026" | Phase A → A2 |
| "Algorithmus-Wörter" / "Banned Words" | Phase A → A3 |
| "Halbzeit-Check" / "Hook-Audit" | Phase B → B1 |
| "Save-Rate flach" / "Diagnose Saves" | Phase B → B2 |
| "Comment-Mining" / "DM-Ideen" | Phase B → B3 |
| "Final-Decision" / "Kill-or-Double-Down" | Phase C → C1 |
| "Winning-Post-Forensik" / "Template extrahieren" | Phase C → C2 |
| "Multiplikation" / "Content-Skalierung" | Phase D → D1 |
| "Funnel-Audit" / "Monetarisierung" | Phase D → D2 |
| "Account #2" / "Cross-Nische" | Phase D → D3 |
| "Risk-Audit" / "Pre-Scale" | Phase D → D4 |

**🔄 TL;DR-Version:** `tiktok-design-assistant/references/perplexity-research-framework.md` hat die Kurzfassung in tabellarischer Form — gut wenn Basti schnell einen Perplexity-Prompt braucht ohne alle 13 Folge-Dateien. Dieser Skill hier ist die Langfassung mit vollem Runbook, Anti-Pattern-Checklisten und einzelnen Prompt-Dateien pro Phase. Beide existieren parallel.

### Workflow

1. Basti sagt Trigger-Phrase (z.B. "Yuno, Perplexity A1")
2. Yuno lädt diesen Skill, holt den A1-Prompt
3. Yuno fragt Basti nach den 5 Top-Nischen aus Master-Prompt (falls noch nicht in Memory)
4. Yuno formatiert den Prompt mit den Variablen und gibt ihn Basti copy-paste-ready
5. Basti fügt in Perplexity ein, wartet 2-5 Min, pastet Antwort zurück
6. Yuno übersetzt Kern-Insights auf deutsch, schlägt Action-Items vor, integriert in `pitch-variants.json` / `brand-system-{nische}.json` falls sinnvoll

### Variablen die Yuno bei jedem Trigger einsetzen muss

- **A1:** Top-5-Nischen aus Master-Prompt
- **B1:** Echte Daten aus `14-Tage-Test-Tracking.md` (Spalten Post/Views/Likes/Saves/Completion%)
- **B2:** Aktuelle Save-Rate + Beispieltitel der Posts
- **B3:** 30+ echte Kommentare (Basti pastet sie)
- **C1:** Finale 14-Tage-Daten + DM/Comment-Sentiment-Beschreibung
- **C2:** Top-3-Posts als vollständiger Carousel-Text
- **D1-D4:** Account-Stats + Revenue-Zahlen

---

## Nach dem Prompt: Report-Evaluierung & Vertrauens-Check

> **Wichtig:** Basti erwartet explizit kritische Prüfung (hat in Session 2026-07-15 gesagt: „evaluiere"). Niemals blind aus Perplexity-Output Aktionen ableiten. Immer zuerst evaluieren, dann handeln.

Nach jedem Perplexity-Deep-Research-Run durchläufst du diese 3-stufige Evaluierung BEVOR du Action-Items vorschlägst:

### Stufe 1: Konsens-Triangulation

Wenn mehr als 1 Report vorliegt, wichte die Claims nach Übereinstimmung:

| Evidenz-Stärke | Bedingung | Bedeutung | Entscheidung |
|---|---|---|---|
| ⭐⭐⭐⭐⭐ | Alle Reports stimmen überein | Robuster Konsens | **Direkt umsetzbar** — kein Gegencheck nötig |
| ⭐⭐⭐⭐ | 2 von 3 Reports bestätigen | Plausibel, eine Quelle abweichend | **Soft implementieren** — tracken, nicht final committen |
| ⚠️ | Nur 1 Report / Klingt plausibel | Einzelmeinung | **Nicht ohne Verifikation committen** — A/B-testen oder manuell prüfen |
| ❌ | Kein Konsens / Halluzinationsverdacht | Widersprüchlich oder erfunden | **Manuell prüfen** — TikTok-Suche, Handle-Check, Primärquelle |

**Beispiel aus 2026-07-15:** „Steuertipps Arbeitnehmer = White Space" kam in allen 3 Reports -> direkt umsetzbar. „Gehaltsverhandlung Top-2 Nische" kam nur in Report 1 -> zurückgestellt.

### Stufe 2: Quellen-Triage

Bevor du einen Perplexity-Claim als Tatsache behandelst, prüfe diese 6 Kategorien:

1. **@-Handles** — Immer auf TikTok selbst prüfen ob der Account existiert. Perplexity halluziniert regelmäßig Accounts mit plausibel klingenden Namen.
2. **Income-Prognosen** („€1k in 3 Monaten", „0→5k in 6 Monaten") — Nie als Planungsgrundlage verwenden. Perplexity extrapoliert oft aus US-Fallstudien auf DACH. Nur Benchmarks mit Quellenangabe akzeptieren.
3. **Design-Urteile** („Gelb+Schwarz ist der Trend 2026", „Deep Teal+Champagne ist Sleeper") — Ästhetische Aussagen sind subjektiv. A/B-testen vor commit, nicht als Brand-Änderung übernehmen.
4. **Rechtsaussagen** („EU AI Act ab 02.08.2026") — Gegencheck mit Primärquelle (BVDW, offizielle EU-Seite, Steuerberater). Perplexity fasst Sekundärquellen zusammen.
5. **Benchmarks ohne DACH-Kontext** („Save-Rate 5% = gut") — Meist aus US-Studien. DACH-Faceless-PDF-Business ist ein neues Segment ohne etablierte Benchmarks. Schwelle lieber niedriger ansetzen.
6. **arXiv-IDs und akademische Zitationen** — Perplexity zitierte `arxiv.org/abs/2601.14470` — dieses Format ist unmöglich. arXiv-IDs sind YYMM.NNNNN (z.B. 2410.12345), nicht 4-stellige Jahreszahlen. Gleiches gilt für DOI-Formate und ISBN/ISSN. Vor Zitation die Primärquelle checken.

### Stufe 3: Entscheidungs-Matrix

Strukturierte Antwort an Basti nach jedem Report:

```
### 1. ROBUST (Konsens) — Sofort umsetzen
• [Claim 1] -> [konkrete Action]

### 2. TESTBAR (Plausibel) — Soft implementieren
• [Claim 2] -> [A/B-Test oder eingeschränkte Umsetzung]

### 3. KRITISCH (Push Back) — Manuell prüfen oder verwerfen
• [Claim 3] -> [warum es ignoriert wird]
```

**Wichtig:** Gib jedem Item einen konkreten Aufwand („15 Min", „30 Min", „1 Std") damit Basti priorisieren kann. Endet mit einem klaren nächsten Schritt.

---

## Workflow-Konvention (Basti's Arbeitsstil)

Basierend auf bisherigen Sessions:

1. **Report kommt rein -> zuerst evaluieren**, nicht sofort handeln (Basti: „evaluiere")
2. Nach Evaluation: **„Mach mal die [Zeit]-Schritte" anbieten** — Basti entscheidet danach ob Sofort-Umsetzung oder erst diskutieren
3. **Niemals blind übernehmen** — Perplexity ist Recherche-Tool, nicht Entscheidungs-Tool
4. **Alle Report-Insights dokumentieren** (Vault + Skill-Reference) für nächsten Modell-Wechsel
5. **Memory schreiben** nach jeder wichtigen Synthese (damit nächste Session nahtlos weiterarbeitet)

---

## Post-Result: Vault-File Creation (Stufe 4)

Nachdem die 3-Stufen-Evaluierung durchgelaufen ist: **baue strukturierte Vault-Files aus dem Research-Output.** Dieses Pattern übersetzt Perplexity-Ergebnisse + Subagent-Pre-Research + eigene Evaluation in permanente, nutzbare Wissensdokumente.

**Dual-Path-Pattern:** Aus jedem Research-Output entstehen zwei Artefakte:
- **User-facing Vault-File** (`~/Dokumente/{domain}/{topic}-{date}.md`) — Basti kann es lesen, referenzieren, erweitern
- **Agent-facing Memory** (`mnemosyne_remember`) — nächste Session hat den synthetisierten Stand ohne Neu-Lesen

**Struktur jedes Vault-Files:**
1. **Title + Datum + Source-Attribution** (welcher Perplexity-Report? welche Pre-Research-Subagent?)
2. **Structured Tables** — konsistentes Format pro Topic
3. **Verified-Sektion** — `## 🔗 Verified Sources` mit allen live-gecheckten URLs
4. **Cross-Refs** — Links zu anderen Vault-Files, Mnemosyne-IDs, Skill-References
5. **Tags + Use-Trigger** — damit der Finder/Search es wiederfindet

**Vault-File-Namenskonvention (validiert auf 5 Files in Session 2026-07-16):**
```
{domain-slug}-{topic-slug}-{YYYY-MM-DD}.md
```

**Complete runbook + template + edge cases:** `references/post-result-vault-pipeline.md`

---

## Post-Result: Memory Consolidation (Stufe 5)

Nach Vault-File-Creation: **Konsolidiere die Session-Erkenntnisse in Memory.**

### Wann consolidieren

| Situation | Aktion |
|---|---|
| >10 neue Memory-Items in dieser Session | → `mnemosyne_sleep(all_sessions=true)` |
| >2 Subagent-Dispatches + Vault-Files erstellt | → `mnemosyne_sleep(all_sessions=true)` |
| Nur 1-2 einfache Fakten gelernt | → Einzelnes `mnemosyne_remember` reicht |

### Was kommt ins Working Memory (global)
- **Final State**: Zusammenfassung was passiert ist
- **Insights**: Lessons learned (Display-Name ≠ @Handle, Cross-Report-Diffs, etc.)
- **Use-Trigger**: „Nächstes Mal wenn wir..."

### Was NICHT in Memory
- Task-Progress (ist in Vault-Files dokumentiert)
- Transiente Zustände (Subagent-Timings, Fehlermeldungen)
- Session-spezifische IDs (außer sie sind durable Referenzen)

Nach Consolidation: prüfe `mnemosyne_diagnose()`.

---

## Pitfalls (aus der bisherigen Erfahrung)

1. **Perplexity halluziniert @-Handles** — IMMER selbst verifizieren bevor Accounts als Inspiration genannt werden. Lieber 2 echte als 5 erfundene.
2. **2026-Daten ≠ Evergreen-Listen** — Perplexity zieht manchmal 2022-Listen wenn die Frage zu generisch ist. Im Prompt immer „2026" + „current data" markieren.
3. **Save-Rate ≠ Conversion** — Perplexity kann Save-Rate und Conversion-Rate verwechseln. Im Prompt klar trennen.
4. **DACH-Markt ≠ US-Markt** — Perplexity default oft US. Im Prompt „German / DACH / DE-AT-CH" immer explizit nennen.
5. **„Link in Bio" ≠ „Mehr in meinem Profil"** — TikTok's algorithmische Behandlung unterscheidet sich nachweislich (siehe A3). Perplexity kann das nicht wissen ohne expliziten Hinweis.
6. **Income-Proofs blind glauben** — Perplexity zitiert oft generische „0→€1k/Monat"-Fallstudien ohne Quellen. Niemals als Planungsgrundlage verwenden.
7. **Design-Urteile als Fakten missverstehen** — „Sleeper-Kombos" und „Farbtrends" sind ästhetische Aussagen, keine Daten. A/B-testen vor commit.
8. **EU-Daten aus US-Studien ableiten** — Viele Benchmarks (Save-Rate, CTR, Conversion) kommen aus US-Markt. DACH hat andere Nutzerverhalten.
9. **arXiv-IDs genau prüfen** — Perplexity zitierte `arxiv.org/abs/2601.14470` — dieses Format ist unmöglich. arXiv-IDs sind YYMM.NNNNN (z.B. 2410.12345), nicht 4-stellige Jahreszahlen. Vor Zitation die echte arXiv-Seite checken (arxiv.org/abs/<id>). Gleiches gilt für DOI-Formate und ISBN/ISSN — Perplexity halluziniert regelmäßig plausible ID-Formate.
10. **US-Benchmarks nicht 1:1 für DACH übernehmen** — Save-Rate, CTR, Conversion-Rates sind marktabhängig. Perplexity default auf US-Daten. Immer DACH-spezifische Benchmarks verlangen.
11. **Income-/Conversion-Prognosen skeptisch** — „0→€1k/Monat in 3 Monaten" ist Marketing-Sprech, kein datengetriebener Forecast. Perplexity zitiert oft generische Case-Studies ohne Beleg.
12. **Platform-Download-Zahlen ≠ echte Nutzung** — MakerWorld zählt jeden „Prepare for Print"-Tap in Bambu Studio als Download, nicht nur tatsächliche Drucke. Ein Modell mit 28k Downloads kann real nur ~5k mal gedruckt worden sein. **Bessere Signalquellen:** Likes (echter Community-Vote), Collections (Intent-Signal), Comments (Diskussion), Boost-Punkte (bezahlte Wertschätzung). Auf Printables/Thangs dasselbe — „Downloads" ist dort oft reine Page-Views. Immer die relativen Metriken (downloads:likes ratio) checken: ein gesundes Modell hat mindestens 1 Like pro 10-15 Downloads. Bei 1:100+ ist der Download-Count fast bedeutungslos.
13. **OBSOLETE/Mark-as-Stale Flag übersehen** — Perplexity listet auch Modelle die der Creator selbst als obsolete markiert hat, ohne das prominent zu signalisieren. Beispiel aus 2026-07-16: „Reduce purge by up to 45%" hat im MakerWorld-Titel „(Obsolete)" stehen, Perplexity erwähnte das nicht. Vor jeder STL/Code-Empfehlung die aktuelle Model-Seite auf Obsolete-Flags, OBSOLETE-Tags oder „no longer maintained"-Hinweise prüfen. Besonders kritisch bei G-Code-Profilen, Scripts und Workarounds — die werden häufig durch native Slicer-Features ersetzt.
14. **Display Name ≠ @Handle auf Plattformen** — Perplexity zitiert oft den User-facing Display Name statt des echten @-Handles. Beispiel 2026-07-16: Perplexity sagte „TuTu (@TuTu)" und „茄汁北塔 (@茄汁北塔)" — LIVE MakerWorld-URLs zeigen @yujixun und @qzbeta. Keine Halluzination (der Account existiert), aber der Handle ist nicht der, unter dem du auf der Platform suchen würdest. **Fix:** Bei Creator-Angaben IMMER die Model-ID (URL-Pfad-ID wie `model/493268`) als Identifikation nutzen, nicht den Display-Namen. Bei Handle-Suche auf der Platform: per Model-ID suchen, nicht per Name. Gleiches gilt für Printables (Display Name vs Username), GitHub (Display Name vs @login), Thingiverse, Etsy.
15. **Cross-Report-Diff für Push-Back Erkennung** — Wenn 2+ Perplexity-Reports auf dasselbe Thema laufen, müssen die Ergebnisse systematisch verglichen werden. Beispiel 2026-07-16: Report #1 listete "Reduce purge by up to 45%" (Leon Fisher-Skipper) als verifizierten Top-Print (12k Downloads). Report #2 (Custom-aware-Prompt) listete denselben Print als **OBSOLETE** — und hatte recht. Der Workaround ist seit ~2024 nativ in Bambu Studio integriert. **Regel:** Führe einen systematischen Cross-Report-Diff durch — gleiche empfohlene Items tabellarisch vergleichen, Status-Unterschiede markieren. Wenn ein Item in Report A als ROBUST und in Report B als KRITISCH/OBSOLETE geführt wird: Report A hat ein Flag übersehen. Umsetzung: Matrix mit Item-Zeilen + Status pro Report + roter Markierung bei Differenz.
16. **Subagent-Claims sind self-reports** — Ein Subagent der "[VERIFIED]" meldet, hat web_extract aufgerufen, aber DU siehst das Resultat nicht. Immer die TOP-3-URLs pro Kategorie selbst per web_extract checken, bevor du sie als Anchor in den Prompt einbaust. Siehe `references/pre-research-subagent-pattern.md` Pitfall #1.
17. **Reddit blockt web_extract** — Subagents können Reddit-URLs nicht verifizieren. Im Subagent-Briefing: "Reddit URLs = search-suggested fallback, mark as (unverified inline)." Vermeide >2 Reddit-URLs pro Topic — Bambu Forum und Bambu Wiki sind verifizierbar und zuverlässiger.
18. **Single-Path Confidence überschätzen** — Ein einzelner Perplexity-Deep-Research-Run hat systematische Blind Spots. Der Custom-Aware-Prompt übersieht generische Top-Picks (weil er auf Lücken fokussiert). Der Fresh-Prompt übersieht Nischen-Picks (weil er dein Wissen nicht hat). **Regel:** Bei Investitionsentscheidungen (Materialkosten >€10, Nischen-Pivot, >5 Std Druck) → Dual-Path Pflicht. Single-Path reicht nur für Quick-Research wo eine schnelle Antwort > Richtigkeit ist.

---

## Cross-Links

- **Skill:** `tiktok-design-assistant` (Brand-System + Canva-CSV-Generierung)
- **Skill:** `tiktok-business-self-improve` (Cron-Job Mo-Fr 19:00)
- **Skill:** `orchestration/agent-orchestration-patterns-2026` (3-Stufen-Evaluierung auf non-TikTok-Topic validiert, Perplexity-Research-Summary als Reference)
- **Vault:** `03 Projekte/Yuno-Anon-TikTok-Business.md` (Projekt-MOC)
- **Vault:** `03 Projekte/Yuno-Anon-TikTok-Business/14-Tage-Test-Tracking.md` (Daten-Quelle)
- **Repo:** `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json` (Output-Integration)
- **Master-Prompt (separat):** Die Master-Deep-Research-Frage aus der Initial-Session, nicht Teil dieses Skills — der Master wird einmal gefeuert, dieser Plan strukturiert die Folgenschritte.