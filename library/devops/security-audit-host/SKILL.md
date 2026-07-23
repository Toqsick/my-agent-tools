---
name: security-audit-host
title: "Security Audit — Host Layer (TPM, HSI, Secure Boot, SSH)"
description: "Use when assessing a Linux host for TPM, fwupd HSI, Secure Boot, SSH config, firewall, service-hardening gaps, or quick-fix cheatsheet. NOT for network/API audit (use security-audit-network) or secret-scanning (use security-audit-secrets)."
category: devops
version: '1.0'
created: '2026-07-23'
author: Yuno (split from system-security-audit)
lane: koenigin
agent: universal
trigger_keywords: ['tpm', 'fwupd', 'hsi', 'secure boot', 'ssh', 'firewall', 'hardening', 'service', 'host']
keywords: ['security', 'host', 'tpm', 'fwupd', 'ssh', 'firewall', 'hardening', 'linux', 'compliance']
related_skills: ['security-audit-network', 'security-audit-secrets']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from system-security-audit 2026-07-23)'

license: MIT
---

# Security Audit — Host Layer (TPM, HSI, Secure Boot, SSH)

_Extracted from system-security-audit on 2026-07-23._

## Ablauf

### 0. Multi-Scout Reconnaissance (optional, empfohlen)

**Wann:** System ist unbekannt, breiter Check gewünscht, "system check" oder "gib mir einen Überblick".
**Was:** 5 parallele Subagenten (delegate_task) scannen unabhängig verschiedene Aspekte.

**Scout-Zuordnung:**

| Scout | Fokus | Fragestellungen |
|-------|-------|-----------------|
| Scout 1 | Hardware & Disk | CPU/RAM/Disk-Belegung, Temperaturen, SMART-Health, Load |
| Scout 2 | Services & Container | systemd-Units, Docker, Cron, OOM-Kills, uptime, Failed-Units |
| Scout 3 | Security & Ports | offene Ports, Firewall-Status, SUID, sudoers (NOPASSWD), fail2ban |
| Scout 4 | Performance & Logs | System-Load, I/O-Wait, Log-Größe, dmesg-Errors, Swap, Kernel-Messages |
| Scout 5 | Network & Connectivity | Ping RTT, DNS, HTTPS-Erreichbarkeit, VPN-Status, Netzwerk-Interfaces |

**Ablauf:**
1. **Parallel feuern** — 5 Scouts über `delegate_task(tasks=[...])` starten
2. **Reports konsolidieren** — Ergebnisse aus allen Scouts lesen
3. **Scout-Bias erkennen** — Scouts übertreiben bewusst ("Gelb" = "Check mal selbst, vermutlich harmlos")
4. **CRIT-Finding-Verification** — JEDEN 🔴/P0-Befund mechanisch via `terminal()` re-verifizieren.
   **Warum:** Scouts nehmen temporale Snapshots — eine CPU von 87°C während des Scouts
   kann ein Burst sein (nach 2 min auf 61°C abgekühlt). Der Scout sieht nur seinen Moment.
   **Vorgehen:** Für jedes 🔴-Finding:
   - Ist der Zustand jetzt noch gleich? (z.B. `sensors | grep Package`)
   - Ist es ein Dauer- oder Momentanzustand? (z.B. Load-Vergleich)
   - Hat der Scout eine legitime Interpretation übersehen? (z.B. Docker-Container-Check)
   **Ziel:** Nur 🔴-Befunde, die bei Re-Verifikation noch bestehen, kommen in den Final Report.
5. **Deep Dive** — Jede Gelb-Flagge mit eigenem `terminal()` verifizieren (ohne sudo wo möglich)
6. **Sortieren** — Befunde in "ohne sudo ziehbar" vs "braucht sudo" gruppieren
7. **Sudo-Sammlung erstellen** — alle sudo-Befehle in ein Script packen (siehe Sudo-Sammlung Pattern)

**Wichtig:** Scouts können nicht sagen "das braucht sudo" — sie haben keinen Terminal-Zugriff.
Die Grenze "ohne sudo" vs "mit sudo" findest du erst in deinem eigenen Deep Dive heraus.

#### Ausgabe-Erwartung

Gib am Ende **keine** offene Frage ("soll ich das machen?"). Stattdessen liefere:
- Klare Liste der **ohne-sudo** Befunde (copy-paste-ready zum eigenen Ausführen)
- Klare Liste der **sudo-Befunde** als strukturiertes Script (siehe Sudo-Sammlung Pattern)
- Kein "vielleicht", kein "wenn du willst"

### Risiko-Sternchen für Sudo-Befehle

Jeder Befehl in der Sudo-Sammlung bekommt ein Sternchen-Rating:

| Symbol | Bedeutung | Beispiele |
|--------|-----------|-----------|
| ⭐ | read-only, kein System-Eingriff | `sudo ss -tlnp`, `sudo dmesg`, `sudo smartctl -H` |
| ⭐⭐ | ändert temporären Zustand, reversibel | `journalctl --vacuum-size=200M`, `apt install`, Log-Rotation |
| ⭐⭐⭐ | schreibt Configs, deaktiviert Dienste, persistent | `systemctl mask`, `iptables -A`, `ufw deny` |

Aus dem Rating folgt die Empfehlung: ⭐ immer sicher, ⭐⭐ nach kurzer Info ausführbar,
⭐⭐⭐ nur nach Zustimmung. Aber **nie** als offene Frage — als Info-Kommentar im Script.

### Sudo-Sammlung Pattern (Copy-Paste-Ready)

Sobald alle Deep-Dives durch sind und die sudo-Befehle feststehen: **ein einzelnes Script**
schreiben, das alle Befehle in nummerierten Blöcken mit Kommentaren enthält.

**Struktur:**
```bash
#!/bin/bash
set -euo pipefail

echo "═══════════════════════════════════"
echo "  BLOCK 1 — Diagnose-Lücken · ⭐"
echo "═══════════════════════════════════"
# Warum: Port 3000 lauscht world-bound, kein Prozessname ohne root
sudo ss -ltnp 'sport = :3000 or sport = :8200'

echo ""
echo "═══════════════════════════════════"
echo "  BLOCK 2 — Journal Vacuum · ⭐⭐"
echo "═══════════════════════════════════"
# Warum: 4.4 GB syslog, 356 MB journal — gibt ~200 MB frei
sudo journalctl --vacuum-size=200M --vacuum-time=7d
```

**Regeln:**
- Jeder Block hat einen Header mit Risiko-Sternchen
- Jeder Befehl hat einen Kommentar **warum** er da steht
- Kein `set -x` — der User soll lesen können, nicht rauschen sehen
- Gefährliche Blöcke sind auskommentiert (nur als Vorlage, nicht auto)
- Kein `sudo -v`-Prompt, kein Expect, kein Script das nach Passwort fragt
- Das Script wird nach `~/Documents/` gespeichert, nicht nach `/tmp/`
- Der User ruft es selbst auf: `bash ~/Documents/sudo-sammlung-*.sh`

