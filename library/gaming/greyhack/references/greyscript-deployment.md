# greybel-js Build Pipeline — GreyHack Tools

> **Created:** 2026-06-17
> **Context:** greybel-js installiert auf Linux-Host, baut .src Dateien für GreyHack

## Installation

```bash
npm install -g greybel-js
```

## Build-Kommando

```bash
greybel build <input.src> <output_dir> -u -dbf -si
```

| Flag | Bedeutung |
|------|-----------|
| `-u` | Uglify (minify Code) |
| `-dbf` | Disable Build Folder (Output direkt, nicht in `/build` Unterordner) |
| `-si` | Silent (unterdrückt unnötige Ausgaben) |
| `-of <name>` | Output Filename angeben |

## Import-Pfad-Resolution

`greybel-js` löst `import_code` Pfade **relativ zur Quelldatei** auf, NICHT relativ zum Arbeitsverzeichnis.

**FALSCH (absolute Pfade):**
```greyscript
import_code("/home/Bratan/bin/lib_core")
```

**RICHTIG (relativ zur .src Datei):**
```greyscript
import_code("../lib_core/lib_core.src")
# Von portscan/portscan.src → greyhack-tools/lib_core/lib_core.src
```

## Bekannte Inkompatibilitäten

| Problem | Beispiel | Lösung |
|---------|----------|--------|
| Backslash-Escaped Quotes | `\"text\"` in Strings | Einfache Quotes `'text'` verwenden |
| In-Game-Only APIs | `shell.start_terminal` | Auskommentieren |
| Fehlende `end function` | xmem.src (44 functions, 22 closes) | Manuell fixen |
| Doppelte schließende Klammer | `import_code("lib_core"))` | Extra `)` entfernen |
| Backslash in Strings | `split("\\n")` | `char(10)` verwenden |

## Build-Skript

`/home/bratan/bin/greyhack-build` — baut alle Tools mit einem Befehl:

```bash
greyhack-build all    # Alle Tools bauen
greyhack-build <name> # Einzelnes Tool bauen
```

Output: `~/greyhack-tools/bin/<tool>.src` (uglified, bereit für In-Game-Nutzung)

## Fileserver

```bash
# Starten (Hintergrund):
cd ~/greyhack-tools && python3 ~/bin/temp_fileserver.py &

# Testen:
curl http://localhost:8765/
```

Serviert `~/greyhack-tools/` für In-Game `pc.wget()` Downloads auf Port 8765.

## Build-Ergebnis (2026-06-17)

11 von 12 Kern-Tools erfolgreich gebaut:

| Tool | Status | Zeilen (uglified) |
|------|--------|-------------------|
| lib_core | OK | 158 |
| portscan | OK | 80 |
| metaxploit | OK | 154 |
| decypher | OK | 84 |
| routerinfo | OK | 75 |
| wifi_crack | OK | 74 |
| forcer | OK | 36 |
| scp_upload | OK | 68 |
| ps | OK | 61 |
| smtp_enum | OK | 104 |
| grsa | OK | 131 |
| xmem | FAIL | Strukturell kaputt |

## Code-Generator Dateien

Diese Dateien sind **Code-Generatoren** (bauen GreyScript-Strings zusammen) und per Design mit `\"` Escapes — greybel-js kann sie nicht bauen:

- `installer/installer.src`
- `launcher/launcher.src`

Sie funktionieren nur im Spiel via `shell.build()`.

## Tool: deploy_all.src

`~/greyhack-tools/deploy_all.src` — In-Game Deployer der vom Fileserver lädt und baut.

**Voraussetzung:** Fileserver laeuft auf Port 8765
**In-Game Nutzung:**
```
cd /bin
wget http://<HOST_IP>:8765/deploy_all.src
build deploy_all.src /bin/deploy_all
deploy_all
```

## GitHub Repo

https://github.com/Toqsick/greyscripts — Hauptrepo mit allen Fixes und Referenzen
- PR #18: Bug-Pattern-Fixes + GREYSCRIPT-REFERENCE.md
