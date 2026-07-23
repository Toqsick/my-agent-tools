# Routing-Tabelle — Trigger-Match-Logik + 52-Skill-Matrix

> **Stand:** 2026-07-07 (v2.0.0, absorbed yuno-team-routing)
> **Source of Truth:** `~/Downloads/team-roster.md`
> **Agent-Tag-Patching:** Siehe `references/agent-tag-patch-workflow.md`

## Trigger → Agent (Kurztabelle)

| Trigger-Phrase (User sagt) | → Agent |
|---|---|
| `build` / `fix` / `refactor` / `review code` / `debug` / `api` / `code` | **Engineer** |
| `find me X` / `what's the latest` / `research` / `compare` / `search` | **Researcher** |
| `design` / `landing page` / `logo` / `UI` / `UX` / `visual` / `color` | **Designer** |
| `spreadsheet` / `model` / `calculate` / `chart` / `data` / `analyze` / `train` | **Analyst** |
| `write a doc` / `draft a proposal` / `compose` / `long copy` / `proposal` / `blog` | **Writer** |
| `verify` / `audit` / `is this done` / `check this` / `validate` / `review PR` | **Verifier** |
| Unklar / Multi-Domain / "mach mal" | **Yuno** (root) |

---

## 52-Skill Agent Inventory

### 🌸 Yuno — Root Orchestrator (5 Skills, v2.0.7+)

**Note:** Yuno ist primär der Routing-Decision-Layer (siehe Haupt-SKILL.md), nicht der Skill-Ausführer. Diese 5 Skills sind die Meta-/Plumbing-Skills, die Yuno für Decompose, Doku, Skill-Erstellung und Tool-Integration pflegt.

| Skill | routing_hint |
|---|---|
| `ideation` | Brainstorming-Phase vor jedem Build — Intent klären, Constraints sammeln, "was will ich eigentlich?" |
| `self-improving` | Persistiert Lessons aus Fehlern in Mnemosyne. Trigger nach jedem nicht-trivialen Fehler. Cross-domain. |
---

## ~56-Skill Agent Inventory

### 🧠 Yuno (Root — 5+ Skills)

Cross-domain Skills, die keine Spezialisierung haben sondern vom Yuno-Orchestrator direkt genutzt werden.

| Skill | routing_hint |
|---|---|
| `self-improving` | Persist Lessons from failures — cross-domain Memory + Skill evolution. Kein Agent-spezifisch, Yuno root |
| `skill-creator` | Create new Skills from descriptions — meta-skill for recurring workflows. Yuno orchestriert |
| `multi-agent-work` | 6-Phase Multi-Agent Workflow — Research → Fixes → PR. Yuno orchestriert die Agenten |
| `ideation` | Intent-Klärung vor kreativen/Build-Arbeiten. Yuno entscheidet, wann decompose nötig ist |
| `worktree-management` | ⚠️ **GAP — kein Hermes-Skill existiert.** Workaround: manuelles `git worktree add`. Trigger für Skill-Kreation: 3x "worktree für Feature X isolieren". → Siehe `references/skill-tiers.md` § "Echte Lücken" |

### 🛠️ Engineer (8 Skills)

| Skill | routing_hint |
|---|---|
| `claude-coder` | Implementation Engineer for hard problems — build, refactor, debug code in any language |
| `claude-coding-specialist` | Senior Software Engineer for hard architectural problems |
| `claude-worker` | Mechanical Execution — batch tasks, boilerplate, mechanical coding |
| `systematic-debugging` | 4-Phase root cause analysis — understand before fixing |
| `github-workflow` | GitHub PR lifecycle, CI/CD, commits via gh CLI + git |
| `subagent-driven-development` | Execute plans via delegate_task subagents with 2-stage review |
| `plan` | Plan mode — write actionable markdown plans to .hermes/p |
| `writing-plans` | Write implementation plans — bite-sized tasks, paths, code |

### 🔬 Researcher (9 Skills)

| Skill | routing_hint |
|---|---|
| `research-tools` | arXiv, blog/RSS monitoring, web archive, research paper discovery |
| `arxiv` | Search arXiv papers by keyword, author, category, or ID |
| `llm-wiki` | Build/query interlinked markdown KB |
| `notebooklm-bridge` | Drive Google's NotebookLM from Hermes |
| `firecrawl-web` | Web scraping, screenshots, structured data extraction |
| `bioinformatics` | Gateway to 400+ bioinformatics skills |
| `ocr-and-documents` | Extract text from PDFs/scans |
| `web-archive-research` | Query web archives (Common Crawl CDXJ, WARC) |
| `research-paper-writing` | Academic paper writing workflow |

### 🎨 Designer (12 Skills)

**Atom/Molecule/Organism (gelernt 2026-07-08):** Skills = Atoms, Persona = Molecule, Multi-Agent-Loop = Organism. Designer-Skills sind einzeln aufrufbar; die Persona bündelt sie zu coherent workflow; der Multi-Agent-Loop (Researcher→Designer→Writer→Engineer→Verifier→Deploy) ist das Organism.

