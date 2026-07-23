---
name: cp77-modding-linux
description: "Use when user asks for Cyberpunk 2077 modding on Linux, CP77 mods via Steam/Proton, Flatpak Steam modding, REDmod setup. NOT for Windows-only modding, Cyberpunk: Edgerunners, or other CDPR games. Cyberpunk 2077 modding on Linux via Steam/Proton (Flatpak)."
version: 1.4.0
author: yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - cyberpunk-2077
    - modding
    - linux-gaming
    - steam
    - proton
    - flatpak
    - red4ext
    - cyber-engine-tweaks
    - mod-collection
    - vortex-alternative
    - nexus-mods
    - cdp-cookie-bridge
    lane: worker-flash
    reasoning_effort: high
trigger_keywords: ['modding', 'cyberpunk', 'steam', 'linux', 'proton']
keywords: ['modding', 'cyberpunk', 'steam', 'linux', 'proton']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Cyberpunk 2077 Modding on Linux (Steam/Proton/Flatpak)

Trigger: User fragt nach CP77 Modding, RED4ext, CET, NG+ Mods, oder will das Game modding-ready machen unter Linux (Proton/Flatpak).

## Quick Start

- [Path Structure](references/path-structure.md) — Flatpak Steam paths, Wine-Prefix, Saves location
- [Framework Dependency Order](references/framework-dependency-order.md) — RED4ext → CET → ArchiveXL → TweakXL → Codeware
- [Installation Directories](references/installation-directories.md) — Where to extract each component
- [Pre-Launch Check](references/pre-launch-check.md) — 12-point smoke test before first game start

## Critical Issues

| Issue | Fix |
|---|---|
| REDlauncher crashes under Proton | [--launcher-skip flag](references/redlauncher-crash-fix.md) |
| RT-Toggles greyed out | [Proton switch + UserSettings.json](references/raytracing-toggles-fix.md) |
| CET console won't open | [GE-Proton downgrade](references/ge-proton-compatibility.md) |
| RED4ext.log missing | [Check via CET console](references/red4ext-log-issues.md) |

## Downloads

| Component | Source | Notes |
|---|---|---|
| RED4ext | GitHub `maximegmd/RED4ext` | Use exact release tag URL |
| CET | GitHub `maximegmd/CyberEngineTweaks` | **NOT** WolvenKit (archived) |
| ArchiveXL | GitHub `psiberx/cp2077-ArchiveXL` |  |
| TweakXL | GitHub `psiberx/cp2077-TweakXL` |  |
| Codeware | GitHub `psiberx/cp2077-codeware` |  |
| redscript runtime | Nexus Mods #1511 | **NOT** on GitHub |

See [GitHub Asset URL Pitfalls](references/asset-url-pitfalls.md) for download workflow.

## Saves & Backups

- [Saves Backup](references/saves-backup.md) — tar from Wine-Prefix, keep last 3 backups
- [Full Reset Procedure](references/full-reset-procedure.md) — Vanilla restore, 6 phases

## Logs & Debugging

- [Live Log Reading](references/live-log-reading.md) — `tail -f` on RED4ext logs
- [RED4ext.log Issues](references/red4ext-log-issues.md) — Can be silent under Proton
- [REDlauncher Diagnostics](references/redlauncher-crash-fix.md) — Log paths, error codes

## Mod Collections (100+ Mods)

- [Mod Collections Workflow](references/mod-collections-workflow.md) — GitHub repo parsing, batches, HTML helper, Vortex via Bottles
- [Nexus Manual Downloads](references/nexus-manual-downloads.md) — Cloudflare blocks curl, use browser
- [Vapor CLI](references/vapor-linux-mod-manager.md) — Linux-native mod manager (experimental)

## Advanced

- [REDscript Runtime vs Compiler](references/redscript-runtime-vs-compiler.md) — Compiler ≠ Runtime plugin
- [REDlauncher Crash Fix](references/redlauncher-crash-fix.md) — Complete fix with launch options
- [Launcher.INI Fix](references/launcher-ini-fix.md) — Force UserGameModsEnabled=true
- [Raytracing Toggles Fix](references/raytracing-toggles-fix.md) — VKD3D-Proton, UserSettings.json edit

## Pitfalls

See [Complete Pitfalls List](references/pitfalls.md) — 27 critical gotchas including:
- Cloudflare TLS fingerprint blocking
- CDP navigation too slow for bulk downloads
- Brave Cookies DB encryption
- VKD3D-Proton version requirements for RTX 5060+
- Full reset as differential diagnosis

## Support Files

- `references/asset-urls.md` — Exact download URLs for all frameworks
- `references/nexus-cdp-cookie-bridge.md` — CDP recipe for cookie extraction
- `references/vapor-linux-mod-manager.md` — vapor build & usage
- `templates/generate-download-helper.py` — HTML helper for large collections
- `scripts/pre-launch-check.sh` — Automated 12-point smoke test
- `scripts/sort-mod-zips.sh` — Auto-sort ZIPs into game root
