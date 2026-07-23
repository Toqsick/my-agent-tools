# GreyScript Library Catalog (Live-DB Verified)

> **Quelle:** Live-Extraktion aus `GreyHackDB.db → Map.LibVersions` (50 Map-Einträge gesampelt, 20 unique Libraries mit MD5-Hash belegt)
>
> **Vollständiger Katalog:** `~/Dokumente/Obsidian Vault/09 System-Doku/GreyHack/GreyHack-Lib-Katalog-2026-07-14.md`
> (1113 Zeilen — Funktionen-Tabellen, Beispiele, Pitfalls pro Library)
>
> **Dieses File ist der schnelle Einstieg:** Library-Liste, Hashes, Methodik, essentielle Signatures.

## Live-DB Extraction Method

```bash
# 1. Identify game DB location
find ~ -name "GreyHackDB.db" 2>/dev/null
# → /mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db

# 2. Extract library versions from Map table entries
sqlite3 GreyHackDB.db "SELECT substr(value, 1, 8000) FROM Map LIMIT 50;" | \
  python3 -c "
import sys, json
data = sys.stdin.read()
libraries = {}
for line in data.strip().split('\n'):
    if not line: continue
    try:
        parsed = json.loads(line.split('\t')[0].split('___')[0] if '___' in line else line)
        libs = parsed.get('libVersions', {})
        for lib, hash_val in libs.items():
            if lib not in libraries:
                libraries[lib] = hash_val
    except: pass
for lib in sorted(libraries.keys()):
    print(f'{lib}: {libraries[lib]}')
"
```

## Library Inventory (20 Libraries with Live Hashes)

| # | Library | Path | MD5 Hash (Beispiel) | Klasse |
|---|---------|------|---------------------|--------|
| 1 | **libssh.so** | `/lib/libssh.so` | `38cab371eb3930d23b9913c8ea0f1f77` | Network Protocol |
| 2 | **libftp.so** | `/lib/libftp.so` | `2b2d632bd87cef6aa0aa4edbce0383be` | Network Protocol |
| 3 | **libhttp.so** | `/lib/libhttp.so` | `7ee0f3bf3c51cc7444c709a983a8cd02` | Network Protocol |
| 4 | **libsql.so** | `/lib/libsql.so` | `3758e220b3971dd7d2a180a464b6da8f` | Database |
| 5 | **libsmtp.so** | `/lib/libsmtp.so` | `6d7a0a43c7d2f04d420b8674430c553d` | Network Protocol |
| 6 | **libchat.so** | `/lib/libchat.so` | `dcbccc04d2337212f1c2e128ff1f3071` | Communication |
| 7 | **libcam.so** | `/lib/libcam.so` | `141fdb116dff4cff0a2bef32479546e5` | Surveillance |
| 8 | **librshell.so** | `/lib/librshell.so` | `19abb85d4f9b4b5b413cdc02215b89b0` | Backdoor Service |
| 9 | **librepository.so** | `/lib/librepository.so` | `bb5da71c220517f80c5111a26a5c5df4` | Storage |
| 10 | **blockchain.so** | `/lib/blockchain.so` | `35b702aa9d74e46fb8ac0f8dd51a3cdf` | Crypto |
| 11 | **libadb.so** | `/lib/libadb.so` | `b2a07d621df59e97b7916c2eca6f5013` | Android Debug |
| 12 | **libsmartappliance.so** | `/lib/libsmartappliance.so` | `8dc48fc33e92aae92e1a0d7115864436` | IoT |
| 13 | **kernel_router.so** | `/lib/kernel_router.so` | `96264d17280b74155e7343cc86553122` | System — Router |
| 14 | **aptclient.so** | `/lib/aptclient.so` | `472d32aeb239bdbf454df46f8a3363e3` | System — Package |
| 15 | **metaxploit.so** | `/lib/metaxploit.so` | `ae09b8dc149aa96daea6b6cb8d4f9d0e` | System — Exploit |
| 16 | **crypto.so** | `/lib/crypto.so` | `c9763876bd6a881542b89cb7ba7630eb` | System — Crypto |
| 17 | **kernel_module.so** | `/lib/kernel_module.so` | `3083b2c1e69e1905dad76c019ba718d3` | System — Kernel |
| 18 | **init.so** | `/lib/init.so` | `50d6b65a8636b83ef7f3c9677dce259a` | System — Init |
| 19 | **net.so** | `/lib/net.so` | `8a01cb5bdb3c9ff4cff0f928945a558f` | System — Network |
| 20 | **libtrafficnet.so** | `/lib/libtrafficnet.so` | `37108b1ddbdce076c605d3d2bea4c47f` | Government/Police |

