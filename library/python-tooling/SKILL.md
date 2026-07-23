---
name: python-tooling
description: "Use when user asks to install, upgrade, remove, or isolate Python CLI tools and libraries, create virtual environments, configure uv or pipx, or bridge a tool into Hermes. NOT for writing application code or system-wide pip installs. Applies PEP 668-safe isolation, wrapper scripts, authentication paths, and MCP integration patterns."
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - python
    - uv
    - pipx
    - pep-668
    - tooling
    - cli-install
    - wrapper-script
    - mcp-bridge
lane: worker-heavy
reasoning_effort: medium
trigger_keywords: ['and', 'python-tooling', 'install', 'upgrade', 'remove']
keywords: ['user', 'asks', 'install', 'upgrade', 'remove']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-maintenance', 'hermes-mcp-integration']
---


# Python Tooling — Install, Isolate, Bridge

Bastis Linux-Workstation ist Ubuntu 24.04 mit PEP 668 = `externally-managed-environment` aktiviert. Klassisches `pip install` schlägt ohne venv mit `error: externally-managed-environment` fehl. Das macht einen **durchdachten Install-Workflow** für jedes neue Python-Tool zur Grundvoraussetzung — kein "einfach pip installieren".

## Quick Decision Matrix

| Situation | Tool | Isolation | Path |
|---|---|---|---|
| **Standalone CLI**, dauerhaft aufrufbar (`notebooklm`, `gmail-organizer`) | `uv tool install "pkg[extras]"` | eigene venv in `~/.local/share/uv/tools/<name>/` | `~/.local/bin/<name>` |
| Standalone CLI, ohne uv | `pipx install "pkg[extras]"` | eigene venv in `~/.local/pipx/venvs/<name>/` | `~/.local/bin/<name>` |
| **Library / API-Consumer** im Projekt (z.B. `notebooklm-py` als Library) | `uv add pkg` im Projekt-venv | `~/10-Projekte/.../.venv/` | `source .venv/bin/activate` |
| **Schnelles Testskript**, ad-hoc | `uv run --with pkg script.py` | ephemere venv | n/a |
| Multi-Service-Dev-Projekt | `python3 -m venv .venv && pip install -r requirements.txt` | `~/10-Projekte/.../.venv/` | `source .venv/bin/activate` |

**Default-Empfehlung für Bastis Workflow:** `uv tool install "pkg[browser]"` (oder `[all]`, `[cli]` — was die Library anbietet) für jedes CLI-Tool. uv ist installiert (`/home/bratan/.local/bin/uv`), schneller als pipx, und Upgrades sind Einzeiler.

## Die "PATH-Falle" in nicht-login-Shells

`uv tool install` und `pipx install` legen Binaries nach **`~/.local/bin/`**. Das ist in Bastis `PATH` (laut `~/.bashrc`), aber:

- **Nicht-login Shells** (z.B. Bash-Skripte via `#!/usr/bin/env bash`, crontab-Exec-Umgebung, manche Subshells) haben `PATH` oft ohne `~/.local/bin`.
- **Symptom:** `command not found: notebooklm` obwohl `ls ~/.local/bin/notebooklm` die Datei zeigt.
- **Lösung:** Wrapper-Skript in `~/50-System/bin/` mit `export PATH="$HOME/.local/bin:$PATH"` am Anfang.

### Wrapper-Pattern (Standardrezept)

```bash
#!/usr/bin/env bash
# /home/bratan/50-System/bin/<name>-wrapper.sh
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

if ! command -v <tool> >/dev/null 2>&1; then
    echo "<tool> nicht installiert. Setup:" >&2
    echo "  uv tool install 'pkg[extras]'" >&2
    exit 127
fi
exec <tool> "$@"
```

Dann Shortcut-Symlink: `ln -sf ~/50-System/bin/<name>-wrapper.sh ~/50-System/bin/<shortcut>` (z.B. `nblm` für `notebooklm`).

**Warum nicht `~/.bashrc` editieren?** Geht auch, aber: Wrapper funktioniert auch in Subshells, crontabs, und wenn `~/.bashrc` aus irgendeinem Grund nicht gesourct wird (Login-Mode vs interaktiv). Wrapper ist robuster und isolierter.

## Auth / Config-Locations (Bastis Konventionen)

CLI-Tools, die mit externen Services sprechen (NotebookLM, Gmail, etc.), speichern Auth typischerweise:

| Tool | Auth-Pfad | Trick |
|---|---|---|
| `notebooklm-py` | `~/.notebooklm/profiles/<profile>/storage_state.json` | Playwright-Cookies, laufen ab → Refresh-Flow oder `--master-token` Mode |
| `gmail-organizer` | `~/.gmail-organizer.json` (Plaintext App-Password) | schon in CLAUDE.md Secrets-Liste |
| `chelper` | `~/.chelper/config.yaml` | Service-spezifisch |
| `docker` | `~/.docker/config.json` | Standard |

**Goldene Regel für Hermes-Agents:** Auth-Files **nicht** in `~/.hermes/` ablegen — das ist Sandbox, write-protected. Tool-eigene Locations in `~/.<tool>/` oder `~/.config/<tool>/` sind tabu-frei.

## Tool + MCP-Bridge-Pattern (wenn Hermes das Tool direkt rufen soll)

