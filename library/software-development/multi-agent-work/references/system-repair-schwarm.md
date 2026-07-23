# System-Repair-Schwarm: Waydroid-Case-Study (2026-07-04)

## Ausgangslage

Waydroid 1.6.2 Mainline auf Ubuntu 24.04, Kernel 6.17.0-35-generic, NVIDIA 595.71.05, GNOME 46 / Mutter Compositor.
`waydroid session start` schlägt fehl mit: **"Hardware service is not even started"** — Container bleibt STOPPED.

## Scout-Fragenkatalog (5 Lanes parallel)

Fünf Scouts wurden losgeschickt, jeder mit einer klaren Lane:

| Scout | Lane | Frage |
|-------|------|-------|
| A | GPU | NVIDIA-Treiber-Status? EGL/GBM-Bridge? Vulkan? |
| B | Display | Wayland-Socket? XWayland? Compositor? GNOME-Mutter? |
| C | Kernel | `binder_linux` lädbar? `ashmem`? Kernel-Version vs Waydroid 1.6.2? |
| D | Konflikt | Docker←→Waydroid-Netzwerk? cgroup v2? User-Namespaces? |
| E | System | Flatpak-Runtimes? ProtonVPN-Route? Andere Störfaktoren? |

**Ergebnis der 5 Scouts (Konvergenz-Bewertung):** 4/5 konvergiert auf dieselbe Root-Cause. Scout D+E bestätigen: keine Kollision mit Docker, keine Flatpak-Störung, keine VPN-Probleme. Hohe Konfidenz.

## Root-Cause (chicken-and-egg)

**Drei unabhängige Blocker, die sich gegenseitig blockieren:**

```
binder_linux nicht geladen ← ashmem fehlt (Kernel 6.17 hat es nicht)
       ↓
Container kann nicht starten (kein /dev/binder, kein /dev/ashmem)
       ↓
Android-Hardware-Service läuft nicht → erzeugt keine host-permissions/*.xml
       ↓
Nächster Startversuch scheitert an fehlenden Permissions
       ↓
(Zurück zu Zeile 1 — Loop)
```

### Blocker im Detail

1. **`binder_linux` nicht persistent geladen** — Ubuntu-Kernel hat das Modul (`binder_linux.ko.zst`) aber Waydroid's `drivers.py` versucht `modprobe` als User → failt still. Container bekommt keine `/dev/binder*`-Nodes.
2. **`ashmem_linux` existiert nicht mehr** — Kernel 6.17 (≥5.18) hat ashmem aus dem Tree entfernt. Waydroid 1.6.2 `drivers.py` ruft `modprobe ashmem_linux` → failt. Android-Init braucht `/dev/ashmem`.
   - **Fix:** `sys.use_memfd=true` ist in `waydroid_base.prop` **bereits gesetzt** (Waydroid 1.6.2 erwartet memfd). Nur der Python-Helfer testet noch auf `/dev/ashmem` → `sudo touch /dev/ashmem && sudo chmod 0666` reicht als Fake.
3. **`/var/lib/waydroid/host-permissions/` ist leer** — Waydroid's `user_manager.py` erzeugt die `1000-wayland.xml` erst **zur Laufzeit** wenn der Container den Wayland-Socket öffnet. Aber Container startet nicht ohne Binder + ashmem → Henne-Ei.

## Reparatur-Phasen

### Phase 1: Scouts (read-only) — 5 parallele Subagenten
- Kein Sudo nötig
- System-Zustand erfassen: `lsmod`, `ls -la /dev/binder* /dev/ashmem`, `cat /var/lib/waydroid/*`, `lsof -i`, `systemctl status`, Docker-Netze
- **Output:** Synthese mit klarer Root-Cause + 3 Optionen

### Phase 2: User-Entscheidung + Sudo-Abfrage
- 3-4 Architektur-Optionen präsentieren (A=Reparatur, B=Modernisierung, C=Reset)
- User wählt → `sudo -v` einmalig
- **Output:** Entscheidung + aktives Sudo für max 15 Min

### Phase 3: Implementierung (parallel A+B mit Sudo)

