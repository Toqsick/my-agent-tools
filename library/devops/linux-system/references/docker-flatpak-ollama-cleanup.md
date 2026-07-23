# Docker / Flatpak / Ollama Cleanup — Full Reference

Deep cleanup guide for the three biggest disk consumers on dev/gaming laptops.
Extracted from session 2026-07-03 cleanup that freed ~45 GB.

## Docker Cleanup

### Diagnosis
```bash
docker system df    # overview: images, containers, volumes, build cache
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}"
docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}"
```

### Cleanup Sequence (ORDER MATTERS)
```bash
# Step 1: Remove stopped containers FIRST
# (otherwise image prune keeps images referenced by them)
docker container prune -f

# Step 2: Remove images not used by any running container
docker image prune -a -f

# Step 3: Clear ALL build cache layers
docker builder prune -a -f

# Step 4 (optional, aggressive): remove unused volumes
docker volume prune -f
```

### Why not `docker system prune -a --volumes`?
It does everything in one shot but is too aggressive — it removes volumes that
you might want (database data, named mounts). The sequential approach gives
control at each step and lets you abort after images without losing volumes.

### Typical Reclaim (2026-07-03 session)
| Category | Reclaimed |
|----------|-----------|
| Build cache (66 layers) | 15.14 GB |
| Unused images (8 removed) | 14.32 GB |
| Stopped containers (8 removed) | 31 MB |
| **Total Docker** | **~29.5 GB** |

---

## Flatpak Cleanup

### Architecture
Flatpak stores data in two places:
- **System runtimes/apps:** `/var/lib/flatpak/` (37 GB observed — multiple Platform/SDK versions, GL drivers)
- **Per-app user data:** `~/.var/app/<app-id>/` (211 GB observed — Steam games, GNOME Boxes VMs, etc.)

### Safe Runtime Cleanup
```bash
# Remove runtimes no app references
flatpak uninstall --unused --noninteractive
```

### What accumulates
| Item | Size each | How many? |
|------|-----------|-----------|
| `org.gnome.Platform` versions | ~1.1 GB | 3–5 versions |
| `org.kde.Platform` versions | ~1.0 GB | 3–4 versions |
| `org.freedesktop.Platform` versions | ~650 MB | 3 versions |
| `org.freedesktop.Platform.GL.default` | 450–540 MB | 6+ (multiple branches) |
| `org.freedesktop.Platform.GL.nvidia-*` | ~820 MB | 1 per driver version |
| `org.freedesktop.Sdk` | ~1.7 GB | if installed |
| `org.gnome.Sdk` | ~2.3 GB | if installed |

### Pinned Runtimes (won't auto-remove)
GTK theme packages (`org.gtk.Gtk3theme.Zorin*`) are pinned by default.
To remove them: `flatpak pin --remove <runtime>` first, then `flatpak uninstall --unused`.

### ⚠️ ~/.var/app/ is NOT cache
This directory holds real application data:
- `com.valvesoftware.Steam` → 155 GB of installed games
- `org.gnome.Boxes` → 34 GB of VM disk images
- `com.usebottles.bottles` → 9.4 GB of Wine prefixes

**Never bulk-delete `~/.var/app/`.** Only delete if user confirms for a specific app.

### Inspecting ~/.var/app/
```bash
du -h ~/.var/app/ --max-depth=1 | sort -rh | head -15
```

---

## Ollama Model Cleanup

### Dual-Location Problem
Ollama can store models in two locations simultaneously:
- **User-level:** `~/.ollama/models/` (owned by user)
- **System-level:** `/usr/share/ollama/.ollama/models/` (owned by `ollama` user)

The systemd service `ollama.service` determines which is active via `OLLAMA_MODELS`
env var or `Home=` directive. But models pulled by different methods can end up
in both locations, wasting 10–25 GB on duplicates.

### Diagnosis
```bash
# Check both locations
du -sh ~/.ollama/models/
du -sh /usr/share/ollama/.ollama/models/

# Check which models exist where
ollama list                              # shows active location
find ~/.ollama/models/manifests -type f  # user-level manifests
sudo find /usr/share/ollama/.ollama/models/manifests -type f  # system-level

# Check systemd config for OLLAMA_MODELS
systemctl cat ollama | grep -i models
```

### Cleanup
```bash
# Remove a specific model
ollama rm <model-name>

# If the model is in the wrong location (not the active OLLAMA_MODELS dir),
# ollama rm won't find it. Manual cleanup:
rm -rf ~/.ollama/models/blobs/sha256-<hash>
# Or for system-level:
sudo rm -rf /usr/share/ollama/.ollama/models/blobs/sha256-<hash>
# Then remove the manifest:
rm ~/.ollama/models/manifests/<path-to-manifest>
```

---

## Session-Validated Cleanup Order

Best-practice sequence for a comprehensive cleanup session:

1. **Diagnose** — `df -h /`, `docker system df`, `du -sh ~/.cache/ ~/.var/app/`
2. **Docker** — containers prune → image prune → builder prune (biggest win: 20–30 GB)
3. **User caches** — `uv cache clean`, `rm ~/.cache/huggingface/hub/*`, `rm ~/.cache/deja-dup/*`
4. **Flatpak runtimes** — `flatpak uninstall --unused`
5. **Journal** — `sudo journalctl --vacuum-size=200M`
6. **Snap revisions** — `sudo snap remove <name> --revision=<old>`
7. **APT rc packages** — `dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge`
8. **Verify** — `df -h /` compare before/after
9. **Report** — present structured Vorher/Nachher table to user
10. **User decisions** — flag large user-data items (Steam, VMs, Ollama models) for manual review

### Journal Permanent Limit
After vacuuming, make the limit permanent:
```bash
# /etc/systemd/journald.conf
SystemMaxUse=200M
# Then restart journal
sudo systemctl restart systemd-journald
```

---

## Pitfalls

1. **Docker `image prune -a` without container prune first** → images stay because
   stopped containers still reference them. Always: containers first, images second.
2. **Flatpak `--unused` misses pinned themes** → manually unpin or accept they stay.
3. **Ollama models in dual locations** → `ollama list` only shows the active dir.
   Always `du` both paths.
4. **`~/.var/app/` looks like cache** → it's not. Steam games and VMs live there.
5. **Snap removal needs sudo** → `snap remove --revision=N` fails without root.
   `sudo` with askpass in non-TTY needs `-S` flag or heredoc password pipe.
