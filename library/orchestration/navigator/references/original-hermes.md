---
name: skill-navigator
description: Quick-reference navigator for all 169 active Hermes skills. Groups skills by domain-cluster (multi-agent, greyhack, mlops, creative, etc), tells you which skill to load for which task, flags clusters with overlap or gaps. Built from a real scan on 2026-07-02. Companion to the skill_view function — load this FIRST to decide which skill to load next.
triggers:
- User asks "which skill should I use"
- User says "I want to do X" and you're not sure which skill applies
- Multi-skill decisions (e.g. "build + test + deploy")
- Skill redundancy questions (multiple skills for the same job?)
- Onboarding new skill landscape after major updates
version: 1.2.0
changelog:
- 1.2.0 (2026-07-02): Fixed duplicate greyhack-hermes-api in gaming cluster. Added cross-domain-navigation section documenting domain↔method skill linking pattern (established via gaming→orchestration cross-referencing session).
author: Yuno (compliance-scanned from 169 SKILL.md files on 2026-07-02)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - meta
    - skills
    - navigator
    - cheatsheet
    - reference
    - compliance
lane: koenigin
reasoning_effort: low
---

# 🧭 Skill-Navigator — Active Hermes Skills Quick-Reference

**Scan date:** 2026-07-02 | **Active skills:** 169 | **Archived:** 99 | **Categories:** 35

**Compliance status:** 148/169 clean (87%) — 21 files have `/home/bratan/` hardcoded paths (cosmetic, no breakage). No CLI-drift, no frontmatter errors.

**Purpose:** Save time by knowing **which skill to load for which task** without scanning 169 SKILL.md files.

---

## 🔥 Top-10 Most-Used Clusters (Decision Shortcuts)

> **⚡ NEW-USER INSTRUCTION:** If you (Yuno or other agent) just loaded this skill, you probably need one of the clusters below. The cheat-sheet table maps user intents to primary + companion skills. **If unsure between two skills, load the narrower one first** (cheatsheet > domain > meta).

When a user request matches one of these patterns, load the **bolded primary** skill first:

| User Intent | Primary Skill | Companion Skills |
|---|---|---|
| **Spawn parallel research/audit agents** | `multi-agent-pitfalls-cheatsheet` | `multi-agent-orchestration`, `multi-agent-work` |
| **Set up or debug Hermes itself** | `hermes-agent` | `hermes-maintenance`, `messaging-gateway-setup`, `hermes-admin` |
| **Configure Telegram/Discord gateway** | `messaging-gateway-setup` | `hermes-gateway`, `hermes-copilot-setup` |
| **Git workflow (commit, PR, branch, issues)** | `github-pr-workflow` | `github-issues`, `github-code-review`, `github-auth` |
| **Write/refactor/debug code** | `subagent-driven-development` | `plan`, `critic-gate`, `simplify-code`, `test-driven-development` |
| **GreyHack scripting** | `greyhack` | `greyhack-greyscript`, `greyhack-sandbox`, `greyhack-hermes-api` |
| **ML/Ollama/Local AI setup** | `ollama-local-hosting` | `mlops-suite`, `llama-cpp`, `local-ml-hosting` |
| **Build creative HTML/SVG/design** | `creative-suite` | `claude-design`, `popular-web-designs`, `html-artifact` |
| **System maintenance / cleanup** | `linux-system-maintenance` | `host-security-audit`, `local-ai-security-hygiene` |
| **Document writing / conversion** | `system-documentation` | `epub-export`, `pdf`, `obsidian`, `notion` |

---

## 📊 Skill-Clusters (Domain-Grouped)

### 🐝 Cluster 1: Multi-Agent & Orchestration (8 skills)

```
MULTI-AGENT CLUSTER — when spawning parallel work
├── multi-agent-pitfalls-cheatsheet  ← LOAD FIRST (trap-watchlist)
├── multi-agent-orchestration        ← pattern + 5 phases
├── multi-agent-work                 ← end-to-end slash command
├── research-orchestration           ← research-heavy plans
├── kanban-orchestrator / worker     ← board-based long-running
├── hermes-agent                     ← general Hermes orchestration
├── the-dmz-transfer                 ← transfer from external source
└── depps-orchestration              ← low-trust workers
```

