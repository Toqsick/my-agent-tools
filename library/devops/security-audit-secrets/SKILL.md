---
name: security-audit-secrets
title: "Security Audit — Forensic Secret-Scanning"
description: "Use when running forensic secret-audits for cloud-coding-agenten or scanning for leaked tokens/keys. NOT for host-hardening (use security-audit-host)."
category: devops
version: '1.0'
created: '2026-07-23'
author: Yuno (split from system-security-audit)
lane: koenigin
agent: universal
trigger_keywords: ['secret', 'token', 'key', 'forensic', 'cloud-agent', 'leak', 'api-key']
keywords: ['secret', 'forensic', 'token', 'key', 'cloud-agent', 'leak']
related_skills: ['security-audit-host', 'security-audit-network']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from system-security-audit 2026-07-23)'

license: MIT
---

# Security Audit — Forensic Secret-Scanning

_Extracted from system-security-audit on 2026-07-23._

## Forensischer Secret-Audit für Cloud-Coding-Agenten

**Wann triggern:** User berichtet „das Modell X leakt Repos / sendet Daten an Y"
und hat kürzlich einen Cloud-Coding-Agenten (Hermes mit Cloud-Provider, Codex
CLI, Claude Code CLI, Copilot CLI, Grok Build CLI etc.) für lokale Aufgaben
genutzt.

Zielgruppe: Forensischer Beleg, was tatsächlich passiert ist — kein Hype, keine
Schuldzuweisung an ein einzelnes Modell ohne Mechanismus.

### 5 Pflichtfragen BEVOR du irgendeinen Befund in den Bericht schreibst

Aus Erfahrung mit dem Grok-Build-Gist (2026-07-10) und dem Basti-MiroFish-Audit
(2026-07-13). Diese fünf Fragen sind die häufigsten Fehlerquellen — beantworte
alle vor deiner ersten Severity-Vergabe:

1. **Headline vs. Mechanismus:** Wird ein **Modell** (z.B. `grok-4.5`) oder ein
   **Produkt-Harness** (z.B. `Grok Build CLI v0.2.93`) beschuldigt? Ein
   „Modell leak" ohne CLI/Harness drumherum ist physikalisch nicht möglich,
   weil das Modell selbst keinen Repo-Zugriff hat — der Provider/Harness stellt
   den her. **Pitfall:** Wenn du das nicht trennst, fabrizierst du entweder
   Entwarnung oder Panik am falschen Objekt.

2. **Welcher Inferenzpfad lief wirklich lokal?** Aus `~/.hermes/logs/agent.log`
   die Zeile `model=X provider=Y base_url=Z` extrahieren. Wenn `provider=nous`
   und nicht `provider=xai`/`anthropic`/`openai`, dann ist es ein Routing-Fall
   mit unbekanntem Downstream — die Storage-Mechanismen einer Direkt-CLI sind
   **nicht äquivalent** zu Modell-Aufrufen über Drittanbieter.

