# NotebookLM-Bridge — Registrierung & Betrieb

## Installationsstand (Stand 2026-07-06)

| Komponente | Pfad / Status |
|---|---|
| Python-Tool | `~/.local/bin/notebooklm` (v0.7.3, installiert via `uv tool install "notebooklm-py[browser]"`) |
| Wrapper | `~/50-System/bin/notebooklm-wrapper.sh` |
| Shortcut | `~/50-System/bin/nblm` |
| Projekt-Ordner | `~/10-Projekte/10-active/notebooklm-bridge/SKILL.md` |
| Profile-Storage | `~/.notebooklm/profiles/default/` |
| MCP-Server | `notebooklm mcp serve` (eingebaut, aber **nicht registriert**) |
| Auth | wechselnd — vor jeder Session `nblm auth check --test --json` verifizieren |

## Warum zwei SKILL.md-Dateien?

Der Skill existiert **zweimal**:

1. `~/.hermes/skills/notebooklm-bridge/SKILL.md` — für Hermes ladbar, automatisch in Skill-Liste, von Yuno direkt konsultierbar
2. `~/10-Projekte/10-active/notebooklm-bridge/SKILL.md` — Projekt-Begleitdoku, editierbar (kein Sandbox-Schutz)

**Regel:** Updates grundsätzlich in der Hermes-Variante (`~/.hermes/skills/...`), weil das die ist, die Yuno beim Session-Start sieht. Die Projekt-Variante ist nur für Bastis eigene Lesezugriffe da.

## MCP-Server aktivieren (auf explizite Freigabe warten)

Wenn Basti will, dass NotebookLM direkt als Hermes-Tool aufrufbar wird (`mcp__notebooklm__*` Tools in der Session):

### Voraussetzungen

1. `nblm login` durchgelaufen
2. `nblm auth check --test --json` ist grün (`status: "ok"`)
3. Basti gibt **explizit** Freigabe für `~/.hermes/config.yaml`-Edit (Sandbox-Schutz)

### Config-Snippet (zur Vorlage, **nicht ungefragt eintragen**)

```yaml
mcp_servers:
  notebooklm:
    command: notebooklm
    args: [mcp, serve]
```

### Verifikation nach Eintrag + Hermes-Neustart

```bash
hermes tools | grep -i notebooklm
# sollte die neuen mcp__notebooklm__* Tools listen
```

Falls `hermes tools` keine Tools listet → MCP-Server-Block falsch formatiert oder Pfad nicht im PATH (`which notebooklm` checken).

## Auth-Refresh-Workflow (Cookies laufen ab)

NotebookLM-Cookies halten typischerweise einige Wochen. Symptom des Ablaufs: 401/403-Fehler bei `nblm ask`.

### Option A — Manueller Refresh (interaktiv)

```bash
nblm login                          # Browser-Login wiederholen
```

### Option B — Master-Token-Mode (unattended, cron-tauglich)

```bash
nblm login --master-token --account you@gmail.com
# speichert ein langlebiges Master-Token, das on-demand frische Cookies mintet
```

Für Cron-Workflows (z.B. täglicher Audio-Briefing) ist Option B Pflicht — siehe Library-Doku im notebooklm-py Repo.

### Diagnose bei Auth-Problemen

```bash
nblm doctor                         # Voll-Diagnose: Profile, Auth, Migration
nblm auth inspect                   # Welche Profile existieren?
nblm auth check --test --json       # Live-Test mit NotebookLM-Backend
```

## Web-Tools-Offline-Workaround (auf Bastis Box)

Hermes' `web_extract` setzt Firecrawl voraus. Wenn nicht konfiguriert → `Web tools are not configured` Error.

**Fallback-Kette** für NotebookLM-Research-Aufgaben:

1. **Direkter curl** auf GitHub Raw-Inhalte:
   ```bash
   curl -sL https://raw.githubusercontent.com/teng-lin/notebooklm-py/main/README.md -o /tmp/nblm-readme.md
   curl -sL https://raw.githubusercontent.com/teng-lin/notebooklm-py/main/docs/cli-reference.md
   ```
2. **PyPI-JSON-API** für Package-Metadaten:
   ```bash
   curl -sL https://pypi.org/pypi/notebooklm-py/json | jq '.info.version, .info.summary'
   ```
3. **GitHub `mcp__github__*` Tools** für Repo-Inhalte (lokal verfügbar, kein Firecrawl)
4. **HEAD-Request** für Existenz-Check: `curl -s -o /dev/null -w "%{http_code}\n" <url>`

Erst danach → User fragen, ob er Firecrawl-Key einrichten will.

## Pitfalls aus der Basti-Session 2026-07-06

- **`uv venv` ohne `--python`-Flag** → nimmt System-Default (3.11 auf Bastis Box), aber `pip` zeigt auf 3.12 → Versions-Mismatch möglich. Immer explizit `--python 3.11`.
- **Erster Login = Browser-Popup** — Yuno kann das nicht remote triggern, Basti macht's selbst.
- **`[browser]` Extra triggert Playwright-Chromium-Download** (~170 MB). Auf Bastis root-NVMe (65-75% voll) vorher Platz checken: `df -h /`.
- **MCP-Bridge nicht automatisch** — `notebooklm mcp serve` ist eingebaut, muss aber manuell in Hermes-Config registriert werden → Sandbox-Schutz → Freigabe nötig.
- **Wrapper-Skript braucht `set -euo pipefail`** — sonst verschluckt es PATH-Bootstrap-Fehler still.

## Quick-Check vor jedem Workflow-Start

```bash
nblm --version                      # Tool da?
nblm auth check --test --json       # Auth funktioniert?
nblm status                         # Welches Notebook ist aktiv?
nblm doctor                         # Bei Problemen
```

Wenn eins davon rot ist → erst fixen, dann Workflow starten.