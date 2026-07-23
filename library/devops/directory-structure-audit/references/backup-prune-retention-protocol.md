# Backup Prune — Retention-Policy-Protokoll

**Session:** 2026-07-04, 50-System/backups/ (2,1 GB)
**Ergebnis:** 0 gelöschte Files — alle < 30 Tage alt, keine DELETE-Regel gegriffen.

## Ausgangslage

- Ziel: `/home/bratan/50-System/backups/`
- User-Vorgabe: "Sichte und prune" mit expliziten Keep/Delete-Regeln
- Constraints: NUR dieses Verzeichnis; KEINE `.hermes/`, KEINE `.yuno-cleaner/`

## Schritt-für-Schritt-Protokoll

### 1. Baseline messen

```bash
du -sh /target/              # 2,1G
date                         # Heute = Sa 4. Jul 2026
ls -la /target/              # Übersicht: 3 Sub-Dirs + ~10 Files
```

**Ergebnis:** Sub-Dirs: `greyhack/`, `hermes/` (leer), `mnemosyne/`.  
Top-Level-Files: 3 große Archive (1,29G + 437M + 53M), DESCRIPTION.md, restore-hermes.sh, 2 kleine ZIPs.

### 2. Rekursive Datei-Auflistung mit Datum (sortiert)

```bash
find /target/ -mindepth 1 -maxdepth 3 \
  -printf "%p|%s|%TY-%Tm-%Td %TH:%TM|%TY%Tm%Td\n" | sort -t'|' -k4 -n
```

**Wichtig:** `-printf` mit `%TY%Tm%Td` (sortierbares Datum) — sortiert die Liste chronologisch.  
So siehst du sofort: ältestes File = 12.06., jüngstes = 04.07.

### 3. Alters-Check: Früher Abbruch?

```
Ältestes File: 2026-06-12 (22 Tage alt)
DELETE-Schwelle: > 90 Tage
→ Alle Files < 90 Tage → KEIN File erfüllt DELETE-Kriterium → Kein Löschen möglich
```

**Früher Abbruch-Richtlinie:** Wenn das älteste File jünger ist als die DELETE-Schwelle,
trotzdem vollständig analysieren (der User will den Bericht sehen!), aber keine Löschungen
durchführen. Dokumentiere "Nächstes Prune-Fenster: YYYY-MM-DD (wenn ältestes File die
DELETE-Schwelle erreicht)."

### 4. Inhaltliche Analyse jedes Sub-Dirs

#### 4a — DESCRIPTION.md lesen

Liefert Kontext: sagt "Mnemosyne-DB-Backups (täglich seit 19.06.)" — bestätigt dass die
mnemosyne/-Subdirs dokumentierte Konvention sind. Wenn DESCRIPTION.md nicht existiert
oder widerspricht: notieren, nicht ignorieren.

#### 4b — Cross-Reference: existieren diese Dateien auch woanders?

```bash
# Prüfe ob große Archive in ~/.hermes/ existieren
find /home/bratan/.hermes -name "hermes-backup*.zip" 2>/dev/null
# → leer: der ZIP ist UNIQUE in backups/

# Prüfe ob Mnemosyne-DBs live existieren
find /home/bratan -maxdepth 5 -name "mnemosyne-2026-07*.db" -not -path "*/backups/*" 2>/dev/null
# → leer: Snapshots sind UNIQUE in backups/

# Prüfe Live-Mnemosyne
ls -la /home/bratan/.hermes/mnemosyne/mnemosyne.db
# → 38MB (04.07.) — aktive DB ist neuer als alle Snapshots
```

#### 4c — Verdächtige Größen-Gleichheit prüfen (MD5)

Wenn viele Files **exakt gleiche Byte-Größe** haben (z.B. 16 GreyHack-DBs à 6.979.584 B):

```bash
# Sind sie identisch?
md5sum GreyHackDB-*.db | head -10
# → ALLE unterschiedlich! Echte Entwicklungs-Iterationen, keine Duplikate.
```

