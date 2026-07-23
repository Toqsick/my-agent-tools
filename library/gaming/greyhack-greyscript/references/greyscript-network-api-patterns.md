# GreyScript Network API Patterns

*Session 2026-07-04: yuno_viper_net.src* — Konkrete API-Aufrufe für Netzwerk-Module, getestet gegen existierende Skripte im Repo.

## Router-Zugriff (lokal vs. remote)

**P0 (verified 2026-07-14 Mock + greyscript-meta):** Für Router-**Objekte** IMMER `get_router` (optional mit IP) nutzen.

```greyscript
// ✅ LOKALER Router-Object
router = get_router
if router == null or typeof(router) == "string" then
	print("[FAIL] kein Router")
	return
end if

// ✅ Router für Target-IP (meta API: get_router([ip]))
router = get_router(targetIp)

// ⚠️ pc.network_gateway ist oft nur die IP als STRING (Mock: typeof="string")
//    — NIEMALS darauf .device_ports / .devices_lan_ip aufrufen!
//    Höchstens als IP-Hinweis, nicht als Router-Objekt.

// Remote Shell/Service: connect_service
// Liefert STRING bei Fehler, nicht null!
sh = get_shell
connection = sh.connect_service(ip, 22, "root", "", "ssh")
if typeof(connection) == "string" then
	print("[!] Connection failed: " + connection)
	return null
end if
// connection ist Shell/Service — nicht automatisch "router"
```

**Defensiver Wrapper (Starter-Standard 2026-07-14):**
```greyscript
safeRouter = function
	r = get_router
	if r == null then
		return null
	end if
	if typeof(r) == "string" then
		return null
	end if
	return r
end function
```

**Legacy note:** Älterer `network_gateway`-Code (yuno_viper_net 2026-07-04) war unvollständig abgesichert. Bevorzugte Pattern heute: `get_router` + typeof string-guard.

## whois_info(ip)

GreyHack-Router haben eine `whois_info(ip)`-Methode. Rückgabe-Typ variiert:
- **String** bei einfachen Antworten
- **Map** mit Schlüsseln bei strukturierten Daten
- **null** bei Fehler/nicht erreichbar

```greyscript
data = router.whois_info(target)
if data == null then
    // Keine whois-Daten
else if typeof(data) == "string" then
    out["raw"] = data
else if typeof(data) == "map" then
    for k in data.indexes
        out["raw_" + str(k)] = str(data[k])
    end for
end if
```

## PortSniffer

Der `PortSniffer` ist eine built-in Klasse (keine `include_lib` nötig):

```greyscript
sn = new PortSniffer
if sn == null then return {"error": "PortSniffer nicht verfuegbar"} end if

// Start: Methodenname variiert zwischen greybel und in-game
ok = false
if typeof(sn).hasIndex("start_sniffer") then
    ok = sn.start_sniffer(router, port)
else if typeof(sn).hasIndex("start") then
    ok = sn.start(router, port)
end if

// Auslesen: session_list liefert Liste von Paket-Maps
wait(sec) // Sniffer braucht Zeit zum Sammeln
hits = []
if typeof(sn).hasIndex("session_list") then
    sess = sn.session_list
    if sess != null and typeof(sess) != "string" then
        for s in sess
            hits.push(str(s))
        end for
    end if
end if

// Stopp: stop_sniffer (wenn vorhanden)
if typeof(sn).hasIndex("stop_sniffer") then sn.stop_sniffer end if
```

**Pitfalls:**
- `start_sniffer(router, port)` statt `start_sniffer(port)` — das `router`-Argument ist zwingend
- `session_list` kann `null` oder leer sein, wenn keine Pakete kamen
- `stop_sniffer` muss nicht existieren (greybel-Unterschied)
- Wait-Zeit: 3–10 Sekunden sind realistisch; mehr als 30 bringt kaum Zusatzertrag

## trace_route(ip)

Auf dem Host-Computer (nicht direkt am Router):

```greyscript
pc = get_shell.host_computer
if typeof(pc).hasIndex("trace_route") then
    res = pc.trace_route(target)
end if

// Ergebnis: Liste von Hop-Einträgen (Maps oder Strings)
normalized = []
for h in hops
    e = {}
    if typeof(h) == "map" then
        for k in h.indexes
            e[k] = h[k]
        end for
        if not e.hasIndex("hop") then e["hop"] = normalized.len + 1 end if
    else
        e = {"hop": normalized.len + 1, "addr": str(h)}
    end if
    normalized.push(e)
end for
```

**Rückgabe:** `null` bei Fehler, String bei Fehlermeldung, Liste von Hops bei Erfolg.

## device_ports(ip) — Portscan

Router-Methode. Methodenname variiert:

```greyscript
ports_raw = null
if typeof(router).hasIndex("device_ports") then
    ports_raw = router.device_ports(ip)
else if typeof(router).hasIndex("used_ports") then
    ports_raw = router.used_ports
end if

// ports_raw ist eine Liste von Maps mit Keys:
//   "port_number" (Integer oder null)
//   "is_closed" (Boolean)
//   "version" (String)
//   "service" (String)

// Defensiv iterieren:
for p in ports_raw
    if typeof(p) != "map" then continue end if
    is_closed = false
    if p.hasIndex("is_closed") then is_closed = p["is_closed"] end if
    num = null
    if p.hasIndex("port_number") then num = p["port_number"] end if
end for
```

## devices_lan_ip — LAN-Topologie

Router-Property, liefert Liste der LAN-IPs (Strings):

```greyscript
devices = router.devices_lan_ip
// Kann null oder String (Fehler) sein
if devices == null or typeof(devices) == "string" then
    // Keine LAN-Geräte
else
    for d in devices
        print(str(d)) // jeder Eintrag ist eine IP als String
    end for
end if
```

## BFS LAN Topologie Crawl (depth 1–3)

Pattern für rekursive Topologie-Erkennung:

```greyscript
visited = {}
visited[router.local_ip] = true
current = [router.local_ip]
level = 1
while level <= depth
    next_lvl = []
    for parent_ip in current
        parent_router = null
        if parent_ip == router.local_ip then
            parent_router = router  // lokal — kein connect nötig
        else
            // Remote-Router via SSH
            tmp = get_shell.connect_service(parent_ip, 22, "root", "", "ssh")
            if tmp != null then parent_router = tmp end if
        end if
        if parent_router == null then continue end if
        devices = parent_router.devices_lan_ip
        if devices == null or typeof(devices) == "string" then continue end if
        for d in devices
            d_str = str(d)
            if not visited.hasIndex(d_str) then
                visited[d_str] = true
                next_lvl.push(d_str)
                // Knoten + Kante zu nodes/edges hinzufügen
            end if
            edges.push({"from": parent_ip, "to": d_str})
        end for
    end for
    current = next_lvl
    level = level + 1
end while
```

**Grenzen:** depth > 3 ist in der Praxis zu langsam (jeder Level = N× SSH-Connects).

## Chat via /lib/chat.so

```greyscript
lib = include_lib("/lib/chat.so")
if lib == null then
    lib = include_lib(current_path + "/chat.so")  // Fallback
end if
if lib == null then return {"error": "chat.so nicht ladbar"} end if

// Services auflisten (öffentliche Chat-Server)
svcs = lib.services  // Liste von Service-Objekten/Strings

// Channel beitreten
if typeof(lib).hasIndex("join_channel") then
    joined = lib.join_channel(service, channel, nick)
else if typeof(lib).hasIndex("connect") then
    joined = lib.connect(service, channel, nick)
end if

// Nachricht senden
if typeof(lib).hasIndex("send_message") then
    lib.send_message(channel, msg)
else if typeof(lib).hasIndex("post") then
    lib.post(channel, msg)
end if
```

## Botnet-Pattern (In-Memory + JSON-Persistenz)

```greyscript
// Initialisierung
if not globals.hasIndex("_yvn_botnet") then globals["_yvn_botnet"] = [] end if

// Eintrag hinzufügen
globals["_yvn_botnet"].push({"name": name, "ip": ip, "user": user, "pass": pass})

// C2 via connect_service + shell.exec
remote = get_shell.connect_service(target["ip"], 22, target["user"], target["pass"], "ssh")
if remote == null then return {"error": "connect_service fehlgeschlagen"} end if
out = remote.host_computer.shell.exec(cmd)
remote.close
```

## Module Development Conventions (aus yuno_viper)

| Convention | Beschreibung |
|-----------|-------------|
| `yvn_` Prefix | Projekt-Prefix zur Kollisionsvermeidung mit anderen Modulen |
| `yvn_print_map()` | Generischer Map-Printer: druckt `key: value` aus einer Map, zeigt `error`-Keys rot |
| `yvn_sep()` / `yvn_header()` | Standardisierte Ausgabe: Trennlinie + Überschrift |
| CLI Dispatcher | `args = params` → `if args.len == 0 then help()` → `else if args[0] == "cmd" then` |
| Error-as-Map | Jede Funktion gibt `{"error": "..."}` bei Fehler, `{"ok": true, ...}` bei Erfolg |
| String/typeof-Guards | Jeder API-Call wird mit `typeof()` auf null/String/erwarteten Typ geprüft |

### Dispatcher Template

```greyscript
args = params
if args == null then args = [] end if

if args.len == 0 or args[0] == "-h" then
    help_fn()
else if args[0] == "cmd1" then
    print_map("cmd1", cmd1_fn(args[1]))
else if args[0] == "cmd2" then
    cmd2_fn(args[1], args[2])
end if
```
