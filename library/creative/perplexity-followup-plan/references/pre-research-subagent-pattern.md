# Pre-Research Subagent Dispatch Pattern

> **Klassen-Level Pattern:** Bevor du einen Perplexity Deep Research Prompt an den User lieferst, dispatche PARALLELE Subagents für PRE-RESEARCH + URL-VERIFIKATION. Die verifizierten URLs werden als PRE-VERIFIED SOURCES in den Prompt integriert. Das reduziert Halluzinationen, halbiert Nachbearbeitungszeit und liefert bessere Perplexity-Resultate.
>
> **Validiert:** 3 Topics parallel (Filament Bible 12 URLs ✅, Troubleshooting Playbook 14 URLs ✅, AMS-Lite — pending) in 144–158s pro Subagent.
>
> **Alternative ohne Subagents:** Wenn Perplexity auf ein bereits gut recherchiertes Thema zielt (Standard-TikTok-Nischen-Check, Standard-Brand-Audit) und die Top-5-Quellen aus vorherigen Sessions bekannt sind → lade das letzte `references/pre-research-*.md` als Template und überspringe die Subagent-Dispatch-Phase.

## Trigger

Dieses Pattern aktivieren wenn:

1. **Basti sagt:** "mach Perplexity zu [neuem Topic]" (besonders bei topics die URL-heavy sind: STL/Modelle, Tools, Filamente, API-Dokumentation)
2. **Topic hat URL-Risiko:** Wenn Perplexity STL-Links, MakerWorld-URLs, Tool-Downloads, PDF-Sources oder @Handles zitieren soll → IMMER pre-research
3. **Topic hat DISPLAY-NAME-Risiko (Pitfall #14):** Creator Display Names ≠ @Handles → Subagents müssen Model-ID (URL-Pfad-ID) statt Display-Name identifizieren
4. **Multiple Reports geplant:** Wenn Phase A + B + C (Folgefragen) → pre-research für ALLE gleichzeitig, nicht nacheinander

**Überspringen wenn:** Einfache Faktenfrage (keine URL-Zitation nötig) → direkter Prompt reicht.

## Workflow

### Phase 1: Custom-Aware Prompt bauen (Parent, 5 Min)

1. Standard `perplexity-followup-plan` Prompt-Template laden
2. Custom-Stack-Listing (Block 3) füllen — liste ALLES was Basti schon hat, mit explizitem "Skip this" für Perplexity
3. Deliverables + Output-Format + Constraints aus dem Template
4. Prompt als Markdown in `~/.hermes/docus/research-prompts/perplexity-prompt-{topic}-{date}.md` speichern

### Phase 2: Pre-Research Subagents DISPATCH (Parent, 1 Min)

Parallel dispatch via `delegate_task(tasks=[...])` — **immer 3 topics gleichzeitig** wenn mehrere Perplexity-Runs geplant sind.

**Briefing-Template (copy-paste):**

```text
Goal: Pre-research for [TOPIC]. Find and verify live URLs for [N] categories. NO file writes — return only a structured summary in your reply.

You need:
[List specific categories + number of URLs needed per category]

For EACH URL returned, give me:
- The exact URL
- Title visible at that URL
- 1-sentence snippet / relevance
- Publication year
- Source category (forum, wiki, YouTube, MakerWorld, brand site, etc.)
- A1-Mini specific? (yes/no/partial)

VERIFICATION REQUIREMENT:
For at least [60%] of the URLs returned, you MUST use web_extract to confirm the URL resolves to live content with the expected topic. State "[VERIFIED]" next to those. Rest can be search-suggested.

Constraints:
- [year range] strongly preferred
- [DACH/EU/local availability]
- No marketing copy, no paid reviews
- Source diversity (not all Reddit, not all MakerWorld)

Output format: markdown table per category, then a "VERIFIED" index at end. Keep under [2000] words.
```

**Role:** `leaf` (kein weiteres Delegatin nötig — reine Recherche)
**Tools:** web_search + web_extract automatisch verfügbar

### Phase 3: Outputs konsolidieren (Parent, 2 Min per Subagent)

Nach Subagent-Complete:

1. **Read full output from cache file** — die Delegation-Rückgabe enthält einen Pfad und einen truncated Summary. Rufe `read_file(path=..., offset=...)` auf um den Mittelteil zu laden (Pitfall #7). Bei 3+ parallel dispatches: lies ALLE Cache-Files bevor du mit Phase 3 beginnst.

2. **Verification confidence check** — subagent claims "[VERIFIED]" sind self-reports. Für die TOP-3-URLs pro Kategorie:
   - `web_extract(url)` selbst aufrufen um zu bestätigen
   - Nur wenn dein eigener web_extract-Call ✅ → mark as "PARENT-VERIFIED"

3. **Cross-check gegen Cross-Report-Diff (Pitfall #15):** Wenn mehrere Subagents zum selben Topic gelaufen sind, erstelle eine Matrix:

```
| Item | Subagent A Status | Subagent B Status | Conflict? |
|------|-------------------|-------------------|-----------|
| URL X | VERIFIED ✅ | VERIFIED ✅ | None |
| URL Y | VERIFIED ✅ | OBSOLETE ❌ | RED FLAG |
```

3. **PRE-VERIFIED SOURCES Block** in den Prompt einbauen:

```markdown
---

## ✅ PRE-VERIFIED SOURCES (via Subagent Pre-Research)

> Diese [N] URLs wurden VOR dem Perplexity-Run live verifiziert (Hermes `web_extract` auf jede Seite). Nutze sie als **Primary Research Anchor** — du brauchst sie nicht selbst nochmal zu suchen.

[URL tables per category, with VERIFIED tags]
```

4. **Stale placeholder cleanup (2026-07-16 refinement):** Nachdem du den PRE-VERIFIED SOURCES Block eingebaut hast, suche im Prompt nach dem **alten** Platzhalter-Block (z.B. `## ✅ PRE-VERIFIED SOURCES (von Yuno via Subagent — läuft gerade)` mit "ETA ~3-5 Min" Text). Entferne ihn vollständig — sonst hat der Prompt einen doppelten PRE-VERIFIED-Sektion-Footer. Vor dem finalen Prompt: lies `tail -5` der Datei um zu bestätigen dass nur EIN PRE-VERIFIED Block existiert.

### Phase 4: Prompt feuern (User)

User kopiert den Prompt (ohne die PRE-VERIFIED SOURCES Sektion — die ist nur für Cross-Check nach Perplexity-Ergebnis) in Perplexity → Deep Research.

### Phase 5: Post-Perplexity Evaluation (Parent, Awaits User)

Sobald der User die Perplexity-Antwort zurückgibt:

1. **Diff gegen PRE-VERIFIED SOURCES:** Welche URLs stimmen überein? Welche sind neu? Welche sind von Perplexity halluziniert?
2. **3-Stufen-Evaluierung** anwenden (aus Haupt-SKILL.md)
3. In Vault mergen (`~/Dokumente/{vault-path}/...`)

## Pitfalls

1. **Subagent-Claims sind SELF-REPORTS** — Ein Subagent der "[VERIFIED]" sagt, hat web_extract AUFGERUFEN, aber du hast nicht selbst gesehen ob der Request 200 oder 404 war. **Regel:** Vertraue, aber verifiziere — ruf die TOP-3-URLs selbst mit web_extract auf.
2. **Subagent-Timeout ≠ Fehler** — Subagents haben 120s Default. Bei 3+ URLs + web_extract pro URL kann es eng werden. Briefing: "Keep under 2000 words" + URL-Budget von 60% verification, 40% search-suggested einplanen.
3. **Display Name ≠ @Handle (Pitfall #14)** — Subagents fallen in dieselbe Falle wie Perplexity. Im Briefing EXPLIZIT sagen: "Extract BOTH display name AND @handle if visible on the page. If unsure, return the Model-ID (URL path) instead."
4. **Reddit blockt web_extract** — Subagents können Reddit-URLs nicht mit web_extract verifizieren (Reddit blockt scraping). Im Briefing sagen: "Reddit URLs = search-suggested fallback, mark as (unverified inline)."
5. **MakerWorld Download-Count ≠ Print-Count (Pitfall #12)** — Subagents in 3D-Druck-Kontext briefing: "Use likes + collections + comments as signal, NOT download count. Check if the model has 'OBSOLETE' or 'no longer maintained' tags anywhere on the page."
6. **Cross-Profile-Awareness** — Wenn Subagents eine Memory-DB aus einem anderen Hermes-Profil laden, können sie veraltete Informationen haben. Briefing: "Ignore any profile-specific context. Start fresh with web_search + web_extract only."
7. **Subagent-Antwort-Truncation** — Bei langen Subagent-Antworten (>8k chars) wird der Mittelteil getrimmt. Lese IMMER `read_file` auf dem Cache-Pfad den die Delegation-Rückgabe zeigt, bevor du die URLs als final markierst.

## Performance Notes

| Metric | This session (2026-07-16) | Typical |
|--------|--------------------------|---------|
| Subagent Wall-Time (3 parallel) | 144–158s (2.4–2.6 Min) | 2–5 Min |
| URLs per Subagent | 12–14 | 6–16 |
| Verification Rate | 85–100% (10–14/14) | 60–80% |
| Parent Verification Overhead | ~3 Min pro Run | 2–5 Min |
| Value Add (vs. direct Perplexity-only) | 2× faster eval, 0 halluzinierte URLs caught | — |

## Beispiel aus 2026-07-16

### Filament-Bible Pre-Research (deleg_ead99728, 144s)

- **Goal:** 12 URLs für 4 Filament-Kategorien (PLA/PETG/TPU/Mixing)
- **Verification:** 12/12 URLs per web_extract bestätigt
- **Conflict caught:** Perplexity Report #1 listet "Reduce purge by up to 45%" (Skipper) als Top-Print. Subagent pre-research + Report #2 zeigen: **OBSOLETE** (seit 2024 nativ in Bambu Studio). Cross-Report-Diff verhindert Fehlempfehlung.
- **Pitfall #14 caught:** Perplexity sagt "TuTu (@TuTu)" — Live-MakerWorld zeigt @yujixun. Model-ID `model/493268` identifiziert korrekt.

### Troubleshooting Pre-Research (deleg_2a8e33b8, 158s)

- **Goal:** 14 URLs für 10 Failure-Modes + YouTube + Wiki + Reddit
- **Verification:** 14/14 per web_extract bestätigt (100%)
- **Unique find:** Firmware 01.06.00.00 regression thread — 2.8k views, Perplexity hätte es ohne pre-research nicht in dieser Tiefe gefunden.
- **Source diversity achieved:** 3 Bambu Wiki + 6 Bambu Forum + 1 Reddit + 4 YouTube
