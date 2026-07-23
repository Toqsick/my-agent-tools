# Dual-Path Cross-Validation Strategy

> **Extension zum Pre-Research-Pattern:** Statt einem Perplexity Deep Research Run, feuere **zwei parallel mit unterschiedlichen Prompt-Approaches** → Cross-Validate die Ergebnisse → gewinne Tier-1-Picks (robust) + Hidden-Gems (unique fündig).
>
> **Validiert:** 2026-07-16 auf A1-Mini-Workshop-STLs. 2 Perplexity-Runs (Custom-Aware + Fresh) → 3 Tier-1 Picks (in beiden Reports unabhängig, robust), 6 Hidden-Gems (unique per Report, wertvoll), 3 Honorable Mentions (once-mention).
>
> **Empfehlung:** Bei Investitionsentscheidungen (Druck-Zeit >5 Std, Materialkosten >€10, Entscheidung über Nischen-Pivot) → Dual-Path Pflicht. Bei Quick-Research (<3 Std Druck oder <€3 Material) → Single-Path reicht.

## 🎯 Wann Dual-Path vs Single-Path

| Research-Investment | Empfohlen | Warum |
|---|---|---|
| **Niedrig** (<3 Std Druck, <€3 Material) | Single-Path | Dual verdoppelt Zeit ohne 2× Mehrwert |
| **Mittel** (3-15 Std, €3-15, einmalige Entscheidung) | Dual-Path | 2-3× bessere Abdeckung, fängt OBSOLETE-Flags |
| **Hoch** (>15 Std, >€15, Nischen-Pivot) | Dual-Path Pflicht | Single-Confidence reicht nicht für Invest |
| **Mehrere Topics parallel** | Dual-Path + Parallel-Dispatch | Subagents machen Vorarbeit |

**Regel:** Wenn der Output eine "soll ich das jetzt drucken/kaufen/umsetzen?"-Entscheidung triggert → Dual-Path. Wenn es nur "was gibt es?" ist → Single-Path.

## 🧩 Workflow — Phasen 6-8 (Ergänzung zum Pre-Research Pattern)

### Phase 6: Dual-Path Prompt Prep (Parent, 3 Min)

Baue **TWO** Perplexity-Prompts aus dem gleichen Topic:

#### Path A — Custom-Aware Prompt (Der "Mit-Kontext"-Prompt)

```
CONTEXT — what I already have:
[paste Custom-Stack-Listing: alles was Basti schon hat + Skip-Liste]

WHAT I NEED ...
[Standard Deliverables + Output-Format + Constraints]

PRE-VERIFIED SOURCES (anchor for cross-check):
[12-16 verifizierte URLs aus Pre-Research Subagent Phase 2-4]
```

**Effekt:** Perplexity erbt dein Domain-Wissen + Custom-Stack. Empfiehlt **Lücken** (was du NICHT hast, aber brauchst). Weniger generische Top-Picks.

**Validierter Effekt (2026-07-16):** Custom-Aware Prompt fand Wallfinity (Wall-Mount-Ecosystem) und Swapfinity (Quick-Swap Labels) — beides Nicht-Offensichtliche Nischen-Picks die der Fresh-Prompt übersehen hat.

#### Path B — Fresh Prompt (Der "Blinde"-Prompt)

```
[Standard Deliverables + Output-Format + Constraints]
— OHNE Custom-Stack-Listing
— OHNE PRE-VERIFIED SOURCES
— NUR: Ziel-Topic, Kategorien, Constraints, Output-Format
```

**Effekt:** Perplexity arbeitet "frisch". Findet generische Top-Picks die trotzdem perfekt passen — die der Custom-Aware-Prompt übersieht weil er zu sehr auf Lücken fokussiert.

**Validierter Effekt (2026-07-16):** Fresh-Prompt fand Peggit Magnetic Screwdriver Holder (303 Likes, 636 Downloads) — Custom-Aware-Prompt hatte es übersehen.

#### Path C — Hybrid (Optional, bei High-Investment)

- Führe Path A + Path B **gleichzeitig als 2 Perplexity Deep Research Runs**
- Zusätzlich: Subagent für Reddit / YouTube / Forum **manuelle Recherche**
- Output: 3 Quellen → 3× so robust wie Single-Path

