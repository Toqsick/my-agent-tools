---
name: local-ai-security-hygiene
description: |
  Use when securely installing, exposing, configuring, auditing, or removing local AI runtimes such as Ollama or llama.cpp and synchronizing Hermes provider settings.
  NOT for model benchmarking, fine-tuning, prompt design, or making an unsecured local inference service publicly reachable.
  Applies least-exposure defaults, explicit provider configuration, credential hygiene, firewall checks, clean teardown, and post-change verification.
version: 1.3.0
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
changelog:
- "1.3.0 (2026-07-17): Pitfall #10 ergänzt (Ollama print_timing-Spam füllt syslog).
  Cross-Reference zu system-security-audit Pitfall #9."
- 1.2.0 (2026-07-13): Pitfall
- 1.1.0 (2026-07-08): Initiale Konvertierung von Claude Code mit kompletter Ollama-Removal-Pipeline.
trigger_keywords: ['local', 'provider', 'securely', 'installing', 'exposing']
keywords: ['local', 'provider', 'securely', 'installing', 'exposing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['local-ml-hosting', 'mnemosyne-memory-provider', 'ollama-local-hosting']
---


# Local AI Security Hygiene

## Trigger
- User will lokalen LLM-Hosting einrichten oder komplett abschalten
- Security-Audit zeigt unnötige lokale AI-Services (offene Ports, große Model-Dirs)
- Hermes soll zwischen Online-Provider (Nous Portal, OpenRouter) und Offline (lokal) umschalten
- Nach Deinstallation sind API-Fehler (401) aufgetreten
- **Ollama soll nur als Offline-Fallback laufen — nicht parallel zum Online-Provider**

## Core Principles
1. **Minimal Exposure**: Lokale Services nur aktiv wenn nötig; sonst Firewall + Abschaltung
2. **Clean Teardown**: Deinstallation muss Binary, Libs, Modelle UND Config-Referenzen entfernen
3. **Config Sync**: Hermes `config.yaml` muss nach Install/Deinstall angepasst werden
4. **Explicit Provider**: Kein `provider: auto` bei Auxiliary Services wenn lokaler Service entfernt wurde
5. **Online-First**: Lokale Ollama nur als Fallback — nicht als aktiver Default wenn Internet verfügbar

---

## Ollama: Complete Removal Checkliste

```bash

set -euo pipefail
# 0. SYSTEMD SERVICE ZUERST PRÜFEN (kritisch!)
# Der Nutzer sagt oft "gelöscht", aber der Service läuft weiter
systemctl --user status ollama 2>/dev/null | grep -E "Active|Loaded"
# Wenn active: stoppen, disable, Unit-File löschen
systemctl --user stop ollama 2>/dev/null
systemctl --user disable ollama 2>/dev/null
rm -f ~/.config/systemd/user/ollama.service
systemctl --user daemon-reload

# 1. Binary (oft ein Symlink!)
which ollama
ls -la $(which ollama) 2>/dev/null   # → Symlink auf ~/.local/lib/ollama/bin/ollama
rm -f ~/.local/bin/ollama

# 2. Bibliotheken
rm -rf ~/.local/lib/ollama

# 3. Modelle & Runtime-Daten (oft 10–50 GB!)
du -sh ~/.ollama 2>/dev/null || echo "~/.ollama nicht vorhanden"
rm -rf ~/.ollama                    # Inkl. models/, manifests/, blobs/

# 3b. Zusätzliche Data-Dirs (je nach Installationsmethode)
rm -rf ~/.local/share/ollama
rm -rf /usr/share/ollama

# 4. Snap-Install-Reste (falls via Snap installiert)
snap list | grep ollama && snap remove ollama
# Achtung: Snap entfernt NICHT ~/.ollama!

# 5. Network Monitor stoppen (falls installiert)
rm -f ~/.local/bin/ollama_network_monitor.sh
crontab -l | grep -v "ollama_network_monitor" | crontab -

# 6. Verifikation
which ollama && echo "WARNUNG: Binary noch vorhanden!" || echo "✓ Binary entfernt"
ls -d ~/.ollama 2>/dev/null && echo "WARNUNG: ~/.ollama existiert!" || echo "✓ ~/.ollama entfernt"
systemctl --user status ollama 2>/dev/null | grep -q "Active" && echo "WARNUNG: Service läuft!" || echo "✓ Service gestoppt"
```

---

## Hermes Config: Nach Ollama-Deinstall bereinigen

### Referenzen finden (alle Stellen!)
```bash

set -euo pipefail
grep -in "ollama" ~/.hermes/config.yaml
```
Typische Treffer:
- `providers.ollama-launch` → Dict entfernen
- `custom_providers` mit `name: ollama-local` → Listenelement entfernen
- `fallback_providers` mit `provider: custom:ollama-local` → Listenelement entfernen
- `model.api_key: ollama` → auf `''` setzen
- `auxiliary.*.provider` → niemals `ollama` oder `auto` wenn Ollama weg ist

### Direkte YAML-Bearbeitung (notwendig für Listen/Dicts)
`hermes config set` kann keine Listen/Dicts bearbeiten. Python direkt:

```python
import yaml

with open('/home/bratan/.hermes/config.yaml') as f:
    data = yaml.safe_load(f)

# Alle Ollama-Referenzen entfernen
data['providers'].pop('ollama-launch', None)
data['custom_providers'] = [
    cp for cp in data.get('custom_providers', [])
    if cp.get('name') != 'ollama-local'
]
data['fallback_providers'] = [
    fp for fp in data.get('fallback_providers', [])
    if 'ollama' not in str(fp.get('provider', ''))
]

# Magic API Key fix
data['model']['api_key'] = ''

with open('/home/bratan/.hermes/config.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

set -euo pipefail
### CLI-Methoden (nur für einfache Keys)
```bash
hermes config set model.api_key '' --profile default
hermes config set auxiliary.title_generation.provider openrouter --profile default
```

set -euo pipefail
---

## 401-Fehler: Root-Cause & Fix

**Symptom**: Alle API-Calls schlagen mit 401 fehl, obwohl Nous Portal/OpenRouter Key gültig ist.

**Ursache**: `model.api_key: ollama` in `config.yaml` überschreibt den echten Key aus `.env`. Hermes sendet `Authorization: Bearer ollama` an die API.

**Fix**:
```bash
hermes config check                    # Zeigt welche Keys fehlen
hermes config set model.api_key '' --profile default
```

set -euo pipefail
---

## Ollama: Offline-Only Fallback (Network Monitor)

Wenn Ollama installiert bleiben soll aber NUR bei fehlendem Internet aktivieren:

### Beschreibung
Ein cron-basierter Network Monitor prüft alle 5 Minuten die Internet-Erreichbarkeit. Bei Offline-Status wird Ollama gestartet, bei Online-Status wird Ollama gestoppt. Hermes benutzt Ollama nur über die `fallback_providers` Kette.

### Script installieren

```bash
# Script herunterladen (aus Skill-Referenz)
cp ~/.hermes/skills/devops/local-ai-security-hygiene/references/ollama_network_monitor.sh ~/.local/bin/
chmod +x ~/.local/bin/ollama_network_monitor.sh

# Cronjob einrichten (alle 5 Minuten)
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/.local/bin/ollama_network_monitor.sh >> /tmp/ollama_monitor.log 2>&1") | crontab -

# Ersten Testlauf manuell starten
~/.local/bin/ollama_network_monitor.sh
```

set -euo pipefail
### Hermes Config (nur Fallback, nie Default)

```yaml
model:
  provider: nous                    # Online-Default
  default: qwen3.7-plus             # Online-Modell
  api_key: ''                       # Aus .env laden

fallback_providers:
  - provider: anthropic             # Fallback 1: Online
    model: claude-sonnet-4-20250514
  - provider: custom:ollama-local   # Fallback 2: Offline (nur wenn Ollama läuft)
    model: deepseek-r1:8b
    base_url: "http://127.0.0.1:11434/v1"

custom_providers:
  - name: ollama-local
    base_url: http://127.0.0.1:11434/v1
    api_key: ''                     # Kein Magic-String!

agent:
  api_max_retries: 1                # Schnelles Failover

auxiliary:
  title_generation:
    provider: openrouter            # Niemals "auto" oder "ollama"
```

### Wichtig
- **Niemals** `model.provider: custom:ollama-local` als Default setzen
- **Niemals** `api_key: ollama` verwenden (verursacht 401)
- Ollama läuft nur wenn Internet UNTENRREICHT, sonst Brave-Browserkrieg
- Bei Systemneustart: `systemctl --user start ollama` manuell oder Network Monitor startet es beim ersten Offline-Check

---

## Security Checklist (lokale Services)
- [ ] Service lauscht nicht auf `0.0.0.0` (nur `127.0.0.1` oder Unix-Socket)
- [ ] Firewall (UFW) blockiert den Port von außen
- [ ] Modelle bei Deinstallation mit `rm -rf` sicher gelöscht (nicht nur Uninstall)
- [ ] Hermes Config hat keine toten Provider-Referenzen
- [ ] Kein `api_key: ollama` oder anderer Magic-String in `config.yaml`

---

## Pitfalls
1. **Snap-Residue**: `snap remove ollama` entfernt das Binary, aber `~/.ollama` (20 GB+ Modelle) bleibt liegen.
2. **Symlink-Trap**: `which ollama` zeigt `~/.local/bin/ollama`, das ist aber ein Symlink. Das eigentliche Binary liegt in `~/.local/lib/ollama/bin/ollama`.
3. **Magic API Key**: `api_key: ollama` ist ein Platzhalter für Ollamas interne API, KEIN echter Key. Er verursacht 401 bei echten Cloud-Providern.
4. **Auto-Provider-Falle**: `provider: auto` bei Auxiliary Services probiert nacheinander alle Provider. Wenn eine tote Ollama-Referenz in der Config steht, blockiert oder fehlschlägt der Call.
5. **~/.ollama ist riesig**: Nutzer vergessen die Modelle. `du -sh ~/.ollama` zeigt die wahre Größe.
6. **Systemd Stealth Mode**: Ollama läuft als `systemd --user` Service weiter, auch wenn das Binary gelöscht wurde. Der Service startet bei Login neu! IMMER `systemctl --user status ollama` prüfen.
7. **hermes config set Limitation**: `hermes config set key value` funktioniert nur für flache Keys. Listen (`fallback_providers`, `custom_providers`) und Dicts (`providers`) müssen direkt im YAML oder via Python bearbeitet werden.
8. **Nutzer sagt "gelöscht" → immer verifizieren**: "Aus Sicherheitsgründen gelöscht" bedeutet oft nur `rm -rf ~/.ollama/models`, nicht das Binary oder den Service. Grep + Status + which prüfen.
9. **Inferenz-Kontext ist nicht privat (gelernt 2026-07-13)**: Auch wenn alle lokalen AI-Services sauber konfiguriert sind (Ollama auf `127.0.0.1`, keine Magic-Strings, gehärtete `.env`), wandert alles, was im Modellkontext landet — Chat-Messages, Tool-Output, Tool-Args — an den Cloud-Provider. Wenn der User einen API-Key direkt in den Chat pastet, der dann per Tool-Call in eine `.env` geschrieben wird, ist der Schlüssel **offengelegt** — unabhängig davon, ob danach `chmod 600` gemacht wird. Mitigation: erst Forensik-Bericht (`~/.hermes/docus/audits/`), dann auf Rotation-Freigabe warten. Reusable-Skript: siehe `system-security-audit` SKILL Sektion "Forensischer Secret-Audit für Cloud-Coding-Agenten" und `scripts/audit-secret-spread.py`.
10. **Ollama print_timing-Debug-Spam füllt syslog** (gelernt 2026-07-17, distinkt von
    Pitfall #9): Ollama 0.30.11 emittiert bei aktiver Modell-Ausführung INFO-Level-Zeilen
    mit Tokens wie `slot get_availabl`, `launch_slot_`, `srv  get_availabl`, `print_timing`,
    `operator()`. In 44h erzeugt das 2.7 GB / 4.5M Zeilen Syslog — selbst wenn der
    Ollama-Service nur als Offline-Fallback läuft und kein Modell aktiv lud, kann das
    Log den Disc-Fill-Alarm triggern. **Symptom:** `/var/log/syslog > 1 GB` ohne klaren
    Verursacher; `journalctl --disk-usage` steigt nicht (Spam läuft über rsyslog, nicht
    journald). **Fix:** `Environment="OLLAMA_DEBUG=0"` + `Environment="OLLAMA_LOG_LEVEL=warn"`
    in `/etc/systemd/system/ollama.service.d/override.conf` + `daemon-reload` +
    `restart ollama` (Modelle werden kurz entladen, re-loaden on-demand). Alternative
    (Symptom-Filter, NICHT empfohlen): rsyslog drop-in `if $programname == "ollama" and
    $msg contains "print_timing" then stop` — riskant, weil echte Ollama-Errors durch
    dieselbe Facility laufen und MÜSSEN fließen. **Detection:**
    `for src in ollama zorin-printers kernel; do printf "%-15s %s\n" "$src" "$(grep -c "$src\?\[" /var/log/syslog)"; done`.
    Volle Detection + Filter-Templates in `system-security-audit` Pitfall #9.

## Companion Skill

`system-security-audit` (Sektion "Forensischer Secret-Audit für Cloud-Coding-Agenten") — enthält das 4-Phasen-Pattern und das SQLite-basierte Secret-Spread-Tool für jeden Cloud-Coding-Agent-Workflow (Hermes, Codex CLI, Claude Code, Grok Build CLI etc.). Bei Verdachtsfall zuerst dort nachschlagen, dann hier für lokale-Service-Konfiguration zurückkehren.

---

## Related Skills
- `ollama-local-hosting` – Installation & Setup (Komplement zu diesem Teardown-Skill)
- `linux-system-maintenance` – Allgemeines System-Cleanup
- `hermes-agent` – Config-Verwaltung via `hermes config` CLI

## Session-Referenzen
- `references/session-2026-06-05-ollama-teardown.md` – Erstes 401-Fix + vollständige Deinstallation
- `references/session-2026-06-05-systemd-stealth-teardown.md` – **Systemd stealth mode**: Ollama läuft weiter obwohl Nutzer "gelöscht" sagte; Python-YAML für Listen/Dicts; Kimi-K2.6 als Nous-Default
