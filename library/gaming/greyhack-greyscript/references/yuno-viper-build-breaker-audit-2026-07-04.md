# Yuno Viper Build-Breaker Audit (2026-07-04)

## Scope

- **Project:** Yuno Viper v1, modules directory `/home/bratan/greyhack-tools/yuno_viper/modules/`
- **Files scanned:** 5 (3008 lines total)
  - `yuno_viper_core.src` (411 lines) — clean ✅
  - `yuno_viper_net.src` (553 lines) — 81 findings 🔴
  - `yuno_viper_post.src` (666 lines) — clean ✅
  - `yuno_viper_scan.src` (718 lines) — 55 findings 🔴
  - `yuno_viper_util.src` (660 lines) — 6 findings 🔴

## Patterns & Results

| # | Pattern | Regex | Total | Severity |
|---|---------|-------|-------|----------|
| (a) | Einzeilige `if X then Y end if` | `\bif\b.*\bthen\b.*\bend\s+if\b` | **142** | 🔴 Critical |
| (b) | Ternary `X if cond else Y` | — | **0** | ✅ OK |
| (c) | `\n` statt `char(10)` | `\\n` | **0** | ✅ OK (korrekt genutzt) |
| (d) | Single-quotes `'text'` | `'[^']*'` | **21** (alle in print()) | ✅ OK (keine Code-Strings) |
| (e) | Inline-if assignment `X = (Y if C else Z)` | — | **0** | ✅ OK |

## Pattern (a) — Detail

### `yuno_viper_net.src` (81 Zeilen)

**Pure one-line-if (79 Zeilen):**
- `if v == null then v = "[null]" end if` (Z. 30, 31)
- `if sh == null then return {"router": null, "error": "..."} end if` (Z. 54, 62)
- Guard pattern: `if target == null or target == "" then return {...} end if` (Z. 70, 109, 174, 348)
- Error return: `if safe["error"] != null then return {...} end if` (Z. 72, 111, 180, 351, 396)
- Default init: `if records.len > YVN_NS_MAX then records = records[:YVN_NS_MAX] end if` (Z. 97)
- PortSniffer bounds: `if sec < 1 then sec = 1 end if` (Z. 137, 138, 176, 177, 392, 393)
- Break-on-ok: `if ok then break end if` (Z. 152)
- Stop-sniffer: `if typeof(sn).hasIndex("stop_sniffer") then sn.stop_sniffer end if` (Z. 167)
- Botnet guards: `if not globals.hasIndex("_yvn_botnet") then ... end if` (Z. 280, 285)
- Chat: `if lib == null then lib = include_lib(...) end if` (Z. 244)
- Port-map copy: `if p.hasIndex("port_number") then num = p["port_number"] end if` (Z. 375)
- Depth guards: `if depth == null then depth = 1 end if` (Z. 391)
- CLI flags: `if args.len >= 3 then port = args[2].val end if` (Z. 485, 486, 498, 503, 526, 530, 549)

**Statement-chain one-line-if (2 Zeilen):**
- Z. 216: `nodes = topo["nodes"]; if typeof(nodes) != "list" then nodes = [] end if`
- Z. 217: `edges = topo["edges"]; if typeof(edges) != "list" then edges = [] end if`

### `yuno_viper_scan.src` (55 Zeilen)

**Pure one-line-if (47 Zeilen) — heavy use of validation guards:**
- `if sub == "" or sub == "help" then exit end if` (Z. 30)
- `if not validIP(ip) then fail("Ungueltige IP") end if` (Z. 56, 123, 186, 276, 365, 420, 521, 614, 650)
- `if not router then fail("Router offline") end if` (Z. 62, 194, 285, 370, 526, 619)
- `if not meta then fail("metaxploit.so nicht verfuegbar") end if` (Z. 131, 214, 451, 539, 663)
- `if not addrs or addrs.len == 0 then warn(...) end if` (Z. 155* — statement chain)
- `if not net then warn("Skip ..."); continue end if` (Z. 228* — statement chain)
- `if openPorts.len == 0 then warn("Kein Ziel"); exit end if` (Z. 534* — statement chain)
- Bounds: `if n < 0 then n = 0 end if` / `if n > 60 then n = 60 end if` (Z. 697, 698)

