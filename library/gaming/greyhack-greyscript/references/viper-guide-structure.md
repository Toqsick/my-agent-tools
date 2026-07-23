# Viper-Guide-Struktur

> Lib_core-basierte GreyScript-Architektur für Module nach dem Pattern von metaxploit.src, portscan.src, auto_exploit.src, yuno_viper_scan.src.
> **Abgrenzung:** Dieses Pattern nutzt `import_code("lib_core")` + `getContext` + `render/step/ok/fail`. Das neuere YUNO VIPER h={}-Pattern (UtilX, `N()`, `Z`, `P`-Globals) ist eine *andere* Architektur und in der SKILL.md unter "YUNO VIPER Framework Architecture" dokumentiert.

## Module-Skeleton

```greyscript
//command: yuno_viper_<name>
//include: yuno_viper_core

import_code("yuno_viper_core")  // oder import_code("lib_core")

// Dispatcher-Dict mit Inline-Funktionen
dispatch = {}
dispatch["help"] = function()
    showHelp("yuno_viper_<name>",
        ["  nmap     <ip>   Port-Scan + Service-Map",
         "  hack     <ip>   Auto-Hack: scan -> select -> shell -> loot"],
        "Scan/Recon/Exploit-Modul")
end function
```

### Dispatcher-Bauformen

**Variante A — Inline-Dispatch-Dict (aus yuno_viper_scan, kompakt):**
```greyscript
dispatch = {}
dispatch["nmap"] = function(ip)
    // Port-Scan + Service-Map + Profil-Tagging
end function
dispatch["hack"] = function(ip)
    // Auto-Hack 5 Phasen
end function

// Main-Dispatch
ctx = getContext()
pc = ctx["pc"]
params = ctx["params"]
cmd = params.len > 0 and params[0] or ""
args = params[1:]
if cmd == "" or cmd == "--help" then dispatch["help"]()
else if dispatch.hasIndex(cmd) then
    dispatch[cmd](args)
else
    fail("Unbekannt: " + cmd)
end if
```

**Variante B — Function-Declarations (aus portscan/metaxploit, lesbarer):**
```greyscript
yuno_nmap = function()
    ip = requireParam(1, "ip")
    render("NMAP :: Port-Scan", ["Ziel: " + ip])
    // ...
end function

// Main-Dispatch
if params.len < 1 or showHelp(params, "yuno_viper_scan", [...] then exit end if
cmd = params[0]
args = params.slice(1)
if cmd == "nmap" then yuno_nmap(args)
```

## Core-Bausteine (aus lib_core / yuno_viper_core)

| Funktion | Aufruf | Ausgabe |
|----------|--------|---------|
| `getContext()` | — | Map mit shell, pc, user, home, bin, config, logs, params |
| `render(title, lines)` | `["info"]` | Boxed Header + grüner Pfeil |
| `step(n, total, msg)` | `step(2, 5, "Metaxploit laden")` | `[*] (2/5) Metaxploit laden` |
| `ok(msg)` | `ok("3 gefunden")` | `[+] OK: 3 gefunden` (grün) |
| `fail(msg)` | `fail("Meta fehlt")` | `[X] FAIL: Meta fehlt` (rot) + exit |
| `warn(msg)` | `warn("Keine Ports")` | `[!] Keine Ports` (gelb) |
| `info(msg)` | `info("Shell aktiv")` | `[i] Shell aktiv` (grau) |
| `hr` | `hr` | Trennlinie `────` |
| `banner()` | `banner()` | ASCII-Header |
| `requireParam(n, name)` | `requireParam(1, "ip")` | Wert oder fail |
| `optionalParam(n, default)` | `optionalParam(2, "0")` | Wert oder Default |
| `lastParam` | — | `params[params.len-1]` |
| `showHelp(cmd, lines, desc)` | — | Hilfe ausgeben |
| `validIP(ip)` | `validIP("192.168.1.1")` | Boolean |
| `validPort(portStr)` | `validPort("22")` | Boolean |
| `logToFile(pc, path, msg)` | `logToFile(pc, "log.log", "OK")` | Append + char(10) |
| `confirm(msg)` | `confirm("Weiter?")` | Bool (j/ja für true) |

## Triple-Type-Check (Metaxploit/Crypto)

Jeder API-Call, der ein System-Lib-Object zurückgibt, muss mit `typeof()` geprüft werden — **drei Guard-Stufen:**

```
T1 — Lib als Object:         typeof(meta) != "object"
T2 — Result-Type:            typeof(result)  → "shell"/"computer"/"file"/"string"/"number"
T3 — Crypto/Special-Key:     typeof(cryptoKey) + typeof(cryptoKey.lib_name) == "string"
```

### T1: Lib-Objekt (nach include_lib)

```greyscript
meta = include_lib("/lib/metaxploit.so")
if not meta then fail("metaxploit.so fehlt") end if
// T1: Meta-Lib als Object
if typeof(meta) != "object" then fail("Meta kein Object") end if

net = meta.net_use(ip, port)
if not net then fail("net_use fail") end if
lib = net.dump_lib
if not lib then fail("dump_lib fail") end if
// T2: Library als Object mit lib_name
if typeof(lib) != "object" or typeof(lib.lib_name) != "string" then
    fail("Lib-Object ungueltig")
end if
```

