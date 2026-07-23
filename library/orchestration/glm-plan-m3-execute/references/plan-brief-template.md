# Plan-Brief Template für GLM 5.2

> Dieses Template geht in den `plan-glm` Brief (`/tmp/plan-glm-brief.md`) mit rein.
> Es erzwingt, dass GLM 5.2 auf Basis verifizierter Realität plant — nicht auf
> Basis von Annahmen.

## Template

```markdown
# Planning Task

## Goal
[User-Task, ein klarer Satz — was soll gebaut/gefixt/refactort werden]

## Context
- Project: [Pfad, z.B. ~/10-Projekte/10-active/greyhack-tools]
- Key Files: [2-5 relevante Dateien die der Task berührt]
- Design-Entscheidungen aus User-Session: [falls vorhanden]
- Constraints: [Test-Framework, Dependencies, Coding-Standards]

## Realitäts-Status (von Königin verifiziert — NICHT auf Annahmen bauen)

| Pfad | Existenz | Größe/Zeilen | ModTime | Evidence |
|---|---|---|---|---|
| src/core/crypto.rs | ✅ exists | 4.2 KB / 120 L | 2026-07-14 | `ls -la` |
| tests/test_crypto.py | ❌ MISSING | — | — | `test -f` → exit 1 |
| docs/api.md | 🆕 muss erstellt werden | — | — | `find docs/ -name "api*"` → 0 Treffer |
| Cargo.toml (dependencies) | ✅ exists | 1.1 KB / 45 L | 2026-07-10 | `head -5` |

### Strukturelle Variation (falls Heuristik/Detection-Task)

Section-Header-Inventar:
```
12 ## Was lief
 3 ## Was lief (Nachmittag)
 2 ## Was Subagent C final berichtet hat
 1 ## 🚀 Hauptphase: ...
```
Variations-Space > 3 → Multi-Marker-Strategie statt Exact-Match verwenden.

### Daten-Health (falls Health-Klassifikation relevant)

| Datei | Plan-Annahme | Live-Status | Match? |
|---|---|---|---|
| 2026-07-15.md | HEALTHY | PARTIAL (leere Sektionen) | ❌ |
| 2026-07-03.md | MISSING | exists (4946 B) | ❌ |

## Pflicht-Quality-Gates im Plan

Der Plan MUSS folgende Strukturmerkmale enthalten (better-plan-strategy S1-S7):

- [ ] **S1 — Realitäts-Status-Tabelle** oben im Plan (kann obige Tabelle übernehmen)
- [ ] **S2 — SSOT-Audit-Tabelle** (nur bei audit-driven Plänen: `Annahme | Live-Status | Aktion`)
- [ ] **S3 — Konkrete Minuten-Schätzungen** pro Task (`15 Min`, nicht `small`)
- [ ] **S4 — Atomic-Write Policy** bei Single-File-Edits (ein `write_file`, nicht zwei `patch`)
- [ ] **S5 — Risiko-Sektion R1-Rn** mit nummerierten Shell-Probes (`test -f ...`, `grep -c ...`)
- [ ] **S6 — Wave-Strategie** (welche Tasks parallel, welche sequentiell, Abhängigkeiten)
- [ ] **S7 — Done-Kriterium Checkbox-Liste** (objektiv überprüfbare Outcomes)

## Working Directory
[Aktuelles Arbeitsverzeichnis, z.B. ~/10-Projekte/10-active/greyhack-tools]
```

## Ausfüll-Anleitung

### Goal-Sektion

Eine Zeile. Beispiel:
- ✅ `Refactor des Crypto-Moduls: RSA-Logik extrahieren, Tests hinzufügen, CI-integrieren.`
- ❌ `Verbessere das Crypto-Modul.` (zu vage)
- ❌ `Hier ist eine Liste von 12 Dingen die du machen sollst...` (kein einzelner Task)

### Context-Sektion

2-5 Bullets, nicht mehr. Was der Planer zusätzlich wissen muss:
- Project-Pfad (immer)
- Key Files (die der Task direkt berührt)
- Design-Entscheidungen oder Constraints aus der User-Session
- Test-Framework, Dependencies, Coding-Standards

### Realitäts-Status-Tabelle

