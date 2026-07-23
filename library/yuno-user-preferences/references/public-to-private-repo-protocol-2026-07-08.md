# Public-to-Private Repo Visibility Protocol (2026-07-08)

Established when making `Toqsick/hermes-v7` temporarily public for external cloning of the `MaxHermes` branch, then reverting to private.

## Workflow

1. **Risk-Assessment vor Public**
   - `git log --all --full-history --name-only | grep -E "\.env$|\.env\."` → no real .env committed
   - `git log --all -p | grep -iE "(sk-[a-zA-Z0-9]{20,}|gho_|AKIA[0-9A-Z]{16})"` → no API keys
   - `.gitignore` prüfen: `git check-ignore -v .env` muss aktiv sein

2. **Public schalten**
   `gh repo edit OWNER/REPO --visibility public --accept-visibility-change-consequences`

3. **Warten auf Clone-Bestätigung**
   User sagt "ist geclont" / "kann wieder privat"

4. **Zurück auf Private**
   `gh repo edit OWNER/REPO --visibility private --accept-visibility-change-consequences`

5. **Verifikation**
   `curl -sI https://github.com/OWNER/REPO` → sollte 404/403 sein

## Wichtig
- Der existierende Clone bleibt funktionsfähig nach Private-Switch
- GH Token kann mid-session expired sein → `gh auth status` vorher prüfen
- Bei HTTP 401: `gh auth refresh -h github.com -s repo`
