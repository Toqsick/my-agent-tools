---
name: host-security-audit
description: |
  Use when auditing Linux host security at the hardware and firmware layer, checking boot-chain protections, or documenting baseline hardening gaps.
  NOT for application code review, incident-response containment, or applying disruptive firmware and boot changes without explicit approval.
  Provides a structured host security assessment covering hardware trust, firmware posture, and evidence-backed hardening recommendations.
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - linux
    - security
    - fwupd
    - hsi
    - tpm
    - secure-boot
    - power-management
    - kernel-taint
    - acpi
    related_skills:
    - system-security-audit
    - linux-display-setup
    - nvidia-laptop-gaming-tuning
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['firmware', 'host', 'security', 'hardware', 'boot']
keywords: ['firmware', 'host', 'security', 'hardware', 'boot']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['claude-security-auditor', 'system-security-audit', 'security-audit']
---


# Host Security Audit (Hardware + Firmware Layer)

**Complement to `system-security-audit` (which is software-layer: ports, services, permissions, firewall).** This skill covers the *hardware + firmware* layer: secure boot chain, TPM, ME, BootGuard, kernel taint, ACPI BIOS bugs, and power management.

## When to load

- User attaches a `Device Security Report.txt` (fwupd output) and asks for analysis or fixes
- User mentions HSI-1 / HSI-2 / HSI-3 / HSI-4 levels
- User says "host security", "laptop security", "firmware security", "kernel is tainted", "BIOS update"
- User wants to fix a specific HSI failure: `Suspend To Idle`, `Encrypted RAM`, `Linux Kernel Verification`
- User asks "why is my Linux Kernel Verification verdorben" / "stale_hw taint"
- User reports lid-switch / suspend not working, especially with external monitor attached

## The 5-Phase Workflow

Always run phases in order. Phase 0 (live verify) before Phase 1 (categorize) — never trust the report alone.

### Phase 0: Live verification (NEVER skip)

`fwupd` reports are point-in-time. Verify each claim against the live system, especially for items that look like runtime checks.

```bash

set -euo pipefail
# Current HSI level
fwupdmgr security 2>&1 | head -30

# Kernel + taint bits
uname -r
cat /proc/sys/kernel/tainted
# Decode with: t=int(open("/proc/sys/kernel/tainted").read().strip()); [print(f"  bit {i}: {name}") for i, name in enumerate(["PROPRIETARY_MODULE","OUT_OF_SPEC_MODULE","UNSIGNED_MODULE","SOFT_LOCKUP","HARD_LOCKUP","UNSIGNED_HW","RESERVED","LIVEPATCH","A_C_SUBSYSTEM","MODULE_FORCE_LOAD","UEVENT_LATE","CPUID_OUT_OF_SPEC","STALE_HW","STALE_SOFTWARE"]) if t & (1 << i)]

# Secure Boot + MOK
mokutil --sb-state
mokutil --list-enrolled

# TPM
ls /sys/class/tpm/tpm* 2>/dev/null
for p in 0 1 2 3 4 7; do cat /sys/class/tpm/tpm0/pcr-sha256/$p 2>/dev/null; done

# Lockdown
cat /sys/kernel/security/lockdown

# Power
cat /sys/power/mem_sleep    # expect [s2idle] or [s2idle] deep
cat /proc/cmdline | tr ' ' '\n' | grep -i mem_sleep

# Available firmware updates
fwupdmgr get-updates 2>&1 | head -20
```

**Pitfall A: Subagent / report claims about "ERROR flutet log" or "X% failed" without date context.** Filter by date before treating as active bug:
```bash

set -euo pipefail
grep ERROR log | awk '{print $1}' | sort -u | tail -10   # dates
# If empty for last 7 days → historical, ignore
```

### Phase 1: Categorize by HSI level + Pitfall class

| Level | Meaning | Common items |
|-------|---------|--------------|
| HSI-1 | UEFI Secure Boot, TPM 2.0, ME locked, firmware locked | UEFI Platform Key, Boot Services Vars, MEI, FW Write Protect |
| HSI-2 | Intel BootGuard, IOMMU, TPM Reconstruction | BootGuard Fuse/Verified/ACM, IOMMU, Platform Debugging locked |
| HSI-3 | Suspend, DMA Protection, CET | Suspend To Idle, Pre-boot DMA, Control-flow Enforcement |
| HSI-4 | Maximum (server-class) | Encrypted RAM (TME/MKTME), Supervisor Mode Access Prevention |

**Categorization rubric:**
- **P0 (security risk, fix now):** Any ! Fail that's exploitable. Examples: Secure Boot off, ME not locked, kernel lockdown off, unsigned module.
- **P1 (HSI score, fix in <30 min):** Configuration-only fixes. Suspend, IOMMU-not-strict-mode, missing update checks.
- **P2 (HW limit, document and accept):** Encrypted RAM on consumer CPU, missing BootGuard on AMD, TME unavailable.
- **P3 (firmware bug, wait for vendor):** ACPI BIOS bugs, kernel verification corrupted from stale HW, EDID firmware invalid.

