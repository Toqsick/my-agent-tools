# Polymorphic Polish Pattern

**Systematic 4-Phase methodology for skill library maintenance.**
Emerged from 4 Polish Rounds on 2026-07-15 (30+ edge tests, 25 BOM migrations, 59 chmod fixes, 8 duplicate removals, 1 meta-skill built).

## The Core Loop

```
┌──────────────────────────────────────────────────────────┐
│  1. SCOPE: Welche Bug-Klasse wird angegangen?            │
│     (BOM, chmod, description, duplicates, encoding)      │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  2. TEST (Isolation): Edge-Cases synthetisch prüfen      │
│     → NIE auf Production-Daten ersttesten                │
│     → Wenn 0 Bugs gefunden: ready für Phase 3            │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  3. AUDIT: Systematischer Scan über alle Skills          │
│     → Welche Files sind betroffen?                       │
│     → Welche konkreten Änderungen nötig?                 │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  4. FIX + VERIFY:                                       │
│     a) Dry-run → review → apply (incrementell)           │
│     b) Fix EINE Bug-Klasse komplett                      │
│     c) Re-Audit → 0 findings = fertig                    │
│     d) Self-Test (Meta-Tools excl. sich selbst)          │
│     e) Memory-Commit + Skill-Doku-Update                 │
└──────────────────────────────────────────────────────────┘
                          ↓
              Konvergenz? → NEIN → zurück zu 2
              (neue Edge-Cases testen)
              Konvergenz? → JA → DONE
              (3 aufeinanderfolgende Runs ohne Neufunde)
```

## Phase 1: Scope-Definition

### Kategorien-Checkliste

| Kategorie | Erkennung | Typische Fehler |
|---|---|---|
| **BOM** | `read_text(encoding="utf-8")` statt `utf-8-sig` | Silent `\ufeff` in Header/Content |
| **chmod** | Shebang-Script ohne `+x` | Script muss via `python3` aufgerufen werden |
| **Description** | `description:` > 60 chars | Hermes Index cut-off |
| **Duplicates** | Byte-identical Scripts in 2+ Skills | Drift-Risiko bei unabhängigen Edits |
| **Encoding** | LATIN-1, CRLF, BOM, Quoted Fields | `utf-8-sig` dekodiert LATIN-1 als ASCII (silent!) |
| **Row-Width** | CSV-Zeilen mit abweichender Spaltenzahl | Canva Import bricht, Daten gehen verloren |
| **Frontmatter** | Fehlende `name`/`version`/`author`/period | YAML-Loader Error oder ignorierter Skill |

### Scope-Selection Faustregel

Teuerste Kategorie zuerst (gemessen an: was wäre wenn das live ist?):

1. **BOM** (P0) — Silentest Bug. Bricht bei Windows-Exporten ohne Fehlermeldung.
2. **Row-Width / Empty-Pitch** (P0) — Daten gehen verloren ohne dass jemand es merkt.
3. **Description** (P1) — Skill ist "da" aber unsichtbar im Index.
4. **Duplicates** (P2) — Drift-Risiko, aber kein akuter Schaden.
5. **chmod** (P2) — Workaround via `python3` existiert immer.

## Phase 2: Test in Isolation

### Prinzip

**NIE zuerst auf Production-Daten testen.** Immer synthetische Edge-Cases bauen.

### Test-Vektoren (Priorität absteigend)

```
1. FORMAT-GRENZEN (6 Tests)
   ├── Leeres File (0 bytes, header-only, whitespace-only)
   ├── Encoding-Brüche (LATIN-1, BOM, CRLF, UTF-16)
   ├── Quoted Fields ("Caption, mit Komma" in CSV)
   ├── Multi-line (Newline innerhalb eines Felds)
   ├── Symlinks (Ziel existiert nicht)
   └── Sehr große Files (500+ Zeilen, >10KB)

2. SCHEMA-BRÜCHE (4 Tests)
   ├── Fehlende Pflichtfelder
   ├── Zusätzliche unbekannte Felder (Forward-Compat)
   ├── Typsalat (String statt Number, Null statt String)
   └── Zeilen mit variabler Spaltenzahl (10, 11, 12 cols)

3. KOMBINATIONEN (2 Tests)
   ├── Quoted + Empty-Fields (beide Bedingungen gleichzeitig)
   └── BOM + Schema-Drift (Header-BOM maskiert Feldnamen)
```

### Test-Template

