---
name: custom-aware-research-prompt
description: >-
  Use when user asks for building a tailored Perplexity research prompt, including a custom tool or configuration stack in research, pre-verifying source URLs for deep research, or coordinating parallel research runs. NOT for performing generic web search directly or writing an ungrounded one-line prompt. Produces source-anchored, custom-aware prompts with explicit output fields, cross-report comparison, and a post-research validation loop.
trigger-words:
- perplexity
- deep-research
- custom-aware
- research-prompt
- perplexity-prompt
- custom-prompt
- pre-research
- subagent-verification
author: Yuno
category: orchestration
lane: koenigin
last-updated: 2026-07-16
version: 2.0.1
key-changes-v2.0.1: 'Added Pitfall #13 (Subagent-Selbst-Verifikation reicht nicht — Parent Re-Verification Gate). Updated Pitfall #2 to reference the limitation.'
license: MIT
trigger_keywords: ['research', 'prompt', 'custom', 'source', 'user']
keywords: ['research', 'prompt', 'custom', 'source', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['perplexity-followup-plan', 'godmode']
---

# Custom-Aware Research Prompt

Baut **Custom-Aware Deep Research Prompts** für Perplexity (oder vergleichbare Deep-Research-Tools) mit Pre-Research-URL-Verifikation durch Subagents. Liefert 30-40% mehr Hidden-Gems als Generic Prompts und reduziert Perplexity-Halluzinations-Risiko drastisch.

## Wann diesen Skill laden

Trigger-Bedingungen:
- User fragt "Bau mir einen Perplexity Prompt für..."
- User hat ein konkretes Research-Target (3D-Drucker-Mods, Cloud-Cost-Vergleich, LLM-Vergleich, etc.)
- User hat bereits einen **Custom-Stack** (selbstgebaute Tools, Configs, vorhandene Libs) den Perplexity kennen soll
- User will **mehrere parallele Research-Runs** mit ähnlicher Struktur

NICHT für: Quick-Fact-Lookup (web_search reicht), Single-URL-Verification (web_extract reicht), Ad-hoc-Fragen ohne Research-Charakter.

## Kern-Prinzipien (aus A1-Mini-Perplexity-Pass 2026-07-16 verifiziert)

### 1. Custom-Aware > Generic
Perplexity liefert **30-40% mehr Hidden-Gems** wenn das User-Setup explizit im System-Kontext steht (Skip-Liste: "Spool-Holder, Filament-Clips" → Perplexity empfiehlt was gefehlt hat statt offensichtliche Nachschläge).

### 2. Pre-Research Subagent vor User-Run
Bevor der User den Perplexity-Prompt abschickt:
- Subagent durchsucht das Topic mit `web_search` und identifiziert **Top-URLs**
- Verifiziert **mindestens N/2** (bei 12 URLs = 6 verified) via `web_extract` → `[VERIFIED]` tag
- Liefert pre-verified URL-Liste als Anchor für den finalen Prompt

**Vorteil:** Perplexity muss nicht raten welche URLs echt sind → weniger Halluzinationen → User kann Output schnell gegen Anchors cross-checken.

### 3. Display-Name ≠ @Handle-Falle
MakerWorld, GitHub, YouTube zeigen **Display Names** statt Creator-Handles. Perplexity zitiert "TuTu" statt `@yujixun` (z.B. bei model/1686183). Bei Verifikation:
- **Model-ID vor Creator-Handle** (z.B. `makerworld.com/en/models/1686183` statt `yujixun`)
- **Cross-Reference:** Model-URL > Creator-Page > Search-Query

### 4. Cross-Report-Diff als Standard
Wenn 2 Perplexity-Runs dasselbe Topic behandeln, **sind Push-Backs Pflicht**. Beispiel aus 2026-07-16: Report #1 verkaufte "Reduce Purge G-Code" als 12.100-Downloads-Hit, Report #2 zeigte "OBSOLETE" im Titel → User spart sich eine Fehlinvestition.

### 5. Output-Format mit konkreten Feldern
Perplexity liefert mit **explizitem 12-15-Felder-Schema** strukturiertere Outputs als mit offenen "tell me about X" Prompts. Pro Item:
- Model/Item-Name + Creator + @Handle + URL
- Quantitative Signals (downloads/likes wenn verfügbar)
- Difficulty + Material + Tool/Requirements
- A1-Mini-Specific-Score (oder analog zum User-Setup)

## Workflow (5 Phasen)

### Phase 1: User-Setup aufnehmen
Lies User-Context:
- Welches System/Produkt/Thema?
- Was hat User **schon** (Skip-Liste)?
- Welche Constraints (Größe, Spec, Budget, Region)?
- Welches Output-Format passt zum Use-Case?

### Phase 2: Pre-Research Subagent (PARALLEL)
Falls 3+ Perplexity-Runs geplant: dispatch **N Subagents parallel** (eines pro Topic) mit:
- Konkretem Output-Format (Markdown-Tabelle, count von URLs, [VERIFIED] requirements)
- Minimum Verified-URL-Quote (z.B. 6/12)
- Timeout-Constraint (subagents brauchen meist 2-5 Min)
- NO file writes (nur Summary im Reply)

Beispiel-Subagent-Prompt-Struktur:
```
You are doing PRE-RESEARCH for [Topic].
Find and verify live URLs for [N categories].
Use web_search AND web_extract.
Return summary in reply only — NO file writes.
For at least N/2 URLs, use web_extract to confirm live content.
Mark each [VERIFIED] when confirmed.
```

### Phase 3: Custom-Aware Prompt formulieren
Original-Prompt + **Custom-Setup im System-Kontext** (Skip-Liste + Constraints) + **Verified-URL-Anchor-Block**:
```
CONTEXT — what I already have:
[Skip-Liste explizit]

WHAT I NEED FROM YOU:
DELIVER N CATEGORIES with EXACTLY M entries each.

[Verified URL Block am Ende:]
## ✅ PRE-VERIFIED SOURCES (von Yuno)
[Subagent-Output als Anchor]
```

### Phase 4: User-Feedback-Loop (optional)
Falls User Optionen sehen will: 2-4 Varianten mit Trade-offs anbieten, **NICHT offene Frage**.
### Phase 5: Post-Processing (Cross-Validation + Vault File)

Nach User-Perplexity-Run: Output nicht einfach ablegen — **cross-valideren, klassifizieren, in Vault-File gießen**.

#### 5a. Input-Sammlung
Sammle ALLE verfügbaren Quellen für dieses Topic:
- **A:** Subagent Pre-Research (Phase 2 — verified URLs + Top-Picks)
- **B:** Perplexity Result 1 (z.B. Context-Aware / "new deep research")
- **C:** Perplexity Result 2 (z.B. Fresh / "existing research context")
- **D:** Weitere Perplexity Runs (wenn vorhanden)

#### 5b. Tier-Klassifizierung
Jedes Modell/Item aus den Quellen klassifizieren:

| Tier | Definition | Aktion |
|------|------------|--------|
| 🏆 **Tier-1** | In **2+ unabhängigen Quellen** (z.B. Subagent + Perplexity ODER Perplexity A + Perplexity B) | **MUST-PRINT** / TOP-PRIORITÄT |
| 🔹 **Hidden-Gem** | Nur in 1 Quelle, aber **live verifiziert** (Creator @Handle + URL + Downloads/Likes) | **HIGH-VALUE**, Phase 2 |
| 📋 **HM** | Nur in 1 Quelle, Community-Signal OK aber keine Cross-Validation | **Optional**, nach Bedarf |

#### 5c. Live-Verifikation (Pflicht vor Final)
Jedes Item im Vault-File **muss live verifiziert** sein:
- `web_extract(char_limit=1500)` auf die URL
- Prüfe: Creator @Handle ✅, Modell existiert ✅, Print-Profile existiert wenn A1 Mini ✅
- Stat-Zahlen (downloads/likes) aus live-Page, nicht aus Perplexity-Output
- A1-Mini-Profile: Prüfe ob explizit gelistet (Search "A1 mini" in print profiles)
- **Bei Diskrepanz: live-Page gewinnt** (z.B. Perplexity sagt `@SyphenGuitarWorks` → live zeigt `@RobSGW`)

#### 5d. Vault-File-Struktur (Template)

```markdown
# [Use-Case] — A1 Mini STL Picks ([Datum])

> [Kurzbeschreibung] — Cross-Validation aus [Quellen].
> Tier-1 Picks live via `web_extract` verifiziert.
> Quellen: [Pfade zu Prompts + Perplexity-Outputs]

## 🏆 Tier-1 Picks (in BOTH [Quelle A] + [Quelle B])
Pro Pick: 12-15 fields (Creator+@Handle+[VERIFIED], URL, Stats live-verifiziert, Material, Print time, Why beats alt, Known A1 Mini issues, Source)

## 🔹 Hidden-Gems — [Quelle A]
Gleiche Felder + Herkunfts-Vermerk

## 📊 Cross-Validation Matrix
Tabelle: Modell | Subagent | Perplexity A | Perplexity B | Tier | Recommendation
```

#### 5e. Druck-Priorisierung (3 Phasen)
Nach Vault-Bau: **immer Phase-1/2/3 vorschlagen**:
- **Phase 1** (~10h, diese Woche): Nur Tier-1 + höchste Hidden-Gems
- **Phase 2** (~12h, nächste Woche): Verbleibende Hidden-Gems mit hohem Wert
- **Phase 3** (nach Bedarf): Honorable Mentions, forward-looking picks

#### 5f. Cross-Report-Diff bei Fresh vs Context-Aware
Wenn 2 Perplexity-Runs zum selben Topic existieren (einer mit vollem Custom-Kontext, einer frisch):
- Explizite Vergleichs-Tabelle: #Items, #Unique, #Match, #Discrepancy
- **Fresh Prompt liefert oft 30-40% mehr Hidden-Gems aber auch mehr Noise** (verified 2026-07-16: Workshop Fresh=45 Items, Context-Aware=27 Items, Overlap=12)
- **Context-Aware Prompt liefert präzisere Recommendations mit weniger Duplikaten** — weil Skip-Liste effektiv filtered
- Merge: Tier-1 = in BOTH, dann deduped merge (Context-Aware behält Ranking, Fresh liefert Ergänzungen)
- **Entscheidungshilfe:** Wenn User erstes Research betreibt → Context-Aware Prompt zuerst (hohe Precision). Wenn User bestehendes Wissen erweitern will → Fresh Prompt zuerst (hohe Recall), dann über Cross-Validation zuspitzen

#### 5g. Live-MakerWorld-Profil-Prüfung (Pflicht bei 3D-Print-Recherche)
Bei jedem `web_extract(char_limit=1500)` auf MakerWorld/Printables-Seiten zusätzlich prüfen:

1. **Print-Profile-Liste scannen:** Enthält die Seite explizit "A1 mini" in der Printer-Select-Liste?
   - ⭐ Factory Profile (Creator authorisiert) = hohe Vertrauenswürdigkeit
   - ⚠️ User G-Code (Custom Profile) = mittlere Vertrauenswürdigkeit
   - ❌ Kein A1-mini-Profil = skalieren/adaptieren nötig
   - 🔥 "Print Profile(X)" mit X>5 = Creator maintaint aktiv → weniger Stale-Risiko

2. **Bildlink-Liste checken:** MakerWorld liefert Image-URLs in web_extract. Wenn alle Images `.gif` statt `.jpg` → Creator zeigt GIF-Demo statt Fotos → möglicherweise nicht-real-world-getestet

3. **Stats aus live-Page, nicht aus Perplexity-Output:** MakerWorld zeigt Downloads + Favorites direkt im SEO-Title oder Header. Perplexity-outputted Zahlen sind oft 2-3 Wochen alt.

4. **Alternative-Links checken:** MakerWorld zeigt Related Models Footer → können Cross-Validation für Honorable Mentions liefern

Verification-Output-Beispiel (2026-07-16):
```
Moskk83 Hotend Cable Chain: A1 mini ✅ P1S ✅ P1P ✅ X1 ✅ X1C ✅ A1 ✅ (14 Profiles, 62.3k Favorites live)
Sebo Witt Anti-Vibration Feet: A1 mini ✅ P1S ✅ P1P ✅ X1 ✅ X1C ✅ A1 ✅ H2D ✅ (98.8k Favorites live)
mlodybuk Camera Holder: A1 mini ✅ X1C ✅ P1S ✅ P1P ✅ X1 ✅ A1 ✅ H2D ✅ (4.8k Dls, 1.4k Favs live, 28 min!)
```

#### 5h. Memory-Update
Nach Merge: Mnemosyne-Entry mit Final State (welche Vault-Files created), Anzahl verifizierter URLs, Key Insights, Pfade zu allen Quellen für Session-Recovery.
- **Source-Tag:** `insight` (keine zukünftige Session sollte die Analyse wiederholen)
- **Veracity:** `tool` (live verifiziert mit web_extract)
- **Scope:** `global` (für alle Future-Sessions nutzbar)

#### 5i. Vault-File → Queue Integration (VERIFIED 2026-07-16)
Nachdem N+ Vault-Files existieren (Phase 5d-5h pro Topic): **Merge in eine Single Druck-Queue mit Phasen-Logik.**

**Integration Steps:**
1. **Alle Tier-1 Items sammeln** aus allen Vault-Files → deduped Master-List
2. **Cross-Topic-Ranking:** Nicht nach Topic sortieren (erst Workshop, dann Gaming) sondern nach **Abhängigkeit**:
   - Phase 1: Baseline/Calibration (jeder Drucker braucht das)
   - Phase 2: Pflicht-Mods (Hardware-Veränderungen → danach ändert sich Vibration/Passform)
   - Phase 3: Optional-Verbesserungen (Camera, Lightbar, AMS-Lite)
   - Phase 4+: Topic-spezifisch nach Lust/Zeit (Workshop, Gaming, Nerd)
3. **"✅ HAB ICH" aus der Custom-Lib markieren** und als NO-PRINT in Phase-Liste führen — verhindert Fehldrucke
4. **Time Accounting:** Pro Phase: ~ Stunden × Anzahl Prints → User kann Wochenende planen
5. **Cross-File-Referenzen:** Jeder Eintrag verweist auf das Ursprungs-Vault-File + Subagent + Perplexity-Output

**Template Queue-Header:**
```
| Phase | Thema | Prints | Estimated Time |
|-------|-------|--------|----------------|
| 1 | [Baseline] | N | ~Xh |
| 2 | [Essential Mods] | N | ~Xh |
| 3 | [Enhancers] | N | ~Xh |
| 4+ | [Topic A/B/C] | N | ~Xh |
| TOTAL | | ~N | ~Y-Z Std |
```

**Phase-Logik-Notiz am Ende:** Erklärt WARUM die Reihenfolge wichtig ist (z.B. "erst Kabel-Ketten, dann Feet, weil Feet Vibration ändern → danach müssen Chains neu justiert werden")

## Pitfalls (5+)

| # | Pitfall | Mitigation |
|---|---------|-----------|
| 1 | Generic-Prompt ohne Custom-Setup → 30-40% weniger Hidden-Gems | Skip-Liste + Constraints IMMER im System-Kontext |
| 2 | Pre-Research Subagent ohne web_extract-Verifikation → URLs können halluziniert sein | Mindestens N/2 mit `[VERIFIED]` markieren, web_extract ist Gate. **⚠️ ABER:** Auch Subagent-Selbst-Verifikation reicht nicht — siehe Pitfall #13 und Schwester-Skill `subagent-url-verification-gate` → Phase 5. |
| 3 | Display-Name als @Handle zitiert → Perplexity-Output ist nicht reproduzierbar | **Model-ID vor Creator-Handle**; cross-reference Model-URL > Creator-Page > Search-Query |
| 4 | Output-Format zu vage ("tell me about X") → Perplexity liefert Bullshit-Bingo | **Explizite 12-15-Felder** pro Item mit konkreten Beispielen |
| 5 | Push-Backs bei Cross-Report-Konflikten werden übersehen | **Immer beide Reports** vergleichen wenn 2+ Runs zum selben Topic |
| 6 | Perplexity zitiert nicht-existente Forum-Threads | Subagent soll `forum.bambulab.com/t/...` Pattern explizit verifizieren |
| 7 | Output verschwindet in Mnemosyne ohne Eval-Marker | Nach Merge: 3-Stufen-Eval (Verified/Plausibel/OBSOLETE) als Markdown-Tabelle |
| 8 | 5+ Perplexity-Runs parallel ohne Subagent-Anchors → 50% URLs falsch | Pro Topic 1 Subagent, max 6 parallel (delegation max_concurrent_children=6) |
| 9 | **Assumed AI Tool Capability ≠ Reality** — User sagt "ich lass die CAD mit Fable kreieren" → nimmt an KI-Tool existiert als eigenständige STL-Generierungs-Pipeline. Realität: Fable ist LLM, braucht FreeCAD MCP Middleware, teuer ($10M/$50M Tokens), liefert CadQuery-Code kein STL. | **Immer Pipeline durchdenken** bevor Prompt gebaut wird: Prompt → Modell → Middleware → Export → Print. Live-Recherche via web_search + web_extract vor Prompt-Bau. Alternativen checken. Siehe `references/fable-5-cad-evaluation-2026-07-16.md` für vollständige Analyse. |
| 10 | **Multi-Topic Vault-Files ohne Queue-Integration** → User hat 8+ Vault-Files aber keine Priorisierung | Nach N+ Vault-Files (Phase 5d-5h): **Merge in Single Queue** mit Dependency-Order (Phase 5i). "✅ HAB ICH" markieren verhindert Fehldrucke. |
| 11 | **Versteckte 200KB+ Perplexity-Outputs** im Vault die Parent-Agent nicht sieht (z.B. `I own a Bambu Lab A1 Mini...md` 210KB, oder `nerd.md` als Duplikat) — Agent arbeitet nur mit letzten 2 Files, übersieht wertvolle Sub-Reports | **Immer Vault-Inventory-Scan vor Phase 5a:** `ls -la ~/Dokumente/[Topic]/*.md` → vergleich Größe vs. Datum. Files >100KB oder mit vollem Custom-Prompt-Header checken. Großer File könnte 3-5 Sub-Reports enthalten. Siehe `references/large-source-file-extraction-2026-07-16.md` für Workflow. |
| 12 | **Tier-1-Claim ohne Live-Verification** — Perplexity gibt Download-Zahlen aus die 2-3 Wochen alt sind oder halluziniert sind | **Hard-Verification Threshold:** Jedes Tier-1 Item in Vault-File muss vor Final-Bau via `web_extract(char_limit=1500)` auf die konkrete URL live-verifiziert sein. Stat aus `web_extract` Snapshot NOT from Perplexity-Output. Konkrete Thresholds: Min. 8 von 10 Tier-1-Candidates brauchen Verified-Status. Sonst: Tier-1 zurückstufen auf Hidden-Gem und im Vault-File markieren als "needs verification". |
| 13 | **Subagent-Selbst-Verifikation reicht nicht** — Subagent markiert URLs als [VERIFIED] die nicht existieren (404). Passiert systematisch bei HF-Modell-IDs (Familien-Name vs. exakte ID) und Version-Floating (Blog-Post vs. Release). Bewiesen 2026-07-16: Subagent hatte ~17% PHANTOM-Rate trotz eigener web_extract-Verifikation. | **Parent Re-Verification Gate:** Mindestens 20% der Subagent-Claims per eigenem web_extract prüfen. Matrix bauen (PHANTOM/CONFIRMED/REDIRECT/STALE). Bei PHANTOM-Rate >10%: gesamten Output reviewen. Siehe subagent-url-verification-gate Phase 5. |

## Connected Skills

- `subagent-url-verification-gate` (Schwester-Skill, gleicher Pattern aus A1-Mini-Pass)
- `web-search` + `web-extract` (Tool-Refs)
- `delegate-task` (für Pre-Research-Phase)
- `mnemosyne-remember` (für Eval-Insights + Memory-Recovery)
- `vault-skill-derivation` (für spätere Vault-zu-Skill-Konversion)

## Memory-Recovery (kritisch für Session-Resumption)

Bei Start einer neuen Session mit Custom-Research-Task:

```python
# Pseudo-Code
if user_topic_matches_research_pattern:
    recall = mnemosyne_recall(query="Perplexity Custom-Aware research pipeline")
    if recall and recall.importance > 0.6:
        # Recovery-Hit — User hat schon mehrere Runs gemacht
        check_for_vault_inventory()  # Phase A der Large-Source-File-Extraktion
        if large_file_found:
            # Sub-Report-Container entdeckt
            invoke_large_source_file_extraction_workflow()  # siehe references/
```

**Pattern ist:** Mnemosyne-Eintrag mit Importance ≥0.6 zu "Perplexity Custom-Aware Research" triggert die Sub-Report-Container-Heuristic bevor naive Vault-Verarbeitung startet.

## Worked Example (2026-07-16, A1-Mini-Pass — Single-Topic)

**Setup:** User hat Custom-OpenSCAD-Lib für A1-Mini-Drucker. Will Druck-Recommendations.
**Generic-Prompt (Report 1):** 15 Empfehlungen, viele Duplikate mit Custom-Stack, 1 OBSOLETE nicht geflaggt
**Custom-Aware-Prompt (Report 2):** 12 Empfehlungen, 30-40% mehr Hidden-Gems (TuTu Numbered Cable Guide, 茄汁北塔 PTFE Stabilizer), 1 OBSOLETE geflaggt
**Subagent-Pre-Research:** 8/8 URLs verifiziert, Display-Name-vs-Handle-Falle dokumentiert
**Cross-Report-Diff:** Report #1 "Reduce Purge G-Code" als 12k-Hit, Report #2 "OBSOLETE" → User sparte sich Fehlinvestition
**Resultat:** 1 Vault-File (`workshop-stls-2026-07-16.md`), ~20 KB, 12 Tier-1 Picks

## Worked Example (2026-07-16, A1-Mini-Pass — Multi-Topic Pipeline)

**Dieselbe Session später:** User wollte 3 weitere Topics (Workshop II, Gaming, Nerd & Hobby).
**Pipeline:** Subagent Pre-Research (3 parallel) → 6 Perplexity Deep Research Runs (3 Context-Aware + 3 Custom-Aware) → Cross-Validation → Live Verification → Vault-File (3×) → Memory (3×) → **Queue Integration (v3)**

**Subagent-Dispatch (3 parallel, deleg_014f185e / deleg_f3aba48e / deleg_efb9c163):**
- Jeder Subagent: web_search + web_extract für ~9 URLs, Minimum 6 [VERIFIED], NO file writes
- Ergebnis: 27 URLs gescreent, 25 [VERIFIED] (92% validation rate), 2 Display-Name-Discrepancies
- Time-to-complete: ~150-173 sec pro Subagent

**8 Perplexity Reports insgesamt:**

| Report | Topic | Type | Items | Verified | 
|--------|-------|------|-------|----------|
| 1 | Workshop | Generic | 15 | 3 URLs stale |
| 2 | Workshop | Custom-Aware | 12 | 1 URL stale |
| 3 | Workshop II | Generic | 20 | 5 URLs |
| 4 | Workshop II | Custom-Aware | 15 | 4 URLs |
| 5 | Gaming | Custom-Aware | 13 | 4 URLs |
| 6 | Gaming | Fresh | 12 | 4 URLs |
| 7 | Nerd & Hobby | Custom-Aware | 9 | 3 URLs |
| 8 | Nerd & Hobby | Fresh | 12 | 4 URLs |

**Phase-Output (Dokumentiert in Memory `8d8b982271d6880d`):**

| Phase | Output | Files | Lines |
|-------|--------|-------|-------|
| 5d | 3 Vault-Files | `workshop-stls.md`, `gaming-stls.md`, `nerd-hobby-stls.md` | ~700 |
| 5e | 3 Phase-1/2/3 Proposals | Inline in Reply | — |
| 5f | Cross-Report-Diff (Fresh vs Context-Aware) | 3 Compare-Tables | ~150 |
| 5g | Dual Source 212KB → 2 extra Vault-Files | `maintenance-calibration-stls.md`, Queue v3 Update | ~530 |
| 5h | Memory-Entry with Final State | Memory `6e022e26b4c00b28` | — |
| 5i | Queue v3 (6 Phasen, 28 Prints, ~55 Std) | `druck-queue-2026-07-16.md` 17 KB | 188 |

**Key Insights aus Multi-Topic Pipeline:**
- Fresh Prompt liefert 30-40% mehr Unique Items aber auch 2× mehr Noise (Stale URLs)
- Context-Aware liefert präzise Recommendations aber findet kaum Cross-Topic-Overlaps
- Subagent-Patch-Loop: Subagent erstellt Prompt → Subagent Rev-Results patchen Prompt → User feuert → Output cross-valideren
- Live A1-Mini-Profil-Prüfung zeigte: 6/8 Top-Picks haben explizites "A1 mini" Profil
- 562 URLs im original 212KB Source-File → auf 18 Top-Picks reduziert (97% reduction rate)

## Source

Abgeleitet aus A1-Mini-Perplexity-Pass 2026-07-16 (siehe `~/Dokumente/3D-CAD/` Vault + Mnemosyne-Entries `be302754122c4e02`, `0776a2109cba86c4`)
