# Hermes GreyHack Co-Pilot Web-UI

## Übersicht

Der Co-Pilot besteht aus **zwei Servern** auf dem Host:

| Server | Port | Aufgabe |
|--------|------|---------|
| Hermes API v2 | 8333 | LLM-Anfragen via Nous Portal (DeepSeek V4 Flash) |
| Co-Pilot Web-Server | 8766 | Serviert HTML-Chat und statische Dateien aus `~/bin/` |

Zugriff im Spiel via Steam-Overlay: `Shift+Tab` → Browser → `http://127.0.0.1:8766/`

## Server starten

### API-Server (Port 8333)

```bash
# Start
~/.hermes/hermes-agent/venv/bin/python3 ~/bin/hermes-gh-api-server.py &

# Health-Check
curl http://127.0.0.1:8333/status

# Alten Prozess killen falls Port blockiert
ss -tlnp | grep 8333
kill -9 <PID>
```

### Co-Pilot Web-Server (Port 8766)

```bash
# Start (serviert ~/bin/ als statischen Webserver)
python3 ~/bin/hermes-copilot-server.py &

# Oder direkt mit Python http.server:
# cd ~/bin && python3 -m http.server 8766 &

# Test
curl -s http://127.0.0.1:8766/ | head -5
```

## CORS-Preflight-Pitfall

Siehe SKILL.md unter "Hermes GreyHack Co-Pilot (Steam-Overlay Web-UI)" → "CORS-Preflight-Pitfall".

**Kurzfassung:** Wenn `do_OPTIONS()` im API-Server fehlt → `fetch()` im Browser (Steam-Overlay) schlägt fehl mit "Failed to fetch". Der Fix ist `do_OPTIONS()` mit:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`

## Dateien

- `~/bin/hermes-gh-api-server.py` — API-Server v2 mit LLM-Anbindung (Python, OpenAI-Client via Hermes-venv)
- `~/bin/hermes-copilot-server.py` — einfacher HTTP-Server für statische Dateien (Python http.server)
- `~/bin/hermes-co-pilot.html` — HTML-Chat-Interface (fetch → Port 8333)
- `~/bin/index.html` — Kopie von hermes-co-pilot.html als Default-Seite (damit `http://127.0.0.1:8766/` ohne Pfad funktioniert)
- `~/bin/hermes-ask` — Host-Terminal-CLI-Skript (für Alt-Tab-Nutzung)

## Deployment-Checkliste

Nach System-Neustart oder wenn der Co-Pilot nicht erreichbar ist:

1. Prüfen: `ss -tlnp | grep -E '8333|8766'`
2. API-Server starten: `~/hermes-gh-api-server.sh` oder manuell starten
3. Web-Server starten: `~/hermes-copilot-server.sh` oder manuell
4. Test: `curl http://127.0.0.1:8333/status`
5. Test: `curl http://127.0.0.1:8766/`
6. Test mit Frage: `curl -s http://127.0.0.1:8333/ask -X POST -H "Content-Type: application/json" -d '{"query":"test"}'`

## Cronjob (Autostart @reboot)

```
@reboot sleep 10 && /home/bratan/.hermes/hermes-agent/venv/bin/python3 /home/bratan/bin/hermes-gh-api-server.py > ~/.hermes/logs/hermes-gh-api-cron.log 2>&1
```