**Beziehung zu linux-system-maintenance:** Die Sudo-Sammlung ist der Endpunkt
der System-Check-Pipeline. Der `linux-system-maintenance` Skill deckt das
eigentliche Disk-Cleanup ab (no-sudo first → sudo cleanups → document).
Die Sudo-Sammlung hier ist **reine Diagnose**, kein Cleanup.

### Fix-Block Delivery Pattern (Sequential Interactive)

**Wann statt Sudo-Sammlung:** Der User führt selbst aus (Terminal-Zugriff vorhanden),
will die Schritte **einzeln und sequentiell** bestätigen statt ein Script zu feuern.
Bevorzugt von erfahrenen CLI-Usern die jeden Schritt sehen und auf Fehler reagieren
wollen — die Alternativ-Variante zum Bulk-Script-Muster oben.

**Unterschied zur Sudo-Sammlung:**

| Aspekt | Sudo-Sammlung (oben) | Fix-Block (dieses Pattern) |
|--------|---------------------|---------------------------|
| Format | Ein Bash-Script | Mehrere unabhängige Code-Blöcke in .md |
| Ausführung | `bash script.sh` | User pastet Block für Block |
| Fehlerbehandlung | Script bricht ab | User korrigiert + sagt "weiter" |
| Bestätigung | Nach Script-Ende | Nach jedem Block |
| Zielgruppe | "Mach mal schnell" | "Zeig mir was passiert, Schritt für Schritt" |

**Struktur eines Fix-Blocks (Template):**

```markdown
### [A1] — [Kurzbeschreibung] ([Dauer])

```bash
# Vorher-Pflicht: Read-only Zustand erfassen
sudo ss -tlnp | grep :PORT

# Der Fix-Befehl
sudo <befehl>

# Nachher-Pflicht: Veränderung verifizieren
sudo ss -tlnp | grep :PORT
```

**Erwartetes Ergebnis:** [Konkrete, überprüfbare Aussage]
**Risiko:** ⭐/⭐⭐/⭐⭐⭐ (siehe Risiko-Sternchen oben)
```

**Drei Pflicht-Regeln:**
1. **Jeder Block hat einen Vorher-Befehl** — User sieht den Zustand vor dem Fix
2. **Jeder Block hat einen Nachher-Befehl** — User sieht die Veränderung
3. **Erwartetes Ergebnis ist überprüfbar** — keine "sollte funktionieren"-Schwammigkeit

**Vierte Regel: Erklären VOR den Blöcken (explain-before-code).**
Der User hat in der 2026-07-16 Session explizit nachgefragt: "was machen die befehle genau?" — nachdem COPY-PASTE-Blöcke ohne Erklärung präsentiert wurden. Fix:
1. Gib zuerst einen **Erklärungs-Table** mit Block-ID, was passiert, erwartetem Effekt, Risiko-Sternchen
2. **Dann** die Code-Blöcke zum Pasten
3. User sagt Block-ID → führt aus → bestätigt "done"
4. **Erst dann** den nächsten Block ausgeben (nicht alle auf einmal außer User sagt explizit "alle")

**Beispiel (validiert 2026-07-16):**
```markdown
| Block | Befehl | Was passiert | Effekt | Risiko |
|-------|--------|------------|--------|--------|
| A1 | `logrotate -f` | Rotiert syslog sofort | 6,4 GB → 27 KB | ⭐ reversibel |
| A2 | `override.conf` | Erlaubt Rotation auf Akku | Verhindert Wiederholung | ⭐⭐ persistente Config |
```
Dann die Blöcke einzeln ausgeben.

**Workflow (validiert 2026-07-16, System-Audit Basti):**

```
1. Agent generiert fix-blocks.md in ~/20-Workspace/results/fix-<thema>-YYYY-MM-DD.md
   → Jeder Block unabhängig, nummeriert, mit Erwartungs-Angabe
2. User sagt "A1 los" → führt Block A1 im Terminal aus (eigenes PWD, eigener TTY)
3. Agent zeigt After-Snapshot + nächsten Block
4. User sagt "A1 done" → Agent markiert als completed in Todo-Liste
5. → Repeat für A2, A3... in beliebiger Reihenfolge (User bestimmt Ordnung)
```

**Benennungskonvention:**
- File: `~/20-Workspace/results/fix-<audit-thema>-YYYY-MM-DD.md`
- Blöcke: `A1`, `A2`, `A3` (logisch gruppiert), `B1`, `D`
- Block-Namen: `A1 — Sofort-Hygiene (90 Sek)`, `B1 — UFW-Fronting (15 Sek)`

**Verifikation nach jedem Block:** Agent zeigt df/ss/ps-Output, User bestätigt mit
"done", erst dann nächster Block. So bleibt der User im Loop und der Agent sieht
jede Veränderung live.

**User-Ordering (validiert 2026-07-16):** Basti gab die Reihenfolge "d nach b1 nach a"
an — der Agent generierte alle Blöcke auf einmal, legte sie numerisch vor, und ließ
den User die Reihenfolge bestimmen. **Niemals die Reihenfolge vorgeben — stattdessen
alle Blöcke als Optionen A/B/C/D oder nummeriert präsentieren und den User wählen
lassen.** Das ist der Kernunterschied zum Sudo-Sammlung-Script, das eine feste
Ausführungsreihenfolge hat.

Siehe `references/fix-block-delivery-pattern.md` für das konkrete Template + Case
Study (2026-07-16 Audit mit A→B1→D Ausführungsreihenfolge).

Zusätzlich im Post-Run-Learnings-Abschnitt (unten): ✅ Fix-Block-Delivery-Pattern validated (2026-07-16).

### 1. Netzwerk & offene Ports

```bash

set -euo pipefail
# Firewall-Status
sudo ufw status

# Offene Ports (lauschende Dienste)
ss -tlnp

# Dienste die auf 0.0.0.0 lauschen (von außen erreichbar!)
ss -tlnp | grep -E "0.0.0.0:|:::|:\*"

# SSH-Server prüfen
systemctl is-active sshd
```

Für jeden Dienst auf `0.0.0.0:` prüfen: Braucht der wirklich Netzwerkzugriff? Sonst auf localhost beschränken per UFW oder Config.

### 2. Berechtigungen

```bash

set -euo pipefail
# Sensitive Configs
ls -la ~/.gmail-organizer.json  # sollte 600 sein
ls -la ~/.hermes/config.yaml     # sollte 600 sein
ls -la ~/.ssh/                   # sollte 700 sein, keine fremden Keys

# HERMES-SPEZIFISCH: Session-DB, Logs, Snapshots
# state.db enthält den kompletten Sitzungsverlauf (~90MB+)
ls -la ~/.hermes/state.db ~/.hermes/kanban.db
# → sollten 600 sein (waren 644 = world-readable!)

# Logs können API-Keys und Tokens enthalten
ls -la ~/.hermes/logs/
# → agent.log, errors.log sollten 600 sein

# Snapshots = Session-Backups (ebenfalls sensitiv!)
ls -lad ~/.hermes/state-snapshots/
ls -la ~/.hermes/state-snapshots/ 2>/dev/null | head -5
# → Verzeichnis sollte 700 sein, dateien 600

# Config-Backups (enthalten oft API-Keys)
ls -la ~/.hermes/config.yaml.bak.* 2>/dev/null
# → sollten 600 sein

# Sicherheitslücken-Ranking: state.db > logs > snapshots > config-backups

# Weltlesbare Dateien in $HOME (außer .py, .md, .txt, Bilder)
find ~ -maxdepth 2 -type f -perm -o+r ! -name "*.py" ! -name "*.md" ! -name "*.txt" 2>/dev/null | head -20
```

