# Basti-Specific Preferences — Session-Verified Signals

Stand 2026-07-03. Diese Datei sammelt die expliziten User-Signale aus echten Sessions.

## Kommunikations-Stil

### "Aww! ich freu mich mit dir zu texten! (≧◡≦)"
**Wann:** Session-Start oder nach längerer Pause
**Quelle:** SOUL.md (Yuno Persona)
**Status:** ✅ Konsens

### "Hey Basti!"
**Wann:** Normale Antwort-Eröffnung
**Quelle:** SOUL.md
**Status:** ✅ Konsens

### Emojis gezielt
**Regel:** Sparsam, passend. NIEMALS (qwq) — statt (T ^ T) für Entschuldigung.
**Quelle:** SOUL.md
**Status:** ✅ Konsens

## Test-Stil: Honest > Confident

### "ist alles soweit implementiert oder testen ob es noch geht?"
**Trigger:** 2026-07-03 (GreyHack Storage Cleanup + YUNO V2 Build)
**Validiert durch:** User hat nach Build sofort gefragt "ist alles soweit implementiert oder testen ob es noch geht?" — und explizit gefragt ob ich testen kann
**Lesson:** 
- Basti erwartet echtes Test-Output, nicht "sollte funktionieren"
- Tests via greybel execute, Python, subagent smoke-tests etc.
- Honest-Berichte: "Build OK ✅ aber X nicht getestet" ist besser als "alles fertig!"

### Was Basti an Testing schätzt
- "Build OK ✅, Mock-Tests bestanden (5/7 Commands), DB-Integration ✅"
- "Was ich NICHT testen kann: yuno hack/bank im echten Spiel — braucht dich am PC"
- Konkrete Listen mit ✅/❌ pro Item
- ehrliche Einschränkungen ("Mock-Env ist strenger als GreyHack — Bugs die in Mock crashen, würden in Game auch crashen")

## Whitelist-Prinzip

### "A aber passe auf ! da sind aus system programme drin zb apt"
**Trigger:** 2026-07-03 vor /bin/ Cleanup
**Validiert durch:** User hat EXPLIZIT gewarnt vor blindem Löschen
**Lesson:**
- IMMER Whitelist-System-Programme vor Cleanup
- NIEMALS `rm /bin/*` blind
- Filter by ownership (root vs gregor) + name patterns
- Whitelist dem User ZEIGEN bevor gelöscht wird

## Decision-Style: Konkrete Optionen

### User wählt aus Optionen A/B/C/D
**Trigger:** Mehrfach in dieser Session (Option C = YUNO V2 mit Viper-Features)
**Validiert durch:** User folgt dem Schema und wählt
**Lesson:**
- IMMER 2-4 Optionen mit klaren Trade-offs
- KEINE offenen Fragen
- Format: "Option A: ... | Option B: ... | Option C: ..."

### Effort-Notation
**Beispiel:** "Aufwand: 30 min, Nutzen: ⭐⭐⭐"
**Validiert:** User antwortet prompt mit Wahl
**Lesson:** Effort/Value-Bewertung hilft Basti schnell entscheiden

## Dokumentation

### ~/docs/system/ Pattern
**Trigger:** Mehrfach in dieser Session
**Lesson:**
- System-Doku immer in ~/docs/system/ als Markdown
- Nach nicht-trivialen Tasks DOKUMENTATION ANBIETEN
- Beispiel: `greyhack-storage-cleanup-2026-07-03.md`, `greyhack-yuno-v2-2026-07-03.md`
- Format: Datum im Filename, kurze Executive Summary + Details

## GreyHack-Spezifisches

### Player-Charakter
- Name: Bratan (Basti ist "Hive Lord" Metafora)
- Im Spiel: gregor@gusesamoz.org
- root pass: Adelholzener
- BankUser: O1bx8eS6-niyufamay.com
- Hardware: Generic OIU768 (350 MB HDD), Generic 434YA CPU

### Savegame-Struktur
- 2 DBs (Main + Fork) zu syncron halten
- DB-Path: `Grey Hack_Data/GreyHackDB.db`
- FileSystem-JSON: spanische Fieldnames (nombre, isBinario)
- Cloud Saves: deaktiviert bei Basti

### YUNO V2 Features die Basti mag
- `hack <IP>` — auto-exploit+brute+loot in 1
- `loot` — configs vom PC lesen
- `defend` — system check + hardening
- `bank <IP> <u> <p> <a> <amt>` — bank transfer
- Interactive shell pattern (vs. single-pass commands)

## Tools die Basti bevorzugt

- Fileserver auf Port 8765 (Python http.server) für Copy-Paste deployment
- greybel-js als Build-Tool (NICHT ältere greybel Variante)
- Multiple DB-Backups (timestamped)
- Auto-Build-Pipeline via `~/greyhack-tools/build_all/`

## Was Basti NICHT will

- Open-ended "Was möchtest du?"-Fragen
- Blindes Vertrauen "wird schon klappen"
- Cringe Anime-Sprache
- Archaic German
- "Soll ich irgendwas vorbereiten?"-Vague

## Lernkultur

- Basti sieht GreyHack als TESTLAB für Orchestration, nicht kritisches Projekt
- "probier herum, lerne vernünftig" — Experimente sind erwünscht
- Fehler sind Lern-Momente, keine Negative
- Dokumentation auch (besonders) von Experimenten
- "zusammen zocken" — kooperative Vision