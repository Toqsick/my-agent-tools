# Skeleton C — Critic-Loop (Maker-Checker / Reflexion)

**Source:** `~/10-Projekte/10-active/agent-orchestration-patterns/critic_loop.py` (578 LOC, 21 KB)
**Pattern:** Maker-Checker / Reflexion mit zwei verschiedenen Modellen
**Use-Case:** Korrektheit kritisch (Code-Gen, Security-Reviews, Content-Validierung)

## Architektur-Übersicht

```
        ┌──────────────────────────────────────────┐
        │            Critic-Loop-Runner            │
        │                                          │
        │  for round in range(max_rounds=3):       │
        │      ┌──────────────┐                    │
        │      │   WORKER     │  (günstig: Flash)  │
        │      │   Maker      │                    │
        │      └──────┬───────┘                    │
        │             │ output                     │
        │             ▼                            │
        │      ┌──────────────┐                    │
        │      │   CRITIC     │  (fähig: Sonnet)   │
        │      │   Checker    │                    │
        │      └──────┬───────┘                    │
        │             │ verdict (PASS/REVISE/FAIL)│
        │             ▼                            │
        │   ┌─────────────────────┐                │
        │   │  Termination-Check: │                │
        │   │  UNRECOVERABLE? → stop              │
        │   │  PASS?         → accept             │
        │   │  REVISE + rounds<max → loop         │
        │   │  REVISE + rounds==max → best-so-far │
        │   └─────────────────────┘                │
        └──────────────────────────────────────────┘
```

## Wann nutzen

✅ **Ja:**
- Korrektheit ist kritisch (Code muss laufen, Tests müssen passen)
- Verification-Overhead gerechtfertigt (z.B. Security-Code, medizinische Inhalte)
- Worker hat Tendenz zu Halluzination/Sycophancy
- Iterative Verbesserung möglich (Feedback verbessert Output)

❌ **Nein:**
- Triviale Tasks (Overhead lohnt nicht)
- Kein klares Rubric definierbar (Critic rät sonst)
- Kosten extrem sensitiv (40-60% teurer als Skeleton A)
- Sequenzielle Subtasks (nicht iterativ verfeinerbar)

## Kern-Komponenten

### 1. WorkerOutput (Output des Workers)

```python
@dataclass
class WorkerOutput:
    content: str             # generiertes Artefakt (Code, Text, ...)
    rationale: str           # Worker-Selbst-Erklärung — NIEMALS an Critic!
    metadata: dict[str, Any]
```

**⚠️ KRITISCH: `rationale` bleibt IMMER LEER wenn an Critic übergeben!**

**Warum Sycophancy-Guard:**
- Wenn der Critic die Worker-Selbst-Einschätzung sieht, mirrort er sie
- Critic wird zum "Ja-Sager" statt objektiv zu prüfen
- Defensiver Pattern: Worker-Code setzt rationale="", nur content wird bewertet

### 2. EvaluationRubric (was der Critic bewertet)

```python
@dataclass
class EvaluationRubric:
    required_criteria: list[str]       # ALLE müssen passen für PASS
    preferred_criteria: list[str]     # nice-to-have, blockieren PASS nicht
    max_score_for_revise: float = 0.79
    unrecoverable_signals: list[str]   # Pattern die auf FAIL hindeuten
```

**Rubric-Design ist KRITISCH:**
- **Vage Rubrics → Critic findet nie Issues → Sycophancy → Loop terminiert früh mit schlechtem Output**
- PRO TASK definieren, nicht global
- Required-Criteria: hart messbar ("GreyScript Syntax ist valide", nicht "Code ist gut")
- Unrecoverable-Signals: harte Stop-Wörter ("contains hardcoded api key", "infinite loop")

### 3. Verdict-Enum (3 Outcomes)

```python
class Verdict(str, Enum):
    PASS = "PASS"       # Akzeptiert, Loop terminiert
    REVISE = "REVISE"   # Worker muss retryen mit Feedback
    FAIL = "FAIL"       # Unrecoverable, kein Retry
```

### 4. CriticLoop (Hauptklasse)

