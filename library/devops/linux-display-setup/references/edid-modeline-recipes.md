# EDID Modeline Recipes

> Known-working modelines for specific monitors. Add new entries as you encounter them.

## Acer XB240H (1080p @ 144Hz)

- **Connection:** DisplayPort (DP-1-1)
- **EDID status:** Broken (0mm x 0mm, only 1024x768 detected)
- **GPU:** NVIDIA GeForce RTX 5060 Laptop

> **WICHTIG (verifiziert 2026-06-03):** Die naive CVT-Standard-Modeline
> (452.50 MHz, ~Modeline "1920x1080_cvt144") liefert beim XB240H ein
> UNSCHARFES Bild — der Monitor mag die hohe Pixelclock / das normale
> Blanking nicht. Loesung: **reduced blanking** verwenden. Damit ist
> das Bild knackscharf bei voller 144Hz.

**Working mode (reduced blanking — VERIFIZIERT scharf @ 144Hz):**
```
Modeline "1080p144"   325.08  1920 1944 1976 2056  1080 1083 1088 1098 +hsync -vsync
```

**Sicherer Fallback (1080p60 reduced blanking, falls 144Hz zickt):**
```
Modeline "1080p60_RB"  138.50  1920 1968 2000 2080  1080 1083 1088 1111 +hsync -vsync
```
(generiert mit `cvt -r 1920 1080 60`)

**Driver:** NVIDIA 595.71.05
**Autostart command (siehe ~/bin/monitor-setup.sh):**
```bash
# Fallback 60Hz RB
xrandr --newmode "1080p60_RB" 138.50 1920 1968 2000 2080 1080 1083 1088 1111 +hsync -vsync 2>/dev/null
xrandr --addmode DP-1-1 "1080p60_RB" 2>/dev/null
# Ziel 144Hz RB
xrandr --newmode "1080p144" 325.08 1920 1944 1976 2056 1080 1083 1088 1098 +hsync -vsync 2>/dev/null
xrandr --addmode DP-1-1 "1080p144" 2>/dev/null
xrandr --output DP-1-1 --mode "1080p144" --right-of eDP-1-1
```

**G-Sync status:** VRR via xrandr possible (`--set "vrr_capable" 1`).
Full G-Sync requires mode in NVIDIA MetaMode (xorg.conf).

### EDID Binary Fix (2026-06-18/2026-06-27)
Das kaputte EDID (0mm x 0mm) kann mit einem custom EDID-Binary behoben werden:
- Alte `acer-xb240h.bin` (136B) war korrekt → ersetzt durch neue 128B Version
- Neues EDID: 1080p144Hz RB + 60Hz Fallback, Range 50-144Hz
- GRUB: `drm.edid_firmware=DP-1:edid/acer-xb240h.bin` (DP-1 = phys. Port)
- Reboot ausstehend — bis dahin xrandr Autostart als Workaround

**Doku:** `~/docs/system/acer-xb240h-edid-fix-pending-2026-06-18.md`

## Template (use for new monitors)

| Field | Your value |
|-------|-----------|
| Monitor model | |
| Connection port | |
| GPU | |
| Native resolution | |
| Target refresh | |
| EDID status | working / broken / partial |
| GPU driver | |

**Compute timings:**
```bash
cvt <WIDTH> <HEIGHT> <REFRESH>
# or for reduced blanking:
cvt -r <WIDTH> <HEIGHT> <REFRESH>
```
