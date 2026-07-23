# Bias-Reproducibility Study Pattern (Multi-Generation)

> **Purpose:** Archetype for multi-generation bias-inheritance studies beyond the A/B/C triade. Covers N-generation chaining (Gen 0 → Gen 2 → Gen 4 skipping intermediate steps), CDI/INS/Cluster-Saturation metrics, and key findings from Sim10.
> **Referenziert von:** `mirofish/skill.md` Step 5g
> **Erstbefüllt:** 2026-07-14, aus Sim10 (3 Runs, 458 Posts)

---

## 1. Wann dieses Archetype verwenden

- Die Forschungsfrage lautet: **Wie kumuliert Bias über N Skill-Generationen?**
- Du hast bereits eine Baseline (Gen 0, Fresh, kein Skill) und willst nach 1×, 3×, N× Re-Inheritance messen
- Die Frage geht über einen einfachen A/B/C-Vergleich hinaus (für A/B/C → `references/skill-chaining-architecture.md`)

**Nicht verwenden wenn:**
- Einfacher Fresh-vs-Template-vs-Derived Vergleich → benutze Skill-Chaining Archetype
- Nur eine Simulation ohne Bias-Frage → Standard Seed aus Skill Step 1

---

## 2. Multi-Generation Design

### Struktur (Sim10 als Template)

```
Seed (biasrepro-seed.md)
│
├── Gen 0 (Fresh, kein Skill) — Baseline
│   ├── Project: proj_<topic>-gen0
│   ├── Skill: none
│   ├── Erwartet: breite Cluster-Verteilung
│   └── Ergebnisse: 167 Posts (Sim10)
│
├── Gen 1 (Skill derived from Gen 0) — intermediate, wird NUR für Gen 2 Skill-Gen genutzt
│   └── Skill: derived-from-gen-0.md (WIRD NICHT ALS EIGENER RUN AUSGEFÜHRT)
│
├── Gen 2 (1× Re-Inheritance) — erster gemessener Schritt
│   ├── Project: proj_<topic>-gen2
│   ├── Skill: derived-from-gen-1.md (enthält Gen 0 Findings)
│   ├── Erwartet: moderate Cluster-Konzentration, CDI 50-60%
│   └── Ergebnisse: 162 Posts (Sim10, CDI=5%)
│
├── Gen 3 (Skill derived from Gen 2) — intermediate
│   └── Skill: derived-from-gen-2.md (WIRD NICHT ALS EIGENER RUN AUSGEFÜHRT)
│
└── Gen 4 (3× Re-Inheritance) — dritter gemessener Schritt
    ├── Project: proj_<topic>-gen4
    ├── Skill: derived-from-gen-3.md (enthält Gen 0+Gen 2 Findings)
    ├── Erwartet: starke Cluster-Saturation, CDI 80-90%
    └── Ergebnisse: 129 Posts (Sim10, CDI=1%, aber Cluster-Hit-Density 71.9%)
```

**Warum Gen 1+3 überspringen:** Jede Generation braucht ~40-60 Min runtime + Report. Bei 5 Generationen = 5h → zu lang. Sim10 überspringt die Skill-Erstellungs-Generation (Gen 1, Gen 3) und läuft nur Gen 0, Gen 2, Gen 4. Die übersprungenen Skills werden dennoch erstellt — sie dienen als Skill-Input für die nächste Generation.

### Seed-Struktur (gegenüber Standard abweichend)

Der Seed enthält ZUSÄTZLICH zur Standard-Struktur:

```
## Section I — Bias Research Question (explizit!)
I.1 Forschungsfrage (DE + EN): Wie kumuliert Bias über N Generationen?
I.2 Erwartete Drift-Rate: CDI 10% → 55% → 88%
I.3 Metriken: Cluster-Saturation, CDI, INS

## Section J — Hypothesen (explizit!)
J.1 Hypothese Gen 2: Auditability 40-50%, Cost stabil
J.2 Hypothese Gen 4: Auditability 70-85%, Cost kollabiert
J.3 Baseline aus Gen 0: wird nach Gen-0-Extraktion aktualisiert
```