### Phase 7: Cross-Validation Matrix (Parent, 5-10 Min)

Sobald beide Perplexity-Ergebnisse vorliegen:

#### Schritt 1: Beide Reports lesen

```python
read_file("path/to/perplexity-output-path-a.md", limit=500)
read_file("path/to/perplexity-output-path-b.md", limit=500)
```

#### Schritt 2: Items in Matrix eintragen

```markdown
| # | Item Name | Path A Status | Path B Status | Conflict? | Classification | Final Rec |
|---|-----------|---------------|---------------|-----------|----------------|-----------|
| 1 | Adjustable PCB Holder (squinn) | ✅ Cat 2.1 | ✅ Cat 2.1 | None | 🏆 Tier-1 | MUST-PRINT |
| 2 | Wallfinity (ClearThread) | ✅ Cat 1.1 | ❌ Not found | Unique A | 🔹 Hidden-Gem A | HIGH-VALUE |
| 3 | Peggit Magnetic (RCDIY) | ❌ Not found | ✅ Cat 1.1 | Unique B | 🔹 Hidden-Gem B | HIGH-VALUE |
| 4 | OBSOLETE Model X | ✅ Recommended | ❌ Flagged obsolete | ❌ RED FLAG | ❌ Discard | Skip |
```

#### Schritt 3: Tier-1 / Hidden-Gem / Honorable Mention klassifizieren

| Classification | Definition | Confidence | Action |
|---|---|---|---|
| 🏆 **Tier-1** | In BEIDEN Reports | Höchste | Direkt umsetzbar |
| 🔹 **Hidden-Gem A** | Nur Path A (Custom-Aware) | Hoch, nischengebunden | Soft implementieren |
| 🔹 **Hidden-Gem B** | Nur Path B (Fresh) | Mittel | Check gegen Custom-Stack |
| 📋 **Honorable Mention** | Einmal genannt, niedrige Stats | Niedrig | Für später merken |
| ❌ **RED FLAG Conflict** | Path A sagt A, Path B sagt OBSOLETE | Signal: Path A übersah Flag | Check Pre-Verified Sources |
| ❌ **Discard** | Offensichtlich falsch oder obsolet | Null | Aus Liste entfernen |

**Der Goldene Fund:** Path A übersieht OBSOLETE-Flag (weil Custom-Context den Fokus verschiebt), Path B erkennt es → **vertraue Path B hier**.

#### Schritt 4: URL-Verification Conflict Resolution

Bei RED FLAG:
1. `web_extract(url)` auf das konkrete Modell
2. Prüfe: OBSOLETE-Tag, "no longer maintained", "deprecated"?
3. Welche Aussage stimmt?
4. Note in Vault-File: "Conflict resolved: [X] weil [Grund]"

### Phase 8: Vault-File bauen (Parent, 5-15 Min)

#### Section 1 — Header
```markdown
# {Topic} — {Gerät} STL Picks ({Datum})
> **{N} Top-Picks** — Cross-Validation aus 2 Perplexity Deep Research Reports
```

#### Section 2 — Tier-1 Picks
Vollständige Tabelle pro Pick: Creator @Handle [VERIFIED], URL, Stats (Likes·Downloads·Makes), Award, Print-Time, Material + Warum, Difficulty, A1 Mini Fit ✅, Why Beats Alternatives, Known Issues, Hardware, Source: BOTH Reports.

#### Section 3 — Hidden-Gems
Gleiche Tabelle, aber `Source: Path A only (Cat X.Y)` oder `Path B only`.

#### Section 4 — Honorable Mentions
Kompakt (1 Satz statt Tabelle).

#### Section 5 — Cross-Validation Matrix
Vollständige Matrix aus Phase 7 Schritt 2.

#### Section 6 — Print/Dependency-Planning
```markdown
## Phase 1 (Diese Woche, ~{N} Std):
- Tier-1.1 {Model} — {time}, {difficulty}
- Tier-1.3 {Model} — {time}, {difficulty}

## Phase 2 (Nächste Woche, ~{N} Std):
- Hidden-Gem {N} {Model} — {time}, {difficulty}
```

