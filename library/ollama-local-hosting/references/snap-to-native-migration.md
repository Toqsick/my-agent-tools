# Snap-to-Native Migration (Model Preservation)

Migrate from a Snap-installed Ollama to a native user-space install while keeping
existing model blobs. Recommended when Snap Ollama is outdated (e.g. v0.24.0) or
broken.

## Why migrate?

- Snap version often lags behind upstream by weeks/months.
- Snap runs as root — harder to manage, conflicts with user systemd services.
- User install survives distro upgrades without snap refresh breakage.
- Models can be copied (not re-pulled) — saves bandwidth.

## Storage Locations

| Install type  | Model path                                 |
|---------------|--------------------------------------------|
| Snap          | `/var/snap/ollama/common/models/`          |
| Manual global | `/usr/share/ollama/.ollama/models/`        |
| User (~/.local) | `~/.ollama/models/`                      |

## Step-by-Step Migration

```bash
# 1. Alles stoppen
sudo snap stop ollama
sudo systemctl stop ollama 2>/dev/null
sleep 2
ps aux | grep ollama | grep -v grep  # verifizieren — sollte leer sein

# 2. Modelle finden (Snap-Speicherort ist /var/snap/, NICHT ~/.ollama/)
sudo ls -la /var/snap/ollama/common/models/blobs/ 2>/dev/null
sudo find /var/snap/ollama -name "*.gguf" -o -name "manifests" 2>/dev/null | head

# 3. Modelle migrieren (kopieren, nicht neu pullen — spart Zeit & Bandbreite)
mkdir -p ~/.ollama/models
sudo cp -r /var/snap/ollama/common/models/* ~/.ollama/models/
sudo chown -R $(id -u):$(id -g) ~/.ollama/models/
du -sh ~/.ollama/models/  # sollte ~20GB anzeigen

# 4. Snap entfernen
sudo snap remove --purge ollama

# 5. Alte globale Installation entfernen (falls vorhanden)
sudo rm -f /usr/local/bin/ollama /etc/systemd/system/ollama.service
sudo rm -rf /usr/local/lib/ollama /usr/share/ollama 2>/dev/null
```

## Install Latest Native Version (User-Space, no sudo)

```bash
# Neueste Version ermitteln
LATEST=$(curl -sL https://api.github.com/repos/ollama/ollama/releases/latest | \
  grep '"tag_name":' | sed 's/.*"v\([0-9.]*\)".*/\1/')
echo "Neueste Version: $LATEST"

# .tar.zst erfordert zstd (meist vorhanden auf Ubuntu), .tgz ist Fallback
curl -fsSL --progress-bar \
  "https://github.com/ollama/ollama/releases/download/v${LATEST}/ollama-linux-amd64.tar.zst" \
  -o /tmp/ollama-linux-amd64.tar.zst

mkdir -p ~/.local/lib/ollama ~/.local/bin
zstd -d /tmp/ollama-linux-amd64.tar.zst -o /tmp/ollama-linux-amd64.tar
tar -xf /tmp/ollama-linux-amd64.tar -C ~/.local/lib/ollama/
ln -sf ~/.local/lib/ollama/bin/ollama ~/.local/bin/ollama
~/.local/bin/ollama --version  # Verifizieren
```

## User-Systemd Service (CUDA-Optimized)

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/ollama.service << 'EOF'
[Unit]
Description=Ollama Service (User) — CUDA Optimized
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/ollama serve
Environment="HOME=%h"
Environment="PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin"
# CUDA statt Vulkan (NVIDIA GPUs)
Environment="OLLAMA_VULKAN=false"
# Flash Attention für schnellere Inferenz
Environment="OLLAMA_FLASH_ATTENTION=true"
# Max 1 Modell gleichzeitig im VRAM (8GB Karten)
Environment="OLLAMA_MAX_LOADED_MODELS=1"
# Modell 10 Minuten im VRAM halten nach letztem Request
Environment="OLLAMA_KEEP_ALIVE=10m"
# Kein Parallel-Inferenz (spart VRAM)
Environment="OLLAMA_NUM_PARALLEL=1"
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable ollama
systemctl --user start ollama
sleep 3
systemctl --user status ollama --no-pager  # verifizieren
```

## CUDA-Verifizierung

```bash
journalctl --user -u ollama --since="1 minute ago" --no-pager | grep -i "library=CUDA\|NVIDIA"
# Sollte anzeigen: library=CUDA compute=12.0 name="NVIDIA GeForce RTX ..."
```

## Key Insights

- Snap-Modelle liegen unter `/var/snap/ollama/common/models/` — NICHT `~/.ollama/models/`
- `du -sh /var/snap/ollama/` zeigt die Gesamtgröße (~20GB für 3 Modelle)
- Alte globale Installation (`/usr/local/bin/ollama`) muss auch entfernt werden
- User-Service (`systemd --user`) vermeidet sudo-Probleme
- `OLLAMA_VULKAN=false` zwingt CUDA-Nutzung auf NVIDIA GPUs
- GPU-Discovery bestätigt CUDA-Nutzung im Journal: `library=CUDA compute=12.0`

## Wenn Port 11434 belegt ist

```bash
sudo lsof -i :11434  # zeigt wer den Port blockiert
```

Oft läuft ein alter Snap-/Systemd-Prozess unerkannt im Hintergrund.