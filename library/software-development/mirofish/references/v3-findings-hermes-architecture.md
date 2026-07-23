# V3 Run Findings: Hermes-V7 Architecture Simulation

> Source: V3 MiroFish Run `sim_f5b0fdaca08c` (2026-07-12)
> 4 Personas, 60 Rounds, 73 Actions, 46 Posts, Twitter only
> Report: "2026 Multi-Agent系统实战预演：从Hermes-V7事故看生产级Agent编排的真相"

## Personas

| ID | Name | Handle | Role |
|---|---|---|---|
| 0 | Metriken-Disziplin | @metrikendisziplin_736 | Performance Analyst, P50/P95/P99/SLI/SLO |
| 1 | Tool | @tool_990 | Verification & Enforcement Layer, SSPC Schema |
| 2 | Senior SRE (Postmortem-Tante) | @senior_sre_postmortemtante_419 | Production-Ops, 80+ Postmortems, MTTR |
| 3 | OpenAI | @openai_770 | Vendor perspective, Token-Accounting |

## Key Findings

### 1. Five Crash Patterns

The simulation converged on **five crash modes** for Multi-Agent production systems:

| # | Crash | Mechanism | Scale |
|---|---|---|---|
| 1 | **Silent Retry-Loop** | Worker calls Tool, fails, retries without external error | 4.2M tokens burned in 1 lane, no alert |
| 2 | **Context-Bloat-Cascade** | Lane outputs accumulate across hops, exceed context window | 200k tokens after 3 hops → hallucination |
| 3 | **Stale-Checkpoint-Race** | Worker A reads checkpoint, Worker B overwrites it | Lost update, schema version mismatch |
| 4 | **Timeout-Cascade** | Queen orchestrates >50 lanes, becomes bottleneck | P99 120s on Mittelklasse-Stack (3 lanes!) |
| 5 | **Memory-Layer Hot-Key** | Single key without replica, cold-storage eviction | System_prompt loses context, cluster-wide |

### 2. A2A Topology Conclusions

| Topology | Best for | Cost | Weakness |
|---|---|---|---|
| Direct | 2-Agent Conv (Research↔Analysis) | Fast | Unobservable |
| Bus (Pub/Sub) | 1-to-N Notifications | Broadcast easy | Filtering hard |
| Hybrid (Queen + Pub/Sub) | 50+ Agent Scale | Queen bottlenecks >50 lanes | Needs Phasen grouping (max 20/lane) |

**OpenAI prefers Hierarchical** for Token-Accounting per lane. Open-source alternatives (Mistral) lack this.

### 3. Queen Mode Constraints

- Queen is **state-readonly** — receives snapshots without mutating them
- Bottleneck at **>50 lanes** — mitigate via Phasen grouping (max 20 per phase)
- Claim-Work Pattern: Workers pull tasks from queue, Queen doesn't push

### 4. WIP-Limits per Role

| Role | Max Concurrent |
|---|---|
| Worker Pool | 10 |
| Reviewers | 3 |
| Research Lanes | 5 |

### 5. SSPC v7.3 Changelog (Tool Persona's Draft)

The Tool persona (@tool_990) produced a concrete **SSPC Changelog Draft** incorporating Auditkriterien from the Metriken-Disziplin persona:

**Mandatory items:**
- `SSPC-CACHE-SLI-MANDATORY-005` — Dual-measurement-chain, p50/p95/p99/p99.9 over 28d
- `SSPC-IDEMP-COST-RETRIEVE-001` — Cost/Usage endpoint idempotency-key mandatory per run_id
- `SSPC-QUORUM-ACTIVE-ACTIVE-004` — Central-Orchestrator SPOF mitigation for production
- `SSPC-SAMPLE-SIZE-P95-001` / `SSPC-SAMPLE-SIZE-P99-002` — n>=500 / n>=5000 floors
- `SSPC-ENVELOPE-STRICT-001` — StrictModel-typed envelope: schema_name, version, message_id, trace_id, payload_type
- `SSPC-MEMORY-QUOTA-PER-RUN-001` — Per-run quota with guaranteed cleanup
- `SSPC-SPLIT-BRAIN-RUNBOOK-006` — Blast radius includes Cost-per-verified-success, not only latency

### 6. Key Metrics (from Metriken-Disziplin)

| Metric | Value | Source |
|---|---|---|
| Mittelklasse-Stack P50 | 12s | 3-lane benchmark |
| Mittelklasse-Stack P95 | 45s | As above |
| Mittelklasse-Stack P99 | 120s | As above |
| Cost per verified success | $0.05 | Mittelklasse, ~15k tokens/run |
| Cache-Hit-Rate p95 threshold | ≥60% | Production acceptance criterion |
| Error-Budget burn rate alert | >2× for 1h | SLO discipline |
| Lane throughput | 50 lanes/hour | Max before Queen bottleneck |

## Use for Future Seeds

These V3 findings are excellent **seed material** for future brainstorming runs because they contain:
- **Concrete numbers** (4.2M tokens, 120s P99, $0.05) → quantitative arguments
- **Named crashes** → persona debate fuel ("Silent Retry-Loop or Context-Bloat-Cascade?")
- **Code-level items** (SSPC IDs) → technical depth
- **Vendor quotes** → controversy ("OpenAI vs Mistral Token-Accounting")
- **Proven patterns** (Queen state-readonly, Claim-Work, Phasen max 20) → constraint-based discussion

**Seed density lesson:** The V3 seed was ~24k chars (too dense!). Despite requesting 10 personas, only 4 were generated. The run produced **deeper technical content** (code snippets, configs, concrete specs) but **fewer personas** than V1/V2. If you want more personas, keep seeds under 12k chars.