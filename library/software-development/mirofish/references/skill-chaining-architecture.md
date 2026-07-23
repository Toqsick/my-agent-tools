# Skill-Chaining Simulation Archetype — Blaupause für A/B/C-Runs

> **Purpose**: Detaillierte Blaupause für MiroFish-Simulationen, die **skill reuse vs fresh generation** vergleichen. Ergänzt Step 5f der mirofish-Skill mit vollständigen Konkretbeispielen aus Sim09.
> **Referenziert von**: `mirofish/skill.md` Step 5f
> **Erstbefüllt**: 2026-07-13, Skill-Chaining-Biene

---

## 1. Wann dieses Archetype verwenden

- Card 09 des Max-Kampagne Decks wird gezogen ("Skill-Chaining, Wiederverwendung")
- Du willst A/B/C-Vergleich zwischen "von Grund auf", "nur Form" und "abgeleitet von Findings"
- Die Forschungsfrage lautet: *Lohnt sich Skill-Reuse, oder führt es zu Format-Bias?"

**Nicht verwenden wenn:**
- Nur eine einzelne Simulation ohne Vergleichsgruppe nötig ist → Standard-Seed aus Step 1
- Die Frage bereits empirisch geklärt ist (nach Sim09 haben wir Daten)

---

## 2. Drei Skill-Typen im Detail

### 2.1 Fresh (kein Skill) — Run A

```
skill_type: null
zep_persona_skeleton_hint: null  # Zep generates everything
setup_time_estimate: 5-7 min
runtime_estimate: 60-90 min
bias_inheritance: none
best_for: Baseline, max surprise
```

**Zep-Verhalten:** Zep generiert Persona-Handles, Rollen, Findings-Cluster und Konfliktlinien ausschließlich aus dem Seed. Keine Einschränkung durch eine Skill-Datei.

**PITFALL — Cluster-Inkonsistenz:** Ohne Skill wählt Zep die Findings-Cluster selbst. Bei 3 Fresh-Runs zum selben Thema können 3 verschiedene Cluster-Architekturen entstehen. Das ist *gewollt* für die Baseline (misst natürliche Varianz), aber macht Cross-Run-Comparisons schwieriger.

### 2.2 Template-Skill (Form only) — Run B

```
skill_type: template
version: 1.0.0
zep_persona_skeleton_hint: 7 functional slots (handles left to Zep)
cluster_structure: 6 empty clusters (content left to Zep)
setup_time_estimate: 3-5 min
runtime_estimate: 30-50 min
bias_inheritance: none (form-only)
best_for: Format-consistency test, bias-free speed
```

**Konkretes Beispiel aus Sim09 (`template-multi-agent-zh.md`):**

Die 7 funktionalen Slots sind:
1. **Architecture-Synthesist** — defends architecture-choice
2. **Cost/Trade-off-Optimizer** — challenges with TCO
3. **Quality/Rigor-Gate-Owner** — defends against rushed conclusions
4. **Operator/SRE** — anchors in incident-reality
5. **Vendor-A (proprietary managed)** — defends managed-runtime stack
6. **Vendor-B (open-weight self-host)** — defends open-weight
7. **Academic-Ethics-Critic** — challenges with bias evidence

Die 6 leeren Cluster:
1. **Layering** — Architecture-Layering, Control-Plane, Sub-Layer
2. **Cost** — Three-Tier-Routing, Cost_per_Verified_Success
3. **Auditability** — Q/W-G, byte-identical-replay, defense-in-depth
4. **Recovery** — Checkpoint, idempotency-key, retry-strategy
5. **Reviewer-Model** — Sonnet/GPT/Mistral review-trade-offs
6. **EU-Compliance** — Self-host vs cloud, data-residency

**YAML-Frontmatter für Template-Skills (template):**
```yaml
---
name: <topic>-template-v1
version: 1.0.0
type: template
scope: persona+findings-structure
applies_to: mirofish-simulation
zep_compatibility: free-tier (≤10 personas)
language: bilingual (EN backbone, DE block-cites)
---
```

