# GreyHack Session 2026-06-27 — Key Learnings

Session mit Gregor (Basti) — verschiedene Hacking-Versuche und Lessons Learned.

## Mission: 16.174.201.225 — Login Credentials (CTF-Style)

**Aufgabe**: Finde Login Credentials für `16.174.201.225` (LAN: `172.16.5.4`).

**Workflow der Lösung**:
1. `get_router("16.174.201.225")` → Router-Objekt
2. `router.device_ports("172.16.5.4")` → Ports des Opfers
3. `metax.net_use("16.174.201.225", port)` → netSession
4. `session.dump_lib` → metaLib
5. `metax.scan(lib)` → Vulnerabilities
6. `metax.scan_address(lib, area)` → Exploit-Details
7. Exploit-Extraktion aus "Unsafe check:" Segmenten
8. `lib.overflow(area, exploit)` → Shell
9. `/home/<user>/Config/Bank.txt` + `Mail.txt` lesen (kein root nötig!)
10. `crypto.decipher(hash)` → Passwörter knacken (lokal, NICHT in SSH!)

**Ergebnis**: Shell als `ingussin` via `Essigna` Exploit auf Port 21 (FTP).
- Bank.txt: `f5gm0jyb:08b9145460ab1df80d14694d471ea23e`
- Mail.txt: `ingussin@cepcs.com:bbbff1ac390876499c81773c274878f8`

**WICHTIG**: `/etc/passwd` ist für non-root User **nicht lesbar** (Permission denied).
Aber `/home/<user>/Config/` ist lesbar — das enthält Bank + Mail Creds!

## Spieler-Profil (aktuell)

| Eigenschaft | Wert |
|-------------|------|
| Nickname | Gregor (PlayerID: `e85129e9ae28753542b9bf710378c645`) |
| Öffentliche IP | `158.14.166.104` |
| Lokale IP | `192.168.0.9` |
| Hostname | `ibm` |
| Home | `/home/gregor` |
| Mail | `gregor@gusesamoz.org` |
| Bank | `O1bx8eS6-niyufumay.com` |
| Cupones | 5 |
| Netzwerk | `Therwing` (BSSID: `25:47:C8:AE:A3:11`) |

## Libraries die Gregor hat

- ✅ `metaxploit.so`
- ✅ `crypto.so`
- ✅ `net.so`
- ✅ `blockchain.so`
- ✅ `aptclient.so`
- ✅ `kernel_module.so`
- ✅ `init.so`

## Tools in /bin die Gregor hat

`cat`, `cd`, `ls`, `ps`, `pwd`, `rm`, `ifconfig`, `iwconfig`, `iwlist`, `crypto.so`, `metaxploit.so`, `init.so`, `net.so`

**NICHT vorhanden in /bin**: `ssh`, `nmap`, `build`, `wget` — diese sind erst später im Spiel freigeschaltet oder müssen via `apt-get install` beschafft werden.

**ABER**: `shell.connect_service()` funktioniert auch ohne `ssh`-Binary!

## In-Game Test-Ergebnisse (Verifiziert)

### FileSystem funktioniert im echten Spiel

```
pc = get_shell.host_computer
passwd = pc.File("/etc/passwd")
print(passwd.get_content)
// → root:32af928a892ba8501894ab3e531db730
// → gregor:32af928a892ba8501894ab3e531db730
```

**Wichtig**: Das Passwort von root und gregor ist identischer Hash → sie haben das gleiche Passwort!

### SSH-Zugriff zu Dee Grettib (199.229.146.172)

```
shell = get_shell.connect_service("199.229.146.172", 22, "root", "agle1")
// → Shell erfolgreich!

dee = shell.host_computer
passwd = dee.File("/etc/passwd").get_content
// → root:ced2809f5ea305d9df169b744d5a5d23
// → Treraz:fa368a40355bfa96b962825da0e19915
// → Browan:91d1a3816ed8d2dff948ff4b3f377e8c
```

