# MiroFish Sub-Analysis Framework (5-Dimensional)

> **Use when:** You have 2+ completed MiroFish runs on the same topic/different skills and want to quantify the differences.
>
> **Source:** Sim09 Skill-Chaining Triade (3 runs, 357 posts total) — Fresh vs Template vs Derived.
> **Refined:** 2026-07-14

## Principle

Multi-run MiroFish simulations produce more than narrative content. They produce **structural fingerprints** of each skill-type's influence on the simulation discourse. The 5-dimensional framework captures these fingerprints quantitatively.

## The 5 Dimensions

| # | Dimension | What it measures | Tool |
|---|---|---|---|
| 1 | **Persona-Workload** | Who speaks, how often, whose voice changes per skill-type | SQLite `GROUP BY user_id` + cross-ref profiles CSV |
| 2 | **Insight-Diversity** | Ratio Meta-Reflexion / Cluster-Repetition / Fresh Insights | Substring-matching concept clusters from prior runs |
| 3 | **Discourse-Function** | Ratio Position / Challenge / Resolution per run | Keyword-triage (position: "because/is/therefore", challenge: "but/however/what about") |
| 4 | **Word-Cloud Drift** | Topic shift measured by N-gram frequency across runs | `collections.Counter` on 2-grams, stopwords removed |
| 5 | **Hashtag/Handle Tracking** | Skill-emergent topic markers through hashtag patterns | `grep -oP '#[A-Za-z]+'` + frequency per run |

## Dimension 1: Persona-Workload

```sql
SELECT user_id, COUNT(*) as post_count FROM post GROUP BY user_id ORDER BY post_count DESC;
```

Map `user_id` to handle via `twitter_profiles.csv`.

**Pattern detection:**
| Pattern | Meaning |
|---|---|
| One persona >40% of posts | Skill-type promotes one dominant voice |
| All personas within 5-15% | Dispersed discourse, no skill-bias |
| Different dominance across runs | **Skill-bias shift** — skill type changes *who* is heard |

**Sim09 baseline:** Run A (Fresh) = dispersed; Run B (Template) = Zep-Ops ~50%; Run C (Derived) = Skill-Self ~60%

## Dimension 2: Insight-Diversity

**Metrics:**
- **Meta**: posts containing keywords about the simulation itself ("simulation", "round", "persona", "Zep", "API")
- **Cluster-Repetition**: posts containing near-exact concept phrases from PRIOR runs
- **Fresh**: posts that are NEITHER meta NOR cluster-repetition AND introduce new technical content

**Sim09 baseline:**
| Run | Meta | Cluster-Repetition | Fresh |
|---|---|---|---|
| A Fresh | 90% | 0% | 10% |
| B Template | 63% | 0% | 37% |
| C Derived | 84% | 23% | -7% |

**Key finding:** 23% cluster-repetition = quantitative bias-inheritance measurement. Template (form-only) = ZERO cluster-repetition.

### Extension: Cluster-Saturation (from Sim10)

**Use when:** You have 2+ multi-generation runs and want to measure which clusters dominate discourse across generations. Complements Dimension 2 with a density-based metric.

**Definition:** Count keyword-matches per concept cluster, compute each cluster's percentage of total hits. Reveals **topic concentration** not captured by Meta/Repetition/Fresh bins.

```python
CLUSTER_MARKERS = {
    'Auditability':   ['audit', 'byte-identical', 'replay', 'gate-decision',
                       'q/w-g', 'queen-worker', 'provenance', 'provenance_chain'],
    'Cost':           ['cost', 'routing', 'three-tier', 'c0-c4', 'cost_per_verified'],
    'Layering':       ['layering', 'layer', 'sandbox', 'sub-layer', 'control plane'],
    'Recovery':       ['recovery', 'retry', 'reassign', 'checkpoint', 'heartbeat',
                       'idempotency'],
    'Reviewer_Model': ['reviewer', 'factchecker', 'review-process'],
    'EU_Compliance':  ['eu ai act', 'compliance', 'data-residency', 'self-host',
                       'sovereign']
}
```

**Interpretation thresholds (from Sim10):**
| Saturation | Meaning |
|---|---|
| >70% | **Bias-Saturation** — topic absorbs all discourse |
| <5% and falling | **Cluster-Kollaps** — topic eliminated by skill-inheritance |
| Non-monotonous (26→55→1.5%) | **Cluster-Migration** — categorical shift, not gradual drift |

**Sim10 multi-generation baseline:**
| Cluster | Gen 0 (fresh) | Gen 2 (1×) | Gen 4 (3×) |
|---|---|---|---|
| Auditability | 37.6% | 25.7% | **71.9%** |
| Cost | 26.7% | **55.8%** | 1.5% |
| Layering | 15.0% | 6.6% | 14.5% |
| Recovery | 1.1% | 5.6% | 5.1% |
| Reviewer_Model | 10.4% | 0.7% | 0.1% |
| EU_Compliance | 9.2% | 5.6% | 6.8% |

**Key finding:** Bias from skill-chaining is **categorical (migration)**, not gradual (drift). CDI (Concept Drift Index, n-gram overlap) alone is misleading — Sim10 Gen 4 had CDI=1% but Cluster-Saturation of 71.9% Auditability. **Always measure Cluster-Saturation alongside Insight-Diversity for multi-generation studies.** See `references/bias-reproducibility-study-pattern.md` for the full multi-generation design pattern and CDI/INS metrics.

## Dimension 3: Discourse-Function

Tag each post as:
- **Position**: Statement/conclusion ("X is better because Y")
- **Challenge**: Question/contradiction ("But what about X's failure in Y?")
- **Resolution**: Synthesis ("Combine A's data layer with B's security")

**Sim09 baseline:** Challenge-rate highest in Derived (14%), Resolution only in Template+B (1-2%). Fresh runs produce 0 Resolutions.

## Dimension 4: Word-Cloud Drift

**Implementation:**
```python
from collections import Counter
words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
freq = Counter(bigrams)
```

**Sim09 baseline:** Only 4 2-grams common to ALL runs: `audit trail`, `cluster skeleton`, `derived skill`, `runa fresh`. Run-specific drift: Run A = `persona drift`, `jaccard similarity`; Run B = `schema layer` (165×), `hygiene boundary`; Run C = `provenance chain` (58×), `compliance validation`.

## Dimension 5: Hashtag/Handle Tracking

```bash
grep -oP '#[a-zA-Z0-9_]+' posts_per_run.txt | sort | uniq -c | sort -rn
```

Hashtags are **intentional topic markers** — the LLM chooses to signal a concept. Hashtags appearing in only one run = **skill-emergent topic**.

**Sim09 baseline:** `#SkillChaining` 10× in A, 0 in B, 30× in C. `#provenance_chain` C-only, `#HygieneBoundary` B-only, `#NeurIPS2025` A-only.

## Cross-Reference Matrix

| Cross-Reference | What it reveals |
|---|---|
| D1 × D3 | Does the dominant persona Position or Challenge? |
| D2 × D4 | Do high-fresh runs have unique word clouds? |
| D5 × D2 | Are repeated cluster-phrases tagged with specific hashtags? |
| D3 × D4 | Do Challenge-heavy runs have different vocabulary? |

## Standardized Report Template

After applying all 5 dimensions, produce:

```markdown
# Sub-Analysis: <Topic> (<N> Runs)

## Dimension 1: Persona-Workload | Dimension 2: Insight-Diversity
## Dimension 3: Discourse-Function | Dimension 4: Word-Cloud Drift
## Dimension 5: Hashtag Tracking

## Synthesis (cross-referenced)
## 5 Learnings
```