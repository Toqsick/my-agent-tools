# Queen Pre-Execute While Bees Scout — Viper-Redeploy Worked Example

**Datum:** 2026-07-15  
**Kontext:** Basti sagte "nutze biene orchestration" für Viper neu aufsetzen  
**Präzedenzfall:** Erster Einsatz des Queen-Pre-Execute-Patterns

---

## Situation

- 5 Viper-Module aus DB-export (yuno_viper_core/scan/post/net/util.src)
- Alle 5 Module in `/tmp/viper-reexport/` (100 KB gesamt)
- Canonical Source klar: DB-export, kein Monolith `viper.src` (162 KB)
- Host-Tools: `greybel` buildbar, `sqlite3` lesbar/schreibbar, Fileserver erreichbar
- Früherer Deploy war kaputt (root/Config size=0 stubs, Viper monolith falsch eingecheckt)

## Dispatch (3 Scout-Bienen)

```python
delegate_task(tasks=[
    {"goal": "Biene A SOURCE: Inventar + Staging", ...},
    {"goal": "Biene B AUDIT: DB + FS Drift Matrix", ...},
    {"goal": "Biene C BUILD: greybel build 5 module", ...},
])
```

→ Direkt MACHWEITER — nicht auf Bee-Outputs warten.

## Queen Parallel-Arbeit

### 1. Source Backup + Staging (30s)
```bash
mkdir -p /tmp/viper-stage-redeploy /tmp/viper-queen \
  "/mnt/.../Grey Hack/yuno-tools/yuno_viper/" \
  "/mnt/.../Grey Hack/yuno-tools/phase-viper/"
cp -f /tmp/viper-reexport/*.src /tmp/viper-stage-redeploy/
cp -f /tmp/viper-reexport/*.src "/mnt/.../yuno-tools/yuno_viper/"
cp -f /tmp/viper-reexport/*.src "/mnt/.../yuno-tools/phase-viper/"
```

### 2. Build Gate — Queen verifiziert direkt (15s)
```bash
for f in /tmp/viper-stage-redeploy/*.src; do
  n=$(basename "$f" .src)
  greybel build "$f" "/tmp/viper-build/$n"
done
# → 5/5 BUILD_OK
```

### 3. Redeploy-Script schreiben (Queen-written, nicht Biene)
Schlüssel-Design:
- `--dry-run` Flag (dry-run ohne DB-Write)
- Auto-Backup mit Timestamp
- 5-Stufen-Verify (load → dry-run → backup → upsert → verify)
- `BEGIN IMMEDIATE` + `rollback` bei Exception

### 4. Dry-Run (5s)
```text
load yuno_viper_core.src: 14325 B cmd=yuno_viper
load yuno_viper_scan.src: 23600 B cmd=yuno_viper_scan
...
DRY RUN only — no DB write
 would upsert Config/yuno_viper_core.src 14325 B
 would upsert Config/yuno_viper_scan.src 23600 B
```

### 5. Live-Deploy (20s)
```text
backup: GreyHackDB.db.backup-viper-redeploy-20260715-011106
Files UPDATE Config/yuno_viper_core.src
...
FS link /home/gregor/Config/yuno_viper_core.src
...
root/Config size refresh yuno_viper_core.src
...
integrity ok
VIPER_REDEPLOY_OK
```

## Verify Loop

5-stufig:
1. Source-Header-Check (5/5 korrekter //command)
2. greybel build (5/5 BUILD_OK)
3. Dry-Run (0 side effects)
4. Post-Commit Verify (content equal=True 5/5, SHA256 match)
5. DB integrity_check (ok)

## Ergebnis

- **Wall-Time vom Dispatch bis zur Bestätigung:** ~90 Sekunden
- Bee-Initialisierung plus Arbeit: Bienen benötigen 2–3 Minuten
- **Queen war schneller fertig als die langsamste Biene initialisiert war.**
- Kein verlorener Kontext: Bienen landeten nach Queen-Finish und keine Post-Hoc-Korrektur nötig

## Bestätigung im Chat

> "Queen-Bee-Orchestrierung: Viper neu aufgesetzt ✅"

Und dann: der In-Game Guide war bereits geschrieben, als die Bienen noch gar nicht gelandet waren.

---

## Lessons

1. **Queen kann Build+Deploy eigenständig, wenn CLI-Tools lokal installiert sind.** Bienen sind hierfür nicht die richtige Abstraktionsebene.
2. **Schreibe immer ein Dry-Run-fähiges Script,** bevor du gegen eine Live-DB deployst — unabhängig davon ob Queen oder Biene ausführt.
3. **Der Queen-Pre-Execute-Pattern ist kein "Bienen ignonieren"-Pattern.** Die Bienen liefern Immervalidierung für Edge-Cases die Queen übersehen könnte (hier: root/Config vs gregor/Config Drift). Aber ihr Output ist nicht Gates, sondern Oversight.
4. **Datei-Affinity zwischen Queen und Bienen sicherstellen.** Queen schrieb nach `/tmp/viper-queen/` und `/tmp/viper-stage-redeploy/`. Bienen schrieben nach `/tmp/viper-bee-*.md`. Kein Overlap.