### 3. Dienste & Autostart

```bash

set -euo pipefail
# Alle laufenden Dienste
systemctl list-units --type=service --state=running | head -30

# Kritische Dienste checken:
for svc in nvidia-powerd gamemoded ollama rygel sshd; do
    systemctl is-active "$svc" 2>/dev/null
done
```

Bei jedem Dienst: Wird er gebraucht? Wenn nein, stop + disable.

### 4. Benutzer & Zugänge

```bash

set -euo pipefail
# Benutzer mit Shell
sudo cat /etc/passwd | grep -E "/home|/bin/bash" | cut -d: -f1,3,7

# Leere Passwörter
awk -F: '($2==""){print}' /etc/shadow 2>/dev/null

# NOPASSWD in sudoers
sudo cat /etc/sudoers 2>/dev/null | grep -i NOPASSWD
sudo cat /etc/sudoers.d/* 2>/dev/null | grep -i NOPASSWD

# Passwort-Hashing (sollte yescrypt oder sha512 sein)
cat /etc/pam.d/common-password | grep pam_unix
```

### 5. Updates

```bash

set -euo pipefail
apt list --upgradable 2>/dev/null | grep -c "/"
flatpak update 2>/dev/null | grep -c "Updating\|Installing"
```

### 6. Bewertung & Doku

Jeden Fund kategorisieren:

| Farbe | Bedeutung |
|-------|-----------|
| 🟢 **✅** | Sicher / korrekt |
| 🟡 **⚠️** | Auffällig — Verbesserung möglich |
| 🔴 **❌** | Kritisch — sofort fixen |

Für jeden 🔴/🟡-Fund notieren:
- Was genau ist das Problem
- Welches Risiko besteht
- Wie es zu beheben ist (genauer Befehl)
- Ob der User zustimmen muss

## Agent-Config Security Audit

**Gegenstand:** Die laufende Hermes/Agent-Config (`~/.hermes/config.yaml`,
`~/.hermes/profiles/*/config.yaml`) gegen die Repository-Vorlage (Template) prfen.
Findet Konfig-Drift, fehlende Security-Blcke, falsche Permission-Settings,
fehlende Limits.

---
---

## Post-Run Learnings (2026-07-13 Audit)

> **Quelle:** Recon-Phase `security-audit-2026-07-13.md` (3 Scouts, 1m44s).
> Diese Learnings ergänzen das obige Pattern — sie ersetzen es nicht.

## Post-Run Learnings (2026-07-16 — Queen-Recon-First Pattern)

> **Quelle:** Sicherheitsaudit `security-audit-2026-07-16.md` (Königin-Recon + 3 Targeted Deep-Dive Bees, ~10 Min Wall-Time).
> **Validierung:** Recurring audit mit vorhandener Baseline (2026-07-13). 2× P0 gefunden und priorisiert.
>
> **Kontext:** Dieses Pattern ergänzt Section 0 (Multi-Scout Reconnaissance). Section 0 ist der Default für UNBEKANNTE Systeme.
> Queen-Recon-First ist der Default für WIEDERKEHRENDE Audits mit vorhandener Baseline.

### Queen-Recon-First: Fast-Track für Recurring Audits

**Problem:** Section 0 dispatcht Scouts als ERSTEN Schritt — ideal für unbekannte Systeme, aber Overkill für wiederkehrende Audits MIT vorhandener Baseline. Scouts brauchen 3–5 Min Warmup + Konsolidierung, bevor die Queen einen P0-Triage hat.

**Lösung (validiert 2026-07-16):** Queen macht Recon INLINE (15+ terminal/execute_code-Calls in ~2 Min), identifiziert P0-Kandidaten aus dem Snapshot + Diff zur letzten Baseline, DANN dispatcht sie gezielte Deep-Dive-Bees auf konkrete Findings.

**5-Phasen-Struktur:**

```
Phase 1 — Königin-Recon (inline, read-only, ~2 Min)
  ├── Disk/CPU/RAM Snapshot         (df -h, free -h, uptime, load)
  ├── Port-Listener-Scan            (ss -tlnp, ss -tupn, ps -eo pid,ppid,etime,user,comm)
  ├── Systemd-Health                (systemctl --failed, systemctl list-units --state=running)
  ├── Log-Größen                    (du -sh /var/log/syslog, du -sh /var/log/journal)
  ├── Prozess-Tree + Boot-Zeit      (who -b, ps --sort=-etime | grep <service>)
  ├── Netzwerk-Health               (tailscale status, tailscale netcheck)
  ├── Cron-Check                    (crontab -l, Count-Vergleich)
  └── Drift-Vergleich               (Diff-Tabelle: besser / unverändert / neu seit letztem Audit)

Phase 2 — Queen P0-Triage (aus Recon + Diff)
  ├── P0-Kandidaten identifizieren (max 2, realistische Dichte)
  ├── P1-Health-Check identifizieren (max 1)
  └── Entscheidung: dispatchen oder eigene Tiefe?

Phase 3 — Targeted Deep-Dive Bees (parallel, background)
  ├── Biene 1: P0 — externer Service / Gateway / Expositions-Prüfung
  ├── Biene 2: P0 — System-Integrität / Logs / Disk-Wachstum
  └── Biene 3: P1 — Hermes-Health / Cron / Prozess-Leakage (Supporting)

Phase 4 — Queen schreibt Report (parallel zu Bees!)
  ├── Schnellstart: Report-Template aus letztem Audit kopieren oder Skeleton schreiben
  ├── Während Bees laufen: Findings-Tabelle + Drift-Sektion + A/B/C/D-Optionen
  ├── Read-only Disclaimer + Subagent-Status (noch laufend)
  ├── Report wird in ~/20-Workspace/results/ geschrieben
  ├── **Nicht auf Bees warten** — Phase 4 liefert den Report AUS, während Bees noch laufen
  └── Skeleton-Strategie (validiert 2026-07-16):
      - Queen hat Report nach ~8 Min geschrieben (14:22), Bees kamen um 14:33
      - Struktur steht, Treiber-Tabelle steht, Fix-Optionen stehen
      - Nach Bees: 3× Patch-Operationen auf den Report (statt komplett neu schreiben)
      - Gewinn: ~5 Min Wall-Time gespart

Phase 5 — Bees liefern nach → Report patchen
  ├── Bienen-Ergebnisse als Update in den bestehenden Report integrieren
  ├── Nicht neu schreiben — patchen! (3× patch in <2 Min)
  ├── Bienen-Subagent-Outputs als Zitate in die Findings-Sektion einbauen
  └── Anhang aktualisieren: Dauer, Tool-Calls, Outcome jedes Bees
```

**Warum 3 Bees statt 5 Scouts für RECURRING Audits:**