**Wichtig:** Die Forschungsfrage MUSS explizit im Seed stehen. Ohne sie antizipieren die Personas die Bias-Frage nicht — und die Ergebnisse werden skill-neutral.

---

## 3. Metriken (CDI, INS, Cluster-Saturation)

### 3.1 Cluster-Saturation (Hauptmetrik)

**Definition:** Wie viel Prozent aller Cluster-Marker-Hits entfallen auf jedes Cluster, pro Generation.

```python
CLUSTER_MARKERS = {
    'Layering': ['layering', 'layer', 'sandbox', 'sub-layer', 'control plane'],
    'Cost': ['cost', 'routing', 'three-tier', 'c0-c4', 'cost_per_verified'],
    'Auditability': ['audit', 'byte-identical', 'replay', 'gate-decision', 'q/w-g', 'queen-worker', 'provenance', 'provenance_chain'],
    'Recovery': ['recovery', 'retry', 'reassign', 'checkpoint', 'heartbeat', 'idempotency'],
    'Reviewer_Model': ['reviewer', 'factchecker', 'review-process'],
    'EU_Compliance': ['eu ai act', 'compliance', 'data-residency', 'self-host', 'sovereign']
}
```

**Interpretation:**
- Cluster mit >70% Saturation in einer Generation = **Bias-Dominanz** (das Thema absorbiert den Diskurs)
- Cluster mit <1% Saturation = **Cluster-Kollaps** (vom Skill verdrängt)
- Nicht-monotoner Verlauf (z.B. Cost 26→55→1.5%) = **Cluster-Migration**, kein gradueller Drift
- Vergleich mit Baseline (Gen 0) zeigt **absolute Bias-Zunahme durch Skill**

**Sim10-Baseline (Cluster-Saturation):**

| Cluster | Gen 0 | Gen 2 (1×) | Gen 4 (3×) |
|---|---|---|---|
| Auditability | 37.6% | 25.7% | **71.9%** |
| Cost | 26.7% | **55.8%** | 1.5% |
| Layering | 15.0% | 6.6% | 14.5% |
| EU_Compliance | 9.2% | 5.6% | 6.8% |
| Recovery | 1.1% | 5.6% | 5.1% |
| Reviewer_Model | 10.4% | 0.7% | 0.1% |

### 3.2 CDI (Concept Drift Index)

**Definition:** Anteil der Top-N N-Gramme aus Gen 0, die in der Ziel-Generation wörtlich vorkommen.

```python
# Gen 0: extrahiere alle 3-5-grams mit freq≥2
# Ziel-Gen: prüfe ob diese Phrasen wörtlich vorkommen
CDI = hits / len(top_phrases) * 100
```

**Interpretation:**
- CDI >50%: **starke textuelle Reproduktion** — Skill zwingt Personas zum Abschreiben
- CDI 10-50%: **moderate konzeptuelle Vererbung**
- CDI <5%: **kein textuelles Bias** — Konzepte werden reformuliert. Bias ist konzeptuell, nicht wörtlich.

**Sim10-Befund:** CDI Gen 2 = 5%, Gen 4 = 1%. Überraschend niedrig. **Konzeptuelles Bias ist wichtiger als textuelles Bias.**

**KONSEQUENZ:** CDI allein reicht nicht als Bias-Indikator. Cluster-Saturation ist primär.

### 3.3 INS (Insight Novelty Score)

**Definition:** Anteil der Top-100 N-Gramme in der Ziel-Generation, die exklusiv (in keiner anderen Generation vorkommen).

```python
phrases_this = set(top_100_trigrams(this_run))
phrases_other = set(top_100_trigrams(other_run))
only_this = phrases_this - phrases_other
INS = len(only_this) / len(phrases_this) * 100
```

