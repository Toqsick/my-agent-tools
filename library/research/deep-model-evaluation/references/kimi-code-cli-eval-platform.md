# Kimi Code CLI — Eval Platform & Provider-Catalog System

**Stand:** 2026-07-19 | **Getestet mit:** Kimi Code CLI v0.27.0 auf Linux (Zorin OS 18.1)
**Stichworte:** kimi-cli, provider-catalog, kimi-k3, moonshotai, token-burn, oauth, eval-harness

---

## 1. Was Kimi Code CLI ist (und was nicht)

Kimi Code CLI (`kimi`) ist ein **provider-agnostischer Agentic Coding Client** — nicht nur ein Kimi-K3-Wrapper. Es hat:

- Ein **Provider-Catalog-System** (`kimi provider catalog`) um Modelle von Dutzenden Anbietern zu entdecken
- **OAuth-Login** (`kimi login`) für Kimi-Native-Accounts
- **Provider-add** für beliebige custom/OpenRouter-API-Endpoints
- **Non-interactive Mode** (`-p "prompt"`) für automatisierte Eval-Runs
- **ACP-Server** (`kimi acp`) als Agent Client Protocol

**Installation:**
```bash
curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
# → ~/.kimi-code/bin/kimi auf PATH
```

**Wichtige Quirk beim Install:** Kimi CLI scannt bestehende Configs (OpenAI API Keys, etc.) und **importiert automatisch** erkannte Provider als `inline`-Quelle. Bei Basti wurde `minimax` importiert, weil die Anthropic-kompatible MiniMax-API-Config existierte.

---

## 2. Provider-Catalog API

### Modelle entdecken

```bash
kimi provider catalog list                       # Alle Provider
kimi provider catalog list moonshotai            # Modelle eines Providers
# → kimi-k3 (1M ctx), kimi-k2.7-code, kimi-k2.6, ...
```

**Bekannte Kimi-relevante Provider im Catalog (Stand Jul 2026):**

| Provider-ID | Wire | Models | Beschreibung |
|---|---|---|---|
| `moonshotai` | openai | 10 | Direkte Kimi-Moonshot-API (K3, K2.7, K2.6, ...) |
| `moonshotai-cn` | openai | 10 | Moonshot API (China-Route) |
| `kimi-for-coding` | anthropic | 3 | Speziell auf Code-Workflows optimiert |

### Provider importieren

```bash
kimi provider catalog add moonshotai              # Alle Modelle von moonshotai
kimi provider catalog add kimi-for-coding         # Agent-optimiert
kimi provider list                                # Nach Import prüfen
kimi provider remove moonshotai                   # Entfernen
```

### Provider manuell hinzufügen (OpenRouter)

```bash
kimi provider add https://openrouter.ai/api/v1
# → Fragt nach API-Key, fügt alle OpenRouter-Modelle hinzu
```

---

## 3. OAuth-Login (für Cup-Token-Verbrauch)

```bash
kimi login
# → Startet Device-Code-Flow → Browser öffnet sich
# → Nach Login: Kimi-Native-Provider + Modelle aktiviert
```

**Ohne** `kimi login` kann K3 trotzdem via OpenRouter/catalog genutzt werden — aber über Billing, nicht Cup-Tokens. Der Login aktiviert den Kimi-Native-Account als zusätzlichen Bezahlweg.

| Zugangsweg | Token-Quelle | Kosten |
|---|---|---|
| `kimi login` (OAuth) | Kimi-Account-Guthaben + Cup-Tokens (Promo) | Cup-Tokens zuerst |
| `kimi provider add openrouter` | OpenRouter-Billing | Standard-Raten |
| `kimi provider catalog add moonshotai` + API-Key | Moonshot-Direkt-Billing | Standard-Raten |

---

## 4. Modell-Running (Non-Interactive Eval)

```bash
kimi --model moonshotai/kimi-k3 -p "Gib mir ein Python-Skript" -y
kimi --model moonshotai/kimi-k3 -p "$(cat task-01.md)" -y   # File als Prompt
kimi --model moonshotai/kimi-k3 -p "..." --output-format text
kimi --model moonshotai/kimi-k3 -p "..." --output-format stream-json
```

**Verfügbare K3-Varianten (Stand Jul 2026):** `moonshotai/kimi-k3` (1M ctx, Chat/Agent). Kein `kimi-k3-max` oder `kimi-k3-swarm-max` im catalog — exklusiv über Kimi Web/Kimi Work.

---

## 5. Eval-Integration (Phase 9 Workflow)

### Pattern A: Kimi CLI als einzige Eval-Harness

