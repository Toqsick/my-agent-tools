# Wire-Capture Bulk Analysis — Process Talkers & Connection Baseline

## When to use

You have a pre-recorded `ss -tupn` capture log (multiple snapshots, e.g. 2-s interval over 1+ hours, 100k+ rows) and need to:
- Identify which processes are the top talkers (by unique connection count)
- Establish a baseline of expected vs unusual communication partners
- Detect orphan connections (rows without `users:(())` metadata)
- Produce a reproducible, data-backed report

## Real example

17.6 MB capture, 3,091 snapshots × ~34 conn/snapshot, 1 h 43 min duration (2026-07-14).  
104,847 connection rows parsed → 19 distinct process owners → baseline per process.

## Structure

### Step 1: Understand the file format

```
2026-07-14T23:42:48+02:00          ← snapshot timestamp
tcp   ESTAB  0  0  LOCAL_IP:PORT  REMOTE_IP:PORT  users:(("name",pid=N,fd=M))
udp   ESTAB  0  0  ...            ...             users:(("name",pid=N,fd=M))
...                                ← ~34 rows per snapshot
---                                ← separator (not always present, use timestamp lines instead)
2026-07-14T23:42:50+02:00          ← next snapshot timestamp
```

### Step 2: Snapshot detection

```python
import re
TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
ROW_RE = re.compile(r'^(tcp|udp|raw)\s')
```

- `TS_RE` matches ISO timestamps → snapshot counter
- `ROW_RE` matches connection rows → process counter  
- Lines `---` are separators, skip them.

### Step 3: Owner extraction

**PITFALL:** `users:((` has **nested parentheses** in the `ss` output.  
A single `re.search(r'users:\(\(...')` will NOT match correctly because the
outer group expects inner groups that may not align with the capturing-engine
state. Use `re.findall` on the **inner** pattern instead:

```python
USER_RE = re.compile(r'\("([^"]+)",pid=(\d+),fd=\d+\)')
users = USER_RE.findall(line)   # returns [("name", "pid"), ...]
```

This works because `findall` iterates over **all** non-overlapping occurrences of the
inner parentheses pattern, ignoring the outer `users:((` wrapper.

**Multiple owners per row:** Some rows contain multiple `users:((...))(...)`, e.g.
`users:(("git",pid=74378,fd=3))users:(("git-remote-http",pid=71592,fd=28))`.  
`findall` captures both correctly.

### Step 4: Deduplication across snapshots

Same connection appearing in N snapshots → count as **1 unique connection**:

```python
proc_unique_conns[name].add(
    (proto, local_addr, local_port, remote_addr, remote_port, pid)
)
```

This gives you the **true fan-out** per process: how many distinct peers it talks to,
not how many times the connection was sampled.

### Step 5: Remote IP heuristic

`ss -tupn` layout: IPs appear in order **local then remote**.  
Extract all IPs with regex, take the **last** as remote:

```python
IPV4_RE = re.compile(r'(?<![\[\w])((?:\d{1,3}\.){3}\d{1,3}):(\d+)')
IPV6_RE = re.compile(r'\[([0-9a-fA-F:]+)\]:(\d+)')

v4_hits = IPV4_RE.findall(line)   # [(ip, port), ...] in line order
v6_hits = IPV6_RE.findall(line)   # [(ip, port), ...] in line order

# Last IP overall = remote
all_addrs = [(ip, port, 4) for ip,port in v4_hits] + [(ip, port, 6) for ip,port in v6_hits]
local = all_addrs[0]   # first = local (host's own IP)
remote = all_addrs[-1] # last = remote (peer)
```

**Verification:** Check that the local IP appears in `ip addr show` output.

### Step 6: Orphan row analysis

Orphan rows = lines without `users:(())` info.  
These are **not** data leaks — they're sockets in transition states (`LAST-ACK`,
`CLOSE-WAIT`, `TIME-WAIT`, `FIN-WAIT`) where the kernel briefly drops the
owner-process metadata.

**Expected ratio:** ~11 % of total rows is normal (observed in real capture).