Viele moderne Python-Tools liefern eingebaute MCP-Server (`notebooklm mcp serve`, `chroma mcp`, `git mcp`, ...). Das aktiviert man in zwei Schritten:

1. **Tool läuft und ist authentifiziert** (siehe oben).
2. **MCP-Config** in `~/.hermes/config.yaml` eintragen — ABER: `~/.hermes/` ist write-protected by design. **Yuno muss beim User um Freigabe fragen**, bevor sie `config.yaml` editiert. Snippet zur Vorlage:

```yaml
mcp_servers:
  <tool>:
    command: <tool>
    args: [mcp, serve]
```

**Workaround ohne Hermes-MCP-Registrierung:** CLI über Wrapper aufrufen (`nblm ask "Frage"`), Output in Yuno-Session zurücklesen. Funktioniert für ad-hoc, ist aber nicht so glatt wie echte Tool-Calls.

## Web-Tools-Offline-Workaround

Hermes' `web_extract` setzt Firecrawl voraus (Cloud-Key oder Self-Hosted-URL). Wenn beides nicht konfiguriert ist → `Web tools are not configured` Error.

**Fallback-Kette** (in Reihenfolge probieren):

1. **Direkter curl** auf bekannte Quellen:
   ```bash
   curl -sL https://raw.githubusercontent.com/<owner>/<repo>/main/README.md -o /tmp/readme.md
   curl -sL https://pypi.org/pypi/<pkg>/json | jq '.info.version'
   curl -sL https://api.github.com/repos/<owner>/<repo>/releases/latest | jq '.tag_name'
   ```
2. **GitHub `mcp__github__*` Tools** für Repo-Inhalte (sind lokal verfügbar, kein Firecrawl nötig).
3. **`PyPI JSON-API`** für Package-Metadaten ohne HTML.
4. **HEAD-Request** für Existenz-Check: `curl -s -o /dev/null -w "%{http_code}\n" <url>`.

Erst danach → User fragen, ob er Firecrawl-Key einrichten will.

## Häufige Befehle (copy-paste-ready)

```bash
# Tool installieren (Browser-Extras wenn verfügbar)
uv tool install "<pkg>[browser]"

# Tool upgraden
uv tool upgrade <pkg>

# Tool deinstallieren
uv tool uninstall <pkg>

# Liste installierter Tools
uv tool list

# venv im Projekt anlegen + Lib installieren
cd ~/10-Projekte/10-active/<project>
uv venv .venv --python 3.11
source .venv/bin/activate
uv add <pkg>

# Auth-Status eines Tools prüfen (Library-spezifisch, Beispiel notebooklm-py)
notebooklm auth check --test --json

# Ad-hoc-Skript mit ephemeren Deps
uv run --with httpx --with rich python3 -c "..."
```

## Pitfalls (aus realen Basti-Sessions)

- **`uv venv` ohne `--python`** pickt default-mäßig die system-Python. Auf Bastis Box ist das 3.11, aber pip zeigt auf 3.12 (siehe Host-Config). Explizit `--python 3.11` setzen, sonst Versions-Mismatch.
- **`pip install` ohne venv** → `error: externally-managed-environment`. Auf Bastis Ubuntu 24.04 ist PEP 668 strikt. Workaround: `pip install --break-system-packages <pkg>` für globale Tools, wenn keine Isolation nötig (selten sinnvoll).
- **`uv tool install` mit Browser-Extras** kann 100-200 MB Chromium-Download triggern (z.B. `notebooklm-py[browser]`). Auf Bastis root-NVMe (65-75% voll) vorher Platz checken: `df -h /`.
- **Erste Login braucht Browser-Interaktion** — kann Yuno nicht remote machen. Workflow: Setup ohne Login → User führt Login selbst aus → danach headless.
- **Cookies laufen ab** — Google-Tools (NotebookLM, Gmail) brauchen alle paar Wochen Refresh. Bei NotebookLM-py: `auth refresh --quiet` als cron-jobbar.

## Upgrade- und Cleanup-Workflow

```bash
# Was ist installiert und welche Version?
uv tool list

# Einzelnes Tool upgraden
uv tool upgrade <tool>

# Alle upgraden
uv tool upgrade --all

# Nicht mehr benötigtes Tool weg
uv tool uninstall <tool>
# + Wrapper-Skript in ~/50-System/bin/ löschen
# + Symlink in ~/50-System/bin/ löschen
# + Optional: ~/.cache/<tool>/ aufräumen
```

## Siehe auch

- `references/basti-specifics.md` — Host-Config, Version-Mismatch, Disk-Pressure-Workarounds, PATH-Persistenz
- `references/hyphenated-module-bridge.md` — **NEU 2026-07-16:** Loader-Bridge via `importlib.util.spec_from_file_location` für Python-Module mit Bindestrich im Dateinamen. Nötig wenn ein Plan `daily-note-health.py` spezifiziert aber Tests `from daily_note_health import …` verwenden.
- `system-documentation` — Workflow für Doku-Updates nach Builds/Fixes
- `security-code-checker` — Python-Code-Audits vor Production-Einsatz
- `bash-script-audit` — Wrapper-Skripte sauber halten (`set -euo pipefail`, Quoting, etc.)
- `~/50-System/bin/` — alle produktiven Wrapper-Skripte und PATH-Symlinks