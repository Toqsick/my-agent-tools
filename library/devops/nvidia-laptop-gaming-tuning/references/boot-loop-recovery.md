# Boot-Loop Recovery — nvidia-smi fail nach GPU-Tweak-Versuch

## Symptom
- `nvidia-smi` meldet "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver"
- System bootet nicht mehr normal (Boot-Loop) oder landet in Grub Rescue
- Nachdem der User versucht hat, GPU-Einstellungen zu tweaken (z.B. Coolbits, Übertaktung, Treiberwechsel)

## PRINZIP: Erst gründlich Research, dann Fix (User-Präferenz)
**NIEMALS blind loslegen.** Immer zuerst:
1. **Read-only Diagnose** — Logs, Paket-Status, Kernel-Module checken OHNE Änderungen
2. **3-Expert Research** (multi-agent-research Pattern): Boot-Loop-Ursache, Treiber-State, Web-Recherche parallel
3. **Synthese + Safe-Fix-Plan** erstellen und dem User präsentieren
4. **Erst nach Freigabe fixen** — Timeshift-Backup muss vorher existieren!

## Ursachen (häufigste zuerst)
1. **Zombie-Pakete (rc-Status) von Treiberwechseln** — Mehrfaches De-/Reinstallieren zwischen Treiberversionen (z.B. 580↔595, open↔proprietär) hinterlässt rc-Pakete, die DKMS blockieren
2. **Kaputtes `/etc/X11/xorg.conf`** von `nvidia-xconfig` — erzwingt NVIDIA-Treiber, blockiert Boot wenn Modul fehlschlägt
3. **Fehlendes `xserver-xorg-video-nvidia-595`** — `nvidia_drv.so` fehlt → Xorg "no screens found"
4. **DKMS-Build fehlt** — nach Kernel-Update oder Treiberwechsel kein Kernel-Modul gebaut
5. **`nvidia-powerd.service` korrumpiert** — "Allocate Root client failed 0x26" durch fehlende GPU-Initialisierung
6. **Secure Boot** blockiert unsigned Module (besonders mit `OpenRmEnableUnsupportedGpus`)
7. **Kernel-Update** ohne Treiber-Rebuild (dkms)

## Diagnose-Workflow (Read-Only)

### Schritt 1: Ursachen-Ranking
| # | Ursache | Prüfbefehl |
|---|---------|-----------|
| 1 | Zombie-Pakete (rc) | `dpkg -l \| grep nvidia \| grep ^rc` |
| 2 | xorg.conf kaputt | `cat /etc/X11/xorg.conf \| grep Driver` |
| 3 | xserver-xorg-video fehlt | `dpkg -l \| grep xserver-xorg-video-nvidia` |
| 4 | DKMS-Build fehlt | `dkms status \| grep nvidia` |
| 5 | nvidia-powerd crash | `journalctl -u nvidia-powerd --since "1 hour ago" \| grep -i error` |
| 6 | Kernel-Module nicht geladen | `lsmod \| grep nvidia` |

### Schritt 2: Detail-Diagnose
```bash
# Xorg-Log (der wichtigste!)
cat /var/log/Xorg.0.log | grep -E "EE|WW|nvidia|dri"

# apt-History nach Treiberwechseln
grep -B2 "nvidia.*install\|nvidia.*purge\|nvidia.*remove" /var/log/apt/history.log

# Kernel-Modul-Pfad prüfen
ls -la /lib/modules/$(uname -r)/kernel/nvidia-595-open/ 2>/dev/null

# nvidia-powerd Debug
/usr/bin/nvidia-powerd --log-level=debug 2>&1 | head -20
```

## Recovery Workflow

### Schritt 0: Backup (IMMER zuerst)
```bash
# Configs sichern
sudo cp /etc/X11/xorg.conf /etc/X11/xorg.conf.bak.$(date +%Y%m%d) 2>/dev/null
sudo cp /etc/default/grub /etc/default/grub.bak.$(date +%Y%m%d)

# Falls kein Timeshift existiert: jetzt erstellen!
sudo timeshift --create --comments "Pre-GPU-fix-$(date +%Y%m%d)"
```

### Schritt 1: Zombie-Pakete entfernen (häufigste Ursache!)
```bash
# Alte 580er-Reste finden und purgen
dpkg -l | grep nvidia | grep ^rc
# Beispiel:
sudo dpkg --purge nvidia-dkms-580-open nvidia-kernel-common-580 \
  nvidia-compute-utils-580 libnvidia-compute-580
```

### Schritt 2: Treiber komplett neu installieren + DKMS bauen
```bash
# Treiber neu installieren
sudo apt install --reinstall nvidia-driver-595 nvidia-kernel-common-595

# DKMS-Build erzwingen
sudo dkms install nvidia/595.71.05 -k $(uname -r) || sudo dkms autoinstall

# Initramfs aktualisieren
sudo update-initramfs -u
```

