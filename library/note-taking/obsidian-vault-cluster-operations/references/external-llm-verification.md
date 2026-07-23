# External-LLM-CLI — 9-Schritt-Verifikationsprotokoll

> **Datum:** 2026-07-05  
> **Kontext:** Vault Phase 7 — Gemini 3.1 Pro Preview via `gemini --yolo`  
> **Modell:** DeepSeek V4 Flash (Yuno/Königin) → Gemini 3.1 Pro Preview (Tool)  
> **Orchestrierung:** Pattern 9b — Direct Queen→CLI Invocation (2-Tier)

## Übersicht

Nach jedem External-LLM-CLI-Run mit `--yolo`-Schreibzugriff auf den Vault MUSS die Königin ein 9-stufiges Verifikationsprotokoll durchführen. Das Protokoll ist spezifisch für Direkt-Invocation (Pattern 9b) — bei Subagent-vermittelten Läufen (Pattern 9a) fängt der Worker-Subagent bereits Pattern-7-Fehler ab, aber die Königin macht trotzdem die Schritte 1, 4, 5, 8 als Stichprobe.

## 9-Schritt-Protokoll

### Schritt 0 (VOR dem Run): Pre-Snapshot

```bash
# Liste aller .md-Dateien (exkl. Obsidian-intern, Trash) aufnehmen
find "/home/bratan/Dokumente/Obsidian Vault" \
  -name '*.md' \
  -not -path '*/.obsidian/*' \
  -not -path '*/.trash/*' \
  | sort > /tmp/gemini-pre-snapshot.txt

# Vorher-Count notieren
wc -l /tmp/gemini-pre-snapshot.txt
# → 116 (Phase 7, 2026-07-05)
```

### Schritt 1: Post-Run-Count

```bash
# Gleicher find-Befehl, gleicher Path
find "/home/bratan/Dokumente/Obsidian Vault" \
  -name '*.md' \
  -not -path '*/.obsidian/*' \
  -not -path '*/.trash/*' | wc -l
# → 118 (Phase 7: +2, erwartet 117–125 ✓)
```

### Schritt 2: Note-Count-Diff (neue vs. fehlende)

```bash
# Alle neuen/fehlenden Files identifizieren
diff <(cat /tmp/gemini-pre-snapshot.txt) \
     <(find "/home/bratan/Dokumente/Obsidian Vault" -name '*.md' -not -path '*/.obsidian/*' -not -path '*/.trash/*' | sort)
# Gibt alle hinzugekommenen (>) und verschwundenen (<) Files aus
# → In Phase 7: 118 Zeilen gegenüber 116 drin, keine gelöscht
```

### Schritt 3: mtime-basierte Modified-Files-Liste

```bash
# Dateien, die während des Runs modifiziert wurden (neuer als Pre-Snapshot)
find "/home/bratan/Dokumente/Obsidian Vault" \
  -name '*.md' \
  -not -path '*/.obsidian/*' \
  -not -path '*/.trash/*' \
  -newer /tmp/gemini-pre-snapshot.txt \
  -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" | sort -n
```

**Ausgabe — detailliert interpretieren:**

| Feld | Bedeutung | Beispielwert |
|---|---|---|
| `%T@` | Unix-Timestamp (mtime) | 1783280664.8769 |
| `%TY-%Tm-%Td %TH:%TM` | Datum lesbar | 2026-07-05 21:44 |
| `%s` | Dateigröße in Bytes | 381 |
| `%p` | Vollpfad | `/vault/Willkommen.md` |

**Worauf achten:**
- Jeder Eintrag ist eine Datei, die Gemini erstellt oder modifiziert hat
- **Creates vs. Patches unterscheiden:** Vorher nicht im Pre-Snapshot → `new`, vorher drin → `modified`
- Reihenfolge der mtimes zeigt Arbeitsreihenfolge (bei Gemini: 2 Patches init, dann 2 Creates, dann 1 Patch = parallel/seriell gemischt)

### Schritt 4: Forbidden-Zone-Check (CRITICAL)

```bash
# Definiere verbotene Ordner (laut Plan/Briefing)
for zone in "01 Kontext" "02 Inbox" "07 Archiv" "08 Anhaenge"; do
    result=$(find "/home/bratan/Dokumente/Obsidian Vault/$zone" \
      -name '*.md' \
      -newer /tmp/gemini-pre-snapshot.txt 2>/dev/null)
    if [ -n "$result" ]; then
        echo "⚠️ REGELVERSTOSS in $zone:"
        echo "$result"
    else
        echo "✅ $zone — sauber"
    fi
done
```