**Bias-Selbstauskunft für Template-Skills:**
```yaml
bias_disclosure:
  inherited_from: none  # Template, kein Inhalt
  self_disclosed_bias: false
  known_limitations:
    - "Does not constrain which topics personas prioritize"
    - "Does not constrain personas' training-data framing"
    - "Inherits Zep's training-set biases via persona-generation"
```

### 2.3 Derived-Skill (deterministisch) — Run C

```
skill_type: derived
version: 1.0.0
derived_from: [report_id_a, report_id_b, ...]
zep_persona_skeleton_hint: deterministic 10-persona-set (override forbidden)
cluster_structure: 6 clusters WITH inherited priorities
setup_time_estimate: 2-4 min
runtime_estimate: 25-40 min
bias_inheritance: high (inherits source priorities)
best_for: Reproducibility test, max bias-inheritance measurement
```

**Konkretes Beispiel aus Sim09 (`derived-from-v1-v2-findings.md`):**

Das Derived-Skill aus Sim09 enthält:
- **Source-Disclosure** mit 3 Reports: `report_df725b58d6a5` (41k, Framework-Layering), `report_9b1f394224a7` (35k, Structural Risks), `report_66fef02753e0` (22k, Pydantic/C0-C4)
- **Bias-Inheritance Summary**: "Framework-Layering treated as given, Cost-Routing as highest-leverage, Q/W-G as only sane pattern"
- **Deterministisches 10-Persona-Set** mit @-Handles und 1-Sentence-Roles
- **6-Cluster-Architektur mit Prioritäten**: Layering=HIGH, Cost=HIGH, Auditability=HIGH, Recovery=MEDIUM, Reviewer-Model=MEDIUM, EU-Compliance=MEDIUM

**YAML-Frontmatter für Derived-Skills:**
```yaml
---
name: <topic>-derived-from-<source>-v1
version: 1.0.0
type: derived
scope: personas+findings
applies_to: mirofish-simulation
zep_compatibility: free-tier (≤10 personas)
language: bilingual (EN backbone, DE block-cites)
derived_from:
  - report_xxxx  # Report-ID aus früherem Run
  - report_yyyy
self_disclosed_bias: true
bias_inheritance_summary: |
  This skill inherits Findings-Schwerpunkte:
  - Framework-Layering emphasized
  - Cost-Routing treated as highest-leverage
  - Q/W-G-Auditability presupposed
  Recovery, Reviewer-Model, and EU-Compliance may be UNDER-represented.
---
```

**Bias-Selbstauskunft für Derived-Skills:**
```yaml
bias_disclosure:
  inherited_from:
    - report_xxxx
    - report_yyyy
  self_disclosed_bias: true
  known_inherited_biases:
    - cluster_1_layering_priority: HIGH
    - cluster_2_cost_priority: HIGH
    - cluster_3_auditability_priority: HIGH
    - cluster_4_recovery_priority: MEDIUM
    - cluster_5_reviewer_model_priority: MEDIUM
    - cluster_6_eu_compliance_priority: MEDIUM
  what_this_skill_does_NOT_inherit:
    - "Specific market-share numbers"
    - "Specific framework rankings"
    - "Specific 2026 regulatory timelines"
  transparency_principle: |
    Transparency about bias does not eliminate bias — it makes it auditable.
```

---

## 3. Seed-Struktur (vollständig)

Die Seed-Datei (`testdata/simXX-<topic>-seed.md`) folgt diesem Schema:

