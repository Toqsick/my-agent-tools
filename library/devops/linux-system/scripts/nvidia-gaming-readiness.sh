#!/usr/bin/env bash
# nvidia-gaming-readiness.sh — comprehensive Optimus + NVIDIA gaming readiness probe.
# Read-only. No sudo. No installs. Designed for: "Games used to work, now they don't".
#
# Output color: green = OK, yellow = suspect, red = blocking issue.
# Exit code: 0 = all critical checks pass, 1 = at least one red.

set -u

# Colors only if stdout is a tty.
if [ -t 1 ]; then
  R=$'\e[31m'; Y=$'\e[33m'; G=$'\e[32m'; N=$'\e[0m'
else
  R=''; Y=''; G=''; N=''
fi

red()   { printf '%s[RED]%s    %s\n'    "$R" "$N" "$*"; }
yellow(){ printf '%s[YELLOW]%s %s\n'    "$Y" "$N" "$*"; }
green() { printf '%s[GREEN]%s  %s\n'    "$G" "$N" "$*"; }
head()  { printf '\n=== %s ===\n' "$*"; }

# ---------------------------------------------------------------- 0. preflight
head "0. Preflight"
KERNEL=$(uname -r)
echo "Kernel: $KERNEL"

# ---------------------------------------------------------------- 1. driver
head "1. NVIDIA driver + module"
if command -v nvidia-smi >/dev/null 2>&1; then
  DRIVER_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1)
  if [ -n "$DRIVER_VER" ]; then
    green "nvidia-smi OK — driver $DRIVER_VER"
    nvidia-smi --query-gpu=name,power.draw,power.limit,temperature.gpu --format=csv,noheader \
      | awk -F', ' '{printf "       GPU=%s | power=%s | limit=%s | temp=%s\n",$1,$2,$3,$4}'
  else
    red "nvidia-smi present but queries fail (driver broken or unloaded)"
  fi
else
  red "nvidia-smi not installed"
fi

if lsmod | grep -q '^nvidia '; then
  green "Kernel module nvidia loaded"
  MODPATH=$(modinfo nvidia 2>/dev/null | awk -F': ' '/^filename/ {print $2}')
  echo "       module: $MODPATH"
else
  red "nvidia kernel module not loaded"
fi

# ---------------------------------------------------------------- 2. OpenGL/Vulkan stack
head "2. OpenGL + Vulkan stack availability"
if command -v glxinfo >/dev/null 2>&1; then
  GL_RENDERER=$(glxinfo -B 2>/dev/null | awk -F': ' '/OpenGL renderer string/ {print $2}')
  GL_VENDOR=$(glxinfo -B 2>/dev/null | awk -F': ' '/OpenGL vendor string/   {print $2}')
  if [ "${GL_RENDERER#*NVIDIA*}" != "$GL_RENDERER" ]; then
    green "glxinfo confirms NVIDIA renderer: $GL_RENDERER"
  else
    yellow "glxinfo renders with: $GL_RENDERER ($GL_VENDOR)  — iGPU only or libre driver"
  fi
else
  yellow "glxinfo missing — apt install mesa-utils (root only)"
fi

if [ -f /usr/share/vulkan/icd.d/nvidia_icd.json ]; then
  green "Vulkan NVIDIA ICD present ($(cat /usr/share/vulkan/icd.d/nvidia_icd.json | grep library_path | awk -F'"' '{print $4}'))"
else
  red "Vulkan NVIDIA ICD missing at /usr/share/vulkan/icd.d/nvidia_icd.json"
fi

if command -v vulkaninfo >/dev/null 2>&1; then
  VULKAN_OUT=$(vulkaninfo --summary 2>/dev/null | grep -E 'GPU id|driverName|apiVersion')
  if [ -n "$VULKAN_OUT" ]; then
    green "vulkaninfo OK:"; echo "$VULKAN_OUT" | sed 's/^/       /'
  else
    yellow "vulkaninfo present but lists zero devices"
  fi
else
  echo "       vulkaninfo not installed (info only — Vulkan still works if ICD present)"
fi

# ---------------------------------------------------------------- 3. Optimus / Prime runtime
head "3. Optimus / Prime runtime env"
PRIME_ENV=$(env | grep -E '^(__NV_PRIME_RENDER_OFFLOAD|__GLX_VENDOR_LIBRARY_NAME|__GL_PRIME_RENDER_OFFLOAD|DRI_PRIME|VK_ICD_FILENAMES)=')
if [ -z "$PRIME_ENV" ]; then
  green "Clean Prime env (no __NV_/__GLX_/DRI_PRIME set globally)"
else
  yellow "Prime-related env vars set (may force global NVIDIA routing):"
  echo "$PRIME_ENV" | sed 's/^/       /'
fi