```bash
# 1. Synthetische Edge-Case-Datei bauen
mkdir -p /tmp/test-xxx/
echo "..."

# 2. Validator drauf loslassen
python3 validator.py test-nische 2>&1
EXIT=$?

# 3. Erwartetes vs. tatsächliches Ergebnis
echo "Erwartet: Exit 1, 1 Error"
echo "Tatsächlich: Exit $EXIT"
[ "$EXIT" -eq 1 ] && echo "PASS" || echo "FAIL BUG"
```

### Self-Test Discipline

> **Vor jedem Polish-Claim:** Alle Edge-Cases laufen lassen. Happy-Path allein ist kein Beweis. Die 4 gefundenen Production-Bugs 2026-07-15 zeigten sich NUR in Edge-Cases, nie im Happy-Path.

## Phase 3: Audit

### Meta-Tool-Pattern

Falls die Bug-Klasse sich für automatisierte Erkennung eignet:
→ **Meta-Skill bauen** der den gesamten Scan macht (wie `skill-polisher`)
→ **Self-Exclusion-Regel**: Das Meta-Tool MUSS sich selbst ausschließen

```python
SELF_PATH = "meta/skill-polisher/scripts/skill_polisher.py"
for py in SKILLS_ROOT.rglob("scripts/*.py"):
    if str(rel) == SELF_PATH:
        continue  # Intentional utf-8-sig, not a BOM bug
```

### Dry-Run

**IMMER Dry-Run zuerst.** Drei Vorteile:
1. Scope wird sichtbar (wie viele Files?)
2. Heuristik kann geprüft werden (macht der Fix Sinn?)
3. Risk-Assessment (welche Files sind kritisch?)

**Bei `fix-description` besonders wichtig**: Heuristik kann Keywords verlieren. Review jeden Vorschlag.

## Phase 4: Fix + Verify

### Incrementell anwenden

- Fix EINE Bug-Klasse komplett, nicht teilweise
- Nach jedem Fix: Re-Audit
- Wenn 0 Findings: Nächste Bug-Klasse
- Wenn Findings bleiben: Fehler im Fix suchen

### Konvergenz-Kriterium

```
Drei aufeinanderfolgende Runs OHNE neue Findings → STOP
```

Das ist das "wenn noch was geht und test" (Basti) — immer eine Runde mehr testen bis du nichts mehr findest. Drei erfolglose Runs = Abbruch.

## Pitfalls (aus der Praxis 2026-07-15)

### P1: Self-Exclusion vergessen
- **Symptom:** Meta-Tool flaggt sich selbst als Bug
- **Fix:** Explizite SELF_PATH-Konstante + Continue im Loop
- **Guard:** Ersten Audit-Run auf Meta-Tool-Script prüfen vor Bulk-Fix

### P2: Pipe-Chain maskiert Exit-Code
- **Symptom:** `tail -5 | grep "error"` → Exit 0 obwohl Fehler da waren
- **Fix:** In Python: `sys.exit(1)` explizit setzen
- **Guard:** Jeder Check-Pfad MUSS bei Fehler Exit 1 liefern

### P3: Encoding-Doppeltür
- **Symptom:** `utf-8-sig` dekodiert LATIN-1 ohne Fehler → Validator sagt "kein Problem"
- **Fix:** Zusätzlicher Byte-Level-ASCII-Check: `raw_bytes.decode("ascii", errors="replace")`
- **Guard:** Jeder Validator MUSS einen expliziten ASCII-Purist-Check haben

### P4: Self-Inflicted Production-Bug durch Row-Width-Check
- **Symptom:** Neuer Row-Width-Check im Validator findet 23 kaputte Posts
- **Lesson:** Ein Validator der "echte Probleme" findet ist KEIN Bug — es ist ein Feature. Repariere die Production-Daten, nicht den Validator.
- **Guard:** Wenn Validator auf echten Daten exit 1 liefert: erst Production-Daten analysieren, dann Validator-Code prüfen.

## Vergleich: Reaktiv vs. Präventiv

| | Self-Improving (reaktiv) | Polish-Pattern (präventiv) |
|---|---|---|
| **Trigger** | Fehler passiert | Zyklische Wartung / Bundle-Import |
| **Domain** | Einzelfehler | Library-weite Bug-Klasse |
| **Geschwindigkeit** | Sofort nach Fehler | Planbar (quartalsweise) |
| **Werkzeug** | Mnemosyne + skill_manage | Meta-Skill (skill_polisher) |
| **Output** | 1 Mnemosyne-Lesson + Skill-Ref | Bulk-Fix + 0 Findings im Audit |
| **Konvergenz** | Bis Lesson dokumentiert | 3 erfolglose Runs ohne Neufunde |

Beide Patterns sind komplementär: Self-Improving fängt akute Fehler, Polish-Pattern verhindert dass dieselbe Bug-Klasse in 480+ Skills gleichzeitig lauert.