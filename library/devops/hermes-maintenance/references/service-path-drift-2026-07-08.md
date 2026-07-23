# Service-Unit Path-Drift: hermes-webui.service Case Study

**Datum:** 2026-07-08
**Symptom:** `http://localhost:8787` → ERR_CONNECTION_REFUSED, Port 8787 nicht belegt

## Ist-Zustand

```bash
# 1. Kein Prozess auf Port 8787
ss -tlnp | grep 8787   # → nichts

# 2. Service-Unit inspizieren
systemctl --user cat hermes-webui.service
```

Unit enthielt:
```
ExecStart=/home/bratan/hermes-webui/ctl.sh start 8787
WorkingDirectory=/home/bratan/hermes-webui
```

```bash
# 3. Pfad prüfen
ls -la /home/bratan/hermes-webui   # → No such file or directory
# 4. Enable-Status
systemctl --user is-enabled hermes-webui.service   # → disabled
```

## Ursache

Nach dem AGENTS.md-Cluster-Umzug wurde das Repo von `~/hermes-webui/` nach `~/10-Projekte/40-archive/hermes-webui/` verschoben. Die systemd-Unit (und alle Crontab-Einträge, die auf den alten Pfad zeigten) wurden **nicht** aktualisiert. Zusätzlich ging der `enable`-Status verloren.

## Fix

### Schritt 1: Symlink erstellen
```bash
ln -s /home/bratan/10-Projekte/40-archive/hermes-webui /home/bratan/hermes-webui
```
**Warum Symlink statt Unit-File-Edit:** Der Pfad `~/hermes-webui/` wird in mehreren Kontexten referenziert (systemd-Unit, vielleicht Cron, eventuell PATH-Aliase). Ein Symlink fixiert alle auf einmal. Nachteil: wenn der Symlink gelöscht wird (z.B. bei nächstem Reorg), bricht alles wieder.

### Schritt 2: Service aktivieren
```bash
systemctl --user daemon-reload     # Symlink einlesen
systemctl --user enable hermes-webui.service   # → Created symlink in default.target.wants/
systemctl --user start hermes-webui.service
```

### Schritt 3: Verifikation
```bash
systemctl --user is-active hermes-webui.service   # → active
ss -tlnp | grep 8787                               # → LISTEN 127.0.0.1:8787
# Browser-Test: http://localhost:8787 → "Yuno" WebUI geladen
```

## Post-Fix-Zustand

| Aspekt | Vorher | Nachher |
|---|---|---|
| Service-Pfad | `/home/bratan/hermes-webui/` (nicht existent) | Symlink → `~/10-Projekte/40-archive/hermes-webui/` |
| enable-Status | disabled | enabled (`default.target.wants/`) |
| Port 8787 | nichts | LISTEN, PID 72861 |
| Autostart | kalt | enabled → bootet mit User-Session |

## Wichtige Einblicke

### Post-Migration Check-Liste (generell)

Nach jeder Cluster-Reorganisation gehören diese Punkte geprüft:

1. **systemd-Unit-Files** — `~/.config/systemd/user/*.service` — Referenzen auf `ExecStart=`, `WorkingDirectory=`, `Environment=`-Pfade
2. **Cron-Jobs** — `crontab -l` — absolute Pfade in Script-/Log-Referenzen
3. **PATH-Aliase** — `~/.bashrc`, `~/.profile`, `~/.config/fish/config.fish` — `export PATH=...` oder `alias`-Definitionen
4. **Desktop-Entries** — `~/.local/share/applications/*.desktop` — `Exec=` Pfade
5. **Script-Referenzen** — andere Scripts die `source <path>` oder `./<relative>` aus dem alten Verzeichnis nutzen

### Type=forking + PIDFile-Pitfall

Die `hermes-webui.service`-Unit verwendet `Type=forking` mit `PIDFile=/home/bratan/.hermes/webui.pid`. Das bedeutet:

- systemd startet `ctl.sh start 8787`
- `ctl.sh` forked in den Hintergrund
- systemd wartet auf die PID-Datei `~/.hermes/webui.pid`
- Erst wenn die Datei existiert, gilt der Service als "active"
- Falls `ctl.sh` **keine** PID-Datei schreibt → `Restart=on-failure` kann nicht tracken → Service stirbt bei Absturz ohne Restart

**Prüfung nach Start:**
```bash
cat ~/.hermes/webui.pid   # existiert? Zeigt auf laufenden Prozess?
```

### Repository-Location (für Folgesessions)

| Repo | Lokaler Pfad |
|---|---|
| hermes-webui (nesquena) | `~/10-Projekte/40-archive/hermes-webui/` |
| symlink (legacy) | `~/hermes-webui/` → oben |
| letzter Commit | `07b9708` (#5756), 2026-07-07 |
| Remote | `https://github.com/nesquena/hermes-webui.git` |
