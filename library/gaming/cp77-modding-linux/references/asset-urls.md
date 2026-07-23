# CP77 Modding Asset URLs

> Stand: 2026-07-03, Game Patch Mai 2026, GE-Proton10-34

## Framework-Download-URLs (exakte Asset-URLs, kein /latest/)

[NICHT /releases/latest/download/ verwenden — GitHub liefert 404 zurück]

```yaml
# RED4ext
repo: WopsS/RED4ext
version: 1.30.0
asset: red4ext-1.30.0.zip
url: https://github.com/WopsS/RED4ext/releases/download/v1.30.0/red4ext-1.30.0.zip
size: 1.2 MB (entpackt)

# Cyber Engine Tweaks (CET)
repo: maximegmd/CyberEngineTweaks
version: 1.37.1
asset: cet_1.37.1.zip
url: https://github.com/maximegmd/CyberEngineTweeks/releases/download/v1.37.1/cet_1.37.1.zip
size: 7.1 MB (entpackt)
note: NICHT das alte WolvenKit-Repo verwenden (archiviert/aufgelöst)

# ArchiveXL
repo: psiberx/cp2077-archive-xl
version: 1.26.8
asset: ArchiveXL-1.26.8.zip
url: https://github.com/psiberx/cp2077-archive-xl/releases/download/v1.26.8/ArchiveXL-1.26.8.zip
size: 1.9 MB

# TweakXL
repo: psiberx/cp2077-tweak-xl
version: 1.11.3
asset: TweakXL-1.11.3.zip
url: https://github.com/psiberx/cp2077-tweak-xl/releases/download/v1.11.3/TweakXL-1.11.3.zip
size: 1.4 MB

# Codeware
repo: psiberx/cp2077-codeware
version: 1.20.3
asset: Codeware-1.20.3.zip
url: https://github.com/psiberx/cp2077-codeware/releases/download/v1.20.3/Codeware-1.20.3.zip
size: 1.9 MB
```

## Nexus Mods (manuell, Login erforderlich)

```yaml
# New Game Plus - Native
nexus_id: 15043
author: notalphanine
url: https://www.nexusmods.com/cyberpunk2077/mods/15043
install_target: red4ext/plugins/New Game Plus/
created_at: 2026-07-03

# Mod Settings
nexus_id: 4885
author: jackhumbert
url: https://www.nexusmods.com/cyberpunk2077/mods/4885
install_target: red4ext/plugins/ModSettings/
created_at: 2026-07-03

# redscript (RED4ext Lua-Plugin)
nexus_id: 1511
url: https://www.nexusmods.com/cyberpunk2077/mods/1511
install_target: red4ext/plugins/redscript/
note: |
  GitHub jac3km4/redscript hat NUR den Compiler (scc.exe)!
  Das Runtime-Plugin (redscript.dll) gibt es AUSSCHLIESSLICH auf Nexus.
  Nicht verwechseln!
created_at: 2026-07-03
```

## API-Abfrage (für zukünftige Automatisierung)

```bash
# RICHTIG: tag_name + browser_download_url aus API lesen
curl -fsSL "https://api.github.com/repos/WopsS/RED4ext/releases/latest" | \
    jq -r '"\(.tag_name)\n\(.assets[].browser_download_url)"'

# FALSCH: /releases/latest/download/ — GitHub redirects auf 404
```
## Repo-Recherche-Hilfe

GitHub-Suche nach CP77-Repos (für Unbekannte):

```bash
# Repo finden
curl -fsSL "https://api.github.com/search/repositories?q=codeware+cyberpunk+2077" | \
    jq -r '.items[] | "\(.full_name) (\(.stargazers_count)★) - \(.description)"'

# Repo-Releases finden
curl -fsSL "https://api.github.com/repos/psiberx/cp2077-codeware/releases/latest" | \
    jq -r '[.tag_name, (.assets[].name | tostring)] | join("\n")'
```

## Versions-Historie

| Komponente | Letzte bekannte Version (2026-07-03) | Game-Kompatibilität |
|---|---|---|
| RED4ext | 1.30.0 | ✅ CP77 2.x (alle Patches) |
| CET | 1.37.1 | ✅ CP77 2.x + Phantom Liberty |
| ArchiveXL | 1.26.8 | ✅ CP77 2.x |
| TweakXL | 1.11.3 | ✅ CP77 2.x |
| Codeware | 1.20.3 | ✅ CP77 2.x |
| GE-Proton | 10-34 | ⚠️ REDlauncher-Crash (Exit 0xC0000005) unter Proton. Fix: `--launcher-skip` in Launch-Options. Falls CET-Konsole tot auf 9-7 fallen. |
