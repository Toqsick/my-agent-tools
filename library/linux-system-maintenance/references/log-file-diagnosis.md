# Log-File Runaway Diagnosis — Read-Only Methodik

**Pattern-Klasse:** Systematische Diagnose eines übermäßig gewachsenen Logfiles (> 1 GB),
ohne sudo, ohne Destruktion, mit vollständiger Ursachenzuordnung.

## Wann anwenden

- User fragt "Warum ist `/var/log/syslog` (oder ein anderes Log) so groß geworden?"
- Disk läuft voll (> 75 %), Hauptverdacht auf Logfile-Bloat
- Rotation scheint nicht zu funktionieren (Logfile älter als 7 Tage)
- Nach einem Boot oder Extension-/Service-Update ist das Log explodiert

## Ablauf (bewährte Reihenfolge)

### Phase 0 — Sofortbild

```bash
# 1. Datei-Größe + Alter
stat /var/log/syslog
# birth=letzte Rotation, modify=letzter Write

# 2. Gesamt-Zeilen
wc -l /var/log/syslog

# 3. Disk-Kontext
df -h /
zramctl

# 4. rsyslog-Status
systemctl status rsyslog
```

### Phase 1 — Top-Verursacher identifizieren (Prozess-Level)

Die einfachste und effektivste Methode: **awk-basiertes Tag-Counting**.

```bash
# Methode A: Nach erstem Wort nach ISO-Timestamp gruppieren
awk '{
  sub(/^[0-9T:.\+-]+ +bratan[^ ]+ +/, "", $0)
  proc = $1
  gsub(/[\[:].*$/, "", proc)
  if (proc ~ /^[a-zA-Z]/) count[proc]++
}
END {
  PROCINFO["sorted_in"] = "@val_str_desc"
  for (p in count) printf "%8d %s\n", count[p], p
}' /var/log/syslog | head -25
```

**Ergebnis:** Liste der Top-Prozesse sortiert nach Zeilenanzahl. Der mit Abstand größte Eintrag ist der Verursacher.

### Phase 2 — Byte-Counting (verifiziert Größe pro Prozess)

Zeilen zählen allein reicht nicht — eine Zeile kann 100 Bytes oder 10 KB sein.
Bei Stack-Traces oder JSON-Zeilen ist Byte-Counting nötig:

```bash
# Byte-Schätzung pro Prozess (awk subtrahiert den Prozess-Namen + Kontext)
for proc in "gnome-shell" "kernel:" "systemd" "NetworkManager"; do
  bytes=$(awk -F"$proc" 'NF>1 {n+=length($0)} END {print n+0}' /var/log/syslog)
  cnt=$(grep -c "$proc" /var/log/syslog 2>/dev/null)
  printf "%-40s %12d lines %14d bytes (~%5.1f MB)\n" "$proc" "$cnt" "$bytes" \
    "$(echo "scale=1; $bytes/1048576" | bc)"
done
```

Bei dominantem Verursacher (> 90 % der Datei) reicht ein einziger `for`-Durchlauf.

**Wenn bc nicht verfügbar oder Locale-Probleme auftreten:** awk pur:

```bash
awk -F'gnome-shell' 'NF>1 {n+=length($0)} END {
  printf "%.2f GB (%.1f%%)\n", n/1024/1024/1024, n*100/6764679238
}' /var/log/syslog
```

### Phase 3 — Inhaltliche Probe (Was spammt da?)

```bash
# Sample der ersten 3 Zeilen vom Top-Verursacher
awk -F'gnome-shell' 'NF>1 {print substr($0,1,200); if (++c >= 3) exit}' /var/log/syslog

# Aus-Normalisieren: welche Nachrichten-Typen tauchen auf?
grep "gnome-shell" /var/log/syslog 2>/dev/null | \
  sed 's/\[[0-9]*\]//g; s/0x[0-9a-f]*//g' | \
  sort | uniq -c | sort -rn | head -15
```

**Suche nach Mustern:**
- `has been already disposed` → Extension-Bug (Gnome-Shell Extension crasht im Loop)
- `assertion failed` → GLib/C Library intern
- `GLib-GIO-WARNING` → Tracker / Dateisystem-Watcher
- `UFW BLOCK` → Firewall-Log (normal, aber rate-limit prüfen)
- `NVRM: GPU0 nvAssertFailedNoLog` → NVIDIA Treiber (kernel)

### Phase 4 — Logrotate-Health-Check

Prüfen, **ob Rotation überhaupt läuft und warum nicht**:

```bash
# 1. Timer-Status
systemctl status logrotate.timer
# → nächster Lauf: 2026-07-17 00:00:00

# 2. Service-Unit (ConditionACPower?)
cat /lib/systemd/system/logrotate.service

# 3. Letzte Rotation im Syslog selbst finden
grep -E "logrotate.service: (Finished|skipped|Deactivated)" /var/log/syslog \
  /var/log/syslog.1 | tail -20

# 4. Rotations-Konfig
cat /etc/logrotate.d/rsyslog

# 5. Statusfile (zeigt letzte Rotation pro File)
ls -la /var/lib/logrotate/status
```

