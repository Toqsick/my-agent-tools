# DB Watchdog — Per-Table Hash Comparison Pattern

**Entstanden:** 2026-07-04 (Cron-Lauf, maxclaw-Workflow)  
**Problem:** Die ATTACH-Database-Diff-Methode (`LEFT JOIN WHERE s.ID IS NULL`) erkennt nur **neue Zeilen**, übersieht aber Content-Änderungen in bestehenden Zeilen (`Files.refCount`-Bumps, `Computer.FileSystem`-Updates, `Map.LibVersions`-Mutationen).

## Kernel: Per-Table SHA256 Hash Comparison

```python
import sqlite3, hashlib, os, json

SNAPDIR = os.path.expanduser("~/.local/share/maxclaw/snapshots")
STATE_FILE = os.path.expanduser("~/.local/share/maxclaw/db-state.json")

# Welche Spalten pro Tabelle in den Hash eingehen
WATCH_SCHEMAS = {
    "Computer":     ["ID", "FileSystem", "Hardware", "ConfigOS", "Procs", "Users"],
    "MailAccounts": ["User", "Mails", "password"],
    "Passwords":    ["ID", "PlainPassword"],
    "BankAccounts": ["User", "Transactions", "Password"],
    "Logs":         ["ID", "Log"],
    "Map":          ["IpAddress", "Bssid", "Essid", "WebAddress", "Mission", "LibVersions"],
    "Files":        ["ID", "Content", "refCount"],
    "Players":      ["PlayerID", "ComputerID", "Missions", "TokenTrace"],
    "WebPages":     ["PublicIp", "LocalIp", "Web", "Address"],
    "InfoGen":      ["Seed","VersionsControl","Exploits","Guilds","Clock","DeleteVersion","AllLibs","Invoices","GlobalMoney","ZeroDaySystem"],
}

def table_hash(path, table, columns):
    """Deterministischer SHA256-String-Hash aller Zeilen einer Tabelle."""
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        cur = c.cursor()
        sel = ", ".join(columns)
        cur.execute(f"SELECT {sel} FROM {table} ORDER BY rowid")
        rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x00".join(str(x) if x is not None else "" for x in r) + "\n")
                 .encode("utf-8", "ignore"))
    return h.hexdigest()[:16], len(rows)
```

## Workflow (ein Cron-Lauf)

```
1. sqlite3 -readonly DB .backup -> snapshots/GreyHackDB-$TS.db
2. Für jede Tabelle in WATCH_SCHEMAS:
     cur_hash, cur_rows = table_hash(snap, table, cols)
     prev_hash = state["hashes"].get(table)
     if prev_hash and cur_hash != prev_hash:
         -> Mögliche Änderung — Phase 2 erforderlich!
3. Phase 2 — canonical-JSON-Verifikation (nur bei geänderten Tabellen OHNE Row-Count-Delta):
     Für jede Tabelle t, deren hash_changed == True aber rows_unchanged:
       Selecte alle Zeilen (alte & neue DB)
       Vergleiche canonical-normalisiert: json.dumps(json.loads(x), sort_keys=True)
       Wenn canonical-equivalent auf ALLEN Zeilen → clock_only_tick (Re-Serialization Noise)
       Nur bei canonical-different oder neuer Zeile → echte Änderung, Alert auslösen
4. state.json aktualisieren: hashes, counts, last_snap, last_alert
5. Nur bei echten Änderungen: alert ausgeben (sonst [SILENT])
```

## Canonical-JSON Post-Hoc Verification (False-Positive-Filter)

