# Mnemosyne-Anchor-Verify Protocol — REVIDIERT 2026-07-17

**Gültig ab:** 2026-07-17
**Letzte Revision:** 2026-07-17 (Tool-Bug-Discovery — siehe self-improving Pitfall #44)
**Auslöser:** Pitfall #44 — `mnemosyne_get` liefert `not_found` für ALLE Memory-IDs, auch Queen-gesetzte. Der gesamte "Subagent hallucinates Mnemosyne-ID"-Vorwurf war 7/7 false positive.

**Wichtigste Erkenntnis:** Subagenten halluzinieren **KEINE** Mnemosyne-IDs. Das Tool `mnemosyne_get` ist **defekt** (asymmetrisch zu `mnemosyne_recall` und SQLite-Direkt-Query). Die Anker waren in 6/6 Fällen real persistiert. Verifikation muss über `mnemosyne_recall` + SQLite erfolgen, nicht über `mnemosyne_get`.

## Problem (Original)

Subagenten behaupten im Self-Report, Mnemosyne-Anker gespeichert zu haben. Diese Behauptung ist **kein Beweis** — aber nicht weil Subagenten halluzinieren, sondern weil:

1. Subagenten **KÖNNTEN** vergessen haben, `mnemosyne_remember()` aufzurufen (realistisch, aber nicht die Hauptursache)
2. `mnemosyne_get` **liefert immer not_found** — selbst für Queen-gesetzte Anker (Hauptursache, bewiesen 2026-07-17)

## Dual-Verification Workflow (Ersatz für mnemosyne_get)

Das Tool `mnemosyne_get` ist defekt — nutze STATT DESSEN:

```python
# Schritt 1: Recall mit Query auf den Content (funktioniert!)
import sqlite3

# Option A: mnemosyne_recall (empfohlen, da FTS5-Suche zuverlässig)
# Suche nach einer eindeutigen Phrase aus dem Memory-Content
# → ID sollte als Top-Treffer mit Score ≥ 0.5 kommen

# Option B: SQLite-Direkt-Query (wenn ID bekannt, sicherster Weg)
DB = os.path.expanduser("~/.hermes/mnemosyne/data/mnemosyne.db")
c = sqlite3.connect(DB)
result = c.execute("SELECT id, source, importance, content FROM memories WHERE id=?", 
                   [claimed_id]).fetchone()
if result:
    print(f"✅ Anker REAL: {result[0]} | source={result[1]} | importance={result[2]}")
else:
    print(f"❌ Anker NICHT in DB — Subagent hat wirklich nicht persistiert")
```

## Queen-Pflicht

Nach jeder Biene die `mnemosyne_remember` aufgerufen haben soll:

```python
1. Skill-File-Patch prüfen (falls Task Dateien schreiben sollte)
   → grep -n "Pitfall PLANNING-1" <datei> (oder ähnlich)
   → stat -c '%y %s' <datei> (ModTime nach Dispatch)

2. Mnemosyne-Anchor prüfen (falls Task Memory speichern sollte)
   → NICHT mnemosyne_get (kaputt)!
   → Statt dessen: mnemosyne_recall mit Query auf erste 20 Zeichen des Contents
   → ODER: SQLite-Direkt-Query (immer zuverlässig)
   
3. Getrennte Bewertung
   - Skill-Patch REAL ✅ + Anchor FAKE ❌ = PARTIAL (Patch zählt, Anchor nachtragen)
   - Skill-Patch FAKE ❌ + Anchor REAL ✅ = PARTIAL (Anchor zählt ggf.)
   - Beide real ✅ = ALL GOOD
   - Beide fake ❌ = FAIL (Subagent hat nichts gemacht)
```

## Guard für Briefings

Ab 2026-07-17 MUSS jedes Briefing das `mnemosyne_remember` erwartet enthalten:

> 1. Rufe `mnemosyne_remember` auf. Merke dir die zurückgegebene ID.
> 2. **Verifiziere** den Anker: rufe `mnemosyne_recall` auf mit einem Query das den ersten Satz deines Contents enthält. Zeige dass deine ID als Top-Treffer kommt.
> 3. **Falls Schritt 2 not_found zeigt:** versuche SQLite-Direkt-Query. Wenn auch das nichts findet, setze den Anker nochmal.
> 4. Melde im Self-Report: ID, Recall-Bestätigung (Score ≥ 0.5 ✅), und ggf. SQLite-Beweis.

**Wichtig:** Subagenten die `mnemosyne_get` nach `mnemosyne_remember` aufrufen, bekommen `not_found` — das ist (seit 2026-07-17 bekannt) ein Tool-Bug, kein Subagent-Versagen. Bewerte den Subagent nicht negativ wenn er "mnemosyne_get sagt not_found" meldet. Sage ihm stattdessen den alternativen Workflow (Recall + SQLite).

## Beleg (2026-07-17)

| Biene | Behauptete ID | mnemosyne_get | mnemosyne_recall | SQLite-Direkt | Urteil |
|-------|--------------|---------------|------------------|---------------|--------|
| A | `567c224ab0cbad45` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| B | `411ec8f8f61d4cc7` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| C | `cb638505661fe1b6` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| D | `ce9bf296c5c7719b` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| E | `8ca07f4585891dfe` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| F | `a533c92cc5a946e7` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |
| Queen-Master | `55ac752a22eeb9f8` | ❌ not_found | ✅ Top-Treffer | ✅ gefunden | **Tool-Bug, Anker real** |

**Fazit:** 7/7 Anker waren real. 0/7 Halluzination. 100% Tool-Bug.

## Cross-Reference

- `self-improving/SKILL.md` § Pitfall #44 — mnemosyne_get Tool-Bug (vollständige Beschreibung + Guard)
- `self-improving/SKILL.md` § Pitfall #36 — revidiert (Variante d zu #44 verschoben)
- `~/.hermes/docus/reports/2026-07-17-mnemosyne-get-tool-bug.md` — vollständiger Investigation-Report mit Reproduktions-Anleitung
- `software-development/better-plan-strategy/SKILL.md` — aktualisiert mit Dual-Verification statt mnemosyne_get
