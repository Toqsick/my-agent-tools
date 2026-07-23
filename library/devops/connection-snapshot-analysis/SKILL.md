---


name: connection-snapshot-analysis
description: |
  Use when you have multiple time-series network connection snapshots (ss/netstat output captured at intervals) and need to detect drift, orphan sockets, port flapping, or unusual outbound destinations.
  NOT for live packet capture (use tcpdump/Wireshark), single-snapshot inspections, firewall-config audits, or non-time-series data.
  Analyzes repeated network-connection snapshots: diffs them to surface drift, identifies outlier processes and ports, flags suspicious outbound IPs.
version: 1.1.0
author: Yuno (Hermes Agent, session 2026-07-15)
tags:
- network-analysis
- ss-capture
- burst-detection
- time-series
- connection-log
- anomaly-detection
- remote-destination
- ptr-lookup
- AS-attribution
- cdn-analysis
triggers:
- wire-capture analyse
- ss snapshot analyse
- verbindungsmuster analysieren
- zeitfenster ungewöhnlich
- sequenz-analyse verbindungen
- connection-heatmap
- burst-detection verbindungen
- netzwerk-log auswerten
- capture-log untersuchung
- connection-snapshot-analysis
- idle-phasen verbindungen
- remote-destination aufschlüsseln
- domains zuordnen
- as attribution
- ptr lookup log analyse
- cdn share berechnen
- verbindungs-herkunft analysieren
- externer verkehr auswerten
- ziel-ip klassifizieren
metadata:
  hermes:
    changelog:
    - '1.0.0 (2026-07-15): Initial. Abgeleitet aus 3091-ss-Snapshot-Analyse. Per-Process-Burst-Detection,
      Idle-Phase, Heatmap, 6 Findings.'
    - '1.1.0 (2026-07-15): Remote-Destination-Profiling-Workflow hinzugefügt. PTR-Lookup,
      Team-Cymru-AS-Attribution, CDN-Anteil, Anomalie-Erkennung. Vgl. references/2026-07-15-remote-destination-profile.md.'
related_skills:
- system-security-audit
- host-security-audit
- sqlite-forensic-diff
- hermes-memory
lane: worker-flash
reasoning_effort: high
license: MIT
trigger_keywords: ['time', 'series', 'network', 'connection', 'snapshots']
keywords: ['time', 'series', 'network', 'connection', 'snapshots']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---
# Connection Snapshot Analysis

Analyze time-series network connection logs from repeated `ss -tupn` / `ss -tlnp` system-state snapshots. Two complementary analysis workflows: (A) local process-behavior — bursts, idle phases, heatmaps; (B) remote-destination profiling — PTR lookups, AS attribution, CDN share, anomaly detection. Parse timestamped snapshots, extract connection records, and produce a structured Markdown findings report.

**Trigger:** User asks to analyze a wire-capture log, ss snapshot log, `.log` with repeated `ss` output, or says "Sequenz-Analyse Zeitfenster", "Burst-Detection", "Connection-Heatmap", "ungewöhnliche Verbindungsmuster", "Remote-Destinations aufschlüsseln", "Domains zuordnen", "AS Attribution", "CDN-Anteil berechnen", "wohin gehen die Verbindungen".

---

## Workflow

### Phase 1 — Parse

Given a log file with `---`-delimited `ss -tlnp` snapshots, each preceded by a timestamp line:

```
2026-07-14T23:42:48+02:00
State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       4096    127.0.0.1:33247     0.0.0.0:*          users:(("hermes",pid=1234,fd=56))
---
2026-07-14T23:42:50+02:00
...
---
```

1. Extract `(datetime, connections[])` per snapshot via `re` regex
2. Connection record = `(proto, local, remote, pid, fd)` — treat as identity key
3. Yield `(timestamp, list_of_connections)` as generator