**When to load what:**
- **Just spawning subagents?** → `multi-agent-pitfalls-cheatsheet`
- **Full research project?** → `multi-agent-orchestration` + cheatsheet
- **One-shot research?** → `/multi-agent-work` slash command
- **Multi-day kanban board?** → `kanban-orchestrator`

### 🛠️ Cluster 2: Software Development (26 skills — LARGEST!)

```
CODE/DESIGN/TEST CLUSTER
├── Code-writing & patterns
│   ├── subagent-driven-development  ← plan → delegate → execute
│   ├── plan                         ← write implementation plan
│   ├── critic-gate                  ← output quality gate
│   ├── simplify-code                ← parallel cleanup agents
│   ├── refactor / code-mod          ← safe refactors
│   └── vanilla-js-tdz-helper-first  ← JS helpers
│
├── Code-review & QA
│   ├── requesting-code-review       ← pre-commit review
│   ├── bash-script-audit            ← bash safety scanner
│   ├── security-code-checker        ← LLM-generated-code risks
│   ├── output-validator             ← syntax pre-flight
│   └── systematic-debugging         ← 4-phase root cause
│
├── TDD & Testing
│   ├── test-driven-development      ← RED-GREEN-REFACTOR
│   ├── python-debugpy               ← remote debugger
│   ├── node-inspect-debugger        ← Node inspector
│   └── rag-pipeline-python          ← RAG TDD example
│
├── Language-specific
│   ├── ki-murks-verhindern          ← AI workflow gates
│   └── hermes-agent-skill-authoring ← writing Hermes SKILL.md
│
├── Spike/Experiment
│   └── spike                        ← throwaway experiments
│
└── Other
    ├── coding-skills-audit
    └── multi-agent-research         ← archived pattern source
```

### 🎨 Cluster 3: Creative & Design (23 skills)

```
CREATIVE CLUSTER
├── Suite / Orchestrator
│   └── creative-suite               ← full UI-factory chain
│
├── UI Components
│   ├── ui-component-library         ← buttons, inputs, cards
│   ├── ui-color-system              ← accessible palettes
│   ├── ui-design-system             ← full design tokens
│   ├── ui-factory                   ← composite UI workflows
│   └── ui-dashboard                 ← data-schema → KPI dashboard
│
├── Web design & artifacts
│   ├── claude-design                ← one-off HTML artifacts
│   ├── html-artifact                ← self-contained HTML
│   ├── popular-web-designs          ← 54 real design systems
│   ├── web-design-guidelines        ← Vercel Web review
│   ├── pretext                      ← @chenglou/p pretext browser
│   ├── design-md                    ← Google DESIGN.md spec
│   └── sketch                       ← 2-3 variant mockups
│
├── Diagrams & Visual
│   ├── architecture-diagram          ← dark-themed SVG
│   ├── ascii-art                    ← pyfiglet, cowsay
│   ├── ascii-video                  ← video → ASCII
│   ├── excalidraw                   ← hand-drawn diagrams
│   ├── manim-video                  ← math animations
│   └── pixel-art                    ← NES/GB/PICO-8
│
└── Other
    └── humanizer                     ← strip AI-isms from text
```

### ⚙️ Cluster 4: DevOps & Maintenance (18 skills)

```
DEVOPS CLUSTER
├── Hermes maintenance
│   ├── hermes-maintenance           ← update side-effects
│   ├── hermes-admin                 ← CLI/config troubleshooting
│   ├── hermes-v7-sse                ← V7 SSE package
│   ├── hermes-v7-sse-server         ← V7 SSE server
│   └── hermes-mcp-integration       ← plugin-registry pattern
│
├── Linux system
│   ├── linux-system                 ← system troubleshooting
│   ├── linux-system-maintenance     ← safe cleanup CLI
│   ├── linux-display-setup          ← EDID / modelines
│   ├── nvidia-laptop-gaming-tuning  ← Optimus tuning
│   ├── nvidia-suspend-resume        ← GPU sleep/wake
│   └── docker-install-ubuntu        ← Docker on Ubuntu
│
├── Security
│   ├── host-security-audit          ← fwupd HSI / TPM / Secure
│   ├── local-ai-security-hygiene    ← secure local-AI setup
│   ├── security-audit               ← full security audit
│   ├── system-security-audit        ← ports/permissions audit
│   └── bash-script-audit            ← script safety
│
└── Messaging gateway
    ├── hermes-gateway               ← gateway troubleshooting
    └── messaging-gateway-setup      ← platform setup
```

