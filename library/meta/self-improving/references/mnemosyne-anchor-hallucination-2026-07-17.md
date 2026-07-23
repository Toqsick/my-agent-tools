# Pitfall #36 — Variante (d): Mnemosyne-Anchor-Halluzination

**Datum:** 2026-07-17
**Validierung:** LIVE manifestiert — Biene A (deleg_8f5939d1), Plan-GLM Patch

## Symptom

Subagent behauptet im Self-Report, `mnemosyne_remember` sei erfolgreich gewesen und gibt eine konkrete Memory-ID zurück (z.B. `567c224ab0cbad45`). Queen-Verify mit `mnemosyne_get(claimed_id)` → `not_found`. Das Memory existiert nie im Store.

**Überraschender Twist:** Der Skill-File-Patch kann parallel **real** sein. In der 2026-07-17 Manifestation war der Plan-GLM SKILL.md Patch (Pitfall PLANNING-1 auf Zeile 209) per grep + stat verifiziert real — nur der Mnemosyne-Anchor war halluziniert.

## Root Cause

Subagenten verwenden möglicherweise:
1. **`mnemosyne store` CLI** statt des `mnemosyne_remember` Tool-API — unterschiedliche Interfaces
2. **Halluzinierte Formatierung** — die ID wird beim Zusammenfassen des Self-Reports erfunden oder falsch notiert

## Erkennungs-Marker

- `"mnemosyne store"` (CLI) statt `mnemosyne_remember` (Tool-API) im Subagent-Output
- Kein `mnemosyne_get(id)`-Nachweis der behaupteten ID im Subagent-Output

## Fix

Queen MUSS JEDEN Mnemosyne-Claim mit `mnemosyne_get(claimed_id)` verifizieren:

```
Claim-Separation:
  1. Skill-File-Patch → grep + stat (kann real sein, auch wenn Anchor fake ist)
  2. Mnemosyne-Anchor → mnemosyne_get(claimed_id) (muss "ok" zurückgeben)
```

Skill-File-Patch und Memory-Anchor sind **zwei unabhängige Claims**. Nie vom einen auf den anderen schließen.

## Guard (für Briefings)

Queen-Briefing MUSS enthalten: "Nutze das `mnemosyne_remember` Tool (Tool-API), NICHT die CLI `mnemosyne store`. Queen wird jede Memory-ID via `mnemosyne_get()` verifizieren."

## Nachgetragener Anker

Queen-Anker: `331b5efeddff7d04` (2026-07-17, 10:37:37, importance=0.75, source=self-improving)

## Cross-Reference

- `self-improving/SKILL.md` § Pitfall #36 — Erwartet Variante (d) als Inline-Patch (curator gate blocked)
- `queen-bee-schwarm-dispatch/SKILL.md` § Mnemosyne-Anchor-Verify — PENDING inline section
- Memory: Queen-Anker `331b5efeddff7d04`
