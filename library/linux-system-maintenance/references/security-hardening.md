# Linux Security Hardening via fwupd HSI

Session: 2026-06-03  
Hardware: ERAZER 17 P1 (i7-13620H)  
OS: Zorin OS 18.1

---

## fwupd HSI lesen

```bash
fwupdmgr security --force
```

Ausgabe ist ein Report mit Leveln HSI-1 bis HSI-4 plus Runtime-Tests.

### HSI-Level Bedeutung

| Level | Was geprüft | Zielgruppe |
|-------|-------------|------------|
| HSI-1 | Firmware-Integrität (Secure Boot, TPM, ME) | Jeder |
| HSI-2 | Boot-Schutz (BootGuard, IOMMU, Debug-Lock) | Jeder |
| HSI-3 | Sleep/DMA/CET (s2idle, Pre-boot DMA) | Security-bewusst |
| HSI-4 | RAM-Verschlüsselung (TME/SME) | Enterprise |

"HSI:2!" bedeutet: alle HSI-1 und HSI-2 Tests bestanden, mindestens ein HSI-3/4-Fail.

---

## Häufige Fails und Fixes

### 1. Linux Swap nicht verschlüsselt

```
Runtime Tests
  Linux Swap: ! Fail (Nicht verschlüsselt)
```

**Warum schlimm:** Swap liegt als Klartext-Datei auf der Platte. RAM-Auslagerung enthält Passwörter, Schlüssel, Dokumente.

**Fix: ZRAM statt Swap-Datei**

ZRAM = komprimierter RAM-Bereich als Swap-Ersatz. Flüchtig, nie auf Platte.

```bash
# Installieren
sudo apt install zram-config

# Alte Swap deaktivieren
sudo swapoff /swapfile
sudo sed -i 's|^/swapfile|# /swapfile|' /etc/fstab

# ZRAM starten
sudo systemctl enable --now zram-config

# Alte Swap-Datei löschen (freut 8GB)
sudo rm /swapfile
```

**Trade-offs:**

| | Swap-Datei | ZRAM |
|---|---|---|
| Geschwindigkeit | ~500 MB/s (SSD) | ~25 GB/s (RAM) |
| Verschlüsselung | ❌ Klartext | ✅ Flüchtig |
| SSD-Verschleiß | ❌ Schreibt auf SSD | ✅ Zero Wear |
| Strom | Niedrig | Etwas höher (Kompression) |

### 2. Suspend-to-RAM (S3) aktiv

```
HSI-3 Tests
  Suspend To RAM: ! Fail (Aktiviert)
  Suspend To Idle: ! Fail (Nicht eingeschaltet)
```

**Warum schlimm:** S3 hält RAM aktiv. Cold-Boot-Attacke möglich (RAM-Chips auslesen nach Abkühlen).

**Fix: s2idle als Standard**

```bash
# GRUB-Config anlegen
echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT mem_sleep_default=s2idle"' \
  | sudo tee /etc/default/grub.d/s2idle.cfg
sudo update-grub
```

**Trade-offs:**

| | S3 (deep) | s2idle |
|---|---|---|
| Sicherheit | ⚠️ Cold-Boot möglich | ✅ CPU läuft minimal |
| Akku im Sleep | ~0.5W (~1%/h) | ~2-3W (~3-5%/h) |
| Aufwachen | ~1s | ~2-3s |
| fwupd HSI | HSI:2 | HSI:3 |

### 3. Linux Kernel "verdorben" (Taint)

```
Runtime Tests
  Linux Kernel Verification: ! Fail (Verdorben)
```

**Meist harmlos.** Status-Code prüfen:

```bash
cat /proc/sys/kernel/tainted
```

| Bit | Wert | Bedeutung |
|-----|------|-----------|
| 12 | 4096 | Kernel warning issued |

Ursache: Proprietärer Treiber (Nvidia) hat `WARN_ON` ausgelöst. Kein echtes Sicherheitsrisiko, aber fwupd moniert es.

**Fix:** `sudo dmesg | grep -i "warning"` → meist harmlos, ignorieren.

### 4. Encrypted RAM nicht unterstützt

```
HSI-4 Tests
  Encrypted RAM: ! Fail (Nicht unterstützt)
```

**Nicht fixbar.** Intel TME (Total Memory Encryption) fehlt in der CPU (i7-13620H hat es nicht, nur HX-SKUs). Hardware-Limit.

---

## Schnelle HSI-Verbesserung

Mit **nur ZRAM** erreicht man meist schon **HSI:3** auf Consumer-Hardware:

```bash
# ZRAM einrichten
sudo apt install zram-config
sudo systemctl enable --now zram-config
sudo swapoff /swapfile
sudo sed -i 's|^/swapfile|# /swapfile|' /etc/fstab
sudo rm /swapfile

# s2idle optional (Trade-off: Akku)
echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT mem_sleep_default=s2idle"' \
  | sudo tee /etc/default/grub.d/s2idle.cfg
sudo update-grub

# Reboot
sudo reboot

# Prüfen
fwupdmgr security --force
```

---

## wichtige Pfade

- `/sys/power/mem_sleep` — aktueller Sleep-Modus (`[s2idle] deep` vs `s2idle [deep]`)
- `/proc/sys/kernel/tainted` — Kernel-Taint-Status
- `swapon --show` — Swap-Status (sollte nur `zram` zeigen)
