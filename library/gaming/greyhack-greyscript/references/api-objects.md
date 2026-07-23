# GreyScript API Objects Reference

Condensed from Greydecode 1.5 Extended Edition. Full upstream docs: https://main.greyscript.org/manuals/

## Shell

Entry point for almost everything.

> **WARNING — Common Runtime Crash:** `get_shell.get_name` does NOT exist.
> Attempting it gives `Runtime Error: Key Not Found: 'get_name' not found in map`.
> `get_shell.get_user` also does NOT exist as a documented property.
> The table below is **EXHAUSTIVE** — anything not listed here WILL crash at runtime.
> For basic info, use only verified calls like `get_shell.host_computer.lan_ip`.

| Method | Purpose |
|--------|---------|
| `get_shell` | Returns active shell object |
| `shell.host_computer` | Local Computer object |
| `shell.build(srcPath, binPath, ?allowImport)` | Compile .src to binary |
| `shell.launch(path, args)` | Run a program (args is list) |
| `shell.scp(srcPath, destPath, remoteShell)` | Copy file to remote, returns 1 on success |
| `shell.connect_service(ip, port, user, pass, ?service)` | Open remote connection; service is string like "ssh". Returns a **Shell object** on success, **string error** on failure. ALWAYS `typeof()` the result. |
| `shell.ping(ip)` | Returns 1 if reachable, 0 if not |

The `connect_service` return is itself a Shell-like object — call `.host_computer` on it to work with the target system.

### Remote Access Pattern (canonical)

```greyscript
shell = get_shell
remote = shell.connect_service("1.2.3.4", 22, "root", "password")
if typeof(remote) == "string" then
    print("Connection failed: " + remote)
    exit(0)
end if
remotePC = remote.host_computer
passwdFile = remotePC.File("/etc/passwd")
if passwdFile != null then
    print(passwdFile.get_content())
end if
```

## Computer

Represents a local or remote OS from script perspective.

| Method | Purpose |
|--------|---------|
| `pc.File(path)` | Returns File object or null. **This is the ONLY way to read/write files.** |
| `pc.get_ports()` | Active ports list |
| `pc.get_name()` | Hostname string |
| `pc.show_procs()` | Running processes |
| `pc.wifi_networks(netDevice)` | Available WiFi networks |
| `pc.lan_ip` | Local IP (property) |
| `pc.public_ip` | Public IP (property) |
| `pc.touch(path, filename)` | Create empty file |
| `pc.create_folder(path, name)` | Create folder |

### File Access Pattern (canonical)

```greyscript
// CORRECT — use pc.File(path)
f = pc.File("/etc/passwd")
if f != null then
    content = f.get_content()
end if

// WRONG — these methods DO NOT exist:
// shell.cat(path)      ← does NOT exist
// pc.cat(path)         ← does NOT exist
// shell.ls(path)       ← does NOT exist (use File.get_files/get_folders)
```

## File

Represents both files and folders. Check before use.

| Method | Purpose |
|--------|---------|
| `f.get_content()` | Read text content |
| `f.set_content(content)` | Write content (overwrite) |
| `f.chmod(perm, ?isRecursive)` | Change permissions, returns 1 on success |
| `f.get_files()` | List files in folder |
| `f.get_folders()` | List subfolders |
| `f.is_folder` | Boolean (property) |
| `f.is_binary` | Boolean (property) |
| `f.path` | Full path string (property) |
| `f.delete` | Remove file/folder |

Rule: always `if not f then fail(...)` after `pc.File(path)` — before reading, writing, or checking `is_binary`.

## Router

Network topology view.

| Method | Purpose |
|--------|---------|
| `get_router` | Local router |
| `get_router(ip)` | Router serving target IP |
| `router.public_ip` | External IP |
| `router.local_ip` | Internal IP |
| `router.essid_name` | WiFi ESSID |
| `router.bssid_name` | WiFi BSSID |
| `router.devices_lan_ip()` | List of LAN IPs |
| `router.device_ports(ip)` | Ports for a LAN target |
| `router.used_ports()` | All used ports |
| `router.firewall_rules()` | Firewall rule list |
| `router.port_info(portObject)` | String description of a port |

## Crypto (`/lib/crypto.so`)

Load via `include_lib("/lib/crypto.so")`. Returns null if missing.

| Method | Purpose |
|--------|---------|
| `crypto.airmon(option, device)` | "start" or "stop" monitor mode |
| `crypto.aireplay(bssid, essid, ?maxAcks)` | Capture traffic → file.cap; returns cap path on success, error string on failure |
| `crypto.aircrack(capFilePath)` | Crack password from cap file |
| `crypto.smtp_user_list(ip, port)` | ⚠️ Returns list, error string, OR null. Triple type-check required. |

### WiFi workflow (canonical order)
1. `crypto.airmon("start", iface)`
2. `cap = crypto.aireplay(bssid, essid, ackCount)`
3. Check `typeof(cap) == "string"` → error
4. `crypto.airmon("stop", iface)` — always, even on error
5. `pass = crypto.aircrack(current_path + "/file.cap")`

## Metaxploit (`/lib/metaxploit.so`)

Load via `include_lib("/lib/metaxploit.so")`. This is a workflow, not a single call.

| Method | Purpose |
|--------|---------|
| `meta.load(path)` | Load local library into MetaLib |
| `meta.net_use(ip, ?port)` | Open remote NetSession |
| `net.dump_lib()` | Pull remote library as MetaLib |
| `meta.scan(metaLib)` | List vulnerable addresses |
| `meta.scan_address(metaLib, memAddress)` | Info about one address (the "unsecValue") |
| `lib.overflow(mempAddress, unsecValue, ?optArgs)` | ⚠️ Can return Shell, Computer, File, String, Number. Always typeof() first. |
| `lib.lib_name` | Library name (property) |
| `lib.version` | Version string (property) |

### Workflow (6 Stufen)
1. Load metaxploit.so
2. Get target lib: `meta.load(path)` OR `net = meta.net_use(ip, port); lib = net.dump_lib`
3. Inspect: `print(lib.lib_name); print(lib.version)`
4. Scan: `addrs = meta.scan(lib)`
5. Analyze each: `info = meta.scan_address(lib, addr)`
6. Exploit: `result = lib.overflow(addr, unsecValue)` → **typeof() before use**
7. Route result: shell.start_terminal / computer.lan_ip / file.get_content / print

## AptClient (`/lib/aptclient.so`)

Environment maintenance.

| Method | Purpose |
|--------|---------|
| `apt.search(name)` | Search packages |
| `apt.show(repo)` | List packages in repo |
| `apt.install(name, ?path)` | Install package |
| `apt.check_upgrade(filePath)` | Check if newer version exists |

## Language Reference Quick-Hits

- `is_valid_ip(string)` — global function, returns boolean
- `user_input(promptString)` — blocking prompt, returns string
- `clear_screen` — statement, no parens
- `exit` / `exit(code)` — terminate script
- `typeof(x)` — returns "string", "number", "list", "map", "shell", "computer", "file", etc.
- `current_path` — global: working directory of running script
- `params` — list of command-line arguments passed via `shell.launch(path, [args])`
- String interpolation: only concatenation via `+` — no f-strings, no `${}`
