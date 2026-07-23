# Mod-Collections auf Linux (ohne Vortex installieren)

Trigger: User will eine große Nexus Mod-Collection (100+ Mods) installieren — typischerweise Vortex-only-Packs wie **City of Dreams** (v2sCollections), **Wasteland Companion**, **Overhaul 2.0**, etc.

## Vortex via Bottles: Bedingt nutzbar (Download-Tool)

Vortex ist Windows-only (.NET-WPF), aber **lässt sich via Bottles installieren** und als **Download-Tool** nutzen. Für das eigentliche Mod-Deployment taugt es nicht direkt, weil:

- **Prefix-Mismatch:** Vortex installiert in seinem Wine-Prefix (`bottles/Vortex-CP77/drive_c/`) — Steam-Proton-Prefix liegt woanders (`compatdata/1091500/pfx/`). Vortex kann nicht ins Proton-Prefix deployen.
- **Vortex macht nur File-Management** (Download + Sortierung + Load-Order) — die Mods laden via RED4ext/CET unabhängig.
- **3 GB Overhead** für den Wine-Prefix.

**Bottles-Setup für Vortex (Download-Modus):**

```bash
# Bottle erstellen
bottles-cli new -b "Vortex-CP77" --environment "Gaming" --version "soda-9.0-1" \
  --arch "win64" --dxvk "True" --vkd3d "True"

# Vortex-Installer silent installieren (NSIS /S)
bottles-cli run -b "Vortex-CP77" -e "$HOME/Downloads/vortex-setup-2.2.0.exe" -- "/S"
```

**Verwendung:** Vortex starten → Nexus-Login → Mods zur Collection hinzufügen → **nur Download**, nicht deploy! ZIPs liegen dann im Bottles-Downloads-Ordner und können manuell entpackt werden.

**Empfehlung:** Für 30 Mods lohnt sich Vortex+Bottles nicht (3 GB Overhead + Setup-Komplexität). Erst bei 100+ regelmäßigen Mod-Updates den Aufwand wert.

**Cleanup (wenn Vortex-Bottle nicht mehr gebraucht wird):**
```bash
# 1. Bottle-Definition löschen
bottles-cli rm -b "Vortex-CP77"

# 2. Verzeichnis löschen
rm -rf "~/.var/app/com.usebottles.bottles/data/bottles/bottles/Vortex-CP77/"

# 3. Wichtig: Vortex-Installer EXE BEHALTEN (~/Downloads/vortex-setup-*.exe)
#    für zukünftige Neuinstallationen. Installer ist nur 345 MB,
#    während der Bottle-Prefix ~3 GB frisst.

# 4. Journal-Eintrag bleibt (historische Referenz)
#    ~/.var/app/com.usebottles.bottles/data/bottles/journals/bottles.log
#    → bewusst nicht löschen, nützlich für Session-History
```

**Pattern: Dokumentieren → Löschen → Installer behalten.** Erst Doku schreiben, dann löschen. So bleibt das Wissen auch ohne die Bottle erhalten.

**Konsequenz für 1-bis-100-Mod-Installationen:** ZIPs manuell entpacken und selbst sortieren (siehe Workflow unten).

## Workflow für 100+ Mod-Collections

### Schritt 1: Mod-Liste aus GitHub-Repo der Collection holen (wenn vorhanden).

Viele große Collections pflegen ein öffentliches Repo mit `Mod-List.md`. Beispiel v2sCollections/City-of-Dreams:
```bash
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/Mod%20List.md" -o mods-raw.md
```
Falls vorhanden: ✅ Schatzkarte. Falls nicht: User nach Liste fragen oder manuell von Nexus scrapen (langsam).

### Schritt 2: Mod-Liste parsen (Markdown → JSON).