Dies ist der wichtigste Teil des Briefs. **Jede Zeile** wird von der Königin
in Phase 1 mit Live-Commands verifiziert. GLM 5.2 plant dann auf Basis dieser
Tabelle — nicht auf Basis von "ich nehme an die Datei existiert".

| Spalte | Bedeutung | Beispiel |
|---|---|---|
| Pfad | Der File-Pfad relativ oder absolut | `src/core/crypto.rs` |
| Existenz | ✅ exists / ❌ MISSING / 🆕 must-create | ✅ |
| Größe/Zeilen | `ls -la` Output | 4.2 KB / 120 L |
| ModTime | Letzte Änderung | 2026-07-14 |
| Evidence | Wie wurde verifiziert | `ls -la`, `test -f`, `find` |

**Wichtig:** Wenn GLM im Plan auf einen Pfad referenziert der nicht in der
Realitäts-Status-Tabelle steht, MUSS GLM ihn vor der Planung selbst verifizieren.

### Strukturelle Variation (nur bei Heuristik-Tasks)

Bei Tasks die klassifizieren/detektieren/parsen (z.B. Daily-Report-Trigger):

```bash
# Section-Header-Inventar (von Königin in Phase 1 erstellt)
find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20
```

Wenn der Variations-Space > 3 unique Patterns → Multi-Marker-Strategie statt
Exact-Match. Das ist die Lektion aus Pitfall #38 (2026-07-16).

### Daten-Health (nur bei Status-Klassifikation)

Bei Tasks die HEALTHY/PARTIAL/STUB/MISSING-Klassifikationen verwenden:

```bash
# Detection auf allen relevanten Files laufen lassen
for f in $(find <target> -name "*.md" | sort); do
    python3 <detection-script> --date "$(basename "$f" .md)" --json
done
```

Die Königin vergleicht Plan-Annahmen mit Live-Status. Jede ❌ wird im Brief
markiert — GLM weiß dann, dass die Annahme falsch ist und plant entsprechend.

## Beispiel-Brief (aus Daily-Report-Trigger-Session 2026-07-16)

```markdown
# Planning Task

## Goal
Implementiere einen Session-Start-Trigger der erkennt wenn die heutige
Daily-Note fehlt oder nur ein Stub ist, und Yuno an eine freundliche
Erinnerung macht (kein Cron, kein Push).

## Context
- Project: Hermes Agent skills + scripts
- Key Files:
  - ~/.hermes/scripts/daily-note-health.py (Detection-Script, existiert)
  - ~/.hermes/skills/productivity/daily-briefing/SKILL.md (Integration-Punkt)
- Constraint: Multi-Marker-Strategie wegen Section-Header-Variation
- Test-Framework: pytest

## Realitäts-Status (verifiziert 2026-07-16)

| Pfad | Existenz | Größe | ModTime | Evidence |
|---|---|---|---|---|
| ~/.hermes/scripts/daily-note-health.py | ✅ | 8.5 KB | 2026-07-16 | `ls -la` |
| ~/.hermes/scripts/test_daily_note_health.py | ✅ | 9.7 KB | 2026-07-16 | `ls -la` |
| ~/.hermes/skills/productivity/daily-briefing/SKILL.md | ✅ | 12.3 KB | 2026-07-16 | `ls -la` |
| Vault: 06 Daily Notes/ | ✅ | 16 files | — | `find` |

### Strukturelle Variation

Section-Header-Inventar (16 Daily Notes):
```
12 ## Was lief
 3 ## Was lief (Nachmittag)
 2 ## Was Subagent C final berichtet hat
 1 ## 🚀 Hauptphase: ...
```
Variations-Space = 4 → Multi-Marker-Strategie erforderlich.

### Daten-Health

| Datei | Plan-Annahme | Live-Status | Match? |
|---|---|---|---|
| 2026-07-15.md | HEALTHY | PARTIAL (leere Sektionen) | ❌ |
| 2026-07-03.md | MISSING | exists (4946 B) | ❌ |

## Pflicht-Quality-Gates
[S1-S7 wie oben]

## Working Directory
/home/bratan
```

GLM 5.2 sah in diesem Brief, dass die Annahmen über 2026-07-15 und 2026-07-03
falsch waren — und plante entsprechend (Multi-Marker-Strategie, Tests gegen
echte Vault-Daten).
