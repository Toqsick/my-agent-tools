# Remote-Destination Profiling — Session 2026-07-15

**Quelle:** `grok-monitor-ss-20260714T214248Z.log` (17.6 MB, 3 091 Snaps, 1 h 44 min)
**Arbeitsverzeichnis sessionspezifisch** — Skripte sind nicht dauerhaft gespeichert, aber das vollständige Analyse-Ergebnis liegt als Report vor (`/tmp/wire_capture_analysis.md` in der Session, nicht dauerhaft).

---

## Python-Parser (Phase B1)

Der Parser für den `ss -tupn` output, der Remote-IPs aus `[::1]:443` / `1.2.3.4:443` korrekt extrahiert:

```python
import re
from collections import Counter

SEP_RE = re.compile(r'^---\s*$')
TS_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+\-]\d{2}:\d{2})$')
# ss header: "tcp   ESTAB      0      0      ..." — tcp/udp as first word, ESTAB as second
CONN_RE = re.compile(
    r'(?P<proto>\w+)\s+'
    r'(?P<state>\S+)\s+'           # ESTAB, LISTEN, etc.
    r'(?P<recv_q>\d+)\s+'
    r'(?P<send_q>\d+)\s+'
    r'(?P<local>\S+)\s+'
    r'(?P<remote>\S+)\s+'
    r'(?:users:\s*)?\(\((?P<proc>[^,]+),pid=(?P<pid>\d+),fd=(?P<fd>\d+)\)\)'
)

def parse_ss_log(path):
    snaps = []
    ts = None
    conns = []
    with open(path) as f:
        for raw_line in f:
            line = raw_line.rstrip('\n\r')
            if TS_RE.match(line):
                if ts is not None:
                    snaps.append((ts, conns))
                ts = __import__('datetime').datetime.fromisoformat(line)
                conns = []
            elif SEP_RE.match(line):
                pass
            elif line.startswith(('tcp', 'udp')) and ts is not None:
                m = CONN_RE.match(line)
                if m:
                    conns.append(m.groupdict())
    if ts is not None:
        snaps.append((ts, conns))
    return snaps
```

**Remote-IP Extraktion:**

```python
def remote_host(addr: str) -> str:
    if addr.startswith('['):
        return addr.split(']:')[0][1:]
    return addr.rsplit(':', 1)[0]

def is_private_ip(ip: str) -> bool:
    return ip.startswith(('127.', '192.168.', '10.', '169.254.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.'))
```

## PTR-Lookup-Taktik

**Nie nur einen Resolver verwenden.** `dig +short -x` kann mit dem Systemresolver NXDOMAIN liefern, während `@1.1.1.1` SERVFAIL gibt oder umgekehrt.

```bash
# Systemresolver
PTR=$(dig +short -x "$ip" +time=3 +tries=1 2>/dev/null)
[ -z "$PTR" ] && PTR=$(dig +short -x "$ip" @1.1.1.1 +time=3 +tries=1 2>/dev/null)
[ -z "$PTR" ] && echo "(kein PTR)" || echo "$PTR"
```

**Erwarteter Anteil NXDOMAIN:** Bei typischen CDN-Providern (Cloudflare, Fastly, CloudFront, Anthropic) sind 50–80 % NXDOMAIN normal. PTR ist ein **Bonus**, kein muss.

**PTR-Mismatch zu AS ist kein Konflikt:** `lb.fra.tailscale.com` in AS16509 (Amazon) = Tailscale mietet AWS-Kapazität. Beide korrekt.

## Team-Cymru-AS-Attribution

**Schlüsselbefehl (IPv4):**
```bash
dig +short TXT "${reversed}.origin.asn.cymru.com" @1.1.1.1 | tr -d '"'
```

**IPv6:** Braucht `ipaddress.ip_address(ip).exploded` → nibbles reversen → `.origin6.asn.cymru.com`. Das Python one-liner aus der Session:

```bash
expanded=$(python3 -c "import ipaddress; print(str(ipaddress.ip_address('$ip').exploded))")
nibbles=$(echo "$expanded" | tr -d ':')
n=$(echo "$nibbles" | fold -w1 | tac | paste -sd'.' -)
result=$(dig +short TXT "${n}.origin6.asn.cymru.com" @1.1.1.1 | tr -d '"')
```

**AS-Namen:**
```bash
dig +short TXT "AS${asn}.asn.cymru.com" @1.1.1.1 | tr -d '"'
```

Ausgabeformat: `ASn | CC | registry | date | NAME - Human Name`

## CDN-Share-Berechnung

Die Python-Logik aus der Session:

```python
AS_GROUPS = {
    13335: 'Cloudflare',
    54113: 'Fastly',
    16509: 'Amazon / CloudFront',
    14618: 'Amazon (AES)',
    20940: 'Akamai',
    396982: 'Google Cloud',
    15169: 'Google',
    399358: 'Anthropic (direct)',
    36459: 'GitHub',
    62041: 'Telegram',
    45102: 'Alibaba',
    37963: 'Alibaba (CN)',
    400940: 'Railway',
    24940: 'Hetzner',
    21859: 'Zenlayer',
    16625: 'Akamai (GS)',
    42675: 'Obehosting (Tor-Snowflake)',
}

def classify(ip_asn_map, counters):
    """ip_asn_map: {ip_str: asn_int}, counters: {ip_str: count}"""
    from collections import defaultdict
    group_totals = defaultdict(lambda: {'v4': 0, 'v6': 0})
    for ip, asn in ip_asn_map.items():
        group = AS_GROUPS.get(asn, f'Unknown AS{asn}')
        is_v6 = ':' in ip
        key = 'v6' if is_v6 else 'v4'
        group_totals[group][key] += counters[ip]
    return group_totals
```

## Report-Struktur

1. **Kopf** — Quelle, Zeitfenster, Snapshots, Observations
2. **IPv4 Top-25 Tabelle** — Rang, IP, N, Anteil, AS, AS-Name
3. **IPv6 Top-25 Tabelle** — gleiches Format
4. **PTR-Ergebnisse** — getrennt nach erfolgreich/erfolglos
5. **CDN-Anteil Tabelle** — Provider vs. obs vs. Prozent
6. **Auffälligkeiten (Findings)** — 4–6 konkrete, nummerierte Findings

## Findings aus dieser Session (Template)

| Finding | IP/Klasse | Wert | Signal |
|---------|-----------|------|--------|
| Dominant IPv4 | 69.46.46.21 (Railway) | 36 % aller IPv4 | Heartbeat/Websocket — Prozess prüfen |
| Top IPv6 | 2607:6bc0::10 (Anthropic) | 20 % aller IPv6 | Aktive Claude-Desktop-Session |
| Alibaba-CN-Cluster | 47.252.0.0/17, 121.41.77.126 | 6 239 obs | Ungewöhnlich für DE-Workstation |
| Tor-Snowflake | 2a0c:dd40:1:b::42 | 2 126 obs | Tor-Pluggable-Transport aktiv |
| PTR · AS-Mismatch | 2606:b740:49::107 | Tailscale PTR / Amazon AS | Erwartet — Tailscale hostet auf AWS |

## Abhängigkeiten

- Python 3 stdlib (`re`, `collections`, `datetime`, `json`)
- `dig` (bind9-dnsutils)
- Kein `whois` erforderlich