---
name: obsidian-canvas-factory
description: |
  Use when you need to use the obsidian-canvas-factory workflow and its documented procedures.
  NOT for unrelated tasks outside the obsidian-canvas-factory workflow.
  Provides focused guidance for obsidian-canvas-factory.
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
    - canvas
    - design
    - visualization
    related_skills:
    - obsidian
    - vault-architecture
trigger_keywords: ['obsidian', 'canvas', 'factory', 'workflow', 'need']
keywords: ['obsidian', 'canvas', 'factory', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---


# Obsidian Canvas Factory

## Overview
Obsidian-Canvas-Dateien (`.canvas`) sind JSON-basierte Dokumente, die visuelle Notizen-Netzwerke, Flussdiagramme oder Gruppen-Strukturen darstellen. Dieser Skill liefert ein deterministisches Regelwerk zur Erzeugung valider Canvas-Dateien, um visuelle Dashboards oder Layouts im Vault anzulegen.

## When to Use
- **Trigger**: Du willst eine visuelle Karte einer Multi-Agenten-Architektur (z.B. Queen-Bee-Schnittstellen) erstellen.
- **Trigger**: Du willst komplexe Zusammenhänge (z.B. Hardware-Layouts, Cron-Verbindungen oder Wissensgraphen) grafisch abbilden.
- **Trigger**: Du willst Wiki-Link-Embeds zentraler Quell-Notizen mit erklärenden Text-Nodes anordnen.
- **Nicht verwenden für**: Einfache Textnotizen (nutze Standard-Markdown) oder Diagramme, die Obsidian nicht nativ rendern kann (z.B. komplexe UML-Klassendiagramme — dafür ist Mermaid-Syntax besser geeignet).

## JSON Specification & Template
Jede `.canvas` Datei besteht aus einem JSON-Objekt mit zwei primären Arrays: `nodes` (Inhalts-Elemente) und `edges` (Verbindungskanten).

```json
{
  "nodes": [
    {
      "id": "a1b2c3d400010001",
      "type": "text",
      "text": "# Titel\n\nBeschreibung",
      "x": -500,
      "y": -300,
      "width": 350,
      "height": 180,
      "color": "1"
    },
    {
      "id": "a1b2c3d400020001",
      "type": "file",
      "file": "05 Ressourcen/Subagent-Patterns - Delegation & Routing.md",
      "x": -300,
      "y": 100,
      "width": 400,
      "height": 500,
      "color": "6"
    }
  ],
  "edges": [
    {
      "id": "e1b2c3d40001edge1",
      "fromNode": "a1b2c3d400010001",
      "fromSide": "right",
      "toNode": "a1b2c3d400020001",
      "toSide": "left",
      "color": "1"
    }
  ]
}
```

## Implementation Steps
1. **Planung**: Definiere die Liste aller Nodes (Typen: `text` für freien Text oder `file` für bestehende Notizen) und deren relative Positionen im Koordinatensystem.
2. **ID-Vergabe**: Erzeuge eindeutige, 16-stellige Hex-Strings für alle Nodes (z.B. `a1b2c3d400010001`) und Edges.
3. **JSON schreiben**: Schreibe die Datei mit dem `write_file` Tool nach `08 Anhaenge/Excalidraw/<Name>.canvas`. Achte auf absolut fehlerfreies JSON (keine schwebenden Kommas).
4. **Verifizierung**: Validiere das JSON-Format und verlinke das Canvas im MOC-Home oder Dashboard.

## Common Pitfalls
1. **Ungültige Node-IDs**: Obsidian verlangt exakt **16-stellige Hexadezimal-IDs** (ohne `0x` Prefix). Kürzere oder längere IDs führen zu Fehlern beim Rendern.
2. **Falsche Pfadangabe bei `file`**: Pfade für Datei-Nodes müssen **absolut zum Vault-Root** angegeben werden (z.B. `05 Ressourcen/Subagent-Patterns.md`), niemals relativ mit `./` oder `~/` und ohne führende Slashes.
3. **Pixel- statt Grid-Koordinaten**: Die Positionen `x` und `y` sowie Dimensionen `width` und `height` sind reine Pixel-Koordinaten (Vorschlag: `x: -500` bis `500` für den Startbereich).

## Verification Checklist
- [ ] Datei liegt unter `08 Anhaenge/Excalidraw/<name>.canvas` vor
- [ ] JSON ist valide (`jq empty <file>.canvas` wirft keinen Fehler)
- [ ] Alle IDs sind exakt 16 Hex-Stellen lang
- [ ] Dateipfade in `file`-Nodes enthalten keine Slashes am Anfang oder relative Suffixe
- [ ] Canvas-File ist über `![[<canvas-name>]]` oder `[[<canvas-name>]]` im Dashboard oder MOC verlinkt

## Verbindet zu
- [[MOC - Obsidian-Vault]] — Vault-Mechanik-Hub
- [[Patterns & Workflows - Innovationsraum]] — Pattern-Synthese
- [[00 Knowledge Graph]] — Graph-Visualisierung
- [[MOC - Home]] — Canvas-Inventar
