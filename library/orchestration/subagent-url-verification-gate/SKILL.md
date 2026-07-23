---
name: subagent-url-verification-gate
description: >-
  Use when user asks for verifying URLs before making recommendations, cross-checking more than five external sources, validating user-supplied links, or assigning confidence levels to source-backed picks. NOT for recommendations with no external links or treating subagent claims as final proof. Batches URL extraction, checks identities and source consistency, scores evidence, and requires parent re-verification before publication.
trigger-words:
- url-verification
- web-extract
- verified-anchor
- hallucination-gate
- recommendation-gate
- pre-research
- url-check
- fact-check
version: 1.1.0
key-changes-v1.1.0: 'Added Phase 5 (Parent Re-Verification Gate) — Subagent self-verification
  is not sufficient. Added Pitfall #9 about phantom URLs. Added references/phantom-url-pattern-2026-07-16.md.'
author: Yuno
category: orchestration
lane: koenigin
license: MIT
trigger_keywords: ['user', 'before', 'recommendations', 'external', 'links']
keywords: ['user', 'before', 'recommendations', 'external', 'links']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Subagent URL Verification Gate

Verifiziert URLs durch **Subagent-gesteuerte `web_extract`-Calls** bevor User-facing Empfehlungen ausgesprochen werden. Verhindert Halluzinationen bei STL-Recherche, Forum-Thread-Empfehlungen, YouTube-Links, GitHub-Issues und anderen external sources.

## Wann diesen Skill laden

Trigger-Bedingungen:
- User fragt "Was sind die besten..." und es kommen Recommender-Tasks (Top-Prints, Top-LLMs, Best-Practices)
- User hat externe Quellen zitiert und du sollst sie verifizieren
- Mehrere URLs (>5) sollen cross-verifiziert werden
- User hat skeptische Attitude gegen AI-Halluzinationen (default für Basti)

NICHT für: Single-URL-Quick-Check (web_extract reicht direkt), vertrauenswürdige offizielle Docs (Bambu Wiki, GitHub official repos — direkt zitieren), oder wenn der User explizit "gib mir was du hast" sagt ohne Verifikations-Anforderung.

## Kern-Prinzipien

### 1. web_extract als Quality-Gate vor Empfehlung
Jede URL die du empfehlen willst, MUSS durch `web_extract` oder direkten `curl`/Browser-Call bestätigt sein. Pattern:

```
web_extract → URL
  ↓
  Existiert? Title matched?
  ↓ ja ↓                       ↓ nein ↓
[VERIFIED] tag anhängen     URL streichen oder alternativen suchen
```

### 2. Verifikations-Quote als Schwelle
Setze eine **Quote-Schwelle** für deine eigene Confidence:
- **100% required:** bei Recommendations die User $$$ kosten
- **80% required:** bei Tech-Stack-Empfehlungen (Default)
- **50% required:** bei generischer Exploration (z.B. "Was gibt's auf MakerWorld zu A1 Mini?")

### 3. Display-Name ≠ Handle-Falle
Externe Plattformen zeigen Display-Namen statt Creator-Handles:
- **MakerWorld:** "TuTu" ≠ `@yujixun` (creator-handle), `model/1686183` ist die stabile ID
- **GitHub:** "SoftFever" ≠ `@softfever` (User-Handle)
- **Reddit:** "u/teachingtech" vs Display-Name "Teaching Tech"
- **YouTube:** Channel-Name vs @handle

**Immer per Model/Resource-ID verifizieren**, nicht per Creator-Handle.

### 4. Subagent-Parallelisierung für Skalierung
Bei >10 URLs:
- **1 Subagent pro Topic-Cluster** (3-5 URLs pro Subagent)
- **Parallel dispatchen** (delegation max_concurrent_children=6)
- **Subagent liefert Summary in Reply, schreibt KEINE Files** (verhindert Vault-Spam)
- **Verified-Liste als Anchor** im finalen Output

