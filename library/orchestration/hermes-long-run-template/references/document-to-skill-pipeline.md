# Document-to-Skill Pipeline

**Provenance**: Diese Methodik wurde beim Bau von `hermes-long-run-template` (2026-07-08) aus einem 14K-Token-Dokument über LLM Long-Running-Prompts entwickelt und verifiziert.

## Zweck

Ein strukturiertes externes Dokument (Guide, Paper, Blogpost, Spec) systematisch evaluieren und in die Hermes-Skill-Landschaft übersetzen — ohne blind zu kopieren und ohne Fähigkeiten zu verlieren.

## Pipeline

### Step 1: Volltext lesen + klassifizieren

Lies das Dokument vollständig (`web_extract` oder `read_file`). Klassifiziere **jede Sektion** nach:

| Kategorie | Bedeutung | Beispiel |
|---|---|---|
| `→ EXISTING_SKILL` | Deckt sich mit einem bereits vorhandenen Skill | ReAct-Pattern → `hermes-react-pattern` |
| `→ EXTEND` | Erweitert einen vorhandenen Skill (neue Facette, neues Pitfall) | Context-Budget-85%-Regel → `hermes-context-budget` |
| `→ NEW_SKILL` | Eigenständiger Inhalt ohne Hermes-Äquivalent | 7-Phasen-Macro-Lifecycle → neuer Skill |
| `→ NOISE` | Allgemeinwissen, Wiederholung, Werbung, nicht übertragbar | — |
| `→ USER_PREF` | Stil/Format/Workflow-Präferenz des Users | Sprache, Ton, Komplexität |

### Step 2: Mapping validieren

Für jedes `EXISTING_SKILL`: Skill per `skill_view` laden und **konkrete Übereinstimmungen zitieren** (keine Bauchgefühle). Erst wenn feststeht: "Sektion 3 spricht über ReAct → `hermes-react-pattern` hat genau das", dann ist das Mapping valide.

Für jedes `EXTEND`: Prüfen, ob der Zusatz im Skill wirklich fehlt. Nur patchen, wenn Lücke **echt** ist — nicht patchen, nur weil ein anderer Autor den Fokus anders gesetzt hat.

### Step 3: Gap-Analyse

Liste die ungedeckten Sektionen (`NEW_SKILL`). Prüfe:
- **Gibt es einen existierenden Hermes-Skill, der nah genug dran ist?** → Lieber erweitern als neu bauen
- **Überlappt der neue Skill einen vorhandenen?** → Grenzen explizit definieren (siehe `hermes-long-run-template` vs. `hermes-react-pattern` vs. `workflow-template`)
- **Ist der neue Skill auf Klassen-Ebene?** (lösungsneutral, nicht auf einen Session-Namen oder Fehlerstring getrimmt)

### Step 4: Skill bauen

Siehe [Skill-Creation-Standard](https://hermes-agent.nousresearch.com/docs/skills).

**Besondere Disziplin bei dokument-abgeleiteten Skills**:
- Quellen-Transparenz: Frontmatter-Author-Feld nennt das Ursprungsdokument
- Kein Blind-Übernehmen: Deutsche Übersetzung + Hermes-spezifische Terminologie
- Trigger explizit aus dem Dokument extrahiert
- Cross-Referenzen zu allen Mapping-Zielen (auch `EXISTING_SKILL`-Zielen, die nicht gepatcht wurden)

### Step 5: Registrierung + Vernetzung

Nach dem Bau:
1. **Navigator aktualisieren**: Cluster-Größe + neue Einträge
2. **Related-Skills patchen**: Jeder Schwester-Skill, der auf den neuen verweisen sollte → `related_skills` updaten
3. **Mnemosyne-Memory**: Kurze Notiz, damit künftige Sessions den neuen Skill kennen
4. **Trigger validieren**: In der Skill-Description die Auslöse-Begriffe aus dem Ursprungsdokument ergänzen

## Anti-Patterns

1. **Dokument zu Skill (1:1)**: Nicht jede interessante Sektion braucht einen eigenen Skill. Erst Gap-Analyse, dann entscheiden.
2. **Mapping ohne Verifikation**: "Sieht nach ReAct aus" reicht nicht — `skill_view` aufrufen und konkrete Textstellen vergleichen.
3. **Zu viele NEW_SKILL**: Mehr als 1 neuer Skill pro Dokument ist verdächtig. Oft steckt ein Skill-Refactoring dahinter (Split) oder der Skill ist zu eng gefasst.
4. **External-Doc-Autorität überschätzt**: Externe Guides können irren, veralten oder auf andere Systeme gemünzt sein. Immer gegen Hermes-Fakten validieren.

## Beispiel: 14K Long-Run-Dokument → Skills

| Dokument-Sektion | Mapping | Begründung |
|---|---|---|
| ReAct (Thought→Action→Observation) | `hermes-react-pattern` | Deckungsgleich, nur ergänzt |
| Chain-of-Thought Prompts | NOISE | Allgemeinwissen, kein Hermes-Mehrwert |
| GOTO-Statements / Workflow-Loops | `hermes-context-budget` (EXTEND) | Keine Context-Budget-Metrik im Original, aber kompatibel |
| "Stack Trace your thought" | NOISE | Spezifisch für andere Systeme (Aider) |
| Plan-Worker-Worker-Consolidate (3/5/6) | Workflow-Lanes in `hermes-long-run-template` | Eigenständiges Macro-Pattern |
| 7-Phasen-Macro-Lifecycle | `hermes-long-run-template` (NEW) | Kein Hermes-Äquivalent vorhanden |
| Queen Bee + Checkpoints | `hermes-long-run-template` | In Phase C integriert |
| "Immer zu früh stoppen" | `hermes-long-run-template` Pitfall #6 | BLOCKED-vertuschen verbieten |
| Append-only Artefakte | `hermes-long-run-template` Pitfall #5 | Aus "no overwrite" + Versionierung |

## Verwandte Skills

- `hermes-agent-skill-authoring` — SKILL.md-Formatierung und Frontmatter
- `skill-creator` — Meta-Skill zum Erstellen neuer Skills
- `vault-skill-derivation` — Skills aus Obsidian-Vault-Notes ableiten (paralleles Pattern, andere Quelle)