**Pitfall 1 — `---` handling:** The last snapshot may or may not be terminated. Use a separator regex and accumulate until next separator or EOF. Check for trailing newlines/whitespace on separator lines. Use `re.compile(r'^---\s*$')` — `rstrip()` before matching.

**Pitfall 2 — Header line:** Every snapshot includes the `State Recv-Q …` header. Filter it out (match on `^State\s+Recv-Q` or check that the process field actually contains a real proc name pattern like `users:`).

### Phase 2 — Time windows

1. Align 5-min windows to the capture start time
2. Assign each snapshot to its window (windows are `[start + N*300, start + (N+1)*300)`)
3. For each window, aggregate connections per process
4. Define **"new" connection** = present in this snapshot, **absent** in the **previous snapshot** of the **same process**. (This catches fresh outbound connections, not idle keep-alives.)
5. Per window: `new_per_proc = {proc_name: count_of_new_connections}`
6. Per window: `total_new = sum(new_per_proc.values())` across the top-N processes

### Phase 3 — Baselines & Burst detection

**Key insight:** Global thresholding (e.g. "total > 2× global median") **hides sparse processes** (gnome-software, simplexity). Always use **per-process baseline**.

1. For each process, compute `median = median(new_per_5min_series)`
2. Burst threshold = `2 × median`
3. If `median === 0` → any value `> 0` is a burst
4. A **burst** = consecutive 5-min windows where process's `new_conns > threshold`
5. Rank bursts by `total_new` across the run

```python
def find_bursts(series, factor=2.0):
    med = median(series)
    if med == 0:
        is_burst = [v > 0 for v in series]
    else:
        is_burst = [v > med * factor for v in series]
    # find runs of consecutive True
    runs = []
    i = 0
    while i < len(series):
        if is_burst[i]:
            j = i
            while j < len(series) and is_burst[j]:
                j += 1
            runs.append((i, j-1))
            i = j
        else:
            i += 1
    return runs, med, thresh
```

### Phase 4 — Idle detection

1. Filter to HTTPS-out connections only (remote port == 443)
2. A process is **idle in a snapshot** if it has 0 new HTTPS-out in that snapshot
3. Consecutive idle snapshots summing to ≥5 min = an **idle run**
4. Report: `{proc, start, end, duration_seconds, snapshot_count}`

### Phase 5 — Heatmap

1. Bucket by hour (0–23)
2. Sum **cumulative** connection counts (not "new" — use raw presence to show volume per hour)
3. Row = hour, column = process

### Phase 6 — Findings

Write 3–6 concrete findings. Each finding must be:
- **Numeric** (not qualitative)
- **Comparable to baseline** (Faktor × vs median, or absolute)
- **Time-anchored** (Window [X], timestamp, or hour range)
- **Process-scoped** (which process)

Good template:
> **F2 — `hermes`-Spike-Cluster Window [17]+[18] (01:07–01:17): 53 + 50 = 103 neue Verbindungen in 10 min. Median 22, Faktor ~2.4×.**

### Phase 7 — ASCII time-series visualisation

Render a bar chart in the report using block characters (`█`). Scale: 1 char ≈ 2 connections (or auto-scale to fit ~50 chars). Include the raw counts alongside so the reader can verify.

```python
bar_w = 50
max_val = max(total_series)
for i, total in enumerate(total_series):
    bar_len = int(round(bar_w * total / max_val))
    bar = '█' * bar_len
    print(f"{i:>3}  {window_starts[i]:<25}  {bar:<52}  {total:>3}")
```

---

## Alternative Workflow B — Remote-Destination Profiling

**When used:** User asks to identify remote endpoints, PTR names, AS ownership, CDN share, or "wohin gehen die Verbindungen" — separate from process-burst analysis.

**Input:** Same `ss -tupn` / `ss -tlnp` capture log as workflow A. The focus shifts from "which process connects when" to "which external IP/FQDN/AS is connected".

### Phase B1 — Remote-IP aggregation

