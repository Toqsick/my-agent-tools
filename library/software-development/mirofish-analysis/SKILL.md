---
name: mirofish-analysis
title: "MiroFish Analysis — Post-Run, Multi-Run, Agent Chat"
description: "Use when user asks to analyze a completed MiroFish simulation: generate reports, compare multiple runs, run post-run interactive agent chat, or extract insight diversity metrics. NOT for live monitoring (use mirofish-pipeline) or pitfall recovery (use mirofish-pitfalls). Covers Step 3a+3b+3c of the MiroFish lifecycle."
category: software-development
version: '2.7'
created: '2026-07-23'
author: Yuno (split from mirofish v2.6)
lane: software-development
agent: universal
trigger_keywords: ['mirofish', 'report analysis', 'multi-run comparison', 'agent chat', 'post-run', 'insight diversity', 'discourse analysis']
keywords: ['mirofish', 'analysis', 'report', 'comparison', 'agent chat', 'post-run', 'multi-run', 'insight']
related_skills: ['mirofish-pipeline', 'mirofish-pitfalls', 'mirofish-runbook', 'skill-reviewer']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from mirofish 2026-07-23)'

license: MIT
---

# MiroFish Analysis — Post-Run, Multi-Run, Agent Chat

MiroFish Analysis — Post-Run, Multi-Run, Agent Chat


## Step 3a: Post-Run Report Analysis


After both reports are generated and saved to disk, the most valuable output is a **comparison** across dimensions. Two simulations on the same topic with different seeds (or slightly different configurations) reveal consensus vs divergence far better than either simulation alone.

### Report Output Shapes


MiroFish generates Chinese-language reports. Two distinct output shapes have been observed:

| Shape | Sections | Focus | Typical Length |
|---|---|---|---|
| **Future Prediction** | 3 sections: Findings, Persona Analysis, Outlook+Risks | Structural risks, dark debts, turning-point signals | 25-35k chars |
| **Structured Analysis** | 4 chapters: Layering, Cost, Auditability, Persona Matrix | Framework positions, cost models, audit paradigms | 35-42k chars |

The `Future Prediction` shape excels at surfacing unspoken risks (dark debts, structural audit gaps). The `Structured Analysis` shape excels at mapping positions and trade-offs. When you run two simulations, you typically get one of each — **this is by design** (the LLM's generation path diverges based on early random seed in persona initialization).

### Comparison Methodology


Create a comparison document (`REPORT-VERGLEICH.md`) mapping across these axes:

```
| Dimension | Report A | Report B |
|---|---|---|
| Focus | ... | ... |
| Key numbers | ... | ... |
| Persona distribution | ... | ... |
| Risk emphasis | ... | ... |
| Conclusion | ... | ... |
```

Then extract a **synthesis** — what both reports agree on (this is the high-confidence consensus) and where they diverge (this reveals the real open questions).

### Writing the Summary


After comparison, write a **German-language summary** (~10-15k chars) in standard Markdown covering:
1. Executive Summary (TL;DR with 3-4 bullet points)
2. Key findings per chapter/section
3. Persona conflict matrix
4. Emergent conclusions
5. Next-step recommendations

Save as `~/10-Projekte/20-experimental/MiroFish/SIMULATION-ZUSAMMENFASSUNG.md`.

### 3a-iv: Sub-Analysis — Insight Diversity & Discourse (Advanced, Multi-Run)


After **two or more completed simulations** on the same topic (e.g. A/B/C skill-chaining runs), the most valuable output is a structured sub-analysis across 5 quantitative dimensions. This reveals **bias inheritance, topic drift, and consensus strength** far better than any single run.

**Permission rule:** Full data extraction (SQLite reads, post content) only AFTER simulation is `completed`. During the run, only read `simulation.log` and check DB file size for liveness.

## Step 3b: Multi-Run Comparison (Advanced)


When the user starts a simulation from the landing page UI, you end up with **two concurrent simulations** (yours + theirs). This is a feature, not a bug — it provides triangulation.

**Check for ALL existing simulations before creating a new one:**
```bash
curl -s http://localhost:5001/api/simulation/list | python3 -c "
import json, sys
d = json.load(sys.stdin)
sims = d.get('data', [])
print(f'Found {len(sims)} existing simulations:')
for s in sims:
    sid = s.get('simulation_id', '?')
    status = s.get('status', '?')
    name = s.get('name', s.get('project_name', '?'))
    print(f'  {sid} | {status} | {name}')
"
```

**When both complete, generate both reports and do a cross-comparison:**
1. Save both reports to disk (see step 2g)
2. Read both content structures — identify which is "Future Prediction" shape vs "Structured Analysis" shape
3. Compare key claims: frameworks, cost models, security positions, persona alliances
4. Write synthesis and offer it as a deliverable

**PITFALL:** The user's simulation (started from the UI) may have different parameters (e.g. `?maxRounds=60` in the URL) than the agent-created one. Both run concurrently as independent OASIS worker processes. The landing page UI's create flow can't be predicted — the user may name the project anything.

---

## Step 3c: Post-Run Interactive Agent Chat


After the report is generated and saved, you can **interact with the report agent** via the chat endpoint. This lets you ask specific questions, interview individual personas, or request deeper analysis of simulation findings.

### Finding the Chat Endpoint


The report agent chat lives at `/api/report/chat` (not `/api/report/agent/help` or similar):

```bash
### Chat API Format


```bash
curl -s -X POST http://localhost:5001/api/report/chat \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_xxx",
    "report_id": "report_xxx",
    "message": "Deine Frage an den Report Agent",
    "interview_agents": true,
    "max_agents": 4
  }'
