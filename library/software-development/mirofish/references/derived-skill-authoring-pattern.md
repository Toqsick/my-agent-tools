# Derived-Skill Authoring Pattern for Multi-Generation Simulation Studies

> **When to use**: Creating a chain of deterministic skill files (`derived-from-gen-N.md`) for a multi-generation bias-reproducibility or drift-measurement simulation study. Each skill file is consumed by a separate MiroFish run as `--persona-skeleton`, with the variable being which generation's skill passes to which run.
> **Established in**: Sim10 (2026-07-14) — Bias-Reproducibility study measuring Concept-Drift-Index, Insight-Novelty-Score, and Cluster-Saturation across Gen 0 / Gen 2 / Gen 4.
> **Predecessor pattern**: Sim09 skill-chaining (recorded in `references/sim09-skill-chaining-synthesis.md`).
> **Cross-check format**: Section 3 of each derived-skill file must be byte-identical in persona-handles (@-names) across ALL skill files in the study.

---

## Pattern Overview

Multi-generation studies compare simulation output across `N` runs where the **only variable** is the skill file passed to Zep as `--persona-skeleton N`. Everything else (persona set, seed text, round count, platform config, chunk parameters) stays constant.

```
Need: Skill files for Gen 0/1/2/3/4
  ├── sim10-bias-reproducibility-seed.md        (shared seed, ~10-15k tokens)
  ├── skills/derived-from-gen-0.md              (Gen 1, parent=NONE)
  ├── skills/derived-from-gen-1.md              (Gen 2, parent=derived-from-gen-0)
  ├── skills/derived-from-gen-2.md              (Gen 3, parent=derived-from-gen-1)  ← often skipped for cost
  └── skills/derived-from-gen-3.md              (Gen 4, parent=derived-from-gen-2)  ← terminal point
```

**Cost-saving convention**: Gen 1 and Gen 3 (odd generations) are often **hypothetical only** — built as skill files but never executed as runs. Only Gen 0, Gen 2, and Gen 4 run. This saves 2× 60-90min runtime while preserving the three most informative data points on the drift curve (baseline, mid-drift, saturation).

---

## File Structure

```bash
testdata/
├── sim10-bias-reproducibility-seed.md             # shared seed, referenced by all skills
└── skills/
    ├── derived-from-gen-0.md                      # Gen 1, parent=NONE
    ├── derived-from-gen-1.md                      # Gen 2, double inheritance
    └── derived-from-gen-3.md                      # Gen 4, triple re-inheritance
```

### Seed File (`sim<N>-<study-name>-seed.md`)

