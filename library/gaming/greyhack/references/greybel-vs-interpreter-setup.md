# greybel-vs Interpreter & GreyScript API Reference

## Teil 1: greybel-vs Interpreter Setup

### Discovery
Der greybel-vs (https://github.com/Toqsick/greybel-vs.git) enthält einen **eigenen GreyScript-Interpreter** mit Mock-Environment. Man kann GreyScript MIT get_shell, include_lib, metaxploit.so etc. testen — OHNE das Spiel zu starten!

### Setup (einmalig)
```bash
cd /home/bratan
git clone https://github.com/Toqsick/greybel-vs.git
cd greybel-vs
npm install
npm run compile
```

### Extension Development Host starten
```bash
cd ~/greybel-vs
mkdir -p test-workspace
code --extensionDevelopmentPath=. test-workspace/
```

### CLI Interpreter (schnellster Test)
```bash
# Direkt ausführen ohne VSCode:
~/node_modules/.bin/greybel execute <file.src> -et Mock -si

# Oder aus dem yuno-tools Ordner:
cd "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools"
~/node_modules/.bin/greybel execute dee_hack.src -et Mock -si
```

### Mock-Environment Details (verified 2026-06-27)
- **Admin:** `root:test`
- **Eigener Computer:** IP `142.32.54.56`, Hostname `entooxi` (seed-abhängig)
- **Libraries in /lib/:** `init.so`, `net.so`, `kernel_module.so`, `crypto.so`, `metaxploit.so`, `blockchain.so`, `aptclient.so`, `testlib.so`, `libssh.so`
- **Binaries in /bin/:** `build`, `cat`, `cp`, `kill`, `ls`, `mkdir`, `mv`, `ps`, `pwd`, `rm`, `sudo`, `touch`, `whoami`, `aircrack`, `aireplay`, `airmon`, `apt-get`, `ftp`, `ifconfig`, `iwconfig`, `iwlist`, `nmap`, `nslookup`, `ping`, `rshell-interface`, `smtp-user-list`, `sniffer`, `ssh`, `whois`, `chgrp`, `chmod`, `chown`, `groupadd`, `groupdel`, `groups`, `passwd`, `useradd`, `userdel`, `decipher`, `scanlib`, `scanrouter`
- **Home-User:** `test`, `guest`
- **Seed:** "test" (konsistente generierte Entities)

### Mock-Limitations (verified 2026-06-27)
| Feature | Mock | Echtes Spiel |
|---------|------|--------------|
| `get_shell.host_computer` | ✅ funktioniert | ✅ |
| `pc.public_ip` / `local_ip` | ✅ | ✅ |
| `pc.is_network_active` | ✅ | ✅ |
| `pc.get_ports` | ✅ (port_number, is_closed) | ✅ |
| `pc.File(path)` | ✅ | ✅ |
| `file.is_folder` | ✅ | ✅ |
| `file.get_files` / `get_folders` | ✅ | ✅ |
| `file.name` / `file.size` | ✅ | ✅ |
| `file.get_content` | ❌ gibt null zurück | ✅ |
| `shell.connect_service(IP, Port, User, Pass)` | ❌ "port closed" | ✅ |
| `metax.net_use(IP, Port)` | ❌ nicht unterstützt | ✅ |
| `include_lib("/lib/metaxploit.so")` | ✅ | ✅ |
| `include_lib("/lib/crypto.so")` | ✅ | ✅ |
| `include_lib("/lib/net.so")` | ❌ gibt null zurück | ✅ |

**Fazit:** Mock-Env ist gut für Syntax-Tests und FileSystem-Exploration. Für echte Hacks (Remote-Shell, Overflow, File-Inhalte) MUSS das echte Spiel laufen.

---

## Teil 2: GreyScript API Reference (verified against greyscript-meta JSON)

### File Object
```greyscript
f = pc.File("/etc/passwd")
if f == null then
    print("nicht gefunden")
else
    print(f.name)        // "passwd"
    print(f.path)        // "/etc/passwd"
    print(f.size)        // "262" (string, nicht int!)
    print(f.permissions) // "-rwxr-xr-x"
    print(f.is_binary)   // 0 oder 1
    print(f.is_folder)   // 0 oder 1
    print(f.get_content) // Dateiinhalt (null bei Binärdateien)
    f.parent            // File-Objekt des Parent-Ordners
end if

// Ordner durchsuchen
folder = pc.File("/home")
if folder.is_folder then
    files = folder.get_files     // Liste von File-Objekten
    folders = folder.get_folders // Liste von File-Objekten
    for file in files
        print("[F] " + file.name + " (" + file.size + "B)")
    end for
    for subfolder in folders
        print("[D] " + subfolder.name)
    end for
end if
```

### Computer Object
```greyscript
pc = get_shell.host_computer

print(pc.public_ip)       // "158.14.166.104"
print(pc.local_ip)        // "192.168.0.9"
print(pc.get_name)        // Hostname
print(pc.is_network_active) // 1 oder 0

ports = pc.get_ports
for p in ports
    state = "open"
    if p.is_closed then
        state = "closed"
    end if
    print("Port " + str(p.port_number) + " | " + state)
end for

pc.File(path)             // File-Objekt holen
pc.create_folder(path, name) // Ordner erstellen
pc.touch(path, name)      // Leere Datei erstellen
```

### Shell Object
```greyscript
shell = get_shell  // KEINE Parameter! Nicht get_shell("user", "pass")

// Remote verbinden (SSH)
remote = shell.connect_service("199.229.146.172", 22, "root", "agle1")
if typeof(remote) == "string" then
    print("Fehler: " + remote)
else
    // remote ist ein Shell-Objekt
    remotePc = remote.host_computer
end if

// Datei transfer
shell.scp("/bin/ls", "/etc/", remoteShell)

// Ping
if shell.ping("199.229.146.172") then
    print("Host erreichbar")
end if

// Build
result = shell.build("/home/Bratan/bin/tool.src", "/home/Bratan/bin/")
if result != "" then
    print("Build-Fehler: " + result)
end if

// Launch
shell.launch("/bin/cat", "/etc/passwd")
```

### Metaxploit Object
```greyscript
metax = include_lib("/lib/metaxploit.so")

// Remote: net_use + dump_lib
net = metax.net_use("199.229.146.172", 22)
if net != null then
    lib = net.dump_lib
    print(lib.lib_name)
    print(lib.version)
end if

// Local: load
lib = metax.load("/lib/init.so")

// Scan
addrs = metax.scan(lib)
for addr in addrs
    info = metax.scan_address(lib, addr)
    // Parse info for exploit labels
    segments = info.split("Unsafe check: ")
    for segment in segments
        labelStart = segment.indexOf("<b>")
        labelEnd = segment.indexOf("</b>")
        if labelStart != -1 and labelEnd != -1 then
            exploit = segment[labelStart + 3: labelEnd]
            print("Exploit: " + exploit)
            // Overflow!
            result = lib.overflow(addr, exploit)
            if typeof(result) == "shell" then
                print("Shell erhalten!")
            end if
        end if
    end for
end for

// Reverse Shell Server
shells = metax.rshell_server
if typeof(shells) == "list" then
    firstShell = shells[0]
end if

// Sniffer
result = metax.sniffer
```

### Port Object
```greyscript
ports = pc.get_ports
for p in ports
    print(p.port_number)  // Int
    print(p.is_closed)    // 1 = geschlossen, 0 = offen
    print(p.get_lan_ip)   // LAN-IP des Ziels
end for
```

### Crypto Object
```greyscript
crypto = include_lib("/lib/crypto.so")

result = crypto.smtp_user_list(ip, port)
if result == null then
    print("Keine Antwort")
else if typeof(result) == "string" then
    print("Fehler: " + result)
else if typeof(result) == "list" then
    for user in result
        print(user)
    end for
end if
```

### Router Object
```greyscript
router = get_router("199.229.146.172")
// oder
router = get_router  // Default-Router

ports = router.used_ports
lan = router.get_lan("199.229.146.172")
pub = router.get_public_ip
```

### BankAccount Object
```greyscript
bank = pc.BankAccounts[0]
print(bank.account)     // Kontonummer
print(bank.balance)     // Kontostand
bank.wireMoney(amount, targetAccount) // Überweisung
```

### MailAccount Object
```greyscript
mail = pc.MailAccounts[0]
print(mail.address)    // "gregor@gusesamoz.org"
print(mail.password)   // Passwort
```

---

## Teil 3: In-Game Deployment (nach Test)

1. **Copy-Paste:** Fileserver → Browser → CodeEditor (sicherster Weg)
2. **Message-Hook:** BepInEx + Plugin → `greybel import`
3. **Manuell:** CodeEditor → New → Schreiben

## Pitfalls
- **Mock ≠ Echter Spiel:** `file.get_content` und `connect_service` funktionieren NUR im echten Spiel
- **Kein wget im Spiel:** Fileserver nur für Interpreter-Tests
- **Free-Model kann offline gehen:** Fallback: `hermes config set delegation.model deepseek/deepseek-v4-flash:free`
- **Greybel execute Pfad:** `greybel execute` braucht absoluten Pfad oder korrektes CWD
- **Backslash in Strings:** `\"` in print-String crasht greybel-js — nutze single quotes für Pfade
- **Inline-if/then/end if:** `if X then Y end if` auf EINER Zeile crasht greybel-js — immer multi-line!
