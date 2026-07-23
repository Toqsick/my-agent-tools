---

name: obsidian-subagent-briefing-template
description: |
  Use when you spawn a sub-agent (Codex, Claude-Code, Gemini-CLI, local Ollama) to do work on the Obsidian vault and need a structured briefing spec — vault path, scope, invariants, deliverables, and validation gates.
  NOT for ad-hoc one-shot edits, non-vault sub-agent work, or synchronously hand-edited notes.
  Spec-blueprint template for Obsidian vault sub-agent briefings: scope, invariants, deliverables, verification gates, and output contract.
category: orchestration
platforms:
- linux
- macos
- windows
version: 1.0.0
author: Yuno (Basti)
source: vault/05 Ressourcen/Skill-Ableitung - Vault-Phase-2-3.md
lane: koenigin
reasoning_effort: medium
metadata:
  hermes:
    tags:
    - obsidian
    - vault
    - subagent
    - briefing
    - template
    - delegation
    related_skills:
    - obsidian-vault-cluster-operations
    - multi-agent-cluster-patterns
    - delegation-anti-patterns
    - subagent-driven-development
triggers:
- subagent briefing
- vault subagent spec
- briefing template
- subagent dispatch vault
license: MIT
trigger_keywords: ['vault', 'agent', 'work', 'obsidian', 'spec']
keywords: ['vault', 'agent', 'work', 'obsidian', 'spec']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-vault-cluster-operations', 'obsidian', 'obsidian-vault-sync']
---


# Obsidian Subagent Briefing Template (Pattern 5)

Das **Spec-Blueprint** für Vault-Cluster-Subagents. Basiert auf Pattern 5 aus `Skill-Ableitung - Vault-Phase-2-3.md` und macht aus "Mach mal den Vault besser" eine **800–1500-Wörter-Spec** mit klarer File-Scope-Disziplin.

## Trigger Conditions

Use this skill when:
- Eine **neue Vault-Cluster-Run** ansteht (siehe `obsidian-vault-cluster-operations` Phase A)
- Subagent-Briefing manuell verfasst werden muss
- Existierende Briefings unvollständig sind (fehlende Anti-Pattern, kein File-Scope, etc.)

Nicht für: Single-Note-Operationen (→ `obsidian`), Cluster-Reporting (→ `multi-agent-cluster-patterns`).

## Kernprinzip

**Subagent-Briefing = Vertrag.** Die Spec muss so präzise sein, dass der Subagent **NICHT** entscheiden muss, **WAS** zu tun ist, sondern nur **WIE**.

Schlechtes Briefing: *"Mach den Vault-Ordner Projekte besser."*
Gutes Briefing: 800–1500 Wörter mit File-Scope, Anti-Patterns, Output-Format, Konflikt-Hinweisen.

## Briefing-Skelett (6 obligatorische Sektionen)