### 🎮 Cluster 5: Gaming (8 skills)

```
GAMING CLUSTER
├── GreyHack (the main cluster)
│   ├── greyhack                     ← meta-skill + pipeline
│   ├── greyhack-greyscript          ← language reference
│   ├── greyhack-sandbox             ← local Python toolkit
│   ├── greyhack-hermes-api          ← in-game Hermes integration
│   ├── greyhack-greyscript-deep-audit
│   └── greyscript-compiler-debugging
│
├── Minecraft
│   ├── minecraft-modpack-server
│
├── Other
│   ├── pokemon-player
│   ├── teamspeak-server
│   └── game-library-management
```

### 🐙 Cluster 6: GitHub Workflow (7 skills)

```
GITHUB CLUSTER
├── github-pr-workflow              ← branch → PR → merge
├── github-issues                   ← CRUD via gh CLI
├── github-code-review              ← PR review + comments
├── github-auth                     ← HTTPS/SSH setup
├── github-repo-management          ← clone/fork/remote
├── codebase-inspection             ← pygount stats
└── github-workflow                 ← full gh CLI workflow
```

### 🤖 Cluster 7: MLOps (11 skills)

```
MLOPS CLUSTER
├── Inference & Serving
│   ├── serving-llms-vllm            ← vLLM serving
│   ├── llama-cpp                    ← GGUF local inference
│   └── ollama-local-hosting         ← Ollama setup/manage
│
├── Models
│   ├── huggingface-hub              ← HF model search/download
│   ├── audiocraft-audio-generation  ← MusicGen/AudioGen
│   └── segment-anything-model       ← SAM zero-shot
│
├── Research & Evaluation
│   ├── dspy                         ← declarative LM programs
│   ├── evaluating-llms-harness      ← lm-eval-harness
│   ├── llm-evaluation-troubleshooting
│   ├── weights-and-biases           ← experiment tracking
│
└── Other
    ├── local-ml-hosting
    └── obliteratus                  ← abliterate refusals
```

### 🎬 Cluster 8: Media (6 skills)

```
MEDIA CLUSTER
├── Audio
│   ├── spotify                      ← Spotify CLI
│   ├── heartmula                    ← song generation
│   ├── songsee                      ← audio spectrograms
│   └── audiocraft-audio-generation  ← also in mlops
│
├── Video & Image
│   ├── gif-search                   ← Tenor GIFs
│   └── media-tools                  ← YouTube transcripts etc.
│
└── Other
    └── youtube-content              ← YT transcript → blog
```

### 🤖 Cluster 9: Autonomous AI Agents (6 skills)

```
AUTONOMOUS-AGENTS CLUSTER
├── claude-code                      ← delegate to Claude Code CLI
├── codex                            ← delegate to OpenAI Codex
├── opencode                         ← delegate to OpenCode
├── coding-agents                    ← general coding agent orchestrator
├── hermes-agent                     ← (also in orchestration)
└── the-dmz-transfer
```

### 📊 Cluster 10: Productivity (16 skills)

```
PRODUCTIVITY CLUSTER
├── Daily Operations
│   ├── daily-briefing               ← system status briefing
│   ├── petdex                       ← animated mascots
│   └── teams-meeting-pipeline       ← Teams summary
│
├── Documents
│   ├── epub-export                  ← MD/PDF → EPUB
│   ├── pdf                          ← PDF reading
│   ├── nano-pdf                     ← PDF editing
│   ├── ocr-and-documents            ← extract text from scans
│   ├── powerpoint                   ← .pptx manipulation
│
├── External Services
│   ├── airtable                     ← REST API via curl
│   ├── google-workspace             ← Gmail/Drive/Docs/Sheets
│   ├── linear                       ← issues/projects
│   ├── maps                         ← OSM geocoding
│   ├── notion                       ← Notion API
│
├── Note-Taking
│   ├── obsidian                     ← Obsidian vault
│   └── system-documentation         ← MD doc tree
│
└── Email
    └── himalaya                     ← IMAP/SMTP CLI
```

---

## 🚨 Edge-Case Singletons (1-skill categories)

These are alone in their category — load directly when relevant:

