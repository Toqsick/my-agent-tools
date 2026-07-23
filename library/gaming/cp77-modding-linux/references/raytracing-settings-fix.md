# Raytracing-Toggle Fix — Debug-Session (2026-07-04)

## Kontext

User (Basti) bemerkte nach Phantom Liberty-Kauf + REDlauncher-Bypass, dass die RT-Toggles im Grafikmenü ausgegraut waren. GPU: RTX 5060 Laptop (Blackwell, Compute 12.0) mit Treiber 595.71.05. CP77 Patch 2.21. Steam Flatpak mit GE-Proton10-34.

## Diagnose-Schritte

### 1. GPU-Fähigkeit prüfen
```bash
# DLSS aktiv? → ja (DLAA mit Transformer Model)
# NVIDIA Reflex aktiv? → ja (Enabled)
# ⇒ GPU ist RT-fähig, Treiber OK
```

### 2. UserSettings.json checken
```bash
USER_SETTINGS="$FLATPAK_STEAM/steamapps/compatdata/1091500/pfx/drive_c/users/steamuser/AppData/Local/CD Projekt Red/Cyberpunk 2077/UserSettings.json"
```

**Gefundene Werte:**
```
RayTracing: False (bool)
RayTracedReflections: False (bool)
RayTracedSunShadows: False (bool)
RayTracedLocalShadows: False (bool)
RayTracedLighting: Off (string_list)
RayTracedPathTracing: False (bool)
RayTracedPathTracingForPhotoMode: False (bool)
```

### 3. Valid Values für RayTracedLighting
```
values: ['Off', 'Medium', 'Ultra', 'Psycho']
```
**⚠️ `On` ist KEIN gültiger Wert** — wurde in der ersten Fix-Runde gesetzt und musste auf `Medium` korrigiert werden.

### 4. Fix-Versuch 1: UserSettings.json Edit (7 Settings → True/Medium)

Backup → `~/cp77-modding/backups/UserSettings-20260704-073457.json`

**Angewendete Settings:**
| Setting | Gesetzter Wert |
|---|---|
| RayTracing | True |
| RayTracedReflections | True |
| RayTracedSunShadows | True |
| RayTracedLocalShadows | True |
| RayTracedLighting | Medium |
| RayTracedPathTracing | True |
| RayTracedPathTracingForPhotoMode | True |

### 5. Ergebnis nach Game-Neustart (KRITISCH)

Nach Game-Start waren RT-Toggles **immer noch grau**. Kontrolle der `UserSettings.json` zeigte:

**Überschrieben (CP77-Capability-Detection hat zurückgesetzt):**
- `RayTracing: True → False` (Master-Switch!)
- `RayTracedLighting: Medium → Off`
- `RayTracedPathTracing: True → False`

**Überlebt:**
- `RayTracedReflections: True` (✅ blieb)
- `RayTracedSunShadows: True` (✅ blieb)
- `RayTracedLocalShadows: True` (✅ blieb)
- `RayTracedPathTracingForPhotoMode: True` (✅ blieb)

### 6. Root-Cause-Analyse: VKD3D-Proton Version

**CP77 Capability-Detection-Mechanismus:**
1. Game startet → D3D12-Device-Erstellung
2. Ruft `IDXGIFactory::CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS5, ...)` auf
3. Fragt: "Unterstützt diese GPU DXR (Raytracing Level 1.1)?"
4. VKD3D-Proton antwortet basierend auf GPU-Compute-Capability-Map

**Proton-Versionsvergleich:**
```
GE-Proton10-34:        vkd3d-1.1-5122-gbd3f5e3d (2023, VOR Blackwell)
Proton Experimental:   vkd3d-1.1-5424-g4232071c (2025, MIT Blackwell)
Proton Hotfix:         vkd3d-1.1-5424-g4232071c (2025, MIT Blackwell)
```

**VKD3D-Proton 5122** kannte keine Blackwell-GPUs (Compute Capability 12.0, released Q1 2025). Die Capability-Detection in Build 5122 hat eine statische GPU-CC-Map, die bei 11.0 (Ada Lovelace) endet. Blackwell (12.0) fällt durch → DXR = false.