**System Defaults (loadable on any computer without purchase):** `libssh.so`, `libftp.so`, `libhttp.so`, `libsql.so`, `libsmtp.so`, `libchat.so`, `libcam.so`, `libadb.so`, `libsmartappliance.so`, `librepository.so`, `libtrafficnet.so`, `kernel_router.so`, `kernel_module.so`, `init.so`, `net.so`, `aptclient.so`

**HackShop-only (must purchase in-game):** `crypto.so`, `metaxploit.so`, `blockchain.so`, `librshell.so` (Service)

## Key Library Signatures (not covered in api-objects.md)

### `librshell.so` — Reverse Shell Service
```greyscript
// Service-side (Opfer): Stellt Verbindung zum Angreifer her
svc = shell.connect_service(YOUR_PUBLIC_IP, 4444, "user", "pass")
// Angreifer-seitig: Empfängt reverse connection
// Kein GreyScript-Call — läuft als Service Process
```
- **Zweck:** Opfer-Prozess verbindet kontinuierlich zurück zum Angreifer
- **Wichtig:** Funktioniert durch Firewalls/NATs da Outbound-Connection
- **Basti-Nutzung:** Kernbibliothek für Vault-Persistenz (siehe `references/hermes-gh-api-server.md`)
- **Service, keine Library:** `include_lib` lädt sie, aber genutzt wird sie via Service-Connection

### `kernel_router.so` — Router Exploitation
```greyscript
// Overflow hat dritten LAN-IP-Parameter (community-discovered)
result = lib.overflow(memAddr, unsecValue, targetLanIp)
```
- **Return:** Shell-Objekt (voller Router-Zugriff) oder String (Fehler)
- **Stateful:** Ein misslungener Overflow blockiert den Router für ~1 Spielstunde (Cooldown)
- **Einstieg:** Erfordert bereits Gast-Zugriff auf den Zielrechner

### `kernel_module.so` — Local Privilege Escalation
```greyscript
// ClassID: kernel_module
result = lib.overflow(address, value)
// Return: Shell (root), Computer, File, String, oder Number
```
- **Zweck:** Lokale Privilege-Escalation (User → Root)
- **Voraussetzung:** Bereits Remote-Shell auf dem Ziel
- **Return-Typ wechselt abhängig vom Exploit** — `typeof` zwingend

### `blockchain.so` — Crypto Wallets
```greyscript
bc = include_lib("/lib/blockchain.so")
wallet = bc.wallet_by_pass(passPhrase)
// oder
wallet = bc.wallet_all_dat([])
// Wallet Methods:
//   wallet.address → string
//   wallet.balance → number
//   wallet.send(value, address) → string (transaction ID oder Fehler)
```
- **HackShop-only** — nicht im System-Default
- **Wallet-Findung:** `wallet_by_pass` für bekanntes Passwort, `wallet_all_dat` scannt Daten-PCs
- **Transaktionen:** Alle Blockchain-Transaktionen sind öffentlich einsehbar (In-Game-Log)

### `init.so` — System Initialization
```greyscript
// ClassID: init
// Keine öffentlichen Remote-Funktionen
// Angriffsoberfläche: metalib.overflow(address, value) via metaxploit.so
```
- **Zweck:** System-Boot- und Init-Prozesse
- **Keine eigenen Call-Funktionen** — nur via metaxploit overflow angreifbar
- **Ziel von `init.overflow`:** Shell auf dem Ziel (erster Einstiegspunkt)

