---
name: system-documentation
title: System & Project Documentation
description: >-
  Use when user asks for maintaining structured system or project documentation, auditing docs against live data sources, writing an audit-recovery report, or validating documentation wikilinks. NOT for keeping ephemeral scratch notes or executing system configuration changes. Defines a durable Markdown tree, evidence-driven drift checks, report quality gates, recovery records, and linked-source validation.
triggers:
- User asks for "Dokumentation" or "Systemübersicht" or "Dokumentation zu allem was
  wir machen"
- User wants to track what was built, fixed, or configured over time
- User says "schreib mal auf was wir gemacht haben"
- After completing a system change, fix, or build (always offer to document it)
- Starting a new project or system modification
- User mentions Obsidian Vault, "Vault aufsetzen", "8-Ordner", Julian Ivanov, Dataview,
  MOC
- User says "befülle den Vault" / "schreib das in Obsidian" / "dokumentiere das in
  Vault"
- User asks for a "how-to", "setup-guide", "install guide", "Tutorial",
  "Anleitung", "Setup", or wants a technology walkthrough documented step
  by step
version: 1.5.0
author: Hermes Agent
changelog:
- 2026-07-22 - GitHub-Wiki vs Obsidian-Vault Format-Unterscheidung + Wiki-Befüllungs-Workflow für Meta-Pages (Quickstart/Installation/Changelog) ergänzt (aus greyscripts-Repo Wiki-Befüllung)
- 2026-07-22 - 1-Index + N-Category Page-Set Workflow ergänzt (Pattern-Kategorisierung, Score-Tabelle, Anti-Patterns-Sektion, glob-Double-Count-Pitfall, pro-Seite Em-Dash-Gate)
- 2026-07-19 - Guide & How-To Document Format hinzugefügt (Trigger, Section, en-dash quality gates, reference file; aus Galaxy-Watch-6-Setup-Session)
- 2026-07-17 - Audit-Recovery-Report-Sektion hinzugefügt + reference-Template (aus Daily-Tracking-Audit-Recovery 2026-07-17, Biene-C-Execution-Pattern)
- 2026-07-14 - Datenquellen-Audit-Workflow hinzugefügt (Live-DB vs. Vault-Doku, Drift-Matrix,
  Quality-Gate, Stale-Markierung)
- 2026-07-08 - Post-Deployment Multi-Target Documentation Workflow hinzugefügt (Projekt-Note
  → Resource → MOC-Patches → Mnemosyne → Verify)
- 2026-07-05 - Obsidian-Vault-Modus (Julian-Ivanov-8-Ordner) als Bastis bevorzugte
  Doku-Stätte seit 2026-07-05
- 2026-07-05 - Dataview-Plugin-Hinweis in Obsidian-Modus integriert
- 2026-07-05 - Mnemosyne-ID-Referenz-Konvention für Vault-Notes etabliert
license: MIT
lane: koenigin
reasoning_effort: xhigh
agent: Writer
routing_hint: '**Agent-Scope:** Long-form content, docs, proposals, copy. Off-scope:
  code, design, data modeling — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['system', 'documentation', 'recovery', 'report', 'user']
