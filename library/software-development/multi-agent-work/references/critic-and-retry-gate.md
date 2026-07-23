# Critic + Ollama Setup (V1.3) & Retry-Gate Konfiguration

## Lokaler Critic via Ollama (deepseek-r1:8b) [NEU in V1.3]

Der Critic läuft **nicht als Hermes-Subagent**, sondern als direktes Ollama-Script. Grund: Kein API-Token-Verbrauch, kein Netzwerk-Latenz, volle GPU-Nutzung der RTX 5060.

### Script

`~/.hermes/scripts/critic-gate-ollama.py`

```bash
# Aufruf:
cat critic_input.json | python3 ~/.hermes/scripts/critic-gate-ollama.py

# Exit-Codes:
# 0 = PASS
# 1 = RETRY
# 2 = FAIL oder Error
```

### Integration in multi-agent-work

Nach Phase 4 (Execution), bevor Finalizing:

```bash
# 1. Output in temporäre Datei schreiben
cat > /tmp/critic_input.json << 'EOF'
{
  "output": "$(cat ~/projects/foo/src/main.py)",
  "task_description": "Implementiere HTTP-Client mit Retry",
  "schema": {"type": "code", "language": "python", "required_sections": ["Error-Handling"]},
  "assertions": [
    {"id": "retry", "text": "Retry-Logik für Connection-Error vorhanden", "critical": true},
    {"id": "timeout", "text": "Timeout-Parameter konfigurierbar", "critical": false}
  ]
}
EOF

# 2. Critic aufrufen
python3 ~/.hermes/scripts/critic-gate-ollama.py < /tmp/critic_input.json > /tmp/critic_output.json
CRITIC_EXIT=$?

# 3. Entscheiden basierend auf Exit-Code
case $CRITIC_EXIT in
  0) echo "✅ PASS — weiter mit Finalizing" ;;
  1) echo "🔄 RETRY — Worker bekommt Delta-Feedback"
     FEEDBACK=$(python3 -c "import json; d=json.load(open('/tmp/critic_output.json')); print(d.get('feedback_for_worker',''))")
     # Worker erneut mit Feedback aufrufen
     ;;
  2) echo "❌ FAIL — Eskalation an Supervisor" ;;
esac
```

### Output-Schnittstelle

Der Critic liefert strukturiertes JSON:

```json
{
  "gate_passed": true,
  "schema_valid": true,
  "schema_errors": [],
  "criteria": [
    {"assertion": "Retry-Logik vorhanden", "met": true, "evidence": "Zeile 42: try/except", "fix": ""}
  ],
  "score": 10.0,
  "verdict": "PASS",
  "feedback_for_worker": ""
}
```

### Vorteile gegenüber Subagent-Critic

| Aspekt           | Subagent (Hermes)      | Lokales Script (Ollama)        |
|------------------|------------------------|--------------------------------|
| Kosten           | API-Token (DeepSeek V4)| 0 € (lokale GPU)               |
| Latenz           | ~5-15s (Netzwerk)      | ~30-120s (GPU lokal)           |
| Reasoning-Trace  | Nicht sichtbar         | Vollständig via R1             |
| Determinismus    | Variiert mit Model-Update| Stabil (lokale Version)      |
| Datenschutz      | Daten verlassen System | 100% lokal                     |
| Parallelität     | Max 3                  | Nur 1 (eine GPU)               |

### Einschränkungen

- **1 GPU = 1 Critic gleichzeitig** (RTX 5060, 8GB VRAM). Kein Batch-Critiquing.
- **Timeout 300s** hart im Script. Bei GPU-Auslastung kann ein Call blockieren.
- **Kein Streaming** — das Script wartet auf vollständige Response.
- Für schnelle Syntax-Checks den `output-validator` Skill nutzen (kein LLM nötig).

---

## Retry-Gate (V1.2)

Nach Phase 4 (Implementierung) wird jedes Worker-Output durch das zweistufige Gate geschleust:

```
Worker-Output
  → [OUTPUT-VALIDATOR]  (Syntax + Struktur)
    → PASS → [CRITIC-GATE via local deepseek-r1:8b]  (Semantik + Qualität)
      → PASS → Finalizing
      → RETRY → Worker bekommt Delta-Feedback (max 2x)
      → FAIL → Eskalation an Supervisor
    → FAIL → Sofort-Fix + Retry
```

