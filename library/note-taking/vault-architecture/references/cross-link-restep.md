# Cross-Link-Restep — Bulk Threshold Enforcement

> Systematische Prozedur, um alle Notes im Vault auf ≥ X Wiki-Links zu bringen. Worked example: Phase 3 Cluster 3 / Phase 4 Cluster J (2026-07-05), 37 Files in ~30 min von durchschnittlich 4,3 auf 15,25 Links/Note.

## Wann anwenden

- Nach einer Cluster-Erweiterung, wenn die durchschnittliche Link-Dichte ungleichmäßig ist
- Der Phase-Plan schreibt einen Zielwert vor (z.B. ≥ 5 Wiki-Links)
- Der User sagt "Cross-Link-Restep" oder "alle Notes auf mindestens X bringen"
- 30+ Notes sollen in einer Session auf ein Minimum gebracht werden

## Workflow (6 Stufen)

### Stufe 1: Inventur — Messen

```python
import re
from pathlib import Path

vault = Path("<vault-path>")
files = sorted([p for p in vault.rglob("*.md") if ".trash" not in str(p) and ".obsidian" not in str(p) and "_templates" not in str(p)])

link_pattern = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")

# Notes mit < Threshold identifizieren
threshold = 5  # Ziel-Wiki-Links
total_notes = 0
total_links = 0
notes_under = []

for f in files:
    text = f.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        continue  # leere Dateien überspringen
    links = link_pattern.findall(text)
    total_links += len(links)
    total_notes += 1
    if len(links) < threshold:
        notes_under.append((f, len(links)))

print(f"Notes: {total_notes}")
print(f"Wiki-Links total: {total_links}")
print(f"Avg Links/Note: {total_links/total_notes:.2f}")
print(f"Notes unter {threshold} Links: {len(notes_under)}")
for f, c in sorted(notes_under, key=lambda x: (x[1], x[0])):
    print(f"  {c} Links | {f.relative_to(vault)}")
```

### Stufe 2: Link-Ziele bestimmen

Vor dem Lesen der dünnen Notes: festlegen, welche Wiki-Link-Targets in Frage kommen. Standard-Kategorien (aus der "Verbindet zu" Decision Framework, siehe SKILL.md):

| # | Kategorie | Typische Targets | Priorität |
|---|---|---|---|
| 1 | **Themen-MOCs** | `MOC - Home`, `MOC - KI-Architektur`, `MOC - Gaming-Performance`, `MOC - Obsidian-Vault`, `MOC - Daily Notes`, `MOC - Inbox`, `MOC - Lernen & Orchestration` | IMMER (jede Note braucht 1-2 MOC-Links) |
| 2 | **Ressourcen** | `Glossar`, `Working Agreement - Yuno Basti`, `Hermes-Quickstart`, `Bash & Python - Conventions` | Meistens |
| 3 | **Projekt-MOCs** | `Projekte - Repo-Map`, projekt-spezifische READMEs | Bei passendem Kontext |
| 4 | **Cross-Cluster** | Notes in anderen Ordnern, die thematisch passen | 1-2 pro Note |
| 5 | **Folder-MOCs** | `_MOC.md` im selben Ordner | IMMER (Navigation) |
| 6 | **Verbundene Notes** | Sibling-Notes im selben Ordner | Bei Bedarf |

**Ziel: 5-8 Links pro Note.** Nie mehr als 12 — das macht die "Verbindet zu"-Sektion unübersichtlich.

### Stufe 3: Dünne Notes lesen

Jede Note muss **einmal vollständig gelesen** werden, bevor ein Patch erstellt wird. Ziel: Kontext verstehen, um sinnvolle Cross-Links zu wählen.

**Anti-Pattern:** Blind Links auf alle Notes klatschen ohne Kontext → Links passen nicht zum Thema und der Vault fühlt sich künstlich an.

**Pattern bei 300+ Zeilen:** Nur den Anfang + das Ende lesen (Titel, Frontmatter, erste Sektion, letzte Sektion/Verbindet-zu). Mittelteil ist meist Kontext, der die Link-Strategie nicht ändert.

### Stufe 4: "Verbindet zu"-Sektion hinzufügen (Patchen)

**Fall A — Note hat bereits "## Verbindet zu" oder "## Wiki-Links":**

Lies die letzten 20-40 Zeilen der Datei, identifiziere die bestehende Link-Sektion und **erweitere sie** (additiv, nicht ersetzen):

```markdown
## Verbindet zu

- [[Bestehender Link 1]]
- [[Bestehender Link 2]]
- [[NEU - Themen-MOC]]
- [[NEU - Ressource]]
- [[NEU - Cross-Cluster]]
```

**Ersetzung (Patch):** `old_string` = die gesamte bestehende Link-Sektion + Inhalt, `new_string` = bestehende + neue Links.

**Fall B — Note hat KEINE "## Verbindet zu"-Sektion:**

Füge am Ende der Datei (nach 1 Leerzeile) eine neue Sektion hinzu:

```markdown

## Verbindet zu

- [[MOC - Home]] — Vault-Haupt-Hub
- [[MOC - <Thema>]] — passendes Themen-MOC
- [[<Folder>/_MOC]] — Navigation im Ordner
- [[<Verbundene Ressource>]] — thematisch passend
- [[<Andere Note>]] — 5. Link (Cross-Cluster oder Projekt)
```

**Ersetzung:** `old_string` = die letzte Zeile der Datei (oder das Ende des letzten Absatzes), `new_string` = letzte Zeile + 1 Leerzeile + "## Verbindet zu" + Liste.

**Regel:** Verwende IMMER `mode='replace'` (patch tool). NIEMALS `write_file` auf einer existierenden Note — das überschreibt den gesamten Dateiinhalt und kann Halluzinationen in den Rest der Datei injizieren.