# ---------------------------------------------------------------- 3a. Prime env provenance
head "3a. Prime env provenance"
for f in ~/.bashrc ~/.profile ~/.zshrc \
         ~/.config/environment.d/*.conf \
         /etc/environment; do
  [ -f "$f" ] || continue
  if grep -qE '__NV_PRIME|__GLX_VENDOR|prime-run' "$f" 2>/dev/null; then
    yellow "Prime vars present in: $f"
    grep -nE '__NV_PRIME|__GLX_VENDOR|prime-run' "$f" 2>/dev/null | sed 's/^/          /'
  fi
done

# System-launcher probe (read-only, no sudo): if env vars set but no user-dotle found,
# the source is usually the Wayland session (gnome-session-binary forks into all kids).
if [ -n "$PRIME_ENV" ]; then
  echo "       Tracing prime vars across all PIDs (source = oldest process still carrying them)…"
  SOURCE_PIDS=$(for p in $(ls /proc | grep -E '^[0-9]+$' | sort -n); do
    if grep -q "__NV_PRIME_RENDER_OFFLOAD" /proc/$p/environ 2>/dev/null; then
      printf 'PID=%-7s CMD=%s\n' "$p" "$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | head -c 80)"
    fi
  done | head -10)
  if [ -n "$SOURCE_PIDS" ]; then
    echo "$SOURCE_PIDS" | sed 's/^/          /'
    yellow "Likely source: a system launcher. Fix with per-user override (PITFALL 9 / fix section)."
  fi
fi

# prime-run presence
if command -v prime-run >/dev/null 2>&1; then
  green "prime-run exists at $(command -v prime-run)"
else
  yellow "prime-run not in PATH — package may be missing or wrapper not generated"
  if dpkg -l nvidia-prime 2>/dev/null | grep -q '^ii'; then
    echo "       nvidia-prime IS installed — wrapper may need regenerating"
  else
    red "nvidia-prime package MISSING"
  fi
fi

# ---------------------------------------------------------------- 4. EC + power profile
head "4. Power / EC constraints"
if command -v powerprofilesctl >/dev/null 2>&1; then
  ACTIVE=$(powerprofilesctl get 2>/dev/null)
  echo "       powerprofiles daemon active: $(powerprofilesctl list 2>/dev/null | grep -E '^\*' | head -1)"
  if [ "$ACTIVE" = "performance" ]; then
    green "powerprofilesctl = performance"
  else
    yellow "powerprofilesctl = '${ACTIVE:-none}' (consider 'performance' for gaming)"
  fi
else
  echo "       powerprofilesctl not installed"
fi

if command -v tuned-adm >/dev/null 2>&1; then
  TUNED=$(tuned-adm active 2>&1)
  echo "       tuned: $TUNED"
fi

if command -v sensors >/dev/null 2>&1; then
  GPU_TEMP=$(sensors 2>/dev/null | grep -i 'edge\|gpu\|temp1' | grep -oE '\+[0-9.]*°C' | head -1)
  echo "       Sensors: $GPU_TEMP"
else
  echo "       lm-sensors not installed"
fi

EC_CAP_RAW=$(nvidia-smi --query-gpu=power.limit --format=csv,noheader 2>/dev/null | head -1)
if [ "$EC_CAP_RAW" = "[N/A]" ] || [ -z "$EC_CAP_RAW" ]; then
  yellow "GPU power.limit = N/A — likely EC-capped (cannot raise via nvidia-smi -pl)"
else
  echo "       power.limit = $EC_CAP_RAW"
fi

# ---------------------------------------------------------------- 5. Steam launcher sanity (optional)
head "5. Steam (only if installed)"
STEAM_HOME="${STEAM_HOME:-$HOME/.steam}"
STEAM_FLAT="$HOME/.var/app/com.valvesoftware.Steam"
if [ -d "$STEAM_HOME/steam" ] || [ -d "$STEAM_FLAT" ]; then
  if pgrep -x steam >/dev/null; then
    green "Steam process running"
  else
    echo "       Steam installed but not running"
  fi
  # Check shader cache bucket for stale GPU hash
  if [ -f "$STEAM_HOME/steam/config/config.vdf" ]; then
    HASH=$(grep -oE 'CurrentBucketGPU[^\\"]*\"[a-f0-9]+' "$STEAM_HOME/steam/config/config.vdf" 2>/dev/null \
           | awk -F'"' '{print $2}')
    if [ -n "$HASH" ]; then
      echo "       shader bucket GPU hash: ${HASH:0:24}…"
    fi
  fi
  # Flatpak Steam: check for empty staging folders (interrupted installs)
  if [ -d "$STEAM_FLAT" ]; then
    LF=$(find "$STEAM_FLAT" -name "libraryfolders.vdf" 2>/dev/null | head -1)
    if [ -n "$LF" ]; then
      grep -oP '"path"\s*"[^"]*"' "$LF" 2>/dev/null | awk -F'"' '{print $4}' | while read -r libpath; do
        [ -d "$libpath/steamapps" ] || continue
        find "$libpath/steamapps" -maxdepth 1 -mindepth 1 -type d -empty 2>/dev/null | while read -r emptyd; do
          yellow "       EMPTY: $emptyd — interrupted install, reinstall via Steam"
        done
      done
    fi
  fi
else
  echo "       Steam not installed"
fi

echo
echo "=== Done. Reds = blocking. Yellows = investigate. Greens = nominal. ==="