Extract orphan destinations for completeness:

```python
orphan_v4 = Counter()
orphan_v6 = Counter()
for line in capture:
    if not ROW_RE.match(line): continue
    if USER_RE.findall(line): continue   # skip rows that DO have owners
    # ... extract remote IPs as above, each line = +1 to orphan counter
```

**Top orphan peers** often match a top talker's primary peer — confirming they're
the same connection, just sampled mid-state-transition.

### Step 7: Report structure

```
## Top-N processes by unique connections

| rank | process | highest pid | unique conns |
|------|---------|-------------|-------------|
| 1    | hermes  | 223141      | 494          |
| ...

## Destinations per process

### process (highest pid=N)
- IPv4 destinations: M unique
- IPv6 destinations: N unique
- top-3 IPv4 by row-count: IP1 (C rows), IP2 ...
- top-3 IPv6 by row-count: IP1 (C rows), IP2 ...

## Full process list

| process | pids seen | conns | v4-IPs | v6-IPs |
|---------|-----------|-------|--------|--------|
| name    | pid1,pid2 |  N    |   M    |   K    |

## Orphan rows
- total: X (Y% of rows)
- top orphan IPv4: IP1 (C), IP2 ...
- top orphan IPv6: IP1 (C), IP2 ...

## Anomalies (takeaways)
- List unexpected peers per process
- Cross-reference with `ipinfo.io` for suspicious IPs
- Flag processes with unusual fan-out or single-peer dominance
```

## Known patterns & interpretations

| Pattern | Interpretation |
|---------|---------------|
| Single peer dominates 90%+ of a process's rows | Likely persistent connection (WebSocket, SSE stream, long-poll). Normal. |
| Process talks to 40+ unique IPv4 + IPv6 peers | Browser (normal fan-out: CDN, trackers, extensions) |
| Process talks exclusively to Docker bridge GW (`2607:6bc0::10`) | Inbound-only service behind a proxy/container. Traffic is tunneled, not direct. |
| High orphan count for a single IP | That IP's socket transitions states frequently (reconnect, keepalive expiry) — same process as the non-orphan rows. |

## Pitfalls

1. **Nested `users:(()` regex trap:** Always use `findall` on the **inner** pattern `\("([^"]+)",pid=(\d+),fd=\d+\)`. A `search()` on the outer `users:\(\(...\)\)` will fail because Python's regex engine counts the outer `\(\(` but the inner groups may not align for the `)?` quantifiers.

2. **First-IP heuristic:** Relies on `ss -tupn` field order. Works for standard output. If the file was piped through something that re-orders columns (unlikely but possible), verify a few rows manually.

3. **Same connection, different PIDs:** A process may show multiple PIDs for the same connection across different snapshots (process re-spawn, PID reuse). Aggregate by process **name**, deduplicate by `(proto,local,remote,pid)` — this overcounts but safely.

4. **Date-line detective:** ISO dates like `2026-07-14T23:42:48+02:00` start with `20` numerically but ALSO happen to match the start of IPv4 addresses `20.xxx`. **Use the letter T as discriminator** — dates contain `T`, IPs do not. The `TS_RE` pattern above handles this.

5. **Snapshots without connections:** If a snapshot marker appears alone (no rows before the next marker), it's fine — the system had zero TCP/UDP sockets at that instant, or `ss` was still starting.

## Comparison to live forensic trace

| Aspect | Live trace (Schritt 4b) | Bulk capture analysis |
|--------|------------------------|-----------------------|
| Data source | `ss -tupn` NOW, single snapshot | Pre-recorded file, N snapshots |
| Time dimension | Point-in-time | Temporal (deduped) |
| Owner extraction | Same regex | Same regex |
| Deduplication | Not needed (1 snapshot) | Critical (N snapshots) |
| Orphan analysis | Optional (few orphans in live) | Important (many orphans in transitions) |
| Output | Single-snapshot summary | Full baseline report |

See also: `connection-forensic-trace.md` for the live-trace variant and IP geo-database.