# Skill-Lane-Registry — Session-Detail 2026-07-02

**Status:** in produktiver Nutzung, 87 Skills mit `lane:`-Frontmatter
**Struktur:** 5 Rollen (Königin, Worker Heavy, Worker Vision, Worker Flash, Gate)

## Rollendefinition

| Rolle | Zielprofil | Standardmodell | Kosten/M Input | Reasoning |
|---|---|---|---|---|
| Königin | main | deepseek/deepseek-v4-pro | 0.44 | xhigh |
| Worker Heavy | yuno-coder | z-ai/glm-5.2 | 0.93 | xhigh |
| Worker Vision | yuno-vision | minimax/minimax-m3 | 0.30 | xhigh |
| Worker Flash | yuno-flash | stepfun/step-3.7-flash:free | 0.00 | high |
| Gate | yuno-coder | z-ai/glm-5.2 | 0.93 | xhigh |

## Verkürzte Skill-Zuordnung

### Königin
- writing-plans
- multi-agent-research
- research-orchestration
- planning

### Worker Heavy
- simplify-code
- security-code-checker
- github-code-review
- systematic-debugging
- python-debugpy
- llm-evaluation-troubleshooting
- bash-script-audit
- critic-gate
- rag-pipeline-python

### Worker Vision
- architecture-diagram
- html-artifact
- pixel-art
- p5js
- manim-video
- ascii-video
- touchdesigner-mcp
- excalidraw
- popular-web-designs
- ui-factory
- ui-design-system
- ui-dashboard
- ui-component-library
- ui-color-system
- design-md

### Worker Flash
- research-tools
- codebase-inspection
- ocr-and-documents
- media-tools
- gif-search
- firecrawl-web
- map/Red-Tooling bei niedriger Stufe
- web-archive-research

### Gate
- requesting-code-review
- humanizer
- security-code-checker
- critic-gate
- output-validator
- test-driven-development

## Applied-Frontmatter-Schema

```yaml
---
lane:
- worker-heavy
- gate
reasoning_effort: xhigh
---
```

**Pitfall:** Multi-Lane-Skills sind explizit erlaubt. Trage sie in `skill_lanes` unter beiden Rollen ein, sonst wirkt nur eine Route.

## Subagent-Routing-Konvention

`delegation.model = z-ai/glm-5.2`
`delegation.reasoning_effort = xhigh`

Subagent erbt **nicht mehr** vom Main. Für Vision-Delegation immer `--profile yuno-vision` setzen.

## Praktischer Aufruf

```bash
hermes chat --profile yuno-coder -s simplify-code -q "Refactor..."
hermes chat --profile yuno-vision -s architecture-diagram -q "Mach Diagramm..."
hermes chat --profile yuno-flash -q "Parse 1000 Logs..."
```

## Pitfalls

1. Skill-Duplikate in `skills/`-Bundle verhindern eindeutigen Load.
2. `hermes config set` überschreibt Sibling-Keys, keine verschachtelten Blöcke.
3. Subagent-Modell muss explizit `delegation.model` gesetzt sein, sonst greift Free-Tier.
4. Schritt-Fun Free hat 429-Bursts, nicht als alleinige Fallback-Kette nutzen ohne zweiten Fallback.
5. Lane-Profiles brauchen `PURPOSE.md` neben `config.yaml`, sonst sind sie nicht sicher unterscheidbar.
6. `security-code-checker` war Duplikat: `/software-development/...` behalten, `/skills/...` archivieren.

## Offen

- Curator-Lauf für neue `lane:`-Metadaten
- Skill `nous-multi-lane-routing` mit Registry mergen falls existent
- End-to-End-Test über `delegate_task` statt nur CLI-Profil-Aufruf