**Implementierer A — Kernel-Ebene:**
```bash
# 1) Binder-Modul persistent laden
sudo tee /etc/modules-load.d/waydroid.conf >/dev/null <<'EOF'
binder_linux devices="anbox-binder,anbox-vndbinder,anbox-hwbinder"
EOF

# 2) Binder jetzt laden
sudo modprobe binder_linux devices="anbox-binder,anbox-vndbinder,anbox-hwbinder"
ls -la /dev/anbox-binder /dev/anbox-vndbinder /dev/anbox-hwbinder

# 3) ashmem-Fake (Kernel 6.17)
sudo touch /dev/ashmem
sudo chmod 0666 /dev/ashmem

# 4) Pakete (optional, empfohlen)
sudo apt install -y nvidia-modprobe vulkan-tools
```

**Implementierer B — Application-Ebene:**
```bash
# 1) Waydroid initialisieren (erzeugt container-strukturen)
sudo waydroid init 2>&1 | tail -10

# 2) host-permissions manuell anlegen (chicken-egg bypass)
sudo bash -c 'cat > /var/lib/waydroid/host-permissions/1000-wayland.xml <<EOF
<permissions>
  <socket name="wayland-0">
    <type>wayland</type>
    <enabled>true</enabled>
  </socket>
</permissions>
EOF'

# 3) NVIDIA EGL-Bridge + GPU-Mounts in LXC-Config
sudo mkdir -p /usr/share/waydroid-extras
sudo ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-egl-gbm.so.1.1.3 /usr/share/waydroid-extras/libnvidia-egl-gbm.so.1
sudo bash -c 'cat >> /var/lib/waydroid/lxc/waydroid/config_nodes <<EOF
lxc.mount.entry = /dev/dri/renderD129 dev/dri/renderD129 none bind,optional 0 0
lxc.mount.entry = /dev/dri/card2 dev/dri/card2 none bind,optional 0 0
lxc.mount.entry = /usr/share/waydroid-extras/libnvidia-egl-gbm.so.1 usr/lib/x86_64-linux-gnu/libnvidia-egl-gbm.so.1 none bind,optional 0 0
lxc.mount.entry = /usr/share/waydroid-extras/libnvidia-egl-wayland.so.1 usr/lib/x86_64-linux-gnu/libnvidia-egl-wayland.so.1 none bind,optional 0 0
lxc.cgroup.devices.allow = c 226:* rwm
lxc.cgroup.devices.allow = c 195:* rwm
lxc.cgroup.devices.allow = c 10:200 rwm
EOF'
```

### Phase 4: Validierung (read-only, kein Sudo nötig)

```bash
# Container neustarten
sudo systemctl restart waydroid-container.service
sleep 5

# Session starten (als User!)
waydroid session start &
sleep 8

# Status checken
waydroid status 2>&1
sudo systemctl is-active waydroid-container.service

# Logs auswerten — ERWARTET: KEIN "Hardware service is not even started"
# STATTDESSEN: "lxc-info … RUNNING" + Container-Hostname
sudo tail -20 /var/lib/waydroid/waydroid.log
```

**Validierungs-Checkliste:**
- [ ] `lsmod | grep binder` — binder_linux geladen
- [ ] `ls -la /dev/anbox-binder` — /dev-Node existiert
- [ ] `sudo systemctl is-active waydroid-container.service` — active
- [ ] `waydroid status` — Session running (nicht STOPPED)
- [ ] `grep "Hardware service" /var/lib/waydroid/waydroid.log` — KEINE Zeile
- [ ] `grep RUNNING /var/lib/waydroid/waydroid.log` — Container RUNNING

### Sudo-Fallback (wenn Sudo-Credentials ablaufen)

Terminal hat kein TTY → `sudo` in terminal()-Calls failt nach ~15 Min ohne `sudo -v`. **Strategie:**

1. Wenn `sudo: no password provided` erscheint → sofort Abbruch
2. User einen Copy-Paste-Block präsentieren
3. Danach: User sagt "weiter" → Validierung läuft read-only

**Copy-Paste-Block-Format (kann der User in 1x Terminal-Kopieren):**
```bash
sudo -v
# ... alle sudo Befehle nacheinander (ein langer &&-Block) ...
echo "FERTIG - Bitte poste die Ausgabe hier"
```
