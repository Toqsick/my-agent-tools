# Parallel Variant — controlcenter Size-Safe Trim (2026-07-15)

## Auslöser
Basti wollte sicherstellen, dass Starter-Skripte nicht zu groß für den GreyHack `//command:` Auto-Load sind (~12 KB Soft-Limit).  
`tools/controlcenter.src` (12560 B) war das einzige Tool über dem Limit.

## User-Instruktion
> *"will halt nicht das die script zu groß für mein grayhack spiel stand sind"*
> *"macht ein genereller trimm sinn ohne mehr bug zu kreieren?"*  
> → Antwort: Nein, selektiv nur wo nötig.
> *"mach einen bug fix und speicher es parallel so das unsere version einwandfrei noch funktioniert"*  
> → Parallel-Kopie, Original unangetastet.

## Was gemacht wurde

| Datei | Bytes | Rolle |
|-------|------:|-------|
| `tools/controlcenter.src` | 12560 | Original — unverändert |
| `tools/controlcenter_size_safe.src` | 11386 | Parallel — Header-only-Trim, Runtime-Body identisch |
| `docs/CONTROLCENTER-SIZE-SAFE-PARALLEL.md` | — | Doku: Warum zwei Dateien, Deploy-Hinweis |

## Gate-Ergebnisse

| Check | Original | Size-safe |
|-------|:--------:|:---------:|
| `wc -c ≤12288` | ❌ | ✅ 11386 |
| Pattern-a (one-line-if) | 0 | 0 |
| `greybel build` | ✅ | ✅ |
| Mock: Willkommen+Menü+Beenden | ✅ | ✅ |
| Deep: Hilfe→7→Exit→0 | — | ✅ |
| Body identity (ab first `import_code`) | — | ✅ identisch |
| Snapshot original | sha256-match | ✅ |
| Recon tools still green | ✅ | ✅ |

## Wichtige Learnings
1. **Parallel-Variant > Overwrite** — nie die kanonische Datei ersetzen. Immer als Copy daneben.
2. **Body-Identity-Gate** — ab erster `import_code(`-Zeile müssen beide Dateien byte-identisch sein.
3. **Grüne Tools nie antasten** — yuno_nscan (5 KB), portscan (2.3 KB), setup (3.5 KB) bleiben unberührt.
4. **Kein genereller Repo-Trim** — Bulk-Trimming produziert Regressionen ohne Size-Gewinn.
5. **Comment-Only-Rule** — Header-Kommentare sind die einzige erlaubte Schnittstelle. Pattern-a (one-line-if) bleibt harte Grenze.

## Commit
```
77a67c8 feat(controlcenter): parallel size-safe variant under //command limit
```
Branch: `feature/starter-kit-2026-07-14` (3 ahead, auf `f72cea5`)