### `net.so` — Network Stack
```greyscript
// ClassID: net
// Keine dokumentierten Remote-Funktionen
// Nutzbar via metaxploit overflow für Netzwerk-Exploits
```
- **Zweck:** Low-Level-Netzwerk-Stack des Zielhosts
- **Nutzen:** Local-Exploit für laterale Bewegung im Netzwerk

### `libadb.so` — Android Debug Bridge
```greyscript
// Vollständige Signatures nur über In-Game-Manual
// Nutzbar via metaxploit overflow
```
- **Live-Hash belegt Existenz**
- Konkrete Signatures nur teilweise öffentlich dokumentiert
- **Pitfall:** Kamera-Zugriff (`libcam.so`) ist in fast allen Versionen ans lokale Heimnetz gebunden

### `libsmartappliance.so` — IoT Devices
- **HackShop-only**
- Nutzung für IoT-Botnets und Smart-Home-Exploitation
- Begrenzte öffentliche Dokumentation

### `libtrafficnet.so` — Government/Police Networks
- **HackShop-only**
- Zugriff auf Verkehrs-Kameras, Vehicle-Locate
- Behörden-Netzwerke mit höheren Security-Ständen

## Key Signatures from `documentation.greyscript.org`

### `libssh.so`
| Method | Parameters | Return | Description |
|--------|-----------|--------|-------------|
| `connect` | (ip, pass, ?user) | Shell or null | SSH-Verbindung |
| `connect_pkey` | (ip, pkey) | Shell or null | Public-Key SSH |
| `connect_port` | (ip, port, pass, ?user) | Shell or null | SSH auf non-Standard-Port |

### `libftp.so`
| Method | Parameters | Return | Description |
|--------|-----------|--------|-------------|
| `connect` | (ip, port, user, pass) | FTPSession or null | FTP-Verbindung |
| `connect_anonymous` | (ip, port) | FTPSession or null | Anonymer Zugriff |

### `libhttp.so`
| Method | Parameters | Return |
|--------|-----------|--------|
| `get` | (ip, port) | HttpResponse |
| `put` | (ip, port, data) | HttpResponse |
| `head` | (ip, port) | HttpResponse |

### `libsql.so`
| Method | Parameters | Return |
|--------|-----------|--------|
| `query` | (ip, port, user, pass, query) | List or null |
| `get_tables` | (ip, port, user, pass) | List or null |
| `test_connection` | (ip, port) | string or null |

### `libsmtp.so`
| Method | Parameters | Return |
|--------|-----------|--------|
| `send_mail` | (ip, port, from, to, subject, body) | Bool or null |
| `enum_users` | (ip, port, userList) | List or map |

### `libchat.so`
| Method | Parameters | Return |
|--------|-----------|--------|
| `join_channel` | (svc, channel, nick) | ChatSession or null |
| `get_messages` | (since) | List or null |

## Cross-Library Pitfalls

| Pitfall | Detail |
|---------|--------|
| **Null-check all includes** | `include_lib` kann `null` zurückgeben. `if not lib then exit("fehler")` |
| **Triple-type returns** | Viele Library-Funktionen geben string/null/list zurück. `typeof()` vor Folge-Operation |
| **`0` ist truthy** | `if result then` matched auch `0`/`""`. Verwende `if result != null then` |
| **Eigene Tools ≠ Libraries** | Eigener Code via `import_code`, System-Libraries via `include_lib`. Vermischung baut nicht |
| **HackShop-Only** | `crypto.so`, `metaxploit.so`, `blockchain.so`, `libadb.so`, `libsmartappliance.so`, `librshell.so`, `libtrafficnet.so`, `librepository.so` — müssen gekauft werden |
| **Exploit-Cleanup** | Nach Exploit: Log leeren, eigene Files löschen, disconnect |
| **Library-Versionen** | Verschiedene Versionen = verschiedene Exploits. `meta.scan` je Ziel wiederholen |
| **Memory-Adressen** | `0x...` absolute Werte aus `scan_address` direkt übernehmen |