```python
loop = CriticLoop(
    max_rounds=3,                          # NIEMALS entfernen!
    worker_timeout=120.0,
    critic_timeout=60.0,
    worker_model="google/gemini-flash-2.0",
    critic_model="anthropic/claude-sonnet-4-5",
)

rubric = EvaluationRubric(
    required_criteria=["x", "y", "z"],
    preferred_criteria=["a", "b"],
    unrecoverable_signals=["contains hardcoded api key"],
)

result = await loop.run(
    task_id="my-task-1",
    task_goal="Write a GreyHack mission runner",
    task_context="Target: bank_server. Tools: nmap, ssh, decipher.",
    rubric=rubric,
    dry_run=False,
)
```

## Termination-Logic (3-Phasen, Priorität)

```
UNRECOVERABLE verdict? → SOFORT stoppen (semantischer Fehler, Retry hilft nicht)
         ↓ no
PASS verdict?         → Akzeptieren, Loop terminiert
         ↓ no
max_rounds hit?       → Best-Output-So-Far zurückgeben (NIEMALS endlos)
```

**Anti-Pattern #13 — Critic-Loop-Runaway:**
- Ohne `max_rounds`-Cap: Agents debattieren ohne zu konvergieren, verbrennen Tokens endlos
- Hard cap (default 3) ist PFLICHT, niemals entfernen

## Cost-Pattern: Cheap-Maker / Capable-Checker

```python
# ✅ RICHTIG: günstiger Worker, fähiger Critic
worker_model = "google/gemini-flash-2.0"    # günstig, ~$0.075/1M tokens
critic_model = "anthropic/claude-sonnet-4-5" # fähig, ~$3/1M tokens

# ❌ FALSCH: beide fähig (40-60% teurer ohne Qualitäts-Gewinn)
worker_model = "anthropic/claude-sonnet-4-5"
critic_model = "anthropic/claude-sonnet-4-5"
```

**Empirisch (Anthropic-Daten):** Cheap-Maker/Capable-Checker spart 40-60% Kosten bei gleicher Qualität auf den meisten Tasks.

## Robust JSON-Parser

Der Critic gibt JSON zurück — aber manchmal mit Markdown-Code-Fences oder Halluzinationen:

```python
def _parse_critic_response(text: str, round_number: int) -> CriticFeedback:
    cleaned = text.strip()
    # Markdown-Fences entfernen
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
    try:
        data = json.loads(cleaned)
        return CriticFeedback(...)
    except (json.JSONDecodeError, ValueError) as e:
        # SAFE DEFAULT: REVISE mit score 0 → Loop läuft weiter
        return CriticFeedback(
            verdict=Verdict.REVISE,
            score=0.0,
            issues=[f"Critic-JSON unparsebar: {e}"],
            ...
        )
```

**Warum SAFE-Default REVISE:** Wenn Critic unparsebar ist, soll der Loop weiterlaufen (nicht silent abbrechen).

## CLI

```bash
# Dry-Run
python3 critic_loop.py --dry-run "Write a GreyHack mission runner"

# Custom Rubric (JSON-File)
python3 critic_loop.py --rubric-file my-rubric.json "..."

# Custom Models
python3 critic_loop.py --worker-model gpt-4o-mini --critic-model claude-opus-4 "..."

# Mehr Rounds
python3 critic_loop.py --max-rounds 5 "..."

# Output in Datei
python3 critic_loop.py --dry-run "..." --output /tmp/loop-result.json
```

## Echte Verifizierung (Dry-Run-Output)

```
$ python3 critic_loop.py --dry-run "Write a GreyHack mission runner for bank hack"
[critic_loop] INFO  LOOP_START  task_id=9414ac14  max_rounds=3  worker=...  critic=...
[critic_loop] INFO  ROUND 1/3
[critic_loop] INFO  VERDICT round=0  verdict=REVISE  score=0.60  issues=1
[critic_loop] INFO  ROUND 2/3
[critic_loop] INFO  VERDICT round=1  verdict=PASS  score=0.92  issues=0
[critic_loop] INFO  PASS  task_id=9414ac14  rounds=2  score=0.92

# → Final: status=passed, rounds=2, history mit 2 feedbacks
```

**Wall-clock:** 2.37s für 2 stub-Rounds (in echt: ~100s × rounds)

## Integration in dein Projekt

