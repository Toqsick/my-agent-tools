---
name: syslog-source-first-audit
description: "Use when user asks for syslog audit, source-first log identification, log-bomb prevention, syslog size measurement. NOT for application-level logging config or non-syslog log files. Syslog-Audit pattern — source-first identification of log-bomb vectors."
version: 1.0.0
author: Yuno
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - syslog audit
  - syslog wächst
  - log bomb
  - syslog explosion
  - log spam
  - rsyslog filter
keywords:
  - syslog
  - logging
  - audit
  - debugging
  - rsyslog
  - logrotate
related_skills:
  - hermes-maintenance
  - self-improving
last_curated: 2026-07-18
curated_by: Yuno
routing_hint: "Use when syslog ungewöhnlich wächst, Log-Bomb-Verdacht, oder systematische Top-Producer-Analyse des /var/log/syslog nötig ist."
---

# Syslog Source-First Audit Pattern

Systematischer Ansatz um Log-Bomb-Vektoren zu identifizieren. Entstanden aus dem
17.07.2026 Audit wo ein 2,7 GB syslog fälschlich demzorin-printers-Loop zugeordnet
wurde, obwohl der eigentliche Verursacher Ollama print_timing-Output war.

## Kern-Prinzip: Source-First, nicht Token-First

Der naive Ansatz `awk '{print $5}' /var/log/syslog | sort | uniq -c | sort -rn`
liefert Tokens, keine Quell-Prozesse. Ein C++-Template-Log mit 4 Millionen `to`
Tokens maskiert die wahre Quelle (Ollama slot get_availabl).

Richtig: Erst prozess-identifizieren, dann drilldown.

## Audit-Workflow

### Schritt 1: Syslog-Größe messen

```
ls -lh /var/log/syslog*
stat -c "size=%s mtime=%y" /var/log/syslog
wc -l /var/log/syslog
```

Wenn größer als 500 MB oder mehr als 1 Mio Zeilen: Log-Bomb-Verdacht.

### Schritt 2: Source-First Identification (PITFALL-Prävention)

NICHT `awk '{print $5}'`. Stattdessen prozess-gruppieren:

```
awk -F'[\\[:]' '{print $6}' /var/log/syslog | sort | uniq -c | sort -rn | head -10
```

Das extrahiert den Programm-Namen zwischen `[` und `:` (Prozess-Slot im rsyslog-
Format `Jul 18 08:38:01 hostname program[pid]: message`).

Alternative für unkomplizierte Fälle:

```
grep -oE '^[A-Za-z]{3} [0-9 ]+[0-9:]+' /var/log/syslog | wc -l  # Zeilencount
grep -c 'ollama\[' /var/log/syslog                               # pro Prozess
grep -c 'zorin-printers' /var/log/syslog                         # pro Prozess
grep -c 'kernel\[' /var/log/syslog                               # pro Prozess
```

### Schritt 3: Top-Producer verifizieren

Für die Top 3 Prozesse aus Schritt 2, Sample-Lines ziehen:

```
grep -m 5 'PROZESSNAME\[' /var/log/syslog
```

Daraus den Spam-Charakter ableiten:

| Pattern | Typ | Beispiel |
|---|---|---|
| C++-Tokens (`to`, `update:`, `operator():`) | Debug-Output eines lokalen Services | Ollama print_timing |
| Gleiche Zeile wiederholt | Loop-Bug | zorin-printers clutter_text |
| Stacktrace-Fragmente | Crash-Loop | gnome-shell disposed |
| `[UFW BLOCK] IN=...` | Firewall-Noise (normal) | Neighbor Discovery |

### Schritt 4: Zeitspanne des Logs bestimmen

```
head -1 /var/log/syslog    # Anfang
tail -1 /var/log/syslog    # Ende
```

Wachstumsrate berechnen:

```
size_bytes / ((end_ts - start_ts) in Sekunden)
```

Wenn größer als 10 KB/s: aktiver Spam. Wenn kleiner als 100 B/s: historischer
Ballast der nicht wegrotiert ist.

### Schritt 5: Root-Cause bestimmen

Für die identifizierte Spam-Quelle den Root-Cause finden:

1. Service-Logs: `journalctl -u <service> --since "1h ago" | tail -20`
2. Service-Config-Check: `systemctl cat <service>` + Drop-In-Overrides
3. Debug-Env-Vars checken: `cat /etc/systemd/system/<service>.service.d/override.conf`

Häufige Root-Causes:

