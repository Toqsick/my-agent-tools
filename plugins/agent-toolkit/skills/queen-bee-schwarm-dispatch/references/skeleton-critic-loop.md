# Skeleton C — Critic-Loop / Reflexion (Maker-Checker)

**Pattern:** Worker generiert Output; Critic evaluiert gegen Rubrik; Loop terminiert auf PASS oder `max_rounds` (Hard-Cap). Maker verwendet Cheap-Model; Checker verwendet Capable-Model — 40-60% Cost-Reduktion vs. Same-Model-Pair.

**Wichtigster Anti-Pattern (Sycophancy Guard):** Der Critic bekommt NIEMALS die `rationale` des Workers (Worker's eigene Selbst-Einschätzung). Sycophancy-Effekt: Critic spiegelt Worker-Bewertung statt unabhängig zu prüfen.

**Quelle:** Perplexity Deep Research 2026-07-15 (Anthropic Engineering Post + Digital Applied Production Audits).

```python
"""
critic_loop.py  —  Production Critic-Loop (Maker-Checker / Reflexion).

Architecture:
  Worker   (cheap model: Haiku / Flash)    -> generates output
  Critic   (capable model: Sonnet / Opus)  -> evaluates against rubric
  Termination: PASS verdict OR max_rounds (hard cap — never omit!)

Failure mode prevented:
  "Critic-loop runaway" — agents debate without converging.
  Fix: max_rounds=3 + exit_condition checklist.

Sycophancy guard:
  Critic receives worker output WITHOUT seeing worker's self-evaluation.
  Prevents the critic from rubber-stamping the worker's own verdict.

Drop-in for:
  - GreyHack mission script generation + automated test runner
  - TikTok hook generation + engagement-score critic
  - Code generation + test-suite critic
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".hermes" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("critic_loop")


# ── Verdict types ─────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    PASS    = "PASS"      # accepted — loop terminates
    REVISE  = "REVISE"    # retry with critic feedback
    FAIL    = "FAIL"      # unrecoverable, stop


@dataclass
class WorkerOutput:
    content: str
    rationale: str         # NOT shown to critic (Sycophancy Guard!)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticFeedback:
    verdict: Verdict
    score: float           # 0.0–1.0
    issues: list[str]
    passed_criteria: list[str]
    round_number: int


@dataclass
class LoopResult:
    task_id: str
    final_status: str      # "passed" | "max_rounds_hit" | "unrecoverable"
    final_output: WorkerOutput | None
    rounds: int
    total_wall_clock: float
    history: list[CriticFeedback]
    tokens_worker: int = 0
    tokens_critic: int = 0


# ── Rubric ────────────────────────────────────────────────────────────────────

@dataclass
class EvaluationRubric:
    """Define PER TASK — not globally. Vague rubrics -> sycophancy -> early PASS = bad."""
    required_criteria: list[str]
    preferred_criteria: list[str]
    max_score_for_revise: float = 0.79
    unrecoverable_signals: list[str] = field(default_factory=list)


# ── Stubs: replace with real model calls ─────────────────────────────────────

async def _call_worker(
    task_goal: str,
    task_context: str,
    previous_feedback: CriticFeedback | None,
    worker_model: str = "google/gemini-flash-2.0",
) -> WorkerOutput:
    """
    TODO: Replace with real worker call.
    For Hermes delegate_task using cheap model:
        raw = await loop.run_in_executor(None, lambda: delegate_task(
            goal=task_goal, context=_build_context(task_context, previous_feedback),
            toolsets=["terminal", "file"], max_iterations=15,
        ))
    For direct API: use Haiku/Flash model.
    """
    feedback_hint = ""
    if previous_feedback:
        feedback_hint = f"\nPrevious issues to fix: {'; '.join(previous_feedback.issues)}"
    await asyncio.sleep(1.0)
    return WorkerOutput(
        content=f"[stub worker output for: {task_goal[:40]}]{feedback_hint}",
        rationale="stub rationale — NOT shown to critic!",
    )


async def _call_critic(
    task_goal: str,
    worker_output: WorkerOutput,
    rubric: EvaluationRubric,
    round_number: int,
    critic_model: str = "anthropic/claude-sonnet-4-5",
) -> CriticFeedback:
    """
    TODO: Replace with real critic call.

    CRITICAL: Do NOT pass worker_output.rationale to the critic.
    Showing it causes sycophancy — the critic mirrors the worker's assessment.

    Prompt structure that works in production:
        system = "You are a strict quality evaluator. Be specific about failures."
        user = f'''
        Task goal: {task_goal}
        Required criteria (ALL must pass): {rubric.required_criteria}
        Output: {worker_output.content}
        Respond JSON: {{"verdict": "PASS"/"REVISE"/"FAIL", "score": 0.0-1.0,
                        "issues": [...], "passed_criteria": [...]}}
        '''
    """
    await asyncio.sleep(0.5)
    verdict = Verdict.REVISE if round_number == 0 else Verdict.PASS
    return CriticFeedback(
        verdict=verdict,
        score=0.6 if round_number == 0 else 0.92,
        issues=["[stub] improve specificity in section 2"] if round_number == 0 else [],
        passed_criteria=rubric.required_criteria if round_number > 0 else [],
        round_number=round_number,
    )


# ── Termination logic ─────────────────────────────────────────────────────────

def _is_unrecoverable(feedback: CriticFeedback, rubric: EvaluationRubric) -> bool:
    """Semantic failures: retrying cannot fix them."""
    for issue in feedback.issues:
        for signal in rubric.unrecoverable_signals:
            if signal.lower() in issue.lower():
                return True
    return False


# ── Critic-Loop runner ────────────────────────────────────────────────────────

class CriticLoop:
    """
    Production Critic-Loop with hard max_rounds cap.

    Three-phase termination (priority order):
      1. UNRECOVERABLE -> stop (semantic failure)
      2. PASS           -> accept output
      3. max_rounds hit -> return best output (never run forever)
    """

    def __init__(self, max_rounds: int = 3, worker_timeout: float = 120.0, critic_timeout: float = 60.0):
        self.max_rounds = max_rounds          # NEVER remove this cap
        self._worker_timeout = worker_timeout
        self._critic_timeout = critic_timeout

    async def run(self, task_id: str, task_goal: str, task_context: str, rubric: EvaluationRubric) -> LoopResult:
        t0 = time.monotonic()
        history: list[CriticFeedback] = []
        best_output: WorkerOutput | None = None
        best_score: float = -1.0
        previous_feedback: CriticFeedback | None = None
        tokens_worker = 0
        tokens_critic = 0

        log.info("LOOP_START  task_id=%s  max_rounds=%d  goal='%s'", task_id, self.max_rounds, task_goal[:50])

        for round_num in range(self.max_rounds):
            log.info("ROUND %d/%d  task_id=%s", round_num + 1, self.max_rounds, task_id)

            # Worker turn
            try:
                worker_output = await asyncio.wait_for(
                    _call_worker(task_goal, task_context, previous_feedback),
                    timeout=self._worker_timeout,
                )
            except asyncio.TimeoutError:
                log.error("WORKER TIMEOUT  round=%d  task_id=%s", round_num, task_id)
                break

            # Critic turn (does NOT see worker.rationale — Sycophancy Guard!)
            try:
                feedback = await asyncio.wait_for(
                    _call_critic(task_goal, worker_output, rubric, round_num),
                    timeout=self._critic_timeout,
                )
            except asyncio.TimeoutError:
                log.error("CRITIC TIMEOUT  round=%d  task_id=%s", round_num, task_id)
                break

            history.append(feedback)
            previous_feedback = feedback

            log.info("VERDICT round=%d  verdict=%s  score=%.2f  issues=%d",
                     round_num, feedback.verdict, feedback.score, len(feedback.issues))

            # Track best output
            if feedback.score > best_score:
                best_score = feedback.score
                best_output = worker_output

            # Termination checks
            if _is_unrecoverable(feedback, rubric):
                log.error("UNRECOVERABLE  task_id=%s  round=%d", task_id, round_num)
                return LoopResult(
                    task_id=task_id, final_status="unrecoverable",
                    final_output=None, rounds=round_num + 1,
                    total_wall_clock=time.monotonic() - t0,
                    history=history, tokens_worker=tokens_worker, tokens_critic=tokens_critic,
                )

            if feedback.verdict == Verdict.PASS:
                log.info("PASS  task_id=%s  rounds=%d  score=%.2f", task_id, round_num + 1, feedback.score)
                return LoopResult(
                    task_id=task_id, final_status="passed",
                    final_output=worker_output, rounds=round_num + 1,
                    total_wall_clock=time.monotonic() - t0,
                    history=history, tokens_worker=tokens_worker, tokens_critic=tokens_critic,
                )

            # REVISE -> loop continues

        # max_rounds hit
        log.warning("MAX_ROUNDS  task_id=%s  returning best_score=%.2f", task_id, best_score)
        return LoopResult(
            task_id=task_id, final_status="max_rounds_hit",
            final_output=best_output, rounds=self.max_rounds,
            total_wall_clock=time.monotonic() - t0,
            history=history, tokens_worker=tokens_worker, tokens_critic=tokens_critic,
        )


async def main():
    loop = CriticLoop(max_rounds=3)
    rubric = EvaluationRubric(
        required_criteria=[
            "GreyScript syntax is valid",
            "Mission runner handles timeout gracefully",
            "No hardcoded credentials",
        ],
        preferred_criteria=[
            "Uses Yuno-style helper functions",
            "Includes inline comments",
        ],
        unrecoverable_signals=[
            "contains hardcoded API key",
            "infinite loop with no exit condition",
        ],
    )

    result = await loop.run(
        task_id=uuid.uuid4().hex[:8],
        task_goal="Write a GreyHack GreyScript mission runner that completes 'bank hack' missions autonomously",
        task_context="Target: bank_server.  Available tools: nmap, ssh, decipher.  Max execution time: 90s.",
        rubric=rubric,
    )

    print(f"\nStatus:  {result.final_status}")
    print(f"Rounds:  {result.rounds}")
    print(f"Elapsed: {result.total_wall_clock:.1f}s")
    if result.final_output:
        print(f"Output:  {result.final_output.content[:200]}")
    print(f"History: {json.dumps([{'round': f.round_number, 'verdict': f.verdict, 'score': f.score} for f in result.history], indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Hermes Config für dieses Skeleton

```yaml
# ~/.hermes/config.yaml
# Critic-Loop braucht keine delegation-Config (kein Subagent-Dispatch)
# Stattdessen: Worker/Critic per API-Direct-Call (Cheap + Capable models)
# Sycophancy Guard ist eine Prompt-Regel, keine Config
```