### Schritt 3: xorg.conf prüfen/entfernen
```bash
# Prüfe ob xorg.conf existiert (BOOT-KILLER!)
cat /etc/X11/xorg.conf 2>/dev/null && echo "⚠️ xorg.conf existiert!"

# Wenn vorhanden: sichern und temporär entfernen
sudo mv /etc/X11/xorg.conf /etc/X11/xorg.conf.disabled-by-yuno-$(date +%Y%m%d)
```

### Schritt 4: Kernel-Module manuell laden (Test)
```bash
sudo modprobe nvidia
sudo modprobe nvidia-drm
sudo modprobe nvidia-modeset
sudo modprobe nvidia-uvm
```

### Schritt 5: nvidia-powerd reparieren
```bash
# Status prüfen
systemctl status nvidia-powerd
journalctl -u nvidia-powerd --since "5 minutes ago" | tail -20

# "Allocate Root client failed 0x26" → GPU nicht initialisiert
# Fix: erst Module laden (Schritt 4), dann Service neu starten
sudo systemctl restart nvidia-powerd

# Service wiederherstellen falls korrumpiert
sudo cp /usr/share/doc/nvidia-kernel-common-*/nvidia-powerd.service \
        /etc/systemd/system/nvidia-powerd.service
sudo systemctl daemon-reload
sudo systemctl restart nvidia-powerd
```

### Schritt 6: Verifizieren
```bash
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,power.draw,clocks.max.graphics --format=csv
systemctl is-active nvidia-powerd
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
```

### Schritt 7: PRIME-Check (vergessene Blockade!)
Nach DKMS-Rebuild und Modprobe kann `nvidia-smi` IMMER NOCH failen, wenn der PRIME-Modus auf `intel` steht. **Das ist kein Indikator für fehlgeschlagenen Fix, sondern ein fehlender PRIME-Wechsel!**

```bash
# PRIME-Status prüfen
prime-select query

# Wenn "intel" → auf nvidia umschalten
sudo prime-select nvidia

# Module laden (wichtig: OHNE Reboot)
sudo modprobe nvidia
sudo modprobe nvidia_modeset
sudo modprobe nvidia_drm
sudo modprobe nvidia_uvm

# Jetzt nvidia-smi testen
nvidia-smi

# Erst dann abmelden + wieder anmelden (sicherer als Reboot)
# → Xorg startet mit NVIDIA, kein Boot-Loop-Risiko
```

**Wichtig:** Nicht blind rebooten! Erst Module laden und `nvidia-smi` testen. Wenn das klappt: `prime-select nvidia` setzen und abmelden (nicht rebooten). Falls doch was schiefgeht: `Strg+Alt+F3` → Text-Console → `sudo prime-select intel` → zurück.

## Vollständige Symptom-Kaskade (aus Session 2026-06-27)

```
GPU-Tweak-Versuch → 6× Treiberwechsel (580↔595, open↔proprietär)
  → 4 Zombie-Pakete vom 580er hängen (rc-Status)
  → DKMS baut kein nvidia-Kernel-Modul (nvidia.ko fehlt)
  → xserver-xorg-video-nvidia-595 fehlt (nvidia_drv.so fehlt)
  → /etc/X11/xorg.conf verlangt HART "nvidia"
  → Xorg: "Failed to load module nvidia (module does not exist)"
  → Xorg: "(EE) no screens found"
  → GDM restart → BOOT-LOOP
```

## Prävention (Don't-Touch Liste)
- **NIEMALS** `nvidia-xconfig` auf Optimus-Laptops ausführen
- Stattdessen: `/etc/X11/xorg.conf.d/` Snippets verwenden
- Vor GPU-Tweaks immer **Timeshift Snapshot** erstellen
- `nvreg_fix.conf` mit `NVreg_OpenRmEnableUnsupportedGpus=1` nicht löschen (RTX 50xx)
- **Max 1 Treiberwechsel pro Tag** — 6 Wechsel in 36h produzieren garantiert Zombie-Pakete
- **NICHT zwischen open und proprietär hin- und herwechseln** — entscheide dich für EINEN

## Pitfalls
1. **xorg.conf auf Optimus-Laptops** = garantierter Boot-Loop
2. **GWE/Green With Envy** kann xorg.conf und powerd.service korrumpiert
3. **Coolbits über xorg.conf.d** (OutputClass) statt xorg.conf (Device Section)
4. **Kernel-Update** kann NVIDIA-Module invalidieren → dkms rebuild nötig
5. **Zombie-Pakete (rc-Status)** blockieren DKMS → immer zuerst cleanen
6. **"Allocate Root client failed 0x26"** ≠ nvidia-powerd Bug → GPU ist einfach nicht initialisiert
7. **xserver-xorg-video-nvidia-595** wird bei open/proprietär-Wechseln oft entfernt → muss explizit neu installiert werden
8. **`modprobe nvidia` funktioniert nicht wenn DKMS fehlt** → DKMS zuerst fixen!
