# greybel execute — Mock-Env Testing Pattern

GreyScript-Scripts können VOR dem In-Game-Einsatz mit `greybel execute` in einer Mock-Umgebung getestet werden. Das hat echte Bugs gefunden, die im GreyHack-Spiel auch gecrasht hätten.

## Basics

```bash
# Einfacher Test (params ohne Script-Name, ab Index 0!)
greybel execute yuno.src

# Mit Parametern (Multi-Wert)
greybel execute yuno.src -p "scan" -p "192.168.1.1" -p "22"

# Silent Mode (unterdrückt Progress-Bar-Warnings)
greybel execute yuno.src -p "loot" --silent

# In-Game Mode (verbindet zu Message-Hook auf Port)
greybel execute yuno.src -et In-Game -pt 8332
```

## Validation-Pattern

```bash
# Check ob Script läuft + was Output ist
greybel execute yuno.src -p "help" --silent
echo "Exit code: $?"
```

Exit Code 0 = OK, Exit Code 1 = Runtime Error.

## Echte Bugs die durch Mock-Testing gefunden wurden

### Bug 1: Port.service Map-Field nicht immer vorhanden (2026-07-03)

**Code (kaputt):**
```greyscript
ports = pc.get_ports
while i < ports.len
    p = ports[i]
    print("  " + str(p.port_number) + " | " + p.service + " | " + st + char(10))
    i = i + 1
end while
```

**Crash:**
```
Runtime error: Path "service" not found in map.
at /path/to/yuno.src:409:57
```

**Fix (robust):**
```greyscript
portInfo = p
svc = ""
if typeof(portInfo) == "map" then
    if portInfo.indexOf("service") != -1 then
        if typeof(portInfo.service) == "string" then
            svc = portInfo.service
        end if
    end if
end if
```

**Lesson:** Bei **jedem** Map-Zugriff in GreyScript erst `indexOf("key") != -1` checken. Die Mock-Env ist strenger als GreyHack-In-Game und findet solche Bugs.

## Test-Strategie für neue Scripts

```bash
# 1. Build-Check
greybel build yuno.src -u
# Exit 0 = syntax OK

# 2. Help-Check
greybel execute yuno.src -p "help" --silent
# Sollte Usage-Info ausgeben

# 3. Jeder Command testen
for cmd in help loot defend scan crack; do
    echo "=== TEST: $cmd ==="
    greybel execute yuno.src -p "$cmd" --silent
    echo "Exit: $?"
done

# 4. Edge-Cases
greybel execute yuno.src -p "scan" "127.0.0.1" "22" --silent  # Single-Port
greybel execute yuno.src -p "scan" "127.0.0.1" "99999" --silent  # Invalid Port
greybel execute yuno.src -p "crack" "" --silent  # Empty Hash
```

## //include: Stub-Pattern für Modul-Tests (NEU 2026-07-04)

Wenn ein Modul `//include: yuno_viper_core` (oder ähnliche Abhängigkeiten) im Header hat, schlägt `greybel execute` fehl, weil die abhängige Datei nicht existiert. **Lösung:** Ein Stub-File mit den benötigten Globals erstellen und per `-et Mock` testen.

```bash
# Stub mit den nötigen Globals
cat > /tmp/test_stub.src << 'GSHEOF'
//command: test_stub
//include: yuno_viper_core
// NOTE: Die //include:-Zeile wird von greybel ignoriert wenn das Ziel fehlt.
// Stattdessen definieren wir die benötigten Globals inline:

// Nötige Farben und Konstanten
I = {}
I.FC = "\x1b[31m"  // rot
I.FD = "\x1b[32m"  // gruen
I.FF = "\x1b[37m"  // weiss
I.FG = "\x1b[90m"  // grau
I.FH = "\x1b[33m"  // gelb
I.FK = "\x1b[36m"  // cyan
I.Fa = "/home/"
I.Fh = "/"
I.Fq = char(10)
I.FO = "string"
I.Fj = 0
I.Fk = -1

// Nötiger Colorizer und State
N = function(text, color)
    return color + text + "\x1b[0m"
end function
Z = get_shell.host_computer
P = {}
P.current_user = Z.get_name

// YUNO-SHARED Alternativ-Pattern (für V6-Stil Module)
YUNO_SHARED = {}
YUNO_SHARED.style = N
YUNO_SHARED.main_session = {"version": "1.0", "object": get_shell}

// JETZT den tatsächlichen Modul-Code einbinden
// (Inhalt von yuno_viper_post.src hier per cat einfügen)
GSHEOF

# Oder kürzer: include-Zeile löschen und Globals in die Test-Datei
greybel execute /tmp/test_stub.src -et Mock -si
```

