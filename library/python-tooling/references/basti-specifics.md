# Python-Tooling — Basti-Spezifika

## Host-Config (Ubuntu 24.04, Zorin OS 18.1)

| Detail | Wert |
|---|---|
| Python-Default | `python3 = 3.11.15` |
| pip-Default | zeigt auf Python 3.12 (Mismatch!) |
| PEP-668-Modus | `externally-managed-environment` = `yes` |
| uv-Pfad | `/home/bratan/.local/bin/uv` (installiert) |
| Tool-Binaries | `~/.local/bin/` |
| Wrapper-Skripte | `~/50-System/bin/` |

**Konsequenz:** Klassisches `pip install` ohne venv schlägt fehl. Immer `uv tool install` oder explizites venv.

## Versions-Mismatch-Falle

```bash
$ which python3
/usr/bin/python3          # 3.11.15
$ which pip3
/usr/bin/pip3             # zeigt auf 3.12!
$ pip3 install foo
# installs gegen 3.12, nicht 3.11
```

**Lösung:** pip nie direkt benutzen, immer `uv` (das respektiert Python-Versionen sauber).

## Empfohlener Workflow für neue CLI-Tools

```bash
# 1. Existenz prüfen
which <tool>   # → not found

# 2. Install via uv (Browser-Extras wenn sinnvoll)
uv tool install "<tool>[browser]"

# 3. Binary-Pfad prüfen
ls -la ~/.local/bin/<tool>

# 4. PATH in nicht-login shells testen
bash -c 'which <tool>'    # wenn not found → Wrapper nötig

# 5. Wrapper-Skript schreiben
cat > ~/50-System/bin/<tool>-wrapper.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
exec <tool> "$@"
EOF
chmod +x ~/50-System/bin/<tool>-wrapper.sh

# 6. Shortcut-Symlink
ln -sf ~/50-System/bin/<tool>-wrapper.sh ~/50-System/bin/<shortcut>

# 7. PATH testen
~/50-System/bin/<shortcut> --version
```

## Secrets-Locations (NICHT in `~/.hermes/`)

Laut CLAUDE.md sind diese Files mit Tokens/Secrets tabu für Yuno:

- `~/.hermes/.env` — Telegram/Discord/API-Tokens
- `~/.gmail-organizer.json` — Plaintext App-Password
- `~/.chelper/config.yaml`, `~/.docker/config.json`, `~/.ollama/id_ed25519`
- `~/.yuno-cleaner/backups/*/client_secret_*.json`
- `~/.config/opencode/opencode.json` — z-ai MCP API-Key
- inline tokens in `crontab -l`

**Yuno darf sie lesen (per Pfad-Referenz), aber niemals Inhalte ausgeben.**

## Disk-Pressure-Workarounds (root-NVMe 65-75% voll)

```bash
# Platz checken VOR jeder größeren Installation
df -h /

# uv-tool-Cache aufräumen wenn nötig
uv cache clean

# Tool-spezifische Caches (z.B. Playwright-Chromium)
ls ~/.cache/ms-playwright/    # ~170 MB pro Browser-Build
```

## PATH-Persistenz

`.bashrc` von Basti hat `~/.local/bin` schon drin (laut CLAUDE.md). Aber:

- **Cronjobs** starten ohne `.bashrc`-Source → PATH fehlt
- **Neue Bash-Subshells** (z.B. in Skripten via `bash -c`) sourcen `.bashrc` manchmal nicht
- **Lösung:** Wrapper-Skript-Pattern oder expliziter `export PATH` am Anfang jedes Skripts

## Crash-Recovery für uv-Tool-Installation

```bash
# Wenn uv tool list ein Tool als installed zeigt, aber Binary fehlt:
uv tool uninstall <tool>
uv tool install "<tool>[browser]"

# Wenn PATH komplett verbogen ist:
source ~/.bashrc
hash -r   # Shell-Hash für which-lookups neu aufbauen
```

## Siehe auch

- `linux-system` (Skill) — System-Maintenance und Disk-Cleanup-Patterns
- `local-ai-security-hygiene` (Skill) — Ollama und Co. sauber installieren/entfernen
- `mnemosyne-memory-provider` (Skill) — Memory-Provider-Setup wenn Memory-Storage mitwandert