| Source | Typische Ursache | Fix |
|---|---|---|
| ollama | Debug-Logging default-on in v0.30 | `OLLAMA_DEBUG=0` im override |
| gnome-shell extension | Loop-Bug in Extension | rsyslog-Filter-Drop-In |
| kernel UFW BLOCK | IPv6 Neighbor Discovery | rsyslog-Filter oder UFW limit |
| tailscale portmap | UPnP-Events bei Router-Wechsel | rsyslog-Filter für `portmap:` |

### Schritt 6: Fix-Optionen evaluieren

Zwei Pfade,.Preference für Source-Fix:

**Option A — rsyslog-Filter (symptomatisch, schnell):**

```
/etc/rsyslog.d/10-<source>-suppress.conf
if $programname == "<source>" and $msg contains "<token>" then stop
```

Wirkt sofort nach `systemctl reload rsyslog`. Aber: weitere Spam-Vektoren der-
selben Quelle fallen nicht darunter.

**Option B — Source-Fix (ursächlich, dauerhaft):**

```
/etc/systemd/system/<service>.service.d/override.conf
Environment="DEBUG_VAR=0"
```

Erfordert Service-Restart. Behebt die Ursache statt das Symptom.

Entscheidungskriterien:

- Quelle ist extern (andere Extension, anderer Dienst): Option A
- Quelle ist lokaler Service mit eigenem Override: Option B
- Quelle ist Kernel: Option A (Kernel-Logs nicht abschaltbar)
- User will keinen Service-Restart jetzt: Option A, dann später Option B

## Logrotate-Verifikation

Parallel zur Spam-Diagnose: rotiert logrotate überhaupt?

```
grep -nE "size [0-9]+M" /etc/logrotate.d/rsyslog    # Size-Trigger prüfen
systemctl status logrotate.service                   # Health
ls /etc/logrotate.d/ | grep -i bak                   # .bak-Dateien (Pitfall!)
ls /etc/systemd/system/logrotate.service.d/          # Drop-Ins
```

Pitfall: Eine `.bak` Datei in `/etc/logrotate.d/` bricht den gesamten logrotate-
Lauf mit kryptischer Fehlermeldung. Checken und entfernen.

## Cross-Check mit Vor-Reports

Syslog-Vorfälle sind selten Einzelfälle. Vorherige Audits und Fixes checken:

- Gab es schonmal Spam aus derselben Quelle?
- Ist der aktuelle Spam wirklich neu oder ein Recurrence?
- Hat ein früherer rsyslog-Filter gewirkt (Hits sollten gegen null gehen)?

Typische Basti-Workstation-Vorfälle:

| Datum | Quelle | Größe | Fix |
|---|---|---|---|
| 2026-07-11 | zorin-printers (scheinbar) | 10,5 GB | schien self-resolving (war Pause) |
| 2026-07-16 | zorin-printers clutter_text | 6,4 GB | rsyslog-Filter, logrotate size 500M |
| 2026-07-17 | ollama print_timing | 2,7 GB | OLLAMA_DEBUG=0 (vorgeschlagen) |

## Anti-Patterns

- NIEMALS `truncate -s 0 /var/log/syslog` ohne Source identifiziert zu haben.
  Der Spam kommt in Minuten zurück, der truncate zerstört aber Diagnose-Daten.
- NIEMALS `awk '{print $5}' | sort | uniq -c` als Source-Identifikation verwenden.
  Das liefert Tokens, keine Prozesse.
- NIEMALS rsyslog-Filter für `programname == "ollama"` ohne Token-Condition setzen.
  Das mutet auch legitime Ollama-Errors weg.
- NIEMALS logrotate-Service neu starten ohne `.bak`-Check in `/etc/logrotate.d/`.
  Eine `.bak` bricht den Service komplett.
- NIEMALS auf "self-resolving Syslog-Drift" hoffen (Basti-Workstation-spezifisch,
  widerlegt durch 3 Vorfälle 07/2026).

## Verification

Nach jedem Audit:

1. Source identifiziert via Schritt 2 (pro-Prozess-Count, nicht Token-Count)
2. Zeitspanne und Wachstumsrate berechnet
3. Root-Cause fix formuliert mit Source-Preference (Option B vor Option A)
4. logrotate-Status verifiziert (kein .bak, Size-Trigger, Drop-In aktiv)
5. Cross-Check mit Vor-Audit ob der Vektor neu oder ein Recurrence ist

## References

- `references/token-vs-source-2026-07-17.md` — Case study: 2.7 GB syslog initially misdiagnosed via token-analysis, then correctly attributed to Ollama print_timing via source-first identification. Full command transcript, root cause, and fix applied.