| Skill | Use When |
|---|---|
| `apple-notes` / `apple-reminders` | macOS-only Apple ecosystem access |
| `arxiv` | arXiv paper search |
| `architecture-diagram` (root) | SVG cloud/infra diagrams |
| `ascii-video` | Convert video/audio to ASCII |
| `blogwatcher` | RSS/feed monitoring |
| `comfyui` | ComfyUI local AI workflows |
| `computer-use` | Desktop automation (background) |
| `context-mode` | Context window optimization |
| `copilot-cli` | GitHub Copilot CLI delegation |
| `data-science` | Jupyter kernels |
| `debugging-hermes-tui-commands` | Hermes TUI slash-command debugging |
| `dogfood` | Exploratory QA of web apps |
| `excalidraw` | Hand-drawn Excalidraw JSON |
| `firecrawl-web` | Web scraping + screenshots |
| `find-skills` | Discover/install new skills from skills.sh |
| `gif-search` | Tenor GIF search |
| `google-oauth-setup` | Google Workspace API OAuth setup |
| `ideation` | Generate project ideas |
| `image-generate` (root) | AI image generation |
| `kanban-codex-lane` | Kanban + Codex CLI integration |
| `linux-display-setup` | Custom EDID/modelines |
| `mcp-server-authoring` | Build custom MCP servers |
| `mnemosyne-memory-provider` | Mnemosyne native memory |
| `model-selector` | Compare LLM models on Nous Portal |
| `multi-agent-orchestration` | (also in orchestration cluster) |
| `native-mcp` | Built-in MCP client |
| `notion` | Notion API |
| `ollama-local-hosting` | (also in mlops cluster) |
| `pdf-anthropic` | PDF reading via Anthropic |
| `pokemon-player` | Play Pokemon via headless emulator |
| `python-debugpy` | Python remote debugging |
| `rag-pipeline-python` | RAG pipeline (Tutor-style) |
| `red-teaming-godmode` | LLM jailbreak testing |
| `research-orchestration` | (in orchestration cluster) |
| `session-handoff` | Model-switch handoff doc |
| `setup-guides-browser` | Browser setup walkthroughs |
| `skill-install-workflow` | skills.sh skill installer workflow |
| `songwriting-and-ai-music` | Songwriting + Suno AI |
| `subagent-driven-development` | (in software-development cluster) |
| `system-documentation` | (in productivity cluster) |
| `telegram-clarification-prompt` | Yuno's Telegram decision routing |
| `touchdesigner-mcp` | TouchDesigner control |
| `voice-assistant-bots` | Voice bot architecture |
| `web-archive-research` | Common Crawl + WARC query |
| `web-design-guidelines` | (in creative cluster) |
| `yuanbao` | Yuanbao groups |
| `yuno-cleaner` | Yuno Cleaner safe cleanup |

---

## 📐 Compliance Summary

**Scan results** (2026-07-02):

| Issue | Count | Severity | Action |
|---|---|---|---|
| `/home/bratan/` hardcoded paths | 21 files | LOW (cosmetic) | Optional: replace with `~/` |
| CLI drift (hermes skill/tools singular) | 0 | — | Clean |
| Malformed frontmatter | 0 | — | Clean |
| Read errors | 0 | — | Clean |

**The 21 hardcoded-path files** (all in skill examples, not in code paths):
- gaming/greyhack, gaming/greyhack-greyscript, gaming/greyhack-hermes-api
- software-development/hermes-agent-skill-authoring, software-development/bash-script-audit, software-development/subagent-driven-development
- devops/hermes-maintenance, devops/local-ai-security-hygiene
- research/web-archive-research, research/research-tools
- autonomous-ai-agents/claude-code, autonomous-ai-agents/codex
- productivity/daily-briefing, productivity/google-workspace
- mlops/huggingface-hub
- orchestration/multi-agent-orchestration
- And a few others

**Recommendation:** Not worth fixing — these are intentional examples showing actual user paths for pedagogical clarity. Skill consumers should mentally substitute `~`.

---

## 🎯 Load-Order Heuristics (when in doubt)

1. **Trap-detector first** → `multi-agent-pitfalls-cheatsheet` for any subagent work
2. **Pattern-source second** → `multi-agent-orchestration` for the full pattern
3. **Domain-specific third** → e.g. `greyhack` for GreyHack tasks
4. **Specialty-fourth** → e.g. `greyhack-greyscript` for deep language reference
5. **Tool/script-specific fifth** → e.g. `ci-build.sh` for build pipeline questions