### T2: Result-Type (nach overflow)

```greyscript
result = lib.overflow(addr, val)
if not result then fail("Overflow fail") end if

rType = typeof(result)  // "shell", "computer", "file", "string", "number"
// Jeder Typ hat eigene Properties:
if rType == "shell" then
    // result.start_terminal — interactive shell
else if rType == "computer" then
    // result.lan_ip, result.public_ip
else if rType == "file" then
    // result.path, result.is_binary, result.get_content()
else if rType == "string" then
    // result ist der Wert direkt
end if
```

### T3: Crypto-Key (nach crypto.lib_name)

```greyscript
if not crypto then crypto = include_lib("/lib/crypto.so") end if
// T3: Crypto-Key mit lib_name
if typeof(crypto) != "object" or typeof(crypto.lib_name) != "string" then
    fail("Crypto kein gueltiges Objekt")
end if
```

## Service-Map (für Port-Identifikation)

Aus yuno_viper_scan: 19 bekannte Port-Service-Mappings:

```greyscript
serviceMap = {}
serviceMap["21"]     = "FTP"
serviceMap["22"]     = "SSH"
serviceMap["23"]     = "Telnet"
serviceMap["25"]     = "SMTP"
serviceMap["53"]     = "DNS"
serviceMap["80"]     = "HTTP"
serviceMap["110"]    = "POP3"
serviceMap["143"]    = "IMAP"
serviceMap["443"]    = "HTTPS"
serviceMap["445"]    = "SMB"
serviceMap["993"]    = "IMAPS"
serviceMap["995"]    = "POP3S"
serviceMap["1433"]   = "MSSQL"
serviceMap["1521"]   = "Oracle"
serviceMap["2049"]   = "NFS"
serviceMap["3306"]   = "MySQL"
serviceMap["3389"]   = "RDP"
serviceMap["5432"]   = "PostgreSQL"
serviceMap["6379"]   = "Redis"
serviceMap["8080"]   = "HTTP-Alt"
serviceMap["8443"]   = "HTTPS-Alt"

serviceName = serviceMap.hasIndex(str(portNum)) and \
    serviceMap[str(portNum)] or "Unknown"
```

## Exploit Known-DB (5 bekannte Libs + Fallback)

```greyscript
knownDB = {}
knownDB["ssh"]     = {"defVal": "shell"}
knownDB["ftp"]     = {"defVal": "shell"}
knownDB["smtp"]    = {"defVal": "root"}
knownDB["http"]    = {"defVal": "exec"}
knownDB["router"]  = {"defVal": "shell"}// <-- trailing comma!
```

**Wichtig:** Das letzte Paar IMMER mit trailing comma — GreyScript akzeptiert das, fehlende Kommas vor `}` führen zu Compiler-Fehlern.

## Auto-Hack Pipeline (5 Phasen)

```greyscript
step(1, 5, "Phase 1 - NMAP")          // Port-Scan via Router
step(2, 5, "Phase 2 - Metaxploit")    // include_lib + net_use
step(3, 5, "Phase 3 - Kandidaten")    // meta.scan(lib) per Port
step(4, 5, "Phase 4 - Exploit")       // lib.overflow -> typeof Guard
step(5, 5, "Phase 5 - Loot")          // Type-dependend extrahieren
```

## Best Practices

1. **Immer getContext() zuerst** — liefert pc, params, logs-Pfad
2. **params[0] = sub-command, rest = args** — Dispatch per params.len check
3. **Immer typeof() vor Verarbeitung** — Metaxploit/Crypto können null, string oder Object zurückgeben
4. **`logToFile()` am Ende jeder Operation** — Beweissicherung für später
5. **`exit` vs `fail()`** — `fail()` zeigt `[X]` + bricht ab; `exit` ist silent
6. **`warn()` für nicht-kritische Fehler** — User sieht `[!]` aber Skript läuft weiter
7. **Module <12KB halten** — sonst erkennt GreyHack das `//command:` nicht
8. **Triple-Type-Check in Kommentaren markieren** — `// T1`, `// T2`, `// T3` für Lesbarkeit

## Fallstricke

- **`typeof(result)` ist IMMER lowercase string** — `"shell"`, nicht `"Shell"` oder `"object"`
- **`validPort("8080")` gibt Boolean, nicht den Port-Wert** — für Zahlen: `portStr.val`
- **`meta.scan_address()` kann `null` zurückgeben** — IMMER mit `or "-"` guarden
- **`lastParam` ist ein String, kein Keyword** — funktioniert nur wenn lib_core es definiert hat
- **`showHelp()` braucht 3 Argumente** — cmd-name, lines-array, description
- **`for p in ports` iteriert VALUES, nicht indices** — nutze `ports.indexes` für Position
- **`//command: <name>` MUSS Zeile 1 sein** — kein Leerzeichen, kein Kommentar davor
