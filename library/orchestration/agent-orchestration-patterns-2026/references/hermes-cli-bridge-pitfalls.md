# Hermes-CLI Bridge — Pitfalls, Bug-Fixes & Live-Test

> Stand: 2026-07-16 · Validiert mit MiniMax-M3 (highspeed) auf Hermes Desktop

## Zusammenfassung

Die 3-strategige Hermes-Bridge (hermes_tools → subprocess → Mock) ist das Kernstück aller 3 Skeletons. Dieser File dokumentiert **was schiefgehen kann**, **wie es gefixt wurde** und **was die Live-Tests ergeben haben**.

## 🐛 Bug: Falsche `-z`-Flag-Position (kritisch)

### Symptom

Der originale Code (aus dem Perplexity Deep Research Report übernommen) hatte:

```python
# ❌ FALSCH — aus Perplexity-Report 2026-07-15
proc = await asyncio.create_subprocess_exec(
    "hermes", "chat", "-z", f"{task.context}\n\n{task.goal}",
    ...
)
```

Das führte dazu, dass:
- `hermes chat -z "prompt"` parst `-z` als **unbekanntes Sub-Command-Flag** (wird ignoriert)
- Der Prompt wird als **Sub-Command-Argument** statt als Prompt interpretiert
- Rückgabe: leerer Output, 0.3s Execution (fälschlich schnell)

### Root Cause

Die Hermes-CLI hat `-z` als **Top-Level-Flag**, nicht als Sub-Command-Flag:

```
hermes [-z PROMPT] chat [options]    ✅ KORREKT
hermes chat -z PROMPT [options]      ❌ FALSCH
```

### Fix (2026-07-16, master_worker.py:152-158)

```python
# ✅ KORREKT — -z ist Top-Level-Flag VOR sub-command
proc = await asyncio.create_subprocess_exec(
    "hermes", "-z", f"{task.context}\n\n{task.goal}",
    "chat",
    "--toolsets", ",".join(task.toolsets) if task.toolsets else "",
    "--model", task.model,
    "--no-restore-cwd",
    "--ignore-rules",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

### Lektion

**Jeder Hermes-CLI-Call per Subprocess muss `-z` direkt nach `hermes` setzen.** Gilt für alle: `hermes -z "prompt" chat`, `hermes -z "prompt" session`, etc. Nicht nur in diesen Skeletons.

---

## 🧪 Live-Test-Metriken (echte Hermes-Calls, kein Stub)

### Setup

| Parameter | Wert |
|---|---|
| Model | MiniMax-M3 (default in `~/.hermes/config.yaml`) |
| Provider | nous |
| Session-Typ | Hermes Desktop, Subprocess-Bridge |
| Test-Runs | 2 |

### Ergebnisse

| Run | Goal | Wall-Clock | Output-Char | Exit-Code |
|---|---|---|---|---|
| Dry-Run (Stub) | "Test goal" | **0.29s** | `[DRY-RUN STUB]` | 0 |
| Live-Test 1 | "Was ist 2+2? Antworte NUR mit der Zahl." | **7.27s** | `"4\n"` (1 char) | 0 |
| Live-Test 2 | "Nenne ein deutsches Sprichwort über Geduld in einem Satz." | **8.40s** | `"Gut Ding will Weile haben."` + 🌹 (~50 chars) | 0 |

### Erkenntnisse

1. **Realitätsfaktor ~25×** — Stub-Dry-Run 0.3s vs. echter LLM-Call 7-8s (MiniMax-M3 highspeed)
2. **Antwortqualität** — Echtes LLM kommt zurück mit korrekter Antwort inkl. Emoji
3. **Kein Stub-Leak** — Der Output ist eindeutig von Hermes/LLM, nicht vom Mock
4. **Token-Stats fehlen** — Hermes-Logs loggen keine Token-Verbräuche für Subprocess-Calls; Token-Tracking bleibt TODO

---

## 🔧 QUEEN_LIVE_TEST Workaround

### Problem

`master_worker.py` hat einen `plan()`-Stub der `NotImplementedError` wirft (TODO für echten Queen-LLM-Call). Für Bridge-Tests muss der Stub umgangen werden.

### Lösung

```bash
export QUEEN_LIVE_TEST=1
python3 master_worker.py --workers 1 --timeout 120 --worker-model MiniMax-M3 "Dein Prompt"
```

**Wirkung:** Wenn `QUEEN_LIVE_TEST` gesetzt ist, erzeugt `plan()` eine deterministische Single-Worker-Task-Liste mit 1 hartkodierten Task (dem Goal selbst). `plan()` wrapped das Goal als WorkerTask ohne LLM-Call.

### Code (in `master_worker.py`)

```python
async def plan(self, goal: str, context: str = "") -> list[WorkerTask]:
    if os.environ.get("QUEEN_LIVE_TEST"):
        return [WorkerTask(id=uuid4().hex[:8], goal=goal, context=context, toolsets=[], model=self.model)]
    raise NotImplementedError(
        "Queen-Plan-Stub: ersetze mit echtem LLM-Call (Sonnet empfohlen). "
        "Für Bridge-Test: QUEEN_LIVE_TEST=1 setzen."
    )
```

### Wann nutzen

- **Bridge-Validierung** — Teste ob Subprocess tatsächlich Hermes/LMM erreicht
- **CI/CD** — Smoke-Test für Hermes-Konnektivität
- **Nicht für Production** — Umgeht die Task-Decomposition; nur für Infrastruktur-Tests

---

## ✅ Verifikation

```bash
# 1. Bridge-Syntax validieren (hermes -z ... chat)
python3 -c "
import asyncio, json
async def test():
    proc = await asyncio.create_subprocess_exec(
        'hermes', '-z', 'Antworte nur mit JA.',
        'chat', '--model', 'MiniMax-M3', '--no-restore-cwd', '--ignore-rules',
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
    print(out.decode().strip())
asyncio.run(test())
"
# Erwartet: "JA"

# 2. Kein Stub-Leak
QUEEN_LIVE_TEST=1 python3 master_worker.py --workers 1 --dry-run "test" \
  | grep -c "DRY-RUN STUB"
# Erwartet: 0

# 3. Vollständige Test-Suite
python3 -m pytest tests/ -q
# Erwartet: 27 passed
```

## Quellen

- Perplexity Deep Research Report "Actionable Python: 3 Production Multi-Agent Orchestration Skeletons" (2026-07-15) — *enthielt die falsche `chat -z PROMPT` Syntax*
- Live-Test-Audit-Trails: `~/.hermes/logs/agent-orchestration-patterns/run-{1784183475,1784183501}-*.json`
- Doku: #agent-orchestration-patterns-2026 (HERMES) — Live Test F Session 2026-07-16