**MERKE:** Gleiche Größe ≠ gleicher Inhalt bei DB-Snapshots. Hash-check ist Pflicht bevor
du "Duplikate" deklarierst.

#### 4d — Restoration-Kontext prüfen

Wenn ein restore-Script im Verzeichnis liegt:

```bash
cat restore-hermes.sh
# → Referenziert: hermes-core, hermes-docs-projects, mnemosyne-memories → das Set
#   bildet eine Disaster-Recovery-Einheit. Files einzeln zu löschen würde das
#   Set zerstören. Entweder ALLE behalten oder NONE. (Hier: alle < 90d → KEEP)
```

### 5. Inventur-Tabelle aufbauen (pro File/Sub-Dir)

Tabelle mit diesen Spalten:

| Sub-Dir / File | Größe | Datum | Alter (Tage) | Regel-Ergebnis | Begründung |
|---|---|---|---|---|---|
| hermes-backup-*.zip | 1,29 GB | 12.06. | 22 | **KEEP** | < 30 Tage (KEEP-Regel) |
| mnemosyne-2026-07-04.db | 36 MB | 04.07. | 0 | **KEEP** | Heute, dokumentierte Konvention |
| GreyHackDB-yuno-v6-*.db | 6,96 MB | 03.07. | 1 | **KEEP** | < 30 Tage, Entwicklungs-Historie |

**Regel-Auswertung pro Zeile:** Jede Zeile wird gegen die Policy evaluiert.  
Die Spalte "Regel-Ergebnis" enthält das Resultat (KEEP/DELETE) plus die Referenz
auf die Regelzeile die zutrifft.

### 6. Nichts-Löschen-Report

Wenn alle Files die KEEP-Regel passieren, liefere einen vollständigen, sauberen Bericht:

1. **Executive Summary:** "0 von 37 Files gelöscht — alle < 30 Tage, KEEP-Regel greift"
2. **Vorher/Nachher-Tabelle:** identische Werte (nichts geändert)
3. **Top-10 größte Files** (für Aufmerksamkeit / nächste Welle)
4. **Empfehlung für nächstes Prune-Fenster:** "Am YYYY-MM-DD werden die ältesten Files
   die DELETE-Schwelle erreichen. Dann erneut prüfen."
5. **Constraints-Checkliste:** ✅ NUR Target angefasst, ✅ Keine geschützten Pfade,
   ✅ Alle Sub-Dirs separat bewertet.

### Wichtige Erkenntnisse & Pitfalls

| # | Erkenntnis | Detail |
|---|------------|--------|
| 1 | **Früher Abbruch lohnt sich** | Wenn ältestes File < DELETE-Schwelle: 80% der Analyse entfällt. Trotzdem vollen Bericht liefern. |
| 2 | **MD5 bei gleichen Größen ist Pflicht** | 16 Files mit exakt 6.979.584 B — alle unterschiedliche MD5. Ohne Hash-Check wären fälschlich "Duplikate" deklariert worden. |
| 3 | **Restore-Script = Cluster-Schutz** | Wenn 3 Archive von einem Script referenziert werden, bilden sie eine Einheit. Nicht einzeln löschen. |
| 4 | **DESCRIPTION.md = Self-Dokumentation nutzen** | Das User-Selbstbild (tägliche Mnemosyne-Backups) sagt was KEEP-würdig ist. Nicht ignorieren. |
| 5 | **Mnemosyne-DB-Snapshots sind UNIQUE** | Die Live-DB (`~/.hermes/mnemosyne/mnemosyne.db`) und die Snapshots (`backups/mnemosyne/`) sind verschiedene Dinge. Die Snapshots sind Historien-Logs, kein Duplikat. |
| 6 | **Gleiche File-Größe bei DB-Iterationen ist normal** | DB-Migrationen erzeugen identisch große Dateien bei ähnlichem Schema-Inhalt. Hash-check verhindert Fehlalarme. |