**Production-Lesson (2026-07-08, Bundle-Showcase-Landing-Page E2E-Test):** Designer MUSS Token-basiert liefern, nicht self-contained HTML. Sonst bricht Multi-Agent-Integration (siehe `references/landing-page-workflow.md` v1.3 → Pitfall #6 + Deployment-Readiness-Snapshot).

| Skill | routing_hint |
|---|---|
| `ui-factory` | Orchestrate full UI chain — color system → design system → components → dashboard |
| `ui-color-system` | Generate accessible color palettes (semantic + scale) |
| `ui-design-system` | Token spec, component library, dashboard scaffold |
| `html-artifact` | Build self-contained HTML files to explain, plan, or review |
| `popular-web-designs` | 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS |
| `anime-design` | Professional anime/2D art style generation |
| `anime-style-forge` | Specialized in anime/2D/character stylization |
| `film-shot` | Professional film storyboard / film still / character card |
| `architecture-diagram` | Dark-themed SVG architecture/cloud/infra diagrams as HTML |
| `excalidraw` | Hand-drawn JSON diagrams (arch, flow, seq) |
| `web-design-guidelines` | UI code review against Vercel's web interface guidelines |
| `claude-design` | Design one-off HTML artifacts (landing, deck, prototype) |

### 📊 Analyst (9 Skills)

| Skill | routing_hint |
|---|---|
| `mlops-suite` | ML model serving, evaluation, hosting — vLLM, Ollama, llama.cpp |
| `axolotl` | YAML LLM fine-tuning (LoRA, DPO, GRPO) |
| `vllm` | High-throughput LLM serving, OpenAI API, quantization |
| `lm-evaluation-harness` | Benchmark LLMs (MMLU, GSM8K, etc.) |
| `weights-and-biases` | Log ML experiments, sweeps, model registry, dashboards |
| `huggingface-hub` | HuggingFace hf CLI — search/download/upload models, datasets |
| `llama-cpp` | Local GGUF inference + HF Hub model discovery |
| `rag-pipeline-python` | RAG pipeline in Python |
| `obliteratus` | Abliterate LLM refusals (diff-in-means) |

### ✍️ Writer (6 Skills)

| Skill | routing_hint |
|---|---|
| `system-documentation` | Maintain structured Markdown documentation tree for all systems |
| `pr-body-standards` | PR body creation with actual test execution prelude |
| `pdf-anthropic` | PDF processing (read, extract, summarize) |
| `nano-pdf` | Edit PDF text/typos/titles via CLI |
| `powerpoint` | Create, read, edit .pptx decks, slides, notes, templates |
| `epub-export` | Convert markdown or PDF content to EPUB |

### 🔐 Verifier (8 Skills)

| Skill | routing_hint |
|---|---|
| `critic-gate` | Deterministic critic with hard gate — check output quality |
| `security-code-checker` | Scanner for LLM-generated code — detects red flags |
| `requesting-code-review` | Pre-commit review — security scan, quality gates, auto-fix |
| `output-validator` | Pre-flight check — validates JSON, Markdown, config format |
| `verify-before-fix` | Execute bug fixes from an issue description |
| `simplify-code` | Parallel 3-agent cleanup of recent code changes |
| `security-audit` | Linux security audit — open ports, services, permissions |
| `test-driven-development` | RED-GREEN-REFACTOR — tests before code |

---

## Trigger-Match-Logik

### 1. Wort-Boundary-Match
Trigger matchen nur als **ganze Wörter**, kein Substring.
Implementiert via Regex `\b{trigger}\b` mit `re.IGNORECASE`.

### 2. Match-Score-Sortierung
Mehr gematchte Trigger = höherer Score = höherer Rang.

### 3. Verifier-Gate-Priorität
Wenn Verifier mit Gate-Phrase matched (`audit`, `verify`, `is this done`, `check this`, `validate`, `qa`, `review`, `gate`), dominiert Verifier **vor** Match-Score.

### 4. Multi-Domain-Detection
2+ Personas aus verschiedenen Domänen → Decomposition-Modus.

### 5. NO-MATCH-Fallback
Chitchat → nichts routen → Yuno Default-Mode.

### 6. Multi-Word-Trigger-Fallback
Multi-Word-Trigger (z.B. `"write a doc"`) haben Fallback: wenn exakter Phrasen-Match fehlschlägt, werden alle **Inhaltswörter >2 Zeichen** (ohne Stop-Wörter) einzeln geprüft.

```python
words = [w for w in trigger_lower.split()
         if len(w) > 2 and w not in {"the", "a", "an", "is", "me"}]
if words and all(re.search(r"\b" + re.escape(w) + r"\b", task_lower) for w in words):
    matched.append(trigger)
```

**Beispiele:**
| Task | Trigger | Matcht? |
|---|---|---|
| `"write doc"` | `"write a doc"` | ✅ |
| `"write"` | `"write a doc"` | ❌ (`doc` fehlt) |
| `"draft proposal"` | `"draft a proposal"` | ✅ Fallback |

## Edge-Cases

| Task | Top-Match | Score |
|---|---|---|
| `"build me a Python CSV summarizer"` | Engineer (build) | 1 |
| `"research the latest in vector databases"` | Researcher (research + what's the latest) | 2 |
| `"research and write a blog post"` | Multi-Domain: Researcher + Writer | — |
| `"audit this deliverable"` | Verifier (audit) | Gate-Prio |
| `"verify this code"` | Verifier (verify) + Engineer (code) | Gate-Prio → Verifier |
| `"hello, how are you?"` | NO MATCH | Chitchat |
| `"fix the design of this UI"` | Designer (design+ui) > Engineer (fix) | Score 2 > 1 |
| `"model a financial spreadsheet"` | Analyst (model+spreadsheet+financial) | Score 3 |
| `"write doc"` | Writer (write a doc via fallback) | Score 2 |

## Sortier-Algorithmus (verbatim aus `personas.py`)

```python
verifier_gate_match = any(
    p == "verifier" and any(
        t in {"verify", "audit", "is this done", "check this", "validate", "qa", "review", "gate"}
        for t in triggers
    )
    for p, triggers, _ in matches
)
if verifier_gate_match:
    matches.sort(key=lambda x: (0 if x[0] == "verifier" else 1, -x[2]))
else:
    matches.sort(key=lambda x: -x[2])
```