Pattern in `Mod-List.md` (Nexus-Export):
```python
import re, json
pattern = re.compile(
    r'###\s+(.+?)\s*\n\s*\n'
    r'Installed\s+([\d/]+)\s+from\s+\[Nexus Mods\]\(https://www\.nexusmods\.com/cyberpunk2077/mods/(\d+)/?\)\s*\(([^)]+)\)',
    re.MULTILINE
)
# liefert: [{name, id, category, url}, ...]
```
Speichern als `mods-parsed.json` für nachfolgende Worker-Batches.

### Schritt 3: Lite-Variante ableiten (falls User Body/NSFW/Photo-Mods überspringen will).
```python
EXCLUDE_CAT = {"Armour and Clothing"}  # ggf. erweitern
BODY_KW = ["hyst", "booba", "thong", "bikini", "nude", "butt", "breast", ...]
# Ergebnis: ~40-50% weniger Mods
```

### Schritt 4: Batches für parallele Subagenten bilden.

Bei 5 verfügbaren Subagenten: 5 Batches × ~89 Mods = 444 Mods.
```python
batch_size = (len(mods) + 4) // 5
for i in range(5):
    batch = mods[i*batch_size:(i+1)*batch_size]
    save_to(f"batch-{i+1}.json")
```

### Schritt 5: Downloads orchestrieren — Login via CDP-Bridge (einmalig).

