# GreyScript API Reference (Verified 2026-06-27)

Complete API reference extracted from `greyscript-meta` JSON files in `node_modules/greyscript-meta/dist/descriptions/en/`.

## General Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `get_shell` | `shell` | Returns shell of current computer. NO parameters! |
| `get_shell.host_computer` | `computer` | Current computer object |
| `get_router([ip])` | `router` | Local router or remote router by IP |
| `include_lib(path)` | `object` | Load library (.so file) |
| `typeof(value)` | `string` | Returns type name: "shell", "string", "number", "list", "map", "file" |
| `string(value)` | `string` | Convert to string |
| `user_input()` | `string` | Read user input |
| `exit()` | - | Exit script |
| `print(text)` | - | Print to terminal |
| `char(10)` | `string` | Newline character |
| `str(value)` | `string` | Convert to string |

## Shell Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `shell.host_computer` | `computer` | Computer associated with this shell |
| `shell.connect_service(ip, port, user, pass)` | `shell` or `string` | SSH/FTP connect. Returns string on error |
| `shell.build(src_path, out_dir)` | `string` | Compile .src to binary. Empty string = success |
| `shell.launch(path, [params])` | `number` or `string` | Launch binary. 1 = success |
| `shell.scp(src, dest, shell)` | `number` or `string` | Copy file between computers |
| `shell.ping(ip)` | `number` | Ping remote IP. 1 = reachable |
| `shell.start_terminal` | - | Open interactive terminal |

## Computer Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `computer.File(path)` | `file` or `null` | Get file/folder at path |
| `computer.get_ports` | `list` | List of port objects |
| `computer.get_name` | `string` | Hostname |
| `computer.public_ip` | `string` | Public IP address |
| `computer.local_ip` | `string` | Local IP address |
| `computer.is_network_active` | `number` | 1 = connected |
| `computer.create_folder(path, name)` | `number` or `string` | Create folder |
| `computer.touch(path, name)` | `number` or `string` | Create empty file |
| `computer.users` | `list` | User accounts |
| `computer.config` | `map` | ConfigOS data |

## File Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `file.name` | `string` | File name |
| `file.path` | `string` | Full path |
| `file.size` | `string` | File size in bytes (STRING, not number!) |
| `file.get_content` | `string` or `null` | Read file content |
| `file.set_content(text)` | `number` or `string` | Write content |
| `file.is_folder` | `number` | 1 = folder (UNRELIABLE — use `not is_binary`) |
| `file.is_binary` | `number` | 1 = binary file |
| `file.get_files` | `list` or `null` | List files in folder (null if not folder) |
| `file.get_folders` | `list` or `null` | List subfolders (null if not folder) |
| `file.parent` | `file` | Parent folder |
| `file.permissions` | `string` | Permission string like "-rwxr-xr-x" |
| `file.chmod(perm, recursive)` | `string` | Change permissions |
| `file.copy(path, name)` | `number` or `string` | Copy file |
| `file.move(path, name)` | `number` or `string` | Move file |
| `file.rename(name)` | `string` | Rename file |
| `file.delete` | `string` | Delete file (empty string = success) |

## Port Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `port.port_number` | `number` | Port number |
| `port.is_closed` | `number` | 1 = closed, 0 = open |
| `port.get_lan_ip` | `string` | LAN IP this port points to |

## Router Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `router.public_ip` | `string` | Public IP |
| `router.local_ip` | `string` | Local IP |
| `router.used_ports` | `list` | All forwarded ports |
| `router.device_ports(lan_ip)` | `list` | Ports for specific LAN device |
| `router.devices_lan_ip` | `list` | All LAN IPs |
| `router.port_info(port)` | `string` | Service info (e.g. "ssh 1.0.0") |
| `router.ping_port(port_num)` | `port` | Ping specific port |
| `router.firewall_rules` | `list` | Firewall rules |
| `router.kernel_version` | `string` | Kernel version |

## Metaxploit Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `metaxploit.load(path)` | `metaLib` | Load local library |
| `metaxploit.net_use(ip, port)` | `netSession` | Connect to remote service |
| `metaxploit.scan(lib)` | `list` | Scan for vulnerabilities (returns memory areas) |
| `metaxploit.scan_address(lib, area)` | `string` | Get vulnerability details |
| `metaxploit.rshell_client(ip, port, name)` | `number` or `string` | Launch reverse shell client |
| `metaxploit.rshell_server` | `list` | List reverse shell connections |
| `metaxploit.sniffer` | `string` | Network sniffer |

## MetaLib Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `lib.overflow(address, exploit)` | varies | Exploit vulnerability. Returns shell/file/number/string |
| `lib.lib_name` | `string` | Library name |
| `lib.version` | `string` | Library version |
| `lib.is_patched` | `number` | 1 = patched |
| `lib.debug_tools(user, pass)` | `debugLibrary` | Debug mode |

## NetSession Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `session.dump_lib` | `metaLib` | Get library from remote service |
| `session.get_num_users` | `number` | Number of users |
| `session.is_any_active_user` | `number` | 1 = active user |
| `session.get_num_conn_gateway` | `number` | Gateway client count |
| `session.get_num_portforward` | `number` | Port forward count |

## Crypto Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `crypto.decipher(hash)` | `string` or `null` | Decrypt MD5 hash to password. Returns null if password doesn't exist in game world |
| `crypto.encrypt(file, key)` | `number` or `string` | Encrypt file |
| `crypto.decrypt(file, key)` | `number` or `string` | Decrypt file |
| `crypto.aircrack(cap_file)` | `string` | Crack WiFi capture |
| `crypto.airmon(action, device)` | `number` or `string` | Toggle monitor mode |
| `crypto.aireplay(bssid, essid, acks)` | `null` or `string` | WiFi replay attack |
| `crypto.smtp_user_list(ip, port)` | `list` or `string` | SMTP user enumeration |

## Wallet/Blockchain Object

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `wallet.get_balance(coin)` | `number` | Get coin balance |
| `wallet.list_coins` | `list` | List wallet coins |
| `wallet.wireMoney(amount, dest)` | `string` or `number` | Wire money (empty string = success) |
| `wallet.buy_coin(name, qty, price, pass)` | `number` | Buy coins |
| `wallet.sell_coin(name, qty, price, pass)` | `number` | Sell coins |

## Exploit Result Parsing

When using `metaxploit.scan_address()`, parse the output like this:

```greyscript
addr = metaxploit.scan_address(lib, area)
segments = addr.split("Unsafe check:")
i = 1
while i < segments.len
    segment = segments[i]
    labelStart = segment.indexOf("<b>")
    labelEnd = segment.indexOf("</b>")
    hasStar = segment.indexOf("*") != null  // * = has requirements
    
    if labelStart != null and labelEnd != null and not hasStar then
        exploit = segment[labelStart + 3: labelEnd]
        result = lib.overflow(area, exploit)
        if typeof(result) == "shell" then
            // SHELL!
        end if
    end if
    i = i + 1
end while
```

## CRITICAL: crypto.decipher Limitations

1. **Does NOT work in SSH sessions** — only on local computer
2. **Returns null if password doesn't exist in game world** — not all hashes are crackable
3. **MD5-based** — only works for passwords that exist in the game's database

## Type Checking Pattern

Always use `typeof()` when API return type varies:

```greyscript
result = get_shell.connect_service(ip, 22, "root", "pass")
if typeof(result) == "string" then
    print("Error: " + result)
else if result == null then
    print("Null shell")
else
    shell = result
    // Use shell...
end if
```