For each snapshot, extract the **remote IP** from each connection (exclude rport, keep the host). Count occurrences across all snapshots. Maintain two counters:
- **IPv4-only** (exclude 127.0.0.0/8, 192.168.0.0/16)
- **IPv6-only**

```python
from collections import Counter

def extract_remote_host(addr: str) -> str:
    """Extract IP from '[::1]:443' → '::1' or '1.2.3.4:443' → '1.2.3.4'"""
    if addr.startswith('['):
        return addr.split(']:')[0][1:]  # [::1]:443 → ::1
    return addr.rsplit(':', 1)[0]       # 1.2.3.4:443 → 1.2.3.4

ipv4_cnt = Counter()
ipv6_cnt = Counter()

for ts, conns in snaps:
    for c in conns:
        ip = extract_remote_host(c['remote'])
        if ':' in ip and '.' not in ip and not ip.startswith('::ffff:'):
            ipv6_cnt[ip] += 1
        elif not ip.startswith(('127.', '192.168.')):
            ipv4_cnt[ip] += 1
```

### Phase B2 — Top-N table with percentages

Compute `pct = count / total * 100` for each IP. Produce ranked markdown table:

```
| # | IP | N | Anteil | AS | AS-Name |
|---|----|---:|---:|---|---|
| 1 | 69.46.46.21 | 15316 | 36.19 % | AS400940 | RAILWAY · Railway (US) |
```

### Phase B3 — PTR Lookup (dig +short -x)

For Top-15 each (IPv4 + IPv6), perform PTR lookup. **Always use two resolvers** to distinguish NXDOMAIN from DNS failure:

```bash
# Primary (system resolver)
dig +short -x <ip> +time=3 +tries=1
# Fallback (1.1.1.1)
dig +short -x <ip> @1.1.1.1 +time=3 +tries=1
```

- If **both** return NXDOMAIN / no answer → provider does not set rDNS (common for Cloudflare, Fastly, CloudFront, Anthropic, Railway). **Do not call it a failure** — call it what it is: *provider does not publish PTR*.
- If one returns and the other does not → trust the one that returned, note the resolver discrepancy.
- PTR may contradict AS (e.g. `lb.fra.tailscale.com.` in AS16509 Amazon) — this is legitimate: Tailscale hosts its Frankfurt load balancer on AWS. **PTR = service name, AS = infrastructure owner**. Both are valid.

**Pitfall:** Do NOT use `nslookup` or `host` as primary — `dig +short -x` is most reliable. `whois` is not always installed; prefer DNS-based methods.

### Phase B4 — AS attribution via Team Cymru DNS

No `whois` needed. Use the Cymru DNS origin database:

```bash
# IPv4: reversed.origin.asn.cymru.com
dig +short TXT "4.3.2.1.origin.asn.cymru.com" @1.1.1.1
# IPv6: nibble-reversed.origin6.asn.cymru.com
dig +short TXT "<nibbles>.origin6.asn.cymru.com" @1.1.1.1
```

**IPv4 reversal idiom:**
```bash
reversed=$(echo "$ip" | awk -F. '{print $4"."$3"."$2"."$1}')
```

**IPv6 nibble reversal** (expand `::` → full exploded form first):
```bash
# Expand IPv6
expanded=$(python3 -c "
import ipaddress
print(str(ipaddress.ip_address('$ip').exploded))
")
# Take each hex nibble and join with dots, reversed
nibbles=$(echo "$expanded" | tr -d ':')
n=$(echo "$nibbles" | fold -w1 | tac | paste -sd'.' -)
result=$(dig +short TXT "${n}.origin6.asn.cymru.com" @1.1.1.1)
```

Result format: `ASn | prefix | CC | registry | date`

AS name resolution:
```bash
dig +short TXT "AS<n>.asn.cymru.com" @1.1.1.1
```
Returns: `ASn | CC | registry | date | NAME - Org Name`

