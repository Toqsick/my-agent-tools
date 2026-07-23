# SD-Karten Validierung (Fake-Erkennung)

## Problem
Billig-SD-Karten (besonders 256GB+, No-Name) melden oft eine falsche Kapazität an. Der Controller fälscht z.B. 500GB, aber der echte Speicher ist nur 8-32GB. Daten über dem echten Limit gehen verloren — oft ohne Fehlermeldung.

## Tools

### f3 (Fight Flash Fraud) — Goldstandard
```bash
sudo apt install f3

# Fake-Test (DESTRUKTIV — löscht alle Daten!)
# --time-ops gibt Schreib-/Lesegeschwindigkeiten aus
sudo f3probe --destructive --time-ops /dev/sdX

# Schreib-/Lesetest (ohne Löschen, aber langsam)
sudo f3write /dev/sdX
sudo f3read /dev/sdX
```

**Wichtig:** `f3probe` schreibt über die gesamte Karte und prüft, ob die gemeldete Kapazität echt ist. Eine Fake-Karte wird sofort erkannt, weil Daten über dem echten Speicherlimit verloren gehen.

### badblocks — Linux-intern
```bash
sudo badblocks -wvs -b 4096 /dev/sdX
```
- Schreibt Muster auf jeden Block und liest sie zurück
- Sehr zuverlässig, aber **extrem langsam** bei großen Karten
- Nur für Surface-Test, nicht primär für Fake-Erkennung

### mmc-utils — für eMMC/SD-Controller
```bash
sudo apt install mmc-utils
sudo mmc extcsd read /dev/mmcblk0
```
- Liest Extended CSD-Register — zeigt echte Kapazität
- **Nicht für USB-Reader** (nur direkte eMMC/SD-Controller)

## Workflow (2-Phase — schnell dann gründlich)

### Phase 1: Schnell-Check (2 Min, nicht-destruktiv)
```bash
# 1. Gerät identifizieren
lsblk -f
df -h /media/$USER/<LABEL>

# 2. USB-Reader prüfen (Verdacht auf No-Name-Adapter)
lsusb | grep -i "reader\|storage\|mxt"
lsusb -v -d <VID:PID> 2>&1 | grep -E "(idVendor|idProduct|iManufacturer|iProduct)"

# 3. Echte Sektorzahl prüfen
sudo blockdev --getsize64 /dev/sdX
sudo parted /dev/sdX print

# 4. Kapazitäts-Diskrepanz erkennen (starker Fake-Indikator)
# Wenn lsblk 500GB meldet aber partition nur 30GB hat → Fake!
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,MODEL,VENDOR /dev/sdX

# 5. 1GB Roundtrip-Test (schnell, nicht-destruktiv)
sudo mount -o uid=$USER,gid=$USER,umask=000 /dev/sdX1 /mnt
dd if=/dev/urandom of=/tmp/test_1gb.bin bs=1M count=1024
cp /tmp/test_1gb.bin /mnt/test_1gb.bin && sync
cp /mnt/test_1gb.bin /tmp/test_1gb_read.bin
cmp /tmp/test_1gb.bin /tmp/test_1gb_read.bin && echo "✅ OK" || echo "❌ KORRUPT"
rm /mnt/test_1gb.bin
```

### Phase 2: Voll-Test (destruktiv, 30min–je nach Größe)
```bash
# Unmount zwingen falls busy
sudo umount -l /dev/sdX1

# f3write füllt gesamte Karte mit Testdateien
f3write /mnt/

# f3read verifiziert alle Dateien
f3read /mnt/

# ODER: f3probe (direkt auf Device, destruktiv, zeigt echte Kapazität)
sudo f3probe --destructive --time-ops /dev/sdX
```

**Hinweis zu Mount-Berechtigungen:** Standard-UDISKS2-Mount als root → `cp` schlägt fehl mit "Keine Berechtigung". Immer mit `sudo mount -o uid=$USER,gid=$USER,umask=000` remounten für User-Zugriff.

## Typische Fake-Indikatoren
- 500GB SD-Karte für <15€ (zu gut um wahr zu sein)
- Kein Markenname / No-Name
- `lsblk` zeigt 500GB Device-Größe aber Partition ist nur 29-32GB
- `lsusb` zeigt generische VID:PID wie `aaaa:8816` (MXTronics)
- Schreibgeschwindigkeit bricht bei echten Speicherlimit ein

## Pitfalls
1. **f3probe ist destruktiv** — löscht alle Daten vorher!
2. **USB-Reader vs. direkter Slot** — manche Reader verbergen Kapazitätsprobleme
3. **mmc-utils funktioniert nicht über USB-Reader** — nur direkte SD-Controller
4. **500GB SD-Karten sind extrem selten** — die meisten "500GB" Karten sind Fakes mit 32-64GB echtem Speicher
5. **Mount-Berechtigungen** — UDISKS2 mounted als root, `cp` für User schlägt fehl → `sudo mount -o uid=$USER,gid=$USER,umask=000` verwenden
6. **f3write bei 500GB dauert ~30min** — im Hintergrund laufen lassen (`background=true`), nicht inline warten
7. **sudo + Background-TTY-Kollision** — `sudo f3probe` im Hintergrund (`background=true`) scheitert ohne TTY weil sudo ein Passwort braucht. Fix: Entweder `sudo -n` (falls NOPASSWD konfiguriert), oder User bittet den Befehl per `! command` im Chat auszuführen (dann interaktives Terminal).

## Bekannte Fake-Reader/Chips

| USB VID:PID | Hersteller | Hinweis |
|---|---|---|
| `aaaa:8816` | MXTronics / MXT USB Storage Device | Häufig in No-Name SD-Readern, oft mit Fake-Karten kombiniert. Meldet oft 500GB Device-Kapazität bei 30GB echter Partition. |
| `090c:xxxx` | Silicon Motion (Feiya) | Seriös, aber auch in Billig-Containern |

## Nach Fake-Erkennung: Karte neu flashen

Wenn f3probe die echte Kapazität z.B. als 32GB zeigt:
```bash
# 1. Partitionstabelle löschen
sudo wipefs -a /dev/sdX

# 2. Neue Partition mit ECHTER Kapazität anlegen
sudo parted /dev/sdX --script mklabel msdos
sudo parted /dev/sdX --script mkpart primary fat32 1MiB 100%
sudo mkfs.vfat -F 32 /dev/sdX1

# 3. Optional: Image flashen (z.B. Raspberry Pi OS, RetroPie)
# sudo dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
```

Danach ist die Karte mit ihrer **echten** Kapazität nutzbar — keine Datenverluste mehr.
