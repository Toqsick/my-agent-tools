# GreyScript Size Limits — Command / Auto-Load / Paste

> Consolidated reference for `//command:` size ceilings and when to worry.
> Verified against V0.9.6771-beta (DB dumps + cross-module verification 2026-07-03…15).

## The Hard Limit

| Threshold | Behaviour | Source |
|-----------|-----------|--------|
| **≤ 12 KB** (source bytes) | Reliable auto-load. Type `<name>` in shell → command loads. | Verified DB dumps, cross-module doc |
| **~12–20 KB** | May load, may not. Intermittent — depends on other loaded commands. | Empirical (controlcenter.src = 12.3 KB, works for some setups) |
| **>20 KB** | Auto-load failure expected. Must use CodeEditor paste + Build Button or `import_code()`. | Known from monolithic tool history |

## Key insight: It's SOURCE bytes, not built binary

The 12KB ceiling applies to the **plain-text `.src` file** — its on-disk (or in-DB) byte count.  
GreyScript counts the source length at parser registration time, not the compiled output.

## Quick-check command (any GreyScript repo)

```bash
cd <repo>
for f in tools/*.src; do
    b=$(wc -c <"$f")
    name=$(basename "$f")
    p=$((100 * b / 12288))
    if [ $b -le 8192 ]; then icon="✅"
    elif [ $b -le 12288 ]; then icon="🟡"
    else icon="🔴"; fi
    printf "%-30s %6d B  %3d%%  %s\n" "$name" "$b" "$p" "$icon"
done
```

Or from Python for richer output (hermes_tools):
```python
from pathlib import Path
for f in sorted(Path("tools").glob("*.src")):
    b = f.stat().st_size
    status = "good <8K" if b < 8192 else ("margin <12K" if b < 12288 else "OVER")
    print(f"{f.name:<36} {b:7d} B  {status}")
```

## What counts toward 12 KB

| Counts | Does NOT count |
|--------|---------------|
| Everything in the `.src` file — comments, whitespace, print strings | Nothing. Raw source bytes. |
| The `//command:` line | Not exempt — every byte. |
| Code inside `//` comments | Still source bytes. |

## Exempt: Libraries via `import_code()`

GreyScript loads `import_code()` dependencies at build time — they are **compiled into the binary**.  
No per-source size limit. `filecore.src` (20.8 KB) is fine as import target.

## Decision framework

Situation | Action
----------|-------
**Tool ≤ 8 KB** (e.g. portscan, bootstrap, localrecon, nscan) | ✅ No action. Room to grow.
**Tool ~8–12 KB** (e.g. configcore: 7.8 KB) | ✅ Still fine. Watch if adding features.
**Tool ~12–15 KB** (e.g. controlcenter: 12.3 KB) | 🟡 Edge. Either split into sub-commands or deploy via CodeEditor paste + Build (bypasses auto-load).
**Tool >15 KB** | 🔴 Must split or deploy as library+runner pattern.

## Best size-splitting pattern

Do NOT shrink by sacrificing readability or reintroducing one-line `if`/`then`/`end if` (greybelbreaker).  
Instead: **split into modular sub-commands** using `YUNO_SHARED` global state bridge:

```
yuno_core.src       (~4 KB)  — shared state + helpers
yuno_scan.src       (~5 KB)  — scan command
yuno_exploit.src    (~5 KB)  — exploit command
yuno_report.src     (~4 KB)  — report/log command
```

Each gets its own `//command:` → each stays under 12 KB → each auto-loads independently.

## Real-world sizes (greyhack-tools repo, 2026-07-15)

```
yuno_bootstrap.src              3799 B  31% ✅
yuno_localrecon.src             3206 B  26% ✅
yuno_nscan.src                  5044 B  41% ✅
portscan.src                    2264 B  18% ✅
setup.src                       3536 B  29% ✅
controlcenter.src              12560 B 102% 🔴 over soft-limit
uicore.src                      4542 B  37% ✅
configcore.src                  7956 B  65% ✅  (import target, fine)
filecore.src                   20776 B 169% 🔴  (import target, fine)
libcore.src                     2977 B  24% ✅
```

## Historical context

- yuno_v5 monolithic: ~66 KB source → UNUSABLE as single auto-load command
- yuno_v6 split: 10 × <12 KB modules → each auto-loads successfully
- Controlcenter (12.3 KB) was deliberately kept as one file for UX; deploy via CodeEditor paste + Build, not auto-load