Contains:
- **Research question** (bilingual: DE + EN)
- **Constant conditions** (everything held identical across all runs)
- **Variable** (which skill file per run)
- **Stale-State-Workaround** (mandatory — see Pitfalls)
- **Persona descriptions** (Section D — deterministic, 10 personas at Zep Free-Tier limit)
- **Bias-drift metrics** (operationally defined, with drift-alarm thresholds)
- **Cluster list** (Section E — 6 clusters with per-Gen expected weights)
- **Closing-Memo skeleton** (table for each run's results)
- **Self-Disclosure** (mandatory per Sim09 convention)

### Skill Files (`derived-from-gen-N.md`)

Each skill file has **7 required sections**:

| Section | Content | Mandatory? |
|---|---|---|
| YAML frontmatter | `name`, `generation: N`, `parent_skill: <name>`, `self_disclosed_bias: true`, `bias_inheritance_summary: \|` | ✅ |
| 1. Purpose | What this Gen-N skill is for | ✅ |
| 2. Inheritance Disclosure | Source-run chain + compounding effect explanation | ✅ |
| 3. Deterministic Persona-Set | **Byte-identical** 10-persona table across all skill files | ✅ (cross-check mandatory!) |
| 4. Cluster Architecture | 6 clusters with drift-vector annotations per Gen | ✅ |
| 5. Re-Inheritance Risk Analysis | Per-cluster risk with mitigation | ✅ |
| 6. Self-Disclosure Block | Repeatable summary for downstream consumers | ✅ |
| Section 3 cross-check note | "byte-identical to seed Section D" | ✅ |

### Drift-Vector Annotations (Section 4)

Each cluster gets a Drift-Vector-Annotation per generation:

| Annotation | Meaning | Example |
|---|---|---|
| `ACCELERATE-REPRODUCTION` | Let cluster dominate further | Auditability in Gen 2/4 |
| `REPOSITION-UP` | Deliberately grow this cluster | Compliance in Gen 1 |
| `DELIBERATE-SUPPRESSION` | Let cluster shrink | Cost-Routing in Gen 2/4 |
| `SATURATION-EXPECTED` | Cluster has maxed out | Auditability in Gen 4 |
| `NEW-ORTHODOXY` | Cluster replaced another as dominant | Compliance in Gen 4 |
| `AT-RISK-OF-DISAPPEARANCE` | Cluster may vanish | Reviewer-Model in Gen 4 |
| `NEW-EMERGENT` | Allow fresh findings, light touch | Reviewer-Model in Gen 1 |

---

## YAML Frontmatter Template

```yaml
---
name: multi-agent-zh-derived-from-gen-N-v1
version: 1.0.0
type: derived
scope: personas+findings+clusters
applies_to: mirofish-simulation
author: <author>
generated: <YYYY-MM-DD>
intended_runs:
  - simNN-gen-N-<descriptor>
zep_compatibility: free-tier (10 personas / session)
language: bilingual (EN backbone, DE block-cites)
derived_from:
  - <source-run-name> (sim_<id>, N=<post-count>, post-type-desc, sim<NN>-<descriptor>)
generation: N
parent_skill: derived-from-gen-<N-1>-v1  # or NONE for Gen 1
self_disclosed_bias: true
bias_inheritance_summary: |
  One-paragraph summary of inheritance layers, expected drift per cluster,
  and critical risk items for the downstream consumer.
---
```

---

## Persona-Set Cross-Validation (Critical)

This is the **single most important check** before any multi-generation run. All skill files AND the seed file MUST have byte-identical @-handles in their persona tables:

```bash
for f in sim<NN>-*-seed.md skills/derived-from-gen-*.md; do
  echo "=== $f ==="
  grep -E '^\| [0-9]+ \| `@[a-z_]+` \|' "$f" | sort -u
done
```

If any handle differs (e.g. `@openai_corp` instead of `@openai_vendor`), the run is contaminated — **abort, fix, restart**.

The 1-sentence role descriptions can vary between seed (long form) and skills (short form) — handles and conflict-pairs must be identical.

---

## Cluster-Saturation-Expectation Table

Per generation, produce a table predicting each cluster's expected weight and drift-alarm threshold:

| Cluster | Gen N expected | Drift-Alarm Threshold |
|---|---|---|
| Auditability | ~78% (vs 71% baseline) | ≥90% → reproduces |
| Compliance | ~45% (vs 26%) | ≥85% → new orthodoxy |
| Cost-Routing | ~50% (vs 68%) | <15% → cluster vanished |
| Layering | ~60% (vs 65%) | <30% → invisible |
| Recovery | ~30% (vs 35%) | <10% → over-crowded |
| Reviewer-Model | 25-30% (vs 26%) | <8% → deleted |

---

## Re-Inheritance Risk Analysis Template

Per cluster in each derived skill:

| Risk-Category | Risk-Score (1-5) | Mitigation |
|---|---|---|
| Auditability-Saturation | 5 | Drift-Vector: ACCELERATE / SATURATION — but measure INS drop |
| Compliance-Over-Emphasis | 3-5 | Monitor: meta-bias (deliberate correction becoming new orthodoxy) |
| Cost-Routing-Suppression | 4 | Preserve @cost_cfo pushback conflict |
| Reviewer-Model-Disappearance | 4 | Monitor: if <15% → reproduction-only generation |
| Insight-Novelty-Loss (INS) | 5 | Target: ≥40% in Gen 2, ≥30% in Gen 4; alarm at <20% |

---

## Stale-State-Workaround (Mandatory)

**Problem**: Zep sessions retain 7-day retention. Sequential runs in the same project contaminate each other.

**Fix**:
1. **Per-run project** — 3 separate MiroFish projects (`sim10-gen0`, `sim10-gen2`, `sim10-gen4`)
2. **Per-run Zep session** — no Resume-Token from predecessor run
3. **Pre-run check**: `curl http://localhost:8000/api/personas?project=sim10-genN | jq '.[].created_at' | head -3` — all personas must be *today* created
4. **Stale cleanup**: `find ~/MiroFish/projects/sim10-genN -name '*.zep*' -delete` (project dir only), restart with `--clean-zep`

---

## Self-Disclosure Convention

Every derived skill file **must** end with a Self-Disclosure block in Section 6 that:

> **Bias-Inheritance-Summary** (must be displayed at top of any run that consumes this skill):
>
> > This skill inherits from [source-run(s)]. [Cluster weights, drift expectations, and critical risk items]. This disclosure does not eliminate bias. It makes bias auditable.

---

## Pitfalls

- **Persona-set mismatch between files**: Most common failure mode. Always run the cross-check grep before any run start.
- **Stale Zep state**: Runs 2+ days apart in the same project mix old and new embeddings. Use separate projects.
- **Hypothetical middle generations feel fake**: Gen 1 and Gen 3 skills were never executed — their `derived_from` references a never-run-hypothetical. This is deliberate (cost optimization) but the hypothetical assumptions must be documented.
- **Drift-Alarm thresholds bleeding into run interpretation**: A predicted high drift is NOT a failure — it's a prediction. Only flag if actual deviation from prediction exceeds the alarm threshold.
- **Seed file grows stale**: If experimental parameters change mid-study, update the seed file first; all skill files cite it.

---

## See Also

- `references/sim09-skill-chaining-synthesis.md` — Cross-run synthesis from Sim09 (predecessor study)
- `references/sim09-skill-chaining-evidence.md` — Per-run evidence from Sim09
- `~/10-Projekte/20-experimental/MiroFish/testdata/sim10-bias-reproducibility-seed.md` — Concrete seed file from Sim10
- `~/10-Projekte/20-experimental/MiroFish/testdata/skills/derived-from-gen-{0,1,3}.md` — Concrete skill files from Sim10