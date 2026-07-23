---
name: game-library-management
description: "Use when user asks for game library management, archiving Steam libraries, optimizing game storage, .csd/.csm backups. NOT for playing games or installing individual games. Manage, archive, and optimize game libraries on Linux."
version: 1.0.0
author: yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - games
    - steam
    - backups
    - compression
    - nvme
    - disk-space
    - zstd
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['game', 'libraries', 'games', 'game-library-management', 'library']
keywords: ['game', 'libraries', 'games', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['computer-use-game-reconnaissance', 'pixel-art']
---



# Game Library Management

Trigger: User fragt nach Steam-Backups, Plattenplatz, Spiel-Archivierung, NVMe-Kompression, oder Inventar seiner Spiele-Library.

## Grundlagen

### Steam-Verzeichnisstruktur
```

set -euo pipefail
steamapps/
├── common/              ← Aktive Installationen (entpackte Spieldaten)
│   └── <Spielname>/
├── appmanifest_*.acf    ← Registry-Dateien mit Name, AppID, InstallDir
├── <Spielname>/         ← Steam-Backups (.csd/.csm-Dateien)
├── compatdata/          ← Proton/Windows-Kompatibilitätsdaten
└── shadercache/         ← Shader-Cache (löschbar)
```

### Steam-Backup-Format (.csd/.csm)
- **.csd** = Content Stream Data (gepackte Spieldaten)
- **.csm** = Content Stream Manifest (Index/Metadaten)
- Bereits **komprimiert** — NOCHMAL packen lohnt sich NICHT
- Ladbar in Steam: `Steam → Backup & Wiederherstellen → Backup-Ordner auswählen`

### common/-Installationen
- Rohdaten, NICHT komprimiert
- Hier lohnt Archivierung mit **zstd** (sehr schnell auf NVMe)

## Workflow

### 1. Inventar erstellen
```bash

set -euo pipefail
python3 steam_inventory.py
```
Zeigt:
- Steam-Backups (.csd/.csm) mit Größe und Teile-Anzahl
- Installationen in common/
- Verwaiste/gemischte Daten

### 2. Platz sparen (Quick-Win)
Wenn ein Spiel in steamapps/<Name>/ als .csd-Backup existiert:
1. In Steam deinstallieren → entfernt aus common/
2. Backup bleibt erhalten
3. Bei Bedarf über Steam wiederherstellen

### 3. Archivierung (ohne Steam-Backup)
Für Installationen in common/ OHNE passendes .csd-Backup:
```bash

set -euo pipefail
python3 steam_archive.py archive "Spielname" --method zstd_fast
```

Methoden:
| Methode | Speed | Ratio | Wann? |
|---------|-------|-------|-------|
| zstd_fast | 🔥🔥🔥 400+ MB/s | ~75-85% | Standard auf NVMe |
| zstd_default | 🔥🔥 200 MB/s | ~70-80% | Platz knapp |
| zstd_max | 🐢 20-50 MB/s | ~65-75% | Langzeitarchiv |
| pigz_fast | 🔥🔥🔥 300+ MB/s | ~85-90% | Kompatibilität |

### 4. Extrahieren
```bash

set -euo pipefail
python3 steam_archive.py extract Archiv.tar.zst
```

### 5. Auto-Archive — verstaubte Spiele automatisch finden & archivieren

Findet Spiele in common/, die seit N Tagen nicht mehr gespielt wurden, und
archiviert sie. Nutzt das `LastPlayed` Feld aus `appmanifest_*.acf`:

```bash

set -euo pipefail
# Vorschau: finde Spiele, die seit >= 30 Tagen nicht gespielt wurden
python3 steam_archive.py auto-archive --days 30 --dry-run

# Echt: archivieren (fragt vorher nach Bestätigung)
python3 steam_archive.py auto-archive --days 60

# Ohne Rückfrage (für Cron/Skripte)
python3 steam_archive.py auto-archive --days 90 --yes --method zstd_max
```

**LastPlayed-Parsing aus appmanifest_*.acf (Regex):**
```python
import re, time

now = time.time()
with open("appmanifest_12345.acf") as f:
    content = f.read()

name_m = re.search(r'"name"\s+"([^"]+)"', content)
lastplayed_m = re.search(r'"LastPlayed"\s+"(\d+)"', content)
size_m = re.search(r'"SizeOnDisk"\s+"(\d+)"', content)

last_played = int(lastplayed_m.group(1)) if lastplayed_m else 0
# last_played == 0 → nie gespielt, als sehr alt behandeln (days_ago = 9999)
days_ago = 9999 if last_played == 0 else int((now - last_played) / 86400)
```

set -euo pipefail
**Wichtig:** `LastPlayed == 0` heißt "nie gespielt" (Spiel installiert, aber
nie gestartet). Solche Spiele zählen als stale. Die Funktion `find_stale_games()`
prüft auch, ob der Spielordner unter `common/<installdir>` wirklich existiert
— nur dann gilt es als "installiert".

**Synthetischer Test bei fehlender DATA-Platte:**
Wenn `STEAM_ROOT` nicht existiert (z.B. DATA-Platte nicht gemountet), NICHT
als "läuft leer durch = ok" abhaken. Stattdessen mit temporären ACF-Fixtures
testen:

```python
import steam_archive, tempfile, os, time
tmp = tempfile.mkdtemp()
steamapps = os.path.join(tmp, "steamapps")
common = os.path.join(steamapps, "common")
os.makedirs(common)

now = int(time.time())
for appid, name, installdir, days, size in [
    ("111", "Frisch", "FreshGame",  2,    5_000_000_000),
    ("222", "Alt",    "OldGame",    90,   30_000_000_000),
    ("333", "Nie",    "NeverGame",  None, 12_000_000_000),
]:
    lp = 0 if days is None else now - days * 86400
    acf = f'...appmanifest_{appid}.acf mit name, installdir, LastPlayed, SizeOnDisk...'
    with open(os.path.join(steamapps, f"appmanifest_{appid}.acf"), "w") as f:
        f.write(acf)
    os.makedirs(os.path.join(common, installdir))

steam_archive.STEAM_ROOT = steamapps
stale = steam_archive.find_stale_games(min_days=30)
assert {g['name'] for g in stale} == {"Alt", "Nie"}
assert stale[0]['name'] == "Alt"  # Größen-Sortierung: 30GB vor 12GB
```

## Pitfalls

1. **NIE .csd/.csm Backups nochmal komprimieren** — sind schon gepackt, Zeitverschwendung
2. **appmanifest_*.acf nicht löschen** — Steam braucht sie zur Identifikation
3. **compatdata/ ist Proton-Wein** — enthält Windows-Registry-Einträge, oft mehrere GB pro Spiel
4. **LABEL statt UUID für Mountpoints** — `/etc/fstab` mit `LABEL=DATA` ist wartbarer als UUID

## Support-Dateien

- `references/steam-backup-formats.md` — Details zu .csd/.csm und appmanifest.acf
- `templates/steam_inventory.py` — Inventar-Scanner
- `templates/steam_archive.py` — Archivierungs-Toolkit (zstd/pigz)
