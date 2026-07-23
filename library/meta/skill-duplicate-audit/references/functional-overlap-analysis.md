# Functional-Overlap Analysis (TF-IDF Cosine Similarity)

**Purpose:** Detect skills with similar intent but different file content — i.e., *functional duplicates* that MD5 hashing will miss.

## When to Use

- After MD5 duplicate-script cleanup, as the second pass
- When two skills share the same trigger keywords but have different SKILL.md texts
- Before merging or archiving any skill category

## Methodology

### 1. Extract Descriptions

```python
import os, re

def desc(path):
    try:
        with open(path) as f:
            for line in f:
                m = re.match(r'^description:\s*(.+)', line, re.I)
                if m: return m.group(1).strip()
    except: pass
    return ""
```

### 2. Tokenize + Compute IDF

```python
import collections, math

def tokens(s):
    s = s.lower()
    return [w for w in re.findall(r'[a-zäöüß]{3,}', s)]

# IDF over all docs
N = len(docs)
df = collections.Counter()
for d in docs.values():
    for w in set(tokens(d)): df[w] += 1
idf = {w: math.log(N/(1+c)) + 1 for w, c in df.items()}
```

### 3. Cosine Similarity per Pair

```python
def tfidf_pair(a, b, idf):
    ta, tb = collections.Counter(tokens(a)), collections.Counter(tokens(b))
    def vec(tc):
        return {w: tf * idf.get(w, 1.0) for w, tf in tc.items()}
    va, vb = vec(ta), vec(tb)
    if not va or not vb: return 0.0
    dot = sum(va[w]*vb.get(w, 0) for w in va)
    na = math.sqrt(sum(v*v for v in va.values()))
    nb = math.sqrt(sum(v*v for v in vb.values()))
    return dot/(na*nb) if na and nb else 0.0
```

### 4. Interpret Results

| Cosine | Meaning | Action |
|---|---|---|
| > 0.60 | Near-identical descriptions | Skills likely do the same thing → merge |
| 0.35–0.60 | Strong overlap, different framing | Investigate for separation clarity |
| 0.15–0.35 | Moderate overlap, adjacent topics | Verify scope boundaries are clear |
| < 0.15 | Low overlap | Safe — different intent |

### 5. Verify with Actual Content

TF-IDF on descriptions alone is a *signal*, not a verdict. Always verify by reading both SKILL.md bodies, checking:
- Do they share the same `When to Use` triggers?
- Do they reference the same external tools?
- Does one skill call the other via `skill_view()`?

## 2026-07-16 Findings (Biene D Schwarm)

**Suspect categories tested:**

| Category | Pairs tested | Overlap hits |
|---|---|---|
| `autonomous-ai-agents/*` | 6 | 4 (0.382–0.622) |
| `devops/*` security | 6 | 3 (0.385–0.525) |
| `orchestration/*` swarm | 8 | 2 (0.129–0.134) |
| `media/*` youtube | 4 | 2 (0.130–0.537) |
| `creative/*` tiktok | 2 | 1 (0.106) |
| `meta/*` skill-quality | 2 | 1 (0.217) |

**Top priority (P0):** autonomous-ai-agents CLI delegation template — 5 skills, 0.382–0.622 cosine. Merge to a single generic skill.