**Problem:** GreyHack re-serialisiert beim Save alle JSON-Blobs (InfoGen.Clock-Tick, Computer.FileSystem, MailAccounts.Mails, BankAccounts.Transactions, etc.). Dabei ändern sich:
- JSON-Key-Reihenfolge (Python-dict hat stabile Keys, C#-JSON-Serializer nicht)
- Whitespace/Indentation
- ModifiabilityToken (eine interne GameSeed, die bei jedem Save neu generiert wird)

Diese Änderungen erzeugen SHA256-Hash-Deltas **ohne** echten Daten-Delta. Im Watchdog führt das zu False-Positives: 6/10 Tabellen zeigen Hash-Änderung, aber 0 echte Daten-Änderungen.

**Lösung:** Nach dem Hash-Phase-1 eine canonical-JSON-Normalisierung für alle Tabellen mit **hash-changed aber count-unchanged**:

```python
import json, re

def canon(s):
    """Normalisiert JSON-Strings deterministisch: sortierte Keys, keine Whitespace-Unterschiede."""
    if not s or s.strip() == "":
        return s.strip() if s else ""
    try:
        obj = json.loads(s)
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    except (json.JSONDecodeError, ValueError):
        # Nicht-JSON — einfache Whitespace-Normalisierung
        return re.sub(r'\s+', ' ', s.strip())

def verify_canonical_equality(path_new, path_old, table, columns):
    """Prüft ob zwei DB-Snapshots für eine Tabelle canonical-äquivalent sind."""
    def fetch_all(p):
        with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as c:
            cur = c.cursor()
            sel = ", ".join(columns)
            cur.execute(f"SELECT {sel} FROM {table} ORDER BY rowid")
            return cur.fetchall()

    a = fetch_all(path_new)
    b = fetch_all(path_old)

    if len(a) != len(b):
        return False, f"Row count differs: {len(b)} → {len(a)}"

    diffs = 0
    for i, (ra, rb) in enumerate(zip(a, b)):
        for ca, cb, col in zip(ra, rb, columns):
            ca_c = canon(str(ca)) if ca is not None else ""
            cb_c = canon(str(cb)) if cb is not None else ""
            if ca_c != cb_c:
                diffs += 1
                # Nur erste Abweichung loggen
                return False, f"Row {i}, col '{col}': canonical diff"

    return True, f"Canonical-equivalent: {len(a)} rows, {len(columns)} cols"

# Integration in den Watchdog-Loop:
changed_tables = [t for t in WATCH_SCHEMAS if cur_hashes[t] != prev_hashes[t] and cur_counts[t] == prev_counts[t]]
for t in changed_tables:
    eq, reason = verify_canonical_equality(snap_path, old_snap_path, t, WATCH_SCHEMAS[t])
    if eq:
        log(f"  {t}: {reason} → clock_only_tick, suppressing alert")
    else:
        log(f"  {t}: REAL CHANGE → {reason}")
        trigger_alert(t)
```

**Signal-Klassifikation `clock_only_tick`:**
| Symptom | Diagnose | Aktion |
|---------|----------|--------|
| Hash-Changed + Counts-Unchanged | Re-Serialization Noise | KEIN Alert, nur state.json updaten |
| Hash-Changed + Row-Count-Delta | Neue/entfernte Zeilen | Alert auslösen, Details zeigen |
| Hash-Changed + canonical-different | Echter Daten-Delta | Alert auslösen |
| Zwei+ aufeinanderfolgende `clock_only_tick` für selbe Tabellen | GameOver=1 inert state | Optional: Cron-Intervall erhöhen (30→60 min) |

**Entdeckt:** 2026-07-06, Watchdog Run 04:32 UTC. 6/10 Tabellen zeigten Hash-Diff aber 0 canonical-Diffs bei GameOver=1.

## Signal-Klassifikation `npc_background_tick` (NEU 2026-07-06)

**Beobachtung:** Drei Computer-Reihen ändern sich (Player-PC `Procs` + 2 NPCs `ConfigOS.networkLan`/`personas`), aber **alle** Player-Spur-Tabellen sind null-Delta:
- `Files`: Row-Count unverändert, keine neuen Einträge
- `Passwords`: Row-Count unverändert (kein SMTP-Enum, kein Stale-Cache-Flush)
- `Logs`: Row-Count unverändert (kein neuer Spieler-Action-Code 0-4)
- `MailAccounts`: keine Mails-Längen-Diff
- `BankAccounts`: keine Tx-Längen-Diff
- `Map`: Row-Count unverändert

**Diagnose:** NPC-Hintergrundsimulation + Player-PC Kernel-Save-Tick (laufende Prozesse). Reines Re-Serialization-Noise + NPC-Save-Mutation, **kein Player-Event**.

**Watchdog-Logik (Player-Spur-Filter vor Alert):**
```python
# Player-Spur-Tabellen — wenn ALLE null-Delta UND nur Computer/InfoGen-Tabellen canonical-diff haben,
# dann ist es NPC-Hintergrundtick, nicht Player-Event.
PLAYER_TRACE_TABLES = {"Files", "Passwords", "Logs", "MailAccounts", "BankAccounts", "Map"}

def classify_with_player_filter(changed_tables):
    real_player_tables = [t for t in changed_tables if t in PLAYER_TRACE_TABLES]
    npc_or_procs_tables = [t for t in changed_tables if t in {"Computer", "InfoGen"}]

    # Echter Player-Event: Player-Spur-Tabelle hat canonical-diff
    if real_player_tables:
        return "real_change", real_player_tables

    # Reine NPC/Procs-Mutation ohne Player-Spur = Hintergrundtick
    if npc_or_procs_tables and not real_player_tables:
        return "npc_background_tick", npc_or_procs_tables

    return "real_change", changed_tables
```

**Erkennungsregel:** `Computer` und `InfoGen` canonical-Änderungen sind **kein** Player-Event, **wenn** alle Player-Spur-Tabellen (`Files`, `Passwords`, `Logs`, `MailAccounts`, `BankAccounts`, `Map`) Row-Count-stabil UND canonical-stabil sind.

**Wann NICHT demoten:** Wenn `Files`-Row-Count steigt → `npc_background_tick` ist **falsch** (Spieler hat neues Script deployed → echtes Event). Ebenso: Wenn `Passwords`+`Logs` gleichzeitig steigen → aktiver Angriff (siehe "Neue Passwords + Logs" oben).

**Konkrete Praxis-Beispiele:**

- **11:31 UTC (3 Computer, NPC-dominant):** Player-PC `171a9e0f-…`: Procs canonical-DIFFERENT aber length-identical (614 Bytes beide) → Kernel-Save-Tick. NPC `219.50.230.162:…`: ConfigOS +1017 Bytes (`networkLan` + `personas`). NPC `197.48.117.207:…`: ConfigOS +192 Bytes (`networkLan` + `personas`). Alle Player-Spuren null → `npc_background_tick`, **silent**.
- **14:02 UTC (1 Computer, single-source trigger — der häufigste Fall):** NUR Player-PC `171a9e0f-…` `Procs` 2606B → 3394B (+788B). Alle Player-Spuren null (Files 256/256, Passwords 282/282, Logs 22/22, Mail 7/7, Map 56/56, BankAccounts 4/4). Watchdog flaggte fälschlich `content_diff` weil Phase-3-Filter fehlte. Nach Patch: korrekt `npc_background_tick`, **silent**. Wichtig: **auch ein einzelner** Computer mit `Procs`-Mutation ohne Player-Spur-Tabellen-Änderung fällt in diese Klasse.

**Unterschied zu `clock_only_tick`:** `clock_only_tick` = Hash-Changed aber canonical-JSON-äquivalent (Re-Serialisierung). `npc_background_tick` = canonical-DIFFERENT (echte NPC-Mutationen) aber **nicht** Player-relevant. Beide sind silent — aus verschiedenen Gründen.

## Self-Test: rewind-and-rerun (Pattern-Verifikation)

**Wann:** Nach jedem Patch am Watchdog-Phase-3-Block, oder wenn du vermutest, dass der Filter nicht greift.

**Prozedur:**
```bash
# 1. Setze last_snap in db-state.json auf den ZULETZT erzeugten Snapshot
python3 /tmp/rewind_state.py   # helper: state["last_snap"] = last_snap_in_snapshots_dir

# 2. Watchdog nochmal laufen lassen — vergleicht jetzt gegen den soeben erzeugten Snapshot
python3 scripts/greyhack-db-watchdog.py

# 3. Erwartete Output bei korrektem Phase-3-Filter:
#    --- Classification ---
#      Real diff: True
#      New rows:  False
#      Diff tables: [('Computer', 'content_diff')]
#      Classification override: npc_background_tick (only Computer/InfoGen changed, player traces stable)
#
#    [SILENT] npc_background_tick — no player event. State updated.

# 4. Wenn Override fehlt → Phase-3-Filter nicht im Code, nur in der Doku (siehe Pitfall #28).
```

**Wichtig:** Die zwei Snapshot-Dateien müssen existieren (`last_snap` zeigen auf existierende .db, neuer Snapshot mit aktueller DB). Sonst läuft der Watchdog im First-Run-Modus ohne Vergleich.

**Helper-Script-Template (`/tmp/rewind_state.py`):**
```python
import json
from pathlib import Path

state_path = Path.home() / ".local/share/maxclaw/db-state.json"
snap_dir = Path.home() / ".local/share/maxclaw/snapshots"
state = json.loads(state_path.read_text())

# Nimm den ZWEITLETZTEN Snapshot (der gerade erzeugte ist der "current" — wir wollen den davor)
all_snaps = sorted(snap_dir.glob("GreyHackDB-*.db"))
if len(all_snaps) >= 2:
    state["last_snap"] = all_snaps[-2].name
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    print(f"Rewound to {state['last_snap']}")
else:
    print("Need at least 2 snapshots for rewind test")
```

**Trigger für diesen Test:** Watchdog flaggt etwas als `content_diff`/`real_change`, das laut Pitfall #27 eigentlich `npc_background_tick` sein sollte. Das ist das **Symptom** für fehlenden Phase-3-Filter im Code.

## Wichtige Details

### Warum Python, nicht sqlite3 CLI?

```bash
# ❌ Geht nicht
sqlite3 db.db "SELECT md5(content) FROM Files"
# Error: no such function: md5
```

sqlite3 CLI hat kein `md5()`/`sha256()`. Die `table_hash()`-Funktion in Python löst das.

### Null-Handling im Hash

Alle Werte werden per `str(x) if x is not None else ""` normalisiert — ein `NULL`-Feld erzeugt denselben Hash-Contrib wie ein leeres String-Feld. Das ist akzeptabel, weil:
- `NULL`-Felder im GreyHack-Schema sind meist immer NULL oder immer gefüllt (z.B. `Map.Mission DEFAULT ''`)
- Ein Watchdog will *irgendeine* Änderung melden — der Unterschied NULL vs `""` ist in diesem Kontext gleichwertig

### Warum SHA256[:16] statt voller Hash?

16 Hex-Zeichen = 64 Bit Kollisionswahrscheinlichkeit. Für einen Watchdog mit ~9 Tabellen à max. 273 Zeilen ist das sicher. Kürzere Hashes sind lesbarer im Debug-Output und in state.json.

## Signal-Anomalien aus der Praxis

### `Files.refCount`-Bump ohne neue Datei

| Timestamp | Datei | refCount vorher | refCount nachher |
|-----------|-------|----------------|-----------------|
| 05:07 | nmap (2a085349…) | 1 | 2 |
| 05:07 | scan-trace (15d9c68f-…) | 1 | 3 |

**Interpretation:** Der Spieler hatte zwei Shells/CodeEditor-Tabs offen, die auf dasselbe Script referenzierten. Oder der Spieler hat `shell.build()` mehrfach aufgerufen, was die refCount erhöht. Keine neue Funktionalität, aber der Spieler ist aktiv.

### Neue Files + Neue Passwords gleichzeitig

Zwei neue Files (`smtp-user-list`, `ssh-server`) tauchen auf + 6 neue Passwörter:

**Korrelation:** Spieler hat SMTP-Enum-Script deployed, auf Ziel-IPs losgelassen → 6 SMTP-User/Credentials extrahiert. Das `ssh-server`-Script deutet auf Vorbereitung für SSH-Lateral-Movement.

### Neuer Log-Eintrag mit bekanntem tokenTrace

```json
{"action":0, "ip":"219.50.230.162", "tokenTrace":"ee23d05c-6782-4aa8-8565-86e8d3045168"}
{"action":0, "ip":"158.14.166.104", "tokenTrace":"ee23d05c-6782-4aa8-8565-86e8d3045168"}
```

Ein neuer Log-Eintrag mit einer **bereits gesehenen** `tokenTrace`-UUID = Fortsetzung derselben Mission.
Ein neuer Log-Eintrag mit **neuer** `tokenTrace`-UUID = neue Session / neue Mission.

### Neue Passwords OHNE neue Logs (Stale SMTP-Cache)

**Beobachtung (2026-07-04, 06:05 Watchdog Run):** Drei neue Passwörter aufgetaucht:
- Missyca (7 Zeichen, pseudo-word)
- Raven (5 Zeichen, pseudo-word)
- Niell (5 Zeichen, pseudo-word)

**Aber:** Kein einziger neuer Log-Eintrag. Keine neuen Files. Keine neuen MailAccounts. Nur `Passwords`-Hash geändert.

**Interpretation:** Das Spiel kommitiert beim nächsten Save alte SMTP-Enum-Funde aus dem Prozess-Cache in die DB. Die Passwörter stammen von einer vorherigen Spiel-Session (SMTP-Enum auf einer früheren Mission), wurden aber erst jetzt in die DB geschrieben. **Kein aktiver Angriff, kein Player-Event.**

**Erkennungsregel im Watchdog:**
```python
# Nur wenn Passwords-Delta > 0 UND Logs-Delta > 0 => echter Angriff
if password_hash_changed and not logs_hash_changed and not files_hash_changed:
    log("Stale SMTP cache commit — no player event, suppressing alert")
    return SILENT
```

**Warum passiert das:** GreyHack puffert SMTP-Enum-Ergebnisse im Arbeitsspeicher und schreibt sie erst beim nächsten autosave/Save-Datensatz in die DB. Wenn der Spieler offline geht, werden diese Puffer in der nächsten Spiel-Session persistiert — auch wenn der Spieler selbst gar nichts tut.

**Abgrenzung:** Echte Angriffe erzeugen immer auch Logs (die Aktion selbst: Port-Scans, Exploit-Versuche, SSH-Verbindungen). Logs-Delta = 0 bedeutet: Es wurde keine Aktion ausgeführt, also können die Passwörter nur aus einem alten Cache stammen.

## Cron-Einrichtung

```bash
# State-File-Verzeichnis
mkdir -p ~/.local/share/maxclaw/snapshots

# Cron-Zeile (alle 30 min)
# */30 * * * * hermes run greyhack-watchdog --profile default > /dev/null 2>&1

# Rotation: max 96 Snapshots (= 48h bei 30-min-Takt)
ls -1t ~/.local/share/maxclaw/snapshots/GreyHackDB-*.db | tail -n +97 | xargs -r rm -f
```

## Verwandte Dokumente

- `greyhack-sandbox` SKILL.md — Hauptdokument mit Snapshot-Backup und ATTACH-Diff
- `references/greyhack-db-forensic-queries.md` — Multi-Table Query-Patterns (TokenTrace, Action-Codes)
- `references/greyhack-db-snapshot-workflow.md` — Snapshot-Setup + Rotation + Anomalieerkennung
- `scripts/greyhack-db-snapshot.sh` — Bash-Snapshot-Skript
- `scripts/greyhack-db-analyze.py` — Python-CLI: JSON-Extraktion + Summary
