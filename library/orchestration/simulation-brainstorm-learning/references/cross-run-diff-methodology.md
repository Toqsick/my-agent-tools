# Cross-Run Diff Methodik

> **Herkunft:** Sim09↔Sim10 Lessons-Diff (2026-07-14, 815 Posts, 6 Runs)
> **Verwendet in:** SIM09-SIM10-LESSONS-DIFF.md
> **Kern-Erkenntnis:** Zwei Triaden mit gleichem Persona-Set und gleicher Methodik, aber verschiedenen Forschungsfragen, produzieren dramatisch verschiedene Diskurs-Formen und Cluster-Drift-Pattern. Die Diff-Methodik ist generalisierbar als Skill-Chaining-Test-Framework.

## Wann Cross-Run Diff Methodik anwenden

- **Zwei+ Triaden** (6+ Runs) auf demselben Simulations-Setup mit **verschiedenen Forschungsfragen**
- User fragt nach **"diff"** oder **"vergleich der triaden"**
- Du willst wissen: **welche Befunde sind robust (über Triaden hinweg stabil) und welche sind setupspezifisch?**
- Nach Abschluss einer zweiten Triade — die erste Triade ist die **Baseline**

## Methodik: 3-Phasen-Prozess

### Phase 1: Jede Triade einzeln auswerten (kann entfallen wenn schon geschehen)

Führe für jede Triade die 5-dimensionale quantitative Analyse aus der Haupt-SKILL.md durch:
1. Persona-Workload
2. Insight-Diversity
3. Discourse-Function
4. Word-Cloud Drift
5. Hashtag Tracking

### Phase 2: Cross-Comparison-Tabelle erstellen

#### Schritt A: Cluster-Hit-Density-Vergleich

Erstelle eine Tabelle: **Cluster × Triade-Mittelwert × Δ**

| Cluster | Triade1-Mittel | Triade2-Mittel | Δ | Pattern |
|---|---|---|---|---|
| Auditability | 47% | 45% | -2pp | ähnlich |
| Cost | 12% | 28% | **+16pp** | verschieden |
| ... | ... | ... | ... | ... |

#### Schritt B: Cluster-Drift-Pattern-Vergleich

Vergleiche **nicht nur die Mittelwerte, sondern die Drift-Richtung innerhalb jeder Triade**:

| Cluster | Triade1-Pattern | Triade2-Pattern | Konsistenz? |
|---|---|---|---|
| Auditability | Monoton wachsend (38→49→54%) | U-Kurve (38→26→72%) | **INKONSISTENT** |
| Cost | V-Kurve (16→8→12%) | Peak-fall (27→56→1.5%) | **UMGEKEHRT** |
| Reviewer_Model | Monoton fallend (7→4→0.7%) | Schneller Fall (10→0.1%) | **KONSISTENT** |

#### Schritt C: Wortwolken-Diff

Führe gemeinsame Wortwolken-Analyse über den gesamten Text beider Triaden:

```python
import json, re
from collections import Counter

def text_from_runs(paths):
    text = []
    for p in paths:
        d = json.load(open(p))
        items = d.get('twitter',{}).get('posts',[]) + d.get('reddit',{}).get('posts',[])
        text.extend(it.get('content','') for it in items)
    return ' '.join(text).lower()

def get_two_grams(text, n=50):
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text_clean.split()
    stop = {'the','a','is','this','that','and','of','to','in','for','with','on','by','are','be','as','at','from','or','an'}
    filtered = [w for w in words if w not in stop and len(w) > 3]
    return Counter(' '.join(filtered[i:i+2]) for i in range(len(filtered)-1)).most_common(n)

triade1_text = text_from_runs(triade1_paths)
triade2_text = text_from_runs(triade2_paths)

t1_2g = dict(get_two_grams(triade1_text, 100))
t2_2g = dict(get_two_grams(triade2_text, 100))

t1_only = set(t1_2g.keys()) - set(t2_2g.keys())
t2_only = set(t2_2g.keys()) - set(t1_2g.keys())
common = set(t1_2g.keys()) & set(t2_2g.keys())
```

Interpretation:
- **Niedriger Common-Anteil** (< 20%) → Triaden sind thematisch fast komplett verschieden → **Forschungsfrage dominiert den Diskurs**
- **Hoher Common-Anteil** (> 50%) → Persona-Set dominiert, Forschungsfrage hat wenig Einfluss
- **Sim09↔Sim10 Benchmark:** 16% common (84+84+16=184 unique 2-grams)

### Phase 3: Kausale Erklärungen + Robuste Befunde finden

#### Schritt A: Identifiziere INVARIANTE Befunde (in beiden Triaden gleich)

**Definition:** Ein Befund ist invariant, wenn er in BEIDEN Triaden in die gleiche Richtung zeigt (auch wenn der Wert variiert).

