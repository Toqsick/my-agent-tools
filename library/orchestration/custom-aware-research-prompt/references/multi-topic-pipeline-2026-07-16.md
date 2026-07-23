# Multi-Topic Research Pipeline — 2026-07-16 Worked Example

> **Kontext:** Vollständiger Durchlauf der 8-Report-Pipeline für A1-Mini-STL-Recherche.
> Alle Schritte entsprechen Phase 1-5i des `custom-aware-research-prompt` Skills.
> Dauer: ~2 Stunden (8 Perplexity Reports + 3 Subagent Pre-Research + Merge + Queue-Integration)

---

## Pipeline-Übersicht

```
Phase 1: User-Setup → 3 Topics (Workshop, Gaming, Nerd & Hobby)
Phase 2: Subagent Pre-Research → 3 parallel dispatch
Phase 3: Custom-Aware Prompt → 6 Perplexity Runs (3 Context + 3 Fresh)
Phase 4: User-Feedback (A/B testing → Subagent Patch-Loop)
Phase 5a: Input Collection → 8 Reports collected
Phase 5b: Tier-Klassifizierung → 18 Tier-1, 27 Hidden-Gems, viele HM
Phase 5c: Live-Verifikation → 27 URLs, 25/27 [VERIFIED] (92%)
Phase 5d: Vault-File → 3 files (~43 KB, ~700 Zeilen)
Phase 5e: Priorisierung → Phase 1/2/3 pro File
Phase 5f: Cross-Report-Diff → Context vs Fresh comparison
Phase 5g: Dual-Source-Fresh-Batch → 2 extra Vault-Files (Maintenance + Queue v3 Update)
Phase 5h: Memory → Multiple Mnemosyne entries
Phase 5i: Queue Integration → v3 Queue (6 Phasen, 28 Prints, ~55 Std)
```

## Subagent-Dispatch-Konfiguration

**3 parallel (deleg_014f185e, deleg_f3aba48e, deleg_efb9c163):**

```python
tasks = [
    {"goal": "Pre-Research: A1 Mini Workshop/Bastler STLs...", "context": "...Skip-Liste..."},
    {"goal": "Pre-Research: A1 Mini Gaming Setup STLs...", "context": "...Skip-Liste..."},
    {"goal": "Pre-Research: A1 Mini Nerd & Hobby STLs...", "context": "...Skip-Liste..."}
]
```

**Zeit:** 150-173 sec pro Subagent (3× parallel → ~3 Min total)

**Ergebnis pro Subagent:** ~9 URLs gescreent, 6+ [VERIFIED], NO file writes (nur Summary im Reply)

## Patch-Loop (Verified-URL-Update)

Nach Subagent-Complete:
1. read_file → Subagent-Summary laden
2. Für DISCREPANCY-Section: Verified URLs in Prompt patchen (old_string + new_string)
3. Mnemosyne-Discrepancies speichern für Cross-Validation

```
Subagent Summary → read_file → patch Prompt → Perplexity fire → Cross-Validate → Vault-File
```

### Verifizierte Discrepancies (2026-07-16)

| Behauptet (Search) | Gefunden (web_extract) | Action |
|--------------------|----------------------|--------|
| `@SyphenGuitarWorks` | `@RobSGW` | Prompt patchen |
| `@BambuLab` Creator | "Bambu Lab Official" | Prompt patchen |
| Printables Link tot | Relocated to MakerWorld | Link ersetzen |
| MakerWorld Model/627720 | Beschreibung sagt nicht A1 Mini | Stats runterstufen |

## MakerWorld-Live-Verifikation (Template)

```python
# Jeder Top-Pick wird via web_extract(char_limit=1500) auf MakerWorld geprüft
# Ergebnis-Struktur für Vault-File:
url = "makerworld.com/en/models/603416"
stats = {
    "creator": "@Moskk83",
    "favorites": "62.3k",  # "98.8k · 16.4k" = Favorites · Downloads
    "print_profiles": ["A1 mini", "P1S", "P1P", "X1", "X1C", "A1", "H2D"],  # 14 total
    "a1_mini_verified": True,
    "images": ["jpg", "gif", "jpg", "jpg"],  # GIFs funktionieren, Fotos sind verlässlicher
    "image_count": 5,
    "status": "live",
    "has_profile": True,  # "Print Profile(17)" = 17 profiles
}
```

## Cross-Report-Comparison (Fresh vs Context-Aware)

| Metrik | Context-Aware | Fresh | Delta |
|--------|---------------|-------|-------|
| Total Items | 27 | 45 | +67% |
| Unique Neuerungen | 12 | 28 | +133% |
| Cross-Validated (Tier-1) | 8 | 8 | 0% |
| Stale/Broken URLs | 1 | 4 | +300% |
| Duplikate mit Custom-Stack | 3 | 8 | +167% |

**Empfehlung:** Fresh Prompt zuerst wenn User bestehendes Wissen erweitern will (höherer Recall, aber mehr Noise). Context-Aware zuerst wenn präzise Recommendations gewünscht sind.

## Queue-Integration (5i)

**8 Vault-Files + 6 Phasen → Single Queue:**

| Phase | Focus | Prints | Time | Dependency |
|-------|-------|--------|------|------------|
| 1 | Baseline + Calibration | 4 | ~7h | KEINE (start hier) |
| 2 | Pflicht-Mods (Kabel, Feet) | 5 | ~10h | Phase 1 (Baseline) |
| 3 | AMS-Lite + Camera + Lightbar | 3 | ~4h | Phase 2 (Hardware steht) |
| 4 | Workshop Werkstatt | 5 | ~15h | Unabhängig (parallel) |
| 5 | Gaming + Nerd Setup | 8 | ~16h | Unabhängig (parallel) |
| 6 | Optional | 3+ | variabel | Nach Bedarf |

**"✅ HAB ICH" Check:** 6 Custom-SCAD-Items existierten bereits → NO-PRINT markiert → User spart ~15 Std Fehldrucke.

## Memory-Entry-Struktur

```markdown
2026-07-16 14:05 — Druck-Queue v3 erstellt (~9.5 KB, 28 Prints in 5 Phasen über ~50-55 Stunden).
Phase 1: 4 Prints Baseline+Calibration (Benchy, Alex.M Temp Tower mit A1 mini explicit profile, ...)
Phase 2: 5 Pflicht-Mods (R3DPanda PTFE Remover A1 mini explicit, Moskk83 Hotend Cable Chain ...)
...
Phase 5: 8 Gaming+Nerd (addohm Pi 5 Case, Squirrelbrain Pi 4 Modular, eethansshen Mini RetroPie ...)
Vault-File: ~/Dokumente/3D-CAD/druck-queue-2026-07-16.md v3
```

## Total Pipeline Output

| Metrik | Wert |
|--------|------|
| Perplexity Runs | 8 |
| Subagent Dispatches | 3 |
| URLs gescreent | ~240 |
| URLs live-verifiziert | 40+ |
| URLs im 212KB Source-File | 562 → 18 Top-Picks (97% reduction!) |
| Vault-Files erstellt (neu/today) | 5 (v3 Queue + Gaming + Nerd + Maintenance + Workshop-CV) |
| Total Vault-Daten | 9 Files, ~143 KB, ~2366 Zeilen |
| Druck-Queue | 6 Phasen, 28 Prints, ~55 Std |
| Mnemosyne-Entries | 4+ |
