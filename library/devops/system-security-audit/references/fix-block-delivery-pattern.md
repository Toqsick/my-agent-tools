# Fix-Block Delivery Pattern — Template + Case Study

> **Validierung:** 2026-07-16, System-Audit Basti (Queen-Recon + 3 Deep-Dive Bees)
> **Session:** System Audit → Befund-Report → Fix-Blocks → User führt in eigener Reihenfolge aus
> **User-Ordering:** "d nach b1 nach a" (Basti wählte selbst)

---

## Template (Copy-Paste-Vorlage)

```
### A1 — [Kurzbeschreibung] ([geschätzte Dauer])

\`\`\`bash
# Read-only Vorher: Zustand erfassen
sudo <befehl-zustand>

# Fix-Befehl
sudo <fix-befehl>

# Nachher: Veränderung verifizieren
sudo <befehl-zustand>
\`\`\`

**Erwartetes Ergebnis:** [Konkrete, überprüfbare Aussage in einem Satz]
**Risiko:** ⭐/⭐⭐/⭐⭐⭐
```

### Block-Nummerierung

| Präfix | Domain |
|--------|--------|
| **A** | System-Integrität (Disk, Logs, Rotation, Service-Config) |
| **B** | Netzwerk-Härtung (Firewall, Ports, Gateway-Fronting) |
| **C** | Konfig-Audit (Permissions, Cron, Hermes-Config) |
| **D** | Deep-Dive / Nachbereitung (Mnemosyne, Provider, CI) |

### Ablauf (Workflow)

```
1. Audit-Report fertig → Fix-Optionen A/B/C/D als nummerierte Blöcke
2. Blöcke in ~/20-Workspace/results/fix-<thema>-YYYY-MM-DD.md
3. User wählt Reihenfolge („d nach b1 nach a" / „a zuerst" / „alles parallel")
4. Block X → User führt selbst im Terminal aus (eigenes PWD)
5. Agent zeigt After-Snapshot + nächsten Block
6. User bestätigt "done" → Agent markiert in Todo-Liste
7. Repeat bis alle Blöcke durch
```

---

## Case Study: 2026-07-16 System-Audit

### Findings (aus Bienen-Bericht)

| # | Finding | P0/P1 | Fix-Block |
|---|---------|-------|-----------|
| A1 | Syslog 6,4 GB (gnome-shell Endlos-Stacktrace, `zorin-printers` Extension) + `ConditionACPower=true` blockiert Rotation auf Akku | **P0** | `A1 — Sofort-Hygiene` |
| A2 | `logrotate.service` ConditionACPower=true verhindert Rotation im Akku-Mode | **P0** | `A2 — Akku-fest machen` |
| A3 | rsyslog hat nur `weekly`, kein size-Trigger für Sturm-Volumen | **P0** | `A3 — size 500M` |
| A4 | Zorin-printers-Extension läuft und flutet syslog | **P0** | `A4 — Extension disablen` |
| B1 | Gateway 8642: Auth aktiv (Bearer via hmac), aber kein UFW-Fronting, LAN offen | **P1** | `B1 — UFW-Fronting` |
| D | Mnemosyne-LLM-Provider auf AAAK-Fallback (seit 13.07.) | **P1** | `D — Provider-Diagnose` |

### Fix-Block-Datei

Die generierte Datei: `~/20-Workspace/results/fix-paste-2026-07-16.md`

Struktur der echten Datei:

```markdown
# A+B1 Fix-Blocks — Copy/Paste für Basti (Do 16.07.2026)

---

## A1 — Sofort-Hygiene: logrotate + Journal vacuum

```bash
# Read-only Vorher
df -h / | head -2

sudo logrotate -f /etc/logrotate.conf
sudo journalctl --vacuum-time=7d

sudo bash -c 'cat >> /etc/systemd/journald.conf <<EOF
SystemMaxUse=200M
MaxRetentionSec=7day
EOF'
sudo systemctl restart systemd-journald

# Read-only Nachher
df -h / | head -2
ls -lh /var/log/syslog*
du -sh /var/log/journal
```

**Erwartetes Ergebnis:** Disk 82 % → ~76 %, syslog ~150 KB
**Risiko:** ⭐⭐ (System-Log-Rotation, reversibel)

---

## A2 — logrotate akku-fest machen

```bash
sudo mkdir -p /etc/systemd/system/logrotate.service.d
sudo tee /etc/systemd/system/logrotate.service.d/override.conf >/dev/null <<EOF
[Unit]
ConditionACPower=
EOF

sudo systemctl daemon-reload
sudo systemctl show logrotate.service | grep -i 'ConditionACPower'
```

**Erwartetes Ergebnis:** ConditionACPower leer → Rotation auch auf Akku
**Risiko:** ⭐⭐⭐ (Overwrite von systemd-Unit-Config)
```

[Weitere Blöcke A3, A4, B1, D-Vorbereitung entsprechend...]

### User-Interaktion

| Schritt | Agent | User |
|---------|-------|------|
| 1 | Generiert alle Blöcke als .md + posted im Chat | |
| 2 | | Sagt "A1 los" |
| 3 | Sagt "Starte mit Block A1" | Führt A1 im Terminal aus |
| 4 | Zeigt After-Snapshot: Disk ~76% ✔ | |
| 5 | | "A1 done" |
| 6 | Markiert A1 als done, zeigt nächsten Block | |
| 7 | | "A2 los" → führt A2 aus → "A2 done" |
| ... | Schleife bis alle Blöcke durch | |

### Unterschied zur Sudo-Sammlung

| Aspekt | Sudo-Sammlung | Fix-Block |
|--------|--------------|-----------|
| **Einmalig oder sequentiell** | Einmalig (Bulk) | Sequentielle Interaktion |
| **User wählt Reihenfolge?** | Nein (Script-Reihenfolge) | Ja (User sagt "d nach b1 nach a") |
| **Lauffähig ohne Agent** | Ja (eigenständiges Script) | Ja (jeder Block unabhängig) |
| **Bestätigung pro Schritt** | Nein (Script läuft durch) | Ja ("done" pro Block) |
| **Fehlerbehandlung** | Script bricht ab, User muss debuggen | User sagt "error: ...", Agent passt Block an |
| **Wann verwendet** | "Mach mal schnell, ich will das Script blind pasten" | "Zeig mir jeden Schritt, ich will mitdenken" |

### Lessons Learned (2026-07-16)

1. **Do not hardcode ordering** — Present as options, let user pick sequence
2. **Every block needs Vorher+Nachher** — User needs to see what changed
3. **Time estimate in header** — User needs to judge whether to invest time now
4. **Expected result must be falsifiable** — "Disk 82% → ~76%" ✔ vs "system works better" ❌
5. **Blocks should be independent** — If A3 fails, user can still do A4. No script-breaking dependencies.
6. **Keep file in ~/20-Workspace/results/** — Colocated with the audit report it belongs to
7. **Explain commands BEFORE the code block** — Basti asked "was machen die befehle genau ?" (2026-07-16) after receiving blocks without explanations. Include 1-2 sentence prose OR a short table (Befehl → Was es macht → Effekt) BEFORE each code block. Applies to SYSTEM-TERMINAL blocks (bash, sudo, config-edit). NOT for in-game GreyHack shell commands, where "Tippe das:" without explanation is correct.
