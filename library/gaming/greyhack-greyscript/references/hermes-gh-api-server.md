# Hermes GreyHack API Server (Stufe 2)

> GreyScript hat KEINEN `HTTP.Request()` Befehl. Die GreyScript-Clients (`hermes_api.src`, `hermes_daemon.src`) in `templates/` KÖNNEN NICHT KOMPILIERT WERDEN, weil sie `HTTP.Request()` verwenden. Festgestellt in Session 2026-06-06.
> Für Setup/Deployment siehe `references/copilot-web-ui.md` und `references/deployment.md`. Kurze Übersicht in SKILL.md.

## Zwei Alternativen für Hermes-Integration im Spiel

1. **Hermes-API-Server (Port 8333) auf dem Host** — läuft, aber GreyScript kann ihn nicht direkt ansprechen. Nutze den Server via Python/curl auf dem Host.
2. **Hermes als In-Game-Computer in der DB** (Stufe 3) — Hermes wird direkt als Computer in `GreyHackDB.db` eingetragen und verhält sich wie ein NPC-Computer im Spiel. Der Spieler kann SSH-Verbindungen zu IP `172.217.22.14` aufbauen.

## Architektur

```
GreyHack (Port 8332) ←── Alt-Tab ──→ hermes-ask CLI → Hermes API Server (Port 8333)
                                                              │
                                                      ┌───────┴───────┐
                                                      │  /ask (LLM)   │
                                                      │  /analyze     │
                                                      │  /generate    │
                                                      │  /crack       │
                                                      └───────────────┘
                                                              │
                                                         Nous Portal
                                                     (DeepSeek V4 Flash)
```

- GreyHack läuft auf Port 8332 (entdeckt beim Debugging)
- Hermes API auf Port 8333 (localhost only)
- Host-Terminal: `~/bin/hermes-ask "frage"` (Alt-Tab)
- GreyScript hat KEIN HTTP — direkter Aufruf aus dem Spiel nicht möglich

## Setup

```bash
# Server starten (einmalig)
~/.hermes/hermes-agent/venv/bin/python3 ~/bin/hermes-gh-api-server.py &

# Status-Check
curl http://127.0.0.1:8333/status

# Autostart via @reboot-Cron
crontab -e  # → @reboot sleep 10 && /home/bratan/.hermes/hermes-agent/venv/bin/python3 /home/bratan/bin/hermes-gh-api-server.py > ~/.hermes/logs/hermes-gh-api-cron.log 2>&1
```

## API-Endpunkte (v2 — mit LLM)

| Endpunkt | Methode | Body | Antwort |
|----------|---------|------|---------|
| `/status` | GET | — | Server-Status + Modell-Info |
| `/ask` | POST | `{"query": "..."}` | Echte LLM-Antwort von DeepSeek V4 Flash |
| `/analyze` | POST | `{"target": "...", "ports": "..."}` | LLM-gestützte Analyse + Tipps |
| `/generate` | POST | `{"tool": "portscan\|backdoor\|bruteforce"}` | Generierter GreyScript-Code |
| `/crack` | POST | `{"type": "ssh", "hints": "..."}` | LLM-Cracking-Strategie |

## Host-Terminal Workflow (empfohlen)

```bash
~/bin/hermes-ask status              # Server-Check
~/bin/hermes-ask "wie hacke ich SSH?" # Frage ans LLM
~/bin/hermes-ask -g backdoor         # GreyScript generieren
~/bin/hermes-ask -a 192.168.1.10 22,80  # Analyse
```

## Server-Code

Pfad: `~/bin/hermes-gh-api-server.py`. Nutzt OpenAI-Client → Nous Portal, loggt nach `~/.hermes/logs/hermes-gh-api.log`, fünf Endpunkte mit echten LLM-Antworten, Auto-Token-Refresh.

## Stufe 3 — Vorschau

Möglich: Hermes als eigener Computer/Player in der GreyHack-DB. Dafür die `Computer`-Tabelle in `GreyHackDB.db` nutzen — dort liegt das gesamte virtuelle Filesystem als JSON-Baum. Datei-Inhalte separat in `Files`-Tabelle (Hash-IDs als Key). Siehe `references/sqlite-database.md`.

## Co-Pilot Web-UI (Steam-Overlay)

Neben dem Terminal-CLI gibt es eine Web-basierte Co-Pilot-UI, die im Steam-Overlay-Browser (Shift+Tab) läuft — kein Alt-Tab nötig.

```
Host-Terminal:     ~/bin/hermes-ask (Bash-Skript)       ← Alt-Tab
Steam-Overlay-UI:  http://127.0.0.1:8766/               ← Shift+Tab + Browser
```

Siehe `references/copilot-web-ui.md` für:
- Server-Code und Start-Kommandos
- HTML-Chat-Interface Details
- CORS-Preflight-Pitfall und `do_OPTIONS()` Fix
- Deployment-Checkliste