### Stufe 5: Verifikation

Nach allen Patches:

```python
import re
from pathlib import Path

vault = Path("<vault-path>")
files = sorted([p for p in vault.rglob("*.md") if ".trash" not in str(p) and ".obsidian" not in str(p) and "_templates" not in str(p)])
link_pattern = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")

threshold = 5
notes_under_5 = []

print(f"{'Links':>6} | File")
print("-" * 80)
for f in files:
    text = f.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        continue
    rel = str(f.relative_to(vault))
    links = link_pattern.findall(text)
    flag = " *** UNTER 5 ***" if len(links) < threshold else ""
    print(f"{len(links):>6} | {rel}{flag}")
    if len(links) < threshold:
        notes_under_5.append(rel)

print(f"\nNotes mit < {threshold} Links: {len(notes_under_5)}")
if notes_under_5:
    for r in notes_under_5:
        print(f"  {r}")

# Gesamtstatistik
total = sum(1 for f in files if f.read_text(encoding="utf-8", errors="ignore").strip())
total_links = sum(len(link_pattern.findall(f.read_text(encoding="utf-8", errors="ignore"))) for f in files if f.read_text(encoding="utf-8", errors="ignore").strip())
print(f"\nVault-Stand: {total} Notes, {total_links} Wiki-Links, {total_links/total:.2f} avg")
```

### Stufe 6: Plan-Dokumente aktualisieren

Nach Abschluss: Wartungs-Log in `Vault-Phase-3-Plan.md` und/oder `Vault-Phase-4-Plan.md` ergänzen:

```markdown
| 2026-07-05 | Cluster J (Cross-Link-Restep): 37 Files gepatcht, alle ≥ 5 Wiki-Links. Vault: 83 Notes, 1266 Links, 15,25 avg |
```

## Worked Example (2026-07-05)

### Ausgangslage

| Metrik | Wert |
|---|---|
| Phase-4-Plan-Targets (Cluster J) | 29 Files |
| Tatsächlich gepatcht | 37 Files (Cluster J + zusätzliche) |
| Ziel-Threshold | ≥ 5 Wiki-Links |
| Gesamt-Links davor (Phase 3 Ende) | ~975 |
| Gesamt-Links danach | 1266 |
| Delta | **+291** |

### Gepatchte Files (Kategorien)

| Ordner | Anzahl | Beispiele |
|---|---|---|
| 02 Inbox | 4 | `_MOC`, Setup, Open Items, Spickzettel |
| 03 Projekte | 9 | Perf-Tuning (README, CHANGELOG, Plan, Troubleshooting), Linux-Assistant, Github-MCP-Server, TokenTelemetry, Odysseus, Yuno-Dashboard, CP77-Modding |
| 05 Ressourcen | 9 | NVIDIA Tuning, GreyHack-Tools, Bash Conventions, Hermes-Quickstart, Claude Code, Julian-Ivanov, OAuth, Plugin-Setup, Phase-4-Plan |
| 06 Daily Notes | 11 | `_MOC` + 10 Daily-Notes (28.6.–5.7. mit Abend) |
| 07 Archiv | 2 | `_MOC`, Mnemosyne Cleanup Report |
| 08 Anhaenge | 1 | `_README` |
| Plan-Dokumente | 2 | Phase-3-Plan + Phase-4-Plan (nur Wartungs-Log) |

### Link-Target-Strategie

Die am häufigsten verwendeten Cross-Link-Targets im Restep:

| Target | Verwendet in | Grund |
|---|---|---|
| `MOC - Home` | ~30 Notes | Vault-Haupt-Hub — jede Note sollte hierhin linken |
| `MOC - KI-Architektur` | ~20 Notes | Hermes/Mnemosyne/Yuno-Navigation |
| `MOC - Gaming-Performance` | ~12 Notes | Gaming-bezogene Notes (Perf-Tuning, CP77) |
| `MOC - Obsidian-Vault` | ~15 Notes | Vault-Mechanik-Notes |
| `Glossar` | ~10 Notes | Akronym-Referenz |
| `Working Agreement - Yuno Basti` | ~8 Notes | Übergeordnete Konvention |
| `Projekte - Repo-Map` | ~5 Notes | Projekt-Übersicht |

### Patches die schiefgehen können

| Risiko | Symptom | Mitigation |
|---|---|---|
| `old_string` nicht eindeutig | Patch fehlschlägt | Mit 2-3 Kontextzeilen drumherum patchen, nicht nur ein Wort |
| Note wurde zwischen Read und Patch modifiziert | `_warning: modified by sibling subagent` | Re-read + re-patch |
| Leere Datei wird gepatcht | Keine `old_string`-Matches | Nicht patchen — löschen oder manuell füllen |
| `Verbindet zu` existiert schon mit anderem Namen | Doppelte Sektion | Erst prüfen, ob `## Wiki-Links` oder `## Cross-Links` oder `## Siehe auch` existiert |
| Mehrere Notes patchen die gleiche Datei (MOC-Home) | Überlappende Patches → eine Änderung überschreibt andere | Wenn 2+ Agents dieselbe Datei patchen: additive Sektionen verwenden (nie denselben `old_string`) |

## Siehe auch

- `vault-architecture` SKILL.md — "Verbindet zu" Decision Framework (6 Kategorien)
- `obsidian-vault-quality-audit` — Backlink-Detektion (findet Notes die Cross-Links brauchen)
- `references/vault-phase3-cluster-control.md` — Phase-3-Cluster-Control mit 3 parallelen Subagents
- `references/glossary-enrichment.md` — Glossar als erstes Target in einem Cross-Link-Restep (weil jede Note dann `[[Glossar]]` linken kann)