```
# MiroFish Simulation XX — <Topic>: Gemeinsamer Seed (A, B, C)

## TL;DR Box
- Seed: testdata/simXX-<topic>-seed.md
- Persona-Count: 10 (Zep-Free-Tier-Limit)
- Round-Count: 60
- Platform: Twitter only
- Chunks: 50, overlap 60

## Section A — Topic Introduction
A.1 What is <Topic> in a Multi-Agent System?
A.2 Why is <Topic> a 2026 Maturity Indicator?
A.3 Trade-off-Hypothesis

## Section B — Persona-Beschreibungen (10, Englisch)
B.1-B.10: Handle, Role, Years, Conflict-Pair, Background, Typical Statements, Conflict lines

## Section C — Research Question (DE + EN)
C.1 Deutsche Forschungsfrage
C.2 English Research Question
C.3 Decomposed Sub-Questions (5)

## Section D — Drei-Run-Schema
Run A (Fresh): skill_file=null
Run B (Template): skill_file=template-<topic>.md
Run C (Derived): skill_file=derived-from-<topic>.md
Diff-Summary-Table
Project-Isolation-Rule

## Section E — Konfliktlinien (mind. 3)
E.1 Conflict 1: Pair A vs Pair B, Trigger Question, Resolution-metric
E.2 Conflict 2: ...
E.3 Conflict 3: ...

## Section F — Metriken-Definition
F.1 Quantitative Metrics (setup_time, format_consistency, jaccard_overlap, ...)
F.2 Findings-Categories-Cluster (6 + 7th for cluster-blindness)
F.3 Qualitative Self-Assessment

## Section G — Stop-Words / Out-of-Scope
G.1 7 out-of-scope topics
G.2 Redirect protocol

## Section H — Closing Brief Template
H.1 Per-run closing memo structure
H.2 Cross-Run-Cross-Comparison template
```

---

## 4. Deployment-Checkliste für Königin

### 4.1 Vor Run-Start

```markdown
- [ ] Seed-Datei geschrieben: testdata/simXX-<topic>-seed.md
- [ ] Template-Skill geschrieben: testdata/skills/template-<topic>.md
- [ ] Derived-Skill geschrieben: testdata/skills/derived-from-<source>.md
- [ ] Alle 3 Dateien validiert:
  - wc -l (Seed: 400-500 Zeilen, Template: 200-250, Derived: 400-500)
  - Code-Fences alle gerade (grep -c '^```' | alle Werte gerade)
  - Alle Tabellen integer (keine broken rows)
  - Persona-Handles identisch in Seed + Derived (grep -oE '@[a-z_]+' | sort -u)
- [ ] Persona-Count = genau 10 (Zep-Free-Tier-Limit)
- [ ] 3 separate Projekte in der MiroFish-API angelegt
- [ ] RAM ≥ 3 GiB frei (free -h)
- [ ] Keine stale OASIS workers (ps -ef | grep run_simulation)
- [ ] Max-Kampagne-Card dokumentiert (one-pager gezeigt zur Bestätigung)
```

### 4.2 Validation vor Run C (Derived-Skill)

```python
validation_checks = [
    ("All 10 @-handles in Zep-output", True),
    ("All 10 1-sentence-roles match (semantically-or-verbatim)", True),
    ("6 cluster-names match exactly", True),
    ("6 cluster-priorities match inherited schema", True),
    ("bias-disclosure-header in Zep-output surfaced", True),
]
# If any fails → ABORT Run C, fix Zep-payload, re-run
```

### 4.3 Während der Runs — Conflict Time Routing

| Round Range | Active Conflict | Personas | Erwartung |
|---|---|---|---|
| 1-15 | Conflict 1 (Setup-Zeit vs Anpassung) | @cost_cfo ↔ @quality_gate | Schnelle quantitative Klärung |
| 20-45 | Conflict 2 (Konsistenz vs Bias-Vererbung) | @basti_synth ↔ @academic_eth | Braucht Findings aus R1-15 |
| 40-60 | Conflict 3 (Self-Hosting vs API-Cloud) | @mistral_vendor ↔ @openai_vendor | Hängt von vorheriger Entsch. ab |

Königin pollt nach jedem Round-Block (15/30/45/60) den Simulation-Status und prüft, ob die Konflikte wie erwartet eskalieren.

### 4.4 Nach jedem Run — Closing Memo

```yaml
run_id: simXX-run-a/b/c
cluster_metrics:
  Layering: { mentions: int, conflicts: int, key_quotes: [str] }
  Cost: { mentions: int, conflicts: int, key_quotes: [str] }
  Auditability: { mentions: int, conflicts: int, key_quotes: [str] }
  Recovery: { mentions: int, conflicts: int, key_quotes: [str] }
  Reviewer_Model: { mentions: int, conflicts: int, key_quotes: [str] }
  EU_Compliance: { mentions: int, conflicts: int, key_quotes: [str] }
