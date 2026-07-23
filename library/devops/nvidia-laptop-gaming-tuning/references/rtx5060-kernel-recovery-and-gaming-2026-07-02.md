# RTX 5060 Kernel Recovery & Gaming Test (2026-07-02)

## Kontext

Nach mehrfachem Treiber-Churn (open↔proprietary, 595.71.05) auf Zorin OS / Ubuntu 24.04
mit NVIDIA GeForce RTX 5060 Laptop GPU + Intel iGPU (Optimus hybrid).

## Befund 1: Wrong Kernel After Reboot

**Symptom:** Komplexer NVIDIA Driver Fix angewandt → Reboot → `nvidia-smi` failt,
`lsmod | grep nvidia` leer, `dmesg` kein nvidia. `dpkg -l | grep nvidia` zeigt `rc`
(zombie). Nutzer denkt: "Treiber kaputt".

**Wahre Ursache:** Der Reboot landete auf einem anderen Kernel
(`6.8.0-134-lowlatency` statt `6.17.0-35-generic`). nvidia-dkms hatte nur für
`6.17.0-35-generic` gebaut → kein nvidia.ko für lowlatency.

**Recovery:**
```bash
# 1. Im GRUB: → Advanced options → generic kernel wählen
# 2. Verify:
uname -r        # muss 6.17.0-35-generic sein (der mit nvidia-dkms)
nvidia-smi      # muss wieder funktionieren
# 3. Persistent fix: alten lowlatency Kernel purge + default fixen
sudo apt purge linux-image-6.8.0-134-lowlatency linux-headers-6.8.0-134-lowlatency
sudo kernelstub -v  # prüfen welcher Kernel default ist
```

**Lektion:** `nvidia-smi` failt nach Reboot → IMMER zuerst `uname -r` checken,
bevor man an Treibern rummacht.

## Befund 2: EC Power Cap [N/A] — Hardware-Limit

Auf dem korrekten Kernel (`6.17.0-35-generic`) mit vollem Treiber (595.71.05)
und allen Fixes (ReBAR, Coolbits 28, governor, nvidia-persistenced) zeigt
`nvidia-smi --query-gpu=power.limit` weiterhin `[N/A]`.

**Das ist ein Hardware-EC-Limit.** nvidia-smi kann den Wert nicht lesen,
weil das Embedded Controller des Laptops das Power-Limit kontrolliert.
Ein `nvidia-smi -pl <value>` wird rejected.

- Kein workaround bekannt
- Gaming funktioniert trotzdem (GPU erreicht ~80W unter Last)
- Akzeptieren. Nicht weiter troubleshooten.

## Befund 3: Flatpak Steam + External Game Library

Steam läuft als Flatpak (`com.valvesoftware.Steam`). Cyberpunk 2077 ist auf
einem externen Mount installiert (`/mnt/DATA/Programme/Steam/steamapps/common/`),
nicht im Flatpak-Sandbox-Ordner.

**Wie Steam die Library findet:** Steam SteamLibraryFolders enthält mehrere Pfade:
- Flatpak intern: `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps`
- Extern: `/mnt/DATA/Programme/Steam/steamapps/`
- /media/bratan/DATA (USB)

Steam recognized the game via the external library folder. Launch works via
pressure-vessel sandbox → bwrap → Proton → Cyberpunk2077.exe.

**Diagnose:**
```bash
# Alle Steam Library Folders anzeigen
cat ~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf
# Game path prüfen
ls "/mnt/DATA/Programme/Steam/steamapps/common/Cyberpunk 2077"
```

**Gaming wird von Flatpak geprüft:** Der `prime-run` Befehl existiert auf dem Host
aber erreicht das Spiel im pressure-vessel Container nicht. Stattdessen Steam
Launch Options verwenden:
```
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia %command%
```

ABER: Auch Launch Options können vom pressure-vessel Entry-Point gefiltert werden
(bekanntes Problem mit Source-2 Engine / Native Linux Spielen).

