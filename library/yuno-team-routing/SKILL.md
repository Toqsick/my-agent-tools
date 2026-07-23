---
name: yuno-team-routing
description: "Use when user asks which Yuno team agent should handle a task, how to decompose a multi-domain request, or how to hand work between the seven specialized agents. NOT for performing the task itself or maintaining a generic organization chart. Applies the authoritative trigger-to-agent routing table, ownership rules, handoff patterns, and anti-patterns."
version: 1.0.0
author: Bratan (Yuno via Owl Alpha)
license: MIT
platforms:
- linux
- macos
- windows
agent: Yuno
routing_source: ~/Downloads/team-roster.md
trigger-words:
- routing
- agent team
- which agent
- wer ist zuständig
- route to
metadata:
  hermes:
    tags:
    - orchestration
    - multi-agent
    - routing
    - team
    related_skills:
    - multi-agent-master-workflow
    - workflow-template
    - multi-agent-orchestration
lane: koenigin
reasoning_effort: low
trigger_keywords: ['the', 'how', 'yuno-team-routing', 'which', 'yuno']
keywords: ['agent', 'task', 'patterns', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['yuno-team-orchestrator', 'skill-tool-computer-use-routing']
---


# Yuno Team Routing — Single Source of Truth

> Authoritative routing spec for all 7 agents in Yuno's team.
> Source: `~/Downloads/team-roster.md` (vom 2026-07-07)

## 🎯 Zweck

Wenn ein User-Task reinkommt und unklar ist welcher Agent zuständig ist → dies ist die Tabelle der Wahrheit. Single-domain Tasks gehen direkt. Multi-domain Tasks decompose.

## 🧭 Roster

| Agent | Role | Owned Skills (Highlights) |
|---|---|---|
| **Yuno** | Root · Kawaii · Orchestration | 247 Hermes-Skills (full access), Multi-Agent-Cluster |
| **Engineer** | Builder · Full-Stack Code | claude-coder, claude-coding-specialist, systematic-debugging, github-workflow, ... |
| **Researcher** | Finder · Deep Research | arxiv, notebooklm-bridge, llm-wiki, firecrawl-web, research-tools, ... |
| **Designer** | Visual · UI/UX | ui-factory, ui-design-system, html-artifact, popular-web-designs, anime-design, ... |
| **Analyst** | Numbers · Data & Modeling | mlops-suite, vllm, huggingface-hub, w&b, llama-cpp, rag-pipeline-python, ... |
| **Writer** | Words · Long-Form Content | system-documentation, pr-body-standards, humanizer, pdf/nano-pdf, powerpoint, ... |
| **Verifier** | Gate · Adversarial QA | critic-gate, security-code-checker, output-validator, verify-before-fix, ... |

## 🚦 Routing-Regeln

| Trigger-Phrase | → Agent |
|---|---|
| `build` / `fix` / `refactor` / `review code` / `debug` | **Engineer** |
| `find me X` / `what's the latest` / `research` / `compare` | **Researcher** |
| `design` / `landing page` / `logo` / `UI` / `UX` | **Designer** |
| `spreadsheet` / `model` / `calculate` / `chart` / `data` | **Analyst** |
| `write a doc` / `draft a proposal` / `compose` / `long copy` | **Writer** |
| `verify` / `audit` / `is this done` / `check this` | **Verifier** |
| Unklar / Multi-Domain | **Yuno** (decompose → hand off → verify → synthesize) |

## 📋 Workflow

1. **Read user request.** Identify the dominant domain (Code / Research / Visual / Data / Long-Form / QA).
2. **Match against table above.** Single-domain → route to the one agent. Multi-domain → decompose.
3. **If off-scope for current agent:** say "this is X's territory, not mine" + hand back to Yuno.
4. **If multi-domain:** Yuno decomposes → dispatches → each worker runs in their agent context → Verifier gates the final.

## 🔀 Hand-off Patterns

- **Engineer → Yuno**: design decision needed, scope ballooning, blocked on missing context.
- **Researcher → Yuno**: claim verification needed across multiple workers.
- **Designer → Researcher**: when brand context (competitors, references) is needed.
- **Designer → Writer**: when copy is needed for the design.
- **Analyst → Designer**: when data visualization is the deliverable.
- **Writer → Researcher**: when fact-check needed.
- **Writer → Designer**: when visual layout is needed.
- **Any → Verifier**: when quality gate is needed before user sees the result.

## 🐝 Anti-Patterns

- **Don't try to do another agent's job.** If the task is Writer's territory and you're Engineer, say so.
- **Don't skip Verifier on multi-domain tasks.** Final gate belongs to Verifier.
- **Don't synthesize without domain specialist input.** Yuno is the conductor, not the orchestra.

## 🔍 Cross-Skill Integration

Jeder Top-Skill hat im YAML-Frontmatter ein `agent:`-Tag der den owning Agent nennt. Diese Spec ist die Single Source of Truth für die Tag-Werte.

```yaml
# Beispiel: claude-coder/SKILL.md
agent: "Engineer"
```

Beim Routing entscheidet das `agent:`-Feld der aufgerufenen Skills ob das im Scope liegt.

## 📂 Where this lives

- **Source:** `~/Downloads/team-roster.md` (12.5 KB Spec, vom 2026-07-07)
- **Buildable Skill** in Hermes: `~/.hermes/skills/yuno-team-routing/SKILL.md` (this file)
- **In MiniMax.io Bundles:** included in all 5 bundles via copy
- **Updates:** wenn `team-roster.md` ändert, regeneriere diese Spec

## 🐝 Verifier's Quality Bar

Bevor dieser Skill als "done" gilt, prüft Verifier:
- [ ] Routing-Tabelle ist 1:1 mit `team-roster.md` synchronisiert
- [ ] Keine Skill-Frontmatter widerspricht der Tabelle (verifiziere alle 55 `agent:`-Tags)
- [ ] Workflow-Description ist klar (single-domain vs multi-domain)
- [ ] Hand-off-Patterns sind explizit (Yuno re-route bei off-scope)
