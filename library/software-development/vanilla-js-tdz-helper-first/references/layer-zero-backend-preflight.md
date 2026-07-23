# Layer Zero: Backend-Datenpipeline vor Frontend-Debug prüfen

## Kontext

Aus Dashboard v4 (2026-07-08): Ein Cache-Bug verursachte 2.5s Latenz pro API-Call.
30+ Tool-Calls Frontend-JS-Debugging bevor jemand `curl /api/data` ausführte.
Der Cache-Bug wäre in 2 Minuten gefunden gewesen statt 4 Stunden.

## Die Lektion

**Wenn das Symptom ein Frontend-Rendering-Problem betrifft (Dashboard zeigt Skeleton, leere Seite, keine Daten):**

NICHT sofort JS-Code lesen oder DOM-Inspektion machen. Prüfe zuerst ob das Backend überhaupt Daten liefert.

## Checkliste

```bash
# 1. API-Health: kommt JSON zurück? Wie schnell?
curl -s -o /dev/null -w "HTTP %{http_code} · %{time_total}s\n" http://localhost:PORT/api/data

# 2. Daten-Inhalt prüfen
curl -s http://localhost:PORT/api/data | head -c 500

# 3. Statische Dateien (Auth-Gate blockt gern HTML)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:PORT/index.html

# 4. JSON-Struktur validieren (null-Felder finden)
curl -s http://localhost:PORT/api/data | python3 -c "import sys,json; d=json.load(sys.stdin); print(type(d), list(d.keys() if isinstance(d,dict) else []))"
```

## Wann Layer Zero übersprungen werden darf

- Das Backend hat Logs die zeigen dass Anfragen ankommen
- Ein anderer Client (zweiter Tab, curl von anderem Host) bekommt Daten
- Der Fehler tritt NUR bei einem bestimmten User/Login-Zustand auf (Auth-Problem)

## Verwandte Skills

- `vanilla-js-tdz-helper-first` — der Skill dem dieses Reference gehört
- `systematic-debugging` (bundled) — 4-Phase-Debugging, Layer Zero ist Pre-Flight davor
- `dev-tools` — Bug-Sektion für Dashboard-Debugging (CORS, CSP, Auth, TDZ)
