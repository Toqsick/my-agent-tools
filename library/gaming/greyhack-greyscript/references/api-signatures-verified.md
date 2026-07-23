# Verified API Signatures — GreyScript

> Verified against greyscript-meta 2026-06-27. Many tutorials online use incorrect method names.
> For the short overview see SKILL.md "Correct API Signatures (quick ref)".

## Shell → Remote Access

```
// CORRECT: connect_service returns a Shell object
shell = get_shell
remote = shell.connect_service("1.2.3.4", 22, "user", "pass")
if typeof(remote) == "string" then
    print("Error: " + remote)
    exit(0)
end if
remotePC = remote.host_computer
```

**WRONG (old skill version said `shell.connect_service` returns `null` on fail):**
```
if remote == null then ...  // ← WRONG, it returns a string error
```

## Shell object — methods that DO exist

Only these are guaranteed:
- `host_computer` — the local Computer
- `build(srcPath, binPath)` — compile a `.src` file
- `launch(path, args)` — start a binary
- `scp(src, dst)` — copy via scp
- `connect_service(ip, port, user, pass)` — open remote session

**Methods that DO NOT exist on Shell:**
- `get_name` — Runtime Error: Key Not Found
- `get_user` — not documented, may crash
- `current_user` — does not exist
- `get_hostname` — does not exist

For the current user/computer name, use `get_shell.host_computer` and check documented properties (`lan_ip`, `public_ip`).

## Computer → File Access

```
// CORRECT: Use pc.File(path) → file object
f = pc.File("/etc/passwd")
if f != null then
    content = f.get_content()
end if

// WRONG: shell.cat("/etc/passwd")  ← does NOT exist in GreyScript
// WRONG: pc.cat("/etc/passwd")     ← does NOT exist
```

Always `f = pc.File(path); if not f then fail(...)` before using.
Check `f.is_folder` and `f.is_binary` before reading — `get_content` fails on folders.

## Metaxploit → Remote Exploitation (6 stages)

```
metax = include_lib("/lib/metaxploit.so")
net = metax.net_use("1.2.3.4", 22)   // returns netSession
metaLib = net.dump_lib               // returns MetaLib
addrs = metax.scan(metaLib)          // list of vulnerable addresses
info = metax.scan_address(metaLib, addrs[0])  // exploit details
result = metaLib.overflow(addrs[0], exploitValue)  // Shell/File/Computer/String/Number
```

1. `meta = include_lib("/lib/metaxploit.so"); if not meta then fail("not found")`
2. `lib = meta.load(path)` for local OR `net = meta.net_use(ip, port); lib = net.dump_lib` for remote
3. `print(lib.lib_name); print(lib.version)` — know your target
4. `addrs = meta.scan(lib)` — list of vulnerable addresses
5. For each `addr`: `info = meta.scan_address(lib, addr)` to learn the exploit value
6. `result = lib.overflow(addr, unsecValue)` — **always typeof() before processing**

## File Object

```
f = pc.File("/path/to/file")
if f != null then
    // Reading
    content = f.get_content()

    // Writing
    f.set_content("new content")

    // Properties
    isBin = f.is_binary
    isDir = f.is_folder
    fpath = f.path

    // Directory listing
    subFiles = f.get_files()
    subDirs = f.get_folders()
end if
```

`chmod()` returns `1` on success, not the new mode value.

## SSH remote filesystem scanning pattern

File access is via `computer.File(path).get_content()`, NOT `shell.cat()` or `shell.ls()` — those methods do NOT exist in GreyScript.

For read-only scanners:

```
remote = shell.connect_service(ip, port, user, pass)
if typeof(remote) == "string" then
    warn("SSH-Verbindung fehlgeschlagen: " + remote)
    return
end if

remotePC = remote.host_computer
if remotePC == null then
    warn("Remote Computer-objekt nicht verfuegbar")
    return
end if

// CORRECT: Use pc.File(path) to read files
passwdFile = remotePC.File("/etc/passwd")
if passwdFile != null then
    content = passwdFile.get_content()
    print(content)
end if

// CORRECT: Use pc.File(path) for directory listing
homeDir = remotePC.File("/home")
if homeDir != null then
    if not homeDir.is_binary then
        files = homeDir.get_files()
        folders = homeDir.get_folders()
    end if
end if

// WRONG (these do NOT exist):
// shell.cat("/etc/passwd")     ← Runtime error
// shell.ls("/home")            ← Runtime error
// remotePC.cat("/etc/passwd")  ← Runtime error
```

**Do not execute exploits or install payloads from a scanner unless the user explicitly approves that next step.** See `references/suid-exploit-remote-2026-06-19.md` for the concrete `suid_exploit` SSH scan implementation.