**Interpretation:**
- INS ~100%: **jede Generation spricht komplett anders** (neues Vokabular) — guter Indikator für Diskurs-Weiterentwicklung
- INS <20%: **Vokabular-Stagnation** — Generationen wiederholen sich

**Sim10-Befund:** INS ~100% in allen 3 Generationen. **Heuristik-Limitation:** 3-grams sind zu kurz für echte Novelty-Messung.

---

## 4. Cluster-Migration (Key Finding)

### Bias ist Migration, nicht Drift

Sim10 hat gezeigt: Bias-Vererbung durch Skill-Chaining ist **nicht** graduell (Drift), sondern **kategorial** (Migration). Cluster springen zwischen Generationen in neue Dominanz-Verhältnisse.

**Drei typische Migrationspfade:**

| Typ | Beschreibung | Sim10-Beispiel | Warnsignal |
|---|---|---|---|
| **Kumulative Saturation** | Cluster wächst monoton mit jeder Generation | Auditability 37→25→71% (nicht-monoton aber explosionsartig in Gen 4) | >70% = Bias-Kippunkt |
| **Peak-and-Collapse** | Cluster steigt in mittlerer Generation, bricht in letzter ein | Cost 26→55→1.5% | Peak in Gen 2 = "frühe Verdrängung" |
| **Kollaps** | Cluster stirbt zwischen Gen 0 und Gen 2 | Reviewer_Model 10.4→0.7→0.1% | <1% = funktional tot |

### Was es bedeutet

- **Reviewer-Model stirbt durch Skill-Chaining**: Wenn Skills deterministisch sind, denken Personas "kein Reviewer mehr nötig". → Gefährlich! Hermes V7 muss explizite Reviewer-Gates für Skill-Chains fordern.
- **Cost-Argumente werden verdrängt**: Skill-Chaining ist ökonomisch blind. → Cost-Frage als Mandatory-Audit-Question pro Run aufnehmen.
- **Recovery ist strukturell latent**: Bleibt in allen Runs zwischen 1-6% — klein aber stabil. → Recovery-Status als Post-Condition für Skill-Chains fordern.

### Vergleich zu Sim09 (A/B/C Triade)

| Aspekt | Sim09 (Triade) | Sim10 (Multi-Gen) | Erkenntnis |
|---|---|---|---|
| Cost-Cluster | 17→21→32% (steigt) | 26→55→1.5% (Peak+Crash) | **Widerspruch** — Skill-Typ vs Generationen-Tiefe wirken anders |
| Reviewer_Model | 22→10→6% (fällt) | 10.4→0.7→0.1% (kollabiert) | **Bestätigt** — Reviewer stirbt in beiden |
| Layering | 24→53→31% (U-Kurve) | 15→6.6→14.5% (U-Kurve) | **Bestätigt** — Layering hat U-Form in beiden |
| Fresh-Diskurs | 41% Auditability | 37.6% Auditability | Stabil — ähnliche Baseline |

→ **Sim09 und Sim10 zeigen unterschiedliche Cost-Dynamik**: In Sim09 (A/B/C, skill-typ-vergleich) steigt Cost mit Skill; in Sim10 (multi-gen, tiefe) kollabiert Cost nach Gen 2. Der Unterschied liegt in **Skill-Typ vs Generationen-Tiefe**.

---

## 5. Runbook für N-Generation-Studie

### Phase 0: Setup

```bash
# 1. Seed schreiben (mit Bias-Frage explizit in Section I+J)
# 2. Gen 0 Skill = null (Fresh)
# 3. RAM check: ≥3 GB frei
# 4. Keine stale OASIS workers
```

### Phase 1: Baseline (Gen 0)

```markdown
1. Sim Create + Prepare + Start (60 rounds)
2. Wait for completion (Observer mit Python, nicht bash)
3. Extract ALL posts → `/tmp/sim0-posts.json`
4. Run Cluster-Saturation analysis → Gen 0 Table
5. Write derived-skill-from-gen-0.md → `testdata/skills/`
```

### Phase 2: Hypothesen schreiben

