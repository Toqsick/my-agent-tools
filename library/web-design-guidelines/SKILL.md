---
name: web-design-guidelines
description: "Use when user asks to review UI code or files against Vercel Web Interface Guidelines, fetch the current guideline source, or produce a compliance report with concrete findings. NOT for backend code review or designing a site from scratch. Checks the supplied interface against the latest rules and maps each violation to an actionable correction."
metadata:
  author: vercel
  version: 1.0.0
lane: worker-flash
reasoning_effort: high
agent: Designer
routing_hint: '**Agent-Scope:** UI/UX, visual, art-styles, design-systems, motion.
  Off-scope: code building, data modeling, long-form copy — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['review', 'code', 'against', 'interface', 'user']
keywords: ['review', 'code', 'against', 'interface', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['requesting-code-review']
---

---


# Web Interface Guidelines

Review Dateien für Compliance mit Web Interface Guidelines.

## Wie es funktioniert

1. Die latest Guidelines von der Source-URL laden
2. Die angegebenen Dateien lesen (oder User nach Dateien/Patterns fragen)
3. Gegen alle Regeln prüfen
4. Findings im tersen `file:line` Format ausgeben

## Guidelines Source

Vor jedem Review fresh laden:
```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

Mit WebFetch/terminal die latest Regeln holen. Die geladene Datei enthält alle Rules und Output-Format-Anweisungen.

## Verwendung

Wenn der User ein Datei- oder Pattern-Argument gibt:
1. Guidelines von der Source-URL laden
2. Angegebene Dateien lesen
3. Alle Regeln anwenden
4. Findings im Guidelines-Format ausgeben

Wenn keine Dateien angegeben: User fragen welche Dateien reviewt werden sollen.

## Für Hermes

Nutze `terminal` + `curl` um die Guidelines zu laden:
```bash
curl -sL "https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"
```
