# Hermes V7 SSE WebUI — "Geht nicht mehr" Diagnostic Session

**Datum:** 2026-07-02
**Symptom:** User meldet "WebUI geht nicht mehr". Mein erster Triage-Schritt war breites Scannen (Ports, Docker, Services) bevor ich eine spezifische Hypothese aufstellte.
**Ergebnis:** Server lief gar nicht (kein Auto-Restart). Fix in 2 Minuten: `terminal(background=true)` start + Curl-Readiness-Probe.

## Was tatsächlich kaputt war

**Root cause:** Hermes-V7-SSE-Server war nach letztem Reboot/Session-Logout nicht mehr hochgefahren. Es existiert **keine systemd-user-unit** für den Server — er muss manuell gestartet werden.

**Warum ich's gefunden hab:** Breiter Port-Scan (`ss -tlnp | grep -E ':(3000|4321|8787|...)`) zeigte: kein Prozess auf 8787, kein Node-Prozess für `node dist/server`, kein systemd-Eintrag.

## Diagnose-Schritte (was funktioniert hat)

```bash
# 1. Breit scannen — nicht nur auf 8787 fokussieren
ss -tlnp 2>/dev/null | grep -E ':(3000|3030|5000|7860|8080|8787|8888|9000|11434|8765|8333) '
# Ergebnis: 8333, 11434, 8080, 3000 (alle fremde Prozesse), 8787 leer

# 2. Hermes-SSE-Prozess suchen
ps -ef | grep -E 'hermes.*sse|hermes-v7|node.*server' | grep -v grep
# Ergebnis: leer

# 3. Memory-Pfad querchecken — Memory sagte ~/hermes-v7/, das stimmt nicht mehr
ls /home/bratan/hermes-v7/  # → "Datei oder Verzeichnis nicht gefunden"

# 4. Realen Pfad finden via Suche
find ~ -maxdepth 4 -name "package.json" -path "*hermes*" 2>/dev/null
# Ergebnis: /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/...

# 5. Build-Output verifizieren
ls /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/dist/server/
# Ergebnis: index.js vorhanden, Build ist da, nur nicht gestartet
```

## Fix-Schritte (Hermes-konform)

```bash
# 1. Start mit terminal(background=true, notify_on_complete=False)
# (Server läuft endlos → keine Completion-Notification)
# Command:
#   cd /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
#   CORS_ORIGINS="http://localhost:8787,http://127.0.0.1:8787"
#   HERMES_AUTH_TOKEN=super-secret
#   HERMES_WEBHOOK_TOKEN=hook-secret
#   PORT=8787
#   node dist/server/index.js

# 2. Erste Versuche scheiterten mit "nohup ... &" Auto-Reject (siehe hermes-maintenance 11.4.1)

# 3. Nach korrektem Start: separater terminal()-Call für Readiness-Probe
sleep 3
curl -s -o /dev/null -w "Dashboard: HTTP %{http_code}\n" http://127.0.0.1:8787/dashboard/hermes-sse-dashboard.html
# → 200 OK (102KB HTML geladen)

curl -s -H "X-Hermes-Token: super-secret" http://127.0.0.1:8787/api/status | head -c 300
# → {"stream":{"clients":0,...},"metrics":{...},"lanes":[...]}

timeout 4 curl -s -N -H "Authorization: Bearer super-secret" http://127.0.0.1:8787/api/events
# → retry: 2500\nid: 1\nevent: stream.open\ndata: {...}
```

## Was ich an den User abgefragt habe (Bevor ich repariere)

User sagte erst "Hermes webUI geht nicht", ich fragte **welche genau**:

> Welches WebUI geht nicht? Ich sehe mehrere Kandidaten — will nicht das falsche reparieren.
> - Hermes Desktop GUI / Hermes Gateway
> - Open WebUI für Ollama
> - Gitea Web
> - Odysseus SearXNG

User antwortete: "Hermes web ui (glaube war auf localhost:8787)". **Lesson:** Bei mehrdeutigen Symptomen erst klären statt annehmen — spart 5-20min Fehldiagnose.

## Lessons Learned (2026-07-02)

### A. Diagnose-Triage-Reihenfolge bei "X geht nicht"

1. **Breit scannen** — `ss -tlnp` über mehrere WebUI-typische Ports, dann `ps -ef | grep <keyword>`, dann Docker/Services.
2. **Pfad-Realitäts-Check** — Memory-Pfade sind oft veraltet. `find` ist Wahrheit.
3. **Fragen statt raten** — wenn Symptom mehrdeutig ("WebUI" kann vieles heißen), 2-4 Optionen anbieten.
4. **Fix umsetzen** — Hermes-konform via `terminal(background=true)`, separate Readiness-Probe.

### B. Hermes-Terminal Bash-Background-Quirk

Siehe `hermes-maintenance` Skill Sektion **11.4.1** (2026-07-02 hinzugefügt). `nohup ... &` wird **automatisch rejected** — Hermes will `terminal(background=true)`. Auch `disown`, `setsid`, trailing `&` triggern den Reject.

### C. Memory-Drift-Pattern

Mnemosyne-Memory sagte "`~/hermes-v7/`", Realität ist `Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/`. **Lesson:** Bei "Pfad nicht gefunden" → `find`-basierten Reality-Check, dann Memory korrigieren.

### D. Server-Start-ENV-Reihenfolge

Bewährt (in dieser Reihenfolge):
```bash
CORS_ORIGINS="..."        # 1. Browser darf überhaupt connecten
HERMES_AUTH_TOKEN="..."   # 2. API-Auth
HERMES_WEBHOOK_TOKEN="..." # 3. Webhook-Auth
PORT=8787                 # 4. Auf welchem Port
node dist/server/index.js # 5. Server start
```

Wenn auch nur eine fehlt → CORS-Block, 401-Loop, oder Port-Conflict.

## Empfehlungen (nicht umgesetzt)

1. **⭐⭐⭐ systemd-user-unit** für SSE-Server anlegen → Auto-Restart nach Reboot/Session-Logout
2. **⭐⭐ Memory-Pfad-Korrektur** → Mnemosyne-Eintrag für Hermes-V7-Pfad aktualisieren (siehe C oben)
3. **⭐ Disk 89% voll** (513G/607G) — kein direkter Crash-Verdacht aber `yuno-cleaner` später