```markdown
Basierend auf Gen 0: Vorhersagen für Gen 2:
- Auditability: X% (Hypothese)
- Cost: Y% (Hypothese)
- CDI erwartet: Z%
- INS erwartet: W%

Basierend auf Gen 0: Vorhersagen für Gen 4:
- ...
```

**Wichtig:** Hypothesen schreiben VOR Gen 2 Start. Der Gap zwischen Vorhersage und Realität ist der eigentliche Befund.

### Phase 3: Gen 2 (1× Inheritance)

```markdown
1. Gen 1 Skill schreiben: `derived-from-gen-0.md`
   → Extrahiere Findings aus Gen 0 Report
   → Struktur: Deterministisches 10-Persona-Set, 6 Cluster mit Prioritäten

2. Gen 2 Project: `proj_<topic>-gen2`
   → Seed + derived-from-gen-1.md multipart upload

3. Sim Create + Prepare + Start
4. Wait + Extract → Cluster-Saturation
5. Compare vs Hypothese → Gap dokumentieren
```

### Phase 4: Gen 4 (3× Inheritance)

```markdown
1. Gen 3 Skill schreiben: `derived-from-gen-2.md`
   → Extrahiere Findings aus Gen 2 Report
  
2. Gen 4 Project + Sim Create + Prepare + Start
3. Wait + Extract → Cluster-Saturation
4. Compare vs Hypothese
```

### Phase 5: Finale Synthese

```markdown
1. Cross-Gen-Vergleich: Tabelle Cluster-Saturation × 3 Runs
2. Hypothese-Validierung: Welche Annahmen waren richtig?
3. 5+ Lessons (methodologisch + skill-system)
4. Empfehlung: Lohnt sich Skill-Chaining für diesen Frage-Typ?
```

---

## 6. Sim10 Factsheet (Referenz)

| Attribut | Wert |
|---|---|
| Runs | 3 (Gen 0, Gen 2, Gen 4) |
| Posts total | 458 |
| Runtime | ~1.5h (inkl. Setup) |
| Seed | `testdata/sim10-bias-reproducibility-seed.md` |
| Skills | 3: `derived-from-gen-{0,1,3}.md` |
| Hypothesis validated | Auditability-Saturation ✅, Cost-Kollaps ✅, Reviewer-Tod ✅ |
| Hypothesis refuted | INS <10% widerlegt (100%), CDI 80-90% zu hoch (1-5%) |
| Unexpected finding | Cluster-Migration > Drift, Recovery latent stabil |
| Files | `/tmp/sim10-gen{0,2,4}-{fresh,mid,deep}-posts.json` |
| Final synthesis | `SIM10-BIAS-DRIFT-SYNTHESE-FINAL.md` |

---

## 7. Pitfalls

### 7.1 Hypothesen zu eng setzen
Sim10 hatte CDI-Hypothese bei 80-90% für Gen 4 — Realität war 1%. Auf CDI allein zu setzen blendet Cluster-Saturation aus. **Immer Cluster-Saturation + CDI + INS parallel messen.**

### 7.2 Skill-Generation-Sequenz falsch verstehen
Gen 1 und Gen 3 sind **Skills, keine Runs**. Ein häufiger Fehler: Gen 2 direkt von Gen 0 ableiten (überspringt den Skill-Bau-Schritt). **Immer: Run N → Report N → Skill N+1 → Run N+2.**

### 7.3 Frontend-Prozent-Anzeige für Prepare
76% Prepare für 5+ Minuten ist normal (LLM-Config-Generation pro Entity dauert 60-120s). **Nicht panic-restarten** — siehe `operational-experience-2026-07-14.md`.

### 7.4 Observer nicht mit bash
Bash-Watchdogs sterben unter Hermes cron-mode. **Immer Python-Observer** — siehe `templates/robust-watcher.py`.

### 7.5 Zep Rate-Limit bei parallelen Graph-Builds
FREE Plan = ~5 req/min. **Immer sequenziell bauen** — siehe `operational-experience-2026-07-14.md`.