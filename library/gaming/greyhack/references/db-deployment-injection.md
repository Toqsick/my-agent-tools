# GreyHack DB — Build-Artifact Deployment (5-Agent-Injection-Pipeline)

**Stand:** 2026-07-04
**Kontext:** Agent (Yuno) hat keinen In-Game-Filesystem-Zugriff. Die DB-Injection via `Files`-Tabelle ist der Weg, um Build-Artifakte in Config/ zu platzieren, damit sie im CodeEditor (Ctrl+O) sichtbar werden und im Spiel gebaut werden können.

## Wann anwenden

- Benutzer sagt "schreib die .src in config" oder "inject in db"
- Benutzer will 5 Subagenten orchestrieren: "ordere eine orchestrierung mit 5 sub agenten"
- Ein Build-Artifact (>30 KB) muss in Config/ landen aber Copy-Paste ist zu groß
- Spiel läuft und CodeEditor-Workflow ist gewünscht

## Das 5-Agent-Pattern

```
Agent 1: Prep    → Read artifact, add //command: header, stage ready-file
Agent 2: Schema  → Analyze Files table for Config/ entries (ID format, refCount)
Agent 3: Inject  → Backup DB, INSERT INTO Files with proper Config/ path
Agent 4: Verify  → Check ID, Content length, //command: prefix, refCount
Agent 5: Doku    → Write deployment README with CodeEditor workflow
```

### Phase 1: Prep — `//command:`-Header injectieren

Jeder Source-Script-Eintrag in der `Files`-Tabelle **MUSS** `//command: <name>` als erste Zeile haben. Ohne diesen Marker erkennt das Spiel die Datei nicht als Script.

**⚠️ Uglified Builds:** greybel `-u` produziert Build-Output OHNE `//command:`-Marker. Vor dem DB-Insert MUSS `"//command: <name>\n"` prepended werden.

**Content-Limits:**
- Files <30 KB → CodeEditor Copy-Paste (sicher)
- Files 30-100 KB → DB-Injection direkt per INSERT INTO Files
- SQLite TEXT kann ~1 Billion Zeichen — nie das Problem

### Phase 2: Schema — Config/-Pfad-Struktur (⚠️ RELATIVER Pfad, korrigiert 2026-07-04)

Die existierende Injektion (`Config/yuno.src`, 46288 bytes, refCount=1) verwendet einen **RELATIVEN Pfad-String als ID**. KEIN absoluter Pfad!

Die `Files`-Tabelle hat ZWEI ID-Klassen:
- **UUID/MD5** (246/247 Einträge) — via `Computer.FileSystem` JSON referenziert.
- **Pfad-String** (1 Eintrag: `Config/yuno.src`) — erzeugt durch in-game `touch()`/`set_content()`. refCount=1 für frische Dateien.

Wichtig: `INSERT INTO Files` mit Pfad-ID allein macht die Datei NICHT automatisch im Game sichtbar. Sie ist nur im Blob-Store persistiert. Für Sichtbarkeit muss entweder ein `Computer.FileSystem`-JSON-Eintrag ergänzt werden, ODER das Spiel generiert ihn via `touch()` + `set_content()`.

```sql
SELECT ID, length(Content) as content_len, refCount
FROM Files WHERE ID LIKE 'Config/%' LIMIT 10;
```
ID-Format (empirisch): **`Config/<name>.src`** — relativer Pfad, kein absoluter.

### Phase 3: Injection

```bash
# Backup
cp "/path/to/GreyHackDB.db" "/path/to/GreyHackDB.db.backup-$(date +%Y%m%d-%H%M)"

# Content vorbereiten + Insert
python3 -c "
import sqlite3
with open('/tmp/ready.src') as f:
    content = f.read()
db = sqlite3.connect('/path/to/GreyHackDB.db')
db.execute('INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)',
           ('Config/yuno_v6.src', content))   # ⚡ RELATIVER Pfad!
db.commit()
print(f'Injected {len(content)} bytes')
"
```

### Phase 4: Verify

```sql
SELECT ID, length(Content), substr(Content,1,25), refCount
FROM Files WHERE ID = 'Config/yuno_v6.src';
```

### Phase 5: Doku

Nach Injection: Deployment-README in `~/docs/system/` mit CodeEditor-Workflow (Ctrl+O → Config/ → Build).

## Pitfalls

1. **Build ≠ Source** — Uglified (169 minifizierte Namen). Nicht modular splitten, als Ganzes deployen.
2. **`//command:` muss Byte 1 sein** — Nicht Zeile 2, nicht nach Leerzeile.
3. **ID = RELATIVER Pfad** `Config/name.src` (!!!) — NICHT absolut `/home/gregor/Config/name.src`. Empirisch verifiziert am existierenden Eintrag `Config/yuno.src`.
4. **DB-Backup vor jedem Inject** — timestamp im Dateinamen.
5. **code-editor UI-Limit unbekannt** — 45KB hat geklappt, 66KB existieren in Live-DB.
6. **Pfad-String-IDs sind SEPARAT von UUID-ID-Klasse** — `Files.ID` `Config/yuno.src` und `Computer.FileSystem` JSON-Referenzen nutzen unterschiedliche ID-Welten (`Config/yuno.src` hat keinen FileSystem-Eintrag).

## Siehe auch

- `references/in-game-db-edit.md` — Allgemeiner DB-Injection-Workflow
- `references/yuno-v6-architecture.md` — V6 Architektur
- `references/storage-consolidation.md` — Script-Konsolidierung
