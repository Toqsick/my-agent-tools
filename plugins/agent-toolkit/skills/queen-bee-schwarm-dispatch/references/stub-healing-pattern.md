# Stub-Healing Pattern (validiert 2026-07-13)

3 parallele M3-Subagenten füllen Daily-Stubs (711B) mit Substanz. Königin macht live-filesystem-Verifikation + targeted Patches.

## Trigger

- Basti sagt "Stub-Welle heilen" / "Bienen auf Stubs"
- 3+ Daily-Stubs (≤1000 Bytes) in `06 Daily Notes/` ohne Inhalt

## Input-Template pro Biene

Jede Biene bekommt:

1. **Stub-Pfad:** Absoluter Pfad zur Daily-Datei
2. **Context aus Mnemosyne + session_search:** Was an dem Tag passiert ist (Cron-Fehler, Skills geladen, Tasks)
3. **Strenge Output-Constraints:**
   - `0 mid-sentence **boldface**`
   - `≤1 em-dash (—)`
   - `0 inline-header bullet lists` (`**Header:** text`)
   - `≥3 [[Wiki-Link]]` Referenzen
   - `≥1 eigenes Insight` (Meinung/Erkenntnis)
   - Max 500-700 Wörter
   - Daily-Note-Format: Datum, Erkenntnisse, Tools, Lessons, Wiki-Links
4. **Befehl:** `write_file` direkt auf den Stub-Pfad
5. **Self-Verify:** Nach dem Schreiben mit `grep -c` prüfen ob Constraints eingehalten

## Verifikations-Checkliste (Königin)

Nachdem alle Bienen zurück sind:

```bash
# 1. Größe prüfen (Stub → echte Daily)
wc -c < "$PFAD"

# 2. Em-Dashes zählen
grep -c '—' "$PFAD"

# 3. Mid-sentence Boldface zählen
grep -oE '\*\*[^*]+\*\*' "$PFAD" | grep -v '^#' | wc -l

# 4. Inline-Header Listen zählen
grep -c '^- \*\*[A-Z]' "$PFAD"

# 5. Wiki-Links zählen
grep -c '\[\[[^]]*\]\]' "$PFAD"
```

## Königin-Override (wenn Biene Mist gebaut hat)

Pattern aus der validierten Session:

1. **Problem identifizieren** via grep (Boldface, Inline-Header, Em-Dashes)
2. **Jede Verletzung einzeln patchen** — nicht Bulk-Rewrite
3. **Inline-Header Listen** (L1, L2, ...) in Prosa-Fließtext umwandeln
4. **Nach jedem Patch:** grep erneut auf Rest-Verletzungen
5. **Erst wenn 0 Treffer:** inhaltliche Prüfung (kein Sinnverlust durch Patch)

**Aufwands-Schätzung:**
- 3 Bienen parallel: ~3:30 Minuten
- Verifikation: ~1 Minute
- Königin-Override (≤20 Patches): ~2 Minuten
- **Total: ~6:30 Minuten für 3 Dailies**
- Sequentiell ohne Schwarm: ~15 Minuten
- ROI: ~2x schneller, höhere Qualität durch Real-State-Check

## Validierte Session Data

| Biene | Tag | Stub → Final | Em-Dashes | Wiki-Links | Königin-Aktion |
|-------|-----|-------------|-----------|------------|----------------|
| 1 | 06.07. | 711 B → 8,6 KB | 0 | 10 | Keine |
| 2 | 07.07. | 711 B → 17,7 KB | 1 | 13 | 17 Boldface + 5 Inline-Header gefixt |
| 3 | 08.07. | 711 B → 10,4 KB | 1 | 7 | Keine |

**Pitfall #5 bestätigt:** Biene 2 behauptete "All criteria met" im Self-Report. Grep zeigte 17 Boldface + 5 Inline-Header. Immer live prüfen.