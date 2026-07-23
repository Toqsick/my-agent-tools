---
title: Kernel-Lockdown=integrity blockiert NVML-Hardware-Writes
datum: 2026-07-05
hardware: MEDION ERAZER 17 P1 · RTX 5060 · i7-13620H · Zorin 18.1
treiber: 595-open
session-beleg: perf-tuning-plan Chat 2026-07-05
---

# Symptom

Beim Versuch, NVML-basierte OC-Tools aufzurufen (z. B. `nvidia_oc set --freq-offset 100 --mem-offset 500`), passiert eines von zwei:

1. **Silent Failure:** Das Tool meldet `Set OK`, aber `nvidia-smi --query-gpu=clocks.current.sm` zeigt unveränderten Takt. Keine Fehlermeldung im Log.
2. **Hard-Lock:** Bildschirm friert ein, Tastatur reagiert nicht, Magic-SysRq unwirksam. Nur Hard-Reset hilft.

# Diagnose

```bash
cat /sys/kernel/security/lockdown
# Ausgabe bei Secure-Boot-Default:
# [ none ] integrity confidentiality
# ^^^^^^^^ aktuell aktive Stufe
```

Wenn `[ integrity ]` aktiv ist, ist das **die** Ursache. Lockdown=integrity bedeutet:

> *"Kernel zwingt Module, nur ihre eigenen Hardware-Register zu nutzen; NVML-Writes in GPU-Hardware-Register außerhalb des Modul-Scopes werden geblockt."*

NVML setzt beim OC aber Clock-Offset / Power-Limit / Memory-Offset direkt — und genau das ist betroffen.

# Lösung

**Vorbedingung:** User-Freigabe einholen. Security-Trade-off transparent kommunizieren.

## Schritt 1 — Vorab-Snapshot

```bash
sudo timeshift --create --comments "pre-lockdown-none-rtx5060" --tags B
```

## Schritt 2 — GRUB anpassen

```bash
sudo nano /etc/default/grub
# Setze/erweitere GRUB_CMDLINE_LINUX_DEFAULT="quiet splash lockdown=none"
# (Vorhandene splash/pci=... Parameter beibehalten, nur lockdown=... hinzufügen oder ersetzen)

sudo update-grub
sudo reboot
```

## Schritt 3 — Verifizieren

```bash
cat /sys/kernel/security/lockdown
# Erwartet: [ none ] leer
# ODER: keine Liste (wenn Lockdown komplett deaktiviert)

# Test-Schritt mit kleinem Offset:
sudo nvidia_oc set --index 0 --freq-offset 50 --mem-offset 200
# Erwartet: kein Silent-Failure, nvidia-smi zeigt geänderten Takt
```

## Schritt 4 — Zurückrollen bei Problemen

```bash
sudo nano /etc/default/grub
# GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"   # lockdown= entfernen, Default = integrity
sudo update-grub
sudo reboot
```

# Security-Trade-off

| Aspekt | Mit Lockdown=integrity | Mit Lockdown=none |
|---|---|---|
| Secure Boot | aktiv | aktiv (unverändert) |
| Modul-Signaturen | erzwungen | erzwungen (unverändert) |
| Live-Patching unsigned Code | **blockiert** | möglich |
| eBPF Programme in Kernel-Space | eingeschränkt | ohne Restriktion |
| NVML-Hardware-Writes | **blockiert** | erlaubt |
| GPU-OC via nvidia_oc/nvoc | **crasht/failt** | funktioniert |

**Fazit:** Lockdown=integrity ist eine **zusätzliche** Schutzschicht, nicht die einzige. Secure Boot + Modul-Signaturen bleiben aktiv. Für Bastis Use-Case (Gaming-Laptop, lokaler Single-User) ist der Trade-off akzeptabel — auf einem Server oder shared workstation würde ich es nicht empfehlen.

# Verwandte Themen

- Pitfall #24 — Wayland + NV-CONTROL: andere Hauptursache der "Tuning-Crash"-Symptome
- `references/wayland-nvcontrol-rtx50xx-2026-07-05.md`
- `references/prime-offload-env-vars-2026-06-28.md` — PRIME-Setup
- `references/boot-loop-recovery.md` — wenn was crasht