keywords: ['system', 'documentation', 'recovery', 'report', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

---
# System & Project Documentation

## Purpose

Keep a living document tree of everything built or fixed on the user's system.
Each entry captures: goal, approach, exact commands, file paths changed, results,
and decision rationale. This makes future sessions self-sufficient — no need to
re-discover what was done or why.

## Directory Structure

All docs live under a central directory. Use the location the user prefers;
default is `~/docs/system/` if no preference is given.

**Basti's preferred structure (shallow, flat):**

```

set -euo pipefail
~/docs/
├── system/
│   ├── README.md          # System-Übersicht (Specs, Pfade, Cleanup-Log)
│   └── security.md        # Sicherheits-Audit (Ports, Dienste, Fixes)
├── builds/
│   └── README.md          # Projekte + Tools (sysdoctor, greysync, gmail-organizer)
└── scripts/
    └── (frei für Script-Doku)
```

Alternative deep tree (use if user has many docs or asks for more structure):

```

set -euo pipefail
~/docs/system/
├── README.md                # Index with links to all entries
├── 01-hardware/
│   └── monitor-setup.md     # EDID fix, custom modelines, monitor configs
├── 02-software/
│   └── hermes-config.md     # Hermes Agent profiles, providers, cron jobs
├── 03-network/
│   └── monitor-edid.md      # EDID recovery, reduced-blanking timing
└── 04-maintenance/
    └── cleanup-workflow.md  # Systempflege steps: kernel, cache, logs
```bash
~/docs/system/
├── README.md                # Index with links to all entries
├── 01-hardware/
│   ├── monitor-setup.md     # EDID fix, custom modelines, monitor configs
│   ├── gpu-tuning.md        # NVIDIA PRIME, Dynamic Boost, GameMode hooks
│   └── cpu-governor.md      # intel_pstate EPP vs governor quirks
├── 02-software/
│   ├── hermes-config.md     # Hermes Agent profiles, providers, cron jobs
│   ├── steam-setup.md       # GameMode, start-options, shader cache notes
│   └── greyhack-tools.md    # GreyScript Arsenal — lib_core, import paths, user name
├── 03-network/
│   └── monitor-edid.md      # EDID recovery, reduced-blanking timing
├── 04-maintenance/
│   ├── cleanup-workflow.md  # Systempflege steps: kernel, cache, logs
│   └── backup-notes.md      # What gets backed up and how
└── 05-projects/
    └── greyhack-arsenal.md  # Full toolset overview, version history
```

set -euo pipefail
> For Basti: he uses `~/docs/system/README.md` (system overview) + `~/docs/system/security.md` + `~/docs/builds/README.md` (projects/tools). Flat files, shallow structure. Offer this format unless he asks for more nesting.

## Obsidian-Vault-Modus (Basti seit 2026-07-05)

Basti hat einen Obsidian-Vault unter `~/Dokumente/Obsidian Vault/` parallel zu `~/docs/`. Der Vault nutzt Julian-Ivanov-8-Ordner-Struktur und ist seit 2026-07-05 **die bevorzugte Doku-Stätte** für neue Builds/Fixes/Konfigurationen — nicht mehr `~/docs/`.

**Welches System nehmen?**

| Wenn ... | Dann nutze ... |
|---|---|
| Notiz ist projektspezifisch (Build/Fix mit Zielbild+Ende) | Obsidian Vault: `03 Projekte/<name>/` |
| Notiz ist dauerhafter Lebensbereich (Gaming, Dev, System...) | Obsidian Vault: `04 Bereiche/<bereich>.md` |
| Notiz ist Hardware-Spec, Profil, Framework-Spiegel | Obsidian Vault: `01 Kontext/` |
| Notiz ist externe Ressource / How-to / Skript | Obsidian Vault: `05 Ressourcen/` |
| Tagesjournal / Daily-Note | Obsidian Vault: `06 Daily Notes/` |
| User fragt explizit nach "~/docs/" oder hat keinen Vault | legacy `~/docs/system/` weiter benutzen |

**Vault-Pfad-Resolution:** Vault liegt unter `~/Dokumente/Obsidian Vault/` (Zorin/Ubuntu deutsches Locales), NICHT `~/Documents/Obsidian Vault/` (eng) und NICHT `~/Documents/`. Immer prüfen via `ls -d` oder `find ~ -maxdepth 4 -type d -iname "*obsidian*"`.

**Vault-Befüllungs-Sequenz (wenn User "befülle den Vault mit allem was du weißt" sagt):**

1. **Ist-Zustand:** `find <vault> -type f -name '*.md' -not -path '*/.obsidian/*'` → Inventar
2. **8 Ordner anlegen:** `mkdir -p` mit führender Ziffer + Leerzeichen + Name (`01 Kontext`, `02 Inbox`, `03 Projekte`, `04 Bereiche`, `05 Ressourcen`, `06 Daily Notes`, `07 Archiv`, `08 Anhaenge`). Niemals ohne `-p`.
3. **`MOC - Home.md` in Vault-Root** mit Dataview-Queries (LIST from "..." SORT file.name ASC).
4. **Hardware-Snapshot** (`01 Kontext/Hardware - <chassis>.md`) — am wichtigsten, gründet alle anderen.
5. **Identitäts-Notes** (`01 Kontext/`): User-Profil, Agent-Identität, Working-Agreement, Framework-Spiegel.
6. **Bereiche** (`04 Bereiche/_MOC.md` + je eine Note pro Lebensbereich) — alle mit Dataview-Queries.
7. **Inbox-Vorlage** (`02 Inbox/<datum> - Inbox Setup.md`) für Quick-Pickup mit 7-Tage-Haltezeit.
8. **Projekt-Hauptthema CHANGELOG** um Befüllungs-Eintrag erweitern mit Mnemosyne-IDs.

**Mnemosyne-als-Source-of-Truth:** Vault-Notizen spiegeln Mnemosyne-Memories, sind aber NICHT die Quelle. Mnemosyne-Recall bleibt im Memory-Layer, Vault ist Browse-Layer für den User. Mnemosyne-ID als Referenz in Vault-Note hinterlassen, damit SOT-Kette klar ist.

**NICHT in Vault-Notes:** Commit-SHAs, PR-Nummern, Issue-Nummern, File-Counts, Branch-Namen — 7-Tage-stale, gehört in Mnemosyne working-tier, nicht in langlebige Notizen.

## Dokumentations-Validierung durch Datenquellen-Audit

**Trigger:** User sagt "prüf ob das noch aktuell ist", "finde Drift", "Audit", "vergleiche mit der Live-Datenbank", "Quality-Gate für den Vault" oder bittet um eine systematische Abweichungsanalyse zwischen dokumentierten Annahmen und tatsächlichem System-/Datenbank-Zustand.

**Klassifikation:** Dieses Muster ist ein **Datenquellen-Audit** — die Live-Datenquelle (DB, API, Filesystem) ist die Source of Truth, die Dokumentation (Vault-Notes, Markdown-Dateien) ist das zu validierende Artefakt. Das ist NICHT dasselbe wie ein Doc-to-Doc-Cross-Reference (Repo-Dokumentations-Pflege, siehe unten).

### Workflow

| Phase | Was | Werkzeug | Output |
|---|---|---|---|
| **Phase 1: SOT-Identifikation** | Wer ist die Quelle der Wahrheit? DB? API? Live-Filesystem? | `terminal(sqlite3 .tables / .schema)`, `read_file`, `ls -la` | SOT-Liste: was wird auditiert gegen was |
| **Phase 2: Snapshot-Extraktion** | Vollständigen Tabellen-Dump oder Key-Metriken extrahieren | Python-Skript (sqlite3 via subprocess) → JSON-Dump nach `/tmp/` | JSON-Datei (2-3 MB, nie in Chat pasten) |
| **Phase 3: Vault/Quellen-Lesen** | Alle relevanten Notizen parallel lesen | `read_file` + `skill_view` auf Vault-Pfaden | Bestandsaufnahme der dokumentierten Annahmen |
| **Phase 4: Drift-Matrix** | Tabellen-Counts, Player-State, Zeitstempel, Topologie vergleichen | Python-Vergleichs-Script + manuelle Tabellen | Tabelle mit altem und neuem Stand |
| **Phase 5: Widerspruchs-Check** | Kreuzvergleich zwischen mehreren Vault-Quellen (widersprechen sie sich?) | 3-4 Notes parallel lesen | Liste widersprüchlicher Behauptungen |
| **Phase 6: Stale-Markierung** | Welche Notizen sind veraltet? Empfehlung: patchen oder Refresh-Hinweis einfügen | `freshness: YYYY-MM-DD` im Frontmatter, Re-Audit-Hinweis im Body | Stale-Matrix mit Patch-Empfehlungen |
| **Phase 7: Quality-Gate** | Selbsttests gegen die Output-Qualitätsregeln | siehe Quality-Gate-Abschnitt unten | Alle Tests grün |

### Wikilink-Resolution-Check (für Wiki-/Vault-Pages)

**Problem:** `[[target|label]]`-Wikilinks deren erstes Segment (`target`) keinem Dateinamen auf Disk entspricht. Erzeugt broken links im Vault/Wiki — die Seite wird über den Link nicht gefunden.

**Häufige Ursache:** Der Agent leitet den Slug aus dem Titel ab (z.B. `"Ornith-1.0-9B" → "ornith-1-0-9b"` oder `"ornith-1-0-9b-deepreinforce-ai"`), aber die Datei heißt tatsächlich `ornith-1.0-9b.md` (mit Punkten statt Bindestrichen). Der Wikilink `[[ornith-1-0-9b-deepreinforce-ai|Ornith-1.0-9B]]` zeigt dann ins Leere.

**Prävention beim Schreiben:** Direkt nach der Wikilink-Einfügung prüfen, ob das target-Segment als `*.md`-File existiert:
```bash
python3 -c "
import re, os, sys
page = sys.argv[1]
all_slugs = {}
for r,_,fs in os.walk(os.path.dirname(os.path.abspath(page))):
    for f in fs:
        if not f.endswith('.md'): continue
        all_slugs[re.sub(r'\.md$','',f)]=1
with open(page) as f:
    hits = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', f.read())
bad = [h for h in hits if h not in all_slugs]
if bad:
    print(f'BROKEN — unresolved wikilink targets: {bad}')
    sys.exit(1)
print('OK — all wikilinks resolve to existing files')
" /path/to/new/page.md
```

**Fix nachträglich (batch über N Pages):** Regex-Substitution über alle neuen/geänderten Pages, die das erste Segment jedes `[[X|Y]]` gegen tatsächliche Dateinamen validiert:
```bash
python3 <<'PY'
import re, os, sys
pages = sys.argv[1:] if len(sys.argv) > 1 else []  # pass list or glob
# collect all wiki slugs
all_slugs = {}
base = os.path.dirname(os.path.abspath(pages[0])) if pages else '.'
for r,_,fs in os.walk(base):
    for f in fs:
        if not f.endswith('.md'): continue
        all_slugs[re.sub(r'\.md$','',f)] = 1
# common wrong→right mapping (derived from actual slugs)
slug_map = {}
for slug in all_slugs:
    normalized = slug.replace('.','-').replace('_','-').lower()
    if normalized != slug:
        slug_map[normalized] = slug
pat = re.compile(r'\[\[([^\]|]+)(\|[^\]]+)?\]\]')
for page_path in pages:
    with open(page_path) as f:
        body = f.read()
    def fix(m):
        t = m.group(1).strip()
        l = m.group(2) or ''
        if t in slug_map and slug_map[t] != t:
            return f'[[{slug_map[t]}{l}]]'
        return m.group(0)
    new = pat.sub(fix, body)
    if new != body:
        with open(page_path,'w') as f: f.write(new)
        print(f'FIXED: {os.path.basename(page_path)}')
PY
```

**Pitfall:** Wikilinks mit zwei Pipes (`[[X||Y]]`) werden von Obsidian/Markdown-Viewern ebenfalls nicht aufgelöst — passiert gern beim Suchen/Ersetzen. Vor dem Fertig-Melden `grep -rn '||'` über alle neuen Pages laufen lassen.

**Siehe auch:** `references/wikilink-slug-validator.py` — standalone-Skript das den Resolution-Check batch-mode über alle Pages eines Verzeichnisses laufen lässt.

### Qualitätskriterien für Audit-Reports

Der Audit-Report selbst muss diese Regeln erfüllen (Pflicht-Check vor Fertig-Meldung).

> **Hinweis:** Diese Quality-Gates sind NICHT auf Audits beschränkt. Sie gelten
> für **jedes generierte Markdown-Dokument** — Obsidian-Notes, CheatSheets,
> Reports, Fix-Pläne. Der vollständige Workflow mit Iterations-Logik,
> typischen Fixes und `replace_all`-Pitfalls:
"references/self-test-document-generation.md",
    "references/wiki-page-set-verification.md"
  ]
| Regel | Ziel | Shell-Check |
|---|---|---|
| Em-Dashes (—) | ≤ 1 | `grep -c '—' datei.md` |
| En-Dashes (–) | 0 | `grep -c '–' datei.md` |
| Mid-sentence Boldface | 0 | `grep -cPn '(?<=\S)\*\*[^*]+\*\*' datei.md` |
| Inline-Header Bullet-Listen | 0 | `grep -cP '^- \*\*[A-Z]' datei.md` |
| Negative-Parallelism | 0 | `grep -cP 'kein \w+ (nötig\|erforderlich)' datei.md` |
| AI-Vokabeln | 0 | `grep -ciP '\b(crucial\|pivotal\|delve)\b' datei.md` |
| Wiki-Links | ≥ 5 | `grep -oE '\[\[[^]]+\]\]' datei.md \| wc -l` |

### Typische Audit-Befunde (Drift-Kategorien)

1. **Count-Drift** — Tabellen-Zeilen, File-Counts, Host-Counts sind anders als dokumentiert
2. **Zeitstempel-Drift** — In-Game-Clock, LastConnection, Update-Timestamps fortgeschritten
3. **Schema-Drift** — DB-Tabellen haben andere Spalten als angenommen (.schema X checken)
4. **Topologie-Drift** — Netzwerk-Hosts sind hinzugekommen oder verschwunden
5. **Player-State-Drift** — Position, Items, Missionen, GameOver-Status geändert
6. **Game-Frozen-Erkennung** — DB-MTime älter als 1 Tag, Savegame stabil (GameOver=1)

### Anti-Patterns

- **Nicht die Live-DB editieren** während das Spiel läuft (SQLite-Lock, Crash). Auf User-Exit warten.
- **Nicht Passwörter/Tokens im Klartext in den Report** — nur Längen-Buckets oder redacted-Werte.
- **Nicht "kein Drift" behaupten** ohne Map.Date, InfoGen.Clock, Logs.Count geprüft zu haben.
- **Vault-Notes nicht blind patchen** ohne Drift zu validieren — die Note könnte einen gültigen historischen Snapshot darstellen. Im Zweifel freshness updaten statt Zahlen überschreiben.
- **Quality-Gate nicht überspringen** — die 6 Selbsttests sind Pflicht nach jedem Audit-Report-Write.

### Siehe auch

- `references/live-db-audit-workflow.md` — Session-Detail und GreyHack-DB-Schema-Quirks
- `yuno-user-preferences` → Output Quality Gate — Formatierungsregeln für Reports

## Audit-Recovery Report (Dokumentation eines abgeschlossenen Recovery-Plans)

**Trigger:** Ein Multi-Task-Plan (z.B. Audit-Recovery, Bug-Bounty, Security-Patching) wurde vollständig abgearbeitet. Ein Abschlussdokument wird benötigt, das den gesamten Durchlauf — von der Ist-Analyse über die umgesetzten Tasks bis zur Meta-Lektion — zusammenfasst.

**Das ist NICHT:** Ein Datenquellen-Audit (SOT gegen Doku validieren), ein Katalog (N Quellen zusammenführen), oder eine einzelne Deploy-Notiz (ein Feature, ein Merge). Das ist der **Dokumentabschluss eines Plans mit mehreren Tasks**.

### Report-Struktur (Pflicht)

| Sektion | Zweck | Pflicht? |
|---|---|---|
| **Context** | Was war der Plan? Wer hat ausgeführt? Welcher Trigger? | ✅ Ja |
| **Reality-Check-Tabelle** | Verbatim aus dem Plan — alle Live-Verify-Ergebnisse, ✅/❌ pro geprüftem Pfad/Annahme | ✅ Ja |
| **Task-Disposition** | Alle Tasks mit Zeit-Schätzung, Total-Stunden, Abhängigkeiten | ✅ Ja |
| **Pitfall-Lesson** | Meta-Lektion aus diesem Durchlauf (Symptom → Root Cause → Fix → Guard) | ✅ Ja |
| **Cross-References** | Verwandte Memories, Pitfalls, File-Pfade, vorherige Reports | ✅ Ja |
| **Completion Status** | ✅-Checkliste mit jedem abgeschlossenen Schritt, Mnemosyne-Anchor-ID | ✅ Ja |
| **Was NICHT wieder einplanen** | Explizite Liste: welche Annahmen/Patches/Verschiebungen wurden gestrichen und WARUM | ⭐ Empfohlen |

### Quality-Gates (vor Fertig-Meldung)

| Check | Befehl | Ziel |
|---|---|---|
| Zeilenanzahl | `wc -l <report>` | ≥ 80 Zeilen |
| Cross-Reference-Files existieren | `ls -la <path>` pro referenziertem File | Alle existieren |
| Reality-Check-Rows vollständig | `grep -c '|' <report>` | Jede Plan-Zeile abgebildet |
| Memory-Anchor geschrieben | Mnemosyne `recall` nach ID | Status: verified |
| Plan-Pfad referenziert | `grep 'plan' <report>` | Absoluter Pfad zum Plan |

### Workflow

1. **Plan lesen** — `read_file` auf den Plan (insb. Reality-Check-Tabelle + Tasks)
2. **Verifizieren** — `ls -la` / `stat` auf alle referenzierten Pfade im Report (Pitfall #42 Prävention)
3. **Report schreiben** — Struktur aus der Tabelle oben, Reality-Check-Zeilen verbatim aus dem Plan
4. **Quality-Gates** — `wc -l`, Cross-Reference-Prüfung, Inhalts-Checks über Python-Inline-Assertions
5. **Mnemosyne-Anchor** — Erst NACH erfolgreicher Verifikation schreiben, dann Report-Status updaten
6. **Verify** — Memory `recall` auf den Anchor-ID, um Persistenz zu bestätigen

### Anti-Patterns

- ❌ Report schreiben, bevor alle referenzierten Pfade existieren (erzeugt dead links)
- ❌ Mnemosyne-Anchor vor der Verifikation schreiben (Anchor verweist auf potentiell korrupten Report)
- ❌ Annahmen aus dem Plan ohne Live-Verify übernehmen (Pitfall #42, in dieser Session validated)
- ❌ "Nicht wieder einplanen"-Liste vergessen — sonst wird im nächsten Durchlauf dasselbe nochmal diskutiert

### Siehe auch

- `references/audit-recovery-report-template.md` — Vollständiges Template mit Platzhaltern für alle Sektionen
- `self-improving` → Pitfall #42 — warum Live-Verify vor Report-Schreiben kritisch ist

---

## Multi-Source Catalog Creation

**Trigger:** User bittet um eine strukturierte Dokumentation (Katalog, Index, Registry, Matrix) die aus **N verschiedenen Quellen** zusammengeführt werden muss — z.B. Skill-Referenz + Vault-Notes + Daily-Notes + externe Docs. Diese Aufgabe unterscheidet sich von einem Datenquellen-Audit (live-SOT gegen Doku validieren) und von einer einfachen Entry-Format-Notiz (ein Thema, eine Session).

### Workflow

| Phase | Was | Beispiel (aus GreyHack-Bug-Katalog 2026-07-14) |
|---|---|---|
| **Phase 1: Quellen identifizieren** | Alle relevanten Dateien in 1–2 Batches lesen | `skill_view(greyhack → known-bugs.md)`, `read_file(Gaming-GreyHack.md)`, `read_file(Queen-Bee-Lab.md)`, Daily-Notes, dmz-handbook, Yuno-Mobile-MaxClaw-Setup — insgesamt 5+ Quellen |
| **Phase 2: Matrix-Struktur definieren** | Welche Spalten? Welche Sortierung? Welche IDs? | Bug-ID, Datei, Tool-Name, Symptom, Entdeckungsdatum, Severity, Workaround |
| **Phase 3: Daten parallel extrahieren** | Pro Quelle die relevanten Zeilen/Patterns notieren | Aus known-bugs.md: 14 Bug-Patterns mit NP-IDs. Aus Gaming-GreyHack.md: Tool-Landschaft-Tabelle (xmem-Status) |
| **Phase 4: Konflikte erkennen und auflösen** | Widersprechen sich die Quellen an irgendeiner Stelle? | known-bugs.md sagt xmem "✅ buildable", Filesystem zeigt leeres Verzeichnis → Auflösung: Fix auf Branch, nie gemerged (siehe greyhack SKILL.md → Build Success Rate → xmem branch-merge gap) |
| **Phase 5: Sektionen gliedern** | Haupttabelle + ergänzende Sektionen (Severity-Verteilung, Pattern-Kreuzverweise, Case-Studies, nächste Schritte) | Katalog (14 Bugs) + Cluster-Funde (4 Cross-Cutting-Patterns) + Case-Study (xmem) + Severity-Verteilung + Cross-Links |
| **Phase 6: Self-Test QA** | Vor Abschluss die Output-Qualität automatisiert prüfen | siehe Quality-Gates unten |

### Quality-Gates für Katalog-Erstellung

Vor jedem Katalog-Delivery müssen diese Selbsttests laufen:

| Check | Befehl | Mindestziel |
|---|---|---|
| Zeilenanzahl | `wc -l <datei>` | ≥ 100 (substantiell genug für einen Katalog) |
| Em-Dashes (—) | `grep -c '—'` | ≤ 1 |
| En-Dashes (–) | `grep -c '–'` | 0 |
| Wiki-Links | `grep -oE '\[\[[^]]+\]\]' \| wc -l` | ≥ 5 (Vault-Integration, Auffindbarkeit) |
| Mid-sentence Bold | `grep -cPn '(?<=\S)\*\*[^*]+\*\*'` | 0 |
| Inline-Header Bullets | `grep -cP '^- \*\*[A-Z]'` | 0 |
| Code-Blöcke | `grep -c '^```'` | ≥ 3 (Architekturdiagramm + CLI-Befehle)

**Fehler-Korrektur:** Wenn ein Test fehlschlägt, mit `patch(... replace_all=true)` korrigieren und erneut testen. Nicht den Fehler akzeptieren.

### Typische Katalog-Klassen

1. **Bug-Katalog:** N bekannte Bugs mit Severity, Workaround, Datum (dieser Session erstellt)
2. **Tool-Registry:** Alle Tools eines Projekts mit Build-Status, Branch, Test-Coverage
3. **Pattern-Index:** Querschnitts-Patterns über mehrere Code-Bereiche
4. **Source-of-Truth-Map:** Welche Quelle sagt was? Wo sind Widersprüche?
5. **Nächste-Schritte-Matrix:** Offene Aktionen mit Owner, Priorität, Deadline

### Anti-Patterns

- **Nicht nur eine Quelle verwenden** — der Wert des Katalogs entsteht aus der Quervernetzung von N≥3 Quellen
- **Nicht den Self-Test überspringen** — Em-Dashes häufen sich bei Tabellen-Dokumenten besonders an
- **Keine unaufgelösten Quellen-Konflikte akzeptieren** — wenn sich zwei Quellen widersprechen, muss die Auflösung dokumentiert sein (nicht nur einer Quelle glauben)
- **Nicht ohne Severity-Legende liefern** — P0/P1/P2 sind bedeutungslos ohne Definition der Stufen

### Siehe auch

- `references/catalog-creation-greyhack-bugs-2026-07-14.md` — Session-Detail des GreyHack-Bug-Katalogs (14 Bugs, xmem-Case-Study)
- `greyhack` SKILL.md → Build Success Rate → xmem branch-merge gap — konkretes Beispiel eines Quellen-Konflikts

## Post-Deployment Multi-Target Documentation Workflow

Nach einem **erfolgreichen Deployment** (PR-Merge + Live-Schaltung einer neuen Feature-Version) das volle Doku-Programm abfahren. Nicht nur eine Note schreiben — das wird sonst im Vault unsichtbar, weil kein MOC darauf zeigt.

**Workflow (in dieser Reihenfolge):**

1. **Projekt-Note in `03 Projekte/`** — Hauptdokumentation des Deployments: was wurde gemerged, welcher Service aktualisiert, wie getestet, Lessons Learned. Datei: `03 Projekte/<Projektname>/<Projektname>.md`
2. **Resource-Note in `05 Ressourcen/`** — Falls ein übergreifendes Pattern/Framework aus dem Deployment entstanden ist (z.B. Fable-5-Audit-Trail, Hardlink-Deployment, CI-Test-Filter-Strategie). Datei: `05 Ressourcen/<Pattern> - Audit-Trail & Workflow.md`
3. **MOC-Patches:** Jede neue Note muss von mindestens einem MOC verlinkt sein:
   - `MOC - Projekte.md` → Projekt-Zeile in der Projekte-Map einfügen, `letzter-review: YYYY-MM-DD` updaten
   - Themen-MOC (z.B. `MOC - KI-Architektur.md`) → Ressource + Sub-Projekt eintragen, `letzter-review` updaten
   - **Prüfung:** `grep "<Projektname>"` in beiden MOCs nach dem Patch
4. **Mnemosyne-Memories speichern** (scope=global, importance=0.65 bis 0.7):
   - Deployment-State: URL, Skin-Name, Live-Daten (Sessions, Tokens, etc.)
   - Pattern-Fakten: Framework-Version, Kosten, Trigger-Conditions
5. **`~/docs/system/` legacy mirror (optional):** Nur wenn der User explizit `~/docs/system/` nutzt oder zwischen Vault und Docs-System wechselt. Sonst weglassen — Vault ist bevorzugt.

**MOC-Post-Review-Checkliste (nach jedem Patch):**

| Check | Befehl |
|---|---|
| Projekt-Note existiert? | `ls -la "03 Projekte/<name>/"` |
| Resource-Note existiert? | `ls -la "05 Ressourcen/<name>.md"` |
| Projekte-MOC hat Eintrag? | `grep "<name>" "MOC - Projekte.md"` |
| Themen-MOC hat Eintrag? | `grep "<name>" "MOC - <Thema>.md"` |
| `letzter-review` aktuell? | `grep "letzter-review" "MOC - *.md"` |
| Mnemosyne gespeichert? | Memory-IDs in Projekt-Note referenziert |

**Anti-Pattern:** Eine Projekt-Note schreiben aber **kein MOC patchen** → die Note ist für den Vault-Browser unsichtbar (kein Wiki-Link-Ziel, kein MOC-Eintrag). Wird nur über direkte Suche gefunden. **Pflicht:** Jede neue Note bekommt mindestens einen MOC-Link.

**Dataview-Plugin:** Pflicht für MOCs. MUSS manuell in Obsidian Settings → Community Plugins aktiviert werden. In Reply erwähnen, nicht in Note. Queries-Snippets stehen in der Frontmatter-Sektion "Dataview-Queries".

## Obsidian-Plugins Quick-Reference

| Plugin | Zweck |
|---|---|
| Dataview | Live-Datenbank-Abfragen (MOCs) — Pflicht |
| Templater | Vorlagen + Datum-Auto (Daily Notes) |
| Calendar | Kalenderansicht für Daily Notes |
| Periodic Notes | Periodische Notizen (täglich/wöchentlich) |
| Excalidraw | Hand-drawn Diagramme |
| Mindmap | Struktur-Karten aus Headings |
| Tasks | Task-Management mit Dataview-Integration |

## Entry Format

Every entry follows the same template:

```markdown
# Title

**Datum:** YYYY-MM-DD
**Kontext:** Session-Summary / Anlass

## Ziel

Was sollte erreicht werden?

## Vorgehen

1. Schritt 1 (Befehl / Ansatz)
2. Schritt 2
3. …

## Dateien & Pfade

- `/home/bratan/some/path` → was wurde geändert
- `/etc/some/config` → Konfiguration

## Ergebnis

Was hat funktioniert, was nicht. Ggf. Screenshot/Log-Hinweise.

## Entscheidungen

Warum wurde Ansatz X statt Y gewählt? Welche Kompromisse?
```

## Guide & How-To Document Format

For setup-guides, installation walkthroughs, and technology tutorials
that explain **how to set something up**, not just what was done.

### Required elements

| Element | Zweck | Beispiel aus Session 2026-07-19 |
|---|---|---|
| **ASCII architecture diagram** | System-Überblick auf einem Blick | InfluxDB → HA → Grafana Pipeline |
| **Prerequisites section** | Hardware + Software + Wissen, das der Leser braucht | Watch 6 Classic, Android 10+, Docker |
| **Numbered phases** | Schrittweise Aufbau-Reihenfolge (Phase 1: DB, Phase 2: HA...) | Phase 1-6 |
| **Copy-paste-ready commands** | Jeder CLI-Befehl muss direkt ausführbar sein | `docker compose up -d`, `openssl rand -hex 32` |
| **Verification table** | Pro Phase: Check + Befehl + erwartetes Ergebnis | `curl localhost:8086/health` → `{"status":"pass"}` |
| **Known limitations** | Was nicht funktioniert + Workaround | SpO2 nur on-demand, HR 5-10s granular |
| **Date in title + footer** | `YYYY-MM-DD` im Titel, `Document version: v1.0` im Footer | Filename enthält Datum |

### Anti-Patterns

- ❌ Nur Text ohne Diagramm — der Überblick fehlt
- ❌ Befehle abgekürzt oder mit Platzhaltern die der Leser raten muss
- ❌ Keine Phasen-Reihenfolge — Setup-Schritte sollten chronologisch sein
- ❌ Keine Verification nach jeder Phase — der Leser merkt erst am Ende ob alles klappt
- ❌ Em-Dashes oder En-Dashes — durch Komma oder "bis" ersetzen (siehe Quality-Gates)

### Pitfalls (aus der Praxis)

- **Docker-Container-Namen** müssen eindeutig sein. Bei Multi-Stack-Setups Prefix nutzen
- **Health Connect Permissions** variieren zwischen Android-Versionen — immer beide Wege checken
- **Galaxy Wearable** nur für Pairing öffnen — danach schließen, sonst überschreibt es Health-Connect-Config
- **Date-Format**: immer `YYYY-MM-DD` im Dateinamen (`<topic>-<YYYY-MM-DD>.md`)
- **Kommentare in Code-Blöcken auf Deutsch**, Fachbegriffe auf Englisch lassen

### Siehe auch

- `references/guide-formatting-conventions.md` — Session-Detail mit Galaxy-Watch-6-Beispiel
- `self-test-document-generation.md` — vollständiger Self-Test-Workflow



For `/home/bratan/greyscripts`, document both system-level build/fix context and research/spec context:

- System/build fixes go under `~/docs/system/`, e.g. `greyhack-p0-build-fixes-YYYY-MM-DD.md`.
- Research outputs go under `/home/bratan/greyscripts/docs/security-research/`.
- Mini-specs go under `/home/bratan/greyscripts/docs/security-research/specs/`.
- Mini-tool implementation reports go under `~/docs/system/`, e.g. `greyhack-mini-tools-implementation-YYYY-MM-DD.md`.
- Always record branch policy: P0 before P1-P4, feature branch from `develop`, never touch `main` without explicit approval.
- Include exact build commands and real Greybel outputs.
- Separate resolved P0 blockers from open later research/tool candidates.

## Documentation Triggers

After any of these actions, offer to document:

1. **System change** (kernel removal, package purge, config edit)
2. **Hardware fix** (monitor EDID, GPU tuning, fan curves)
3. **Build** (new toolset, script collection, CLI project)
4. **Config migration** (hermes config, Thunderbird/Evolution, cron jobs)
5. **Debugging path** (something that took >5 steps to resolve)
6. **Cron delivery issue** (timeout, missing script, delivery_error)
7. **TypeScript/JS project fix** (tsc errors, jest failures, build fixes)

## Hermes V7 Project Documentation

For `~/hermes-zorin` (Branch: `Zorin-Hermes-alt` → `origin/Zorin-Hermes-alt`):

- **Build:** `npx tsc --noEmit` (type check) → `npx tsc` (build to `dist/`)
- **Test:** `npm run test` (jest, konfiguriert aber 0 tests)
- **Live-Test:** `node depp-live-test.js` (benötigt `OPENROUTER_API_KEY`)
- **Import-Convention:** `.js`-Suffixe in Imports (ESM-Style) → nur via `tsc`→`node dist/` ausführbar, NICHT via ts-node
- **Root:** `rootDir: "."` (wegen `cli/` + `src/`)

See: `references/typescript-build-pitfalls.md` for full error transcripts and fixes.

## TypeScript Project Documentation

For TypeScript/Node.js projects (like `~/hermes-zorin`), document:

- Build command: `npx tsc --noEmit` (type check) or `npm run build`
- Test command: `npm run test` (jest)
- LSP diagnostics: `npx tsc --noEmit 2>&1 | head -50`
- Common error patterns: type narrowing, duplicate modules, import path mismatches
- Fix verification: always re-run `tsc --noEmit` after fixes

### TypeScript Pitfalls (from hermes-zorin V7 development)

1. **`.js` Import-Suffixe + CommonJS**: `module: commonjs` + `.js`-Imports → ts-node kann Module nicht auflösen. Fix: `npx tsc` → `node dist/` ODER Imports ohne Suffix
2. **Type Narrowing in Compound Conditions**: TS narrows types after first check — extract to variables first
3. **Verdict vs Signal Type Confusion**: Don't compare against enum A when checking enum B
4. **Duplicate Module Detection**: `diff file1 file2` — if identical, delete the one with broken import paths. Nach Löschen: `rm -rf dist && npx tsc`
5. **Implicit `any` Cascade**: Fix the missing import, don't add `: any`
6. **rootDir Mismatch**: `rootDir` muss alle included Dateien enthalten (inkl. `cli/`)

Siehe auch: `references/typescript-build-pitfalls.md` für vollständige Session-Traces.

## GitHub-Wiki vs Obsidian-Vault: Format-Unterscheidung

Wichtige Trennung: **welche Wiki-Plattform** wird befüllt? Format und Cross-Reference-Syntax unterscheiden sich fundamental.

| Eigenschaft | GitHub-Wiki (`<repo>/wiki/`) | Obsidian-Vault (`~/Dokumente/Obsidian Vault/`) |
|---|---|---|
| Cross-Reference-Syntax | `[Label](Page-Name)` oder `[Label](relative/path.md)` | `[[Page-Name]]` oder `[[Page-Name\|Label]]` |
| Hierarchie | Flach (keine Unterordner im Wiki) | Julian-Ivanov-8-Ordner-Struktur |
| Sidebar | Statische `_Sidebar.md` + `_Footer.md` | Dynamisch via Dataview-MOCs |
| Index-Landingpage | `INDEX.md` (oder `Home.md`) | `MOC - Home.md` |
| Quality-Gates | Em-Dash ≤ 1, En-Dash = 0, Wiki-Links ≥ 5 | Selbe Gates |
| Wiki-Links-Check | `[Name](Name)` (Markdown-Links) | `[[Name]]` (Wikilinks) |

**Erkennungs-Heuristik:** Wenn das Repo ein `wiki/`-Verzeichnis mit `_Sidebar.md` und `_Footer.md` enthält → GitHub-Wiki. Wenn Pfade `01 Kontext/`, `02 Inbox/`, `04 Bereiche/` enthalten → Obsidian-Vault.

**Pitfall (aus Wiki-Befüllung 2026-07-22):** Obsidian-Wiki-Syntax `[[X]]` in GitHub-Wiki-Pages rendert nicht als Link, sondern als literaler Text. Umgekehrt funktioniert `[X](X)` in Obsidian, ist aber kein navigierbarer Wikilink. **Im Zweifel:** beide Formate in der `Siehe auch`-Sektion mischen ist OK — Obsidian resolved `[Label](Page-Name)` als Markdown-Link, GitHub rendert `[[X]]` als Plain-Text.

**Vorgehen beim Befüllen eines GitHub-Wikis (Quickstart/Installation/Changelog-Pattern):**

1. **Bestehendes Wiki inspizieren** — `ls <repo>/wiki/` zeigt vorhandene Pages + Sidebar/Footer
2. **INDEX.md (oder Home.md) lesen** — bestehende Verlinkungen + Kategorien verstehen
3. **Style des Wikis matchen** — Header-Hierarchie, Link-Syntax, Stand-Datum (`**Stand:** YYYY-MM-DD`) übernehmen
4. **3 Standard-Meta-Pages** wenn nicht vorhanden: `Quickstart` (5-Min-Guide), `Installation` (vollständiger Walkthrough), `Changelog` (Release-Highlights)
5. **Cross-Links als relative Markdown-Links** schreiben: `[Installation](Installation)` (nicht `[[Installation]]`)
6. **Sidebar/Footer konsistent halten** — bestehende Sidebar erweitern, nicht neu erfinden
7. **Self-Tests laufen** (Em-Dash/En-Dash/Wiki-Links-Count) — siehe `references/self-test-document-generation.md`

## 1-Index + N-Category Page-Set Authoring

**Trigger:** User bittet darum, einen strukturierten Satz Wiki-Pages zu erstellen — typischerweise 1 Index-Page + N Category-Pages (z. B. `Patterns-Index` + `Pattern-Build`/`Pattern-Files`/...). Das ist **NICHT** dasselbe wie 3 standalone Meta-Pages (Quickstart/Installation/Changelog) — Category-Sets haben strenge Per-Page-Struktur, Quervernetzung und spezifische Verification-Pitfalls.

**Erkennung:** Aufgabe enthält Aufzählung wie "Erstelle 7 Pattern-Wiki-Pages (1 Index + 6 Categories)" oder ähnliche N+M-Verteilung mit Quervernetzung.

### Workflow

1. **Datenquellen-Inventar** — Alle Quelldateien (z. B. `patterns/*/`, `patterns/verified/*.meta.md`) parallel lesen, Score + Pfad pro Pattern notieren
2. **Index-Struktur definieren** — Spalten: Name | Kategorie | Score | Pfad-zur-Category-Page. Alle Pfade als relative Markdown-Links auf `Pattern-<Kategorie>` (nicht auf die `.src`-Datei)
3. **Per-Category-Page** mit fixer Sektion-Struktur schreiben (siehe Template unten)
4. **Anti-Patterns-Sektion pro Page** — Mindestens 3-5 explizite "Was NICHT tun"-Punkte aus dem Pattern-Kontext ableiten. Das ist Pflicht — ohne diese Sektion ist die Page für die Codebase wertlos
5. **Self-Tests pro Page laufen** (siehe Verification unten) — Em-Dash/En-Dash müssen pro Page erfüllen, nicht nur aggregiert
6. **Glob-Double-Count-Pitfall kennen** — siehe Pitfall-Sektion unten

### Per-Page-Template (Category-Page)

```markdown
# Pattern-<Kategorie>

**Kategorie:** <kategorie>
**Quelle:** [patterns/<kategorie>/](https://github.com/.../tree/main/patterns/<kategorie>)
**Verifizierte Patterns:** <N>
**Stand:** YYYY-MM-DD

## Übersicht

<Kontext, wofür die Kategorie da ist, welches Referenzmuster aus src/ sie spiegelt>

## Verifizierte Patterns

### <pattern-name>
**Score:** XX/100 (Class A)
**Datei:** [patterns/<kategorie>/<pattern>.src](...)
**Meta:** [patterns/verified/<pattern>.meta.md](...)

**Zweck:** <ein Satz>

**Code-Pattern:**
```greyscript
<maximal ~30 Zeilen — bei längeren Patterns nur die Kern-Helfer extrahieren>
```

**Wann nutzen:** <konkrete Anwendungsfälle>

---

## Anti-Patterns (was NICHT tun)

- <Pitfall 1>
- <Pitfall 2>
- <Pitfall 3>

## Verwandte Kategorien

- [Pattern-<AndereKategorie>](Pattern-<AndereKategorie>)
- [Patterns-Index](Patterns-Index)
```

### Per-Page-Quality-Gates (Pflicht vor Fertig-Meldung)

Diese Gates sind **pro Page** zu erfüllen — nicht nur aggregiert über den ganzen Satz.

| Gate | Limit | Befehl |
|---|---|---|
| Em-Dashes (—) | ≤ 1 pro Page | `grep -c '—' <page>.md` |
| En-Dashes (–) | 0 pro Page | `grep -c '–' <page>.md` |
| Cross-Links | ≥ 3 pro Category-Page, ≥ 10 im Index | `grep -oE '\]\(Pattern-[A-Za-z]+\)' <page>.md \| wc -l` |
| Anti-Patterns-Punkte | ≥ 3 pro Page | `grep -cP '^- ' <page>.md` im Anti-Patterns-Abschnitt |
| Code-Snippet-Länge | ≤ 30 Zeilen pro Pattern-Block | `awk '/^```greyscript$/,/^```$/'` zählen |

**Pitfall (aus Session 2026-07-22):** `grep -c '—'` aggregiert über alle Pages kann 0 ergeben, während eine einzelne Page 5 Em-Dashes enthält. Immer pro Page prüfen, dann aggregieren.

### Glob-Double-Count-Pitfall (Verification)

Wenn der User die Verification per Shell-Glob formuliert wie:

```bash
ls /path/Pattern*.md /path/Patterns*.md | wc -l   # muss N ergeben
```

…dann matchen beide Globs typischerweise die Index-Page (sie heißt `Patterns-Index.md`, fängt also mit `Pattern` UND mit `Patterns` an). `wc -l` zählt die Zeilen, nicht die unique Files — und liefert **N+1** statt **N**.

**Detection:**
```bash
ls /path/Pattern*.md /path/Patterns*.md | sort -u | wc -l   # unique count
```

**Verify sofort nach Patch:**
```bash
grep -nE '^\|\|' vault/MOC*.md   # muss leer sein (Pipe-Vertipper)
```

**Richtige Verification-Sequenz für 1+N Page-Sets:**
1. `ls Pattern*.md Patterns*.md | sort -u | wc -l` — unique count
2. `wc -l <page>.md` pro Page — Substantiellität
3. Pro Page: `grep -c '—'`, `grep -c '–'`, `grep -cE '\]\(Pattern-'` — Quality-Gates
4. Optional: `for f in *.md; do echo "$f: em=$(grep -c '—' $f) en=$(grep -c '–' $f)"; done` — Übersichts-Tabelle

### Anti-Patterns

- **Nicht nur die Hauptseite schreiben, ohne Index-Verlinkung** — Index muss **erste oder letzte** Page sein, sonst finden Browser die Pages nicht
- **Nicht das `.src`-File komplett pasten** — bei Patterns > 30 Zeilen nur die Kern-Helfer extrahieren, sonst wird die Wiki-Page unleserlich
- **Nicht ohne Anti-Patterns-Sektion liefern** — das Pattern-Wiki dokumentiert "so macht man's richtig" nur sinnvoll im Kontrast zu "so nicht"
- **Nicht externer Quell-Link ohne GitHub-URL** — relative Markdown-Links funktionieren in GitHub-Wiki nicht zuverlässig; immer `https://github.com/owner/repo/blob/main/...` nutzen
- **Nicht pro Page aggregierte Gates prüfen** — Gates sind per Page; eine Seite mit 5 Em-Dashes fällt durch, auch wenn die anderen 0 haben

### Siehe auch

- `references/wiki-page-set-verification.md` — Standalone-Skript für Page-Set-Self-Tests inklusive Glob-Double-Count-Detection

## Repository Documentation Maintenance

For maintaining README, CHANGELOG, ROADMAP, NAVIGATION, and cross-references in **GitHub project repos** (e.g. `~/greyhack-tools/`).

### Workflow

1. **Inventory** — Collect all `.md` files (exclude `backups/`, `.git/`, `de/`): `find . -name "*.md" -not -path "./backups/*" -not -path "./.git/*" | sort`
2. **Dead-link scan** — Use `search_files(target='content', pattern='...')` to find stale references across the whole repo
3. **Audit cross-links** — Check that files reference each other (README links to CHANGELOG, NAVIGATION links to README, etc.)
4. **Verify numbers** — Count actual artifacts (`.src` files, tool directories) and compare against claims in meta-docs
5. **Apply fixes** — Use `patch` for targeted edits across multiple files
6. **Verify** — Write a temporary verification script in `/tmp/hermes-verify-*.py` that checks:
   - Dead links (e.g. `docs/CHANGELOG.md` → `CHANGELOG.md`)
   - Date ordering in CHANGELOG (newest first)
   - Cross-references between README/CHANGELOG/ROADMAP
   - Actual file counts match doc claims
7. **Cleanup** — Remove verification script after run

### Key commands for repo doc maintenance

```bash
# Find all broken references
search_files(target='content', pattern='docs/CHANGELOG\\.md', path='~/repo/')

# Count actual files (exclude backups, .git)
find . -name "*.src" -not -path "./backups/*" -not -path "./.git/*" | wc -l

# Verify all cross-references
# Write a focused Python script to /tmp/ and run it
```

set -euo pipefail
### Common fixes

| Problem | Fix |
|---------|-----|
| Moved file, dead link | `patch(old_string, new_string)` with exact paths |
| Outdated counts | Re-scan repo and update all affected docs |
| Missing file reference | Add link to Quick-Links or table of contents |
| CHANGELOG dates out of order | Regex `^## (\d{4}-\d{2}-\d{2})` and sort |

See `references/repo-doc-workflow.md` for a full session trace.

## Entity Consolidation (Merge & Re-link)

When two pages in a documentation tree cover the same ground, merge one into the
other and rewrite every inbound wikilink across all files.

**Quick reference:** Find all links to the absorbed slug → multi-file V4A patch →
verify zero residual `grep` hits → delete absorbed file → update index + log.

Full workflow with worked example in `references/entity-consolidation.md`.

## Language Conventions

- **Write in German** unless the user explicitly asks for English
- Be specific with **exact file paths** and **exact commands run**
- Include the **error messages** that were encountered and how they were resolved
- Keep entries **browseable** — use headings, tables, and code blocks
- Link between related entries (e.g., "siehe auch GPU-Tuning")

## User Preference: Basti

- Basti wants detailed docs ("mehr Tiefe, nicht Quick-and-Dirty")
- Prefers CLI-level precision: exact commands, full paths, no hand-waving
- Docs are for **cross-session context** — so a new model after a switch can
  get up to speed immediately

## README.md (Index File)

Maintain a README.md that serves as the table of contents:

```markdown
# System-Dokumentation

Übersicht aller dokumentierten Builds, Fixes und Konfigurationen.

## Hardware
- Monitor EDID Fix — Acer XB240H, reduced-blanking
- GPU & Gaming — RTX 5060, GameMode Hooks
- CPU Tuning — intel_pstate, EPP, powerprofilesctl

## Software
- Hermes Config — Profile, Providers, Cron
- Greyhack Tools — Bratan's Arsenal v2.0

## Maintenance
- Cleanup Workflow — Regelmäßige Systempflege

## Projekte
- Greyhack Arsenal — 12 GreyScript Tools
```

Update the README.md every time a new entry is added so it stays current.

## Pitfalls

1. **Don't duplicate memory.** Memory captures who the user is and what's stable.
   Documentation captures *what changed* and *how*. If it's a procedural how-to
   that will be reused, it belongs here as a doc entry.
2. **Don't duplicate skills.** Skills capture *how to do something* for the agent.
   Documentation captures *what was done* for the user. Different audiences.
3. **Keep docs shallow.** Max 3 levels of nesting (`01-hardware/`, not
   `01-hardware/01-gpu/02-nvidia/03-rtx-5060/…`).
4. **Offer, don't force.** After a change, ask: "Soll ich das dokumentieren?"
   Let the user decide.
5. **Never document secrets.** API keys, passwords, tokens, or personal emails never go into the doc tree. Use memory or env vars instead.
6. **If a secret was pasted in chat:** do not transcribe the value into documentation. Document only that the secret was treated as exposed, rotation was recommended, and no value was stored.
7. **Docker backend: Repo paths don't exist in the container.** When the agent runs in Docker terminal backend (`terminal.backend: docker`), all file tools operate inside the container — not on the host. If the user references a host repo path like `/home/bratan/my-project`, `cd`/`read_file`/`search_files` will fail with "No such file or directory". Do NOT retry the same path, guess contents, or fabricate results. Instead: (a) ask the user to mount the repo into the container with `-v`, (b) ask for `docker cp` of specific files, or (c) provide the fix as a patch the user applies on the host. Early detection: if `ls /home/` shows only `pn` (not the user's real home), you're in an isolated backend — adapt immediately.
8. **MOC-Patch-Tabellen-Header-Vorsicht (2026-07-10).** Beim `patch()` auf Markdown-Tabellen mit Header `| Note | Cluster |\n|---|---|` ist `old_string` mit nur einer Zeile risikoreich — andere MOCs benutzen denselben Header und der Patch könnte theoretisch mehrfach matchen. **Lösung:** Bei Tabellen-Patches immer **2+ Zeilen als `old_string`** (Header + erste Daten-Zeile) nehmen, oder `replace_all` mit Bedacht. Achte außerdem darauf, dass `new_string` den Markdown-Trenner `|` nur einmal am Zeilenanfang hat — `|| Note | Cluster |` ist ein häufiger Vertipper-Symptom (doppel-Pipe nach Sektion-Heading). **Verify sofort nach Patch:** `grep -nE '^\|\|' vault/MOC*.md` muss leer sein.

## Event-Tracking mit Cron-Updates

Für Multi-Day-Events (Esports-Turniere, Sport-Events, Konferenzen) das Muster:
Schedule-Doc anlegen → täglichen Update-Cron → Archive-Cron nach Event-Ende.

Details in `references/event-tracking-workflow.md`:
- Workflow: initialer Schedule → Update-Cron → Archive-Cron
- Live-Score-Quellen: Liquipedia, HLTV, Polymarket (bester Fallback)
- Cron-Prompt-Aufbau, Pitfalls (Zeitzonen, Truncation, Badges)

## Multi-Agent Deep Research Docs

For sessions that spawn parallel research experts (3+ agents), use the
enhanced template in `references/deep-research-template.md`:

- **Master-Bericht** — Full research results + fixes + roadmap
- **Retrospektive** — What worked, what didn't, metrics, improvements
- **README-Update** — Index entry linking to both

This produces a 3-document set per research round instead of a single flat file.
