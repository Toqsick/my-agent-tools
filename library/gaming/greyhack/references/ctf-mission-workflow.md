# CTF/Mission Hacking Workflow (Verified 2026-06-27)

For missions that ask for "login credentials of any user on a remote machine" with a known public IP and LAN IP.

## Mission Pattern

```
Target: <public_ip> (LAN: <lan_ip>)
Goal: Login credentials (user:password)
```

## Optimal Workflow

### 1. Router → Device Ports
```greyscript
router = get_router("PUBLIC_IP")
devicePorts = router.device_ports("LAN_IP")
```

### 2. Metaxploit → Exploit → Shell
```greyscript
metax = include_lib("/lib/metaxploit.so")
session = metax.net_use("PUBLIC_IP", port)
lib = session.dump_lib
scan = metax.scan(lib)

for area in scan
    addr = metax.scan_address(lib, area)
    segments = addr.split("Unsafe check:")
    for segment in segments[1:]
        labelStart = segment.indexOf("<b>")
        labelEnd = segment.indexOf("</b>")
        if labelStart != null and labelEnd != null then
            exploit = segment[labelStart + 3: labelEnd]
            result = lib.overflow(area, exploit)
            if typeof(result) == "shell" then
                shell = result
            end if
        end if
        if shell != null then break
    end for
    if shell != null then break
end for
```

### 3. Creds via /home (NOT /etc/passwd!)

**CRITICAL**: Non-root shells get "Permission denied" on `/etc/passwd`.
Read `/home/<user>/Config/` instead:

```greyscript
victim = shell.host_computer
home = victim.File("/home")
for folder in home.get_folders
    username = folder.name
    // Bank.txt format: account:hash
    bankFile = victim.File("/home/" + username + "/Config/Bank.txt")
    if bankFile != null then print(bankFile.get_content)
    // Mail.txt format: email:hash
    mailFile = victim.File("/home/" + username + "/Config/Mail.txt")
    if mailFile != null then print(mailFile.get_content)
end for
```

### 4. Decipher (LOCAL only!)

`crypto.decipher()` does NOT work in SSH sessions. Two options:

**Option A**: Print hashes, decipher locally in a separate script
**Option B**: Write hashes to local file, then decipher

```greyscript
// On local computer:
crypto = include_lib("/lib/crypto.so")
password = crypto.decipher("hash_here")
```

## Fallback: SSH Bruteforce

If Metaxploit doesn't yield a shell:

```greyscript
passwords = ["admin", "root", "123456", "password", "test", "agle1", "Gerso"]
users = ["root", "admin", "guest"]

for user in users
    for pass in passwords
        shell = get_shell.connect_service("IP", 22, user, pass)
        if typeof(shell) != "string" and shell != null then
            // SUCCESS
        end if
    end for
end for
```

## Mission Example: 16.174.201.225

- Router: ✅ reachable
- Open port: 21 (FTP, `libftp.so v1.0.0`)
- Exploit: `Essigna @ 0x1784DF8F`
- Shell as: `ingussin`
- `/etc/passwd`: Permission denied
- `/home/ingussin/Config/Bank.txt`: `f5gm0jyb:08b9145460ab1df80d14694d471ea23e`
- `/home/ingussin/Config/Mail.txt`: `ingussin@cepcs.com:bbbff1ac390876499c81773c274878f8`