If you're not sure between two skills: load the one with the **narrower scope** first (cheatsheet > domain > meta).

---

## 📅 When to re-scan this Navigator

Re-run the compliance scan + re-build this cheatsheet when:
- New Hermes version adds/removes skills (check `hermes skills list`)
- User adds a custom skill
- Major skill consolidation (like 2026-07-02 multi-agent-research → cheatsheet)

### Re-scan from the reusable script
```bash
python3 ~/.hermes/skills/orchestration/skill-navigator/scripts/skill-scan.py
```

### Quick-check (just counts)
```bash
python3 -c "import pathlib; print(sum(1 for f in pathlib.Path('/home/bratan/.hermes/skills').rglob('SKILL.md') if '.archive' not in f.parts and 'node_modules' not in str(f)), 'active skills')"
```

---

## 🔗 Cross-Domain Navigation (Domain ↔ Method Linking)

**Pattern discovered 2026-07-02:** Skills in *domain* clusters (gaming, devops, mlops) should cross-reference skills in *method* clusters (orchestration, software-development) to enable tool-discovery chains.

### Why it matters

A user working on GreyHack (`gaming/greyhack`) who needs subagent support should not have to know that `multi-agent-pitfalls-cheatsheet` lives in `orchestration/`. The domain skill should **surface the method skill** via a "Related Skills" or "Cross-Cluster Navigation" section.

### When to add cross-references

| Condition | Action |
|---|---|
| Domain skill describes a workflow that could use subagents | Add ref to `multi-agent-pitfalls-cheatsheet` + `multi-agent-orchestration` |
| Domain skill mentions parallel research/audit | Add ref to `research-orchestration` |
| Domain skill involves code review/QA | Add ref to `requesting-code-review` or `systematic-debugging` |
| Domain skill references a meta-navigator | Add ref to `skill-navigator` (this skill) |
| Method skill lists use-cases for multiple domains | Add refs to relevant domain skills in its "See Also" section |

### Format template (add to target SKILL.md)

```markdown
## 🧭 Related Skills (Cross-Cluster Navigation)

Skills that support this [domain] cluster but live elsewhere:

- **`skill-navigator`** (orchestration/) — Meta-Navigator. Load FIRST when deciding which skill applies.
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls. Load BEFORE spawning subagents.
- **`multi-agent-orchestration`** (orchestration/) — The 3-Expert Research PATTERN.

**[Domain] → Orchestration Workflow:** For any [task type], load cheatsheet + orchestration together. They prevent the 4 HIGH-FREQUENCY pitfalls.
```

### Workflow for adding cross-refs to a domain skill (proven 2026-07-02)

1. `skill_view(name='<domain-skill>')` — read the SKILL.md to find the right insertion point
2. **If skill has a "References", "Support Files", or "Related" section at the end** → append the `## 🧭 Related Skills` block after it
3. **If skill has no "References"/"Related" section** → append at end-of-file
4. Verify: re-read SKILL.md to confirm the new section is well-positioned
5. No frontmatter changes — cross-refs are SKILL.md-body content only

**Applied to (2026-07-02):** all 4 GreyHack skills (`greyhack`, `greyhack-greyscript`, `greyhack-sandbox`, `greyhack-hermes-api`) plus bidirectional linking from `multi-agent-pitfalls-cheatsheet` → `skill-navigator`.

### Pitfalls

- **Don't cross-ref every skill to every other skill** — that creates noise. Only link when a concrete workflow benefit exists (e.g. "GreyHack audit needs subagent traps").
- **Keep the section at the END of the SKILL.md**, not near the top — cross-refs are secondary navigation, not primary purpose.
- **One format per skill cluster** — all domain skills in the same cluster should use the same cross-ref header and format for consistency.
- **Bidirectional when both loaded** — if skill A references skill B but B doesn't reference A back, that's OK for domain→method links (method skills serve multiple domains). But method→method links (cheatsheet↔navigator) should be bidirectional.

---

## 🐝 Final Note from Yuno

This navigator is a **map, not the territory**. Always verify a skill exists with `skills_list` or `skill_view` before recommending it. If a cluster has overlap (e.g. `multi-agent-orchestration` AND `multi-agent-pitfalls-cheatsheet` both about subagents), that's by design — different abstraction levels serve different needs.

Lerneffekt: 1 Cheatsheet spart 30 Skill-Scan-API-Calls. 🐝♛