| Aspekt | Multi-Scout (Section 0) | Queen-Recon-First (2026-07-16) |
|--------|------------------------|-------------------------------|
| Vorbereitung | 5 Scouts × 30-60s Warmup = 3-5 Min | Queen ~2 Min inline |
| P0-Triage | Nach Scout-Landung | Bereits während Recon |
| Report-Beginn | Nach Scout-Landung + Konsolidierung | Parallel zu Bees (Phase 4) |
| Bee-Fokus | Generisch (Hardware, Services, Security...) | Targeted auf konkrete Findings |
| Baseline-Nutzung | Keine (Scout scannt immer frisch) | Diff gegen Vor-Audit (Phase 1 integriert) |
| Wall-Time (total) | ~8-12 Min bei 2 Wellen | ~5-8 Min inkl. Report |
| False-Positive-Rate | Höher (Scouts sehen temporale Snapshots) | Niedriger (Queen triagiert während Recon) |

**Entscheidungsmatrix:**

| Situation | Pattern | Begründung |
|-----------|---------|-----------|
| Erster Audit, keine Baseline | Section 0 (Multi-Scout) | Breite Coverage nötig |
| Wiederkehrender Audit, Vorlage existiert | Queen-Recon-First | Schneller, fokussierter, Diff nutzbar |
| User sagt "schnell mal checken" | Queen-Recon-First (Mini) | Inline + max 1 Bee, ~3 Min |
| User sagt "tiefer Audit, alles" | Hybrid: Queen-Recon-First + Section 0 | Queen für Tiefe, Scouts für Breite |

### Baseline-Comparison Pattern (Drift-vs-Last-Audit)

**Wertvollster Zusatz bei wiederkehrenden Audits:** Eine Tabelle die zeigt, was sich seit dem letzten Audit verändert hat. Der User sieht sofort: wurde meine letzte Aktion wirksam? Gibt es neue Risiken?

**Struktur (validiert 2026-07-16):**

```markdown
## Drift vs. [Vor-Audit-Datum]

### ✅ Besser
| Item | Vorher | Jetzt | Hinweis |
|---|---|---|---|
| NVIDIA-Treiber | 3 Units failed | Alle aktiv | Treiber-Update oder Config-Fix |
| Failed-Units | 3 (nvidia, ...) | 0 | — |

### ⚖️ Unverändert
- [Liste der Punkte die stabil sind — kein Handlungsbedarf]

### ⚠️ Neu seit [Vor-Audit]
| Neu | Detail | Severity |
|---|---|---|
| Gateway auf 0.0.0.0:8642 | War not-found, jetzt reaktiviert | P0 klären |
| Syslog-Wachstum 6,4 GB | 1 GB/Tag, Trend steigend | P0-B |
```

**Wann diese Tabelle weglassen:** Erster Audit (keine Baseline vorhanden).

### Targeted-Bee-Briefing (abweichend von Section 0 Scouts)

Anders als Section 0 Scouts (generische Foki: Hardware, Services, Security, Performance, Network) bekommen Deep-Dive-Bees ein **konkretes P0-Finding als Thema** mit Phasen aus dem Layer-4-Audit (für Services) oder aus dem Log-Analyse-Pattern (für Logs):

**Briefing-Struktur für Deep-Dive Bees:**
```
Du bist Biene <N> in Yunos Security-Audit-Schwarm.

KONTEXT:
- Host: [Hostname] · Kernel [Version]
- Audit-Zyklus: [Datum], Baseline [Vor-Datum]
- Queen-Recon-Befund: [P0/P1 Finding Beschreibung]

DEINE TASKS (ALLES READ-ONLY):
1. [Konkrete Diagnose-Schritt 1 — Datei/Port/Kommando nennen]
2. [Konkrete Diagnose-Schritt 2]
3. [Optionale Sub-Aspekte]

OUTPUT-CONSTRAINTS (PFLICHT):
- Rein Text in deiner Antwort (kein File-Write)
- Pro Finding: Pfad + konkrete Zahlen
- SELF-REPORT am Ende: N tool-calls, M findings

MAX <8-15> tool-calls. Nach Limit Synthese mit was du hast.
```

**Wichtig:** Das Briefing enthält NIE die Queen-Vermutung als gesicherten Befund — nur als Hinweis ("Queen-Recon hat gefunden: ..."). Die Biene muss bestätigen oder widerlegen.

### 3-Bee-Scope-Design Heuristik (validiert 2026-07-16)

Die 3 Bienen im Audit-Schwarm decken maximal 2 P0-Ebene + 1 P1-Ebene ab:

```
Biene 1: P0 — externer Service / Gateway / Expositions-Prüfung
         → Layer-4-Audit-Phasen (Route Probing, Auth, Network Exposure, Config Tracing, Lifecycle)
Biene 2: P0 — System-Integrität / Logs / Disk-Wachstum
         → Log-Größen-Trend, Rotations-Status, Haupt-Verursacher
Biene 3: P1 — Hermes-Health / Cron / Prozess-Leakage (Supporting)
         → Container-Count, Prozess-Watchdog, Cron-Coverage
```

**Warum 3 statt 5:**
- Max 2 P0-Findings pro Audit-Session (mehr ist ungewöhnlich für einen stabilen Desktop)
- 1 P1-Health-Check rundet das Bild ab
- 5 Bees bräuchten P0×3 + P1×2 — unrealistische Finding-Dichte
- 3 Bees erzeugen genug Output für einen substanziellen Report

**Fallback bei weniger Findings:** Wenn die Queen nur 1 P0 findet → 2 Bees: 1× P0 Deep-Dive + 1× P1 Health. Kein künstlicher dritter Bee. Wenn 0 P0 → kein Schwarm nötig (Queen macht alles inline).

### ✅ Was gut funktioniert hat
- **3-Scout-Pattern (statt 5)** reicht für „Basti will Überblick": maxclaw-Live-Script
  (Recon), Live-System-State (Firewall/Listeners/Perms), Drift-Check (Doc vs Live).
  Bei 5 Scouts war die 5. Scout-Achse (Network/Ping) redundant, weil Scout 2+3
  schon `ss -tlnp` und `tailscale` abdecken.
- **Re-Verifikation von P0 vor Final-Report** (Schritt 4) hat heute einen
  entscheidenden Bug gefunden: MaxClaw-Script v1.0.0 P0-Flag
  `P0.backup.secretref_exists` war Stale-Pfad-False-Positive (greift auf
  `~/.openclaw/out` zu, das seit 2026-07-04-Restruktur nicht mehr existiert).
  Wäre ohne Re-Verifikation als echte P0 in den Report gewandert.
- **Sudo-Sammlung-Pattern** ist Gold wert: alle 4 Optionen A–D als
  Copy-Paste-Runbook in `~/20-Workspace/results/security-audit-2026-07-13-actions.md`
  ausgelagert, User führt selbst aus. **Subagents dürfen NIEMALS sudo-Passwörter
  speichern oder via TTY-Bypass sudo erzwingen.**
- **Fix-Block-Delivery-Pattern** validiert (2026-07-16): Light-Weight-Alternative
  zum Sudo-Sammlung-Script für sequentielle, interaktive Ausführung. User paster
  Block für Block, bestätigt "done" nach jedem, Reihenfolge selbst bestimmt.
  Siehe `references/fix-block-delivery-pattern.md`.

