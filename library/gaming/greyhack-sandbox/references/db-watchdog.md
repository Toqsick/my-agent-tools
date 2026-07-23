# DB Watchdog — Per-Table Hash Comparison (Cron Pattern)

Die ATTACH-Diff-Methode oben erkennt **neue Zeilen**, übersieht aber **Content-Änderungen in bestehenden Zeilen** (z.B. `Files.refCount`-Bumps, `Computer.FileSystem`-Updates, `Logs`-Erweiterungen, `Map.LibVersions`-Mutationen). Für einen echten Watchdog brauchst du **per-table SHA256-Hashing** über Python — die sqlite3-CLI hat kein `md5()`.

**Technik:** Statt zeilenweiser Diffs werden alle Zeilen einer Tabelle als deterministischer Hash-String konkatiniert und mit SHA256 gehasht. Ändert sich der Hash → mindestens eine Zeile hat sich geändert.

**Warum nicht ATTACH allein:** Die ATTACH-Methode (`LEFT JOIN WHERE s.ID IS NULL`) findet NUR neue IDs. Wenn ein existierender File-Eintrag seinen `refCount` von 1→2 ändert oder ein Computer sein FileSystem-JSON-Update erhält, bleibt ATTACH blind. Der Hash-Catch deckt beides ab.

```python
import sqlite3, hashlib

def table_hash(path, table, columns):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        cur = c.cursor()
        sel = ", ".join(columns)
        cur.execute(f"SELECT {sel} FROM {table} ORDER BY rowid")
        rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x00".join(str(x) if x is not None else "" for x in r) + "\n").encode("utf-8", "ignore"))
    return h.hexdigest()[:16]

# Beispiel: welche Spalten pro Tabelle hashen
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
```

**State-File-Pattern (db-state.json):** Statt bei jedem Lauf zwei Snapshots zu laden, persistiere `{hashes, counts, last_snap}` in `~/.local/share/maxclaw/db-state.json`:

```json
{
  "last_snap": "GreyHackDB-20260704-0531.db",
  "last_run": "2026-07-04T05:31",
  "hashes": {
    "Computer": "40fce258ff52bfd3",
    "Files": "6c65179790a148e8"
  },
  "counts": { "Computer": 18, "Files": 250 },
  "last_alert": { "tables": ["Files", "Passwords"], "summary": "2 new scripts, 6 pw" }
}
```

**Signal-Klassifikation im Watchdog:**
| Änderungstyp | Wahrscheinliche Interpretation |
|---|---|
| Neue `Files`-Einträge | Neue Scripts deployed (entweder per DB-Injection oder via `touch()`/`wget()`) |
| `Files.refCount` erhöht | Bestehendes Script wurde von einer weiteren Shell referenziert (= Tool aktiv genutzt) |
| Neue `Passwords` **+ neue `Logs`** | SMTP-Enum, Crack-Versuch oder SSH-Erfolg — **aktiver Angriff**, neue Credentials aufgetaucht |
| Neue `Passwords` **OHNE** neue `Logs` | **Stale SMTP-Cache** — Spiel committed alte Enum-Funde beim nächsten Save. KEIN Player-Event. Erkennbar an Passwords-Delta > 0 bei Logs-Delta = 0 und Files-Delta = 0. |
| Neue `Logs` + bekannter `tokenTrace` | Fortsetzung der aktuellen Spieler-Session |
| `Map.LibVersions` geändert   | NPC-Hintergrundaktivität — keine direkte User-Aktion |
| `Computer.FileSystem` geändert | Dateisystem-Manipulation durch Spieler |
| Hash-changed, count-unchanged + canonical-JSON-identisch | **Re-Serialization Noise (`clock_only_tick`)** — Spiel hat Save neu serialisiert (JSON-Key-Order/Whitespace-Drift), aber keine echten Daten-Änderungen. KEIN Alert, nur state.json updaten. GameOver=1 typisch. |

**Siehe:** `references/greyhack-db-watchdog-hash-pattern.md` — vollständiges Python-Script + Cron-Einrichtung + TokenTrace-Korrelation + **Canonical-JSON-Post-Hoc-Verifikation** (Hash-False-Positive-Filter für Re-Serialization-Noise).

**⚠️ Wichtige Erweiterung — Canonical-JSON False-Positive Filter:** SHA256-Hash-Diff allein reicht NICHT. GreyHack re-serialisiert beim Save alle JSON-Blobs (InfoGen.Clock-Tick, ModifiabilityToken). Das erzeugt SHA256-Hash-Änderungen **ohne** echten Daten-Delta — nur JSON-Key-Order/Whitespace-Drift. Der Hash-Diff ist Phase 1; Phase 2 muss **canonical-JSON-Normalisierung** auf allen geänderten Tabellen durchführen, bevor ein Alert ausgelöst wird. Siehe `references/greyhack-db-watchdog-hash-pattern.md` Abschnitt "Canonical-JSON Post-Hoc Verification".