**Most HSI-3/4 fails are P1 or P2/P3 — not P0.** The user's "is this safe?" worry usually resolves to "yes, you just don't have server-class features".

### Phase 2: Apply fixes (in dependency order)

For each fix:

1. **Backup if destructive:** Configs → drop-in files (non-destructive), kernel params → GRUB (recoverable), BIOS → vendor tool.
2. **Apply via the right interface:** systemd configs → `/etc/systemd/<unit>.d/*.conf`, GNOME → `gsettings`, GRUB → `/etc/default/grub` + `update-grub`.
3. **Verify active config:** `systemd-analyze cat-config systemd/<unit>` — this shows the *effective* merged config, not just what you wrote.
4. **daemon-reload only when needed:** systemd config changes need `sudo systemctl daemon-reload`; GNOME gsettings take effect on next gsd-power signal.

**Critical:** Always check `/sys/power/mem_sleep` AND systemd config — both matter. Kernel `mem_sleep_default=s2idle` in cmdline AND systemd `SuspendState=mem` in sleep.conf.

### Phase 3: Verify (live, not by report)

After applying fixes, trigger the actual event the metric measures (don't just claim "config is set"):

| HSI item | Verification trigger |
|----------|---------------------|
| Suspend To Idle | `systemctl suspend` OR lid-zuklappen, then `fwupdmgr get-history | grep suspend` |
| Linux Kernel Verification | Reboot, then check taint — if BIOS bug, taint returns |
| Encrypted RAM | Check CPU model + Intel ARK — consumer CPUs never support TME |
| Pre-boot DMA | `dmesg | grep -i intel_iommu` after reboot |

### Phase 4: Document

Write findings to `~/docs/system/host-security-audit-YYYY-MM-DD.md` with sections:
- Live state (HSI level, kernel taint bits, Secure Boot, TPM PCRs)
- Findings table (P0/P1/P2/P3 + status)
- Fixes applied (commands, file diffs, before/after)
- Limits (HW/firmware) + accept rationale
- Pitfalls hit during the audit (see references/)

## Linux Power Management: the gnarly sub-skill

The `Suspend To Idle` (HSI-3) check fails for THREE independent reasons, all of which need to be addressed:

1. **Kernel not configured for s2idle:** `cat /sys/power/mem_sleep` should show `[s2idle]`. Kernel cmdline `mem_sleep_default=s2idle` ensures it's the default.
2. **systemd not configured to use it:** `/etc/systemd/sleep.conf.d/s2idle.conf` with `SuspendState=mem`.
3. **logind not configured to actually suspend on lid close:** `/etc/systemd/logind.conf.d/s2idle.conf` with `HandleLidSwitch=suspend`.
4. **GNOME not blocking it via gsettings:** `gsettings set org.gnome.settings-daemon.plugins.power lid-close-suspend-with-external-monitor true` — critical when an external monitor is connected.

**After all four configs:** Suspend should work. But GNOME's `gsd-power` **caches the gsettings value at startup** and only refreshes on monitor attach/detach events. If you change `lid-close-suspend-with-external-monitor` while gsd-power is running, the lid-switch inhibitor persists.

**Workaround for the GNOME cache bug** (discovered 2026-06-08):
```bash

set -euo pipefail
# SIGUSR1 makes gsd-power re-read its gsettings
kill -USR1 $(pgrep gsd-power)

# Verify
systemd-inhibit --list 2>&1 | grep -E 'handle-lid-switch|gsd-power' | head -3
# Expected: empty (inhibitor cleared)
```

If SIGUSR1 doesn't work: kill `gsd-power` (it respawns via `gnome-session-binary`, sometimes needs `start_new_session=True` in manual respawn).

**gnome-session-binary** also holds a `block` inhibitor on `sleep` mode with reason "user session inhibited". This blocks `systemctl suspend` directly. SIGUSR1 trick on gsd-power usually clears this too.

**Triggering the test without exposing yourself to gnome-session-b inhibitor:**
- Lid zuklappen: blocks via gsd-power's `handle-lid-switch` inhibitor
- `systemctl suspend`: blocks via gnome-session-b's `sleep` inhibitor
- Both clear with SIGUSR1 → gsd-power

## Kernel taint triage

`/proc/sys/kernel/tainted` returns an integer (decimal). Decode:

| Bit | Name | Common cause | Action |
|-----|------|--------------|--------|
| 0 | PROPRIETARY_MODULE | NVIDIA out-of-tree, ZFS, VirtualBox | Accept (or `modprobe.blacklist` if not needed) |
| 2 | UNSIGNED_MODULE | DKMS modules, custom kernel builds | Sign with MOK or remove |
| 12 | STALE_HW | ACPI BIOS errors, firmware-DMI mismatch | BIOS update (often unavailable) |
| 4096 (12) | combined | Usually stale HW + proprietary modules | Inspect `dmesg | grep -iE 'stale|taint|ACPI'` |

**ACPI BIOS errors are the most common cause of `stale_hw`.** Pattern:
```

set -euo pipefail
ACPI BIOS Error (bug): Could not resolve symbol [\_SB.PC00.MHBR], AE_NOT_FOUND
ACPI Error: Aborting method \_SB.PC00.CNVW.IFUN due to previous error
```

If `fwupdmgr get-updates` reports no BIOS update available: it's a vendor-firmware bug, not your fault. Document and accept. The `stale_hw` bit is informational, not a security vulnerability.

## Common subagent-fabricated findings to watch for

When delegating a host security audit to a subagent, expect these to come back as "critical" but actually be non-issues:

1. **"OpenRouter payment warnings flood the log"** — usually `auxiliary_client` skipping OpenRouter when no credits, not a host issue.
2. **"Telegram home channel invalid literal int '@BotName'"** — historical bug, fixed in later updates. Filter by date.
3. **"Permission X is 711, should be 700"** — `711` (`rwx--x--x`) is intentional for cron-executed scripts. Owner still has full rwx; group/other have only execute (--x) for inheritance.
4. **"Snapshot directory is 775"** — yes, but `state.db` and `manifest.json` are 600 after fix. Directory needs `+x` for traversal; if all files are 600 the contents are safe.

Verify before reporting as a finding.

## Output template (Doku)

```markdown
# Host Security Audit — YYYY-MM-DD

**Host:** [model], [CPU], [distro], [NVIDIA driver]
**fwupd version:** [from report]
**HSI live:** [HSI:N] — [HSI-1+2: pass, HSI-3+4: partial]
**Source:** [path to Device Security Report or "live scan"]

## Live State
- Secure Boot: [enabled|disabled], MOK: [list keys]
- Kernel: [version], Taint bits: [decoded]
- TPM: [v2.0, PCR0-7: hashes]
- Lockdown: [integrity|confidentiality|none]
- Power: [mem_sleep options], [cmdline has mem_sleep_default]

## Findings
| P | Item | Status | Resolution |
|---|------|--------|------------|
| P0 | ... | fixed | command |
| P1 | Suspend To Idle (HSI-3) | fixed | drop-in files + SIGUSR1 |
| P2 | Encrypted RAM (HSI-4) | accepted | i7-13620H non-vPro, TME unavailable |
| P3 | Linux Kernel Verification | accepted | ACPI BIOS bug, no update available |

## Fixes Applied
[List each: file, setting, before → after, verification command, expected result]

## Limits (HW/FW)
- [CPU model, BIOS version, vendor update policy]

## Pitfalls Hit
- [e.g. "GNOME gsd-power caches gsettings at startup; SIGUSR1 needed to refresh"]
```

set -euo pipefail
## References

- `references/fwupd-hsi-levels.md` — what each HSI level measures, threshold definitions, common HSI-3/4 fail patterns and fixes
- `references/linux-power-management.md` — s2idle vs deep, suspend inhibitors, GNOME gsd-power, the SIGUSR1 workaround, drop-in templates
- `references/kernel-taint-decoder.md` — all 14 TAINT_* bits, what causes them, when to care, dmesg patterns for ACPI BIOS bugs
- `references/secure-boot-tpm-playbook.md` — MOK enroll, PCR baseline, tpm2-tss setup, systemd-cryptenroll for LUKS+TPM
- `templates/s2idle-drop-in.conf` — ready-to-copy drop-in files for `/etc/systemd/logind.conf.d/s2idle.conf` and `/etc/systemd/sleep.conf.d/s2idle.conf`

## Verification workflow after applying fixes

```bash
# 1. systemd configs are active
systemd-analyze cat-config systemd/logind.conf | grep HandleLidSwitch
systemd-analyze cat-config systemd/sleep.conf | grep SuspendState

# 2. GNOME gsettings
gsettings get org.gnome.settings-daemon.plugins.power lid-close-suspend-with-external-monitor
# Expect: true
gsettings get org.gnome.settings-daemon.plugins.power lid-close-ac-action
# Expect: 'suspend'

# 3. Refresh gsd-power cache (the magic step)
kill -USR1 $(pgrep gsd-power)
sleep 1
systemd-inhibit --list 2>&1 | grep -E 'gsd-power|handle-lid-switch' | head -3
# Expect: empty (no inhibitors)

# 4. Trigger the actual suspend (you do this, not the agent)
systemctl suspend  # or lid zuklappen

# 5. Verify HSI improved
fwupdmgr get-history 2>&1 | grep -i suspend
# Expect: 'Suspend To Idle: Nicht eingeschaltet → Bestanden'
fwupdmgr security 2>&1 | head -30
# Expect: HSI:3 (up from HSI:2)
```
