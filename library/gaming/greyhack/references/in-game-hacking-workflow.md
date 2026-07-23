# In-Game Hacking Workflow (Verified 2026-06-27)

Complete workflow for hacking NPCs in GreyHack, tested and verified in real gameplay.

## Prerequisites

Before hacking, recon your own computer to know what you have:

```greyscript
pc = get_shell.host_computer
print(pc.public_ip)    // Your public IP
print(pc.local_ip)     // Your LAN IP
print(pc.get_name)     // hostname

// Check libraries
metax = include_lib("/lib/metaxploit.so")
crypto = include_lib("/lib/crypto.so")
net = include_lib("/lib/net.so")

// Check ports
ports = pc.get_ports

// Check tools in /bin
binFolder = pc.File("/bin")
if binFolder.is_folder then
    files = binFolder.get_files
    for f in files
        print(f.name)
    end for
end if
```

## Phase 1: Router Recon

Get the target's router and find open ports:

```greyscript
router = get_router("TARGET_PUBLIC_IP")
if router == null then exit("Router unreachable")

// Get ports for specific LAN device
devicePorts = router.device_ports("TARGET_LAN_IP")

// Or scan all router ports
allPorts = router.used_ports
for p in allPorts
    lanIp = p.get_lan_ip
    info = router.port_info(p)
    print("Port " + p.port_number + " → " + lanIp + " (" + info + ")")
end for
```

## Phase 2: Metaxploit Scan

Scan target for vulnerabilities:

```greyscript
metax = include_lib("/lib/metaxploit.so")

// Try common ports
testPorts = [21, 22, 25, 80, 141, 8080, 1222, 1542, 3306, 3307, 3308, 6667, 37777]

for port in testPorts
    session = metax.net_use("TARGET_IP", port)
    if session == null then continue
    
    lib = session.dump_lib
    if lib == null then continue
    
    print("Port " + port + ": " + lib.lib_name + " v" + lib.version)
    
    // Scan for vulnerabilities
    scan = metax.scan(lib)
    if scan == null then continue
    
    for area in scan
        addr = metax.scan_address(lib, area)
        if addr != null then
            // Parse exploits (see API reference)
            segments = addr.split("Unsafe check:")
            // ... extract and try exploits
        end if
    end for
end for
```

## Phase 3: SSH Login (if you have credentials)

Direct login with known credentials:

```greyscript
shell = get_shell.connect_service("TARGET_IP", 22, "root", "password")
if typeof(shell) == "string" then
    print("Login failed: " + shell)
else if shell != null then
    print("Shell obtained!")
    target = shell.host_computer
end if
```

## Phase 4: File Access

Once you have a shell, read files:

```greyscript
target = shell.host_computer

// /etc/passwd — ONLY readable by root!
passwdFile = target.File("/etc/passwd")
if passwdFile != null then
    content = passwdFile.get_content
    if content == null then
        print("Permission denied — need root shell")
    else
        // Parse: username:hash per line
    end if
end if

// NON-ROOT FALLBACK: Read /home/<user>/Config/ for creds
home = target.File("/home")
if home != null and home.is_folder then
    folders = home.get_folders
    for folder in folders
        username = folder.name
        bankFile = target.File("/home/" + username + "/Config/Bank.txt")
        if bankFile != null then
            bankContent = bankFile.get_content
            if bankContent != null then
                print("Bank: " + bankContent)
            end if
        end if
        mailFile = target.File("/home/" + username + "/Config/Mail.txt")
        if mailFile != null then
            mailContent = mailFile.get_content
            if mailContent != null then
                print("Mail: " + mailContent)
            end if
        end if
    end for
end if
```

## Phase 5: Decipher Passwords

**MUST be done on LOCAL computer, NOT in SSH session!**

```greyscript
// On your OWN computer:
crypto = include_lib("/lib/crypto.so")

// Hashes from target's /etc/passwd
hashes = ["ced2809f5ea305d9df169b744d5a5d23", "fa368a40355bfa96b962825da0e19915"]
usernames = ["root", "Treraz"]

i = 0
while i < hashes.len
    password = crypto.decipher(hashes[i])
    if password != null then
        print(usernames[i] + " = " + password)
    else
        print(usernames[i] + " = (not crackable)")
    end if
    i = i + 1
end while
```

## Phase 6: Money Transfer

After obtaining bank credentials:

```greyscript
// Bank.txt format: { "account": "DEE-8847", "balance": 2450, "ip": "166.80.248.141" }
// Access bank via browser or in-game terminal
// Navigate to bank IP, login with credentials
```

## Common Pitfalls

1. **`connect_service` returns string on error** — always check `typeof(result) == "string"`
2. **`decipher` doesn't work in SSH** — copy hashes to local computer first
3. **`file.size` is a STRING** — use `.to_int` to convert
4. **`get_shell` takes NO parameters** — use `get_shell` not `get_shell("user", "pass")`
5. **Mock ≠ Real game** — `get_content` returns null in Mock but works in-game
6. **`device_ports` may return null** — fallback to `used_ports` and filter by `get_lan_ip`
7. **One-line `if/then/end if` fails in greybel** — always use multi-line
8. **`//` comments ARE valid** — greybel-js accepts `//` single-line comments (verified 2026-06-27)
9. **`=======` separators break greybel** — `=======` standalone lines cause "Punctuator where expression expected". Remove or replace with `// ---`
10. **`lib.overflow()` not `metaLib.overflow()`** — In greybel-js, call overflow on the MetaLib reference from `dump_lib`, not on the metax object
11. **Permission denied on `/etc/passwd`** — non-root shell cannot read `/etc/passwd`. Read `/home/<user>/Config/` instead for credentials
12. **Mock-Env limitations** — `connect_service` to external IPs fails in Mock ("can't connect: port closed"). `get_content` returns null. Test in-game for real results.
13. **`line.indexOf(":") != null` is wrong** — `indexOf` returns `-1` not `null`. Use `line.indexOf(":") != -1`

## Quick Test Script

Use this to verify your setup before a real hack:

```greyscript
print("=== SETUP TEST ===" + char(10))

pc = get_shell.host_computer
print("IP: " + pc.public_ip)
print("Host: " + pc.get_name)

if pc.is_network_active then
    print("Network: OK")
else
    print("Network: FAIL")
end if

// Libraries
libs = ["/lib/metaxploit.so", "/lib/crypto.so", "/lib/net.so"]
for lib in libs
    result = include_lib(lib)
    if result != null then
        print(lib + ": OK")
    else
        print(lib + ": MISSING")
    end if
end for

// Ports
ports = pc.get_ports
print("Ports: " + ports.len)

// /etc/passwd
passwd = pc.File("/etc/passwd")
if passwd != null then
    content = passwd.get_content
    if content != null then
        print("passwd: " + content.len + " chars")
    end if
end if

print("=== TEST COMPLETE ===" + char(10))
```
