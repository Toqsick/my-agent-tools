# libxnvctrl0 Version Mismatch vs Driver — Discovery 2026-06-27

**Session:** RTX 5060, Driver 595.71.05, Zorin 18.1

## Symptom

- libxnvctrl0: `510.47.03-0ubuntu4.24.04.1` (zu alt!)
- Treiber/Utils: `595.71.05-0ubuntu0.24.04.1` (aktuell)
- nvidia-settings zeigt nur Basis-Info, keine OC-Controls
- GWE crasht mit "NV-CONTROL missing!"

## Root Cause

`libxnvctrl0` (NV-CONTROL X extension runtime) ist auf 510 gefroren, der Treiber
ist 595. Das Ubuntu Noble-Repo hat kein neueres libxnvctrl0. Das Paket wird für
Treiber >535 nie aktualisiert.

## Diagnose

```bash
apt-cache policy libxnvctrl0
apt-cache showpkg libxnvctrl0 | grep -A3 Versions
```

## Lösungen (inkaufen Aufsteigend)

```bash
# Option 1: Ausreichend für Wayland-Only (nvidia-smi reicht)
# Ignorieren — libxnvctrl0 wird nur für X11/nvidia-settings benötigt

# Option 2: Neueren Stand aus allem Treiber-Paket nutzen
# Der Treiber enthält libnvidia-cfg1-595, aber NICHT libxnvctrl0
# libxnvctrl0 ist ein eigenständiges Ubuntu-Paket ohne Update

# Option 3: numpy aus Treiber-Quelle extrahieren (advanced)
# cp libxnvctrl.so.510.x → libxnvctrl.so.595.x + symlink
# NICHT EMPFOHLEN: Broken bei jedem lib-Update

# Option 4: X11-Session für OC-Steuerung
# nvidia-smi -q -d PAGE_RETIRED_PAGES → Power check
# Kein OC über Wayland möglich!
```

## Botschaft für andere Sessions

**libxnvctrl0 ist ein eigenständiges Ubuntu-Paket, das nie aktualisiert wird
für Treiber >535.** Wenn der User "lib update" will — erklären, dass es nicht
geht und kein Risiko für den Betrieb darstellt solange nur Wayland. Falls der
User X11 für OC will: Das `xserver-xorg-video-nvidia-595` Paket hat keine
nvidia_drv.so → zuerst `sudo apt install --reinstall xserver-xorg-video-nvidia-595`.