**Häufige Probleme mit logrotate:**

| Problem | Erkennung | Fix |
|---------|-----------|-----|
| `ConditionACPower=true` | skipped im syslog alle 24h, Notebook auf Akku | `systemctl edit logrotate.service` → Override `ConditionACPower=` (leer) |
| `weekly` ohne `size`-Trigger | Log wächst bei einem Sturm > 1 GB/Tag | `/etc/logrotate.d/rsyslog` → `size 500M` vor `weekly` |
| Rotation im syslog erfolgreich, aber File wächst weiter | Logrotate hat rotiert, aber neues File läuft sofort wieder voll | Muss Ursache bekämpfen (gnome-shell Extension / Service Bug) |

### Phase 5 — Root-Cause (Wer produziert den Spam?)

Nachdem Phase 1–4 den Spammer + die ausgefallene Rotation identifiziert haben:

**Gnome-Shell:** Extension-Location prüfen
```bash
ls /usr/share/gnome-shell/extensions/zorin-printers@zorinos.com/
cat /usr/share/gnome-shell/extensions/.../extension.js | head -50
# Extension disablen (nur nach User-Freigabe):
# gnome-extensions disable zorin-printers@zorinos.com
# oder gnome-shell restart (weg-desktop)
```

**Systemd-Service:** `journalctl -u $service --since yesterday` prüfen

**Kernel-Modul:** `dmesg -T | grep -i error` prüfen

**UFW/Network/Log-Spam:** Ist es normaler Log-Spam (IPv6 multicast, WLAN auth) → rate-limit in `/etc/rsyslog.conf`

### Phase 6 — Bewertung + Dokumentation

Ergebnis nach P0/P1/P2 klassifizieren:

| Prio | Kriterium | Beispiel |
|------|-----------|---------|
| P0 | Akute Disk-Überlast (> 80 %), prognostizierte Voll-Lauf in < 7 Tagen | 6,4 GB syslog, +1 GB/Tag, Disk 82 % |
| P1 | System-Fix nötig (Service, Extension, Config), keine akute Bedrohung | logrotate Condition-Fix, size-Trigger ergänzen |
| P2 | Aufräumarbeiten, Monitoring verbessern, Doku aktualisieren | AGENTS.md-Disk-Schwelle anpassen, Tailscale DNS prüfen |

**Immer dokumentieren:** Ziel-Ordner `~/20-Workspace/results/` mit Datumsstempel.

### Phase 7 — Handlungsempfehlung

Die Empfehlung trennen in:

1. **Stop-the-Bleeding** (Jetzt, sofort wirksam) — zB `sudo logrotate -f`, Extension disablen
2. **Secondary-Fixes** (Heute/In dieser Session) — logrotate Override, size-Trigger
3. **Prevention** (Diese Woche) — Doku-Update, Monitoring, regelmäßiger Check

## Pitfalls

- **Nicht auf Zeilenanzahl allein verlassen** — Stack-Trace-Zeilen sind oft 10× größer als normale Zeilen. Immer Byte-Counting machen.
- **`sudo -n` blockt** ohne interaktives Passwort. Adm-Gruppe (`adm`) gibt lesenden Zugriff auf `/var/log/syslog`, aber nicht auf `/var/log/auth.log`. Für auth.log muss interaktives sudo her.
- **`logrotate -d` dry-run als non-root** gibt `EUID != 0`-Warnungen, die sind **erwartet und harmlos**. Der Plan wird trotzdem korrekt ausgegeben.
- **Logrotate-Skipping ist still** — bei `ConditionACPower=true` erscheint KEIN Fehler im syslog, nur eine `skipped because...`-Info-Zeile. Nicht übersehen.
- **Disk-Usage kann zwischen Boots springen** — ein Boot löscht oft /tmp und manche Caches. Immer `df -h /` nach Boot messen.
- **ZRAM verfälscht Disk-Rechenart** — 7,7 GB ZRAM schlucken 0 GB Platte (komprimierter RAM). `free -h` zeigt RAM, `df -h /` zeigt Disk. Beides messen.

## Referenz: Vollständige Diagnose-Kette (2026-07-16)

Für eine ausgearbeitete Example-Session siehe:
`~/20-Workspace/results/syslog-diagnosis-2026-07-16.md`

Tech-Stats des tatsächlichen Fundes:
- 10.901.678 gnome-shell-Zeilen (10,9 Mio) in 6 Tage
- 6.737 MB aus gnome-shell allein (99,5 % der Datei)
- Verursacher: `zorin-printers@zorinos.com` Extension (St-BoxLayout-Disposal-Error-Loop)
- Rotation: 3 von 5 Läufen wegen `ConditionACPower=true` auf Akku skipped
- Disk: 79 % → 82 % in 3 Tagen (+3 %-Punkte) bei ~1,3 GB/Tag
