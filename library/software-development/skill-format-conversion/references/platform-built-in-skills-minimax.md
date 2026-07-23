# MiniMax.io (M3 Agent Team) — Built-in Skill Inventory

**Discovered:** 2026-07-07 via web research + platform UI explore
**Purpose:** Layer-1 exclusion filter — don't convert Hermes skills that MiniMax.io already has
**Source:** https://agent.minimax.io/ — Skill Hub sidebar

> This is a snapshot. MiniMax.io's skill library grows. Re-inventory before every conversion session.

---

## 🏆 Design & Visual Skills (21 discovered)

| Built-in Skill | Trigger | What it does | Hermes Equivalent to SKIP |
|---|---|---|---|
| `ui-ux-pro-max` | "UI/UX design", "color palette" | 50+ styles, 97 palettes, 57 fonts, 9 tech stacks | ui-color-system (partial) |
| `landing-page-builder` | "landing page", "high-end web page" | High-end landing page generator | claude-design (partial) |
| `pptx-generator` | "PowerPoint", "PPTX" | Professional PPT via PPTX/JS + markitdown | — |
| `mckinsey-presentation-generator` | "consulting deck", "MCK style" | Data-rich McKinsey-style decks | — |
| `html-presentation-generator` | "HTML PPT", "web slide" | Multi-page HTML-PPT with PDF/PPTX export | — |
| `visual-content-generator` | "infographic", "chart" | Charts, infographics, dashboards, timelines | architecture-diagram (partial) |
| `ui-ux-designer` | "design system", "wireframe" | Design systems, a11y audits, HTML/CSS impl | ui-design-system (partial) |
| `interactive-visualization-architect` | "interactive 3D", "WebGL" | 3D/2D Web demos with drag controls + share link | p5js (partial) |
| `image-craft` | "AI image prompt", "stylish image" | Curated image-gen prompts (figures, scenes, products) | video-prompting (partial) |
| `icon-maker` | "icon", "logo concept" | AI icons in 20+ styles | — |
| `minimax-pdf` | "PDF erstellen" | Token design system, 15 doc types, cover patterns | — |
| `minimax-docx` | "Word-Dokument", "DOCX" | DOCX via OpenXML SDK (.NET) | — |
| `minimax-xlsx` | "Excel", "Spreadsheet" | XLSX/XLSM/CSV/TSV | — |

## 🛠️ Code & Engineering Skills (~30 discovered)

| Built-in Skill | Trigger | What it does |
|---|---|---|
| `app-builder` | "Full-Stack App", "Build app" | Web apps + APIs + Mobile with auth+DB+Stripe |
| `mini-coder-max` | "autonomous coding agent" | Truly autonomous coding with multi-subagents |
| `senior-software-engineer` | "wie senior engineer" | Engineering principles for production code |
| `prd-assistant` | "PRD", "Product Requirements" | Full PRD + HTML prototype |
| `seo-geo-optimization-expert` | "SEO", "GEO" | SEO + Generative Engine Optimization |
| `deep-research-agent` | "deep research", "100+ sources" | 100+ sources verification |
| `knowledge-digest` | "PDF → Lernmaterial" | Multimodal learning materials from PDF/textbook |
| `industry-research-report-writer` | "market research" | Professional research reports |
| `social-media-trend-search` | "trends" | Cross-platform social media trend monitoring |
| `topic-tracker` | "trend topics" | Topic tracking + content generation |
| `b2b-lead-generation` | "find leads", "competitor analyze" | 5-stage lead-gen pipeline |

## 🎛️ Multi-Modal Core Tools (Layer 2 — NOT skills)

These are platform primitives, not installable skills. Never package an equivalent Hermes skill:

| Capability | Backend | Details |
|---|---|---|
| **Text-to-Image** | FAL.ai · FLUX 2 Klein 9B | landscape/square/portrait, up to 9 reference images, image-to-image editing |
| **Video Generation** | FAL · PixVerse v6 | 1-15s, 360p-1080p, 16:9/9:16/1:1/4:3/3:4/3:2/2:3, optional audio |
| **Text-to-Speech** | Edge TTS (default) / OpenAI / MiniMax | — |
| **Speech-to-Text** | OpenAI Whisper | — |
| **Vision Analyze** | Multimodal M3 | Inline image analysis with context questions |
| **Web Search** | Browser | Search-engine queries |
| **Web Extract** | Firecrawl | Markdown from URLs, up to 5 URLs per call |
| **Browser Automation** | Headless browser | Click, type, snapshot, scroll, vision screenshot |
| **MCP Client** | Built-in | Figma MCP, Canva MCP, Adobe Express MCP, Notion MCP, GitHub MCP, Maps MCP, Slack MCP, MiniMax MCP |

## 🔍 Discovery Method (for re-inventory)

```python
import requests
from bs4 import BeautifulSoup

# Option 1: MiniMax.io skill hub API (if authenticated)
# Check: https://agent.minimax.io/api/skills
# Or scrape: https://agent.minimax.io/skills

# Option 2: Ask the platform directly
# In chat: "List all built-in skills you have available"
# MiniMax.io M3 will list what's in its skill hub

# Option 3: Manual explore
# Sidebar → Skills → "+" → Browse Skill Hub
# Screenshot + vision_analyze each category page
```

## 🧹 Exclusion Application

Always apply against both names and `display-name` fields:

```python
BUILT_IN_NAMES = {
    "ui-ux-pro-max", "landing-page-builder", "pptx-generator",
    "mckinsey-presentation-generator", "html-presentation-generator",
    "visual-content-generator", "ui-ux-designer",
    "interactive-visualization-architect", "image-craft",
    "icon-maker", "minimax-pdf", "minimax-docx", "minimax-xlsx",
    "app-builder", "mini-coder-max", "senior-software-engineer",
    "prd-assistant", "seo-geo-optimization-expert",
    "deep-research-agent", "knowledge-digest",
    "industry-research-report-writer",
    "social-media-trend-search", "topic-tracker",
    "b2b-lead-generation",
}

# Fuzzy match: also check display names
BUILT_IN_DISPLAY_NAMES = {
    "UI/UX Pro Max", "Landing Page Builder", "PPTX Generator",
    "McKinsey Presentation Generator", "HTML Presentation Generator",
    "Visual Content Generator", "UI/UX Designer",
    "Interactive Visualization Architect", "Image Craft",
    "Icon Maker", "MiniMax PDF", "MiniMax DOCX", "MiniMax XLSX",
    "App Builder", "Mini Coder Max", "Senior Software Engineer",
    "PRD Assistant", "SEO/GEO Optimization Expert",
    "Deep Research Agent", "Knowledge Digest",
    "Industry Research Report Writer",
    "Social Media Trend Search", "Topic Tracker",
    "B2B Lead Generation",
}
```

## ⚠️ Curation Notes

- This is a **snapshot** from 2026-07-07. MiniMax.io adds skills to their hub regularly — re-inventory before each conversion session.
- MiniMax.io M3 (v3.0.47) has **Computer Use temporarily disabled** due to compatibility issues. Expected back in v3.0.48+.
- Skills with `minimax-` prefix are proprietary — no Hermes equivalent should ever map to them.
- The `app-builder` + `mini-coder-max` suite covers full-stack development. Hermes coding skills (claude-coder, systematic-debugging, test-driven-development) remain additive because they target specific workflows not covered by MiniMax's general-purpose equivalents.