### 5. Cross-Source-Konsistenz-Check
Falls URL aus mehreren Quellen zitiert wird (Perplexity + Subagent + eigene Suche):
- Konsens über mehrere Pfade = hoher Confidence
- Single-Source = niedriger Confidence → explizit flaggen
- Konflikt zwischen Sources = OBSOLETE-Check (kann sein dass Modell outdated ist)

## Workflow (6 Phasen)

### Phase 1: URL-Liste sammeln
Sammle alle URLs aus Quellen:
- Perplexity-Output
- User-Eingabe
- Eigene web_search-Resultate
- Mnemosyne-Recall (alte Session-Daten)

Format: `(URL, claimed-title, claimed-source)` Tripel.

### Phase 2: Verifikations-Batch
Batch URLs nach Topic-Cluster. Pro Cluster:
```python
# Pseudo-code für Subagent-Prompt
subagent_prompt = f"""
Verify {N} URLs for topic '{topic}'.
For EACH: use web_extract, confirm title + topic matches expected.
Mark [VERIFIED] if confirmed, [UNVERIFIED] if blocked.
For UNVERIFIED: suggest alternative URL or note absence.
Return summary in reply only — NO file writes.
"""
```

**Timeout:** 2-5 Min pro Subagent (für 5-8 URLs).

### Phase 3: Eval-Matrix bauen
Pro URL drei Spalten:

| Status | Kriterium | Action |
|--------|-----------|--------|
| **VERIFIED** | web_extract confirmed title + topic | Direkt empfehlen mit Confidence |
| **PLAUSIBLE** | URL pattern valid aber blocked/wrong-content | Alternativen suchen oder mit Caveat nennen |
| **OBSOLETE/INVALID** | Topic outdated oder URL falsch | Streichen, OBSOLETE-Marker |
| **HALLUZINATION** | URL-Format invalid / nicht-existente Resource | Streichen + Note für User |

### Phase 4: Output mit Confidence-Levels
Im finalen Output:
- **Verified-Liste** als Anchor (was du live bestätigt hast)
- **Plausible-Liste** mit Caveats ("based on Perplexity but not live-verified")
- **Streicher** explizit dokumentieren ("OBSOLETE: Reduce Purge G-Code is native in Bambu Studio now")
- **Confidence-Quote** angeben ("10/10 verifiziert = 100%")

### Phase 5: Parent Re-Verification Gate (CRITICAL — Subagent Self-Verification ist nicht genug)

Subagent-Claims sind **self-reports**, keine verifizierten Fakten. Subagenten können URLs als `[VERIFIED]` markieren die **tatsächlich 404/not found** sind — passiert systematisch bei Model-Repository-Recherche (HF-Modell-IDs, GitHub-Repos).

**Deshalb: Parent re-verifiziert eine Stichprobe BEVOR der Output den User erreicht.**

#### Workflow

1. **Anteil der Subagent-Outputs parent-verifizieren:**
   - **≥20% der subagent-claims** (min 2 URLs) per eigenem `web_extract` checken
   - **Fokus:** Die *wichtigsten* Empfehlungen + ungewöhnliche Funde (Hidden Gems)
   - **Nicht:** Alle URLs nochmal checken — das macht den Subagent obsolet

2. **Verifikations-Ergebnis-Matrix bauen:**

   ```
   | URL | Subagent Claim | Parent Check | Status |
   |-----|---------------|--------------|--------|
   | huggingface.co/.../Qwen3-Coder-7B | [VERIFIED] | 404 NOT FOUND | ❌ PHANTOM |
   | huggingface.co/.../Granite-4.0-7B | [VERIFIED] | 404 NOT FOUND | ❌ PHANTOM |
   | huggingface.co/Qwen3-Coder-Next | [VERIFIED] | 200 OK, SWE-Bench 70.6 | ✅ CONFIRMED |
   ```