Nexus-Mod-Download geht nur mit User-Cookie und **funktioniert nicht via curl** (Cloudflare blockt TLS-Fingerprints, siehe Pitfall #20). Stattdessen:

1. **Separate Brave-Instanz mit `--remote-debugging-port=9333` öffnen** (siehe `references/nexus-cdp-cookie-bridge.md`)
2. **User loggt sich einmal auf nexusmods.com ein** — das reicht für die ganze Session
3. **Cookies via CDP extrahieren (einmalig)** — dienen NUR als Auth-Nachweis für das HTML-Download-Helper-Fenster

**WICHTIG: CDP Page-Navigation ist zu langsam für Bulk-Downloads** (Pitfall #21). `Page.navigate` + auf Cloudflare-Challenge warten braucht 3-5 sec/Mod → für 100+ Mods nicht praktikabel.

**Stattdessen: HTML-Download-Helper generieren mit allen Mod-Links (siehe `templates/generate-download-helper.py`).** User öffnet die Helper-HTML im normalen Brave, klickt Mods → Nexus-Tab → "Manual Download". Status wird im localStorage gespeichert.

### Schritt 6: ZIPs bereitstellen — User verschiebt Downloads.

Die ZIPs landen im normalen `~/Downloads/` (Brave-Downloads). User verschiebt sie (oder ich helfe):

```bash
mv ~/Downloads/*.zip ~/cp77-modding/downloads/ 2>/dev/null
```

**Alternative:** Wenn der Download-Ordner bekannt ist, kann ich automatisch sortieren ohne manuelle Verschiebung:
```bash
# Batch-Verschiebung aller ZIPs die zur Collection gehören
for f in ~/Downloads/*.zip; do
    mod_id=$(basename "$f" | grep -oP '^\d+')
    if grep -q "$mod_id" ~/cp77-modding/downloads/.mods-parsed.json 2>/dev/null; then
        mv "$f" ~/cp77-modding/downloads/
    fi
done
```

### Schritt 7: Pro Batch — Entpacken → Sortieren → Smoke-Check (Subagenten).

| Dateityp | Zielort |
|---|---|
| `.archive` | `archive/pc/mod/` oder `archive/pc/ep1/mod/` |
| `.dll` | `red4ext/plugins/<ModName>/` (eigener Ordner!) |
| `.reds` | `red4ext/plugins/<ModName>/` |
| `.yaml/.tweak` | `red4ext/plugins/<ModName>/` |
| `bin/x64/cyber_engine_tweaks/scripts/<file>.lua` | direkt in `bin/x64/cyber_engine_tweaks/scripts/` |
| `.ent` (entity) | `archive/pc/mod/` |

### Schritt 8: Vortex-only-Custom-Mods erkennen und Workaround.

Manche Collections haben Custom-Mods vom Curator (z.B. `v2_All_in_one_Vortex_Installer`). Diese sind oft `.exe` oder in einem Vortex-Pack-Format ohne klare ZIP-Struktur.
**Workaround:** ZIP trotzdem herunterladen + mit `unzip -l` inspizieren — meist sind `.archive` + `.dll` Files drin versteckt. Manuell rauskopieren statt via Vortex zu installieren.

## vapor — Linux-native CLI Mod-Manager (Experimental)

`Elsie19/vapor` (12 Stars, Rust, GPLv3) ist der vielversprechendste Linux-native Mod-Manager für CP77. Stand Juli 2026: **nur Source verfügbar**, kein Binary.

**Bauen aus Source:**
```bash
# Rust installieren (falls nicht vorhanden)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# vapor klonen + bauen
git clone https://github.com/Elsie19/vapor ~/cp77-modding/tools/vapor
cd ~/cp77-modding/tools/vapor
cargo build --release
# Binary: ~/cp77-modding/tools/vapor/target/release/vapor
```

**Verwendung:**
```bash
vapor init                                 # Einmalig: Game-Root angeben
vapor add "path/to/mod.zip" --name "Name"  # Mod installieren
vapor status                               # Status anzeigen
vapor disable "Name"                       # Mod deaktivieren
vapor graph                                # Dependency-Tree
```

**Limitation:** vapor ist low-level — keine automatische Dependency-Auflösung, kein Version-Break-Check. Gut für 10-30 Mods, für 100+ zu manuell.

**Kompatible Tools (Scraping):** `qcargile/CyberpunkModlistSetup` (0 Stars, Preinstallation Setup für Mod-Listen) — nur relevant wenn du Mod-Listen-Exporte von Vortex hast.

## City-of-Dreams-Case-Study

- **Heavy**: 1010 einzigartige Mods (29 GB Download)
- **Lite**: 444 Mods (Heavy minus Body/Clothing/Photo-Mods)
- **GitHub-Repo**: `v2sCollections/City-of-Dreams` mit `Mod List.md` (17.999 Zeilen)
- **Patch 2.21** kompatibel (CP77-Version prüfen!)
- **P0-Setup vor Installation:**
  - Saves-Backup aus Wine-Prefix (`drive_c/users/steamuser/Saved Games/CD Projekt Red/Cyberpunk 2077`)
  - Framework komplett: RED4ext + CET + ArchiveXL + TweakXL + Codeware
  - `launcher.ini`: `UserGameModsEnabled=true`
  - REDlauncher.exe dummy-verschoben ODER `--launcher-skip` aktiv
- **Load-Order-Risiko bei 444 Mods:** Hoch — Tweaks überschreiben sich gegenseitig. Erst in Etappen testen (50 → 100 → 200 → alle).

## Pitfalls bei großen Collections

- **Vortex-Pack nicht automatisch installierbar** — Custom-Mods erfordern manuelles Entpacken der ZIP-Inhalte
- **Load-Order manuell setzen** — kein Vortex = keine automatische Sortierung. Reihenfolge: Framework → Tweaks → Content (Vehicles, Weapons, Clothing) → Overrides
- **Patch-Mismatch** — Mods sind oft gegen bestimmten Game-Patch. README prüfen (z.B. "Compatible with Patch 2.21") und eigene Game-Version checken
- **Diskspace** — 29 GB Download + entpackt ~50-70 GB. Vorher `df -h` checken
- **CET + GE-Proton10-34** = bekannte Inkompatibilität. Falls CET-Konsole (`~`) nicht aufgeht: GE-Proton9-7 oder 8-31 downgraden
- **Phantom Liberty DLC** — EP1-Mods müssen nach `archive/pc/ep1/mod/`, nicht `archive/pc/mod/`