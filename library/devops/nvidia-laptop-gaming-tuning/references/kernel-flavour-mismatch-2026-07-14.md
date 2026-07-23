# Kernel Flavour Mismatch — lowlatency booted, NVIDIA modules only on generic

**Datum:** 2026-07-14 (Rezidiv von 2026-06-27)
**Setup:** Zorin OS 18.1, NVIDIA-driver-595-open, RTX 5060
**Auswirkungen:** `nvidia-smi` bricht mit "couldn't communicate with the NVIDIA driver" ab, `lsmod` leer, `nvidia_oc` crasht `DriverNotLoaded`.

---

## Symptom-Tabelle

| Check | Normal | Fail |
|---|---|---|
| `uname -r` | `6.17.0-35-generic` | `6.8.0-134-lowlatency` |
| `lsmod | grep nvidia` | `nvidia`, `nvidia_drm`, `nvidia_modeset`, `nvidia_uvm` | (leer) |
| `nvidia-smi -L` | `RTX 5060 Laptop GPU` | `Failed to communicate with NVIDIA driver` |
| `nvidia_oc` | `active` | `DriverNotLoaded` |
| `find /lib/modules/$(uname -r) -name 'nvidia*.ko*'` | nvidia.ko (595-open) + nvidia_uvm.ko | nur `nvidiafb.ko.zst` und `nvidia-wmi-ec-backlight.ko.zst` |
| `ls /dev/nvidia*` | `/dev/nvidia0 /dev/nvidiactl /dev/nvidia-modeset` | (nichts) |
| `systemctl is-active ollama` | geht auf GPU | CPU-only, langsames Ollama |

---

## Root Cause (sehr typisch für Ubuntu Studio + NVIDIA)

Das System bekam per GRUB den **Ubuntu Studio lowlatency-Kernel-Flavour** (`6.8.0-134-lowlatency`) vorgezogen, weil `/etc/default/grub.d/ubuntustudio.cfg` setzt:

```bash
GRUB_FLAVOUR_ORDER="lowlatency $GRUB_FLAVOUR_ORDER"
```

Die NVIDIA-595-open-Module sind aber nur für den **generic HWE-Kernel** (`6.17.0-35-generic`) per Paket installiert:

```
ii  linux-modules-nvidia-595-open-6.17.0-35-generic
ii  linux-modules-nvidia-595-open-generic-hwe-24.04
rc  linux-modules-nvidia-595-6.17.0-35-generic             # purged
```

Für den lowlatency-Kernel existiert kein `linux-modules-nvidia-595-open-6.8.0-134-lowlatency` — folglich kein `nvidia.ko`, Driver lädt nicht, NVML bleibt leer.

## Das Paket ist da! Kein Reinstall nötig

Wichtig: `nvidia-driver-595-open`, `nvidia-utils-595`, `nvidia-prime` und sogar der Module-Metapaket sind **alle installiert (ii)** — der Fehler liegt AUSSCHLIESSLICH darin, dass der falsche Kernel bootet. **Reinstall des Drivers bringt nichts und verursacht nur Churn.**

## Fix

### Phase 1: Pre-Reboot (GRUB-Flavour-Override + Default setzen)

**1. Flavour-Reihenfolge überschreiben**  
Erzeuge eine override-config die nach `ubuntustudio.cfg` alphabetisch greift:

```bash
sudo tee /etc/default/grub.d/zz-yuno-flavour-generic.cfg >/dev/null <<'EOF'
# Yuno 2026-07-14: generic before lowlatency (NVIDIA modules only on generic)
GRUB_FLAVOUR_ORDER="generic lowlatency"
EOF
```

Bestätigen:
```bash
grep -n GRUB_FLAVOUR_ORDER /etc/default/grub.d/*
# Erwartet: zz-yuno-flavour-generic.cfg als letzter Eintrag
```

**Alternative (invasiver):** direkt in `ubuntustudio.cfg` kommentieren:
```bash
sudo sed -i 's/GRUB_FLAVOUR_ORDER/#GRUB_FLAVOUR_ORDER/' /etc/default/grub.d/ubuntustudio.cfg
```
Das entfernt nicht den Rest der Datei (`threadirqs` bleibt aktiv).

**2. Default auf generic setzen**

```bash
# Zuerst Entry-Titel finden:
awk -F\' '/menuentry / {print i++ " : " $2}' /boot/grub/grub.cfg

# Dann setzen (Beispiel — exakten Titel anpassen):
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.17.0-35-generic"
# Oder one-shot für erste Boot:
sudo grub-reboot "Advanced options for Ubuntu>Ubuntu, with Linux 6.17.0-35-generic"

sudo update-grub
```

**3. Verify:**
```bash
grub-editenv list
# saved_entry oder next_entry soll auf generic zeigen
```

**4. Nvidia_OC Service deaktivieren (optional, verhindert Boot-Fail)**  
Da `nvidia_oc` auf failed geht wenn der Kernel falsch ist:
```bash
sudo systemctl disable nvidia_oc   # erst wieder aktivieren wenn generischer Kernel läuft
systemctl disable --now nvidia_oc  # stoppt auch sofort
```

### Phase 2: Reboot

Nach Sicherung offener Arbeiten:
```bash
sudo reboot
```

Beim GRUB-Menü (5s Timeout) notfalls manuell **Advanced options → 6.17.0-35-generic** wählen.

### Phase 3: Post-Reboot-Verification

```bash
uname -r
# Muss enden: -generic

lsmod | grep -E '^nvidia'
# Erwartet: nvidia, nvidia_uvm, nvidia_drm, nvidia_modeset

nvidia-smi -L
# RTX 5060 Laptop GPU

bash -ic 'prime-run nvidia-smi -L'
# Auch mit PRIME-Offload-Env funktional

systemctl restart --now nvidia_oc
systemctl is-active nvidia_oc
# active
```

### Phase 4: Rezidiv-Schutz (optional)

Metapackage halten damit kein apt upgrade den NVIDIA-Support auf dem generic-Kernel verliert:
```bash
sudo apt-mark hold \
  nvidia-driver-595-open \
  nvidia-utils-595 \
  nvidia-prime \
  linux-modules-nvidia-595-open-generic-hwe-24.04
```

Lowlatency-Kernel entfernen (nur wenn Studio-Audio nicht gebraucht wird):
```bash
# NUR auf explizite Anweisung!
# sudo apt remove linux-image-lowlatency linux-headers-lowlatency
```

---

## Häufigkeit / Vorgeschichte

- **2026-06-27:** Erstes Auftreten dokumentiert in `docs/system/` und `nvidia-laptop-gaming-tuning` Trigger-Liste
- **2026-07-14:** Gleicher Fehler, gleicher Fix. Dieses Mal trat der Flavour-Wechsel vermutlich durch `apt upgrade` und Kernel-Update auf, das die lowlatency-Metas neu aktivierte

Das Muster wiederholt sich wenn GRUB bei einem Kernel-Update auf lowlatency springt. Der Fix (`zz-yuno-flavour-generic.cfg`) bleibt beim Update erhalten.