## Befund 4: CS2 Native Linux + NVIDIA Routing Problem

Counter Strike 2 ist ein **Native Linux Spiel** (Source 2 Engine, Vulkan).
Es läuft als `cs2.sh -steam` via linuxsteamrt64, NICHT via Proton.

**Problem:** Weder `prime-run` noch `__NV_PRIME_RENDER_OFFLOAD=1` in Steam
Launch Options erreichen CS2. Grund: Der pressure-vessel/bwrap Entry-Point
stripst gezielt Umgebungsvariablen. Die NVIDIA Prime Env-Vars kommen nicht
beim Spiel an.

**Symptom:**
- `nvidia-smi` zeigt nur gnome-shell, Steam, linux-assistant → 0% NVIDIA
- CS2 läuft mit 20 FPS auf Intel iGPU
- Launch Options gesetzt → keine Wirkung
- CPU auf 25% (Game läuft, GPU nicht involviert)

**Workaround (nicht vollständig getestet):**
```bash
# 1. prime-select auf nvidia setzen (weg von on-demand)
sudo prime-select nvidia
# 2. Reboot
systemctl reboot
# 3. Oder: Steam Runtime Sniper on-demand mode (ohne pressure-vessel)
# Steam → CS2 Properties → Uncheck "Enable Steam Play for all other titles"
```
oder direkt in der Steam Launch-Option:
```
DXVK_FILTER_DEVICE_NAME="NVIDIA GeForce RTX 5060 Laptop GPU" %command%
```
(Diese Option gilt für DXVK/VKD3D, also nur Proton-Spiele. Für Native Vulkan
Spiele wie CS2 braucht es `VK_LAYER_NV_optimus=NVIDIA_only` oder `MESA_VK_DEVICE_SELECT`).

## Befund 5: nvidia-persistenced fehlt

`nvidia-persistenced` war nicht installiert. Dieses Tool verhindert dass der
GPU-State beim ersten Access nach Boot initialisiert werden muss → reduziert
Start-Latenz für Spiele.

**Fix:**
```bash
sudo apt install nvidia-persistenced
sudo systemctl enable --now nvidia-persistenced
nvidia-smi  # verify: nvidia-persistenced sollte als Prozess sichtbar sein
```

## Quick-Reference: Gaming Ready Triage

```bash
# 1. Kernel prüfen
uname -r                # muss der sein für den nvidia-dkms gebaut hat
# 2. Treiber
nvidia-smi              # GPU vorhanden?
nvidia-smi --query-gpu=name,driver_version,power.draw,power.limit,clocks.current.graphics,utilization.gpu --format=csv
# 3. Renderer
glxinfo | grep "OpenGL renderer"          # NVIDIA oder Intel?
# 4. Prime env
env | grep -E '^(__NV_PRIME|__GLX_VENDOR)'
prime-select query                        # on-demand vs nvidia
# 5. Power
powerprofilesctl get                      # performance setzen für Gaming
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# 6. VRAM
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
# 7. Flatpak Steam Libraries
cat ~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf
# 8. Proton GE Version
ls ~/.var/app/com.valvesoftware.Steam/.local/share/Steam/compatibilitytools.d/
```

## Ergebnis dieser Session

| Check | Status |
|-------|--------|
| Kernel | ✅ 6.17.0-35-generic |
| NVIDIA Treiber | ✅ 595.71.05, module loaded |
| OpenGL Renderer | ✅ NVIDIA GeForce RTX 5060 |
| prime-select | ✅ on-demand |
| ReBAR | ✅ enabled |
| Coolbits 28 | ✅ installiert |
| CPU Governor | Balance_Performance (powerprofilesctl performance gesetzt) |
| Power Limit | [N/A] — EC-cap hardware, akzeptiert |
| Cyberpunk 2077 | ✅ Startet via GE-Proton10-34 (Prozess läuft) |
| CS2 | ⚠️ Läuft auf Intel iGPU — Prime env wird von pressure-vessel gestripped |
