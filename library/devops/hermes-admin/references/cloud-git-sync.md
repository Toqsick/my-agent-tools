# Git-Based Cloud Hermes Sync (when SSH/VPN is impossible)

Erprobt am **MaxHermes Cloud Pod** (2026-07-08) — Alibaba ECI mit Deny-All-Ingress.
Kein SSH, kein VPN, kein Tailscale möglich. Lösung: **Git als Transport-Layer**.

## Architektur (Desktop → GitHub → Cloud Pod)

```
┌─────────────────┐     Git Push     ┌───────────────────┐     Git Pull (Cron)    ┌─────────────────┐
│  Basti Desktop   │ ────────────────→│  GitHub: MaxHermes │ ←──────────────────────│  Cloud Pod       │
│  (Config bauen)  │                  │  Branch             │                        │  (Config nutzen) │
└─────────────────┘                  └───────────────────┘                        └─────────────────┘
        │ Git pull von user.local                                      Kein SSH, VPN, LB — nur HTTPS outbound
        │ offline edit, commit, push
        ▼
   ~/hermes-v7/examples/maxhermes/
```

**Kern-Erkenntnis:** Wenn ein Cloud-Pod keinen Ingress erlaubt (Alibaba ECI, K8s Pod ohne Service/LB), aber HTTPS-Outbound funktioniert, ist **Git-Pull der einzige reliable Sync-Weg**.

## Key Pattern: Branch als Config-Portal

Statt einem separaten Repo → **dedizierter Branch im bestehenden Hermes-Repo**.

### Vorteile
- Kein zweites Repo zu verwalten (Issues/CI/Secrets bleiben zentral)
- Branch basiert auf main → CI-Pipelines + Linter gelten automatisch
- Config-Templates sind versioniert und diffbar
- Späterer Merge nach main möglich (wenn Config verallgemeinert)

### Nachteil
- Branch muss nicht-geschützt sein (damit Pod pushen kann, z.B. Backup)
- README im Branch muss klar machen: **"Das ist die Cloud-Variante, nicht der main-Branch"**

### Verzeichnisstruktur (erprobt)
```
maxhermes/                          # Wurzel der Cloud-Konfiguration
├── README.md                       # Quick-Start + Architektur-Erklärung
├── config/                         # Sanitisierte YAML-Templates
│   ├── model.yaml                  #   Model & Provider Defaults
│   ├── mcp.yaml                    #   MCP-Server-Konfiguration
│   ├── security.yaml               #   Cloud-Hardening (kein sshd, redact_secrets=true)
│   └── providers.yaml              #   Multi-Provider mit Fallbacks
├── skills/                         # Empfehlungen: Welche Skills im Cloud-Kontext Sinn machen
│   ├── RECOMMENDED.md              #   Top-20 für Cloud (Web, Image, GitHub, Research)
│   └── SKILLS-INDEX.md             #   Vollständiges Inventar + Ausschlussliste
├── scripts/                        # Pod-seitige Tools (müssen ausführbar sein)
│   ├── sync-from-github.sh         #   Cron-Pull alle 60 Min
│   ├── healthcheck-pod.sh          #   Self-Test aller Komponenten
│   └── backup-config.sh            #   Snapshot der Pod-Config nach Git (sanitised)
├── docs/                           # Architektur-Doku (lesbar, ohne Secrets)
│   ├── ARCHITECTURE.md             #   3-Hosts-Übersicht + Verbindungs-Matrix
│   ├── SSH-STATUS.md               #   SSH-Limitations analysiert + dokumentiert
│   └── SETUP-STATUS.md             #   Pod-Status zum Zeitpunkt der Doku
├── _pod-backups/                   # (nur .gitkeep committed) — echte Backups ignored
└── workflows/
    └── README.md                   # GitHub-Actions-Plan für Cloud
```

## Pattern: Sanitisierte Config-Templates

Beim Erstellen von Cloud-Configs im Branch: **Niemals echte API-Keys, Tokens oder Secrets committen.**

### Was raus muss
- `api_key` / `token` Felder → Kommentar `# aus .env`
- `password` / `secret` Keys → placeholder `"__REPLACE_WITH_ENV__"`
- Absolute Pfade zur Desktop-Umgebung → Pfade, die erst im Pod existieren

### Was drin bleiben darf
- Provider-Definitionen (welcher Provider, welche URL)
- Feature-Flags (redact_secrets, toolsets, etc.)
- Timeouts, Limits, generische Konfiguration
- Kommentare und Struktur-Vorlagen

### Beispiel (aus Modell-Config)
```yaml
# maxhermes/config/model.yaml — Template ohne Secrets
model:
  default: minimax-m3-0806
  provider: minimax
  # api_key wird aus ~/.hermes/.env geladen
  context_length: 128000
```