**Erwartung:** Alle Zonen = `sauber`. Jede Modifikation in 01/02/07/08 ist ein **Regelverstoß** (es sei denn, der Plan erlaubt es explizit). Phase 7: alle sauber.

### Schritt 5: MOC-Integritäts-Check

```bash
# Alle MOC-Files (egal ob MOC - Name.md oder Ordner/_MOC.md) auf mtime prüfen
find "/home/bratan/Dokumente/Obsidian Vault" \
  \( -name 'MOC*' -o -name '_MOC*' \) \
  -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" | sort -n
```

**Erwartung:** Alle MOC-mtimes müssen VOR dem Run-Datum liegen. Wenn ein MOC-File nach dem Run-Datum modifiziert wurde → möglicher Regelverstoß (es sei denn, der Plan erlaubt MOC-Patches).  
In Phase 7: MOC-mtimes alle bei ~1783265xxx (vor Run 1783280xxx) — sauber.

**Kollisions-Fallunterscheidung:**

| Situation | Bewertung |
|---|---|
| MOC-mtime > Run-Start | ❌ Verstoß — External LLM hat trotz Verbot MOC gepatcht |
| MOC-mtime < Run-Start | ✅ Korrekt — MOCs nicht angefasst |
| MOC-mtime < Run-Start ABER in Schritt 3 gelistet | ⚠️ Möglich: Eine andere Datei (kein MOC) wurde modifiziert |

### Schritt 6: Zero-Content-Note-Check

```bash
# Bekannte Zero-Content Notes (aus Plan/Phase-Doku)
for note in "Yuno-Dashboard.md" "2026-07-04.md" "06 Daily Notes/2026-07-04.md"; do
    full="/home/bratan/Dokumente/Obsidian Vault/$note"
    if [ -f "$full" ]; then
        size=$(stat --format=%s "$full")
        echo "$size $full"
    else
        echo "NOT_FOUND $full"
    fi
done
```

**Erwartung:** Zero-Content Notes (0 Bytes) dürfen NICHT gefüllt werden (laut Plan). Wenn eine Zero-Content-Note plötzlich 1000+ Bytes hat → Regelverstoß (External LLM hat trotz "nicht anfassen"-Anweisung geschrieben).  
In Phase 7: `Yuno-Dashboard.md` = 0 B, `2026-07-04.md` = 0 B, `06 Daily Notes/2026-07-04.md` = 3134 B (war schon vorher Content, Daily Note — ok wenn Daily-Note-Patches erlaubt).

### Schritt 7: Neue-Notes-Content-Validierung

```bash
# Alle neuen Files aus Schritt 2-Diff nehmen und prüfen
for newfile in "<pfad aus diff>"; do
    # 1. Existiert? → stat
    stat --format='GROESSE=%s' "$newfile"
    
    # 2. Hat es Frontmatter?
    head -5 "$newfile" | grep -q '^---$' || echo "⚠️ Kein Frontmatter: $newfile"
    
    # 3. Ist es > 100 Bytes? (Anti-Pattern: leere Satelliten)
    [ "$(stat --format=%s "$newfile")" -gt 100 ] || echo "⚠️ Zu kleine Note: $newfile"
    
    # 4. Enthält es nur Platzhalter? ("Content folgt", "TODO", etc.)
    head -20 "$newfile" | grep -qi 'content folgt\|todo\|in bearbeitung\|hier kommt\|placeholder' \
        && echo "⚠️ Nur Platzhalter: $newfile"
done
```

**Erwartung:** Jede neue Note sollte >100 Bytes, mit YAML-Frontmatter, ohne Platzhalter-Texte sein.  
Phase 7: Beide Satelliten 1781 + 1489 B, mit Tags, kein Platzhalter-Text.

### Schritt 8: Duplicate-Drift-Scan (NEU seit Phase 7)

