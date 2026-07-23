# Zombie-rc-Paket Beseitigung — Boot-Loop-Prävention 2026-06-27

**Session:** RTX 5060, Driver 595.71.05-open, Kernel 6.17.0-35

## Symptom

Nach Treiber-Wechseln (proprietär↔open, 535↔595, etc.) bleiben rc-Pakete:

```
rc  linux-modules-nvidia-595-6.17.0-35-generic
rc  nvidia-dkms-595-open
rc  linux-modules-nvidia-595-open-6.17.0-35-generic
```

Diese rc-Pakete können:
1. DKMS-Builds blockieren (Konflikt zwischen altem und neuem Kernel-Modul)
2. Kernel-Update triggern ohne saubere Modul-Installation
3. System in "scheduled for reboot" State trapping
4. Wenn nvidia_drv.so fehlt + xorg.conf hard-require: **BOOT-LOOP**

## Diagnose

```bash
# ALLE nvidia rc-Pakete finden (MIT ^rc — das sind die problematischen!)
dpkg -l | grep nvidia | grep ^rc

# Irreführende sichere Pakte (ignorieren):
dpkg -l | grep nvidia | grep ^ii   ← OK
dpkg -l | grep nvidia | grep ^iU   ← Installed, nicht configured
dpkg -l | grep nvidia | grep ^iF   ← FAILED (ALARM!)

# Ist DKMS-Build intakt trotz rc-Paketen?
dkms status | grep nvidia
```

## Lösung (Sequenz!)

```bash
# 1. Zuerst: Timeshift snapshot
sudo timeshift --create --comments "Zombie-cleanup-$(date +%Y%m%d)"

# 2. Zombie rc-Pakete purgen (IMMER alle in einem Befehl)
sudo dpkg --purge \
  linux-modules-nvidia-595-6.17.0-35-generic \
  nvidia-dkms-595-open \
  linux-modules-nvidia-595-open-6.17.0-35-generic \
  2>/dev/null

# 3. Falls rc-Paket restenweise bleibt:
sudo dpkg --purge $(dpkg -l | grep nvidia | grep ^rc | awk '{print $2}')

# 4. DKMS-Status prüfen (muss "installed" zeigen):
dkms status | grep nvidia

# 5. Rebuild falls nötig:
sudo dkms install nvidia/595.71.05 -k $(uname -r)
```

## Boot-Loop-Fallsicherheit

Wenn die rc-Purging PRIORI eines Treiber-Wechsels stattfand:
1. `apt autoremove --purge` alte Reste beseitigen
2. `dkms install --force` erzwingen
3. `update-initramfs -u`
4. Erst dann REBOOTEN, nicht zuvor!

## Botschaft für andere Sessions

**Max 1 Treiberwechsel pro Tag** ist heilig. Jeder Wechsel produziert
mindestens 1 rc-Paket. Der Sicherheits-Check für jede Session:

```bash
dpkg -l | grep nvidia | grep ^rc
```

Muss leer sein. Wenn nicht → zuerst purgen, dann erst weiter arbeiten.
