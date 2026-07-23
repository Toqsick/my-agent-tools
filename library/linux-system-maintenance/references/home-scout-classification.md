# Home-Scout File Classification Protocol

> **Ziel:** Erschöpfende Klassifikation aller Top-Level-Dateien in `~/` (oder einem anderen `$HOME`) mit Priorisierung, Domänenzuordnung und Aufräumempfehlung.
> **Entdeckt bei:** Home-Scout B Scan 2026-07-04

## 1. Scan-Phase (read-only)

```bash
# Alle Top-Level-Files mit Größe + Datum
find /home/bratan -maxdepth 1 -type f -printf '%p\t%s\t%TY-%Tm-%Td %TH:%TM\n' | sort
```

**Wichtig:** `-maxdepth 1 -type f` — nur Files, keine Dirs, nicht rekursiv.

## 2. Klassifikation pro File

Jede Datei wird nach **5 Dimensionen** klassifiziert:

### Kategorie

| Kategorie | Beschreibung | Beispiele |
|-----------|-------------|-----------|
| `Bericht` | Fertiges Dokument, Report, Analyse | `GreyHack_Netzwerk_Report.md`, `ABSCHLUSSBERICHT_*.md` |
| `Playbook` | Handlungsanleitung, Checkliste, Script | `setup_security_fixes.sh`, `gpu-reload.sh` |
| `README` | Home-Index, Navigation, Systembeschreibung | `README.md`, `DESCRIPTION.md`, `NAVIGATION.md` |
| `Quick-Capture` | Unfertiger Entwurf, Session-Notiz | `mission_yuno_v6_test.txt`, `cyberpunk-clip-1.md` |
| `Test` | Explizite Test-Skripte (nicht produktiv) | `test_*.py`, `test_*.js` |
| `Sonstiges` | Installer, Binaries, Orphans | `.deb`, `.zip`, `page.png` |
| `Systemfile` | Config, Node-Projekt, Secret | `.gitconfig`, `package.json`, `.claude.json` |
| `Backup` | Explizite Sicherung | `hermes-backup-*.zip` |
| `Log` | Runtime-Output eines Programms | `linux-assistant-run.log` |
| `Duplicate` | Exakte oder semantische Kopie | `.deb.1`, `MODEL_HANDOFF_SHORT.md.bak` |

### Domäne

Das Themenfeld, dem die Datei logisch zugehört:

- `GreyHack DB` / `GreyHack DMZ` / `GreyHack Game`
- `Cyberpunk-Trilogie`
- `Hermes` / `Yuno` / `System/NVIDIA`
- `Meta/Doku`
- `AI/Research`
- etc.

### Eigentümer (Author)

Woher stammt die Datei? Aus Header-Metadaten, Dateinamen-Konventionen oder Kontext ermitteln:

| Autor | Signal |
|-------|--------|
| **Yuno** | Header: `Author: Yuno`, `Bearbeitet von: Yuno`, Datei: `ABSCHLUSSBERICHT*`, `MODEL_HANDOFF*` |
| **Basti** | Manuell erstellt, manuell heruntergeladen (OAuth-Secrets, Steam-Kram) |
| **Pair (Yuno+Basti)** | Briefing durch Basti, Output durch Yuno, z. B. Cyberpunk-Playbook |
| **Tool** | Auto-generierte JSON-Logfiles (`.steam_backup_inventory.json`, `.yuno-mobil-lastcheck.json`) |
| **root** | Datei im Home mit root-owner — fast immer ein Systemfehler/Orphan |
| **System** | bash history, package-lock.json, `.flutter` |

### Priorität (Quick-Wins)

Sortierung nach **Aufwands-Nutzen-Verhältnis**:

| Prio | Farbe | Kriterium | Beispiel |
|------|-------|-----------|---------|
| 🔴 1–3 | Rot | Große Duplikate oder verwaiste GB-Fresser | `.deb + .deb.1`, `hermes-backup-*.zip` |
| 🟠 4–7 | Orange | Eindeutiger Müll, kaputte Dateinamen | `" "` whitespace, `ystemctl` typo, `.bak` |
| 🟡 8–13 | Gelb | Test-Varianten, kontextlose PNGs, Einzeiler | `test_*.py*` Mehrfachvarianten |

### Status (lebendig / verwaist / orphan)

| Status | Definition |
|--------|-----------|
| **Lebendig** | Aktiv referenziert, kürzlich bearbeitet, Teil eines laufenden Projekts |
| **Veraltet** | Nicht mehr gebraucht, aber historisch dokumentiert (`.bak`, älterer Report) |
| **Orphan** | Kein Kontext erkennbar, kaputter Dateiname, root-owned |