```markdown
# Subagent-Briefing: <Cluster-Name>

Du arbeitest an: **<Cluster-Name> — <Eine-Zeile-Zweck>**
Vault-Pfad: **<absoluter Pfad>**
Gehört zu Cluster-Run: **<Parent-Run-ID>**

## 1. File-Scope (EXAKT)

### Du DARFST lesen:
- `<vault>/03 Projekte/<cluster>/**` — Notes in deinem Cluster
- `<vault>/05 Ressourcen/<relevante-notizen>.md` — Hintergrundwissen

### Du DARFST schreiben:
- `<vault>/03 Projekte/<cluster>/<neue-notes>.md` — max. <N> Notes
- `<vault>/03 Projekte/<cluster>/_MOC.md` — NUR: Sektion `<deine-sektion>`

### Du DARFST NICHT anfassen:
- Andere Ordner (außerhalb 03 Projekte/<cluster>)
- Andere Subagent-Sektionen in derselben _MOC.md
- `MOC - Home.md`, Themen-MOCs (Königin macht das)
- Files mit `lock:cluster-X` Frontmatter

## 2. Anti-Pattern (was NICHT tun)

| Anti-Pattern | Warum verboten | Was stattdessen |
|---|---|---|
| Notes erfinden ohne Quelle | Müll im Vault | "Status: ungeprüft (<Datum>)" wenn Quelle fehlt |
| Andere Sektionen in _MOC.md anfassen | Race-Condition | Nur eigene Sektion editieren |
| Quick-Links in MOC - Home patchen | Subagent-Scope-Verletzung | Königin macht das |
| Wiki-Links OHNE URL-Encoding | Dataview findet nichts | `[[Mein%20Note]]` für Suchpfade |
| Mehr als <N> Notes erstellen | Cluster-Spec-Verletzung | Stop nach N, Rest dokumentieren |
| Subagent anderen Subagenten dispatchen | Scope-Verletzung | Nie (das ist Königin-Arbeit) |

## 3. Output-Format (was am Ende reportet wird)

Am Ende antworte EXAKT in diesem Format:

```
## Cluster-Report: <Cluster-Name>

### Was gemacht
- <Note 1>: <Was rein kam, 1 Zeile>
- <Note 2>: <Was rein kam, 1 Zeile>
- ... (max N Zeilen)

### Verifizierung
- Wiki-Links gesetzt: <Anzahl>
- Backlinks vorhanden: ja/nein
- Konflikte: <wenn welche, wie gelöst>

### Was NICHT gemacht (out-of-scope)
- <Liste>

### Lessons für Königin
- <Was gut lief>
- <Was subagent nicht lösen konnte>
```

## 4. Anti-Halluzinations-Tripwire

Wenn du eine Datenquelle brauchst, die du NICHT lesen kannst:

1. Versuche erst zu lesen (Repo-File, Config, Log)
2. Wenn das nicht klappt, schreibe in der Note:
   ```
   ## Status
   Status: ungeprüft (Quelle nicht zugreifbar am <Datum>)
   ```
3. Lasse Felder leer oder TODO
4. Erfinde **KEINE** Versionsnummern, Dependencies, Befehls-Flags

Diese Regel ist NICHT verhandelbar.

## 5. Patch-Konflikt-Hinweise

Falls `patch` einen "file modified since you last read"-Warnung bringt:
1. `read_file(path)` erneut
2. `patch(path, old_string, new_string)` retry
3. Bei 2× Fehlschlag: STOP und im Subagent-Report dokumentieren

BEI RACE CONDITION mit anderem Subagent auf derselben Sektion:
1. STOP
2. Im Report dokumentieren: "Konflikt in _MOC.md Sektion X mit Subagent Y"
3. NICHT deine Sektion verlassen

## 6. Wiki-Link-Syntax

Wiki-Links in Markdown: `[[Dateiname]]` (ohne `.md`)

Für **Suchpfade** (Dataview, Suche): URL-encode Leerzeichen
- Datei: `Mein Vault Note.md`
- Markdown-Link: `[[Mein Vault Note]]`
- Dataview-Pfad: `FROM "Mein%20Vault%20Note"` ← URL-encoded

Beispiel:
```dataview
LIST FROM "05%20Ressourcen"
WHERE contains(file.tags, "skill")
```

## Zusätzliche Sections (optional, je nach Cluster)

### Schreibstil
- Sprache: Deutsch (außer Tech-Begriffe englisch)
- Tonalität: sachlich, knapp, kein Bullshit-Bingo
- Immer Dataview-/Code-Blöcke wenn Daten visualisiert werden

### Pflicht-Verlinkungen
Pro Note MUSS:
- 3+ Out-Links zu thematisch passenden Notes
- 1+ In-Link von MOC oder Hub-Note (Königin macht das oft im Cluster-Phase-D)

### Quellenhierarchie
1. Repo-Configs / offizielle Docs (P1, primary)
2. Erfahrungsnotizen im Vault (P2, secondary)
3. Web-Search (P3, fallback) — nur bei Lücken

## Beispiel: Realistisches Briefing

```markdown
# Subagent-Briefing: GPU-Tuning Notes (Cluster 2026-07-05-GPU)

Vault: /home/bratan/Dokumente/Obsidian Vault
Cluster-Run-ID: 2026-07-05-GPU-Tuning

## 1. File-Scope
DARF lesen:
- /home/bratan/Dokumente/Obsidian Vault/03 Projekte/Perf-Tuning RTX5060/**
- ~/.local/share/Steam/.../config.vdf (User-Game-Profile)

DARF schreiben:
- 03 Projekte/Perf-Tuning RTX5060/GPU-Tuning-Methoden.md
- 03 Projekte/Perf-Tuning RTX5060/Treiber-Konflikte.md
- _MOC.md Sektion "GPU-Tuning-Notes" (NICHT andere Sektionen)

## 2. Anti-Pattern
- KEINE Versionsnummern erfinden wenn Source nicht lesbar
- NICHT NVIDIA-Settings doc patchen (Königin macht das)
- NICHT Treiber herunterladen (Königin-Aktion)

## 3. Output-Format
(siehe oben, exakt)

## 4. Anti-Halluzinations-Tripwire
Wenn ~/.local/share/Steam/.../config.vdf nicht lesbar:
schreibe "Status: ungeprüft (Steam-Config nicht lesbar am 2026-07-05)"
LASSE Tooling-Felder LEER, erfinde NICHTS.

## 5. Patch-Konflikt
"file modified" → re-read + retry. Bei 2× fail: STOP und Report.

## 6. Wiki-Link-Syntax
[[Perf-Tuning RTX5060]] für Markdown
FROM "03%20Projekte/Perf-Tuning%20RTX5060" für Dataview
```

## Pitfalls beim Briefing-Schreiben

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Briefing <500 Wörter → Subagent erfindet Scope | Briefing-Gerüst erzwingt Mindestlänge |
| 2 | File-Scope nicht exhaustive → Subagent macht zu viel | "DARF lesen/schreiben NICHT anfassen" explizit |
| 3 | Anti-Pattern-Section fehlt → Subagent macht Anti-Patterns | Sektion 2 ist obligatorisch |
| 4 | Output-Format nicht spezifiziert → Reports nicht parseable | Template EXAKT vorgeben, Königin prüft |
| 5 | Anti-Halluzinations-Tripwire vergessen → Müll im Vault | Sektion 4 ist nicht verhandelbar |
| 6 | Wiki-Link-Encoding nicht erklärt → Dataview-Queries brechen | Sektion 6 mit Vor- und Nach-Beispiel |

## Connecting Skills

- **`obsidian-vault-cluster-operations`** — Pattern 5 ist hier detailliert
- **`multi-agent-cluster-patterns`** — Clustering-Patterns nutzen diese Briefings
- **`delegation-anti-patterns`** — Hermes-spezifische Delegation-Pitfalls
- **`subagent-driven-development`** — Subagent-Workflow generisch (Code oder Nicht-Code)

## Source

- Vault: `Skill-Ableitung - Vault-Phase-2-3.md` (05 Ressourcen, 2026-07-05)
- Pattern 5: Subagent-Spec-Disziplin, abgeleitet aus Phase-2 + Phase-3-Briefings
