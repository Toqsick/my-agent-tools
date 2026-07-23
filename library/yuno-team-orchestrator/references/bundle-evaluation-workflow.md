# Bundle-Evaluation-Workflow: Drittanbieter-Bundles auf Wissensextraktion prüfen

> **Kontext:** Yuno bekommt ein ZIP, Skill-Bundle oder Release-Tarball von einem
> Drittanbieter. Nicht jedes Bundle ist ein Bug-Fix-Kandidat (`third-party-bundle-patch-release`).
> Viele sind **Redundanzen** — ältere/andere Varianten von Skills, die wir bereits haben.
> Der Wert liegt dann in der **Wissensextraktion**, nicht im Patching.
>
> **Gelernt:** 2026-07-11, Session swarm-v1.0 → `skill-tiers.md` Integration.
> Das swarm-Bundle war eine ältere Variante unseres 7-Agent-Teams (verbatim aus
> `team-roster.md`), aber die `catalog/skill-tiers.md` (Priorisierungs-Matrix) war
> echter Mehrwert.

## 1. Entscheidungsbaum: Patch vs. Wissen vs. Nichts

```
Bundle kommt rein
    │
    ├─ Ist es ein BUGGY/BROKEN Bundle für ein Feature, das wir
    │  nicht selbst haben?
    │  → YES: third-party-bundle-patch-release (Step 1–8)
    │
    ├─ Ist es eine VARIANTE/REDUNDANZ von etwas, das wir bereits
    │  haben (Team-Roster gleiche Agenten, Skill-Namen bekannt)?
    │  → Gehe zu Schritt 2 (Wissensextraktion)
    │
    └─ Ist es weder noch (reine Werbung, alter Snapshot ohne Mehrwert)?
      → Nichts tun. Begründung dokumentieren.
```

### Kriterien für "Redundanz"

- **Agent-Namen matchen 1:1** (`Engineer`, `Researcher`, `Designer`, etc.)
- **Skill-Namen sind erkennbar** (auch wenn anders benannt → auf Pendant mappen)
- **System-Prompts sind ältere Versionen** derselben Idee (nicht substantiell anders)
- **Bundle-Datum älter als letzter Team-Build** (hier: `team-roster.md` vom 2026-07-07)
- **Keine neuen Agent-Typen oder signifikant neue Architektur**

### Kriterien für "Mehrwert extrahierbar"

| Signal | Beispiel |
|---|---|
| Fremde Skill-Priorisierung mit Tiers | `catalog/skill-tiers.md` — **Hauptgrund für diese Session** |
| Power-Combo-Stacks (Skills chaining) | "Research→Plan→Code→Review" mit Pipeline-Beschreibung |
| Neue Workflow-Patterns | Mavis' Leader-Worker-Verifier-Architektur war uns neu |
| Trigger-Phrasen-Tuning | "write doc" → Writer auch ohne Stop-Wörter |
| Pitfall-Sammlungen | Fremde Fehler-Erfahrungen die unseren ergänzen |
| Tool-Set-Empfehlungen | Welche Tools für welche Agenten |
| Agent-Health-Checks | "Skill-Health-Check" aus swarm-Bundle, ohne Pendant bei uns |

## 2. Wissensextraktion (wenn "Redundanz + Mehrwert")

### 2.1 Bundle-Inventur
```bash
find /path/to/bundle -name "SKILL.md" -o -name "*.md" -o -name "*.yaml" -o -name "*.csv" | sort
```
Auf verdächtige Dateien achten: `catalog/`, `tiers/`, `docs/`, `references/` — Orte mit kuratiertem Wissen.

### 2.2 Kategorisieren der Funde
Was ist drin? (Ankreuzen, nicht raten)

| Kategorie | Beispiel | Wert |
|---|---|---|
| **Priorisierungs-Matrix** | Tier 1/2/3 Listen | ⭐⭐⭐ |
| **Power-Combo-Stacks** | "Research-Stack: X→Y→Z" | ⭐⭐⭐ |
| **Trigger-Tuning** | Neue Phrasen, Edge-Cases | ⭐⭐ |
| **Agent-Profile** | System-Prompts, Tool-Sets | ⭐ (wenn redundant) |
| **Pitfall-Sammlungen** | "Don't do X if Y" | ⭐⭐ |
| **Health-Checks** | "Wie pflege ich Skills" | ⭐ |
| **Pipeline-Definition** | CI/CD, Build, Test | ⭐⭐ |

