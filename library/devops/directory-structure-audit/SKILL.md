---
name: directory-structure-audit
title: Directory Structure Audit — Classification & Reorganisation
description: |
  Use when inventorying unfamiliar folders, classifying their purpose and activity, detecting duplicates or stale trees, or planning a safe filesystem reorganization.
  NOT for immediately moving or deleting files, auditing a single known file, or modifying application-internal configuration directories.
  Produces an evidence-based directory map with ownership, activity, content type, risks, and proposed destinations before any migration occurs.
triggers:
- User bittet um Uebersicht oder Struktur in einem Home-Verzeichnis oder Workspace
- User fragt nach einem Scout- oder Reconnaissance-Bericht ueber einen Dateisystem-Baum
- User gibt eine Liste von Verzeichnissen zur Klassifizierung (was ist das, ist es
  aktiv, wohin soll es)
- Nach einer laengeren Arbeitsphase ohne Struktur-Check: Angebot zur Struktur-Revision
version: 1.4.0
author: Hermes Agent
license: MIT
lane: koenigin
reasoning_effort: high
trigger_keywords: ['activity', 'inventorying', 'unfamiliar', 'folders', 'classifying']
keywords: ['activity', 'inventorying', 'unfamiliar', 'folders', 'classifying']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['project-landscape-audit', 'desktop-window-reconnaissance']
---


# Directory Structure Audit

## Ueberblick

Ein mehrphasiger Scan, der eine Liste von Verzeichnissen nimmt und fuer jedes herausfindet:
was es **ist** (Zweck, Inhaltstyp), **ob es lebt** (letzte Aenderung, Aktivitaetstrend),
**wem es gehoert** (Domaene/Bereich), und **wo es hingehört** (Vorschlag fuer neue Struktur).

## Pipeline

```
Input: Liste von Ordnern (aus User-Auftrag oder ls)
  |
  v
Phase 1 — Survey (du -sh + batch ls -la)
  |
  v
Phase 1b — Quantitative Metrics (LOC, File-Count, Dateitypen)
  |  (optional) Phase 1c — Per-File Provenance Audit (First-Line + Directive-Check + Sub-Verify)
  |
  v
Phase 2 — Content Deep-Dive (stat, head, README/DESCRIPTION/NAVIGATION-Check)
  |
  v
Phase 3 — Domain Classification (Cluster-Bildung, Aktivitaetsbewertung)
  |
  v
Phase 4 — Cross-Reference mit existierender Doku (README.md, NAVIGATION.md, DESCRIPTION.md)
  |
  v
Phase 5 — Bericht (Tabelle + Tote + Vorschlaege + Insights)
  |
  (Optional) Phase 6 — Reorganisation (Moves via `filesystem-restructure-execution`)
  ODER Phase 6 — Prune Execution (DELETE via siehe unten), nur mit expliziter User-Erlaubnis
```hase 6 — Reorganisation (Moves via `filesystem-restructure-execution`)
  ODER Phase 6 — Prune Execution (DELETE via siehe unten), nur mit expliziter User-Erlaubnis