3. **Datum-Korrektur:** User-Erinnerung („11.6.") ist nicht vertrauenswürdig,
   wenn die Session-DB eine andere Zeit hat. Im Audit IMMER zuerst
   `state.db` → `sessions.started_at` lesen, dann die User-Aussage als
   Selbstauskunft behandeln. Den User-Hinweis im Bericht erwähnen
   („User nannte JJ.MM., Belege zeigen JJ.MM."), nicht stillschweigend
   überschreiben — sonst referenziert die spätere Diskussion eine Phantom.

4. **„Produkt installiert" ≠ „Produkt lief":** Bei Grok-Build-Exfil reichte die
   Anwesenheit der Binary nicht — der Mechanismus feuerte auf *jeden* CLI-Start,
   sobald `grok` in einem Git-Repo gestartet wurde. Daher:
   `command -v grok` UND `grep agent.log` (oder lokales Run-Profil).
   Nur die Anwesenheit beweist noch keinen Vorfall.

5. **„Whole-Repo" ist vom Upstream differenzierbar:** Wenn das Repo lokal
   gegen `git ls-remote origin HEAD` identisch ist und keine Hooks/Submodule/
   Autostarts hat, kann kein Whole-Repo-Bundle-Drop ohne Spuren geblieben sein.
   Clean-Check, der den Mechanismus sofort entkräftet:
   ```bash
   git rev-parse HEAD
   git ls-remote origin HEAD
   test -z "$(git submodule status --recursive)"
   test -z "$(for f in .git/hooks/*; do [ -x "$f" ] && case "$f" in *.sample) ;; *) echo "$f";; esac; done)"
   ```

### 4-Phasen-Pattern (read-only)

| Phase | Frage | Quellen |
|---|---|---|
| 1. Headline entkoppeln | Wird ein **Modell** (z.B. `grok-4.5`) oder ein **Produkt-Harness** (z.B. `Grok Build CLI v0.2.93`) beschuldigt? | News-Body, Original-Gist, GitHub-Repo |
| 2. Tool-Lokalisierung | Welcher Agent lief lokal? Welcher Provider, welche base_url, welche Modell-ID? | `~/.hermes/logs/agent.log`, Session-DB `~/.hermes/state.db`, MCP-Config, installierte Binaries |
| 3. Lokale Timeline | Welche Aktionen wurden wann ausgeführt? Was wurde in den Modellkontext gegeben? | Hermes-Session-API-Calls, Tool-Aufrufe, `.env`-Modus, Bash-History |
| 4. Secret-Spread | Welche Schlüssel wurden während der Session in Chat/Tool-Output übermittelt? | `scripts/audit-secret-spread.py` |

### Phase 2: Tool-Lokalisierung — Schnellprofil

```bash

set -euo pipefail
# Welche Agent-CLIs sind installiert?
for b in hermes codex claude copilot opencode grok grok-build agy; do
  command -v "$b" 2>/dev/null && echo " ↑ $b found" || true
done
# Harness-Verzeichnisse?
ls -ld ~/.grok/ ~/.claude/ ~/.copilot/ ~/.opencode/ ~/.codex/ 2>/dev/null
# Laufende Agent-Prozesse?
pgrep -af 'grok|claude|codex|copilot|opencode|hermes-cli'
```

**Entscheidungs-Logik:** Wurde weder die verdächtige CLI noch ein anderer
bekannter Exfil-Harness ausgeführt, ist der gemeldete Vorfall mechanistisch
**nicht** anwendbar auf die lokale Maschine — was nicht heißt, dass nichts
passiert ist (siehe Phase 4), sondern dass der konkrete Whole-Repo-Upload-Mechanismus
lokal nicht gefeuert haben kann.

### Phase 4: Secret-Spread in Hermes-Sessions (SQLite read-only)

Bastis Vorliebe (gelernt 2026-07-13): **immer zuerst Bericht, dann auf Freigabe
warten.** Bei einem Secret-Audit nichts auto-rotieren, nichts in `.env` patchen,
bevor er explizit grünes Licht gibt.

Verwendung des Audit-Skripts:

```bash

set -euo pipefail
SID=$(hermes session list --recent 1 | grep -oE '[a-f0-9_]+' | head -1)
python3 ~/.hermes/skills/devops/system-security-audit/scripts/audit-secret-spread.py \
  "$SID" ~/Pfad/zum/Repo
```

Das Skript prüft für jeden Wert aus jeder `.env` im Projekt-Tree, wie oft der
Wert in `~/.hermes/state.db` (Tabelle `messages`, session = `SID`) in `content`
oder `tool_calls` auftaucht. Ausgabe: **nur Prefix, Länge, Hit-Count, Schweregrad — nie der Klartext.**

| Hit-Pattern | Schwere | Aktion |
|---|---:|---|
| 0 in messages, nur in `.env` | 🟢 | kein Leak-Pfad über Inferenz; nur File-Perm prüfen (sollte 600) |
| ≥1 in messages/content (User-Msg) | 🔴 P0 | **Rotation sofort freigeben lassen — nicht auto-fixen** |
| ≥1 in tool_calls | 🔴 P0 | **Rotation sofort freigeben lassen — Tool kann Output re-senden** |
| ≥1 nur in Tool-Output, nicht in content/tool_calls | 🟡 P1 | wahrscheinlich Tool-Antwort mit Echo; genauer prüfen |

**Pitfalls (Phase 4)**

- **Niemals Secret-Value im Audit-Output anzeigen.** Nur Prefix (`z_1d`), Länge,
  Hit-Count, Schweregrad. Volltext-Wert ausschließlich in Rotation-Skripten
  verwenden, die der User explizit startet.
- **`mode=ro` URI** in SQLite-Connects verwenden, sonst editiert die Lib ggf.
  WAL-Header. Audit ist read-only.
- **Nicht alle Treffer sind Daten-Leaks.** Ein Hit in `tool_calls` kann legitim
  sein (z.B. wenn der Tool den Key brauchte). Aber sobald der Chat-Inhalt an
  den Modell-Inferenzpfad ging, zählt der Schlüssel als offengelegt.
- **Multi-Provider-Sessions:** Bei Modellwechseln (z.B. Grok → DeepSeek →
  MiniMax) wurde der Geheimnispfad an alle beteiligten Provider gesendet. Bei
  Privacy-Anforderung muss jeder Provider separat informiert werden.

### Reporting-Workflow (Basti-Präferenz 2026-07-13)

1. Audit komplett durchziehen — alles notieren, aber **nichts auto-fixen**,
   keine Rotation, keine `.env`-Edits.
2. Bericht in `~/.hermes/docus/audits/<topic>-audit-YYYY-MM-DD.md` schreiben
   (Mode 0600).
3. Vault-Spiegel nach `~/Dokumente/Obsidian Vault/09 System-Doku/Security/`
   (kompakte Variante + Wikilink-Frontmatter).
4. Mnemosyne-Memory mit dem Audit-Outcome, scope = global, importance ≥ 0.85.
5. **Erst dann** dem User konkrete A/B/C/D Optionen vorlegen
   (Rotation, Mitigation, nichts tun).
6. Jede Rotation als kleines PATCH-Update in den Bericht: Zeitpunkt + Key-ID,
   **nie** den Wert.

## Final Report mit Options

Nach Abschluss von Scouts + CRIT-Verification + Sudo-Sammlung: den Final Report
als **dringlich + entscheidbar** liefern. Keine offene Frage, sondern konkrete
A/B/C/D-Optionen.

### Report-Struktur

1. **P0-KRITISCH** (🔴) — Sofort-Handlungsbedarf
2. **P1-WICHTIG** (🟡) — Diese Woche adressieren
3. **GESUND** (🟢) — Kein Handlungsbedarf
4. **Artefakt-Verweise** — Pfade zu Sudo-Sammlung, Report-Dateien
5. **Options-Übergabe** — Konkrete A/B/C/D Optionen

### Options-Struktur

```
Option A: [PERSISTENT] Beschreibung — was passiert, Risiko
Option B: [TEMPORÄR] Beschreibung — reversibler Fix, erwarteter Gewinn
Option C: [NACHPRÜFEN] Beschreibung — Klärungsbedarf, keine Aktion
Option D: [AUFRÄUMEN] Beschreibung — Dinge stoppen/löschen, Platzgewinn
```

Jede Option hat: konkrete Aktionsschritte, Risiko, erwarteter Effekt.

### Beispiel aus 5-Scout-Schwarm 2026-07-11

```
Option A: [PERSISTENT] Hermes-Config Härten (default-deny + write_paths + deny-list)
  → Config-Backup + YAML-Patch + reload. Risiko: Service-Neustart.
Option B: [TEMPORÄR] syslog + Journal vacuum (~12 GiB)
  → truncate -s 0 + journalctl --vacuum. Reversibel.
Option C: [NACHPRÜFEN] Tailscale-Ports 443/8443-46 klären
  → Bewusst oder Leak? Erst klären, dann entscheiden.
Option D: [AUFRÄUMEN] github-mcp-server Container stoppen
  → Container-Hygiene, ~535 MB+ freigebbar.
```

### Referenzen
- `references/wire-capture-bulk-analysis.md` — Bulk-Capture-Analyse von `ss`-Logs mit N Snapshots: Deduplizierung, Orphan-Analyse, Regex-Pitfall (`users:(())`), Report-Struktur.
- `references/network-service-audit.md` — Vollständiges Audit-Protokoll einer Hermes-Gateway-Security-Inspektion (2026-07-16): Live Route Probing, Auth Mechanism Verification, Configuration Source Tracing, Network Exposure Assessment, Process Lifecycle Tracking. **Primäres Referenz-Dokument für Layer-4-Audits.**
- `references/fix-block-delivery-pattern.md` — Fix-Block-Delivery-Pattern: Template, Aufbau und Case Study aus dem 2026-07-16 System-Audit (A→B1→D Ausführungsreihenfolge). Sequentielle Copy-Paste-Blöcke als Alternative zur Sudo-Sammlung.
- `references/grok-build-cli-leak-2026-07-13.md` — Vollständiges Beispiel-Audit: Headline → Mechanismus.
- `references/grok45-model-assessment-detail.md` — Strukturierte Modellevaluierung für Grok 4.5.
- `references/drift-aware-audit-report.md` — **Erweitert 2026-07-18 (v2.0).**
  Recurring-Audit-Report-Pattern mit 4 Strukturelementen: Reality-Check-Tabelle,
  Drift-Cross-Check, Read-only-Disclaimer, und NEU CLAUDE.md/AGENTS.md-Drift-
  Sektion. Plus logrotate-SUCCESS-≠-Rotation-Pitfall. Validiert am System-Audit
  2026-07-17 (2× P1, 4× P2, 5× P3) und erweitert am System-Scan 2026-07-18.
