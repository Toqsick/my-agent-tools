---
name: obsidian-vault-color-consolidation
description: |
  Use when aligning an Obsidian vault color palette, synchronizing graph color groups, centralizing CSS variables, or exposing theme values through Style Settings.
  NOT for general note organization, content editing, unrelated theme redesign, or changing vault configuration without preserving valid JSON and CSS syntax.
  Consolidates vault-wide colors across graph.json, CSS custom properties, and Style Settings into a consistent system.
version: 1.0.0
author: Yuno (Basti)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - obsidian
    - color
    - design
    - css
    - customization
    related_skills:
    - obsidian
    - vault-architecture
trigger_keywords: ['vault', 'color', 'graph', 'theme', 'style']
keywords: ['vault', 'color', 'graph', 'theme', 'style']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-themes', 'ui-color-system', 'obsidian-visual-iteration-loop']
---


# Obsidian Vault Color Consolidation

## Overview
Dieser Skill synchronisiert und konsolidiert die Farbgestaltung deines Obsidian Vaults über alle 3 logischen Schichten hinweg: (1) `graph.json` colorGroups für den Knowledge Graph, (2) CSS-Snippets (`yuno-variables.css`) für Custom Properties und (3) `@settings`-Blöcke für das Style Settings Community-Plugin.

## When to Use
- **Trigger**: Es gibt ungenutzte oder doppelt belegte RGB-Farben in `graph.json` (Farb-Kollisionen).
- **Trigger**: Neue Akzent-Farben (wie das Yuno-Rosa) sollen global im Theme und im Graphen registriert werden.
- **Trigger**: Die farbliche Kennzeichnung im Graphen weicht von den CSS-Akzenten der Ordner und Tags ab.
- **Nicht verwenden für**: Den vollständigen Theme-Wechsel (dein Sanctum-Theme bleibt bestehen — dieser Skill kümmert sich ausschließlich um die farbliche Akzent-Schicht).

## Core Concepts & Alignment

### Schicht 1: CSS Variablen (`yuno-variables.css`)
Hier liegen alle Farbwerte als Custom Properties. Sie sind die Single-Source-of-Truth:
```css
:root {
  --yuno-purple: #a78bfa;
  --yuno-purple-deep: #8b5cf6;
  --yuno-pink: #fbcfe8;
}
```

### Schicht 2: Graph Tags in `graph.json`
Verwende Pfad- oder Tag-basierte Queries mit exakter Anführungszeichen-Syntax für Ordner mit Leerzeichen:
```json
{
  "query": "path:"01 Kontext"",
  "color": { "a": 1, "rgb": 16742048 }
}
```
*Hinweis:* RGB wird in der `graph.json` als vorzeichenbehafteter 32-Bit Dezimal-Integer gespeichert (nicht als Hex-String).

### Schicht 3: Style Settings Integration
Für die Anpassung über das Plugin verwende ein dediziertes Snippet (`yuno-theming-controls.css`) mit `@settings` Deklaration:
```css
/*
@settings
name: Yuno Theme Controls
id: yuno-theming
settings:
  -
    id: yuno-purple
    title: Yuno Purple (Primary Accent)
    type: variable-themed-color
    default-light: '#7c3aed'
    default-dark: '#a78bfa'
*/
```

## Common Pitfalls
1. **Pfad-Queries ohne Quotes**: Einfache Suchpfade wie `path:01 Kontext` schlagen in Obsidian fehl, da Leerzeichen ohne Anführungszeichen den Query-Parser brechen. Richtig: `path:"01 Kontext"`.
2. **Hex-Werte in graph.json**: Das Eintragen von Hex-Strings (z.B. `"#a78bfa"`) in `graph.json` bricht die Konfiguration. Wandle Hex immer in Dezimal-Integer um (z.B. `#a78bfa` → `10980346`).
3. **Reihenfolge in appearance.json**: Damit Variablen-Änderungen greifen, muss das Definitions-Snippet `yuno-variables` vor allen konsumierenden Snippets in der Liste geladen werden.

## Verification Checklist
- [ ] `yuno-variables.css` definiert alle aktuellen Farbwerte
- [ ] `graph.json` nutzt korrekte, dezimale Integer-Farbwerte
- [ ] Alle Pfad-Queries für Ordner mit Leerzeichen sind in Backslashed-Quotes `"` gesetzt
- [ ] `jq empty` validiert alle geänderten JSON-Dateien erfolgreich
- [ ] Obsidian-Prozess wurde nach Änderungen neu gestartet (erzwingt Reload)

## Verbindet zu
- [[MOC - Obsidian-Vault]] — Vault-Mechanik-Hub
- [[Obsidian - Plugin-Setup]] — Plugin-Übersicht
- [[Snippet-Liste]] — CSS-Snippets im Vault
- [[Patterns & Workflows - Innovationsraum]] — Pattern-Synthese