### 2.3 Entscheiden: Wohin integrieren?

**Priorität 1: In einen existierenden class-level Skill integrieren (NICHT neuen Skill erstellen)**

| Fund passt zu | Existierender Skill |
|---|---|
| Tier-Priorisierung, Power-Combo-Stacks | `yuno-team-orchestrator` → `references/skill-tiers.md` |
| Neue Trigger-Phrasen, Edge-Cases | `yuno-team-orchestrator` → `references/routing-table.md` |
| Agent-Profile, System-Prompts | `yuno-team-orchestrator` → persönliche Regel (nicht auto-importieren) |
| Pitfall-Sammlungen, Tool-Set-Ideen | `yuno-team-orchestrator` → SKILL.md § Anti-Patterns |
| Pipeline/Build-Patterns | Jeweiliger Domain-Skill (z.B. `github-pr-workflow`) |
| Security/Health-Checks | `system-security-audit` / `linux-system-maintenance` |

**Checkliste vor Integration:**
- [ ] Ist der Fund **besser/aktueller** als was wir haben? Nicht "anders", sondern "besser"
- [ ] Ist der Fund **übersetzt** ins Hermes-Vokabular? (Claude-Ökosystem → Hermes-Pendants)
- [ ] Ist die **Quelle** klar referenziert? (Datei-Pfad, Version, Datum)
- [ ] Sind **ehrliche Lücken** markiert? (`worktree-management` ohne Pendant → ⚠️ GAP)
- [ ] Gibt es **falsche Annahmen** im Bundle, die wir NICHT übernehmen? (z.B. Claude-spezifische CLI-Befehle)
- [ ] **Tier-Drift-Check:** Jeder neue Tier-Skill in `references/skill-tiers.md` → existiert er auch in `references/routing-table.md`?

### 2.4 Konsolidierungs-Prinzipien

1. **Source-of-Truth bleibt unsere Team-Definition.** Das Bundle ist eine Referenz, nicht das neue Wahr.
2. **Skill-Tiers als zweite Achse.** Die Team-Definition sagt "wer", die Tier-Liste sagt "was priorisiert". Beide müssen konsistent sein.
3. **Nicht das ganze Bundle installieren.** Wenn's eine ältere Variante ist, sind 80% der Dateien redundant. Nur die 20% mit echtem Mehrwert landen in unseren Skills.
4. **Read-only Referenz reicht oft.** `~/Downloads/<bundle>/catalog/skill-tiers.md` als See-Also-Eintrag ist legitim — muss nicht in Hermes-Skills kopiert werden.
5. **Ehrliche Lücken dokumentieren, nicht füllen.** Ein "TODO: worktree-management" ist besser als ein nacherfundener Workaround-Skill.

### 2.5 Vermeide

| Anti-Pattern | Warum | Stattdessen |
|---|---|---|
| Alle Dateien 1:1 in eigene Skills kopieren | Redundant, quillt auf, Pflege-Overhead | Nur 20% Mehrwert extrahieren |
| Bundle-Agent-Profile überschreiben unsere | Source-of-Truth ist `team-roster.md` | Im Changelog notieren, nichts ersetzen |
| "Das ist interessant" ohne Integration | Endet als verwaister Gedanke | Integration in existierenden Skill ODER Read-only-Referenz in See-Also |
| Neue Standalone-Skills aus Bundle-Extraktion | Klasse existiert bereits | In existierenden class-level Skill integrieren |
| Tier-Liste ohne Cross-Check zur Agent-Matrix | Konsistenz-Drift: Skills die in Tier-Liste stehen aber in Routing-Matrix fehlen | Nach jeder Integration: `for skill in $(grep -E '^\\| \\`[a-z]' references/skill-tiers.md | grep -oE '\\`[a-z-]+\\`'); do grep -q "$skill" references/routing-table.md || echo "❌ $skill fehlt"; done` |

## 3. Quellen

- 2026-07-11: swarm-v1.0 Bundle (Mavis/MiniMax) → `skill-tiers.md` Integration
- `yuno-team-orchestrator/SKILL.md` § Changelog v2.0.7–2.0.9
- `third-party-bundle-patch-release` für den Bug-Fix-Pfad (dieser Workflow ist der Gegenpfad)

## Changelog

- **v1.0 (2026-07-11)** — Initial. Extrahiert aus der swarm-v1.0-Integration dieser Session.