### Retry-Gate Konfiguration

```yaml
retry_gate:
  enabled: true
  max_retries: 2                # danach: Eskalation an Supervisor
  feedback_mode: delta          # nur Critic-Feedback + letzter Output, kein Full-Rerun
  retry_target: worker          # zurück an Worker, nicht an Phase 1
  escalate_on_exhaust: true     # nach 2 Fails: Supervisor entscheidet
```

### Regeln

1. **verdict == "PASS"** → Weiter zur Finalizing-Phase
2. **verdict == "RETRY"** und `retries < 2` → Worker bekommt `feedback_for_worker` + letzten Output als neuen Kontext
3. **retries == 2** → Supervisor entscheidet: `no_prune` + stärkeres Reasoning, oder sauber abbrechen
4. **verdict == "FAIL"** → Sofortige Eskalation, kein weiterer Retry

### Delta-Feedback

Statt komplettem Task-Rerun bekommt der Worker nur:

```
TASK: <Original-Aufgabe>
LAST_OUTPUT: <Was der Worker zuletzt geliefert hat>
FEEDBACK: <Konkrete Fehler + Fixes vom Critic>
→ "Ergänze handle_retry() gemäß Plan-Schritt 4"
```

Dadurch:

- Token-Ersparnis: Kein Full-Rerun
- Präziser Kontext: Worker weiß genau was an dem letzten Output falsch war
- Kein Kontext-Creep: `context-pruner` V2 sorgt für Minimal-Kontext

---

## DMZ Dual-Review Gate Pattern (NEU V1.6)

Das mächtigste Orchestrierungs-Pattern aus der Analyse von TheMorpheus407's [the-dmz](https://github.com/TheMorpheus407/the-dmz) Projekt (Session 2026-06-23):

### Warum zwei Reviewer?

Statt eines Reviewer-Gates: **zwei unabhängige Reviewer mit verschiedenen Scopes**:

| Reviewer            | Scope                                  | Frage                       | ACCEPTED wenn...              |
|---------------------|----------------------------------------|-----------------------------|-------------------------------|
| **A (Correctness)** | Code-Qualität, Security, Syntax        | "Ist der Code korrekt?"     | Lint + Build + Tests grün     |
| **B (Coverage)**    | Anforderungsabdeckung                  | "Löst der Code das Issue?"  | Alle AC-Kriterien erfüllt     |

**Gate-Logik:** Beide müssen `ACCEPTED` als erstes Wort liefern. Bei `DENIED` → Delta-Feedback an Worker (kein Full-Rerun). Max 3 Retries, dann Eskalation an Supervisor.

### Shell-Orchestrierung (Alternative zu subagent-only)

Während `delegate_task` die primäre Methode für Hermes ist, zeigt das DMZ-Projekt einen alternativen Ansatz: Bash als Orchestrator, der AI-CLIs (`claude`/`codex`/`opencode`) aufruft. Vorteile: deterministischer, einfach debuggbar, Agent-Backend pro Rolle austauschbar. Für Hermes adaptiert via `hermes chat -q --model <role-model>`.

### Delegation-Modell-Strategie

**Empfehlung: Gratis-Modelle für alle Worker-Rollen.**

| Rolle             | Modell                       | Kosten | Kontext |
|-------------------|------------------------------|--------|---------|
| Research          | `openrouter/owl-alpha`       | 0€     | 1M      |
| Implement         | `openrouter/owl-alpha`       | 0€     | 1M      |
| Reviewer A        | `openrouter/owl-alpha`       | 0€     | 1M      |
| Reviewer B        | `openrouter/owl-alpha`       | 0€     | 1M      |
| Finalizer         | `openrouter/owl-alpha`       | 0€     | 1M      |
| **Parent (Queen)**| `deepseek/deepseek-v4-pro`   | paid   | —       |

`hermes config set delegation.model openrouter/owl-alpha` — alle Subagenten laufen gratis.

**Referenz:** `references/dmz-dual-review-patterns.md` — vollständige Analyse, Code-Beispiele, GreyHack-Adaption.