### ⚠️ Echte P0/P1 sind selten — die meisten „Findings" sind Tool-Artefakte
- **Stale-Path-False-Positives** sind das größte Problem bei selbstgebauten
  Audit-Scripts. Wenn ein Script `~/.openclaw`, `~/greyhack-tools` oder
  `/tmp/maxclaw-clone` referenziert und die Cluster-Struktur sich ändert, werden
  diese Pfade zu permanenten P0-Flags.
- **Config-Key-Checks ohne Verifikation, ob die Keys konsumiert werden**, sind
  Müll. Heute: 5× P1 in MaxClaw-Script für `write_paths`, `monthly_limit_eur`,
  `git push main`, `sudo deny` — das installierte Hermes liest KEINEN dieser
  Keys (verifiziert via `grep -rE 'write_paths|monthly_limit_eur' ~/.hermes/`
  lieferte 0 Treffer im Hermes-Code).
- **Score-System ist irreführend**: MaxClaw-Score 0 → 19 zwischen 2026-07-05
  und 2026-07-13, weil das Script **mehr** P1-Flags hinzugefügt hat (nicht
  weil die Lage besser geworden ist). Score reflektiert Script-Coverage, nicht
  Real-Risk.

### 🔧 Konkrete Skill-Ergänzungen für die nächste Recon
1. **Bei Tailscale präsenter Box** (heute entdeckt: 4× Listener auf
   `100.96.90.61:443/8443/8444/8446`): IMMER `tailscale serve status` und
   `tailscale funnel status` separat listen — die Loopback-Baseline reicht
   nicht, Tailnet-IPs sind externe Exposition.
2. **NVIDIA-Persistenz-Check** in den 5-Scout-Block aufnehmen:
   `systemctl status nvidia-powerd nvidia_oc nvidia-persistence` — alle drei
   können nach Treiber-Updates failed sein (heute: `DriverNotLoaded` /
   `Allocate Root client failed 0x59`).