persona_metrics:
  - handle: @basti_synth
    drift_count: int
    final_position: str
quantitative_metrics:
  setup_time_seconds: int
  format_consistency: bool
  jaccard_overlap_with_source: float
  persona_drift_count: int
  new_insights_pct: int
  post_processing_minutes: int
```

---

## 5. Cross-Run Synthese (Finaler Schritt)

Nachdem alle 3 Runs abgeschlossen sind:

### 5.1 Cross-Comparison-Tabelle

| Skill-Type | Konsens-Punkte | Risiken |
|---|---|---|
| **Fresh (Run A)** | was universally agreed | what went unaddressed due to no structure |
| **Template (Run B)** | was universally agreed | where empty template constrained useful conflict |
| **Derived (Run C)** | was universally agreed | which blind spots inherited from source |

### 5.2 Final-Recommendation (zwingend!)

> *"For Q3/Q4-2026 multi-agent simulation campaigns, recommend Skill-Type `X` for question-type `Y`, because `Z`. Skill-Type `W` is contra-indicated because `V`."*

### 5.3 Expected Findings (aus Sim09-Ableitung)

Erwartung für Skill-Chaining-Simulationen (basierend auf Sim09-Pattern):
- **Fresh (Run A)** hat die niedrigste Jaccard-Overlap mit Quell-Reports → misst "echt neuen Ground"
- **Derived (Run C)** hat die höchste Jaccard-Overlap → misst Bias-Vererbung (das ist *erwartet*, nicht bug)
- **Template (Run B)** liegt in der Mitte → misst ob Format allein schon Bias verursacht

**Wenn Run C < 20% new_insights_pct** → Skill-Chaining ist für diese Frage-type kontraproduktiv
**Wenn Run C > 40% new_insights_pct** → Der Bias ist überraschend niedrig → Skill-Chaining lohnt sich
**Wenn Run B ≈ Run A + <10% Format-Vorteil** → Template-Skills lohnen sich nicht (zu wenig saving für den Formatzwang)

---

## 6. Übernommenes Wissen aus Sim09

### 6.1 Lessons-from-V2 (apply verbatim)

1. max_tokens=8192 im ontology_generator ist bereits gepatched
2. source_targets Auto-Truncate auf max 10 implementiert
3. Backend-Restart via Background-Process (nicht via npm)
4. Watcher ohne notify_on_complete, mit log-file
5. RAM-Awareness: ≥3 GB frei VOR Start
6. Project-Isolation: jedes Run eigenes Projekt

### 6.2 Biene-Delegation-Prompt (Template)

```
Du bist die **Skill-Chaining-Biene**. Deine Aufgabe: drei versorgungs-fertige
Artefakte in <project-root>/testdata/ anlegen:

1. testdata/simXX-<topic>-seed.md — gemeinsamer Seed
2. testdata/skills/template-<topic>.md — YAML-frontmatter, form-only
3. testdata/skills/derived-from-<source>.md — deterministisch

KEINE MiroFish-Starts, KEINE API-Calls, KEINE Pip-Install — nur File-Erstellung.

Referenz-Dateien:
- <path-to-style-ref> (Stil-Vorgabe: DE/EN bilingual, diskursiv/strukturell/operativ)
- <path-to-source-reports> (wenn Derived-Skill aus Vorberichten abgeleitet wird)

Persona-Set (muss in Seed + Derived-Skill IDENTISCH sein):
1. @basti_synth — Synthesist...
(10 personas)

Validierung nach Erstellung:
- wc -l auf alle 3 Dateien
- Persona-Handles identisch: grep -oE '@[a-z_]+' | sort -u | diff
- Code-Fences alle gerade
- Tabellen alle integer-aligned (Python-check)
- Explizites Verbot von API-Calls oder Simulation-Starts
```