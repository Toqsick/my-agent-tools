# Raytracing-Toggles Fix

## Symptom: RT-Toggles ausgegraut

RT-Toggles im Grafik-Menü sind ausgegraut/deaktiviert, obwohl die GPU RT-fähig ist (RTX 3060+).

### Ursache: VKD3D-Proton zu alt für Blackwell/Ada-GPUs

CP77 führt beim Start eine **Capability-Detection** durch: es fragt `D3D12_FEATURE_D3D12_OPTIONS5` bei VKD3D-Proton an. Wenn VKD3D-Proton die GPU nicht kennt (ältere Version vor der Blackwell-Unterstützung), antwortet es "DXR nicht verfügbar" → CP77 **überschreibt die RT-Settings** auf False.

**Das bedeutet: Ein UserSettings.json-Edit alleine reicht NICHT.** CP77 setzt 4 von 7 RT-Settings beim nächsten Start wieder zurück:
- ❌ Überschrieben: `RayTracing: True→False`, `RayTracedLighting: Medium→Off`, `RayTracedPathTracing: True→False`
- ✅ Überlebt: `RayTracedReflections`, `RayTracedSunShadows`, `RayTracedLocalShadows`, `RayTracedPathTracingForPhotoMode`

## Stufe 1: Proton-Version prüfen und ggf. aktualisieren (PRIMÄRER FIX)

Prüfe zuerst, ob VKD3D-Proton deine GPU kennt. **Das ist der häufigste Fix für RTX 4000+ und RTX 5000-Serien.**

```bash
# 1. Aktuelle VKD3D-Proton Version von GE-Proton checken
cat "$FLATPAK_STEAM/compatibilitytools.d/GE-Proton10-34/files/lib/wine/vkd3d-proton/version"
# Beispiel-Ausgabe: bd3f5e3d vkd3d-proton (vkd3d-1.1-5122-gbd3f5e3d)
#               ^^^ Build 5122 ≈ 2023

# 2. Proton Experimental VKD3D-Proton Version checken
find "$FLATPAK_STEAM/steamapps/common/Proton - Experimental" \
  -path "*vkd3d-proton*" -name "version" -exec cat {} \;
# Beispiel-Ausgabe: 4232071c vkd3d-proton (vkd3d-1.1-5424-g4232071c)
#               ^^^ Build 5424 ≈ 2025

# 3. Heuristik: Bauzahl vergleichen
#    GE-Proton Bauzahlen: 5122 (vkd3d-1.1) = VOR Blackwell (2023)
#    Prog Exp Bauzahlen:  5424 (vkd3d-1.1) = MIT Blackwell (2025)
#    Faustregel: < 5300 = zu alt für Blackwell-RT
```

**GPUs ab Compute Capability 12.0 (Blackwell, RTX 5060+)** brauchen mindestens **VKD3D-Proton Build 5300+**. GE-Proton10-34 (Build 5122) ist zu alt.

**Empfohlener Fix: Im Steam auf Proton Experimental umschalten**
- Steam → Cyberpunk 2077 → Rechtsklick → Properties → Compatibility
- **"Use other Proton version" anhaken**
- **Dropdown: "Proton Experimental"** wählen
- OK → Game starten

| Proton-Version | VKD3D-Proton Build | Blackwell-RT-Support |
|---|---|---|
| GE-Proton10-34 | vkd3d-1.1-5122 (2023) | ❌ Nein |
| Proton Hotfix | vkd3d-1.1-5424 (2025) | ✅ Ja |
| **Proton Experimental** | **vkd3d-1.1-5424 (2025)** | **✅ Ja (empfohlen)** |

**Warum Proton Experimental und nicht Hotfix:** Hotfix ist nur für Game-Crash-Patches, während Experimental den aktuellsten VKD3D-Proton-Stack hat. Beide haben Build 5424, aber Experimental bekommt Updates zuerst.

