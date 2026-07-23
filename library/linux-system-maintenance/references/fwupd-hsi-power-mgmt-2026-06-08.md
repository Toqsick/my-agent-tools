# fwupd HSI, s2idle & GNOME Power-Management (2026-06-08)

## fwupd HSI — Was die Levels WIRKLICH messen

fwupd's Host Security ID (HSI) hat 4 Stufen, aber **die Messung ist oft
event-basiert, nicht capability-basiert**. Das ist ein häufiger Fehler bei
der Interpretation.

### Event-based vs Capability-based — der Unterschied

| Level | Capability-Frage (was geht) | Event-Frage (was ist passiert) |
|-------|---------------------------|-------------------------------|
| HSI-1 UEFI/TPM/Secure Boot | ✓ capability | ✓ statisch messbar |
| HSI-2 BootGuard/IOMMU | ✓ capability | ✓ statisch messbar |
| **HSI-3 Suspend To Idle** | "kann das System s2idle?" | **"Wurde jemals s2idle ausgeführt?"** |
| HSI-3 Suspend To RAM | "kann das System STR?" | "Wurde jemals STR ausgeführt?" |
| HSI-3 Pre-boot DMA | ✓ capability | ✓ statisch messbar |
| HSI-4 Encrypted RAM | "Hat HW TME?" | identisch (capability-only) |

**Konsequenz:** HSI-3 zeigt "Nicht eingeschaltet" obwohl s2idle verfügbar ist,
solange kein Suspend-Cycle seit Boot stattgefunden hat. Die "Nicht
eingeschaltet"-Meldung ist NICHT "feature fehlt" sondern "feature nie benutzt".

### Debug-Workflow für HSI-3 "Nicht eingeschaltet"

```bash
# 1. Ist s2idle im Kernel verfügbar?
cat /sys/power/mem_sleep
# → [s2idle] deep  (s2idle verfügbar, aktuell default)

# 2. Ist s2idle im Kernel-cmdline als Default?
cat /proc/cmdline | grep mem_sleep
# → ... mem_sleep_default=s2idle ...

# 3. systemd-suspend.service aktiv?
systemctl status systemd-suspend | grep Active
# → Active: inactive (dead)  ← kein Suspend seit Boot = HSI-3 fail

# 4. Was blockiert Suspend?
systemd-inhibit --list
# → Liste alle Inhibit-Services (ModemManager, NetworkManager, etc.)

# 5. Manueller Suspend (legt Laptop 10s schlafen)
systemctl suspend
# → Nach Resume: fwupd-Refresh → HSI-3 wird Pass
```

### fwupd-Historie checken

```bash
# fwupdmgr history mit Datum-Filter (Pitfall 26 aus multi-agent-research)
fwupdmgr get-history | awk '/Date|Suspend|HSI/' | head -20
```

## fwupd "Verdorben" / Taint — die echten Ursachen

"Linux Kernel Verification: Verdorben" klingt alarmierend, ist meist harmlos.
Die echten Ursachen:

### Taint-Bits 101

`/proc/sys/kernel/tainted` zeigt OR-kombinierte Bits. Häufig:

| Bit | Wert | Name | Ursache |
|-----|------|------|---------|
| 0 | 1 | PROPRIETARY_MODULE | NVIDIA/AMD out-of-tree Treiber |
| 2 | 4 | UNSIGNED_MODULE | unsignierte Module geladen |
| 12 | 4096 | STALE_HW | Hardware-Inkonsistenzen (ACPI-Bugs) |

**NVIDIA Out-of-Tree lade-Taint** ist NORMAL auf Linux-Laptops mit dedizierter
GPU. Der Treiber ist signiert (Canonical Ltd. Master Key), aber das ändert
nichts am Taint. fwupd zählt das als "verdorben" obwohl es sicher ist.

### ACPI-BIOS-Bugs als stale_hw-Quelle

```bash
# Boot-Log nach ACPI-Errors durchsuchen
journalctl -k | grep -iE 'ACPI.*(error|bug)' | head -10
# Häufig: "Could not resolve symbol [...], AE_NOT_FOUND"
# → BIOS-Hersteller hat fehlerhafte DSDT/SSDT-Tabellen ausgeliefert
```

