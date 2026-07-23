# Worked Example: 8 Patterns → 4 Skills (2026-07-05)

Vollständiger Durchlauf der Vault-Skill-Derivation aus dieser Session. Quelle: `Skill-Ableitung - Vault-Phase-2-3.md`.

## Ausgangssituation

- **Quell-Note:** `05 Ressourcen/Skill-Ableitung - Vault-Phase-2-3.md` (4.632 Bytes, 98 Lines)
- **Inhalt:** 8 Patterns aus Vault-Phase 2/3 (Subagent-Clustering)
- **User-Auftrag:** "4 echte Hermes-Skills aus Skill-Ableitungs-Note erstellen + 1 Vault-Spiegel"

## Phase 0: Quell-Note identifizieren

Gefunden via `search_files(pattern="Skill-Ableitung", target="files", path="/home/bratan/Dokumente/Obsidian Vault")`. Vollständig gelesen mit `read_file` (3 Chunks × ~40 Lines).

## Phase 1: Pattern-Cluster

| Pattern | Name | Cluster |
|---------|------|---------|
| 1 | Read→Patch-Retry bei Sibling-Konflikten | Ops |
| 2 | Additive Patches als Cluster-Disziplin | Ops |
| 3 | Anti-Halluzinations-Tripwire | Ops |
| 4 | Themen-MOC Hierarchie (3-stufig) | Ops |
| 5 | Subagent-Spec-Disziplin | Template (eigenständig) |
| 6 | Backlink-Roundtrip-Audit | Audit |
| 7 | Verwaiste-Notes-Detection | Audit |
| 8 | Cluster-Phase-Reporting | Umbrella |

## Phase 2: Skill-Spezifikation

### Skill A: `obsidian-vault-cluster-operations`

- **Category:** note-taking
- **Patterns:** 1–5 (fokussiert auf Vault-Cluster-Ops)
- **Lines:** 214 (SKILL.md)
- **Key sections:** Trigger Conditions, Core Principles (5 Patterns), Workflow (5 Phasen A–E), Pitfalls (6), Connecting Skills
- **Lane:** koenigin, reasoning_effort: xhigh

### Skill B: `obsidian-vault-quality-audit`

- **Category:** note-taking
- **Patterns:** 6–7
- **Lines:** 193
- **Key sections:** Core Heuristics (2 Patterns), Workflow (5 Schritte inkl. Dataview-Queries + Python-Fallback), Pitfalls (6)
- **Lane:** koenigin, reasoning_effort: high

### Skill C: `obsidian-subagent-briefing-template`

- **Category:** orchestration
- **Patterns:** 5 (als kopierbares Spec-Skelett)
- **Lines:** 235
- **Key sections:** 6 obligatorische Sektionen (File-Scope, Anti-Pattern, Output-Format, Tripwire, Konflikt-Hinweise, Link-Syntax), komplettes Beispiel-Briefing, Pitfalls (6)
- **Lane:** koenigin, reasoning_effort: medium

### Skill D: `multi-agent-cluster-patterns`

- **Category:** orchestration
- **Patterns:** 1–8 (generalisiert über Obsidian hinaus)
- **Lines:** 264
- **Key sections:** Pattern-Übersichtstabelle, alle 8 Patterns generalisiert, 5-Phasen-Template, Pitfalls (7)
- **Lane:** koenigin, reasoning_effort: xhigh

## Phase 3: Skills anlegen

Alle 4 Skills mit `skill_manage(action='create')` angelegt. Verifikation:

```bash
# SKILL.md existiert?
find ~/.hermes/skills/{note-taking,orchestration}/ -name "SKILL.md" | wc -l
# → 4

# Frontmatter valide?
for f in ~/.hermes/skills/{note-taking,orchestration}/*/SKILL.md; do
  echo "$(head -1 "$f") $(grep -c "^name:" "$f") $(grep -c "^description:" "$f")"
done
# → Alle haben name + description + version
```

## Phase 4: Vault-Mirror-Note

- **Pfad:** `05 Ressourcen/Skill-Mirror — 4 Cluster-Patterns Skills.md`
- **Inhalt:** YAML (tags, quelle, zweck, datum), Pattern→Skill-Mapping-Tabelle, Lade-Hierarchie, Wiki-Links zurück zu `Skill-Ableitung - Vault-Phase-2-3` + zu Hubs (MOC - Home)
- **Wartungs-Log:** initialer Eintrag 2026-07-05

## Lade-Hierarchie (aus Mirror)

```
Königin hat Vault-Cluster-Run vor sich
       ↓ lädt zuerst
   multi-agent-cluster-patterns (übergeordnete Patterns 1–8)
       ↓ für konkrete Phase A (Spec-Splitting)
   obsidian-subagent-briefing-template (Pattern 5 Spec-Template)
       ↓ für konkrete Phase B–D (Cluster-Ops)
   obsidian-vault-cluster-operations (Pattern 1–5 Workflow)
       ↓ für konkrete Phase D (Audit)
   obsidian-vault-quality-audit (Pattern 6–7 Heuristiken)
```

## Besonderheiten dieser Session

1. **Overlap by design:** Pattern 5 taucht in 3 Skills auf — das ist Absicht (spezifischster Skill wird geladen)
2. **Kategorie-Wahl:** `note-taking` für Vault-Ops weil sie eng an Obsidian gebunden sind; `orchestration` für generalisierte Patterns
3. **Companion-Disziplin:** Mirror-Note ist Pflicht ab ≥3 abgeleiteten Skills
4. **Source-Feld** in jedem Skill: "Vault: Skill-Ableitung - Vault-Phase-2-3.md (05 Ressourcen, 2026-07-05)"

## Lessons

- **Pattern 1–3** sind generisch genug für alle Write-Operations (nicht nur Vault)
- **Pattern 4** (MOC-Hierarchie) ist Obsidian-spezifisch — in der generalisierten Version als "Hierarchische Hub-Struktur" neutralisiert
- **Pattern 5** spec-Template lohnt sich als eigener Skill, weil es zu groß für eine Subsection in `obsidian-vault-cluster-operations` ist
- **Pattern 8** (Reporting) ist in keinem Skill isoliert — taucht in `multi-agent-cluster-patterns` und als Appendix in `obsidian-vault-cluster-operations` auf. Ein dedizierter "Cluster-Report"-Skill wäre eine mögliche nächste Iteration.
