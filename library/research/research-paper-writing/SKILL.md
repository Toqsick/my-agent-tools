---
name: research-paper-writing
title: Research Paper Writing Pipeline
description: "Use when user asks to design experiments, analyze results, write, review, revise, or submit an ML/AI research paper for venues such as NeurIPS, ICML, ICLR, ACL, AAAI, or COLM. NOT for simple copyediting or a non-research blog post. Runs the iterative research-paper pipeline from experiment design through evidence-backed submission."
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies:
  - semanticscholar
  - arxiv
  - habanero
  - requests
  - scipy
  - numpy
  - matplotlib
  - SciencePlots
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['Research', 'Paper Writing', 'Experiments', 'ML', 'AI', 'NeurIPS', 'ICML', 'ICLR', 'ACL', 'AAAI', 'COLM', 'LaTeX', 'Citations', 'Statistical Analysis']
    category: research
    related_skills: ['arxiv', 'ml-paper-writing', 'subagent-driven-development', 'plan']
    requires_toolsets: ['terminal', 'files']
lane: worker-heavy
reasoning_effort: xhigh
agent: Researcher
routing_hint: |
  **Agent-Scope:** Deep-research, fact-checking, paper-search, knowledge-base. Off-scope: code-building, visual design, writing — return to Yuno.
  
  Routing-Spec: `yuno-team-routing`.