### Phase B5 — CDN/Provider classification

Map ASNs to known provider groups:

| AS | Group | 
|---|---|
| 13335 | Cloudflare |
| 54113 | Fastly |
| 16509, 14618 | Amazon / CloudFront / AWS |
| 20940 | Akamai |
| 396982 | Google Cloud |
| 15169 | Google |
| 399358 | Anthropic (direct) |
| 36459 | GitHub |
| 62041 | Telegram |
| 45102, 37963 | Alibaba |
| 400940 | Railway |
| 16625, 21399, 22244 | Akamai (Akamai Game State / EdgeSuite) |
| 24940 | Hetzner |
| 21859 | Zenlayer |

Compute aggregate shares:
```
| Provider | IPv4 obs | IPv6 obs | Σ | Anteil |
|---|---:|---:|---:|---:|
| Cloudflare | 3090 | 11493 | 14583 | 14.0 % |
```

### Phase B6 — Anomaly detection

Look for:
1. **IPs in unexpected AS for the user's geography** (e.g. Alibaba-CN IPs from a DE workstation with no known CN-service usage)
2. **PTR resolving to known security-adjacent services** (torproject.net, snowflake, known VPN endpoints)
3. **Single IP dominating >25% of all connections** (likely a heartbeat/websocket stream — identify process)
4. **PTR mismatches with AS** (not usually anomalous, but note them)

Each finding should:
- State **what** (IP, AS, count)
- State **why it's noteworthy** (geography mismatch, Tor, dominant volume)
- Suggest **next step** (identify process, check if expected, investigate)

---

## Data quality checks (always run)

- Snapshot count and gap distribution (max gap, median gap)
- Zero-connection snapshots (should be 0 — if present, parser may be broken)
- `first_seen` / `last_seen` per process (identify late-arriving processes)
- All `---` terminators accounted for (count separators vs snapshots)

---

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Global burst threshold hides sparse procs | gnome-software has 0 bursts despite visible activity in window 7 | Use per-process median, not global |
| Snapshot boundary misalignment | Burst edges at [0] or [N-1] are artifacts | Flag "capture-start effect" in findings |
| `---` line has trailing whitespace | Last snapshot not parsed | Use `rstrip()` or regex `^\s*---\s*$` |
| Connection dedup key too narrow | Same connection counted in every snapshot | Key = `(proto, local, remote, pid, fd)` — covers identical conns across snapshots |
| Idle detection uses all ports | Every process shows false-positive idle | Idle = specifically **HTTPS-out** (rport 443) only |
| PTR NXDOMAIN interpreted as tool failure | User reports "DNS is broken" | Always cross-verify with a second resolver (`@1.1.1.1`). Many providers (Cloudflare, Fastly, CloudFront, Anthropic) do not set rDNS — NXDOMAIN is the correct result. |
| `whois` assumed installed | `whois` command fails — tool returns nothing or errors | Use DNS-based AS attribution (Team Cymru `dig +short TXT reversed.origin.asn.cymru.com`). Works everywhere, no deps. |
| IPv6 address collision with IPv4 parser | IPv6 addresses parsed as IP:port-style fail | IPv6 format is `[::1]:443` — split on `]:` first. Never use `rsplit(':', 1)` alone on untagged address strings. |
| PTR · AS contradiction misinterpreted | "Tailscale IP is AS16509 Amazon — something is wrong!" | PTR = service name, AS = infrastructure. Tailscale runs its load-balancers on AWS. Both attributions are correct — report both. |

---

## Expected output

- Structured Markdown report saved to caller-specified path (e.g. `~/.hermes/wire-captures/analysis/`)
- Analysis JSON with all windows, bursts, idle phases for potential re-rendering
- Cleanup: parser scripts are ephemeral (no permanent files outside report path)

## Dependencies

- Python 3 stdlib only: `re`, `datetime`, `collections`, `json`, `statistics`
- No external packages required