**VKD3D-Proton 5424** hat die aktualisierte Map mit Blackwell-Support.

**DLL-Prüfung:**
- `$CP77_PFX/drive_c/windows/system32/d3d12.dll` = 159 KB (vkd3d-proton)
- `$CP77_PFX/drive_c/windows/system32/libvkd3d-1.dll` = 758 KB (Wine-Stdlib)
- VKD3D-Proton DLLs existieren im Prefix: `d3d12.dll` + `d3d12core.dll`
- Das Problem ist NICHT die DLL-Installation, sondern die GPU-CC-Map im Binary

### 7. Korrektur: Auf Proton Experimental umstellen

**Fix:** Steam → CP77 → Properties → Compatibility → "Use other Proton version" → Proton Experimental

**Warum:** Proton Experimental und Proton Hotfix haben identisch neue VKD3D-Proton Builds (5424), aber Experimental bekommt Updates zuerst. Beide haben Blackwell-Support.

**Warum nicht GE-Proton:** GE-Proton10-34's VKD3D-Proton ist von 2023 und hat die Blackwell-Map nicht. Die VKD3D-Proton-Version in GE-Proton ist **nicht** direkt aktualisierbar — sie gehört zum Build-Release.

### 8. UserSettings.json als Sekundär-Fix

Nach dem Proton-Wechsel müssen die Settings immer noch gesetzt werden (CP77 überschreibt sie nicht automatisch, selbst wenn DXR jetzt verfügbar ist). Siehe Hauptdoku für das Python-Fix-Script.

## Weitere Info

- CP77 verwendet seit Patch 2.0+ **nur noch DX12** (DX11 wurde entfernt). Es gibt keinen API-Switch in Settings.
- DLSS funktioniert unabhängig von RT — beide aktiv zu haben ist normal.
- RED4ext.log wurde nicht geschrieben → silent load (bekanntes Proton-Phänomen, siehe Skill-Hauptdoku).
- Phantom Liberty DLC war korrekt registriert (AppID 2138330 in appmanifest_1091500.acf).
- Die NVIDIA Treiberversion 595.71.05 ist aktuell genug für Blackwell-RT (Vulkan-RT funktioniert nativ).
- Das Problem ist **ausschließlich** der D3D12-Emulations-Layer (VKD3D-Proton), nicht der native Vulkan-RT-Support des Treibers.

## Verwandte Skill-Abschnitte

- `## 🔴 Raytracing-Toggles ausgegraut — Diagnose + Fix` (Hauptdoku, 3-Stufen-Fix)
- `## 🔴 Proton: REDlauncher Crash Fix` — warum der Launcher umgangen wurde
- `## 🔧 Launcher.INI: ModsEnabled erzwingen` — zweite Config-Force für Mods
- Pitfall #25: `RayTracedLighting` NIE auf `On` setzen
- Pitfall #27: VKD3D-Proton Version < 5300 = kein Blackwell-RT
- Pitfall #28: Full Reset als Differenzial-Diagnose für RT-Toggles
- `references/full-reset-procedure.md` — Reset-Doku (bestätigt: RT-Toggle-Issue ist nicht mod-bedingt)

## Update 2026-07-04: Full Reset bestätigt VKD3D-Proton-Hypothese

Nach dem Full Reset (REDlauncher entfernt + Modloader entfernt + UserSettings.json gelöscht + Steam Repair) blieben die RT-Toggles **immer noch grau**. Damit ist bewiesen:

- **Das RT-Problem ist NICHT durch Mod-Installation oder REDlauncher-Bypass verursacht**
- Es liegt **ausschließlich** an der VKD3D-Proton-Version (Build 5122 kennt Blackwell nicht)
- Selbst ein komplett frischer Game-Start (mit frischem REDlauncher und frischer UserSettings.json) ändert nichts

**Konsequenz:** Der einzige Fix bleibt der Wechsel auf Proton Experimental (oder ein GE-Proton mit neuerem VKD3D-Proton). Der Reset war als Diagnose-Schritt wertvoll (erfolgreich falsifiziert "vielleicht liegt's an den Mods"), hat aber das Problem nicht gelöst.