trigger_keywords: ['design', 'research-paper-writing', 'experiments', 'analyze', 'results']
keywords: ['research', 'design', 'paper', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['design-md']
---
---

# Research Paper Writing Pipeline

End-to-end pipeline for producing publication-ready ML/AI research papers targeting **NeurIPS, ICML, ICLR, ACL, AAAI, and COLM**. This skill covers the full research lifecycle: experiment design, execution, monitoring, analysis, paper writing, review, revision, and submission.

This is **not a linear pipeline** — it is an iterative loop. Results trigger new experiments. Reviews trigger new analysis. The agent must handle these feedback loops.

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## When To Use This Skill

Use this skill when:
- **Starting a new research paper** from an existing codebase or idea
- **Designing and running experiments** to support paper claims
- **Writing or revising** any section of a research paper
- **Preparing for submission** to a specific conference or workshop
- **Responding to reviews** with additional experiments or revisions
- **Converting** a paper between conference formats
- **Writing non-empirical papers** — theory, survey, benchmark, or position papers
- **Designing human evaluations** for NLP, HCI, or alignment research
- **Preparing post-acceptance deliverables** — posters, talks, code releases

## Core Philosophy

1. **Be proactive.** Deliver complete drafts, not questions. Scientists are busy — produce something concrete they can react to, then iterate.
2. **Never hallucinate citations.** AI-generated citations have ~40% error rate. Always fetch programmatically. Mark unverifiable citations as `[CITATION NEEDED]`.
3. **Paper is a story, not a collection of experiments.** Every paper needs one clear contribution stated in a single sentence. If you can't do that, the paper isn't ready.
4. **Experiments serve claims.** Every experiment must explicitly state which claim it supports. Never run experiments that don't connect to the paper's narrative.
5. **Commit early, commit often.** Every completed experiment batch, every paper draft update — commit with descriptive messages. Git log is the experiment history.

### Proactivity and Collaboration

**Default: Be proactive. Draft first, ask with the draft.**

| Confidence Level | Action |
|-----------------|--------|
| **High** (clear repo, obvious contribution) | Write full draft, deliver, iterate on feedback |
| **Medium** (some ambiguity) | Write draft with flagged uncertainties, continue |
| **Low** (major unknowns) | Ask 1-2 targeted questions via `clarify`, then draft |

| Section | Draft Autonomously? | Flag With Draft |
|---------|-------------------|-----------------|
| Abstract | Yes | "Framed contribution as X — adjust if needed" |
| Introduction | Yes | "Emphasized problem Y — correct if wrong" |
| Methods | Yes | "Included details A, B, C — add missing pieces" |
| Experiments | Yes | "Highlighted results 1, 2, 3 — reorder if needed" |
| Related Work | Yes | "Cited papers X, Y, Z — add any I missed" |

**Block for input only when**: target venue unclear, multiple contradictory framings, results seem incomplete, explicit request to review first.

---

## Phase Overview

Eight phases, each detailed in its own reference file. Each reference has the same heading convention: `# Phase N: Title`.

| # | Phase | Goal | Reference |
|---|-------|------|-----------|
| 0 | Project Setup | Establish workspace, identify contribution | [phase0-setup.md](references/phase0-setup.md) |
| 1 | Literature Review | Find papers, gather verified citations (never hallucinate BibTeX) | [phase1-literature.md](references/phase1-literature.md) |
| 2 | Experiment Design | Map claims → experiments, define baselines & evaluation protocol | [phase2-experiment-design.md](references/phase2-experiment-design.md) |
| 3 | Execution & Monitoring | Run reliably, recover from failures, track via cron + journal | [phase3-execution.md](references/phase3-execution.md) |
| 4 | Result Analysis | Statistics, story, figures; write `experiment_log.md` as bridge to writing | [phase4-analysis.md](references/phase4-analysis.md) |
| 5 | Paper Drafting | Narrative principle, sections, LaTeX preamble, TikZ, algorithm2e, latexdiff | [phase5-drafting.md](references/phase5-drafting.md) |
| 6 | Self-Review & Revision | Ensemble + VLM + claim-verification passes; rebuttal writing | [phase6-review.md](references/phase6-review.md) |
| 7 | Submission Preparation | Anonymize, validate, compile, submit; covers Phase 8 + workshop + paper types | [phase7-submission.md](references/phase7-submission.md) |

### Cross-cutting reference docs (used across phases)

> **Note:** Diese cross-cutting reference docs sind als zukünftige Erweiterungen geplant. Die Inhalte zu writing quality, citations, checklists, reviewer guidelines, experiment patterns, autoreason, human evaluation, paper types und sources sind aktuell in den jeweiligen Phase-Referenzen (`references/phaseN-*.md`) inline eingebettet. Beim späteren Ausbau können diese Docs aus den Phase-Files extrahiert werden.

**LaTeX templates** live in `templates/` (NeurIPS 2025, ICML 2026, ICLR 2026, ACL, AAAI 2026, COLM 2025). See templates/README.md for compilation setup.

---

## Common Pitfalls (Top Warnings)

> **Never hallucinate citations.** AI-generated BibTeX has ~40% error rate. Always fetch via DOI programmatically and mark unverifiable ones as `[CITATION NEEDED]`.

> **Every experiment must map to a claim.** No orphan experiments. If you can't point to the paper claim it supports, don't run it.

> **Read papers as a story, not a list.** Related work is grouped by methodology, not paper-by-paper. ("One line of work uses X [refs] whereas we use Y because...")

> **Never copy LaTeX preambles between templates.** When converting venues, start fresh from the target template and copy only content.

> **Commit experiments and drafts continuously.** Git log is the experiment history. Use `experiment_journal.jsonl` to track the reasoning tree (hypothesis → result → next-step), not just file changes.

> **Simulated reviews need negative bias.** LLMs default to positive; explicitly instruct reviewers to flag weaknesses and not give "the benefit of the doubt."

> **Verify every claim in the draft against the actual result files.** Delegate this to a fresh sub-agent with no shared memory to prevent confirmation bias.

See [references/phase6-review.md](references/phase6-review.md) for the full review protocol and [references/phase4-analysis.md](references/phase4-analysis.md) for handling negative/null results.

---

## Hermes Agent Integration

This skill is designed for the Hermes agent — uses `terminal`, `process`, `execute_code`, `read_file`/`write_file`/`patch`, `web_search`/`web_extract`, `delegate_task`, `todo`, `memory`, `cronjob`, `clarify`, and `send_message`.

**Supersedes `ml-paper-writing`** (all its content plus the experiment/analysis pipeline and autoreason methodology).

### Related skills

| Skill | When to Use | How to Load |
|-------|-------------|-------------|
| **arxiv** | Phase 1: arXiv search, BibTeX, Semantic Scholar | `skill_view("arxiv")` |
| **subagent-driven-development** | Phase 5: parallel section writing + 2-stage review | `skill_view("subagent-driven-development")` |
| **plan** | Phase 0: structured plans before execution | `skill_view("plan")` |
| **qmd** | Phase 1: local knowledge bases (BM25+vector) | `skill_manage("install", "qmd")` |
| **diagramming** | Phase 4-5: Excalidraw architecture diagrams | `skill_view("diagramming")` |
| **data-science** | Phase 4: Jupyter live kernel for analysis | `skill_view("data-science")` |

### Standard patterns

**Parallel section drafting** — each `delegate_task` runs as a **fresh subagent with no shared context**; include all needed info in the prompt.

**Experiment monitoring loop:**
```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<msg>' && git push")
→ send_message("Experiment complete: <summary>")
```

**Session startup:** `todo("list")` → `memory("read")` → `git log --oneline -10` → `ps aux | grep python` → `ls results/ | tail -20` → report status.

**Notify vs `[SILENT]`**: notify on experiment completion / unexpected finding / draft ready / deadline approaching; stay `[SILENT]` for in-progress experiments and routine no-change checks.

**Use `patch` (not `write_file`)** for targeted edits to large .tex files.

---

## Reviewer Evaluation Criteria

| Criterion | What They Check |
|-----------|----------------|
| **Quality** | Technical soundness, well-supported claims, fair baselines |
| **Clarity** | Clear writing, reproducible by experts, consistent notation |
| **Significance** | Community impact, advances understanding |
| **Originality** | New insights (doesn't require new method) |

**NeurIPS 6-point scale:** 6 = Strong Accept → 1 = Strong Reject. See references/reviewer-guidelines.md for detailed guidelines and rebuttal strategies.

---

## Common Issues (Quick Index)

| Issue | Where to fix it |
|-------|---------|
| Abstract too generic | [phase5 § Step 5.1](references/phase5-drafting.md) — 5-sentence formula |
| Introduction exceeds 1.5 pages | [phase5 § Step 5.3](references/phase5-drafting.md) |
| Experiments lack explicit claims | [phase4 § Step 4.3](references/phase4-analysis.md) |
| Reviewers find paper hard to follow | [phase5 § Writing Style](references/phase5-drafting.md) — Gopen & Swan, signposting |
| Missing statistical significance | [phase4 § Step 4.2](references/phase4-analysis.md) + experiment-patterns.md |
| Scope creep in experiments | [phase2 § Step 2.1](references/phase2-experiment-design.md) — claims-to-experiments map |
| Paper rejected, need to resubmit | [phase7 § Step 7.7](references/phase7-submission.md) — never reference prior review |
| Missing broader impact | [phase5 § Step 5.10](references/phase5-drafting.md) |
| Human eval criticized as weak | [phase2 § Step 2.5](references/phase2-experiment-design.md) + human-evaluation.md |
| Reviewers question reproducibility | [phase7 § Step 7.10](references/phase7-submission.md) — code packaging |
| Theory paper lacks intuition | paper-types.md § Theory |
| Results are negative/null | [phase4 § Step 4.3](references/phase4-analysis.md) — handling negative results |

---

## Key External Sources

**Writing:** [Neel Nanda](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) · [Sebastian Farquhar](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) · [Gopen & Swan](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) · [Lipton](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) · [Perez](https://ethanperez.net/easy-paper-writing-tips/)

**APIs:** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) · [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) · [arXiv](https://info.arxiv.org/help/api/basics.html)

**Venues:** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) · [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) · [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) · [ACL](https://github.com/acl-org/acl-style-files)
