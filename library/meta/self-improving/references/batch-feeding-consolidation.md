# Batch-Feeding Consolidation — 69→25 Dedup & Welle 1→2 Timing

> **Eingesetzt:** 2026-07-07 (6-Bee-Schwarm, 9 Sessions, 7 Tage)
> **Ergebnis:** 69 Roh-Lessons → 25 Mnemosyne-Einträge (36% Yield)

## Das Kernproblem

Subagenten (Bienen) extrahieren Rohmaterial — viele Lessons, unterschiedliche
Qualität, teils redundant. Die Königin muss daraus **hochwertige, deduplizierte
Mnemosyne-Einträge** machen, **bevor alle Bienen zurück sind**.

## Der Consolidation-Flow

```
Welle 1 (3 Bienen) ──→ Erste Results ──→ Konsolidierung 1 ──→ Mnemosyne Batch 1
Welle 2 (2-3 Bienen) ──→ Spätere Results ──→ Konsolidierung 2 ──→ Mnemosyne Batch 2
                                                      ↓
                                            Final Report + Skill-Promote
```

### Phase A: Pre-Consolidation (sobald erste Biene zurück)

1. **Ergebnisse auslesen** — `read_file(<OUTPUT_PATH>)` auf jede zurückgekehrte Biene
2. **Raw-Count erfassen** — wieviele Lesson-Blöcke (Pattern: `### [DATUM]`)
3. **Deduplizieren** — gleicher Root Cause → detailliertere Version behalten
4. **Priorisieren** — `verified` > `hypothese`, hohe Importance > niedrige

**Wichtig:** Nicht auf alle Bienen warten! Die ersten ~60% der Ergebnisse
sind meist die wertvollsten. Konsolidiere im Flug.

### Phase B: Mnemosyne-Feeding (Batch-Strategie)

Jeder Batch = 5 `mnemosyne_remember`-Calls parallel.

**Batch-Plan für 25 Lessons:**
- Batch 1: Top 5 (höchste Importance, verified)
- Batch 2: Nächste 5 (verified, wichtige Kategorie)
- Batch 3: Nächste 5 (verified, gemischt)
- Batch 4: Nächste 5 (verified, niedrigere Importance)
- Batch 5: Letzte 5 (hypothese, niedrigste Importance)

**Batch-Struktur (Template für jeden Eintrag):**
```python
mnemosyne_remember(
    content=f"""
    ### [YYYY-MM-DD] <Kurztitel>
    - Symptom: <was sichtbar war>
    - Root Cause: <die eigentliche Ursache>
    - Fix: <der konkrete Befehl / die Änderung>
    - Guard: <wie künftig vermieden>
    - Status: verified | hypothese
    """.strip(),
    importance=0.7,  # 0.7-0.9 für verified, 0.3-0.5 für hypothese
    source="self-improving",
    veracity="verified",  # oder "inferred"
    metadata={
        "tags": ["self-improving-lesson", "<domain>", "<kategorie>", "verified"],
        "status": "verified",
        "category": "<tool-quirk | build-error | workflow | orchestration | hardware>",
    },
    scope="global",
)
```

### Phase C: Yield-Optimierung

**Faustregeln aus der Praxis (2026-07-07):**

| Roh-Lessons | Nach Dedup | Yield | Wann stop? |
|---|---|---|---|
| 69 | 25 | 36% | Wenn die letzten 5 nur noch "hypothese" oder niedrige Importance sind |

**Dedup-Kriterien (in Reihenfolge):**
1. **Exakter Root Cause** → älteren/dünneren Eintrag verwerfen
2. **90% ähnlicher Fix** → konkatenieren mit `|` (seltene Alternative)
3. **Selbe Session, selbe Fehlerfamilie** → Meta-Lesson statt mehrerer Einträge

**Stop-Kriterium:** Wenn die nächste Batch nur noch Einträge mit
`importance < 0.5` hat → abbrechen. Die verbleibenden sind Rauschen,
nicht Signale.

**Yield-Treiber 2026-07-07:**
1. **W1-A (Bug-Hunt):** 22 Roh → 6 Top-Lessons (größter Treiber)
2. **W1-B (Gaming):** 17 Roh → 5 Top-Lessons
3. **W1-C (System/Hardware):** 17 Roh → 4 Top-Lessons
4. **W1-D (Orchestrierung):** 13 Roh → 3 Top-Lessons (höchste Dedup-Rate, weil viele Workflow-Lektionen)
5. **W2-E + W2-F:** ~7 Roh → 7 (noch nicht dedupliziert — liefen später)

### Phase D: Welle 1→2 Timing

**Das Timing-Problem:** Welle 2 läuft noch während du Welle 1 konsolidierst.

**Lösung: Konsolidiere während du wartest**

```
Welle 1 zurück ──→ Konsolidierung Phase A-C ──→ Mnemosyne Batch 1
                                            ↓
                                    [Warte auf Welle 2]
                                            ↓
Welle 2 zurück ──→ Konsolidierung Phase A-C ──→ Mnemosyne Batch 2
                                            ↓
                              Final Report + Skill-Promote-Check
```

**Erfahrung 2026-07-07:**
- Welle 1 (4 Bienen): ~20-30 Min bis alle zurück
- Konsolidierung 1 (Phase A-C, 4 Bienen): ~10 Min
- Wartezeit auf Welle 2: ~5-15 Min
- Konsolidierung 2 (Phase A-C, 2 Bienen): ~3 Min
- Total: ~40-50 Min bis Final Report

### Phase E: Final Report

Nachdem alle Bienen konsolidiert sind:

```
## 📊 <KATEGORIE> — <Anzahl> Lessons

| Kategorie | # | Top-Finding |
|---|---|---|
| <category> | N | <bester Fund> |

## Schwarm-Statistik
| Biene | Lessons | Quelle |
|---|---|---|
| W1-A | N | <Session> |
| Total | N | |

## Noch ausstehend
| Biene | Status | Was fehlt |
|---|---|---|
| <Name> | 🔄 | <was> |

## Yield
- Roh-Lessons: N
- Nach Dedup: N
- Yield: N%
```

## Gespeichert wurden 2026-07-07 pro Kategorie

| Kategorie | # | Höchste Importance |
|---|---|---|
| build-error | 5 | 0.9 (one-line-if 40×) |
| hardware | 5 | 0.9 (GRUB lowlatency, Flatpak DXVK) |
| cron/telegram | 5 | 0.9 (Provider-Drift #44585) |
| orchestration | 4 | 0.9 (Subagent Silent Truncation) |
| tool-quirk | 3 | 0.85 (Cloudflare TLS-Fingerprint) |
| workflow | 3 | 0.8 (hermes config race, Mnemosyne 3-Safety) |

## Was AVOIDED wurde

- ❌ **Keine Environment-Failures** (fehlende Binaries, apt-Errors)
- ❌ **Keine negativen Tool-Claims** (nicht "X tool kaputt", sondern Fix dokumentiert)
- ❌ **Keine One-off Task Narratives** (PR-spezifische Details ausgefiltert)
- ❌ **Keine doppelten Einträge** (gleiche Lesson aus verschiedenen Sessions → dedupliziert)
- ❌ **Keine Hypothese >0.7 Importance** (Hypothesen bleiben ≤0.5, werden vom Cronjob gecleaned)
