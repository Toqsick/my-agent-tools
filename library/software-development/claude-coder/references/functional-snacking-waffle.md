# Big overall optimization — performance, security, disk (2026-07-05)

## Context

You asked for a full sweep across the workstation. I ran three read-only audits in parallel:
`perf-tuner` (CPU/GPU/gaming), `security-auditor` (firewall/listeners/Hermes hardening), and a
manual disk-usage/yuno-cleaner pass. Below is what's actually broken vs. already fine vs. stale in
`CLAUDE.md`/prior docs, plus the exact remediation for everything I have permission to fix myself.

Good news first: **hardware health is fine** — no thermal throttling this boot, CPU governor/EPP
correct, GPU idles properly, zram swap unused, disk isn't in crisis (66% root, 200G free). The
issues below are configuration bugs and stale assumptions, not hardware problems.

---

## 1. Fixes I'll apply directly (with your go-ahead, each needs sudo)

### 1a. GameMode is completely non-functional — two independent bugs
- `/etc/gamemode.ini` `[custom] start=`/`end=` still point at the dead pre-restructure path
  `/home/bratan/bin/gamemode-{start,end}.sh` (doesn't exist). Real scripts live at
  `~/50-System/bin/gamemode-{start,end}.sh`.
- `/etc/gamemode.ini` `[gpu] gpu_device=0` doesn't match this system — NVIDIA enumerates as
  `card2`, not `card0`. Confirmed via journal: `Couldn't open vendor file at
  /sys/class/drm/card0/device/vendor`.
- Net effect confirmed live: GameMode currently delivers **zero** CPU or GPU boost on game launch.
- Fix (review `~/20-Workspace/fix-scripts/apply-gaming-fixes.sh` first — it may already encode this):
  ```bash
  sudo sed -i 's#/home/bratan/bin/gamemode-start.sh#/home/bratan/50-System/bin/gamemode-start.sh#' /etc/gamemode.ini
  sudo sed -i 's#/home/bratan/bin/gamemode-end.sh#/home/bratan/50-System/bin/gamemode-end.sh#'   /etc/gamemode.ini
  sudo sed -i 's/^gpu_device=0/gpu_device=2/' /etc/gamemode.ini
  ```
- Verify: launch `gamemoderun sleep 5 &`, check `gamemoded -s` reports active and
  `powerprofilesctl get` flips to `performance` during the run.

### 1b. Broken polkit rule for GameMode (minor, every-boot log spam)
- `journalctl` shows `polkitd: Error loading script /etc/polkit-1/rules.d/10-gamemode.rules` on
  every boot. File is root-only, couldn't inspect contents without sudo.
- Action: `sudo cat /etc/polkit-1/rules.d/10-gamemode.rules` to find the syntax error, fix in place.

### 1c. Ollama running + enabled, idling with no active use
- `systemctl is-enabled ollama` → enabled, actively running, holding a 12GB model
  (`xentriom/gemma-4-12B...:Q8_0`) resident in RAM. Two model stores on disk total ~24GB
  (`~/.ollama/models` + `/usr/share/ollama/.ollama/models`).
- This contradicts a "keep Ollama off until needed" posture and is pure idle resource cost.
- Action: `sudo systemctl stop ollama && sudo systemctl disable ollama`.
- Separate decision (not doing this without explicit confirmation): whether to delete the ~24GB
  of model weights on disk (`ollama list` first, then `ollama rm <model>` for ones you don't want
  to keep cached) — this is destructive and easy to redo (re-pull), so I'll only do it if you say so.

---

## 2. Doc correction (no system change, just fixing a wrong claim)

- `CLAUDE.md` and prior briefings state the GPU is "power-capped at 25W of a possible 115W —
  BIOS/EC limit, no software fix." **Live `nvidia-smi -q -d POWER` contradicts this**: Default
  Power Limit is **80W**, Min 5W, Max 115W. There is no 25W cap in effect, and it *is*
  software-adjustable (via `nvidia-smi -pl`) up to 115W.
- Action: update the CLAUDE.md hardware line to reflect the real 80W default / 115W max. I am
  **not** proposing to raise the power limit — that's a real thermal/stability decision, flagging
  only that the documented ceiling was wrong.

---

## 3. Disk cleanup

- `yuno-cleaner scan` found only 6.9GB of safe, easy junk: a 7GB regenerable Steam shader cache
  (`/mnt/DATA/Programme/Steam/steamapps/shadercache`) + 0.4GB of old `.deb` files in
  `/var/cache/apt/archives`. Low-risk, backup-by-default.
  - Action: `cd ~/10-Projekte/10-active/yuno-cleaner && python3 yuno_cleaner.py clean` (has
    built-in confirmation prompt + backup unless `--no-backup`).
- The real disk mass is Steam itself: **372GB across two active libraries** (Flatpak: 154G —
  Cyberpunk 2077 92G + Expedition 33/Clair Obscur 44G; `/mnt/DATA`: 218G — CS:GO 66G, Metro Redux
  duology ~17G). Root is only 66% full (200G free) so there's no urgency, but if you want to
  reclaim space this is where it is. I'm not recommending uninstalling any specific title —
  that's your call on what you're still playing. The third "stale" library path mentioned in
  CLAUDE.md (`/media/bratan/DATA/Programme/Steam`) is confirmed gone (unmounted/nonexistent) —
  nothing to do there, just update the doc note.
- If you disable Ollama (1c above) and decide to remove its model weights, that's another ~24GB.

---

## 4. Security — items I can verify but NOT fix myself

All four of these live inside `~/.hermes/`, which is agent-write-protected by design
(`CLAUDE.md`: "never modify directly... report rather than editing"). All four remain unresolved
since the 2026-07-04 remediation doc — I'll report them, you'd apply the YAML blocks already
drafted in `docs/system/security-remediation-2026-07-04.md`:

- `write_paths`/`deny_paths` still absent from `~/.hermes/config.yaml` (0 occurrences) — no
  filesystem default-deny for the agent.
- No terminal deny rules (no guard against accidental `git push`/`sudo` from the agent).
- `monthly_limit_eur` still absent — no hard provider spend cap configured.
- `~/.hermes/hermes-agent/.venv/.lock` is world-writable (`-rw-rw-rw-`) again, despite a prior fix
  — recurred, needs to be re-applied (`chmod 644` or tighter) by you inside the sandbox.

---

## 5. Security — items needing a judgment call, not a mechanical fix

- **UFW is actually fine** — confirmed active+enabled live (`/etc/ufw/ufw.conf` `ENABLED=yes`,
  systemd active/enabled). The daily audit script's "not active" result is a **false negative**
  (it runs without sudo and can't read UFW state) — worth noting the script itself is unreliable,
  not the firewall.
- **`*:9800` fluidsynth** bound on all interfaces (MIDI synth, user session service) — UFW blocks
  inbound, but no reason for it to bind `0.0.0.0` if you don't use MIDI synth software. Candidate
  to disable if unused; I won't disable a running service without your say-so.
- **`*:3000`** — `gitea.service` is showing inactive, yet something is still listening on 3000.
  Could not identify the holder without sudo. Needs `sudo ss -tlnp | grep :3000` to confirm before
  deciding anything.
- **rygel UPnP/DLNA** actively sharing Music/Videos/Pictures on the LAN (`192.168.178.92`). Works
  as designed if you use DLNA to another device; otherwise it's an avoidable LAN-facing service.
  Your call whether to keep it.
- **3 world-writable app configs** (Proton Mail, MiniMax Agent, NVIDIA Nsight Compute) — low risk
  on a single-user box, but easy to tighten: `chmod 600` each if you want it done.
- Empty-password check, NOPASSWD sudoers, and full UFW rule contents couldn't be verified without
  sudo this run — a one-off `sudo` pass would close that gap if you want full re-confirmation of
  the baseline.

---

## What I will NOT touch without further explicit confirmation

- Any file under `~/.hermes/` (report-only per CLAUDE.md).
- Steam library contents / game uninstalls (your data, your call which titles to drop).
- Raising the GPU power limit (real thermal-risk decision).
- Stopping fluidsynth, rygel, or whatever's on :3000 (need your confirmation these are actually unused).
- Deleting Ollama's cached model weights (destructive, only the service stop/disable is "safe").

## Verification after fixes land

- GameMode: `gamemoderun sleep 5 &`; check `gamemoded -s` shows active and CPU profile flips to
  `performance` then back to `balanced` on exit.
- Ollama: `systemctl is-enabled ollama` → disabled, `pgrep -a ollama` → empty.
- Disk: `df -h /` before/after `yuno_cleaner.py clean`, confirm ~6.9GB reclaimed and backup exists.
- Re-run `~/50-System/bin/maxclaw-security-audit.sh` with `sudo` afterward to fully re-confirm the
  UFW/sudoers/shadow items that couldn't be checked this pass.