**Wichtig:** Füge NUR die Globals ein, die das Modul tatsächlich referenziert. Bei V6-Modulen (`commands`-Dict, `YUNO_SHARED`-Bridge) reichen `YUNO_SHARED.style` und `YUNO_SHARED.main_session`. Bei VIPER-Modulen (`h`-Dict, `I.F*`, `N()`) brauchst du `I`, `N`, `Z`, `P`. Unnötige Globals erzeugen nur Noise.

## Limits von greybel execute

| Limit | Wert | Workaround |
|-------|------|------------|
| Timeout | Default 5min (für `execute_code` Tool) | Background mode |
| Memory | Greybel default | Sub-processe |
| Real Network | ❌ Mock | In-Game mode (`-et In-Game`) |
| Real Filesystem | ❌ Mock (kann Files lesen via `host_computer.File()`) | Live-Test im Spiel |

## Wann NICHT mock-testbar

| Feature | Mock-Support | Test-Strategie |
|---------|--------------|----------------|
| `include_lib("/lib/X.so")` | ⚠️ Mock kann das, aber ohne echte Libs | Funktioniert, aber Library-Funktionen return null |
| `metax.net_use()` | ⚠️ Mock simuliert offene Ports | Funktioniert teilweise, aber Vulns sind statisch |
| `crypto.decipher()` | ✅ Echte MD5-Wordlist | Funktioniert |
| `get_custom_object` | ❌ Mock return null | Nur im echten Spiel testbar |
| `object.launch()` | ❌ Mock return null | Nur im echten Spiel testbar |
| `user_input()` | ⚠️ Mock piped stdin | Funktioniert mit `echo "input" \| greybel repl` |

## Pre-Flight Checklist für GreyScript-Tools

Vor dem Deployment:

- [ ] `greybel build <tool>.src -u` → Exit 0
- [ ] `greybel execute <tool>.src -p "help" --silent` → Exit 0
- [ ] Jeder Command einmal getestet
- [ ] Edge-Cases (leere Params, ungültige IPs, fehlende Files)
- [ ] Alle Map-Zugriffe mit `indexOf` Guard
- [ ] Alle `null`-Returns behandelt (Computer/File kann null sein)
- [ ] `typeof()` Check vor String-Operations auf Objects
- [ ] `char(10)` statt `\n` in Strings
- [ ] Keine Inline-if/then/end if auf einer Zeile
- [ ] Keine negativen Index-Notationen (`list[-1]`, `params[^0]`)
- [ ] Keine `pass` als Variablen-Name (reserved)

## Build-Pipeline für Repo

```bash
#!/bin/bash
# ci-build.sh — baut alle Tools und prüft mit execute
TOOLS_DIR=~/greyhack-tools/src
cd "$TOOLS_DIR"

for src in $(find . -name "*.src" -not -path "*/backups/*"); do
    # 1. Build
    greybel build "$src" -u > /tmp/build.log 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ BUILD FAIL: $src"
        cat /tmp/build.log
        continue
    fi
    
    # 2. Test help (wenn vorhanden)
    greybel execute "$src" -p "help" --silent > /tmp/exec.log 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ $src — help OK"
    else
        echo "⚠️  $src — no help or crashed"
    fi
done
```

## Lessons

1. **Mock-Env ist strenger als GreyHack-In-Game** — Bugs die in Mock crashen, würden in Game auch crashen. UMGEKEHRT gilt nicht zwingend (Game-spezifische Bugs).
2. **Map-Field-Checks IMMER mit `indexOf`** — verhindert "Path X not found in map" Errors.
3. **`params[0]` ist bei `greybel execute` das ERSTE Argument** (nicht der Script-Name wie in GreyHack-In-Game).
4. **`--silent` ist wichtig** für saubere CI-Logs ohne Progress-Bar-Spam.
5. **`greybel execute` mit `-p` ist der Standard-Test-Weg** — keine REPL nötig.