# Steam Backup Formate & Struktur

## .csd / .csm — Steam's proprietäres Backup-Format

- **.csd** (Content Stream Data) — Die eigentlichen gepackten Spieldaten
- **.csm** (Content Stream Manifest) — Metadaten/Index für die .csd-Teile
- **sku.sis** — Spiel-Identifikation (oft verschlüsselt/obfuskiert)

### Eigenschaften
- Bereits komprimiert (keine zusätzliche Kompression sinnvoll)
- Ladbar in Steam: `Steam → Backup & Wiederherstellen → Backup-Ordner`
- Mehrteilige Archive (depotcache_1.csd, depotcache_2.csd, ...)

### Wichtige Pfade
```
steamapps/
├── common/              ← Aktive Installationen (entpackt)
│   ├── ABInfinite/
│   └── ProjectZomboid/
├── appmanifest_*.acf    ← Steam's Spiel-Registry (Name, AppID, InstallDir)
│   ├── "appid" "12345"
│   ├── "name" "Project Zomboid"
│   └── "installdir" "ProjectZomboid"
├── <Spielname>/         ← Steam-Backups (.csd/.csm)
│   ├── 12345_depotcache_1.csd
│   ├── 12345_depotcache_1.csm
│   └── sku.sis
└── compatdata/          ← Proton/Windows-Kompatibilitätsdaten
```

### appmanifest.acf parsen (Regex)
```python
import re

patterns = {
    'appid': r'"appid"\s+"(\d+)"',
    'name': r'"name"\s+"([^"]+)"',
    'installdir': r'"installdir"\s+"([^"]+)"',
    'SizeOnDisk': r'"SizeOnDisk"\s+"(\d+)"',
}
```

### Kompressions-Empfehlungen
| Quelle | Bereits komprimiert? | Empfohlene Aktion |
|--------|---------------------|-------------------|
| .csd/.csm Backups | JA (Steam-eigen) | Nicht nochmal packen |
| common/ Installationen | NEIN (Rohdaten) | zstd Level 1 (schnell) |
| Texturen/Audio in common/ | Teilweise (Ogg, DDS) | Wenig Platzgewinn |
| Shader-Cache | NEIN | Optional löschen |