## 3. Multi-File Cross-Reference („Stalactite Detection")

Ein Kern der Methodik: Dateien **nicht isoliert** betrachten, sondern **überlappende Sets identifizieren**:

| Symptom | Erkennung | Aktion |
|---------|-----------|--------|
| **Exakte Duplikate** | Gleiche Größe + gleicher Name + `.1` Suffix | Löschen des Suffix-Exemplars |
| **Semantische Duplikate** | Gleicher Zweck, unterschiedliche Namen | Konsolidieren, bis auf 1 löschen |
| **Test-Mehrfachvarianten** | `test_*` prüft dasselbe Tool 3–5 mal | Einen Master behalten, Rest löschen |
| **Report-Überlapp** | Gleiche DB/Datenquelle, 2+ Reports mit >50% Overlap | In `~/docs/` subdir verschieben + `index.md` |
| **Ghost-Files** | Whitespace-Namen, Tippfehler im Dateinamen, root-owned im Home | Löschen + ggf. korrekt ablegen |

### Typische Funde aus der Praxis

| Ghost-Typ | Fund | Ursache |
|-----------|------|---------|
| Whitespace-Dateiname | `" "` → nvidia-powerd systemd-Unit | `sudo tee` mit fehlerhaftem Pfad |
| Tippfehler-Dateiname | `ystemctl --user list-units \| grep -i ollama` | Redirect in Datei statt Befehl |
| HTML-Fehlerseite als Installer | `nomachine_8.16.1_1_amd64` (42 KB HTML) | Download-Fehler, Server returned 404-Seite |
| Kontextloses PNG | `page.png` 1280×577 | Screenshot ohne Referenz |

## 4. Report-Format (5 Sections)

Jeder Home-Scout Bericht hat genau diese Struktur:

```
## 1) Inventar-Tabelle
— Alle Files mit #, Name, Größe, Alter, Kategorie, Domäne, Vorschlag

## 2) Quick-Wins (Prio geordnet)
— 🔴🟠🟡 priorisierte Lösch-/Move-Empfehlungen
— Jede Zeile: Prio | Datei | Aktion | Begründung

## 3) Eigentümer / Autoren-Map
— Welcher Agent/Mensch hat was produziert?
— Signal-basiert (Header, Dateiname, Tool)

## 4) Domänen-Zuordnung (für navigation.md-Index)
— Welches Thema → welche Files?
— Ready zum Einfügen in NAVIGATION.md

## 5) Orphan-/Veraltet-Befunde
— Alle Ghosts, Duplicates, Overlaps in einem Block
— Explizites Fazit: „Keine Moves ausgeführt — nur Analyse"
```

## 5. Wichtige Regeln

1. **Nur Top-Level.** Kein Rekursion in Unterverzeichnisse — das ist Sache eines separaten Deep-Scans.
2. **System/Config-Files nicht antasten.** `.bashrc`, `.profile`, `.gitconfig`, `.bash_history` etc. werden inventarisiert, aber als „legitim" markiert. Nicht in die Löschliste aufnehmen.
3. **Keine Moves ausführen.** Der Bericht empfiehlt Aktionen, führt sie nicht aus. Explizit als read-only deklarieren.
4. **Tatsächliche Daten nehmen, nicht schätzen.** Jede Größenangabe = `stat -c%s` oder `wc -l`. Jedes Datum = `%TY-%Tm-%Td` aus find.
5. **Begründung pro Quick-Win.** „Warum löschen?" muss nachvollziehbar sein („exaktes Duplikat", „HTML-Fehlerseite", „3 Varianten desselben Tests").

## 6. Erkennungshilfen (Schnell-Checks)

```bash
# Ghost-Files: whitespace oder komische Zeichen im Namen
find /home/bratan -maxdepth 1 -type f -name "* *" -o -name "*[![:print:]]*" 2>/dev/null

# root-owned files im Home
find /home/bratan -maxdepth 1 -type f ! -user bratan

# Duplikate: gleiche Größe
find /home/bratan -maxdepth 1 -type f -exec stat -c'%s %n' {} \; | sort -n | uniq -d -w 12

# Kontextlose PNGs/Binaries ohne Referenz in anderen Files
# — manuelle Prüfung via `grep -rl "filename" ~/docs/ ~/*.md 2>/dev/null`

# Test-Varianten cluster
for f in /home/bratan/test_*; do
  echo "$(wc -l < "$f") $f"
done

# Report-Overlap: gleiche DB/Quelle in mehreren .md
grep -l "GreyHackDB\|Grey Hack_Data" /home/bratan/GreyHack_*.md /home/bratan/greyhack-*.md 2>/dev/null
```
