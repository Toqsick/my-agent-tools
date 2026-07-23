# Vault Improvement Bundling (Research → Plan → Gate)

> **Cross-phase pattern for vault proposals.** Instead of asking "was soll ich tun?", present 3 concrete packages with effort estimates, risks, and outcomes. The user picks a package and you implement.

## Trigger Conditions

- "Was noch rein sollte?" / "Großes Research für Vault"
- "Next phase plan?" / "Vision für Vault"
- "Research, dann paper, dann Gate und Ausführung"

## Step 1: Ground-Truth Recon (Critical)

Advisory voices — including multi-voice self-review ("Advisor-Stimmen", "Rater") — can hallucinate factual claims about vault state. **Always run ground-truth verification before acting on any voice claim.**

**Checklist (mandatory run BEFORE analysis):**
```bash
# Verify plugin system exists
cat <vault>/.obsidian/community-plugins.json 2>/dev/null || echo "MISSING: blockiert alle Plugin-Installationen"
ls <vault>/.obsidian/plugins/ 2>/dev/null || echo "MISSING: plugins/ existiert nicht"

# Verify key structural files
wc -l <vault>/05\ Ressourcen/Glossar.md 2>/dev/null || echo "Glossar fehlt"
grep baseSize <vault>/.obsidian/graph.json 2>/dev/null || echo "Kein baseSize in graph.json (expected)"

# Check for stray files/backups in vault root
find <vault> -maxdepth 1 -name '*.backup*' -type d 2>/dev/null
find <vault> -maxdepth 1 -name '*.md' -size 0 2>/dev/null
ls <vault>/08\ Anhaenge/ 2>/dev/null || echo "08 Anhaenge/ === Geist-Ordner (nur _README.md)"
```

**Proven false positives (2026-07-05):**
| Voice claim | Ground truth | Risk |
|---|---|---|
| "Glossar fehlt / zu kurz" | ✅ 265 Zeilen, 18.4 KB, ~95% linked | Duplikat-Glossar |
| "`baseSize: 12` — absurd" | ✅ Kein baseSize-Key, `nodeSizeMultiplier: 0.8` | Phantom-Config-Jagd |
| "Graph-Farben alle schwarz" | ✅ 16 colorGroups mit RGB-Werten | Doppelte Arbeit |
| "08 Anhaenge/ fehlt" | ✅ Existiert (leer: nur _README) | Falsche Problemstellung |

**Why this happens:** Multi-voice self-review loads each voice's reasoning context with your current working context. If your context has uncertainties or gaps, the voices fill them with best-guess content. The voices don't know what you haven't told them.

## Step 2: 3-Package Sizing Model

Always size vault improvements into these 3 tiers:

| Package | Effort | Risk | Typical Scope |
|---|---|---|---|
| **A — Minimal-Cleanup** | ~30 min | 🔵 Niedrig | Plugins aktivieren, Stubs entfernen, Backups quarantänen |
| **B — Standard-Visualisierung** | ~90 min | 🟡 Mittel | A + Style Settings, Folder-Farben, Sub-Strukturen, Templater |
| **C — Full-Send-Vision** | ~3-4 h | 🟠 Mittel-Hoch | A+B + Canvas-Files, Dashboard, CHANGELOG, MOC-Erweiterungen |

**Decision format:** Present as `1 / 2 / 3` or `A / B / C` to the user. Include 1 sub-question if needed (e.g., "Backups quarantänieren? ja/nein"). Every package has 1-2 Obsidian restarts.

## Step 3: Gate Before Implementation

Send the user a brief inline summary (not a paper):
1. **Ist-Zustand** — 1-2 lines (notes count, plugin status, visual state)
2. **Findings** — 3-5 bullets, only from verified ground-truth
3. **Packages** — A/B/C with effort + risk
4. **1 sub-question** — e.g. "Backups quarantänieren?"

Wait for the user's response before ANY file edit.