3. **`/var/log/syslog` immer mit `du -sh` listen** — bei 3+ GB ist das ein
   eigener Finding („log rotation missing"), nicht nur eine Info.
4. **`crontab -l` zählen** und mit Vorlauf-Audit vergleichen. Heute: 3 → 15
   Einträge seit 2026-07-05 (10 neue). Kein Security-Risiko, aber
   Konsolidierung-Kandidat.
5. **Drift-Check gegen `~/AGENTS.md` und `~/CLAUDE.md`** — diese Doku driftet
   ständig. Heute: `navigation.md` Header sagt `Shell: fish` (soll bash),
   AGENTS.md sagt Disk-Use 65–75 % (tatsächlich 79 %).
6. **`ConditionACPower=true` auf logrotate.service prüfen** (2026-07-16 entdeckt):
   ```bash
   grep ConditionACPower /lib/systemd/system/logrotate.service
   systemctl show -P ConditionACPower logrotate.service
   journalctl -u logrotate --since "7 days ago" | grep -c "skipped"
   ```
   Diese Condition blockiert logrotate stillschweigend auf Akku. Bei Notebooks
   mit häufiger Akkunutzung ist ein Override `ConditionACPower=` (leer) nötig
   um Rotation zu ermöglichen. **Nicht auto-fixen — erst Bericht, dann Freigabe.**
7. **Zorin-OS-Defekt-Extensions erkennen** (2026-07-16 entdeckt):
   Extension `zorin-printers@zorinos.com` verursachte 99,5 % des syslog-Volumens
   (10,9 Mio Zeilen = 6,4 GB in 5 Tagen) durch `Object has been already disposed`/
   `clutter_text_* assertion failed`-Stacktraces in Endlosschleife. Prüfe Aktivität:
   ```bash
   gnome-extensions list --enabled
   # Bei Verdacht: syslog Top-5 nach Tag + Prozess mit awk-Byte-Count
   sudo awk '{a[$5]++} END{for(p in a) printf "%s\t%d\n", p, a[p]}' /var/log/syslog | sort -k2 -rn | head -5
   ```

8. **rsyslog Audit-by-Source, NICHT by Token** (2026-07-17 entdeckt — kritischer Pitfall):
   Wenn `/var/log/syslog` aufgebläht ist, NICHT `awk '{print $5}' | sort | uniq -c` benutzen
   um den Top-Verursacher zu finden — das zählt Wörter (Tokens), nicht Prozesse. Im 17.07-Audit
   lieferte das `4.49M "to"-Tokens`, was wie ein generisches Log-Rauschen aussah. Die echte
   Quelle war Ollama-C++-Template-Output in EINEM Prozess (`ollama[138740]:`).

   **Richtige Reihenfolge:**
   ```bash
   # Schritt 1: Wer schreibt überhaupt? (Source-Count, IMMER zuerst)
   grep -c "ollama\[" /var/log/syslog       # 66.639 (echte Source)
   grep -c "zorin-printers" /var/log/syslog # 22 (Filter wirkt)
   grep -c "kernel\[" /var/log/syslog       # 4.5K

   # Schritt 2: Optional — Token-Drilldown INNERHALB der dominanten Source
   awk '/ollama\[/{print $5}' /var/log/syslog | sort | uniq -c | sort -rn | head -5
   ```

   **Lehre:** Audit-by-Source ist die Wahrheit, Audit-by-Token ist nur Detail-Drilldown
   NACH der Source-Identifikation. Verwechslung kann zu stundenlanger Fehldiagnose führen
   ("log rotation missing" statt "neuer Spam-Vektor in altem Programm").

9. **Ollama 0.30.11 print_timing-Debug-Spam als Log-Bomb** (2026-07-17 entdeckt — neuer Vektor,
   distinkt vom 16.07 zorin-printers-Loop):
   Ollama emittiert bei aktiver Modell-Ausführung INFO-Level-Zeilen mit Tokens wie
   `slot get_availabl`, `launch_slot_`, `srv  get_availabl`, `print_timing`, `operator()`. In
   44h erzeugte das 2.7 GB / 4.5M Zeilen Syslog. Der 16.07-Filter `if $msg contains "clutter_text"`
   wirkt NICHT (anderes Programm, andere Tokens).

   **Zwei Fix-Optionen (Wurzel vs. Symptom):**

   ```bash
   # Option B (empfohlen, Wurzel): Logging-Level in Ollama-Server dämpfen
   sudo mkdir -p /etc/systemd/system/ollama.service.d
   sudo tee -a /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
   Environment="OLLAMA_DEBUG=0"
   Environment="OLLAMA_LOG_LEVEL=warn"
   EOF
   sudo systemctl daemon-reload
   sudo systemctl restart ollama   # Modelle werden kurz entladen, re-loaden on-demand

   # Option A (Symptom, analog zu 16.07): rsyslog-Filter (nur wenn Option B nicht greift)
   # ACHTUNG: $programname == "ollama" blanket blocken ist gefährlich — Ollama-Errors
   # gehen durch dieselbe Facility und MÜSSEN fließen. Stattdessen Token-spezifisch filtern:
   sudo tee /etc/rsyslog.d/10-ollama-print-timing-suppress.conf <<'EOF'
   if $programname == "ollama" and $msg contains "print_timing" then stop
   if $programname == "ollama" and $msg contains "slot get_availabl" then stop
   if $programname == "ollama" and $msg contains "slot launch_slot_" then stop
   if $programname == "ollama" and $msg contains "srv  get_availabl" then stop
   EOF
   sudo systemctl reload rsyslog
   ```

   **Detection-Pattern für künftige Audits:**
   ```bash
   # Wenn /var/log/syslog > 1GB ohne klare Ursache:
   for src in ollama zorin-printers kernel gnome-shell tailscaled; do
     printf "%-15s %s\n" "$src" "$(grep -c "$src\?\[" /var/log/syslog 2>/dev/null || echo 0)"
   done
   journalctl -u ollama --since "1 hour ago" | wc -l   # unabhängige Cross-Check
   ```

   **Beziehung zu 16.07 zorin-printers-Filter:** Beide Vektoren teilen das Pattern
   "Programm X loggt in Endlosschleife". Filter funktioniert immer nur für den
   spezifischen Programm/Token — neuer Vektor braucht neuen Filter oder besser
   eine Wurzel-Fix (Log-Level runter). Vor jedem neuen Filter: Re-Verify ob der
   vorherige Vektor wirklich tot ist (`grep -c "<alt-pattern>"`), nicht nur dass
   syslog wächst.

10. **Drift-Aware Security Audit Report Pattern** (2026-07-17, validiert beim
    recurring System-Audit; **erweitert 2026-07-18** um CLAUDE.md-Drift-Sektion
    und logrotate-SUCCESS-≠-Rotation-Pitfall): Wenn ein Audit gegen eine
    **vorhandene Baseline** läuft (z.B. ein vorheriger Audit-Report existiert),
    wird der Report erheblich wertvoller mit folgenden 4 Strukturelementen.
    Siehe `references/drift-aware-audit-report.md` (v2.0) für die vollständige
    aktuelle Version:

    - **Reality-Check vs. plan** — Jede Plan-Annahme wird mit Live-Evidenz
      abgeglichen (Disk, Service-State, Filter-Wirkung).
    - **Drift vs. previous audits** — Explizite Cross-Referenz (16.07 → 17.07 →
      18.07), fängt Vektor-Verwechslungen (z.B. zorin-printers vs. Ollama).
    - **Read-only Disclaimer** — Setzt den Vertrag: Findings = Proposed-Fixes
      mit exakten Befehlen + Risiko-Sternchen, NICHT Auto-Aktionen.
    - **CLAUDE.md/AGENTS.md Drift-Sektion (NEU 2026-07-18)** — Projekt-Context-
      Files driften genauso wie das Live-System. Der 18.07-Scan fand 4 Drifts in
      CLAUDE.md (Ollama-state, Disk-Zahlen, .steampath-Referenz, fehlender
      CPU-temp Watch-Item). Der Audit-Report validiert jetzt explizit Doku-
      Fakten gegen Live-Reality und listet Korrekturvorschläge.

    **Logrotate-Pitfall (NEU 2026-07-18):** `systemctl status logrotate.service`
    kann `Deactivated successfully` melden, während die `size 500M`-Regel nie
    beim Timer-Tick evaluiert wurde → 3.45 GB syslog bleibt unrotiert.
    **Fix:** `sudo logrotate -f /etc/logrotate.d/rsyslog` erzwingt sofortige
    Rotation unabhängig von Conditions.

    Hinweis: Das `syslog-source-first-audit`-Skill (hub-installed) enthält die
    komplementäre Loganalyse-Methodik und den Drei-Fenster-Wachstumsverifikations-
    Schritt (Schritt 4a, validiert 2026-07-18).

8. **Peripherals-Check vor Service/Extension-Disable-Empfehlung** (2026-07-16, validiert):
   **Problem:** Die `zorin-printers`-Extension flutete 6,4 GB Syslog. Erster Reflex: "Deaktiviere die Extension". User-Frage: "warum die drucker aus?" → Basti hat einen **3D-Drucker** am Laptop.
   **Fix:** Statt Disable → Log-Filter in rsyslog (`/etc/rsyslog.d/00-gnome-shell-bug-suppress.conf`) mit `if $msg contains "clutter_text" then stop`.
   **Regel:** Bevor du einen Service, eine Extension oder ein Device deaktivierst:
   1. Check User-Profile-Memory: hat Basti Hardware die diesen Service braucht? (Drucker, Scanner, Webcam, GPU-Tools)
   2. Wenn ja: Filter-Lösung bevorzugen (rsyslog drop-in, logrotate size-trigger, log-level-senken)
   3. Extension-Disable ist der letzte Ausweg, nicht erster.
   4. Ausnahme: Service ist sicherheitskritisch (SSH auf World-Listener, RDP) → dann Disable trotz Hardware-Präsenz.

### 🚫 Was NICHT mehr in Recon-Berichten stehen sollte
- „MaxClaw-Score X/100" — Score ohne Baseline-Kontext wertlos
- „Tool-Flag P0 für Pfad Y, der nicht existiert" — Stale-Path, ignorieren
- „Config-Key X fehlt" — ohne Verifikation, ob Key konsumiert wird, ist die
  Flag Rauschen

### ✅ Tailscale-Dead-Listener-Triage (2026-07-13 Tailscale C)

→ `references/tailscale-dead-listener-triage.md` — Vollständiges 6-Schritt-Protokoll + Bulk-Scan-Script + Case Study (tokentelemetry stale path).

**Warum das wichtig ist:** Stale systemd-Units sind lautlos. Der Service ist `disabled` + `inactive`,
der Tailscale-Listener zeigt noch die alte Route, aber niemand antwortet auf dem Backend.
Der User merkt es erst beim ersten Zugriff. Ein Bulk-Scan aller Units findet es sofort.

### ✅ Subagent-Schätzungen immer live verifizieren (2026-07-13)

**Lektion:** Heute schätzte ein Scout "syslog = 3,5 GB" — live `du -sh` zeigte 3,3 GB.
Kein Weltuntergang (~6 % Abweichung), aber zeigt: Subagenten geben **konsistente aber
nicht exakte** Messungen zurück, weil ihr `df`/`du`-Snapshot im Moment ihrer Ausführung
genommen wird und sie nicht auf zwischenzeitliche Log-Rotation warten.

**Faustregel für Scout-Auswertung:**
- Größenangaben > 10 % vom Live-Wert entfernt → explizit im Report vermerken ("Scout schätzte X, live Y")
- Dateizählungen (`wc -l`, `find ... | wc -l`) sind meist exakt (kein Zeitreihen-Problem)
- ALLE 🔴/P0-Befunde live re-verifizieren (das Pattern existiert schon in CRIT-Verification)
- Milde Größenangaben (5–10 % Abweichung) nicht als "Scout-Fehler" framen — sie sind
  temporale Snapshots und per Definition nicht präzise genug für 1-%-Genauigkeit

### 📌 Wenn du „D-Rewrite" hörst: zuerst Skill checken
Bevor du ein neues Audit-Script schreibst: **guck in `~/.hermes/skills/devops/`
nach** — es gibt schon `system-security-audit` (v1.1.1, dieses Skill) UND
`claude-security-auditor` (read-only Recon default). Doppel-Arbeit vermeiden.

Siehe auch `references/decommission-stub-pattern.md` — die vollständige Checkliste wenn ein
Legacy-Script stillgelegt und durch Skill ersetzt wird.


Dieser Audit-Typ untersucht nicht das Host-System (siehe Host-Sektionen oben),
sondern die *Agent-Konfiguration selbst* — die zweite Sicherheitsschicht.

### Wann ausfhren

- Nach Repo-Wechsel / Config-Migration
- Wenn der User "hardening", "security audit" oder "config check" sagt
- Nach Skill-Installationen (Skills knnen Config-Blcke berschreiben)
- Periodisch (monatlich) zur Erkennung von Konfig-Drift

### Phasen-Workflow (adaptiert aus GreyHack)

| Phase | Fokus | Typische Checks |
|-------|-------|-----------------|
| 0 | Backup/SecretRef | Snapshot-Alter, Secret-Backend-Existenz, Key-Rotation |
| 1 | User-Audit | Agent luft als root? ~/bin-Ownership? |
| 2 | Port-Audit | Gateway-Bind (127.0.0.1?), world-listening Services |
| 3 | Egress/Firewall | ufw aktiv? DNS fr Allowlist-Hosts? |
| 4 | Permission-Check | default: deny, write_paths, deny-lists, world-writable Files |
| 5 | Trace/Cron | Root-Cron, Git-Branch, uncommitted Changes |
| M | Modell-Limits | monthly_limit_eur, Heartbeat-Budget, Provider-Konfig |

#### Phase 0: Backup / SecretRef-Status

```bash

set -euo pipefail
# Secret-Backend (OpenClaw SecretRef oder Hermes-nativ?)
ls -la ~/.openclaw/out/ 2>/dev/null || echo "SecretRef fehlt — Hermes-native?"
ls -la ~/.hermes/auth.json 2>/dev/null

# Config-Sicherung — Alter ermitteln
SNAP=$(ls -t ~/.hermes/state-snapshots/ 2>/dev/null | head -1)
[ -n "$SNAP" ] && echo "Letzter Snapshot: $(stat -c %y ~/.hermes/state-snapshots/$SNAP | cut -d. -f1)"
BACKUP=$(ls -t ~/.hermes/config.yaml.bak.* 2>/dev/null | head -1)
[ -n "$BACKUP" ] && echo "Letztes Config-Backup: $(stat -c %Y "$BACKUP")"
```

**Threshold:** SecretRef muss existieren ODER Hermes-native mit 0600. Snapshot max 14 Tage alt.

#### Phase 1: User-Audit

```bash

set -euo pipefail
[ "$(id -u)" -eq 0 ] && echo " Agent luft als root!"
ls -ld ~/bin/ ~/bin/*.sh 2>/dev/null | grep -v "$(id -un):$(id -gn)" | head -3
```

**Threshold:** Agent uid != 0. Falls uid 0: P0-Finding, sofort stoppen.

#### Phase 2: Port-Audit (Gateway)

```bash

set -euo pipefail
# Gateway auf 127.0.0.1? (NIE 0.0.0.0)
ss -tlnp | grep 18789 | grep -v "127.0.0.1:" && echo " Gateway auf 0.0.0.0!"
# Alle world-listening Ports katalogisieren
ss -tlnp | grep "0.0.0.0:" | grep -v "127.0.0.1:" | head -10
```

**Threshold:** Gateway nur auf 127.0.0.1. World-listening-Ports dokumentiert und begrndet.

#### Phase 3: Egress / Firewall

```bash

set -euo pipefail
ufw status 2>/dev/null | grep -q "Status: aktiv" || echo " ufw inaktiv"
for host in openrouter.ai api.telegram.org github.com; do
    host "$host" >/dev/null 2>&1 || echo " DNS-Fehler: $host"
done
```

#### Phase 4 Preamble: Default-Deny vs Default-Permit (User-Decision-Point)

**Wichtig:** Bevor der Permission-Check startet, **User-Profil abschätzen** — nicht automatisch den härtesten `default: deny` erwarten.

| User-Typ | Empfehlung | Begründung |
|----------|-----------|------------|
| **Power-Orchestrator** (viele delegation/swarm/kanban) | **Default-Permit** + Surgical-Deny (8-15 Nuklear-Befehle) | Default-Deny blockiert Flow massiv. Jeder Subagent braucht Ausnahmen. |
| **Light-User** (Single-Chat) | **Default-Deny** (strict) | Kaum Subagents, wenig delegation. Maximal-Sicherheit ohne Flow-Verlust. |
| **Server / Headless** | **Default-Deny** (strict + allowlist) | Kein interaktiver User, jeder Spawn explizit erlaubt. |

**Indikatoren für Heavy-User / Power-Orchestrator:**
```bash
# Profile-Dichte = delegation-Intensität
hermes profile list 2>&1 | grep -cE "(yuno|worker|coder|flash)"
# Cron-Dichte
crontab -l 2>/dev/null | grep -v "^#" | grep -c .
# Kanban-Aktivität
hermes kanban assignees 2>&1 | grep -c "done"
```

**Faustregel:** 3+ Profile UND 10+ Cron-Jobs = **Default-Permit + Surgical-Deny** (80/20). Sonst = **Default-Deny** (Maximum Security).

**Pitfall:** Nicht `default: deny` setzen ohne Kontext. Power-Users die Flow verlieren, deaktivieren die ganze Policy → weniger Sicherheit als wenn man sie korrekt abholt. **Basti (2026-07-11):** 7 Profile, 35 Cron-Jobs, 6 Boards. Bewusst Default-Permit mit Surgical-Deny gewählt.

---

#### Phase 4: Permission-Check (DEFAULT-DENY)

```bash

set -euo pipefail
CONFIG="$HOME/.hermes/config.yaml"
test -f "$CONFIG" || { echo " Keine Hermes-Config"; exit 1; }

python3 << 'PY'
import yaml, os, subprocess
with open(os.path.expanduser("~/.hermes/config.yaml")) as f:
    cfg = yaml.safe_load(f) or {}
findings = []
perm = cfg.get("permissions", {})
if perm.get("default") != "deny":
    findings.append(("P1", "permissions.default != deny"))
write_paths = perm.get("file", {}).get("write_paths", [])
if not write_paths:
    findings.append(("P1", "write_paths fehlt — Default-Deny fr Files nicht durchsetzbar"))
elif len(write_paths) > 6:
    findings.append(("P2", f"write_paths hat {len(write_paths)} Eintrge — zu breit"))
deny = perm.get("tools", {}).get("terminal", {}).get("deny", [])
deny_str = " ".join(deny)
if "git push* main*" not in deny_str and "main" not in deny_str:
    findings.append(("P1", "git push auf main nicht in deny"))
if "sudo" not in deny_str:
    findings.append(("P1", "sudo nicht in deny — Rechte-Eskalation"))
config_perm = oct(os.stat(os.path.expanduser("~/.hermes/config.yaml")).st_mode & 0o777)
if config_perm != "0o600":
    findings.append(("P0", f"config.yaml ist {config_perm} (sollte 600)"))
result = subprocess.run(
    ["find", os.path.expanduser("~/.hermes/"), "-type", "f", "-perm", "-o+w"],
    capture_output=True, text=True, timeout=10)
ww = [f for f in result.stdout.strip().split("\n") if f.strip()]
if ww:
    findings.append(("P0", f"{len(ww)} world-writable Dateien: {ww[0]}"))
for sev, msg in findings:
    print(f"[{sev}] {msg}")
if not findings:
    print("Alle Permission-Checks OK")
PY
```

**Threshold-Table:**

| Check | Severity bei Fail | Soll-Wert |
|-------|-------------------|-----------|
| default: deny | P1 | deny |
| write_paths definiert | P1 |  1 Pfad, < 6 |
| git push* main* in deny | P1 | substring in deny: |
| sudo* in deny | P1 | substring in deny: |
| config.yaml Perm | P0 | 0600 |
| World-writable Files | P0 | 0 Treffer |

#### Phase 5: Trace-Monitoring (Cron + Git + Prozesse)

```bash

set -euo pipefail
# Root-Cron (sollte leer sein)
crontab -l 2>/dev/null | grep -v "^#" | head -10
sudo crontab -l 2>/dev/null && echo " Root-Cron aktiv!"
# Git-Branch
cd "$REPO_DIR" 2>/dev/null && git branch --show-current
```

#### Phase M: Modell-Limits & Routing

```bash

set -euo pipefail
python3 << 'PY'
import yaml, os
with open(os.path.expanduser("~/.hermes/config.yaml")) as f:
    cfg = yaml.safe_load(f) or {}
for name, m in cfg.get("models", {}).items():
    limit = m.get("monthly_limit_eur")
    if limit is None:
        print(f"[P1] Modell '{name}': Kein monthly_limit_eur")
    elif name == "heartbeat" and limit > 5:
        print(f"[P2] Heartbeat: Limit {limit}€ — fr Watchdog zu teuer")
PY
```

### Finding-Bewertung und Aktionen

| Severity | Bedeutung | Aktion |
|----------|-----------|--------|
| **P0** | Sicherheitsverletzung | Nie auto-fixen — User fragen. Hook: Telegram-Alert |
| **P1** | Wichtige Lcke, diese Woche | Daily-Digest, dann gemeinsam fixen |
| **P2** | Nice-to-have | Log only, nchster Monats-Durchlauf |
| **OK** | Erfllt | Keine Aktion |

### Config-Gegencheck: Template vs Live

Der produktivste Schritt: laufende Config gegen Repo-Vorlage differn.

```bash

set -euo pipefail
TEMPLATE="/tmp/maxclaw-clone/config/config.yaml"  # oder angepasster Pfad
LIVE="$HOME/.hermes/config.yaml"
if [ -f "$TEMPLATE" ]; then
    python3 -c "
import yaml
with open('$TEMPLATE') as f: t = yaml.safe_load(f)
with open('$LIVE') as f: l = yaml.safe_load(f)
for section in ['permissions', 'models', 'gateway', 'automation']:
    t_s = t.get(section, {}); l_s = l.get(section, {})
    for key in t_s:
        if key not in l_s:
            print(f'[P1] Fehlt in {section}.{key}')
        elif l_s[key] != t_s[key]:
            print(f'[P2] Abweichung in {section}.{key}')
"
fi
```

### Referenzen

- `references/greyhack-security-phases.md` — Mapping der 6 GreyHack-Security-Phasen auf Linux/Hermes-Checks, mit CLI-Befehlen pro Phase
- `references/decommission-stub-pattern.md` — Checkliste zum Stilllegen von Legacy-Audit-Scripts und Ersetzen durch Skills (inkl. Stub-Template, Case Study vom MaxClaw-Decommission 2026-07-13)
- **Layer 4 (unten):** Network Service Security Audit — dedizierte Methodik für HTTP-Service-Posture-Prüfung (Route Probing, Auth-Verifikation, Config-Source-Tracing, Network-Exposure, Process-Lifecycle, Risk-Classification)

## Quick-Fix Cheatsheet

```bash

set -euo pipefail
# Dienst deaktivieren
sudo systemctl stop <dienst>
sudo systemctl disable <dienst>

# Dienst auf localhost beschränken (UFW deny+allow pattern)
# Blockiert ALLE externen Zugriffe, erlaubt nur localhost
sudo ufw deny <port>/tcp
sudo ufw allow from 127.0.0.1 to any port <port> proto tcp
# Vorteil: Dienst bleibt aktiv und nutzbar, aber nicht von extern erreichbar

# SSH deaktivieren (wenn nicht gebraucht)
sudo apt purge openssh-server

# Config-Berechtigungen korrigieren
chmod 600 ~/.gmail-organizer.json ~/.hermes/config.yaml
chmod 700 ~/.ssh/

# HERMES-SPEZIFISCH: Session-DB + Logs härten
chmod 600 ~/.hermes/state.db ~/.hermes/kanban.db ~/.hermes/.hermes_history
chmod 600 ~/.hermes/state.db-wal ~/.hermes/state.db-shm
chmod 600 ~/.hermes/logs/agent.log ~/.hermes/logs/errors.log
chmod 700 ~/.hermes/state-snapshots/
find ~/.hermes/state-snapshots/ -type f -exec chmod 600 {} \;
chmod 600 ~/.hermes/config.yaml.bak.* 2>/dev/null

# Request-Dumps löschen (alte API-Debug-Files, potentiell sensitiv)
find ~/.hermes/ -name 'request_dump_*.json' -delete

# Fail-Close aktivieren (Tool-Ausfall = Ablehnung, nicht Open-Bar)
hermes config set tirith_fail_open false

# DM-Policy schließen (nur bekannte User)
hermes config set telegram.dm_policy closed

# Nach Config-Änderungen: Gateway neustarten
systemctl --user restart hermes-gateway.service

# Config .env Backup vor Edits (Niemals sed -i auf .env!)
cp ~/.hermes/.env ~/.hermes/.env.pre-$(date +%s)

# Config .env aus Pre-Update-Snapshot wiederherstellen (bei Korruption)
# ls ~/.hermes/state-snapshots/ | sort | tail -1 → snapshot-dir
# cp ~/.hermes/state-snapshots/<latest>/.env ~/.hermes/.env

# Ollama Crash-Loop beenden (Port-Konflikt zwischen Snap und systemd)
# 1. Finde was auf Port 11434 läuft
ss -tlnp | grep 11434
# 2. Snap-Version läuft bereits → systemd-Version deaktivieren
sudo systemctl stop ollama && sudo systemctl disable ollama
# ODER: Snap entfernen + systemd-Version nutzen
sudo snap remove ollama
```

## Dokumentation

Nach dem Audit eine Datei `~/docs/system/security.md` schreiben mit:
- Übersicht offene Ports (nach Interface getrennt)
- Berechtigungs-Status
- Dienst-Status-Tabelle
- Quick-Wins (was wurde/wird gefixt)
- Datum

Format siehe `~/docs/system/security.md` (Beispiel vom 03.06.2026).
