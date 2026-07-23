---
name: vault-skill-derivation
description: >-
  Use when user asks for turning an Obsidian pattern note into a Hermes skill, deriving reusable workflows from vault knowledge, closing a skill gap with structured vault material, or preserving phase learnings as a skill. NOT for copying raw notes verbatim or routine note editing. Applies a pattern-to-skill pipeline with candidate checks, mapping guidance, linked references, and verification gates.
category: meta
platforms:
- linux
- macos
- windows
version: 1.0.0
author: Yuno (Basti)
lane: koenigin
reasoning_effort: xhigh
metadata:
  hermes:
    tags:
    - skills
    - vault
    - derivation
    - knowledge-engineering
    - pattern-extraction
    related_skills:
    - hermes-agent-skill-authoring
    - skill-creator
    - skill-library-maintenance
    - obsidian
    - vault-architecture
license: MIT
trigger_keywords: ['skill', 'pattern', 'note', 'vault', 'user']
keywords: ['skill', 'pattern', 'note', 'vault', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian', 'vault-architecture', 'obsidian-vault-cluster-operations']
---

# Vault → Skill Derivation

Strukturiertes Wissen aus Obsidian-Vault-Notes in Hermes-Skills überführen. Die Vault-Derivation ist die Brücke zwischen **deklarativem Wissen** (Pattern-Notes, Lessons-Learned, Architektur-Notes) und **prozeduralem Wissen** (Hermes-Skills, die Yuno laden und ausführen kann).

## Trigger Conditions

Use this skill when:
- Der User sagt: "mach daraus einen Skill", "Skills aus der Wissensdatenbank", "Ableitung aus Phase-2/3-Patterns"
- Eine Vault-Note enthält strukturierte Patterns (Listen, Tabellen, Workflow-Schemata, Pitfalls) → diese Note ist Kandidat für Derivation
- Eine existierende Hermes-Skill-Lücke wurde identifiziert, die Vault-Wissen schließen könnte
- Nach einer Vault-Phase (z. B. Phase 2/3) sollen die Erkenntnisse als Skills festgehalten werden

Nicht für: Ad-hoc-Skill-Erstellung ohne Vault-Quelle (→ `skill-creator` oder direktes `skill_manage`), In-Repo-Skill-Authoring (→ `hermes-agent-skill-authoring`), Skill-Formate konvertieren (→ `skill-format-conversion`).

## Derivation Pipeline

```
Phase 0: Quell-Note identifizieren
    │
    ├── Suche in 05 Ressourcen/ nach "Skill-Ableitung", "Pattern", "Phase"
    ├── Prüfe: enthält die Note strukturierte Patterns (Listen, Tabellen, Workflows)?
    ├── Lies die vollständige Note → extrahiere alle Patterns
    │
    ↓
Phase 1: Pattern-Cluster identifizieren
    │
    ├── Welche Patterns gehören logisch zusammen?
    │   - Operations-Patterns (Wie machen?) → ein Skill
    │   - Audit/Quality-Patterns (Wie prüfen?) → ein Skill  
    │   - Template/Spec-Patterns (Was braucht man?) → ein Skill
    │   - Generelle Patterns (für alle Cluster) → Umbrella-Skill
    │
    ├── Faustregel: 2–4 Patterns pro Skill
    ├── Ein Pattern darf in mehreren Skills auftauchen (Overlap by design)
    │
    ↓
Phase 2: Pro Skill schreiben
    │
    ├── Für jeden Pattern-Cluster:
    │   1. Name: <domain>-<action> (kebab-case, ≤64 chars)
    │   2. Category: note-taking / orchestration / software-development / devops
    │   3. Description: "Use when <trigger>. <one-line behavior>."
    │   4. Trigger Conditions: wann lädt Yuno diesen Skill?
    │   5. Core Principles: die Patterns mit Code/Query-Beispielen
    │   6. Workflow / Schritt-für-Schritt (Wenn-Dann-Abläufe)
    │   7. PitfallsTable: mindestens 5 Einträge
    │   8. Connecting Skills (Cross-References zu anderen Skills)
    │   9. Source: "Vault: <Dateiname> (<Pfad>, <Datum>)"
    │
    ↓
Phase 3: Skills anlegen (skill_manage action='create')
    │
    ├── Pro Skill: skill_manage(action='create', name='...', category='...', content='...')
    ├── Die SKILL.md muss vollständig sein (kein "work in progress")
    ├── Frontmatter: name + description + version mindestens
    │
    ↓
Phase 4: Vault-Mirror-Note anlegen
    │
    ├── Pfad: selber Ordner wie die Quell-Note
    ├── Name: "Skill-Mirror — <N> <Domain> Skills.md"
    ├── Inhalt:
    │   - YAML: tags, quelle, zweck, datum
    │   - Pattern→Skill-Mapping-Tabelle (siehe Vorlage unten)
    │   - Lade-Hierarchie (welcher Skill wann?)
    │   - Wiki-Links zurück zur Quelle + zu Hubs
    │   - Optional: Wartungs-Log
    │
    ↓
Phase 5: Verifikation
    │
    ├── Alle SKILL.md existieren? → find ~/.hermes/skills/<cat>/<name>/SKILL.md
    ├── Frontmatter valide? → name + description + version vorhanden
    ├── Vault-Mirror existiert? → neben der Quell-Note
    ├── Pattern-Vollständigkeit? → jedes Pattern ist mindestens einem Skill zugeordnet
```

## Pattern→Skill-Mapping-Tabelle (Vault-Mirror-Vorlage)

```markdown
| # | Pattern (Quelle) | Skill (Ableitung) |
|---|------------------|-------------------|
| 1 | <Pattern-1-Name> | `<skill-name>` |
| 2 | <Pattern-2-Name> | `<skill-name>` + `<umbrella-skill>` |
...
```

## Lade-Hierarchie-Vorlage (für Mirror-Note)

```markdown
```
Königin hat <Domäne>-Run vor sich
       │
       ↓ lädt zuerst
   <umbrella-skill> (übergeordnete Patterns)
       │
       ↓ für konkrete Phase <X>
   <operations-skill> (Pattern <N>–<M> Workflow)
       │
       ↓ für konkrete Phase <Y>
   <audit-skill> (Pattern <N> Heuristiken)
```
```

## Verifikation-Checklist

- [ ] Jedes Pattern aus der Quelle ist mindestens einem Skill zugeordnet
- [ ] Pro Skill: `skill_manage(action='create')` erfolgreich ausgeführt
- [ ] Jeder SKILL.md hat valides YAML (name + description + version)
- [ ] Jeder SKILL.md hat eine PitfallsTable mit ≥5 Einträgen
- [ ] Vault-Mirror-Note existiert neben der Quelle
- [ ] Mirror enthält Pattern→Skill-Mapping + Lade-Hierarchie
- [ ] Mirror hat Wiki-Links zurück zur Quelle + zu Hubs (Home, Themen-MOCs)
- [ ] Alle neuen Skills werden bei `skills_list` gefunden (nach Session-Neustart)
- [ ] Keine Lücken: Patterns ohne Skill-Zuordnung sind dokumentiert (bewusst ausgelassen)

## Pitfalls

| # | Pitfall | Mitigation |
|---|---------|------------|
| 1 | Skill-Name zu sessionspezifisch ("fix-audit-2026-07-05") | Class-Level-Name verwenden: <domain>-<action> (z. B. vault-quality-audit) |
| 2 | Pattern in mehrere Skills kopiert ohne Cross-Reference | Overlap ist OK → `related_skills` in Frontmatter setzen |
| 3 | Mirror-Note vergessen → Traceability verloren | Phase 4 ist obligatorisch ab ≥3 abgeleiteten Skills |
| 4 | Skills in falscher Kategorie landen | note-taking für Vault-Ops, orchestration für Multi-Agent, software-development für Code |
| 5 | Description > 1024 chars → Validierung schlägt fehl | Pro Skill prüfen: `len(description) ≤ 1024` |
| 6 | Mirror-Note zitiert Pattern-Nummern, die in Quelle geändert wurden | Datum in Source-Feld setzen; bei Quell-Änderung Mirror updaten |
| 7 | Skill-Creation in protected Skill-Kategorie (bundled/hub) | `skill_manage` verweigert das → Fehler abfangen und Kategorie wechseln |

## Connected Skills

- `hermes-agent-skill-authoring` — In-Repo-SKILL.md-Authoring (diese Skill ergänzt um user-local Derivation)
- `skill-creator` — Allgemeine Skill-Erstellung (Hub) — protected, aber Inspiration für Workflow-Struktur
- `skill-library-maintenance` — Nach Derivation: deduplizieren, slimmer, health-check
- `obsidian` — Read/Search/Patch im Vault
- `vault-architecture` — 8-Folder-Schema und MOC-Hierarchie für Mirror-Note-Platzierung
- `skill-reviewer` — Qualitäts-Review nach Derivation

## References

- `references/vault-derivation-worked-example-2026-07-05.md` — Vollständiges Beispiel der 8-Patterns→4-Skills-Derivation aus dieser Session

## Source

- Erstmalig abgeleitet aus: `Skill-Ableitung - Vault-Phase-2-3.md` (05 Ressourcen, 2026-07-05)
- 8 Patterns → 4 Hermes-Skills → 1 Vault-Mirror-Note