**Risiko:** Sehr gering. Du kannst jederzeit zurück auf GE-Proton wechseln. Andere Games sind nicht betroffen (die Einstellung gilt nur für CP77).

## Stufe 2: UserSettings.json editieren (SEKUNDÄRER FIX — NUR nach Proton-Wechsel)

Nachdem die Capability-Detection grünes Licht gibt (Stufe 1 abgeschlossen), müssen die RT-Settings in der Config aktualisiert werden. CP77 überschreibt sie sonst nicht automatisch.

```bash
USER_SETTINGS="$CP77_PFX/drive_c/users/steamuser/AppData/Local/CD Projekt Red/Cyberpunk 2077/UserSettings.json"

# IMMER Backup!
cp "$USER_SETTINGS" "$BACKUP_DIR/UserSettings-$(date +%Y%m%d-%H%M%S).json"
```

**Settings unter `/graphics/raytracing`:**

| Setting | Typ | Gültige Werte | Effekt |
|---|---|---|---|
| `RayTracing` | bool | `true`/`false` | Master-Switch für alles RT |
| `RayTracedReflections` | bool | `true`/`false` | Spiegelnde Oberflächen |
| `RayTracedSunShadows` | bool | `true`/`false` | Sonnenschatten |
| `RayTracedLocalShadows` | bool | `true`/`false` | Lokale Schatten (Lampen etc.) |
| `RayTracedLighting` | string_list | `Off`, `Medium`, `Ultra`, `Psycho` | Globale Beleuchtung |
| `RayTracedPathTracing` | bool | `true`/`false` | Full Path Tracing (Overdrive) |
| `RayTracedPathTracingForPhotoMode` | bool | `true`/`false` | Path Tracing im Photo Mode |

**⚠️ Wichtig:** `RayTracedLighting` akzeptiert NUR `Off`, `Medium`, `Ultra`, `Psycho` — NICHT `On`, `Low`, `High`. Falscher String → UI-Fehler/Read-Failures.

**Python-Fix (sicher):**
```python
import json
with open(USER_SETTINGS) as f:
    d = json.load(f)
for entry in d.get('data', []):
    if isinstance(entry, dict) and entry.get('group_name') == '/graphics/raytracing':
        for opt in entry.get('options', []):
            name = opt['name']
            if name in ['RayTracing','RayTracedReflections','RayTracedSunShadows',
                        'RayTracedLocalShadows','RayTracedPathTracing',
                        'RayTracedPathTracingForPhotoMode']:
                opt['value'] = True
            elif name == 'RayTracedLighting':
                opt['value'] = 'Medium'
with open(USER_SETTINGS, 'w') as f:
    json.dump(d, f, indent=2)
```

**Nach dem Edit:** CP77 starten → RT-Toggles sollten aktiv sein. Falls Toggles immer noch ausgegraut: Prüfe ob Stufe 1 wirklich gegriffen hat (VKD3D-Proton Version-Konflikt).

## Stufe 3: Wenn immer noch ausgegraut — VKD3D-Config erzwingen

In seltenen Fällen erkennt VKD3D-Proton DXR trotz neuer Version nicht korrekt. Dann als LaunchOptions in Steam setzen:

```
VKD3D_CONFIG=force_bindless_texel_buffer %command%
```

`force_bindless_texel_buffer` wird explizit im GE-Proton-Script genannt (siehe `check_environment("vkd3dbindlesstb")`) und ist der einzige dokumentierte VKD3D-Toggle für Kompatibilitätsprobleme. **NICHT** `nodxr` oder `dxr` verwenden — die existieren nicht in VKD3D-Proton.

## Performance auf RTX 5060 Laptop (erwartet)

| RT-Stufe | FPS (1080p) |
|---|---|
| Medium (Lumen-Effekte) | ~50-60 |
| Ultra | ~30-40 |
| Psycho (PathTracing) | ~20-25 |