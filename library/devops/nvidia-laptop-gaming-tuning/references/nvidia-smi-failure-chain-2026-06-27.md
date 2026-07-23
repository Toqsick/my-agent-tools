# nvidia-smi Failure Chain — Layered Diagnosis (RTX 5060 Laptop, Wayland, Driver 595)

**Session:** 2026-06-27, Zorin OS 18.1, RTX 5060 Laptop, NVIDIA 595.71.05
**Symptom:** `nvidia-smi` → "No devices were found" despite driver loaded

## Die 6 Schichten des nvidia-smi Failures

### Schicht 0: 5-Sekunden-Scan (IMMER ZUERST)
```bash
nvidia-smi >/dev/null 2>&1 && echo "OK" || echo "FAIL"
ls /usr/lib/xorg/modules/drivers/nvidia* 2>/dev/null || echo "nvidia_drv.so MISSING"
ls /etc/X11/xorg.conf 2>/dev/null && echo "xorg.conf (riskant)" || echo "kein xorg.conf"
dpkg -l | grep nvidia | grep ^rc || echo "keine Zombies"
dkms status | grep nvidia
cat /sys/bus/pci/devices/*/power_state 2>/dev/null
```

### Schicht 1: GPU im D3cold (Deep Sleep) — HÄUFIGSTE URSAKE
- Runtime PM schaltet GPU ab wenn idle
- Control: `auto` → GPU on/off je nach Nutzung
- nvidia-smi kann D3cold-GPU nicht ansprechen
- Fix: `echo on | sudo tee /sys/bus/pci/devices/0000:01:00.0/power/control`
- Info: `nvidia-smi` ist NICHT "Fake" — es braucht aktiven Kernel-Request

### Schicht 2: nvidia_drv.so fehlt (NUR Xorg, NICHT nvidia-smi!)
`nvidia-smi` kommuniziert via `/dev/nvidia0` (kernel interface).
`nvidia_drv.so` ist der Xorg-Treiber. Wenn er fehlt:
- nvidia-smi funktioniert trotzdem ✓
- Xorg crasht bei `Driver "nvidia"` in xorg.conf ✗
- Fix: `sudo apt install xserver-xorg-video-nvidia-595`

### Schicht 3: Verstecktes /etc/X11/xorg.conf
- `nvidia-xconfig` generiert: `Driver "nvidia"` in Device Section
- Auf Wayland (Mutter) kein Problem (Muter nutzt modesetting/EGL)
- ABER: Wechsel zu X11-Session → Xorg liest xocrash → Crash!
- Fix: `sudo mv /etc/X11/xorg.conf /etc/X11/xorg.conf.disabled`
- Verwende: `/etc/X11/xorg.conf.d/` snippets statt xorg.conf

### Schicht 4: Zombie-Pakete
- `dpkg -l | grep nvidia | grep ^rc` zeigt Reste von alten Installationen
- Einziges rc-Paket kann DKMS blockieren
- Fix: `sudo dpkg --purge <package>` für jede rc-Zeile

### Schicht 5: DKMS-Build fehlt
- Kann auch ohne Kernel-Update passieren (nach modprobe-Fehlern)
- Oder: Paket-Konflikt, fehlende Kernel-Headers
- Fix: `sudo dkms install nvidia/595.71.05 -k $(uname -r)`

### Schicht 6: EC Power Capping
- Embedded Controller zwingt Power Cap
- nvidia-smi zeigt Cap, kann ihn nicht ändern
- Fix: Power-Profiles-Daemon → `performance`, X11 + Coolbits
- Siehe: `references/ec-power-capping-2026-06-18.md`

## Display-Output Optimierung (Optimus)

- Internes Display: `prime-select on-demand` + `__NV_PRIME_RENDER_OFFLOAD=1`
- Externes Display (DP-1): `prime-select nvidia` + Abmelden (nicht Reboot!)
- Anzeigeprobleme: `nvidia-smi -q -d POWER|PERFORMANCE`
- Freigabe: `sudo prime-select nvidia` + `sudo modprobe nvidia_modeset nvidia_drm`

## Wayland-spezifische Probleme
- NV-CONTROL X extension existiert nur in X11
- nvidia-settings/GWE crashen auf Wayland
- GPU Control nur über nvidia-smi möglich

## Zorin OS-spezifisch
- Zorin 18.1: Kernel 6.17, 595-Treiber unterstützt
- Alle Fixes sind user-space / config-only
- Kein Treiber-Update nötig — Treiber ist aktuell
