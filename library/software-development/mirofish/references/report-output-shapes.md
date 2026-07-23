# MiroFish Report Output Shapes

MiroFish generates reports in Chinese via the LLM's default language. Two distinct output shapes have been observed empirically from real runs. These are NOT deterministic — the LLM's generation path diverges based on early random seed in persona initialization — but they reliably recur.

---

## Shape 1: "Future Prediction" (3-Section Structure)

**Typical length:** 25-35k characters (Chinese), 400-500 lines Markdown

**Title pattern:** `未来预测报告` (Future Prediction Report)

**Section structure:**

```
## 1. 预测场景与核心发现
  (Prediction Scenarios & Core Findings)
  - 6-8 numbered "core findings" with citations from persona posts
  - Each finding: statement + supporting quote + analysis

## 2. 人群行为预测分析
  (Crowd Behavior Prediction Analysis)
  - Social topology analysis (opinion leaders, blockers, bridgers, outliers)
  - Persona alliance patterns and conflict dynamics
  - Temporal evolution: fragmentation → convergence → stratification

## 3. 趋势展望与风险提示
  (Trend Outlook & Risk Warnings)
  - Turning point signals with concrete evidence
  - Regulatory domino predictions
  - "Dark debts" (structural risks no one talks about)
  - Observable early-warning signals (5-item checklist)
```

**Strengths:** Excels at surfacing unspoken risks, structural audit gaps, and actionable turning-point indicators. The persona analysis section (2) is uniquely valuable for understanding HOW the ecosystem will evolve, not just WHAT will happen.

---

## Shape 2: "Structured Analysis" (4-Chapter Structure)

**Typical length:** 35-42k characters (Chinese), 450-500 lines Markdown

**Title pattern:** `多智能体生态2026-2028：` + subtopic (Layering, Control Plane, Auditability Paradigm)

**Section structure:**

```
## 1. 框架生态的层化
  (Framework Ecosystem Layering)
  - Zero-sum narrative → layered division of labor
  - LangGraph: control plane bearer
  - AutoGen: dialog layer sub-component
  - CrewAI: sandbox (retained, demoted)
  - 4 driving signals for the shift

## 2. 成本即架构
  (Cost is Architecture)
  - Three-Tier Model Routing as highest-leverage move
  - C0-C4 cost class taxonomy
  - 87% cost reduction at 97.7% accuracy retention
  - Cost_per_Verified_Success formula
  - Self-hosting economics (39 USD/mo vs 60-180 USD/mo)

## 3. 可审计性范式确立
  (Auditability Paradigm)
  - Queen-Worker-Gate as "only sane option"
  - 3 convergence lines: byte-identical replay, gate-before-commit, structured contracts
  - 4-layer instantiation: Planning/Execution/Review/Release
  - Defense-in-Depth Layer 4 (tamper-evident trace IDs at Gate)
  - Solo-Dev reservation (fair boundary)

## 4. 七类Persona的站位博弈与涌现冲突
  (7 Persona Position Gambits & Emergent Conflicts)
  - 5 major conflict matrices
  - 2 strong alliances (MCP + Maintainer, Cost-Optimizer + Enterprise-Architekt)
  - Emergent conclusion: "Framework-Winner identity disappears"
```

**Strengths:** Excels at mapping positions, trade-offs, and architectural consensus. The persona conflict matrix (4) is uniquely valuable for understanding which groups are aligned vs opposed.

---

## When Each Shape Appears

| Condition | Likely Shape |
|---|---|
| First run on a broad topic (general whitepaper) | Future Prediction |
| Second run on same topic, different seed/emphasis | Structured Analysis |
| Seed focused on "risks" or "security" | Future Prediction |
| Seed focused on "architecture" or "frameworks" | Structured Analysis |
| Shorter simulation (< 30 rounds, fewer actions) | Future Prediction |
| Longer simulation (> 40 rounds, 100+ actions) | Structured Analysis |

The heuristic: **the LLM optimizes for breadth first (Future Prediction shape), then depth on re-run (Structured Analysis shape).** Running two simulations and getting one of each is the most informative outcome.

---

## How to Read a Chinese Report Without Chinese

Since the LLM reports are in Chinese, use this reading strategy:

1. **Read the title** — identifies the shape
2. **Read the section headers** (they're usually bilingual or contain enough English technical terms) — identifies the structure
3. **Extract quoted English text** — persona quotes are often preserved in their original language (English or German)
4. **Extract numbers** — key metrics (87%, 97.7%, $39, $0.08/Run, 56.6%) are language-agnostic
5. **Write a German summary** — this forces you to synthesize rather than translate

The Chinese text itself is well-structured Markdown with consistent formatting, so even without reading every character, the structural signals (blockquotes, tables, numbered lists, bold terms) convey the argument flow.