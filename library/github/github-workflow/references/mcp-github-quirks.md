# MCP GitHub vs gh CLI Fallback

Hermes kann GitHub über zwei völlig getrennte Pfade ansprechen, und **die Credentials sind NICHT geteilt**:

| Pfad | Auth-Quelle | Token-Speicher |
|------|-------------|----------------|
| `mcp_github_*` Tools (MCP) | `mcp_servers.github.env.GITHUB_TOKEN` in `~/.hermes/config.yaml` | Docker-Container-Env |
| `gh api ...`, `gh issue ...` etc. | `gh auth login` (keyring) oder `~/.config/gh/hosts.yml` | System-keyring + Config |

## Symptom wenn MCP GitHub 401t während `gh` CLI funktioniert

```
mcp_github_get_me() → {"error": "failed to get user: GET https://api.github.com/user: 401 Bad credentials []"}
gh auth status       → ✓ Logged in to github.com account Toqsick
```

## Was dann zu tun ist (Pitfall-Pattern)

1. **NICHT** mehrfach MCP-Tools retryen — das ändert nichts, weil MCP eigene Credentials hat.
2. **NICHT** blind `mcp_servers.github.env.GITHUB_TOKEN` patchen — kann Config-Drift zwischen MCP-Docker-Container und Host-`gh` Auth verursachen.
3. **Sofort auf `gh` CLI umsteigen** für read-only Operations:
   - User-Suche: `gh search users --json login,name`
   - Repo-Liste: `gh repo list Toqsick --json name,pushedAt,description`
   - Issues: `gh issue list --repo Toqsick/hermes-v7 --state open`
   - Issue-Body: `gh issue view 1 --repo Toqsick/hermes-v7 --json body | jq -r .body`
   - PR-Suche: `gh search prs --author Toqsick --state open --json number,title,repository`
   - API-generisch: `gh api "repos/Toqsick/hermes-v7/contents/ROADMAP.md" --jq .content`
4. **Verifizieren** mit `gh auth status` — zeigt aktiven Account + Token-Scopes.
5. **Bei MCP-Fix-Bedarf:** siehe `devops/hermes-admin` Skill → "Auth prüfen" Sektion (Container-Restart nach `config.yaml`-Patch nötig).

**Wann MCP reparieren statt umgehen:** Wenn der User explizit MCP-basierte Features nutzt (z.B. MCP-Tool-Routing via Plugin-Registry) oder wenn mehrere Sessions neu starten müssen. Für einmalige Research-Tasks: **`gh` CLI ist schneller und zuverlässiger** als MCP-Config-Debugging.

## MCP-tool response traps (verified 2026-07-07 batch CONTRIBUTING.md push)

- **`mcp__github__create_or_update_file` may return "File already exists. Provide SHA." even when the file genuinely does NOT exist on the target repo.** Verified: file was missing (curl 404), MCP said "already exists", but the server-side write still went through and the file appeared on the next GET. Treat MCP write errors as **soft signals, not ground truth**. After any error from this tool, always curl-verify the resulting state with `curl -s -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/OWNER/REPO/BRANCH/PATH`.
- **`mcp__github__get_file_contents` returns a sentinel success with SHA `777035533703e3b24b90916e17598aeb2f8fb17a`** for files that don't exist (curl gives HTTP 404). Never trust MCP existence checks — always curl-confirm with `https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=BRANCH` and parse the JSON.
- **`mcp__github__create_or_update_file` enters "MCP server 'github' is unreachable after 3 consecutive failures. Auto-retry available in ~32s." cooldown** after repeated failures. Do not keep hammering it — switch to `gh api -X PUT` or curl with `gh auth token` for the rest of the session. The cooldown is per-tool-call, not per-session, and the warning explicitly says "Do NOT retry this tool yet".
- When MCP and curl disagree on a file's existence, **curl wins**. MCP's success metadata is not authoritative for filesystem-shape questions (file present? which SHA? which size?).

## Beispiel-Workflow für Repo-Audit (read-only via `gh`)

```bash
# Repo-Inventar
gh repo list Toqsick --limit 100 --json name,description,pushedAt

# Heutige Commits (alternative zu MCP search)
gh api "repos/Toqsick/$repo/commits?since=$(date +%Y-%m-%d)T00:00:00Z&per_page=100" --jq 'length'

# Issue-Triage mit Labels
gh issue list --repo Toqsick/$repo --state open --limit 20 --json number,title,labels,createdAt \
  | jq -r '.[] | "#\(.number) [\(.labels | map(.name) | join(","))] \(.title)"'
```

## "Was wurde kürzlich gepusht?" — Push-Audit-Recherche

Wenn User behauptet „du hast gestern gepusht" / „da wurde was committed" / „ich glaub mein Auto-Push ist gelaufen" — die Frage ist **„was sagt der Remote-Stand im Vergleich zu lokal?"**, nicht „was sagt mein lokales Log?".

**Ground-Truth-Reihenfolge:**
1. `git ls-remote origin` → autoritativ, zeigt direkt was remote existiert (SHA + Ref pro Branch/PR)
2. Vergleich mit `git rev-parse origin/main` und `git rev-parse HEAD` → identisch = nichts gepusht
3. Wenn MCP GitHub 401 wirft: **nicht** retryen, sondern direkt `gh api` oder `git ls-remote` nutzen
4. Wenn `curl https://api.github.com/repos/.../commits` **404** zurückgibt → Repo ist **privat**, das ist eine nützliche Diagnose, kein Fehler

Vollständige Verifikationsmatrix (MCP/ls-remote/gh/public-API Triangulation), häufige Fehler (z. B. „Working tree clean ≠ nichts gepusht") und Session-Recipes: siehe `references/push-audit-research.md`.