```bash
# 1. Skeleton kopieren
cp ~/10-Projekte/10-active/agent-orchestration-patterns/critic_loop.py \
   ~/mein-projekt/orchestration/

# 2. Rubric für deinen Use-Case definieren
cat > my-rubric.json <<EOF
{
  "required_criteria": [
    "Code compiles without errors",
    "All tests pass",
    "No hardcoded credentials"
  ],
  "preferred_criteria": [
    "Inline comments for complex logic"
  ],
  "unrecoverable_signals": [
    "contains hardcoded api key",
    "uses eval() on user input"
  ]
}
EOF

# 3. In deinem Code
from orchestration.critic_loop import CriticLoop, EvaluationRubric
import json

rubric = EvaluationRubric(**json.load(open("my-rubric.json")))
loop = CriticLoop()
result = await loop.run(
    task_id="my-task",
    task_goal="...",
    task_context="...",
    rubric=rubric,
)
```

## Sycophancy-Guard — warum so wichtig

**Das Problem (vor dem Fix):**
```
Worker generiert Code.
Worker-Selbst-Bewertung: "Sieht gut aus, alle Tests passen."
Critic sieht das + Code → "Ja, sieht gut aus, alle Tests passen." (PASS)
→ Schlechter Code wird akzeptiert weil Critic die Worker-Meinung spiegelt
```

**Die Lösung (Sycophancy-Guard):**
```
Worker generiert Code.
Worker.rationale = "" (LEER, IMMER)
Critic sieht nur Code, KEINE Selbst-Bewertung
→ Critic bewertet objektiv gegen Rubric
```

**Implementiert in:**
- `WorkerOutput.rationale` ist Dataclass-Feld, bleibt aber `""` in echten Calls
- `Worker-Code-Pfad` (in `_call_worker()`) setzt rationale explizit auf `""`
- Test verifiziert via `inspect.getsource()` dass rationale NICHT in critic loop runner gelesen wird

## Default-Rubric (GreyHack-Use-Case)

```python
DEFAULT_GREYHACK_RUBRIC = EvaluationRubric(
    required_criteria=[
        "GreyScript Syntax ist valide",
        "Mission-Runner handelt Timeouts graceful",
        "Keine hardcoded Credentials",
        "Verwendet Yuno-style Helper-Functions wo passend",
    ],
    preferred_criteria=[
        "Inline-Kommentare für komplexe Logik",
        "Logging für Debug-Sichtbarkeit",
    ],
    unrecoverable_signals=[
        "contains hardcoded api key",
        "infinite loop with no exit condition",
        "uses eval() or exec() on user input",
    ],
)
```

## Tests (13 Tests, alle grün)

```bash
cd ~/10-Projekte/10-active/agent-orchestration-patterns
python3 -m pytest tests/test_critic_loop.py -v

# → 13 passed in ~7s
```

Coverage-Matrix:
- ✅ JSON-Parser strippt Markdown-Fences
- ✅ JSON-Parser handhabt Plain-JSON
- ✅ JSON-Parser unparseable → SAFE-Default (REVISE)
- ✅ Unrecoverable-Detection matcht Signals
- ✅ Unrecoverable-Detection false bei normalen Issues
- ✅ Dry-Run passes on round 2 (Stub-Simulation)
- ✅ max_rounds-Cap verhindert Runaway
- ✅ Unrecoverable terminiert sofort
- ✅ Sycophancy-Guard: rationale NICHT in Runner-Code
- ✅ max_rounds < 1 raises ValueError
- ✅ Rubric-Defaults sinnvoll
- ✅ CLI dry-run return-zero
- ✅ CLI dry-run exit-code korrekt

## Related

- **Skeleton A** (`master_worker.py`) — für Single-Domain ohne Verification
- **Skeleton B** (`hierarchical_tree.py`) — pro Sub-Domain als Verification-Stage
- `multi-agent-cluster-patterns` Skill — Pattern 10 (MERGER) für Konsolidierung
- `multi-agent-pitfalls-cheatsheet` — Pitfall #13 (Critic-Loop-Runaway)
- `requesting-code-review` Skill — für Pre-Commit-Verification

## Pattern-Variationen

| Variation | Wenn |
|---|---|
| Single-Critic (default) | Standard Verification |
| Multi-Critic (3+ Subagents bewerten) | Hochrisiko-Code, mehrere Perspektiven nötig |
| Critic + Human-in-the-Loop | Wenn Mensch finale Approval braucht (z.B. vor Deploy) |
| Self-Critic (Worker bewertet sich selbst) | Nur für billige Tasks, meistens schlechter als 2-Model |