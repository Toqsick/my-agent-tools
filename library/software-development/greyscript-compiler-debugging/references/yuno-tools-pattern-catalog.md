# GreyScript Pattern Catalog — Yuno-Tools (28 Real-World Scripts)

> Extrahiert aus `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/`
> am 2026-07-04. Game Version: 0.9.6771-beta. **Stand: Juli 2026**.

## Builtin Frequency (Top 22, über 31 Core-Scripts)

| Builtin | Count | Typ |
|---------|-------|-----|
| `host_computer` | 222 | Core — jeder Script braucht Host-Zugriff |
| `get_shell` | 105 | Core — Shell-/Process-Management |
| `ports` | 86 | Recon — Port-Scannen |
| `get_content` | 79 | Config-Lesen |
| `is_folder` | 69 | Datei-Navigation |
| `metaxploit` | 65 | Exploit-Core |
| `include_lib` | 64 | Library-Loading |
| `net` | 62 | Netzwerk-Layer |
| `crypto` | 61 | Hashing/Verschlüsselung |
| `cat` | 55 | Datei-Ausgabe |
| `bank` | 54 | Bank-Operationen |
| `users` | 46 | User-Management |
| `net_use` | 46 | Service-Exploit |
| `ssh` | 43 | Remote-Login |
| `get_files` | 42 | File-Enumeration |
| `touch` | <20 | File-Erstellung |
| `set_content` | <20 | File-Schreiben |
| `FileSystem.GetFolder` | <20 | Native API |
| `user_input` | <10 | Interactive Input |
| `bank_logs` | <10 | Bank-Logs |

**Nicht existent (❌):** `notify()` , `error()` , `str_repeat()`.

## 10 Working Patterns (✅ aus yuno-tools extrahiert)

### 1. Mehrzeiliges `if/else/end if` (funktioniert ohne `-u`)
```
// ✅ FUNKTIONIERT — greybel build (ohne -u) akzeptiert dies
if condition then
    print("true")
else if other_condition then
    print("other")
else
    print("fallback")
end if
```
**Quelle:** dee_hack, multihop_strike, mission_v3.

### 2. Verschachteltes `if/end if` (Workaround für `else if`)
Wenn der mehrzeilige `else if` auch crasht:
```
// ✅ Workaround — schonendster Parser-Pfad
if condition1 then
    print("1")
end if
if condition2 then
    print("2")
end if
```
**Quelle:** phase1_explorer (bewusst gewählt als Workaround).

### 3. `include_lib` mit Null-Check + `exit`
```
// ✅ Pflicht-Pattern
include_lib = include_lib("/lib/net.so")
if include_lib == null then
    print("[!] Failed to load lib/net.so")
    exit
end if
```
**Quelle:** dee_hack, mission_v3, multihop_strike, deep_recon, br00te_force, dee_z.

### 4. `typeof(val) == "shell"` Connection-Validierung
```
// ✅ Verified: typeof unterscheidet null von shell
session = include_lib.net_use(target_ip, target_port)
if typeof(session) != "shell" then
    print("[!] Connection failed")
    exit
end if
```
**Quelle:** dee_hack, deep_recon.

### 5. `while i < list.len` statt `for`-Loop
```
// ✅ GreyScript hat keinen native for-Loop
i = 0
while i < targets.len
    print(targets[i])
    i = i + 1
end while
```
**Quelle:** Alle Core-Scripts ohne Ausnahme — 0 `for`-Loops gefunden.

### 6. `params.len > 0 then` für CLI-Args
```
// ✅ Standard-Pattern
if params.len > 0 then
    command = params[0]
    if command == "scan" then
        // ...
    end if
end if
```
**Quelle:** bruteforce, bank_grab, misc.

### 7. `char(10)` für Newlines
```
// ✅ Einheitlich in ALLEN Scripts
line = "key: value" + char(10)
content = content + line

// ✅ char(34) für doppelte Anführungszeichen
content = content + "password = " + char(34) + actual_pass + char(34) + char(10)
```
**Quelle:** 31/31 Scripts.

### 8. UPPER_CASE Constants
```
// ✅ Konstanten gross, Variablen klein
TARGET_IP = "199.229.146.172"
SSH_PORT = 22
ROOT_PASS = "root"
BANK_IP = "199.229.146.172:5000"
```
**Quelle:** strike1, multihop_strike, dee_z, bank_grab, sven_strike.

### 9. Type-Literal für Object-Literale
```
// ✅ funktioniert: gemischte Typen im Objekt
config = {
    "host": "199.229.146.172",
    "port": 5000,
    "use_ssl": true,
    "timeout": 30,
}
```
**Hinweis:** Trailing-Komma am letzten Eintrag ist **Pflicht** in GreyScript.

### 10. `ports[i].toString()` für Port-Enumeration
```
// ✅ ports gibt Array von Port-Objekten zurück
p = ports("199.229.146.172")
i = 0
while i < p.len
    port_str = p[i].toString()
    i = i + 1
end while
```
**Quelle:** multihop_strike.

## 10 Broken Patterns (❌ aus Compiler-Bugs)

