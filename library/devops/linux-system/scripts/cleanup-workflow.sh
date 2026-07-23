#!/usr/bin/env bash
# cleanup-workflow.sh — Reusable system cleanup recipe
# Source-of-truth: linux-system skill, derived from sessions 2026-06-17.
#
# Run order matters: update → kernel purge → journalctl → user caches
# All steps are idempotent except the kernel purge (skip if no old kernel).

set -euo pipefail

# ---------- 0. Pre-flight ----------
if [[ $EUID -eq 0 ]]; then
  echo "ERROR: do not run as root. Use sudo inside the script." >&2
  exit 1
fi

echo "=== Pre-flight ==="
df -h / /home 2>/dev/null || df -h /
free -h
uname -r
echo

# ---------- 1. Security updates ----------
echo "=== 1. apt upgrade (security) ==="
sudo apt update -qq
sudo apt upgrade -y
echo

# ---------- 2. Old kernel purge ----------
# ⚠️  autoremove does NOT catch explicitly installed HWE kernels.
# Detect candidate (one version behind current) and purge the 4-package set.
echo "=== 2. Old kernel purge ==="
current_kernel="$(uname -r | sed 's/-generic$//')"
old_kernel="$(dpkg -l | awk '/^ii.*linux-image-[0-9]/ {print $2}' \
  | sed -E 's/^linux-image-//; s/-generic$//' \
  | grep -v "^${current_kernel}$" | head -1 || true)"

if [[ -n "${old_kernel:-}" ]]; then
  echo "Old kernel detected: $old_kernel"
  sudo apt purge -y \
    "linux-image-${old_kernel}-generic" \
    "linux-headers-${old_kernel}-generic" \
    "linux-modules-${old_kernel}-generic" \
    "linux-modules-extra-${old_kernel}-generic"
else
  echo "No old kernel found — skipping."
fi
echo

# ---------- 3. Orphaned configs ----------
echo "=== 3. rc package purge ==="
rc_count="$(dpkg -l | grep -c '^rc' || true)"
if [[ "$rc_count" -gt 0 ]]; then
  dpkg -l | awk '/^rc/ {print $2}' | xargs sudo dpkg --purge
  echo "Purged $rc_count rc packages."
else
  echo "No rc packages."
fi
echo

# ---------- 4. journalctl vacuum ----------
echo "=== 4. journalctl vacuum (7d) ==="
sudo journalctl --vacuum-time=7d
echo

# ---------- 5. User caches ----------
echo "=== 5. User caches ==="
for d in \
  "$HOME/.cache/thumbnails" \
  "$HOME/.cache/pip" \
  "$HOME/.npm/_cacache" \
  "$HOME/.cache/BraveSoftware/Brave-Browser/Default/Cache" \
  "$HOME/.cache/BraveSoftware/Brave-Browser/Default/Code Cache"; do
  if [[ -d "$d" ]]; then
    size_before="$(du -sh "$d" 2>/dev/null | awk '{print $1}')"
    rm -rf "${d:?}"/* 2>/dev/null || true
    echo "  $d: $size_before → cleaned"
  fi
done
echo

# ---------- 6. (Optional) APT cache ----------
# Uncomment to also clear /var/cache/apt/archives/*.deb
# echo "=== 6. apt clean ===" && sudo apt clean
# echo

# ---------- 7. Verify ----------
echo "=== Post-flight ==="
df -h /
dpkg -l | grep -E 'linux-(image|headers|modules)' | wc -l \
  | xargs -I{} echo "Kernel packages installed: {}"
journalctl --disk-usage

echo
echo "Cleanup complete."