```bash
for model in "minimax/MiniMax-M3" "moonshotai/kimi-k3"; do
  for task in tasks/task-*.md; do
    task_name=$(basename "$task" .md)
    output_dir="runs/$(echo "$model" | tr '/' '_')/$task_name"
    mkdir -p "$output_dir"
    start=$(date +%s%N)
    kimi --model "$model" -p "$(cat "$task")" -y > "$output_dir/output.md"
    end=$(date +%s%N)
    echo $(( (end - start) / 1000000 )) > "$output_dir/duration_ms.txt"
  done
done
```

**Pitfall Bash-Quoting:** Lange Prompts mit Backticks, `$()`, oder geschachtelten Quotes brechen. Sicherer Weg für komplexe Tasks:

```bash
tmpfile=$(mktemp)
cat tasks/task-01.md > "$tmpfile"
cat >> "$tmpfile" << 'EOF'

--- User Input ---
Implementiere die Funktion parse_config() ...
EOF
kimi --model "$model" -p "$(cat "$tmpfile")" -y
rm -f "$tmpfile"
```

### Pattern B: Kimi CLI + Hermes Hybrid (empfohlen für K3-Eval)

- **Baseline-Modelle** (M3): Über `hermes -p yuno-eval-<model>` — voller Tool-Stack
- **K3-Vergleich**: Über `kimi --model moonshotai/kimi-k3 -p "..."` — nutzt Cup-Tokens
- Gleiche Tasks, gleiche Acceptance-Criteria, gleiches Judging

---

## 6. Budget-Pivot: Token-Burn-Strategie

Wenn User sagt "kein Geld mehr" → sofort pivoten:

### Staircase-Workflow

```
1. FRAGE: "Hast du irgendwelche Promo-Tokens/Credits?"
2. WENN JA: Nutze die als primäre Eval-Plattform
   → Identifiziere Tool das Tokens konsumiert (CLI, Web, App)
   → Baue Burn-Strategie mit Phasen
   → Setze Hard-Deadline-Reminder (Crons!)
3. WENN NEIN: Nutze lokale Modelle als Baseline
   → Reduziere Task-Scope auf 2-3 Kern-Tasks
4. IMMER: Freeze Baseline zuerst (kostenlos/minimal)
   → Kill-Switch: wenn Premium unter Baseline → abbrechen
   → First-Run-Cost vs Steady-State-Cost rapportieren
```

### Token-Burn-Phasen-Plan (Template)

| Phase | Tage | Burn-Rate | Fokus |
|---|---|---|---|
| 1. Heavy Sprint | 1-3 | ~35M/Tag | Coding-Sessions (Refactor, Feature, Debug) |
| 2. Deep Research | 4-7 | ~75M/Tag | 1M-Context Doc-Analysen, Multi-File-Synthesis |
| 3. Bulk Processing | 8-10 | ~70M/Tag | Batch-Runs, Parallel-Sessions, Swarm-Testing |
| 4. Final Burn | 11-12 | ~30M/Tag | Resteverwertung vor Deadline |

**Hard Deadline immer in Beijing Time prüfen!** (UTC+8 → z.B. 31.07. 23:59 CST = 17:59 MESZ)

---

## 7. Bekannte Limitationen & Pitfalls

| Problem | Symptom | Lösung |
|---|---|---|
| Session-DB pro CWD | Zwei Sessions im gleichen Verzeichnis teilen History | Separate `runs/`-Subdirs nutzen |
| Kein `--max-turns` im prompt-Mode | `-p` fährt nur eine Runde | Task muss alles in ein Prompt packen |
| Auto-import von bestehenden Providern | Kimi nutzt MiniMax statt Kimi-K3 nach Install | `kimi provider add moonshotai` + default setzen |
| Tool-Use nur mit `-y` | Ohne -y hält Kimi bei jedem Tool-Call | `-y` setzen für non-interactive Eval |
| Reasoning-Token-Overhead bei K3 | Always-on Reasoning (~79% Token-Overhead) | Kosten pro Task ~1.8× Rohpreis einplanen |
| Kein Effort-Level bei K3 | Anders als DeepSeek V4 Flash | Kostet IMMER full reasoning |
| Config persistenz nach login | `kimi login` ändert nicht `default_model` | `default_model` in config.toml manuell setzen |
| `kimi server` Port-Kollision | Daemon auf localhost | Nicht parallel im eval-run nutzen |

---

## 8. Verifikation nach Setup

```bash
kimi doctor                                              # Config valide?
kimi --model moonshotai/kimi-k3 -p "Reply only: OK" -y   # Model verfügbar?
kimi provider list                                       # Alle Provider?
ls ~/.kimi-code/server.token 2>/dev/null && echo "✅ OAuth active"
```

---

## Verwandte Skills

- `deep-model-evaluation` — Phase 9 API Eval Methodology (diese Datei ist Sub-Referenz)
- `model-selector` — Modell-Preisvergleich (K3 Pricing, Benchmarks)
- `claude-code-provider-profiles` — paralleles Pattern für Claude Code Multi-Provider