**Aber**: Die User auf Dee heißen **nicht** `dee` — sondern `Treraz` und `Browan`! `agle1` hat trotzdem funktioniert — vermutlich war das nicht das Passwort für root, sondern für einen der anderen Users.

Dee's User haben **andere** Passwort-Hashes als Gregor → `agle1` war ein gültiges Passwort für einen der Users.

### Mission: Login Credentials für 16.174.201.225 (172.16.5.4)

Gregor bekam eine Mission: Finde Login Credentials für `16.174.201.225`.

**Ergebnis**:
- Router erreichbar ✅
- Metaxploit Port 21 (FTP) lieferte Vulnerabilities ✅
- Exploit "Essigna @ 0x1784DF8F" lieferte Shell als User `ingussin` ✅
- `/etc/passwd` → Permission denied (nicht-root User!)
- `/home` durchsuchen als Alternative für Creds

## mock-Env vs Echter Spiel — Bekannte Limitations

| Feature | Mock-Env | Echter Spiel |
|---------|----------|--------------|
| `pc.public_ip` | Dummy-IP (z.B. `142.32.54.56`) | Echte IP des Spielers |
| `pc.get_content` | ❌ Gibt nie Inhalt zurück | ✅ Liefert Dateiinhalt |
| `crypto.decipher()` | ❌ Nicht implementiert | ✅ Funktioniert |
| `connect_service()` externe IPs | ❌ "can't connect: port closed" | ✅ Funktioniert |
| `metax.net_use()` externe IPs | ✅ Liefert Session + Vulnerabilities | ✅ Funktioniert |
| `lib.overflow()` | ✅ Liefert Shell | ✅ Funktioniert |
| `is_folder` | ✅ Funktioniert | ✅ Funktioniert |
| `get_files` / `get_folders` | ✅ Funktioniert | ✅ Funktioniert |

**Fazit**: Mock-Env ist gut für Syntax-Tests und Metaxploit-Workflow-Tests, aber **nicht** für echte Hack-Resultate. Immer final im Spiel testen.

## Greybel-js Syntax-Regeln (erneut bestätigt)

1. **`//` Kommentare**: ✅ Erlaubt
2. **`=======` als Separator**: ❌ Build-Error → "Punctuator where expression expected"
3. **Backslash in Strings `\"`**: ❌ In manchen Kontexten Build-Error
4. **One-line `if X then Y end if`**: ❌ Build-Error → multi-line verwenden
5. **Verschachtelte if/else**: ✅ Funktioniert wenn korrekt geöffnet/geschlossen
6. **`string()` Funktion**: ❌ Existiert nicht in GreyScript → `str()` verwenden

## Decipher-Regel

`crypto.decipher(hash)` funktioniert **NICHT** in einer SSH-Session (wird als "SSH encryption process" erkannt). Hashes müssen zum lokalen Computer kopiert und dort entschlüsselt werden.

## Exploit-Extraktion aus scan_address Output

Der Output von `metax.scan_address()` enthält "Unsafe check:" Segmente. Jedes Segment kann einen Exploit-Namen enthalten:

```
segments = addr.split("Unsafe check:")
// segments[0] = Header
// segments[1..N] = Exploits

for segment in segments[1:]
    labelStart = segment.indexOf("<b>")
    labelEnd = segment.indexOf("</b>")
    hasStar = segment.indexOf("*") != null  // * = hat Anforderungen
    
    if labelStart != null and labelEnd != null then
        exploit = segment[labelStart + 3: labelEnd]
        result = lib.overflow(area, exploit)
        if typeof(result) == "shell" then
            // SHELL!
        end if
    end if
end for
```

**Wichtig**: Exploits mit `*` haben zusätzliche Anforderungen (bestimmte Libraries, Port-Forwarding, User-Typen). Ohne `*` sind "zero-requirement" Exploits.
