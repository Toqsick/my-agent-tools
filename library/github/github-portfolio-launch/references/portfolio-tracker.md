# GitHub Portfolio Tracker — gh-portfolio-tracker.py

Ein CLI-Script, das den GitHub-Portfolio-Status automatisch als Obsidian-Markdown-Snapshot speichert.

## Standort

- **Canonical:** `~/50-System/bin/gh-portfolio-tracker.py`
- **Symlink (PATH):** `~/bin/gh-portfolio-tracker`

## Features

- Holt alle öffentlichen Repos via `gh api users/<user>/repos`
- Klassifiziert: eigene Repos vs Forks, Sprache, Stars, Topics
- Holt CI-Status pro eigenem Repo via `gh run list`
- Rendert als strukturiertes Markdown mit Tabellen und Badge-Icons
- Speichert in Obsidian Vault (`01 Inbox/portfolio-snapshots/`)
- `--diff` Mode: Vergleich mit vorherigem Snapshot
- `--verbose`: Ausführliche Ausgabe

## Usage

```bash
# Einmalig Snapshot erstellen
python3 ~/50-System/bin/gh-portfolio-tracker.py --once

# Mit Details
python3 ~/50-System/bin/gh-portfolio-tracker.py --once --verbose

# Nur Änderungen anzeigen (kein neuer Snapshot)
python3 ~/50-System/bin/gh-portfolio-tracker.py --diff

# Über den PATH-Bridge
gh-portfolio-tracker --once
```

## Cron-Einrichtung (optional)

```cron
# Täglicher Snapshot um 23:00
0 23 * * * /usr/bin/python3 /home/bratan/50-System/bin/gh-portfolio-tracker.py --once
```

## Output

- Erzeugt: `~/Dokumente/Obsidian Vault/01 Inbox/portfolio-snapshots/gh-portfolio-YYYY-MM-DD.md`
- Enthält: Repo-Liste mit CI-Status, Größe, Sprache, Topics
- Erkennt Änderungen seit letztem Snapshot

## Nützliche Erkenntnisse aus dem Tracker

Der Tracker deckt automatisch Portfolio-Schwächen auf:
- Repos mit roter CI (z.B. Weblate-german-translate)
- Repos ohne Beschreibung ("(keine Beschreibung)")
- Größen-Anomalien (zu große Repos, verwaiste Projekte)

## Abhängigkeiten

- `gh` CLI (GitHub CLI) — muss authentifiziert sein (`gh auth status`)
- Python 3.10+
- Keine externen Python-Pakete (nur stdlib)
