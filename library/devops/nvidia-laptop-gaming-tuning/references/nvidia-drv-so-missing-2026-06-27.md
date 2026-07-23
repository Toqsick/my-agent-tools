# nvidia_drv.so Fehlt Trotz Installiertem Treiber — Discovery 2026-06-27

**Session:** RTX 5060, Driver 595.71.05, Zorin 18.1, Kernel 6.17.0-35

## Symptom

- `dpkg -l xserver-xorg-video-nvidia-595` → installiert, OK
- Aber: `ls /usr/lib/xorg/modules/drivers/nvidia*` → NIKS
- Xorg meldet: `"Failed to load module nvidia (module does not exist, 0)"`
- nvidia-smi funktioniert dennoch (nutzt `/dev/nvidia0` kernel interface)

## Root Cause

Das Paket `xserver-xorg-video-nvidia-595` enthält die Datei `nvidia_drv.so` nicht
für den Kernel 6.17. Entweder:
1. Das Dateipaket wurde bei der Debian-Paketierung nicht mitgeliefert
2. Oder: Bei open↔proprietär-Wechseln wurde die Datei durch ein leeres Paket ersetzt
3. DKMS baut nur Kernel-Module (.ko), nicht die Xorg-.so-Datei

## Diagnose

```bash
# Ist das Paket wirklich installiert?
dpkg -L xserver-xorg-video-nvidia-595 | grep "\.so"
# Wenn leer → Paket enthält keine .so-Datei!

# Alternative: Ist nvidia-driver-595 (proprietär) installiert?
dpkg -l nvidia-driver-595 | grep "^ii"

# Xorg-Log checken
cat /var/log/Xorg.0.log | grep -E "EE.*nvidia|WW.*nvidia"
```

## Lösung

```bash
# Neuinstallation erzwingen
sudo apt install --reinstall xserver-xorg-video-nvidia-595
# Falls immer noch leer → open kernel wechseln oder proprietär probieren
sudo apt install --reinstall nvidia-driver-595 xserver-xorg-video-nvidia-595
```

**Wichtig:** Auf Wayland ist dieses Problem nicht sichtbar (Mutter nutzt
modesetting/EGL). Es wird erst relevant bei X11-Session-Switch oder wenn
`/etc/X11/xorg.conf` den nvidia-Driver hart fordert.

## Botschaft für andere Sessions

Manchmal hat `apt install` das Paket "markiert als installiert" aber die Binärdatei
wurde nie geschrieben (leeres Paket). Immer `dpkg -L <paket> | grep .so` checken,
nicht nur `dpkg -l | grep ii`.
