# Tailscale Dead-Listener-Triage

> **Herkunft:** Security-Audit 2026-07-13, Tailscale C (3 von 4 Serve-Listenern tot).
> **Fund:** 3 tote Backends (`:443 → :8642`, `:8444 → :9119`, `:8446 → :8445`),
>   Ursache: stale systemd-Unit-Pfade nach Filesystem-Restruktur.

## 6-Schritt-Protokoll

Wenn ein Tailscale-Serve-Listener ein Backend exponiert, aber der Dienst nicht antwortet:

| Schritt | Aktion | Tool | Erkenntnis |
|---------|--------|------|------------|
| 1 | Backend-Prozess finden | `ss -tlnp \| grep :BACKEND_PORT` | Kein Eintrag = Prozess läuft nicht |
| 2 | Systemd-Unit identifizieren | `grep -r PORT ~/.config/systemd/user/` oder Setup-Doku | Welcher Service sollte auf diesem Port lauschen? |
| 3 | Unit-Pfad prüfen | `cat ~/.config/systemd/user/<unit>.service \| grep ExecStart` | `test -f <path>` → wenn nein: Stale-Path-Finding |
| 4 | Unit-Status prüfen | `systemctl --user status <unit>` | `inactive (dead)` + gültiger Pfad = anderer Fehler; `inactive (dead)` + toter Pfad = Unit patchen oder entfernen |
| 5 | Toten Listener abräumen | `tailscale serve --https=PORT off` | Kein sudo, sofort wirksam |
| 6 | ODER Service wiederbeleben | Pfad fixen → `daemon-reload` → `start` → Backend checken → neues `serve --https=PORT` | Unit-Pfad ok, Backend läuft, Tailscale neu setzen |

## Bulk-Scan aller systemd-User-Units auf tote Pfade

```bash
find ~/.config/systemd/user/ -name "*.service" | while read f; do
  cmd=$(grep ^ExecStart "$f" | head -1 | sed 's/ExecStart=//')
  path=$(echo "$cmd" | awk '{print $1}')  # first word (no env prefix)
  echo "$f → $path"
  test -f "$path" && echo "  OK" || echo "  🔴 PATH TOT"
done
```

## Case Study: tokentelemetry.service (2026-07-13)

**Symptom:** `tailscale serve status` zeigte `:8444 → 127.0.0.1:9119`, aber Port 9119 war tot.
**Ursache:** `tokentelemetry.service` hatte `ExecStart=%h/tokentelemetry/start.sh`, aber
`~/tokentelemetry/` existierte seit der 2026-07-04-Restruktur nicht mehr — der Code
war nach `~/10-Projekte/10-active/tokentelemetry/` gewandert.
**Fix:** `WorkingDirectory` und `ExecStart` im Unit-File auf den neuen Pfad korrigiert,
`systemctl --user daemon-reload`, `tailscale serve --https=8444 off` (Listener bleibt tot,
bis Node-Version manuell gefixt ist).

## Warum das wichtig ist

Stale systemd-Units sind lautlos. Der Service ist `disabled` + `inactive`,
der Tailscale-Listener zeigt noch die alte Route, aber niemand antwortet auf dem Backend.
Der User merkt es erst beim ersten Zugriff — oder gar nicht, weil der Port nie benutzt wird.