3. **Klassifikation:**

   | Parent-Check-Ergebnis | Bedeutung | Aktion |
   |---|---|---|
   | **PHANTOM** | URL existiert nicht, Subagent halluziniert | **Streichen**, korrekte URL recherchieren, in Memory notieren |
   | **REDIRECT** | URL leitet weiter (z.B. HF-Modell umbenannt) | Korrekte URL dokumentieren, Subagent war fast richtig |
   | **CONFIRMED** | URL existiert, Titel/Inhalt matcht | Confidence erhöhen |
   | **STALE** | URL existiert aber Inhalt ist veraltet | OBSOLETE-Marker, Empfehlung zurückstufen |

4. **Wenn PHANTOM-Rate > 10%:** Subagent-Output kompletten Review unterziehen. **Nicht blind vertrauen.** Subagent-Halluzinationen sind Cluster-Bugs — wenn einer falsch ist, sind meist mehrere falsch.

5. **Memory-Update nach Parent Gate:**
   - Nur CONFIRMED URLs + korrigierte PHANTOM URLs speichern
   - Schlagwort: `subagent-phantom-urls` + konkretes Datum
   - Veracity: `tool` (eigenhändig via web_extract verifiziert)
   - Scope: `global` (Pattern für alle Future-Sessions)

#### Warum Subagent Self-Verification nicht reicht

Subagenten bestätigen URLs aus mehreren Gründen fälschlich:

- **Familien-Namen vs. exakte Modell-IDs:** Subagent weiß dass "Qwen3-Coder-7B" in der Qwen3-Coder-Familie existiert (es gibt `Qwen3-Coder-Next`, `Qwen3-Coder-30B-A3B`), rät die exakte ID (`Qwen3-Coder-7B` existiert nicht)
- **Gedächtnis-Halluzination:** Subagent "erinnert" sich an ein HF-Modell oder GitHub-Repo das nie existierte
- **Version-Floating:** Subagent kennt `granite-4.0-7B` aus Blog-posts (IBM kündigte Granite 4.0 an), aber das **tatsächliche Release** war `granite-4.1-8b` (andere Nummer, andere Größe)
- **web_extract Grenze:** Subagent hat 404-Seite gelesen aber Titel-Check war zu lax ("HuggingFace 404 page" wurde nicht als Fehler erkannt)

**Bewiesen 2026-07-16 (Ornith-Modell-Vergleich):** Subagent lieferte 10/12 URLs als `[VERIFIED]`. Parent re-verified 3 URLs → 2 waren PHANTOM (404). Subagent's Selbst-Verifikation versagte bei 20% der getesteten URLs. Siehe `references/phantom-url-pattern-2026-07-16.md`.

### Phase 6: Post-Verification — Patch-Loop ins Prompt (Brücke zu custom-aware-research-prompt)

Nachdem URLs verifiziert sind (Phase 1-4): **Results in das zugehörige Prompt patchen** bevor der User es feuert.

**Workflow:**
1. Subagent complete → `read_file` oder Reply Summary laden
2. Verified-URLs in DISCREPANCY-Section des Prompts notieren
3. `patch(old_string=placeholder_URL, new_string=[VERIFIED]_URL)` → Prompt aktualisieren
4. Mnemosyne-Discrepancies speichern (für Cross-Validation nach Perplexity-Run)

**Patch-Loop-Beispiel (2026-07-16):**
```
Subagent sagt: @SyphenGuitarWorks → LIVE zeigt: @RobSGW
→ patch in prompt: "SyphenGuitarWorks" → "@RobSGW"
→ User feuert Perplexity mit korrigiertem Prompt
→ Cross-Validation zeigt: Perplexity OUTPUT korrekt (weil Prompt es wusste)
```

**Nur patchen bei Discrepancies:** Wenn Subagent 9/9 URLs bestätigt ohne Fehler → Skip Patch-Loop, direkt zu Custom-Aware-Prompt-Formulierung.

**Pro-Tipp:** old_string muss unique genug sein für `patch(replace_all=false)`. Nutze `---` oder `|` als Anchor im Prompt-Template.

