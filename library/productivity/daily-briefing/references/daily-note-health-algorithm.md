# Daily-Note-Health Detection Algorithm

**Stand:** 2026-07-16 (Multi-Marker-Strategie)
**Script:** `~/.hermes/scripts/daily-note-health.py`
**Tests:** `~/.hermes/scripts/test_daily_note_health.py`

## Problem

Daily Notes im Obsidian Vault (`~/Dokumente/Obsidian Vault/06 Daily Notes/`) haben
flexible Section-Header-Namen. Die alte Logik suchte exakt `## Was lief` und verfehlte
damit Varianten wie `## Was lief (vermutet aus Mnemosyne-Recall)` — ein realer
Regression-Fall vom 2026-07-03.

## Lösung: Multi-Marker-Strategie

Statt eines fixen Section-Namens werden 5 Marker gegen jeden `## `-Header
geprüft (case-insensitive substring match). Die erste Section deren Header
einen Marker **als Substring enthält** UND **echten Content hat**, gilt als
"echter Inhalt" → HEALTHY.

### Marker-Liste

| Marker | Header-Beispiele (alle gefunden im Real-Vault) |
|--------|------------------------------------------------|
| `was lief` | `## Was lief`, `## Was lief (vermutet aus Mnemosyne-Recall)`, `## Was lief am 2026-07-04` |
| `erkenntnisse` | `## Erkenntnisse` (alternativer Abschnitt ohne "Was lief") |
| `lessons learned` | `## Lessons Learned` (englische Variante) |
| `hauptaufgaben` | `## Hauptaufgaben` |
| `hauptphase` | `## Hauptphase` (aus Templater-Vorlage) |

### Erkennungslogik

```
1. Finde alle re.MULTILINE-Matches auf ^##\s+(.+)$
2. Für jeden gefundenen Header (case-insensitive):
   a. Prüfe ob Header einen der 5 Marker als Substring enthält
   b. Extrahiere Body: von Header-Ende bis zum nächsten ## oder EOF
   c. Prüfe ob Body echten Content hat (nicht nur Whitespace/Newlines)
3. Gib erste Match (Header, Body) zurück
4. Kein Match → ("", "") → PARTIAL/STUB
```

### Edge Cases (alle durch Real-Vault-Daten belegt)

| Fall | Beispiel | Erwartung | Realer Datum |
|------|----------|-----------|--------------|
| Annotation-Variante | `## Was lief (vermutet aus Mnemosyne-Recall)` | HEALTHY (Regression 2026-07-03) | 2026-07-03 |
| Annotation-Variante 2 | `## Was lief am 2026-07-04` | HEALTHY | 2026-07-04 |
| Alternativer Marker | `## Erkenntnisse` (kein "Was lief") | HEALTHY | via Template-Test |
| Emoji-Prefix, kein Marker | `## 🌙 20:00-Addendum: TikTok-Business` | PARTIAL (kein Marker matcht) | 2026-07-16 |
| Leerer Hauptteil, große Datei | 3348 Bytes, aber nur Addenda mit Inhalt | PARTIAL (nicht HEALTHY) | 2026-07-16 |
| Kleine Datei, echter Inhalt | <1000 Bytes aber gefüllte "Was lief"-Section | HEALTHY (Größe irrelevant) | ruhiger Tag |
| Hauptphase aus Templater | `## Hauptphase` von Vorlage generiert | HEALTHY | 2026-07-15 |

## Script-Architektur

```
~/.hermes/scripts/daily-note-health.py
├── DAILY_LOG_MARKERS          # Liste der 5 Marker
├── STUB_SIZE_THRESHOLD = 1000 # Bytes-Schwelle
├── _extract_any_section_with_content(content) → (str, str)  # Multi-Marker
├── _extract_section(content, section_name) → str             # (unverändert, legacy)
├── _has_real_content(section_text) → bool
├── classify_daily_note(daily_dir) → DailyNoteResult
│   ├── Datei existiert? → MISSING
│   ├── Größe < 1000 und kein Content? → STUB
│   ├── Multi-Marker matched? → HEALTHY
│   └── Sonst: Größe < 1000 → STUB, sonst PARTIAL
└── CLI: --date, --json, --help
```

## Test-Konstanten und ihre Intention

Die Test-Edge-Cases in `test_daily_note_health.py`:

| Konstante | Testet | Regression |
|-----------|--------|------------|
| `TEMPLATE_CONTENT` | Leeres Template → STUB | Basis-Fall |
| `PARTIAL_CONTENT` | Addenda ohne Hauptinhalt → PARTIAL | 2026-07-16 |
| `HEALTHY_CONTENT` | Normale "Was lief"-Section → HEALTHY | Basis-Fall |
| `SMALL_REAL_CONTENT` | <1000 Bytes mit Inhalt → HEALTHY | Ruhiger Tag |
| `ANNOTATION_HEALTHY_CONTENT` | "Was lief (vermutet aus ...)" → HEALTHY | **2026-07-03 Regression** |
| `ERKENNTNISSE_HEALTHY_CONTENT` | "## Erkenntnisse" → HEALTHY | Alternativer Marker |
| `NO_MARKER_PARTIAL_CONTENT` | Emoji-Header ohne Marker → PARTIAL | 2026-07-16 Emoji-Fallback |

## Real-Vault Smoke-Testing

Nach Code-Änderungen immer mit REALEN Daily-Notes testen — die Test-Konstanten
decken nur bekannte Edge-Cases ab, aber der Vault hat Überraschungen.

```bash
# Alle relevanten Daten aus dem Vault testen
for d in 2026-07-16 2026-07-15 2026-07-03 2026-07-13 2026-07-04; do
  python3 ~/.hermes/scripts/daily-note-health.py --date "$d"
done
```

Letzter bekannter guter Stand (2026-07-16, nach Multi-Marker-Refactor):

| Datum | Status | Größe | Marker |
|-------|--------|-------|--------|
| 2026-07-16 | PARTIAL | 3348B | (kein Marker — Addenda only) |
| 2026-07-15 | HEALTHY | 7365B | hauptphase |
| 2026-07-03 | HEALTHY | 4946B | was lief (annotation) |
| 2026-07-13 | HEALTHY | 16918B | was lief |
| 2026-07-04 | HEALTHY | 3113B | was lief (annotation) |

## Verwandte Skills

- `daily-briefing` → §0.9 (Session-Start Gate, Reminder-Verhalten)
- `obsidian-vault-quality-audit` → Pattern 8 Thin-Notes-Detection (andere Metrik)
- `self-improving` — wenn das Script selbst einen Bug produziert hat