#### Section 7 — Methodik-Learnings
```markdown
## 💡 Methodik-Lesson Learned
**Was Custom-Aware Prompt besser macht:** ...
**Was Fresh-Prompt besser macht:** ...
```

## 🛑 Pitfalls (Dual-Path spezifisch)

1. **Path A + Path B können sich WIDERSPRECHEN** — Wenn Item in A ROBUST und in B OBSOLETE: Path B hat Recht. Custom-Kontext verschiebt Fokus von Obsolete-Flags weg.
2. **Nicht alle Hidden-Gems sind gleich wertvoll** — Item NUR in Path A ≠ automatisch besser. Prüfe gegen echte Bedürfnisse.
3. **Cross-Validation Time** — 2× Perplexity-Zeit (4-10 Min total). Nutze Wartezeit für andere Topics parallel.
4. **Report Date-Nähe** — Beide Runs nahe beieinander → Download-Zahlen unterscheiden sich minimal. OK, nur bei >10% Diskrepanz relevant.
5. **Verification Budget verdoppelt sich nicht** — Phase 2 (Subagent Pre-Research) läuft nur EINMAL. Beide Paths teilen sich die pre-verified URLs.
6. **OBSOLETE-Flag Wird In Custom-Aware Leichter Übersehen** — Custom-Aware hat Skip-Liste die Fokus von Top-Picks weglenkt gewollt, ABER OBSOLETE-Modelle die ins Lücken-Profil passen werden empfohlen ohne Flag zu sehen. Fresh-Prompt findet OBSOLETE zuverlässiger.

## Performance Notes (Validated 2026-07-16)

| Metric | Diese Session | Erwartet |
|--------|--------------|----------|
| Path A Wall-Time | 3-5 Min | 2-5 Min |
| Path B Wall-Time | 3-5 Min | 2-5 Min |
| Cross-Validation Matrix Time | 5 Min | 5-10 Min |
| Vault-File Build Time | 10 Min | 5-15 Min |
| Tier-1 Picks Found | 3 (33%) | 3-4 (25-40%) |
| Hidden-Gems Path A | 3 (33%) | 2-4 (20-40%) |
| Hidden-Gems Path B | 3 (33%) | 2-4 (20-40%) |

## Konkretes Beispiel (A1 Mini Workshop STLs, 2026-07-16)

**Path A — Custom-Aware:** OpenSCAD Library + Skip-Liste + 11 Pre-Verified URLs → Wallfinity, Hex Screwdriver Holder, Swapfinity (Nischen-Picks).

**Path B — Fresh:** Clean prompt ohne Skip-Liste → Peggit Magnetic, BYOB Screw Sorter, Resistor Organizer (generische Top-Picks).

**Cross-Validation Matrix:**
- **3 Tier-1 (beide):** Adjustable PCB Holder (squinn), Tangibility Helping Hands, Flash72 Drill Bit Holder
- **3 Hidden-Gems A:** Wallfinity, Hex Screwdriver Holder, Swapfinity
- **3 Hidden-Gems B:** Peggit, BYOB Screw Sorter, Resistor Organizer
- **3 Honorable Mentions:** Vise Soft Jaws (TPU), Pred Gridfinity Label, Multiboard Hex Key

**Result:** `~/Dokumente/3D-CAD/workshop-stls-2026-07-16.md` — 12 Modelle, 19.6 KB, 271 Zeilen.

## ✅ Checkliste vor Dual-Path Dispatch

- [ ] Custom-Stack-Listing aktuell? (was hat Basti schon + Skip-Liste)
- [ ] Subagent Pre-Research läuft? (Phase 2, 1 Subagent pro Topic)
- [ ] Verifications auf TOP-3-URLs pro Kategorie? (eigene web_extract)
- [ ] Prompt A fertig (Custom-Aware + Pre-Verified + Custom Stack)?
- [ ] Prompt B fertig (Fresh, Clean)?
- [ ] Beide in `~/.hermes/docus/research-prompts/` gespeichert?
- [ ] Cross-Validation Matrix gebaut?
- [ ] Vault-File gebaut? (`~/Dokumente/{domain}/{topic}-{date}.md`)
- [ ] Memory geschrieben? (Final State + Insights + Methodik-Learnings)