```
Starte mit einem Groessen- und Inhalts-Ueberblick. Batch alle Befehle in einem Terminal-Aufruf.

```bash
# 1. Gesamt-Groessen (sortiert, human-readable)
du -sh /home/bratan/*/ 2>/dev/null | sort -h

# 2. Kurz-Listing jedes Ordners (erste 20-25 Zeilen)
cd /home/bratan && for d in <liste>; do echo "===== $d ====="; ls -la "$d" 2>&1 | head -20; echo; done
```

**Batch-Regel:** So viele unabhaengige Aufrufe wie moeglich in einen einzigen terminal()-Call
packen. Fuer 40 Ordner reichen 2-3 Durchgaenge.

## Phase 1b — Quantitative Metrics (bei Tiefen-Audits)

Wenn der User Datei-Zahlen, Lines of Code oder eine detaillierte Größenaufschlüsselung pro Verzeichnis will — oder wenn die Migration einen quantitativen Befund braucht.

Batch alle Messungen in einen Terminal-Aufruf:

```bash
# 1. File-Count pro Directory
for d in <dirlist>; do echo "$d: $(find "$d" -type f 2>/dev/null | wc -l) files"; done

# 2. LOC pro Directory nach Dateityp
for d in <dirlist>; do
  echo "=== $d ==="
  for ext in src py sh yaml json md; do
    count=$(find "$d" -name "*.$ext" -type f 2>/dev/null | xargs wc -l 2>/dev/null | tail -1)
    [ -n "$count" ] && echo "  .$ext: $count"
  done
done

# 3. Dateigrößen-Summe pro Directory
du -sh <dirlist> 2>/dev/null | sort -rh

# 4. File-Type-Breakdown (Anzahl je Endung)
find <root> -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

**Bericht für Phase 1b:** Tabelle mit | Verzeichnis | Größe | Files | LOC | Haupt-Endung | Notizen |

Verwende diese Zahlen im Bericht für:
- Priorisierung: Ordner mit 0 Files oder nur `.gitkeep` sind Tot-Kandidaten
- Größenordnung: 4–5 K / 17 Files ≠ 120 K / 1 File (Build-Output)
- Vergleichbarkeit: Gleiche File-Anzahl aber 10× LOC → unterschiedliche Komplexität
\n### Phase 1c — Per-File Provenance Audit (bei Tool/Asset-Inventur)\n\nWenn der User eine Sammlung von Dateien (Scripts, Tools, Assets) systematisch klassifizieren will — z.B. "was ist das, lebt es noch, welche Libraries nutzt es?" — oder wenn jedes File eine bestimmte Direktive/Header/Property in Zeile 1 haben muss.\n\n#### Schritt 1 — Batch First-Line + LoC Scan\n\n```bash\nfor f in *.src; do\n  FIRST=$(head -n1 "$f")\n  LOC=$(wc -l < "$f")\n  echo "FILE: $f | LOC: $LOC | FIRST: ${FIRST:0:80}"\ndone\n```\n\n#### Schritt 2 — Parallel Deep-Read (6-8 Files gleichzeitig)\nLese die Files via `read_file` (max 50 Zeilen für große Files) und klassifiziere:\n- **Zweck** (1-2 Sätze)\n- **Verwendete Libraries** (via grep nach `include_lib` oder `import`)\n- **Status** (active / dead / test / prototype / demo)\n\n#### Schritt 3 — Independent Sub-Verification\nSpawn eine `delegate_task(goal=..., role='leaf')` mit EXAKT demselben Auftrag, aber OHNE deine Ergebnisse zu teilen:\n\n```\nZiel: Prüfe für jedes File ob die erste Zeile der Build-Pflicht-Direktive entspricht\nOutput: Eigenständige Markdown-Tabelle + Summary\n```\n\n**Verifikation:** Vergleiche Sub-Bienen-Ergebnis mit eigener Analyse. Bei Abweichung → manuelle Klärung. Unterschiedliche Counts = Audit-Fehler.\n\n**Pitfall:** Sub-Bienen bekommen KEINEN deinen Session-Kontext. Übergib alle Infos (Pfade, Regel für "was zählt als gültig", Dateiliste) EXPLIZIT im `context`-Parameter.\n\n#### Schritt 4 — Structured Output (3 Files)\n\n1. **Vault-Markdown** — Ausführlicher Katalog mit Tabellen, Status-Klassifizierung, Empfehlungen\n2. **JSON-Arsenal** — Maschinenlesbar mit allen Properties pro File (LoC, Libraries, Status)\n3. **Sub-Verify-MD** — Vom Sub-Agenten unabhängig erstellte Ergebnis-Tabelle\n\n#### Schritt 5 — Self-Verification\nPrüfe dass ALLE drei Output-Files existieren: `cat`/`ls -la` jedes, plus JSON-Parse-Check.\n\n#### Status-Klassifizierung für Arsenal-Einträge\n\n| Status | Kriterium |\n|--------|-----------|\n| **active** | Live nutzbar, deployt, aktiv genutzt |\n| **dead** | Vorgänger einer neueren Version, obsolete Targets |\n| **test** | Nur lokaler Mock, kein externes Target |\n| **prototype** | Unvollständig, Work-in-Progress |\n| **demo/mock** | Nur Print-Output, keine echte Aktion |\n| **flagship** | Aktiv gepflegtes Haupt-Produkt |\n\nVerwende im Bericht eine Tabelle pro File, die diese Felder kombiniert:\n| File | LoC | Zweck (1 Satz) | Status | Libraries |

Fuer jeden Ordner, in dem Phase 1 unklar war oder der besondere Aufmerksamkeit braucht:

| Check | Befehl | Erkenntnis |
|-------|--------|------------|
| Letzte Aenderung | `stat -c '%y %n' <ordner>/*` | Aktivitaets-Trend |
| README/DESCRIPTION | `head -20 <ordner>/README.md` | Zweck des Ordners |
| Sub-Ordner-Struktur | `ls -la <ordner>/<sub>` | Tiefe, Komplexitaet |
| Schluessel-Dateien | `head -5 <ordner>/<key-file>` | Code-Typ, Sprache, Framework |

**Wichtige Querchecks:**
- Gibt es README.md, DESCRIPTION.md, CHANGELOG.md im Ordner? → Nutzen um Zweck zu verstehen.
- Gibt es eine uebergeordnete README.md oder NAVIGATION.md im Home? → Mit diesem Selbstbild abgleichen.
| Schluessel-Dateien | `head -5 <ordner>/<key-file>` | Code-Typ, Sprache, Framework |
| Gibt es `.git/` im Ordner? | `ls -la <ordner>/.git 2>&1` | Es ist ein Git-Repository |

### Phase 2b — Import/Reference Analysis (bei Codebase-Audits)

Durchsuche die Codebase nach Import-Patterns, um Modul-Abhängigkeiten zu kartieren. Besonders wichtig vor Migrationen (damit nichts zerbricht).

```bash
# GreyScript: Suche nach import_code()-Patterns
grep -rn "import_code\|importcode" src/ gamescripts/ --include='*.src' | sort -u

# Python: Suche nach import-Statements
grep -rn "^import\|^from" src/ --include='*.py' | sort -u

# Klassifiziere Import-Typen (in der Analyse, nicht per Tool-Aufruf):
# A) Relative Pfade: import_code('../target.src') — vom Datei-Standort abhängig
# B) Qualified Prefix: import_code('src/core/...') — auf Verzeichnisstruktur angewiesen
# C) Reiner Dateiname: import_code('target') — Namespace-Auflösung via Search-Path
```

**Was mit den Ergebnissen tun:**
1. **Dangling Imports:** Zeilen deren Target-Datei nicht existiert → Fehler bei Build/Load
2. **Duplikat-Erkennung:** Zwei verschiedene Pfade die dieselbe Semantik haben (z.B. `portscan.src` und `portmon.src`) → Dedup-Kandidaten
3. **Cross-Directory Imports:** GreyScript die aus `tools/` in `src/` importiert → erhöhtes Migrations-Risiko
4. **Unused Imports:** Dateien die importiert aber nirgends referenziert werden → Cleanup-Kandidaten

**Bericht-Format für Phase 2b:** Tabelle mit | Import-Pfad | Target-Datei | Existiert? | Typ (A/B/C) | Risiko bei Move |

### Phase 2c — Snapshot & Redundanz-Detektion

Prüfe ob dieselben Daten in mehreren Verzeichnissen existieren — typische Muster:

| Muster | Befund | Empfehlung |
|--------|--------|------------|
| Triple-Snapshot | Gleiche Daten in working tree + `imports/` + `de/imports/` | Zwei der drei Kopien löschen |
| Stale Snapshot | Snapshot-Verzeichnis mit Timestamp im Namen > 14 Tage alt | SoT prüfen, dann löschen |
| Backup-Ordner | `backups/` mit vollständigen working-tree-Kopien | Löschen wenn aktives Git vorhanden |
| Build-Reste | `build/`, `dist/`, `.ci-build/` mit kompilierter Ausgabe | .gitignore checken, ggf. löschen |

```bash
# Snapshot-Alter prüfen
find <verdacht>/ -maxdepth 0 -printf '%TY-%Tm-%Td\\n'

# Diff working-tree vs snapshot (Struktur, nicht Inhalt)
diff <(tree <working> -I '.git|node_modules' 2>/dev/null) \
     <(tree <snapshot> -I '.git|node_modules' 2>/dev/null) \
     | head -40
```

**Bericht für Phase 2c:** Kasten mit gefundenen Redundanzen. Für jede: Pfad(e), Größe, Alter, ob working-tree divergiert hat. Entscheidung: löschen/behalten.

## Phase 3 — Domain Classification

Jeder Ordner bekommt eine Domaene zugewiesen. Erwartbare Domaenen bei typischen
Desktop-Home-Verzeichnissen:

| Domaene | Typische Ordner | Merkmal |
|---------|----------------|---------|
| Hermes-Build | hermes-v7-wt, hermes-webui, hermes-zorin | Hermes im Namen, Skills/, projects/, .hermes/ |
| Yuno/Skill-Tool | yuno-cleaner, yuno-dashboard, yuno-voice-bot | yuno- Praefix, Python/HTML, Hilfstools |
| GreyHack | greyhack-tools, greyscripts, greyhack-repos | .src-Dateien, GreyScript, CI-Build |
| Basti-Projekt | build/, projects/, workspace/ | Eigene Entwicklung, Sandbox |
| Spiele/Modding | cp77-modding, steam_backup_toolkit | Spiele-Mods, Backups |
| System-Maintenance | backups, fix-scripts, LenovoLegionLinux | Systemwiederherstellung, Treiber, Kernel |
| Forschung | results/llm-eval | Benchmarks, Auswertungen |
| Privat-Media | Bilder, Videos, Musik, Calibre-Bibliothek, voice-memos | Medien-Dateien, XDG-Standard |
| Privat-Misc | Downloads, Dokumente, Schreibtisch, Vorlagen | XDG-Standard, persoenliche Dateien |
| System-Install | minimax-install, google-cloud-sdk | Installationspakete, SDKs |

### Aktivitaetsbewertung

| Stufe | Kriterium | Marker |
|-------|-----------|--------|
| tot/leer | Letzte Aenderung > 30 Tage ODER 0 Dateien | Keine src-/py-/md-Dateien, nur leere Ordner |
| stabil | Letzte Aenderung 7-30 Tage, keine offenen Issues | Projekt scheint pausiert |
| frisch | Letzte Aenderung < 7 Tage | Aktive Entwicklung |
| aktiv heute | Heutige Aenderung(en) | Laufendes Projekt |

## Phase 4 — Cross-Reference mit existierender Doku

Mindestens 3 Quellen pruefen, bevor der Bericht finalisiert wird:

1. README.md im home — enthaelt oft eine Selbstdarstellung der Ordner-Struktur
2. NAVIGATION.md im home — vom User gepflegter Index mit Beschreibungen
3. DESCRIPTION.md im home — Detailbeschreibung pro Ordner (Zweck, was gehoert rein, was nicht)

Pruefe ob der tatsaechliche Inhalt mit diesen Selbstbildern uebereinstimmt:
- Ein Ordner der laut README Projects ist, aber nur alte Dateien enthaelt → Im Bericht erwaehnen
- Ein Ordner der beschrieben wird, aber leer ist → Tot-Kandidat

## Phase 5 — Berichts-Format

### Haupttabelle

```
| Pfad | Groesse | Zweck (1 Satz) | Aktiv? | Domaene | Vorschlag |
```

### Sektion: Offensichtlich tote Ordner

```
## Tote / verwahrloste Ordner

| Ordner | Befund | Empfehlung |
|--------|--------|------------|
| name/  | Leer seit..., nur PID-File... | loeschen / pruefen / konsolidieren |
```

### Sektion: Domaenen-Clustering

Gib einen Cluster-Blick: welche Ordner gehoeren zusammen? Das hilft dem User,
Gruppen zu erkennen (z.B. 5 Hermes-Varianten → 1 Hermes-Cluster).

### Sektion: Reorganisations-Vorschlaege

Nur Stichpunkte. **Keine Moves ausfuehren** ohne explizite User-Aufforderung.

Beispiel-Proposal-Struktur:

```
## Vorschlaege fuer neue Struktur (KEINE Moves)

### Repo-artiges Layout
```
~/
├── ~/media/         # Konsolidiert: Bilder + Videos + Musik
├── ~/projects/      # Eigenentwicklung (hermes, yuno, greyhack)
└── ~/NAVIGATION.md
```

### Konkrete Aufraeum-Vorschlaege
1. Leerer-Ordner/ loeschen — kein Inhalt seit Anlage
2. X/ nach Y/ verschieben — thematisch passend
3. A/, B/, C/ → Subfolder von projects/group/
```

### Sektion: Insights fuer nachfolgende Scouts

Am Ende des Berichts: Wichtige Erkenntnisse, die der naechste Scout braucht:
- Tabus, die bestaetigt wurden
- Groesste Einzeldateien (Aufraeum-Kandidaten)
- Cluster, die zusammengefasst werden koennten
- Widersprueche zwischen README-Selbstbild und Realitaet

### Sektion: Risiko-Matrix (bei Migrations-Plan)

Wenn der Bericht einen konkreten Migrationsplan enthält, ergänze eine Risiko-Matrix:

| Risiko | Beschreibung | Impact | Mitigation |
|--------|-------------|--------|------------|
| Snapshot-Divergenz | Working tree ≠ archiviertem Snapshot — Löschung des Snapshots verliert Daten | Hoch | Diff vor Löschung, Recovery über Git |
| Import-Resolvability | Nach Move lösen sich import_code()-Pfade nicht mehr auf | Hoch | Mapping-Tabelle Alt→Neu, grep-Audit vor Move |
| Build-Break | Build-Skript referenziert alte Pfade | Mittel | Build-Test nach jedem Schritt |
| Verifikations-Lücke | Smoke-Tests decken nicht alle GreyScript-Pfade ab | Mittel | Dedizierte Test-Datei pro Subsystem |

### Sektion: Migrations-Plan (bei Bedarf)

Strukturierter Plan mit Phasen — kein Mega-PR, sondern mehrere kleine, revertierbare Schritte:

1. **Phase 1 — Vorbereitung:** Baseline-Test (pytest/greybel), grep-Audit aller Import-Pfade, Mapping alt→neu
2. **Phase 2 — In-place Moves:** 1–3 kleine PRs/Commits, jeder einzeln revertierbar
3. **Phase 3 — Import-Fixes:** Nach jedem Move: grep-Audit → Pfade anpassen → Build-Test
4. **Phase 4 — Verifikation:** Vollständiger Build, Smoke-Tests aller Subsysteme, Vorher/Nachher-Vergleich
5. **Phase 5 — Sync & Cleanup:** Branch mergen, Tag setzen, temporäre Redundanzen löschen

**Regel:** Kein Mega-PR. Jeder Move-Schritt ein eigener Commit mit eigenem Testlauf.

## Regeln

1. **Keine Moves ohne Freigabe.** Der Bericht ist read-only. Reorganisation passiert nur auf expliziten Befehl. Sobald der User grünes Licht gibt: `filesystem-restructure-execution` laden — enthält alle Move-Patterns mit Safety-Nets.
2. **Praktisch sein.** Groessen aus du, Daten aus stat, Inhalte aus head. Keine Schaetzungen.
3. **Batch so viel wie moeglich.** Unabhaengige ls-, du-, stat-Aufrufe gehoeren in einen Terminal-Call.
4. **Nicht in geschuetzte Verzeichnisse schauen.** .hermes/, docs/, .ssh/, .gnupg/ sind tabu.
5. **Tabellarisch berichten.** Keine Fliesstexte fuer Daten, die in eine Tabelle gehoeren.
6. **Cluster denken.** Einzelne Ordner sind weniger interessant als ihre Gruppen.
7. **Vorhandene Doku nutzen.** README.md, NAVIGATION.md, DESCRIPTION.md geben das User-Selbstbild vor.
8. **Dead-Folder-Markierung konsequent.** tot = leer ODER > 30 Tage unveraendert ODER nur PID/Log-Reste.
9. **Domaenen trennen.** Ein Ordner hermes-v7-wt gehoert zu Hermes-Build, nicht zu Privat oder Tooling.
10. **Fokus auf Wert fuer den User.** Der Bericht soll dem User helfen zu entscheiden, WAS er tun will — nicht die Entscheidung abnehmen.
11. **Word/Character Ceiling einhalten.** Wenn der User eine explizite Wortzahl- oder Zeichenbegrenzung für den Output vorgibt (z.B. "max 800 Wörter"): **Baue den Bericht von Anfang an innerhalb dieser Grenze.** Iteriere nicht nach unten — der erste Draft sollte bereits nah am Limit sein. Kürze Tabellen (merge rows), kürze Erklärungen, nutze kompakte Formate. 7+ Iterationen zum Runtertrimmen sind ein Anti-Pattern.

## Phase 6 (Optional) — Prune Execution (DELETE / Bereinigung)

Wenn der User explizit eine **Bereinigung** (löschen/prune/entfernen) anstatt nur einer Umstrukturierung (move) fordert — z.B. "sichte und prune" oder "was darf weg".

### Phase 0 — Retention Policy Definition (vor 6a)

**NUTZE DIESE PHASE BEI ARCHIV-PRUNES MIT ALTERS-REGELN.** Überspringe wenn der User nur "lösche was offensichtlich Müll ist" sagt (dann direkt zu 6a).

Bei Alters- oder Aufbewahrungs-Regeln: definiere die Policy als ersten Schritt — **bevor** irgendein File analysiert oder gelöscht wird. Halte die Policy in einer kurzen Tabelle fest:

```markdown
## Retention Policy

| Regel | Wert | Begründung |
|-------|------|------------|
| KEEP | < N Tage | Frische Daten, noch relevant |
| DELETE | > M Tage UND dupliziert woanders | Alt und redundant |
| DEFAULT | KEEP | Unsicher = behalten |
```

**Typische User-Vorgaben:**
- KEEP < 30 Tage / DELETE > 90 Tage UND Duplikat → User sagt "sichte und prune backups/"
- KEEP < 7 Tage / DELETE > 60 Tage → für temporäre Build-Artefakte
- KEEP < 90 Tage / DELETE > 365 Tage UND dupliziert → für Jahres-Archive
- Reine "ist das Müll"-Bewertung ohne Altersregel → Phase 0 überspringen, direkt zu 6a

**Wichtig:** Lies und dokumentiere die Policy bevor du scanst. Die Policy entscheidet für jedes File — du wendest sie nur an. Wenn der User keine expliziten Tage nennt, frage mit 2-3 Optionen (z.B. "Sollen wir 30/60/90 Tage als Grenze nehmen?").

### Phase 0b — Ältestes File bestimmen

Bevor du mit aufwändiger Analyse beginnst: Prüfe ob überhaupt ein File die DELETE-Schwelle erreicht.

```bash
# Ältestes Datum im Ziel-Ordner
find /target/path -type f -printf '%TY-%Tm-%Td\n' | sort | head -1

# Heute minus ältestes = max Alter in Tagen
# Wenn max Alter < DELETE-Schwelle → Report: "Kein File prunebar, nächste Welle am YYYY-MM-DD"
```

Wenn das älteste File jünger als die DELETE-Schwelle ist, brich früh ab: erstelle einen sauberen Report, dokumentiere "nächstes Prune-Fenster", aber führe KEINE Löschungen durch.  
Siehe `references/backup-prune-retention-protocol.md` für ein vollständig durchgeführtes Beispiel mit 0 gelöschten Files.

### 6a — Cross-Reference mit aktivem System-Zustand

Bevor archivierte Daten gelöscht werden: **prüfe ob die aktiven Gegenstücke noch existieren und aktuell sind**.

| Prüfung | Befehl | Bedeutung |
|---------|--------|-----------|
| state.db im Archiv vs aktiv | ls -la ~/.hermes/state.db + ls -la <archiv>/state.db | Archiv-Snapshot obsolet wenn aktives state.db neuer/größer ist |
| state-snapshots | ls ~/.hermes/state-snapshots/ | Pre-Update-Snapshots anlegen beim nächsten hermes update — alte sind obsolet |
| Aktive Config | head -3 ~/.hermes/config.yaml vs archivierte | Config-Backups 30d+ alt sind Duldung, nicht Sicherheit |
| .env-Backups | Nur Existenz prüfen, KEIN diff (Secrets!) | Löschen, nicht lesen |
| Skills-Verzeichnis | ls ~/.hermes/skills/ | wc -l | Vergleich mit archivierten Skill-Backups |
| Gateway-Status | hermes config get use_gateway | false = gateway deaktiviert, state ist Stale |

**Whitelist-Prinzip (CRITICAL — aus Bastis Preferences):** Bei Löschungen niemals blind vorgehen. Immer zuerst identifizieren was BLEIBEN muss (READMES, aktive Dependencies), dann erst löschen.

### 6b — README-Erkundung

Archive-Bereiche haben oft READMEs die explizit sagen "Kann bei Platzbedarf gelöscht werden" oder "Nur für Debug-Diagnose". **Diese READMEs sind der beste Filter.** Lies sie VOR dem Löschen.

### 6c — Phasen-basierte Löschung von außen nach innen

```
Phase A: Große, isolierte Brocken (größte Einsparung, geringstes Risiko)
  rm -rf <big-obsolete-snapshot>/
  rm -f <big-bak-file>

Phase B: Container-Inhalte (Behalte READMEs, lösche Inhalt)
  find <dir> -mindepth 1 -not -name 'README.md' -delete

Phase C: Kleine Files & alte Sub-Dirs
  rm -f <file1> <file2>
  rm -rf <old-empty-dir>/
```

**Reihenfolge:**
1. **Sichere große Einzelfunde** zuerst — isolierte Snapshots, .bak-Files ohne aktives Gegenstück
2. **Inhalte von Ordnern** deren README Löschung erlaubt (unter Erhalt der README)
3. **Kleine Reste** — einzelne Files, leere Ordner

### 6d — Vollständige Verifikation

Nach der Löschung:

```
1. Finale Größen-Kontrolle: du -sh <target-dir>
2. Struktur-Kontrolle:     ls -la <target-dir>/ (sind READMEs noch da?)
3. Aktiv-System-Check:     Nichts außerhalb des Targets berührt
   - ls -la ~/.hermes/state.db (unberührt)
   - ls -la ~/.hermes/state-snapshots/ (unberührt)
   - ls ~/.hermes/skills/ | wc -l (gleiche Anzahl)
4. Kollateralschaden:       NUR bei Verdacht — ls ~/.hermes/*/
```

**Dokumentation:** Speichere den Inventory-Bericht als Referenz für zukünftige Sessions.

### 6e — Umgang mit API-Key-haltigen Backups

Backups von `.env` enthalten **API-Keys**. Sicherheitsregeln:
- Lösche sie (KEINEN Inhalt lesen/vergleichen/anzeigen)
- Prüfe nur: Existenz, Größe, Dateiname, README-Beschreibung
- Vertraue dem README dass es ".env Backups — enthalten API-Keys" sagt
- Lösch-Entscheidung: aktive .env lebt separat; Backups >30d sind obsolet

## Related Skills

- **`filesystem-restructure-execution`** — Führt die vom Audit vorgeschlagenen Moves tatsächlich aus (mit Safety-Nets). Immer dann laden wenn der User sagt "Jetzt die Moves umsetzen."
- **`project-landscape-audit`** — Git-Repo-Inventur für den Fall dass viele Git-Projekte involviert sind
- **`system-documentation`** — Für Dokumentation der neuen Struktur und Migration im docs-Tree
- **`yuno-cleaner`** — System-Cleanup-Tool (Browser-Cache, Gaming-Junk, große Dateien) — komplementär zu Archive-Prune
- **`yuno-user-preferences`** — Bastis Preferences: Whitelist-Prinzip, keine Blind-Löschungen, sichere Reihenfolge

## Example References

- `references/greyhack-tools-audit-2026-07-05.md` — Vollständig durchgeführter Audit mit LOC-Counts, Import-Analyse, Triple-Snapshot-Detektion, Migrations-Plan und Risiko-Matrix (800-Wörter-Ceiling). Lade bei Migration/Audit-Aufgaben als Referenz.

## Tools

- **`filesystem-restructure-execution`** — Move-Skill für die Umstrukturierung nach Audit