## Pattern: Pod-seitiger Sync (Cron-Job)

Der Pod **pullt** selbständig vom Branch, statt dass jemand pushen muss.

```bash
# Im Cloud-Pod EINMALIG ausführen:
git clone https://github.com/<owner>/hermes-v7.git ~/hermes-v7-cloud
cd ~/hermes-v7-cloud && git checkout <branch>

# Dann Cron-Job einrichten:
(crontab -l 2>/dev/null; echo "0 * * * * cd ~/hermes-v7-cloud && git pull --ff-only && bash maxhermes/scripts/sync-from-github.sh >> /tmp/maxhermes-sync.log 2>&1") | crontab -
```

### Sync-Script (sollte im Branch liegen)
```bash
#!/usr/bin/env bash
# maxhermes/scripts/sync-from-github.sh
# Läuft stündlich via Cron. Pullt neue Config vom MaxHermes-Branch.
set -euo pipefail

BRANCH="MaxHermes"
REPO_DIR="${HOME}/hermes-v7-cloud"

cd "$REPO_DIR"
git fetch origin "$BRANCH"
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [[ "$LOCAL" != "$REMOTE" ]]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Sync: $LOCAL → $REMOTE"
    git merge --ff-only "origin/$BRANCH"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Sync: OK"
else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Sync: already up-to-date"
fi
```

## Pattern: GitHub Actions für Cloud-Validierung

Workflows, die beim Push auf den Cloud-Branch feuern — **kein Pod-Zugriff nötig**, läuft auf GitHub-Runnern.

| Workflow | Trigger | Prüft |
|---|---|---|
| `maxhermes-validate.yml` | Push/PR auf Branch | YAML-Syntax, ShellCheck, Markdown-Links, Executable-Flags |
| `maxhermes-daily-check.yml` | Cron 03:00 UTC | Neue Commits in letzten 24h → Summary in GitHub UI |

### validate.yml — Minimal aber effektiv
```yaml
on:
  pull_request:
    branches: [MaxHermes]
    paths: ['maxhermes/**']
jobs:
  validate-configs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { ref: MaxHermes }
      - name: YAML syntax check
        run: for f in maxhermes/config/*.yaml; do
               python3 -c "import yaml; yaml.safe_load(open('$f'))"
             done
      - name: ShellCheck
        uses: ludeeus/action-shellcheck@2.0.0
        with: { scandir: maxhermes/scripts }
```

## Evaluation Workflow for Cloud Deployments

Bevor Config gebaut wird: **immer erst Ist-Zustand analysieren, dann evaluieren, dann bauen.** Erprobt und vom User bestätigt.

```
Phase 1 — Architektur-Review (Ist-Zustand)
├── 1.1 Cloud-Instanz: Hardware, OS, Netzwerk
├── 1.2 Hermes-Konfiguration: Version, Model, Provider, Toolsets
├── 1.3 Verzeichnis-Struktur & Persistenz
├── 1.4 Installierte Tools & CLI-Agents
├── 1.5 Multi-Agent-Architektur-Status
└── 1.6 Fazit + Scorecard-Rohdaten

Phase 2 — Evaluation (Scorecard)
├── 2.1 Kriterien: Connectivity, Security, Sync, Performance, etc.
├── 2.2 Gewichtete Bewertung (1-5 Sterne pro Kriterium)
├── 2.3 Optionen-Vergleich: SSH/VPN vs Git-Only vs andere
└── 2.4 Empfehlung mit Begründung

Phase 3 — Setup (Neubau)
├── Konfig-Templates erstellen (sanitisiert)
├── Sync-Skripte schreiben
├── Workflows anlegen
├── Doku schreiben
└── Commit + Push auf Branch
```

## Bekannte Pitfalls

1. **Kein `git push --force`** auf Branch ohne Rücksprache — Pod verliert Referenz
2. **Cron-Job darf nicht aufstapeln** — `--ff-only` bricht ab wenn Konflikt, Pod merkt es im Log
3. **Configs immer zuerst sanitisieren** — kein Token soll je im Branch landen
4. **README muss klar sein** — Branch ist Cloud-Variante, nicht der main-Branch
5. **Pod-Backups nie committen** — mit `_pod-backups/[0-9]*/` im `.gitignore` ausgeschlossen

## Full Worked Example

→ Siehe `Toqsick/hermes-v7` Branch `MaxHermes` (erstellt 2026-07-08) als lebendes Beispiel:
- 7 Commits, ~1700 Zeilen
- Config-Templates: model.yaml, mcp.yaml, security.yaml, providers.yaml
- 3 Pod-Skripte: sync, healthcheck, backup
- 3 Architektur-Dokumente
- 2 GitHub-Workflows
- README-MaxHermes.md als Einstiegspunkt
