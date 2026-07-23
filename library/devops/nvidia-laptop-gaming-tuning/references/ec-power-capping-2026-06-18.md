# Laptop EC Power Capping — RTX 5060 Laptop (2026-06-18)

## Symptom
`sudo nvidia-smi -pl 115` → "Changing power management limit is not supported in current scope for GPU: 00000000:01:00.0."

## Diagnosis
```bash
nvidia-smi -q -d POWER
# Shows: "SW Power Cap: Active", "SW Power Capping: <timestamp> us"
# Current Power Limit: 25.00 W (despite Default: 80W, Max: 115W)
```

The laptop's Embedded Controller (EC) enforces a power cap via the `SW Power Capping` mechanism. The NVIDIA driver reports the cap but cannot override it — the EC has ultimate authority over the power budget.

## Why it happens
Modern laptops with strict thermal/VRM/battery budgets use the EC to dynamically adjust GPU power limits. The 25W cap (vs 80W default / 115W max) suggests the EC is in a conservative mode, possibly due to:
- Thermal headroom (shared CPU/GPU cooling)
- Battery conservation
- AC adapter wattage detection
- BIOS power profile

## What does NOT work
- `nvidia-smi -pl <value>` — blocked by EC
- `nvidia-smi -ac <mem>,<gpu>` — deprecated in driver 595 ("The requested functionality has been deprecated")
- Direct register writes — risk of hardware damage or EC lockout
## What MIGHT work

1. **X11 + Coolbits 28** — NV-CONTROL may expose a Power Limit slider that can override EC (not guaranteed)
2. **BIOS settings** — some laptops have a "Performance" or "Turbo" mode that raises EC limits
3. **AC adapter** — ensure the original high-wattage charger is connected (some laptops limit GPU power on lower-wattage USB-C PD chargers)
4. **OS performance mode** — on this system, switching the power profile to "Leistungsmodus" (performance) via the GNOME power settings released the EC cap from 25W to 80W (Default). This is the easiest first step before trying Coolbits.
5. **Accept the cap** — 25W is sufficient for 1080p gaming and non-GPU workloads

## Do NOT attempt
- Direct EC register writes via `devmem` or `iotools`
- Kernel module patches to bypass power capping
- These can cause system instability, battery issues, or permanent EC state corruption

## Related
- `nvidia-laptop-gaming-tuning` SKILL.md pitfall #12
- `linux-system/references/nvidia-driver-troubleshooting.md` PITFALL 7
