# GreyHack Security Phases → Linux/Hermes Mapping

Adaptiert aus GreyHack-Hardening (`hardening_audit.src`) für den MaxClaw
Config-Security-Audit. Jede Phase prüft eine isolierte Sicherheitsdomäne.

## Phase 0: Backup & SecretRef (Orig: Backup-User anlegen)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| Backup-User existiert? | Config-Snapshot existiert? | `ls ~/.hermes/state-snapshots/` |
| Backup ist aktuell | Snapshot < 14 Tage alt |  `stat -c %y ~/.hermes/state-snapshots/$(ls -t ~/.hermes/state-snapshots/\|head -1)` |
| KEIN Secret-Key Hardcoded | SecretRef oder Hermes-native? | `ls -la ~/.openclaw/out/` / `ls -la ~/.hermes/auth.json` |
| Rotations-Policy | Key-Rotation-Intervall | `grep rotation config.yaml` |

**P0-Finding wenn:** SecretRef-Verzeichnis fehlt UND Hermes-auth.json nicht 0600.
**P1-Finding wenn:** Snapshot > 14 Tage alt.

## Phase 1: User-Audit (Orig: Gast-Account listen)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| Gast kein sudo | Agent uid != 0 | `id -u` |
| Gast in eigener Gruppe | ~/bin gehört User | `ls -ld ~/bin/` |
| Kein fremder Prozess | Kein fremder Prozess als User | `ps -u $(whoami) \| wc -l` |

**P0-Finding wenn:** uid=0.
**P1-Finding wenn:** Fremde Besitzer in ~/bin/ oder ~/.hermes/.

## Phase 2: Port-Audit (Orig: offene Ports listen)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| Router-Telnet offen | Gateway auf 127.0.0.1? | `ss -tlnp \| grep 18789` |
| Unbekannter Listener | World-listening Services | `ss -tlnp \| grep "0.0.0.0:"` |
| Port-Scan | Offene TCP-Ports | `ss -tlnp` |

**P1-Finding wenn:** Gateway NICHT auf 127.0.0.1.
**P2-Finding wenn:** Unbekannte world-listening Services.

## Phase 3: Egress / Firewall (Orig: Router-Regeln empfehlen)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| Firewall aktiv | ufw aktiv? | `ufw status` |
| DNS-Spoofing | DNS resolution für Allowlist | `host openrouter.ai` |
| Egress-Regel | Default deny outgoing | `ufw status verbose` |

**P2-Finding wenn:** ufw nicht installiert oder inaktiv.

## Phase 4: Permission-Check (Orig: /etc/passwd-Modus prüfen; P0!)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| /etc/passwd 644 (falsch) | config.yaml 0600? | `stat -c %a ~/.hermes/config.yaml` |
| World-writable Scripts | World-writable in ~/.hermes | `find ~/.hermes/ -perm -o+w` |
| Schreib-Allowlist | write_paths definiert? | `grep write_paths config.yaml` |
| Deny-Liste | main+sudor verboten? | `grep deny config.yaml` |

**P0-Finding wenn:** config.yaml nicht 0600 ODER world-writable Files existieren.
**P1-Finding wenn:** write_paths fehlt ODER deny-Liste unvollständig.

## Phase 5: Trace-Monitoring (Orig: Active Trace erkennen → disconnect)

| GreyHack | Linux/Hermes | CLI-Befehl |
|----------|-------------|------------|
| Active Trace | Root-Cron aktiv? | `sudo crontab -l` |
| Compiler faked | Git-Branch unerwartet? | `git branch --show-current` |
| Deviated Command | Uncommitted Änderungen | `git status --short` |
| Running Claw | Agent-Prozess läuft? | `pgrep -a hermes` |

**P1-Finding wenn:** Root-Cron aktiv (nicht vom Agent verursacht, informieren).
**P2-Finding wenn:** Viele uncommitted Änderungen im Audit-Repo.

## Phase M: Modell-Limits (Zusatzphase, kein GreyHack-Äquivalent)

| Check | CLI-Befehl |
|-------|-----------|
| monthly_limit_eur pro Modell? | `grep monthly_limit_eur config.yaml` |
| Heartbeat auf billigem Modell? | `grep -A5 heartbeat config.yaml` |
| Fallback-Provider definiert? | `grep fallback config.yaml` |

**P1-Finding wenn:** monthly_limit_eur fehlt.
**P2-Finding wenn:** Heartbeat-Modell zu teuer (> 5 €/Monat).

## Severity-Matrix

| Severity | GH-Analogon | Bedeutung für Basti |
|----------|------------|-------------------|
| P0 | Exploit im Kernel | Sicherheitsverletzung, sofort fixen. Nie auto — Basti fragen |
| P1 | Offene Router-Telnet | Wichtige Lücke, diese Woche beheben |
| P2 | Backup veraltet | Nice-to-have, nächster Durchlauf |
| OK | System gehärtet | Keine Aktion |