**Fix:** Nur durch BIOS-Update des Herstellers. `fwupdmgr get-updates`
checken, oft kein neueres BIOS verfügbar (Median/ERA ZER etc.).

**Workaround-Kernelparameter (VORSICHTIG testen):**
```bash
# Klare Errors statt Tableload (kann manche HW-Features brechen)
sudo grubby --update-kernel=ALL --args="acpi=strict"

# Linux erzwingt statt Windows-ACPI
sudo grubby --update-kernel=ALL --args="acpi_osi=Linux"
```

## s2idle aktivieren + lid-switch konfigurieren

### Standard-Konfiguration (Zorin/Ubuntu)

Ubuntu 22.04+ und Derivate (Zorin) haben s2idle im Kernel, ABER:
- `HandleLidSwitch` ist in `/etc/systemd/logind.conf` **auskommentiert** (default = suspend)
- GNOME-Setting `lid-close-suspend-with-external-monitor` ist **false** (default)
- → Bei externem Monitor: lid-close macht NICHTS

### Komplettes Aktivierungspaket

```bash
# 1. LidSwitch-Logind-Drop-in (sudo)
sudo mkdir -p /etc/systemd/logind.conf.d/
sudo tee /etc/systemd/logind.conf.d/s2idle.conf > /dev/null <<'EOF'
[Login]
HandleLidSwitch=suspend
HandleLidSwitchExternalPower=suspend
HandleLidSwitchDocked=ignore
EOF

# 2. s2idle-Sleep-Drop-in (sudo)
sudo mkdir -p /etc/systemd/sleep.conf.d/
sudo tee /etc/systemd/sleep.conf.d/s2idle.conf > /dev/null <<'EOF'
[Sleep]
SuspendState=mem
SuspendEstimationSec=60min
EOF

# 3. GNOME-Power-Management (User-Level, ohne sudo)
gsettings set org.gnome.settings-daemon.plugins.power lid-close-suspend-with-external-monitor true
gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action 'suspend'
gsettings set org.gnome.settings-daemon.plugins.power lid-close-battery-action 'suspend'

# 4. Daemon-reload (sudo)
sudo systemctl daemon-reload

# 5. Test
systemctl suspend  # 10s warten, dann Power-Button zum Aufwachen

# 6. fwupd-History prüfen
fwupdmgr get-history | grep -i suspend
# → "Suspend To Idle: Nicht eingeschaltet → Bestanden" = HSI-3 grün
```

## GNOME lid-switch-Inhibitor — der gemeinste Stolperstein

Nach den obigen Settings: **lid-zuklappen macht TROTZDEM manchmal nichts**.
Grund: gsd-power hält einen `handle-lid-switch`-Inhibitor, typischerweise wenn:

```bash
# Inhibitoren checken
systemd-inhibit --list
# Häufiger Schuldiger:
# bratan ... gsd-power handle-lid-switch
#   "External monitor attached or configuration changed recently"
#   → block-Modus, nichts geht durch
```

### Drei Optionen bei block-Inhibitor

| Option | Befehl | Wirkung |
|--------|--------|---------|
| A. Manueller systemctl suspend | `systemctl suspend` | GEHT (umgeht lid-inhibitor) |
| B. gsd-power restart | `systemctl --user restart gsd-power` | Cleared Inhibitor, danach lid-close geht |
| C. Warten | (nichts) | gsd-power gibt Inhibitor nach Minuten automatisch frei |

**Wann A:** Schneller Test wenn du nur den fwupd-Event auslösen willst.
**Wann B:** Wenn du lid-close dauerhaft funktional haben willst.
**Wann C:** Geduldig, Inhibitor löscht sich meist nach 5-15 min.

### Eigene Erfahrung (2026-06-08)

Setting `lid-close-suspend-with-external-monitor true` allein **reicht nicht**
— der Inhibitor wird vom gsd-power intern gehalten und cleared sich erst
nach explizitem restart. In der Zwischenzeit:
- `systemctl suspend` funktioniert (geht direkt zu systemd, nicht über gsd-power)
- `lid-close` über den GNOME-Inhibitor geblockt (auch mit neuem Setting)

