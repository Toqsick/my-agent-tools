# CI Build Fix — One-Line If & Ternary Expansion (2026-06-19)

## Problem

greybel-js kann `if ... then ... end if` auf einer Zeile NICHT parsen — egal ob mit oder ohne `-u` Flag. Auch ternäre Ausdrücke wie `("OK" if cond else "FAILED")"` werden nicht akzeptiert.

**10 Dateien, ~51 Syntax-Fehler** blockierten den CI-Build.

## Batch-Fix Muster (Python Heredoc)

Dieses Python-Skript findet und expandiert alle one-line `if COND then BODY end if` in einem Ordner:

```bash
cd ~/greyscripts
python3 << 'PYEOF'
import re, os

files = [
    "src/buildcore.src",
    "src/crypto/decypher.src",
    # ... weitere Dateien
]

total_fixed = 0
for f in files:
    if not os.path.exists(f): continue
    with open(f) as fh:
        lines = fh.readlines()
    
    new_lines = []
    fixed = 0
    for line in lines:
        stripped = line.lstrip()
        indent = line[:len(line) - len(stripped)]
        
        m = re.match(r'^if\s+(.+?)\s+then\s+(.+?)\s+end if\s*$', stripped)
        if m:
            condition = m.group(1)
            body = m.group(2)
            new_lines.append(f"{indent}if {condition} then\n")
            new_lines.append(f"{indent}\t{body}\n")
            new_lines.append(f"{indent}end if\n")
            fixed += 1
        else:
            new_lines.append(line)
    
    if fixed > 0:
        with open(f, 'w') as fh:
            fh.writelines(new_lines)
        total_fixed += fixed

print(f"Fixed {total_fixed} one-liner(s) in {len(files)} files")
PYEOF
```

## Ternäre Ausdrücke manuell fixen

Pattern `"OK" if cond else "FAILED"` → explizites `if/else/end if`:

```greyscript
// VORHER:
print("[test] Ergebnis: " + ("OK" if ok else "FAILED"))

// NACHHER:
if ok then
    print("[test] Ergebnis: OK")
else
    print("[test] Ergebnis: FAILED")
end if
```

**Fehlerbild:** `Build error: got Keyword 'if' where ")" is required`

## Backslash-Escapes in Strings

GreyScript unterstützt kein `\"` innerhalb von Strings. Fix: innere `"` durch `'` ersetzen:

```bash
cd ~/greyscripts
python3 << 'PYEOF'
with open("tools/setup.src") as f:
    content = f.read()
content = content.replace('\\"', "'")
with open("tools/setup.src", 'w') as f:
    f.write(content)
PYEOF
```

## Ergebnis

```
Vor Fixes:   8/18 ✅  10/18 ❌  Build failed
Nach Fixes: 18/18 ✅   0/18 ❌  Build complete: 18 file(s) ok
```

## CI Build Script

`scripts/ci-build.sh` erkennt automatisch `greybel` oder `greybel-js`. Baut alle `.src` unter `src/` und `tools/` in `.ci-build/`.

Mit `-u -dbf` Flags:
- `-u` (uglify): minifiziert Ausgabe
- `-dbf` (disable build folder): kein `build/` Subdir

Ohne `-u -dbf`: Output in `$target_dir/build/` (mit Sub-Ordner).