**Statement-chain one-line-if (8 Zeilen):**
- Z. 155, 196, 228, 295, 374, 528, 534, 564 — alle haben `warn(...); exit` oder `warn(...); continue` nach dem `then`

### `yuno_viper_util.src` (6 Zeilen)

**Statement-chain one-line-if (3):**
- Z. 242, 389, 569: `if file then tmp = file.get_content; if typeof(tmp) == I.FO then old = tmp end if` — **verschachteltes `if/then/end if` innerhalb einer Zeile**

**If/for-chain (2):**
- Z. 539: `if Dp then for Cd in Dp; Cd.chmod("777"); changed = changed + 1; end for; end if`
- Z. 541: `if DG then for Cd in DG; Cd.chmod("777"); changed = changed + 1; end for; end if`

**Module registration (1):**
- Z. 635: `if not h then h = {} end if` — (einziger reiner Einzeiler in util)

### `yuno_viper_core.src` (0) — clean ✅
### `yuno_viper_post.src` (0) — clean ✅

## Key Takeaways

1. **net.src und scan.src sind die Hotspots** — 81 + 55 = 136 von 142 Funden (96%). Fix priorisieren.
2. **Statement-chain Varianten** sind gefährlicher zu fixen (9 in scan.src, 5 in util.src, 2 in net.src) — erfordern sorgfältige Aufteilung der `;`-getrennten Statements.
3. **Drei modulare Fix-Strategien:**
   - **Simple Expansion** (reine Einzeiler): `if X then Y end if` → 3 Zeilen
   - **Statement-chain Expansion**: `if X then Y; Z end if` → 4 Zeilen (if/body/body/end if) — aber nur das `if`-Statement, die Zuweisung vor `;` bleibt auf der gleichen Zeile
   - **Pre-Statement + if**: `A = B; if X then Y end if` → `A = B\nif X then\n  Y\nend if`
4. **Verschachtelte chains** (util.src Z. 242, 389, 569): `if file then tmp = ...; if typeof(tmp) == I.FO then old = tmp end if` — diese brauchen die meiste Sorgfalt beim Refactor.

## Fix Template (Shell)

```bash
# Pure one-line-if → multi-line
cd /home/bratan/greyhack-tools/yuno_viper/modules
python3 << 'PYEOF'
import re, sys

files = [
    "yuno_viper_net.src",
    "yuno_viper_scan.src",
    "yuno_viper_util.src",
]

# Regex für Pure one-line-if: optional führender Whitespace, if ... then ... end if
pattern = re.compile(r'^(\s*)if\s+(.+?)\s+then\s+(.+?)\s+end\s+if\s*$')

for fpath in files:
    with open(fpath) as f:
        orig = f.read()
    
    lines = orig.split('\n')
    new_lines = []
    fixed = 0
    
    for line in lines:
        m = pattern.match(line)
        if m:
            indent = m.group(1)
            condition = m.group(2)
            body = m.group(3)
            # Don't expand if body contains ';' — those need manual handling
            if ';' not in body:
                new_lines.append(f"{indent}if {condition} then")
                new_lines.append(f"{indent}\t{body}")
                new_lines.append(f"{indent}end if")
                fixed += 1
                continue
        new_lines.append(line)
    
    result = '\n'.join(new_lines)
    if result != orig:
        with open(fpath, 'w') as f:
            f.write(result)
        print(f"{fpath}: fixed {fixed} pure one-line-if(s)")
    else:
        print(f"{fpath}: no changes")
PYEOF
```