**Empfehlung für reproduzierbares Verhalten:**
```bash
# Persistenter Fix: systemd-suspend.service manuell starten
sudo systemctl enable systemd-suspend.service
# Dann ist zumindest systemctl suspend immer ohne Inhibitor-Konflikt verfügbar
```

## systemd-inhibit — das wichtigste Debug-Tool

Bei SUSPEND-Issues IMMER zuerst `systemd-inhibit --list` checken.

```bash
# Alle aktiven Inhibitoren
systemd-inhibit --list

# Nur Block-Inhibitoren (verhindern Aktion komplett)
systemd-inhibit --list --mode=block

# Was für "sleep" blockt?
systemd-inhibit --list --what=sleep
```

**Häufige Inhibitor-Quellen:**
- `gsd-power` (GNOME) — lid-switch, power-key handling
- `ModemManager` — "needs to reset devices" (delay, nicht block)
- `NetworkManager` — "needs to turn off networks" (delay)
- `UPower` — "Pause device polling" (delay)
- `Unattended Upgrades Shutdown` — "Laufende Aktualisierungen" (delay)
- `gnome-session-b` — "user session inhibited" (block während active session)

**delay vs block:**
- `delay` — verschiebt Suspend bis Inhibitor aufgibt (z.B. nach 90s)
- `block` — verhindert Suspend komplett, muss explizit aufgehoben werden

## Swap — wann encrypted, wann none, wann ZRAM?

fwupd prüft 3 Swap-States: deaktiviert / nicht verschlüsselt / verschlüsselt.
**Best Practice je nach Use-Case:**

| Use-Case | Empfehlung |
|----------|-----------|
| Desktop mit 16GB+ RAM, kein Hibernate | **kein Swap** (so wie 2026-06-08) |
| Laptop mit Hibernate (Suspend-to-Disk) | verschlüsselter Swap = RAM + 2GB |
| Memory-intensive Workloads (Docker, Browser-Tabs) | ZRAM (compressed swap in RAM) |
| Server | dedizierte Swap-Partition, encrypted |

**Swap deaktivieren (wie bei Basti 2026-06-08):**
```bash
sudo swapoff -a
# Dauerhaft: /etc/fstab-Eintrag für Swap-Partition auskommentieren
```

**ZRAM einrichten (moderne Alternative):**
```bash
sudo apt install zram-config
# systemd-service startet automatisch
swapon --show  # zeigt jetzt zram0 statt Partition
```

**Encrypted Swap (für Hibernate):**
```bash
# 1. Swap-File anlegen (Größe = RAM + Reserve)
sudo fallocate -l 18G /swapfile
sudo chmod 600 /swapfile

# 2. Verschlüsseln (interaktiv: Passwort setzen)
sudo cryptsetup luksFormat /swapfile
sudo cryptsetup open /swapfile cryptswap
sudo mkswap /dev/mapper/cryptswap
sudo swapon /dev/mapper/cryptswap

# 3. Resume-Device in initramfs setzen (für Hibernate)
echo "RESUME=UUID=$(blkid -s UUID -o value /swapfile)" | \
  sudo tee /etc/initramfs-tools/conf.d/resume
sudo update-initramfs -u
```

## fwupd-Refresh beschleunigen

Default: alle 12h (`fwupd-refresh.timer`). Für schnelleren BIOS-Update-Push:

```bash
sudo systemctl edit fwupd-refresh.timer
# Inhalt:
# [Timer]
# OnCalendar=*:0/4
# RandomizedDelaySec=15min
```

## Quick-Reference: HSI-Ziel auf Consumer-Laptop

| HSI-Level | Voraussetzung | Auf Bastis ERAZER 17 P1 |
|-----------|---------------|--------------------------|
| HSI:1 | UEFI/Secure Boot/TPM/ME gesperrt | ✓ ja |
| HSI:2 | + BootGuard/IOMMU aktiv | ✓ ja |
| HSI:3 | + Suspend/DMA/CET | ✓ erreichbar (10 Min Fix) |
| HSI:4 | + Encrypted RAM (TME) | ❌ HW-Limit (kein vPro) |

**Ziel:** HSI:3 (★★★★ auf Consumer-Laptop) — exzellent.
HSI:4 nur mit Server-CPU (Xeon, AMD EPYC).
