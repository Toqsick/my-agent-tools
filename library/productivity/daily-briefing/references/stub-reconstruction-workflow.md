# Stub Reconstruction Workflow — Daily Note aus Stub wiederherstellen

> **Wann:** Eine Daily-Note existiert als leerer/711-Byte-Stub (Templater/Periodic-Notes erzeugt), aber die Session hat stattgefunden. Ziel: Stub durch echte Tagesdokumentation ersetzen.
>
> **Validierung:** 2026-07-13 (Basti bat um Rekonstruktion der 2026-07-07 Daily, Stub 711 Bytes → 17.7 KB Daily)

## Phasen

### Phase 1: Quellen sammeln (parallel)

```
# 1. Stub-Inhalt lesen
read_file "06 Daily Notes/2026-07-07.md"

# 2. Session-Suche — mehrere facettenreiche Queries (parallel)
session_search(query="2026-07-07", limit=3)
session_search(query="<stichwort_aus_stub>", limit=3)

# 3. Referenz-Daily finden (letzte vollständige Daily, Style-Mirror)
ls -lat "/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/" | head -5
# Letzte vollständige Daily (≥2 KB) als Style-Referenz laden
read_file ".../06 Daily Notes/2026-07-02.md"

# 4. Wiki-Link-Targets prüfen (MOC-Ordner + bestehende Notes)
ls "/home/bratan/Dokumente/Obsidian Vault/04 Bereiche/"
ls "/home/bratan/Dokumente/Obsidian Vault/05 Ressourcen/"
search_files pattern="MOC -" target="files" path="~/Dokumente/Obsidian Vault"
```

### Phase 2: Synthese

Aus den gesammelten Quellen einen kohärenten Tagesbericht bauen:

| Quelle | Liefert |
|--------|---------|
| session_search (bookend_start + bookend_end) | Was gemacht wurde, offene Punkte, Entscheidungen |
| session_search (match-window ±5) | Detail zu wichtigen Punkten |
| Referenz-Daily | Stil, Struktur, Abschnittsnamen, Tonalität |
| MOC/Glossar-Check | Valide Wiki-Links (keine Broken Links) |

**Struktur (nach Referenz-Daily):**

```
## Auf einen Blick
(1-2 Absätze Fließtext, fasst den Tag zusammen)

## Was lief
### <Thema 1>
### <Thema 2>

## Erkenntnisse
1. **...** — Erklärung
(3-6 Stück, nummeriert)

## Welche Tools konkret benutzt wurden
- **tool_name** für Beschreibung

## Wiki-Links
- [[MOC - ...]] — Beschreibung
(≥3, maximal 1 Em-Dash gesamt)

## Was Basti heute explizit gewollt hat
- Zitat → Ergebnis

## Lessons Learned
- **L1:** ... (max 5)

## Offene Punkte
- [ ] Punkt 1

## Bezug zu Vortagen
(Brücke zu gestern, vorgestern, nächste Woche)

## Mood / Energy
(1-2 Absätze Fließtext)

## Siehe auch
- [[MOC - ...]] — Beschreibung
```

### Phase 3: Schreiben

1. Vollen Inhalt als write_file schreiben (overwrite)
2. Keine Zwischenversionen — Stub komplett ersetzen

### Phase 4: Verifikation (Quality Gate)

```
F=".../06 Daily Notes/2026-07-07.md"
echo "Bytes:        $(wc -c < "$F")"        # Ziel >2000
echo "Em-Dashes:    $(grep -c '—' "$F")"    # Ziel ≤1
echo "Boldface:     $(grep -oE '\*\*[^*]+\*\*' "$F" | wc -l)"  # nur Überschriften+Codes
echo "Wiki-Links:   $(grep -oE '\[\[[^]]+\]\]' "$F" | sort -u | wc -l)"  # Ziel ≥3
echo "NegParall:    $(grep -ciP 'kein \w+ (nötig|erforderlich)' "$F")"   # Ziel 0
echo "Frontmatter:  $(head -10 "$F" | grep -cE '^(type:|date:|mood:|energy:|mode:)')"

# AI-Vokabeln prüfen
for word in crucial pivotal robust leverage seamless; do
  cnt=$(grep -oi "$word" "$F" | wc -l)
  [ "$cnt" -gt 0 ] && echo "  FOUND '$word': $cnt"
done
```

**Korrektur-Phase bei Fail:**
- Em-Dashes >1 → alle bis auf 1 ersetzen (Python/sed)
- Mid-sentence Bolds → entfernen, Satz umformulieren
- AI-Vokabeln → deutsche Alternative
- Negative-Parallelism → positive Aussage
- Wiki-Links <3 → weitere valide Targets suchen

## Pitfalls

- **session_search(limit=10) vermeiden** — 5 ist Obergrenze. Bei 10 kommen Sessions die nichts mit dem Thema zu tun haben.
- **Wiki-Links gegen reale Targets prüfen** — `grep -r "Note Name" ~/Dokumente/Obsidian\ Vault/` vor dem Link-Einbau. Sonst Broken Links.
- **Em-Dash-Regel:** MAX 1 pro Datei, nur im Wiki-Link-Bereich. Nicht in Prosa.
- **Boldface-Regel:** Nicht mid-sentence. Erlaubt: Überschriften, Code-Inline, Erkenntnis-Header (1. **Titel**), L1-L5 Codes.
- **Keine AI-Vokabeln** (crucial, pivotal, robust, leverage, seamless, ecosystem, streamline, optimize) — immer deutsche Alternativen.
- **Keine Negative-Parallelism** ("kein X nötig", "kein Y erforderlich") — sag was IST.
- **Mood/Energy als Fließtext** — nicht als "Mood: X / Energy: Y" Liste.
- **Bezug zu Vortagen konkret** — "Gestern wurde X beschlossen, heute haben wir Y daraus gemacht."
- **Offene Punkte als echte Checkliste** — `- [ ]` mit konkretem nächstem Schritt.