```bash
# Für jede NEUE Datei: Prüfen ob ähnlicher Name schon existiert
# Heuristik: gleicher Wort-Stamm, aber andere Trennzeichen
for newfile in $(diff ... | grep '^>' | awk '{print $2}'); do
    basename_no_ext=$(basename "$newfile" .md)
    # Vereinfachte Normalisierung: Trennzeichen entfernen
    normalized=$(echo "$basename_no_ext" | tr -d '[:space:]-_')
    # Suche nach existierenden Files mit ähnlichem Stamm
    find "/vault" -name '*.md' -not -path '*/.obsidian/*' | while read existing; do
        enormalized=$(basename "$existing" .md | tr -d '[:space:]-_')
        if [ "$normalized" = "$enormalized" ] && [ "$newfile" != "$existing" ]; then
            echo "⚠️ DUPLIKAT-VERDACHT: $newfile ≈ $existing"
            # Inhalt-Vergleich
            diff <(head -30 "$newfile" | grep -v '^---$' | grep -v '^tags:' | grep -v '^quelle:') \
                 <(head -30 "$existing" | grep -v '^---$' | grep -v '^tags:' | grep -v '^quelle:')
        fi
    done
done
```

### Schritt 9: Stichproben-Patch-Validierung

```bash
# Aus Schritt 3 (modifizierte Files) 3 Dateien per Stichprobe prüfen
for sample in "Willkommen.md" "05 Ressourcen/Glossar.md" "06 Daily Notes/2026-07-05 - Phase 2 Final.md"; do
    full="/home/bratan/Dokumente/Obsidian Vault/$sample"
    echo "=== $full ==="
    head -20 "$full"
    echo "---"
done
```

**Erwartung:** Die Patches sind **additiv** (nichts gelöscht), die "Verbindet zu"-Sektionen existieren, Links sind im `[[...]]`-Format, Frontmatter ist intakt (genau 2 × `---`).

---

## Phase 7 — Worked Example (2026-07-05)

| Schritt | Befehl | Ergebnis | Status |
|---------|--------|----------|--------|
| 0 | `find ... > pre-snapshot.txt` | 116 Zeilen | ✅ |
| 1 | `wc -l post-snapshot` | **118** (+2, in Range 117-125) | ✅ |
| 2 | `diff pre post` | Nur > (neue), keine < (gelöscht) | ✅ |
| 3 | `find -newer ... -printf` | 7 Files modifiziert (2 creates + 5 patches) | ✅ |
| 4 | Forbidden zones | 01/02/07/08 = kein Treffer | ✅ |
| 5 | MOC-Check | Alle MOC-mtimes vor Run-Datum | ✅ |
| 6 | Zero-Content | Yuno-Dashboard 0 B, 2026-07-04 0 B | ✅ |
| 7 | Neue-Notes-Inhalt | 1781 + 1489 B, Frontmatter, kein Platzhalter | ✅ |
| 8 | Duplicate-Drift | ⚠️ `Obsidian-Plugins-Setup.md` ≈ `Obsidian - Plugin-Setup.md` | ⚠️ Erkannt |
| 9 | Stichprobe Patches | Additive "Verbindet zu"-Sektionen, intakte Frontmatter | ✅ |

### Duplikat-Detail

| Neu | Alt | Aktion |
|-----|-----|--------|
| `05 Ressourcen/Obsidian-Plugins-Setup.md` (10 KB, Bindestrich) | `05 Ressourcen/Obsidian - Plugin-Setup.md` (8 KB, Spatium) | Löschen oder Mergen |

**Ursache:** Gemini 3.1 Pro bekam Verbot "keine Notes umbenennen", erstellte daher eine neue Datei mit Bindestrich-Namen statt die existierende Spatium-Note zu patchen. Die neue Note hatte Tags, Quelle und Rückverweis auf die Alt-Note. Kein böser Wille, aber ein strukturelles Anti-Pattern.

**Empfehlung:** `Obsidian-Plugins-Setup.md` löschen — die Alt-Note enthält den verifizierten Community-Plugin-Befund, der in der neuen Note fehlt.

## Querverweise

- Skill: `obsidian-vault-cluster-operations` → Pattern 9b (Direct Queen→CLI) + Pattern 9c (Duplicate-Drift)
- Skill: `coding-agents` → `references/gemini-cli.md` (CLI-spezifische Auth-Pitfalls)
- Vault: `Vault-Phase-7-Plan - Gemini-Audit.md` (vollständiger Plan mit Scope + Anti-Patterns)
- Backup: `~/.cache/vault-backups/phase7-gemini-20260705_213718/` (Backup VOR Phase 7)