**Verbindung:** Dieses Pattern ist dokumentiert im Schwester-Skill `custom-aware-research-prompt` → `references/multi-topic-pipeline-2026-07-16.md`.

## Pitfalls (5+)

| # | Pitfall | Mitigation |
|---|---------|-----------|
| 1 | URL blind aus Perplexity übernehmen ohne `web_extract` | **Immer** web_extract als Gate vor Empfehlung |
| 2 | Display-Name als @Handle verwenden → User kann Handle nicht finden | **Model-ID vor Creator-Handle** in Output-Format |
| 3 | Subagent schreibt Files → Vault-Spam | Subagent-Prompt: "Return summary in reply only, NO file writes" |
| 4 | Verifikations-Quote zu niedrig (30%) → User mit Halluzinationen zugemüllt | Mindestens **50% Verified-Quote** vor User-Facing-Output |
| 5 | Cross-Source-Konflikt nicht geflaggt → User kriegt OBSOLETE-Empfehlung | **Konflikte explizit dokumentieren** ("Report 1 vs Report 2 differ on...") |
| 6 | `web_extract` truncated bei langen Pages → Title-Check unzuverlässig | Head + Tail truncation ist OK; Topic muss in ersten 500 chars matchen |
| 7 | Subagent-Subagent-Chain (Halluzination-Propagation) | Max 1 Subagent-Hop, keine nested delegation für URL-Checks |
| 8 | YouTube-Videos als Quelle ohne Thumbnail-Check | youtube.com/watch?v= Pattern reicht für Existence-Check, Content-Check nicht möglich — explizit flaggen |
| 9 | **Subagent claims [VERIFIED] bei nicht-existenter URL** — Subagent bestätigt URL via `web_extract` aber übersieht 404-Seite (Titel "HuggingFace 404" wird nicht als Fehler erkannt). Subagent markiert URL als grün → Parent vertraut blind. | **Parent Re-Verification Gate (Phase 5):** Mindestens 20% der Subagent-Claims per eigenem `web_extract` prüfen. Matrix bauen (📋). Bei PHANTOM-Rate >10%: gesamten Subagent-Output reviewen. Besonders gefährdet: HF-Modell-IDs (Familien-Name ≠ exakte ID) und Version-Floating (Blog-Post sagt "Granite 4.0", Release war "Granite 4.1"). Bewiesen 2026-07-16: Subagent hatte 20% PHANTOM-Rate. |

## Connected Skills

- `custom-aware-research-prompt` (Schwester-Skill, baut die Prompts die diese Gate nutzen)
- `delegate-task` (für Subagent-Parallelisierung)
- `web-extract`, `web-search` (Tool-Refs)
- `tech-fact-check` (für einzelne Fakten)
- `mnemosyne-remember` (für reusable URL-Patterns)

## Worked Example (2026-07-16, A1-Mini-Pass)

**Subagent-Run 1 (Filament):** 12 URLs geliefert, 6 mit `web_extract` verifiziert → 50% Quote (Schwelle erreicht)
**Subagent-Run 2 (Troubleshooting):** 14 URLs, 8 verifiziert → 57% Quote
**Subagent-Run 3 (AMS-Lite):** 16 URLs, 8 verifiziert → 50% Quote

**Discrepanz gefunden:** Perplexity zitierte SyphenGuitarWorks als Creator-Handle für MakerWorld model/1310652. Echter Handle ist `@RobSGW`. Suche per Handle hätte nichts gefunden; Suche per Model-ID 1310652 funktionierte.

**Cross-Report-Diff gefangen:** Report #1 verkaufte "Reduce Purge G-Code" (Leon Fisher-Skipper) als 12.100-Downloads-Hit. Report #2 zeigte "OBSOLETE" im Titel → Workaround ist nativ in Bambu Studio ("Long retraction when cut").

## Source

Abgeleitet aus A1-Mini-Perplexity-Pass 2026-07-16 (siehe `~/Dokumente/3D-CAD/` Vault + Mnemosyne-Entries `be302754122c4e02`, `0776a2109cba86c4`)
