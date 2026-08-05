# Tool Reference — mcp-server-basti

## Tools

Alle Tools advertise `readOnlyHint=True` (keine Mutationen) und — außer `echo_tool` —
`tags={"system","read-only"}`. Strukturierte Rückgaben sind TypedDicts aus
`src/mcp_server_basti/schemas.py`; FastMCP leitet das JSON-Schema automatisch ab und
liefert das Ergebnis als `structuredContent`.

| Tool | Parameter | Rückgabetyp | Beschreibung | Side-Effect |
|------|-----------|-------------|--------------|-------------|
| `get_system_status` | keine | `SystemStatus{uptime: str}` | Führt `uptime` aus. | read (Subprocess) |
| `echo_tool` | `text: str` (required) | `str` (roh) | Health-Check, gibt Text unverändert zurück. | none |
| `get_repo_info` | keine | `RepoInfo{branch,last_commit,detached}` | Git-Branch + letzter Commit des Server-Repos (`DEFAULT_REPO_PATH`). | read (git-Subprocess) |
| `get_disk_status` | keine | `DiskStatus{filesystems: [Filesystem]}` | `df -h --output=...` über alle Dateisysteme. | read |
| `get_gpu_status` | keine | `GpuStatus{...}` | `nvidia-smi` Treiber/Temp/Auslastung/VRAM + `-q -d POWER` (power_* evtl. `None`). | read |
| `get_memory_status` | keine | `MemoryStatus{free,zram,swaps}` | `free -h` + `zramctl` + `swapon --show` (rohe Text-Blöcke). | read |
| `get_failed_units` | keine | `FailedUnits{failed: [str], raw: str}` | `systemctl --failed` (gefiltert auf echte Unit-Namen). | read |
| `get_kernel_warnings` | keine | `str` (roh) | `journalctl -b -p warning` (bewusst unparseiert). | read |
| `get_boot_timing` | keine | `BootTiming{blame: [BlameEntry], critical_chain: str}` | `systemd-analyze blame` + `critical-chain`. | read |
| `get_power_profile` | keine | `PowerProfile{profile: str}` | `powerprofilesctl get`. | read |
| `get_firewall_state` | keine | `FirewallState{ufw, listening_ports}` | `sudo -n ufw status verbose` + `ss -tlnp`; benötigt NOPASSWD-sudoers-Regel (siehe `SUDOERS_SETUP.md`). | read (sudo, eng begrenzt) |

## Beispiele

### get_system_status

**Input:** keine Parameter

**Output (beispielhaft, Linux):**
```
 04:24:40 up  2:46,  1 user,  load average: 9,64, 8,19, 6,85
```

> Format hängt vom Betriebssystem ab. Der Server gibt den rohen `uptime`-stdout zurück.

### echo_tool

**Input:**
```json
{"text": "hello"}
```

**Output:** `hello` (roher String, beliebiger Text inkl. Leer/Unicode round-trip-t).

### get_repo_info

**Input:** keine Parameter

**Output (beispielhaft, attached):**
```json
{"branch": "main", "last_commit": "634ff36 Merge pull request #1 ...", "detached": false}
```

**Detached HEAD:** Im detached-HEAD-State scheitert `git symbolic-ref --short HEAD`
(non-zero); das Tool fällt auf `git rev-parse --short HEAD` zurück und liefert
`branch: "detached@<short-sha>"`, `detached: true`.

> Ruft `git symbolic-ref --short HEAD` (mit `rev-parse --short`-Fallback) und
> `git log -1 --oneline` für das Server-Repo auf. Kein Remote, keine Tags.

### get_firewall_state

**Voraussetzung:** installierte NOPASSWD-sudoers-Regel — siehe `SUDOERS_SETUP.md`.
Ohne die Regel degradiert der Aufruf zu einem `ToolError`, der auf jene Datei verweist
(kein stiller Partial-Result). Das Tool ist dennoch immer advertised (Discovery ist
statisch); nur die *Ausführung* benötigt die Regel.

**Output (beispielhaft):** rohe Text-Blöcke für UFW-Status und `ss -tlnp`.

## Fehlerformat

Tool-Errors werden als **`ToolError`-Exception** signalisiert. Der mcp-lowlevel-Pfad
baut die Wire-Antwort in `mcp/server/lowlevel/server.py`; nur Exceptions werden zu
`CallToolResult(isError=True)`. Normale Return-Werte werden pauschal mit
`isError=False` gewrappt — deshalb raise statt `return ToolResult(is_error=True)`.

```json
{
  "isError": true,
  "content": [{"type": "text", "text": "Systemstatus konnte nicht ermittelt werden: ..."}]
}
```

## skill-mcp-router Integration

Der Server ist für die Integration mit dem bestehenden `skill-mcp-router` vorbereitet, aber **noch nicht aktiv verdrahtet**. Die `routing/registry/registry.json` hat ein `mcp_server`-Feld pro Skill, in das `"mcp-server-basti"` eingetragen werden kann, um Skill-Intents zu diesen Tools aufzulösen.

**Status:** Derzeit nutzt kein Skill in der Registry den Server `mcp-server-basti`. Um ihn zu aktivieren, müssten Skills mit passenden Intents angelegt und in der Registry registriert werden. Siehe `routing/registry/registry.json` für das Format.