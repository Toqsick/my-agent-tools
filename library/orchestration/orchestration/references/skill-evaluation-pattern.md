# Skill-Evaluation-Pattern

> Selbst-Evaluierung der eigenen Skill-Bibliothek auf Orchestrierungs-Patterns, Lücken und Verbesserungs-Potenzial.
> Erstmals angewandt 2026-06-27: 8 Patterns in 40+ Skills identifiziert, inklusive P0/P1/P2-Roadmap.

## Warum?

Skills sind die prozedurale Erinnerung des Agenten. Sie wachsen organisch, aber selten wird der Gesamtbestand systematisch evaluiert:
- Welche Orchestrierungs-Patterns existieren?
- Welche überschneiden sich?
- Welche fehlen?
- Welche sind für den User aktuell am wertvollsten?

## Workflow

```
Phase 1: Inventory (skills_list + filtern)
Phase 2: Deep Load (skill_view für relevante Kategorien)
Phase 3: Pattern Extraction (AS-IS analysieren)
Phase 4: Synthese + Bewertung (8 Patterns mit Reife/Kosten)
Phase 5: Roadmap (P0/P1/P2/P3)
Phase 6: Dokumentation (~/docs/research/orchestration/)
Phase 7: Skill-Update (in betroffene Skills patchen)
```

## Phase 1: Inventory

```python
from hermes_tools import terminal, write_file

# Alle Skills abrufen — nach Kategorien gruppiert
categories = [
    "software-development", "devops", "orchestration",
    "autonomous-ai-agents", "github", "mcp"
]
```

Filtere nach:
- NUR agent-created Skills (nicht bundled/hub-installed — die sind protected)
- NUR Skills mit Orchestrierungs-Relevanz
- Ignoriere: Einzelfall-Skills (fur eine Session), Tool-Referenzen ohne Pattern

## Phase 2: Deep Load

Lade die SKILL.md der relevanten Skills via `skill_view(name)`:

```python
skill_view(name="multi-agent-work")
skill_view(name="the-dmz-transfer")
skill_view(name="ki-murks-verhindern")
# etc.
```

**Achte auf:**
- Frontmatter (tags, triggers, related_skills)
- Inhaltliche Pattern: Phasen, Gates, Delegation, Parallelisierung
- Referenzen: welche `references/` gibt es, wie tief sind sie?

## Phase 3: Pattern Extraction

Jeder Skill bekommt eine strukturierte Bewertung:

| Skill | Pattern | Reife | Kosten | Stärke | Schwäche |
|-------|---------|-------|--------|--------|----------|
| multi-agent-work | 6-Phase Workflow | ⭐⭐⭐⭐ | Mittel | Vollständigster WF | Komplex |

**Kriterien für Reife:**
- ⭐⭐⭐⭐⭐: 5+ Sessions validiert, dokumentiert, stabil
- ⭐⭐⭐⭐: 2-4 Sessions validiert, kleinere Quirks
- ⭐⭐⭐: 1 Session validiert, oder konzeptionell solide
- ⭐⭐: Konzeptionell, noch nicht validiert
- ⭐: Neu/Experimentell

## Phase 4: Synthese + Bewertung

Erstelle eine übergreifende Tabelle und dedupliziere:

```
## Cross-Cutting Patterns
| # | Pattern | Skills | Reife | Kosten |
|---|---------|--------|-------|--------|
| 1 | Queen-Bee Delegation | multi-agent-research, ... | ⭐⭐⭐⭐⭐ | 0€ Scouts |
```

**Deduplizierungs-Regeln:**
- Zwei Skills mit gleichem Pattern → nur EINEN in die Cross-Cutting-Liste
- Der ausgereiftere gewinnt
- Zusätzlich: Tool-Use/Computer-Use als separate Kategorie

## Phase 5: Roadmap

Identifiziere Lücken zwischen aktuellen Skills und User-Interessen:

| Priorität | Was | Aufwand | Begründung |
|-----------|-----|---------|------------|
| **P0** | Fehlendes Computer-Use Toolset | 1-2h | User interessiert → 0 Skills in Kategorie |
| **P1** | Queen-Rule konsequent anwenden | 0h | Disziplin, kein Code |
| **P2** | MCP-Server für Eigenbau | 3-5h | Braucht es nicht heute |

## Phase 6: Dokumentation

Schreibe nach `~/docs/research/orchestration/<name>-YYYY-MM-DD.md`:

```markdown
# Skill-Evaluierung YYYY-MM-DD

**Bewertete Skills:** N (davon tief geladen: M)
**Gefundene Patterns:** K
**P0/P1/P2-Aufgaben:** wie oben

## Ergebnis-Tabelle (Top-Patterns)
...

## Ausführliche Beschreibung pro Pattern
...

## P0-Roadmap
...
```

## Phase 7: Skill-Update

Wenn neue Patterns oder Lücken gefunden wurden, **sofort** die Skills patchen:
- Neu identifiziertes Pattern? → In bestehenden Skill als `references/`-Datei hinzufügen
- Bestehender Skill unvollständig? → Patch (neue Trigger, Erweiterung)
- Ganz neue Klasse? → Neuen Class-Level-Skill erstellen

## Beispiel-Session: 2026-06-27

**Ausgangslage:** User fragt nach Evaluierung meiner Skills auf Orchestrierungs-Patterns.

**Durchführung:**
1. `skills_list()` für software-dev, devops, orchestration → 44 Skills
2. Tiefer geladen: multi-agent-work, the-dmz-transfer, ki-murks-verhindern, kanban-codex-lane, coding-agents, github-workflow, multi-agent-orchestration
3. 8 Patterns extrahiert, bewertet, priorisiert
4. P0 identifiziert: Computer-Use Toolset ist leer
5. Report geschrieben nach `~/docs/research/orchestration/skill-evaluation-2026-06-27.md`

**Learnings:**
- 3 parallel dispatchte Subagents (Bienenschwärme) kamen zurück — Queen-Bee-Pattern praktisch validiert
- Die bestehenden Skills hatten das Self-Evaluation-Pattern NICHT → wurde hinzugefügt
- `linux-system-maintenance` hatte bereits `fake-storage-validation.md` → kein Update nötig
