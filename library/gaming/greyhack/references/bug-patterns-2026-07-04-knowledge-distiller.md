# Bug Patterns — Knowledge Distiller Round 2026-07-04 (NP-69 bis NP-73)

> **Quelle:** Knowledge-Distiller-Cron 2026-07-04
> **Kontext:** Weekly Insights KW 27, Analyse von 6 Doku-Files + GreyHackDB.db-Snapshot + MaxClaw v3-Upgrade
> **Vorgänger:** `bug-patterns-2026-06-19-round11.md`, `known-bugs.md` (NP-18–NP-67)

---

## NP-69: `yuno defend` stürzt ab bei Ports ohne `service`-Map-Field

**Symptom:** `yuno defend` im Spiel crasht wenn ein Port-Objekt aus dem Mock-Env keine `service`-Property hat. TypeError bei `typeof` + `indexOf` auf nicht-existenter Map-Property.

**Repro:**
- Mock-Env (greybel execute) gibt Ports zurück die NUR `portInfo["Port"]` haben aber kein `portInfo["Service"]`
- `yuno defend` iteriert über Ports und greift auf `p.service` zu → TypeError

**Fix:** Robuster `typeof()`-Guard + `indexOf` vor jedem Map-Zugriff:
```greyscript
if typeof(p.service) == "string" and p.service != "" and p.service != null then
    // Zugriff ist safe
end if
```
**Datei:** `yuno.src` / `yuno_v6.src`, Zeile 409-427.

**Status:** ✅ Gefixt + re-tested (2026-07-03)
**Quelle:** `~/docs/system/greyhack-storage-cleanup-2026-07-03.md:108-114`

---

## NP-70: Multi-Agent-Truncation bei FileSystem-JSON >15 KB

**Symptom:** Subagenten mit großen JSON-Strukturen (z.B. `Computer.FileSystem` mit 418 Verzeichnissen) werden truncated. In einem 3-Experten-Deep-Dive (2026-07-04) brauchte die Content-Expertin 359s / 56 API-Calls, 2 von 3 Reports waren truncated.

**Ursache:** `delegate_task` Subagenten haben keine spezielle JSON-Handling-Logik. Große JSON-Spalten aus SQLite (FileSystem-Bäume, ConfigOS) überschreiten den Context-Window.

**Mitigationen:**
1. **Max API-Calls auf 40 begrenzen** im Subagent-Briefing
2. **Struktur-zuerst-Ansatz:** Bei FileSystem-Analysen erst Baumstruktur zählen, dann gezielt Sub-Pfade lesen
3. **4. Expertin als Validatorin** — reviewt Claims der ersten 3 Agenten und merkt Truncation an
4. **Output immer auf Disk sichern** — `write_file(path, output)` vor Session-Ende, auch wenn truncated

**Quelle:** `~/docs/system/greyhack-deep-research-2026-07-04.md:101-118`

---

## NP-71: `hermes cron create --model` still ignoriert

**Symptom:** `hermes cron create ... --model heavy` wird akzeptiert (kein Fehler) aber das Flag wird ignoriert. Der Cron läuft mit dem Default-Modell.

**Repro:**
- `hermes cron create --name greyhack-knowledge-distiller --schedule "0 22 * * 0" --skill greyhack --model heavy`
- Cron wird erstellt aber `hermes cron list` zeigt kein model-Feld
- `hermes cron create --help` listet `--model` gar nicht als Parameter (verified 2026-07-04)

**Workaround:** `register-workflows.sh` nutzt `model`-Werte im `JOBS`-Array nur intern (`model_args` statt `--model`). Nachträgliches Model-Pin via:
```bash
cronjob action=update job_id=<id> model=heavy provider=nous
```

**Pitfall erkannt:** Cron-CLI parst vielleicht `--model` als unbekanntes Flag und ignoriert still — kein Error-Exit. Immer `--help` auf neue CLI-Optionen prüfen.

**Quelle:** `~/docs/system/maxclaw-v3-upgrade-2026-07-04.md:48-52`
**Siehe auch:** Multi-Agent-Pitfalls-Cheatsheet (Pitfall #10: `hermes cron create` CLI-Caveats)

---

## NP-72: Dual-ID-Class in `Files`-Tabelle

**Symptom:** SELECT aus GreyHackDBs `Files`-Tabelle liefert IDs die entweder UUID/MD5 (246/247 Einträge) oder Pfad-Strings (1 Eintrag: `Config/yuno.src`) sind. Beide Klassen funktionieren, aber eine DB-Injection mit Pfad-ID allein macht die Datei nicht im Game sichtbar.

**Konsequenz für DB-Injection:**
```sql
-- ❌ REICHT NICHT — Datei bleibt unsichtbar
INSERT INTO Files (ID, Content, refCount) VALUES ('tools/my_tool.src', '...', 1);

-- ✅ RICHTIG — auch Computer.FileSystem-JSON updaten
-- 1. File mit UUID-ID einfügen
-- 2. Computer.FileSystem-JSON: neuen Eintrag mit UUID im "files"-Array ergänzen
```

**Prüfung vor Deployment:** `SELECT ID FROM Files WHERE ID NOT LIKE '%-%'` zeigt Pfad-String-IDs. Für neue Dateien immer UUID generieren.

**Quelle:** GreyHack Skill SKILL.md, `Dual-ID-Class Discovery (2026-07-04)` Sektion

---

## NP-73: `//command:` Marker + Config/-Pfad zwingend für Build-Erkennung

**Symptom:** Source-Skripte die OHNE `//command:` als erste Zeile angelegt werden, erkennt GreyHack nicht als Script ("Can't build. Binary file." beim Build-Versuch). Auch Dateien im falschen Pfad (`/home/<USER>/` statt `/home/<USER>/Config/`) werden nicht als Commands erkannt.

**Validierung bei DB-Injection:**
```python
if not content.startswith("//command:"):
    raise ValueError("Missing //command: marker — script won't be detected as command")
```

**Pfad-Regel:**
- `/home/gregor/Config/<name>.src` → ✅ Command erkennbar
- `/home/gregor/<name>.src` → ❌ Nicht als Command erkennbar

**Quelle:** GreyHack Skill SKILL.md ("KRITISCH: //command: Marker + Config/ Pfad für Source-Scripts (NEU 2026-07-03)")

---

## Patterns ohne NP-Nummer (Beobachtungen aus der Session)

### P-WI-1: Input-Substitutions-Pattern
Wenn ein Cron-Job erwartete Input-Pfade nicht findet:
1. Alternative Quellen identifizieren (`find -newermt`)
2. CWD auf `/tmp/`-Installation checken (temp-Clone?)
3. `hostname`, `pwd`, `whoami` für Environment-Context
4. Im Ergebnis klar als "substituiert" markieren (Audit-Hinweis im Footer)

### P-WI-2: Zeitfenster-Eingrenzung
```bash
find ~/docs/system ~/greyhack-tools -type f -newermt "YYYY-MM-DD" 2>/dev/null | sort
```
`-newermt` filtert exact. Zeitspanne immer ±1 Tag offen lassen (Vorwoche + aktuellen Tag).