### 1. `else if` in bestimmten Kontexten
```
// ❌ CRASHT ohne -u Flag
// greybel build ohne -u: Parser-Fehler
```
**Betroffen:** bruteforce.src:25, yuno_v2.src:4.
**Workaround:** Mehrzeiliges Pattern (siehe ✅ #1) oder verschachteltes `if/end if`.

### 2. Einzeiler-if: `if cond then BODY end if`
```
// ❌ CRASHT
if pw != "" then print("found") end if

// ✅ Workaround — Mehrzeiler
if pw != "" then
    print("found")
end if
```
**Workaround:** Immer Mehrzeiler verwenden.

### 3. Inline-if: `x = if cond then a else b`
```
// ❌ CRASHT
used_flag = if greybel_flag then true else false

// ✅ Workaround
use_flag = false
if greybel_flag then
    use_flag = true
end if
```
**Konsequenz:** `greybel build -u` ist tabu (verwandter Bug, bricht an anderer Stelle).

### 4. `greybel build -u` ist tabu
```
// ❌ NIEMALS
greybel build -u input.src output.bin

// ✅ IMMER
greybel build input.src output.bin
```
**Begründung:** Das `-u` Flag aktiviert einen Parser der zwar `else if`/Einzeiler-if akzeptiert, dafür an **anderen Stellen** bricht. Ohne `-u` hast du zwar Syntax-Einschränkungen aber deterministische Fehler.

### 5. `is_folder` vs `is_binary` Verwechslung
```
// ❌ is_binary existiert nicht — falsche Property ist silent no-op
if myFile.is_binary then  // ergibt immer null → falsy

// ✅ Immer is_folder prüfen
if myFile.is_folder then
    print("is a folder")
end if
```

### 6. `0` ist NICHT truthy
```
// ❌ count=0 → if count then → falsy
count = 0
if count then
    print("never reached")
end if

// ✅ Expliziter Vergleich nötig
if count == 0 then
    print("zero")
end if
```

### 7. Negative Indizes crashen
```
// ❌ arr[-1] → RUNTIME CRASH
last = arr[-1]

// ✅ Workaround
last = arr[arr.len - 1]
```

### 8. `str_repeat` existiert nicht
```
// ❌ Nicht existent
padding = str_repeat("=", 50)

// ✅ Workaround
padding = ""
i = 0
while i < 50
    padding = padding + "="
    i = i + 1
end while
```
**Hinweis:** In 31 Scripts 0 Vorkommen von `str_repeat`.

### 9. HTTP nur via `lib/net.so`
```
// ❌ Kein natives HTTP
http_get("https://api.example.com")

// ✅ Korrekt
net = include_lib("/lib/net.so")
if net == null then exit end if
response = net.get("http://199.229.146.172:8080/config.txt")
```

### 10. `notify()` und `error()` existieren nicht
```
// ❌ Beide existieren nicht in GreyScript
notify("Download complete")  // Runtime: unknown function
error("Connection failed")    // Runtime: unknown function
```
**Workaround:** `print()` oder interner Log-Mechanismus.

## 5 Wiederverwendbare Code-Idiome (keine Funktionen in GreyScript)

Da GreyScript **keine `function`-Definitionen** unterstützt, werden diese Blöcke kopiert:

### Idiom 1: Lib-Loader
```
include_lib_name = include_lib("/lib/name.so")
if include_lib_name == null then
    print("[!] can't load lib/name.so")
    exit
end if
```
**Verwendet in:** dee_hack, mission_v3, multihop_strike.

### Idiom 2: Null-Check mit `typeof()`
```
if typeof(variable) != "shell" then
    print("[!] invalid type")
    exit
end if
```
**Verwendet in:** dee_hack, deep_recon.

### Idiom 3: Port-Scan-Loop
```
i = 0
while i < open_ports.len
    target = open_ports[i]
    session = metax.net_use(target_ip, target.port)
    if typeof(session) == "shell" then
        print("[+] got shell on port " + target.port)
    end if
    i = i + 1
end while
```
**Verwendet in:** multihop_strike, mission_final.

### Idiom 4: Home-Config-Looter
```
hacker = get_shell("root", "root")
home_fs = hacker.host_computer.File("/")
i = 0
while i < home_fs.len
    target = home_fs[i]
    if not target.is_folder then
        content = target.get_content
        if content.contains("password") then
            print("[+] found pass in " + target.name)
            // ...
        end if
    end if
    i = i + 1
end while
```
**Verwendet in:** strike1, multihop_strike, mission_v4.

### Idiom 5: Param-Parser
```
if params.len > 0 then
    i = 0
    while i < params.len
        p = params[i]
        if p == "--target" then
            target_ip = params[i + 1]
            i = i + 1
        end if
        i = i + 1
    end while
end if
```
**Verwendet in:** bruteforce, bank_grab.

## Script-Metriken im Überblick

| Metrik | Wert |
|--------|------|
| Core-Scripts (ohne Versionen) | 31 |
| Ø Zeilen pro Script | 103.2 |
| Spannweite | 25–214 |
| Gesamt-LoC Core | 3.201 |
| Größte Datei | viper.src (4.189 Z.) |
| Header `// ====` | 21/31 |
| Header `//command:` | 0/31 ⚠️ |

**Anmerkung:** Keins der 31 Scripts hat einen `//command:`-Header. Das ist ein bekannter Pain-Point: diese Scripts werden via DB-Injection ins Spiel geladen, nicht via `build`-Pipeline. Neue Scripts, die mit `greybel build` gebaut werden sollen, **brauchen** zwingend `//command:` als erste Zeile.

## Quellen

- Alle 28+ Scripts aus `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/`
- Extraktion am 2026-07-04 im Rahmen des MaxClaw v3.0 Agent-Upgrades
- Game-Version: GreyHack 0.9.6771-beta
- Tool-Chain: `greybel build` (ohne `-u` Flag)