```

**Key parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `simulation_id` | string | yes | The completed simulation ID |
| `report_id` | string | yes | The report ID to query |
| `message` | string | yes | **REQUIRED field name** — NOT `question`! The API expects `message` |
| `interview_agents` | bool | no | Whether to interview individual personas for the answer |
| `max_agents` | int | no | Max personas to interview (1-4, default 4) |

**PITFALL — Field name is `message`, NOT `question`:** The endpoint returns `{"error":"请提供 message"}` if you send `question` instead of `message`. This is a Chinese-language API error — the field name `message` is hard-coded.

### Frontend Chat (Browser)


The report chat is also available in the browser:
- **URL:** `http://localhost:3000/report/{report_id}` — the report view includes a chat input
- **URL:** `http://localhost:3000/interaction/{report_id}` — dedicated interactive agent chat view

### Question Strategy: Option A+C Pattern


The most effective approach for the report agent combines two strategies:

**Option A — Open-ended persona interview:** Ask the agent to interview all personas about their perspectives. This surfaces the full range of opinions.

**Option C — Controversial question:** Ask a pointed question that creates tension between specific personas. This forces the agent to surface disagreements.

**Combined (A+C) — Best approach:** Ask the agent to interview personas AND then answer a specific controversial question. Example:

> "Interview all 4 personas about their A2A topology preferences. Then answer: what would the agreed-upon production topology look like if we forced a decision today?"

**Recommended question types (from V3 experience):**
1. **Offene Persona-Befragung**: "Was sind eure drei wichtigsten Take-Aways aus der Simulation? Welche Patterns haben sich konsistent gezeigt?"
2. **Kontroverser Konflikt**: "Persona-A vs Persona-B: Wer bekommt das letzte Wort wenn Parameter X vs Parameter Y im Konflikt stehen?"
3. **Priorisierungsfrage**: "Welche der SSPC-Items sind am dringendsten? Reihenfolge nach: Time-to-Implement, Risk-if-Skipped, Cost-to-Maintain."
4. **Vendor-Skeptiker-Frage**: "Wo sind die Vendor-Lügen die wir explizit herausrechnen müssen?"
5. **Meta-Frage**: "Wenn ihr nur EINE Production-Regel durchsetzen könntet — welche wäre es?"

---
