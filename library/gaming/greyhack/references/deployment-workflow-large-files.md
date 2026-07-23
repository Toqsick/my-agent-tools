# Deployment-Workflow für große Dateien (3 Methoden)

## Methode A: pc.wget() aus der Game-Shell (NEU — empfohlen!)

Bei Dateien bis ~100 KB — **ein Befehl, kein Copy-Paste:**
```
pc.wget("http://192.168.178.92:8765/yuno_v6_c.src", "/tmp/tool.src")
// Prüfen ob geklappt:
ls /tmp/tool.src
// Build:
shell.build("/tmp/tool.src")
```

**Vorteil:** Kein Browser-Click, kein Markieren, kein Pasten. Einfach in die Shell tippen.
**Voraussetzung:** Fileserver läuft (siehe fileserver-setup.md), Game auf gleicher Maschine.
**Fallback:** Falls `127.0.0.1` nicht geht → LAN-IP probieren.

## Methode B: CodeEditor + Browser (Klassiker)

Bei Dateien über 1000 Zeilen (z.B. YUNO V6 mit 2100 Zeilen / 78 KB):

1. Agent: Fileserver auf Port 8765 starten (`python3 -m http.server 8765 &`)
2. User: In-Game-Browser öffnen → `http://<host-ip>:8765/<file>.src`
3. User: Gesamten Inhalt markieren + kopieren (Strg+A, Strg+C)
4. User: CodeEditor → New → Einfügen (Strg+V) → Save → Build → Run

### Alternative bei sehr großen Dateien (Chunking)

- Agent teilt das File in 3-4 Chunks à 500-700 Zeilen
- User kopiert Chunk für Chunk in separate CodeEditor-Tabs
- Nach Build: nur die gebaute Binary zählt — Chunks werden zusammengefügt

## Problemlösung, wenn keine Methode funktioniert

1. Fileserver läuft? → `curl -s -o /dev/null -w "%{http_code}" http://10.2.0.2:8765/<file>.src` prüfen
2. Browser im Spiel? → Mit `apt-get install wget` falls Package-Manager verfügbar
3. Nichts geht? → Chunking + CodeEditor ist immer die letzte zuverlässige Methode

## Methode C: DB-Injection (nicht hier dokumentiert)

Für Dateien >30 KB siehe `in-game-db-edit.md` und `config-deployment-db-injection.md`.