**Beispiel aus Sim09↔Sim10:** Reviewer_Model kollabiert in beiden Triaden (7→0.7% und 10→0.1%) → **INVARIANT → kann als Gesetz formuliert werden**

#### Schritt B: Identifiziere SETUP-ABHÄNGIGE Befunde

**Definition:** Ein Befund ist setup-abhängig, wenn die Richtung zwischen Triaden variiert.

**Beispiel:** Auditability wächst monoton in Sim09, zeigt U-Kurve in Sim10 → **SETUP-ABHÄNGIG → darf NICHT als Gesetz formuliert werden**

#### Schritt C: Schreibe kausale Erklärung für jeden signifikanten Diff

Für jeden Cluster mit Δ > 10pp oder Pattern-Inkonsistenz schreibe:

```markdown
### Warum ist [Cluster] in [Triade2] [Metrik]-fach größer/kleiner?

**[Triade1] Setup**: [Kurze Beschreibung der Forschungsfrage]
**[Triade2] Setup**: [Kurze Beschreibung der Forschungsfrage]

→ **[Kausale Erklärung]**: [Warum die Forschungsfrage den Unterschied erklärt]
```

**Sim09↔Sim10 Beispiele:**

```
### Warum ist Cost in Sim10 2.3x größer?
Sim09 Setup: "Compare skill-chaining against alternatives"
Sim10 Setup: "Quantify bias drift rate per generation"
→ Sim10 triggert Cost-Diskussion methodisch (weil mehr Re-Inheritance = mehr Setup-Aufwand + mehr Maintenance)
```

### Schritt D: Extrahiere Meta-Learnings aus dem Diff

Frage für jeden signifikanten Diff:
1. **Was sagt dieser Diff über das zugrundeliegende System?**
2. **Welche Design-Implikation hat er für Hermes V7 / das Zielsystem?**
3. **Ist der Befund robust genug, um als Regel zu gelten?**

## Sim09↔Sim10 Baselines (Referenz für zukünftige Cross-Run-Vergleiche)

### Baseline A: Cluster-Hit-Density (Sim09 vs Sim10)

| Cluster | Sim09-Mittel | Sim10-Mittel | Δ |
|---|---|---|---|
| Auditability | 47% | 45% | -2pp |
| Cost | 12% | 28% | +16pp |
| Layering | 15% | 12% | -3pp |
| EU_Compliance | 19% | 7% | -12pp |
| Reviewer_Model | 4% | 4% | ≈0 |
| Recovery | 3% | 4% | +1pp |

### Baseline B: Wortwolken-Exklusivität

- **Common 2-grams**: 16 von 200 (8%)
- **Sim09-only**: 84 — technisch, Zep-API-spezifisch (`admission boundary`, `audit hook`)
- **Sim10-only**: 84 — methodologisch, bilingual (`bias reproducibility`, `closing memo`, `cluster centroid`)
- **Schluss:** Forschungsfrage prägt Diskurs-Form fundamental

### Baseline C: Invariante vs Setup-abhängige Befunde

| Befund | Sim09 | Sim10 | Robust? |
|---|---|---|---|
| Reviewer_Model kollabiert | ja (7→0.7%) | ja (10→0.1%) | **INVARIANT** |
| Auditability wächst | monoton (38→54%) | U-Kurve (38→72%) | setup-abhängig |
| Cost-Verhalten | stabil-niedrig | Peak-Gen-2 → Kollaps | setup-abhängig |
| EU_Compliance | steigt mit Skill | fällt mit Skill | setup-abhängig |

## Lessons-to-Specs Conversion (Was kommt nach dem Diff?)

Nachdem du die Diffs analysiert und Meta-Learnings extrahiert hast, konvertiere **die robusten Befunde** in **konkrete Implementation-Specs**. Die Tier-1-Lessons (invariante, implementierbare Befunde) haben den höchsten Wert:

1. **Tier 1 (Sofort):** Safety-kritische, implementierbare Befunde
2. **Tier 2 (Bald):** Operativ wichtige, aber nicht kritische
3. **Tier 3 (Später):** Architektur-Insights, nice-to-have

Jede Spec enthält:
- **Source** (welche Triade, welcher Befund)
- **Why** (kausale Erklärung)
- **Implementation** (YAML-Spec, Python-Pseudo-Code)
- **Validation** (wie testen, dass die Spec greift)

**Siehe auch:** Die 15 Lessons aus Sim09+Sim10 sind in `SIM09-SIM10-LESSONS-DIFF.md` unter `~/10-Projekte/20-experimental/MiroFish/` dokumentiert. Die 5 Tier-1-Lessons wurden bereits parallel zu Specs ausgearbeitet und liegen unter `~/docs/system/skill-system-specs/`.