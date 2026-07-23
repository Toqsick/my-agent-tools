# Mock-Env Port Guard Chain (NP-68 + 2026-07-14 update)

## Pitfall

Port-Handling muss **beide** Formen verkraften:

| Quelle | `typeof(p)` | Eigenschaften |
|--------|-------------|---------------|
| Live GreyHack + greybel Mock (2026-07-14) | **`"port"`** (native) | `p.port_number`, `p.is_closed`, `p.get_lan_ip` — **kein** `hasIndex` |
| Manche Wrapper / alte Dokus | `"map"` | Keys via `hasIndex("port_number")` etc. |

Service-Name kommt oft **nicht** am Port, sondern am Router:

```greyscript
svc = router.port_info(p)   // z.B. "ssh 1.0.0"
```

## Empfohlene Guard-Kette (Starter yuno_nscan / portscan)

```greyscript
readPort = function(p, router)
	info = {}
	info["num"] = "?"
	info["svc"] = "?"
	info["closed"] = false
	info["lan"] = ""
	if p == null then
		return info
	end if
	if typeof(p) == "map" then
		if p.hasIndex("port_number") then
			info["num"] = p["port_number"]
		end if
		if p.hasIndex("is_closed") then
			info["closed"] = p["is_closed"]
		end if
		if p.hasIndex("service") then
			info["svc"] = p["service"]
		end if
	else if typeof(p) != "string" and typeof(p) != "number" then
		// native Port-Objekt (Mock + Game)
		info["num"] = p.port_number
		info["closed"] = p.is_closed
		info["lan"] = p.get_lan_ip
		if router != null and typeof(router) != "string" then
			pinfo = router.port_info(p)
			if typeof(pinfo) == "string" and pinfo != "" then
				info["svc"] = pinfo
			end if
		end if
	end if
	return info
end function
```

## Anti-Patterns

| ❌ Falsch | Warum |
|----------|--------|
| `p.hasIndex("port_number")` bei `typeof="port"` | hasIndex ist Map-API |
| `p.indexOf("service")` | indexOf nur String/List |
| `router = pc.network_gateway` dann `router.device_ports` | gateway oft **IP-String** |
| Nur Map-Guard `if typeof(p) != "map" then continue` | skippt alle echten Port-Objekte |

Siehe NP-68 in `references/known-bugs.md` + Starter-Kit Debug 2026-07-14.