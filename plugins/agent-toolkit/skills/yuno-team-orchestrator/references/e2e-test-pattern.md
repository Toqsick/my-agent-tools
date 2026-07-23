# E2E Multi-Domain Delegation Pattern

> Gelernt aus dem E2E-Test vom 2026-07-07 (Bundle-Showcase-Landing-Page).
> Dieses Pattern ergänzt das Multi-Persona Fix-Loop Pattern aus dem Haupt-SKILL.md mit dem **Pre-Preparation-Layer** für parallele Subagent-Dispatches.

## Das Problem

Multi-Domain-Tasks brauchen mehrere Subagenten parallel. Jeder Subagent bekommt `delegate_task(goal=..., context=...)`. Aber **wie viel Kontext** muss rein? Zu wenig → Subagent halluziniert falsche Annahmen. Zu viel → Tokens verschwendet, weil jedes Subagent denselben Projekt-Überblick bekommt.

## Das Pattern: Context-Injection-Matrix

### Struktur des Context-Parameters

Jeder Subagent-Briefing besteht aus diesen 6 Schichten:

```python
context = f"""
Du bist die **{AGENT_ROLLE}** im Yuno 7-Agent-Team.
(siehe ~/Downloads/team-roster.md für deine volle System-Prompt und Rolle)

KONTEXT FÜR DICH:
- {PROJEKT_KONTEXT: was der agent wissen muss}
- {TASK_UMFELD: welche anderen agents parallel arbeiten}
- {STATS: zahlen, daten, facts}

{ZU_TUN_SECTION}

OUTPUT-FORMAT (WICHTIG - präzise befolgen):
{FORMAT_SPEC: exact spec wie der output aussehen soll}

{QUALITY_BAR}

{ANTI_PATTERNS}

Antworte am Ende auf Deutsch.
"""
```

### Schichten im Detail

| # | Layer | Zweck | Beispiel |
|---|-------|-------|----------|
| 1 | **Rollen-Definition** | Identität + Scope aus team-roster.md | `Du bist der Researcher...` |
| 2 | **Projekt-Kontext** | Warum dieser Task existiert | `Ziel: Marketing-Landing-Page auf GitHub-Pages` |
| 3 | **Task-Umfeld** | Welche anderen Agents parallel laufen | `Designer hat index.html, Writer hat copy.json` |
| 4 | **Stats + Daten** | Fakten, die der Agent braucht | `5 Bundles: Code 90 Skills / Design 35 / ...` |
| 5 | **Output-Format** | Exakte Spezifikation (JSON-Schema / Markdown-Template) | `Speichere nach /tmp/...` und zeige `{}`-Block |
| 6 | **Quality-Bar + Anti-Patterns** | Was NICHT tun + Mindestqualität | `Keine fabrizierten Quotes`, `Mindestens 5 Quellen` |

### Anti-Patterns für Context-Injection

- **Zu viel Kontext = Rauschen:** Nicht den gesamten 12 KB team-roster.md in jedes Context-Feld kopieren. Nur die Rolle + die spezifische Tabelle.
- **Zu wenig Kontext = Halluzination:** Fehlende Format-Specs führen zu Output, den kein anderer Agent parsen kann.
- **Sprach-Direktive nicht vergessen:** `Antworte am Ende auf Deutsch.` — Subagents haben kein Memory der Conversation.
- **Stats nicht in 2 Subagents inkonsistent halten:** Gleiche Bundle-Größe in Researcher + Designer + Writer → Single Source of Truth vorher definieren.

## Data-Contract Schema Definition (Decompose-Phase)

> **Gelernt aus dem E2E-Test vom 2026-07-08:** Writer lieferte `meta/hero/features/get_started/repo`, spec verlangte `hero/bundles/why_yuno/faq/final_cta/footer`. Engineer's Build-Script wrappte automatisch (Glückstreffer), aber Designer zog parallel sein eigenes 41 KB HTML — niemand hatte die Data-Contracts synchronisiert.

### Das Problem

In der Decompose-Phase sagst du `"Writer schreibt Copy"` und `"Engineer baut Template"`. Ohne expliziten Data-Contract entstehen Schema-Driften:

```
Researcher: ~/Downloads/team-roster.md → eigene Struktur
Designer:  style-tokens.json → eigenes Schema
Writer:    copy.json → wieder anderes Schema (flach, kein copy-Envelope)
Engineer:  index.html.template → erwartet {{copy.hero.x}}
```

**3 verschiedene Schemas** für denselben Topic — Integration nur per Auto-Wrap gerettet.

### Der Fix: Data-Contract in der Decompose-Phase

Jeder Parallel-Dispatch muss **vor** `delegate_task` ein explizites Data-Contract-Objekt definieren:

```python
# In der Decompose-Phase (Parent):
DATA_CONTRACT = {
    "copy.json": {
        "schema_version": "1.0",
        "paths": {
            "hero.eyebrow": "string, max 40 chars",
            "hero.headline": "string, max 80 chars",
            "features.items[]": "array von {icon, title, description}",
            "bundles": "array von {name, skills_count, size_mb, accent_color}",
            "why_yuno": "array von {icon, title, description}",
            "faq": "array von {question, answer}",
            "cta": "{label, href}",
        },
        "filename": "/tmp/yuno-landing-page/copy.json"
    },
    "style-tokens.json": {
        "schema_version": "1.0",
        "colors": {
            "bg": "hex color",
            "fg": "hex color",
            "accent": "hex color per bundle"
        },
        "filename": "/tmp/yuno-landing-page/style-tokens.json"
    },
    "index.html": {
        "constraint": "self-contained, <500kb, inline SVG favicon",
        "theme": "light/dark switcher mit localStorage",
        "filename": "/tmp/yuno-landing-page/index.html"
    }
}
```

**Jeder Subagent-Briefing bekommt nur seinen Teil des Contracts:**
- Writer: `"copy.json Schema: {hero.headline: string, hero.subheadline: string, bundles: [{name, skills_count, ...}]}"`
- Designer: `"style-tokens Schema: {colors: {bg, fg, accent}} + index.html muss self-contained sein"`
- Engineer: `"Erwarte copy.json in Schema {hero: {headline, subheadline}, bundles: [{name, skills_count}]}"`

### Wann Auto-Wrap akzeptabel ist

Der Engineer's Auto-Wrap (`if "copy" not in data → wrap`) war ein **Glückstreffer**. Er funktionierte weil:
1. Writer-Keys (`meta`, `hero`, `features`) sind Teilmenge von Engineer's `copy.`-Pfaden
2. Die Template-Engine die Keys automatisch als `copy.hero.x` behandelt

**Nicht verlassen:** Wenn der Writer ein komplett anderes Schema liefert (z.B. `content.headline` statt `hero.headline`), hilft auch Auto-Wrap nicht. Der Data-Contract in der Decompose-Phase ist der einzige verlässliche Schutz.

### Token-Naming Convention Protocol

> **Gelernt aus dem E2E-Test v2 (2026-07-08):** Designer nutzte `{{copy.hero.eyebrow}}` im Template, Engineer's Template-Engine erwartete `{{hero.eyebrow}}` (ohne `copy.`-Prefix). Build-Script musste beide Notationen via Auto-Wrap + Prefix-Strip unterstützen.

#### Das Problem

In einer Multi-Agent-Pipeline mit Template-Engine gibt es **drei mögliche Token-Naming-Conventions** — und jeder Agent kann eine andere wählen:

```
Designer:    {{copy.hero.eyebrow}}   — "alles unter einem copy-Namespace"
Writer:       hero → "eyebrow": ... — flaches JSON ohne Namespace
Engineer:    {{hero.eyebrow}}        — "direkter Dot-Path ohne Envelope"
```

Das Problem: Der **Designer schreibt das Template**, der **Writer liefert die Daten**, der **Engineer baut den Renderer**. Alle drei kommunizieren über Tokens — aber wenn sie verschiedene Naming-Conventions annehmen, passen die Bausteine nicht zusammen.

#### Der Fix: Token-Naming im Data-Contract spezifizieren

In der Decompose-Phase muss Yuno **vor dem ersten Dispatch** die Token-Naming-Regel definieren und in ALLE Agent-Briefings injizieren:

```python
TOKEN_SPEC = """
Token-Naming Rule: **{{copy.<section>.<field>}}**

Prefix jedes Tokens mit `copy.` gefolgt von der Section (hero, bundles, why_yuno, faq, cta, footer).

Beispiele:
  ✅ {{copy.hero.headline}}       — Hero-Überschrift
  ✅ {{copy.hero.eyebrow}}        — Hero-Eyebrow
  ✅ {{copy.bundles.[].name}}     — Bundle-Name (im #each-Block via this.name)
  ✅ {{copy.faq.[].question}}     — FAQ-Frage

Falsch (nicht verwenden):
  ❌ {{hero.headline}}            — fehlt copy.-Prefix
  ❌ {{copy.hero.headline.text}}  — zu tief verschachtelt
  ❌ {{headline}}                 — kein Section-Kontext
"""
```

**Jeder Subagent-Briefing bekommt diese Spec:**
- **Designer:** Schreibe Template-Tokens im Format `{{copy.<section>.<field>}}`
- **Writer:** Strukturiere copy.json als `{hero: {...}, bundles: [...], ...}` (Engine wrappt automatisch in `copy`-Envelope)
- **Engineer:** Template-Engine interpretiert `{{copy.X.Y}}` + unterstützt Auto-Wrap für flache JSON-Keys

#### Backcompat-Strategie bei Schema-Drift (Plan B)

Selbst mit Token-Spec kann es zu Drift kommen. Definiere im Engineer-Briefing einen Backcompat-Plan:

```python
# 1. Auto-Wrap: Prüfe ob Top-Level-Keys ohne "copy"-Envelope existieren
if "copy" not in data:
    copy_keys = {"meta", "hero", "features", "bundles", "why_yuno", "faq", "cta", "footer"}
    if copy_keys & set(data.keys()):
        data = {"copy": data}
        log.warning("Auto-wrapped writer JSON in copy-Envelope")

# 2. Prefix-Strip: Prüfe ob Tokens in copy.-Form im Template
#    aber Daten haben keinen copy-Key → strip Prefix
if "copy" not in flatten(data):
    TOKEN_RE = re.compile(r'\{\{(?![#/])copy\.([^{}]+?)\}\}')
    # Ersetzt {{copy.hero.x}} durch {{hero.x}} im Template
```

#### Wann die Token-Spec kritisch ist

| Multi-Agent-Szenario | Token-Spec nötig? | Grund |
|---|---|---|
| Designer + Writer + Engineer **parallel** | 🔴 **Zwingend** | Alle 3 brauchen gleiche Naming-Convention |
| Designer allein (self-contained HTML) | 🟢 Nicht nötig | Keine Daten-Integration nötig |
| Writer + Engineer **sequenziell** | 🟡 Empfohlen | Engineer hat Writer-Output als Referenz |
| Agent-B nutzt Agent-A's Output als Input | 🔴 **Zwingend** | Format muss kompatibel sein |

## Data-Path Decision: Designer-HTML vs Template-Engine

> **Gelernt aus dem E2E-Test vom 2026-07-08:** Designer baute 41 KB self-contained HTML mit Theme-Switcher + Bundle-Grid. Engineer baute parallel ein 6 KB Template + Build-Script. Ergebnis: `make all` produzierte 6 KB Output und ignorierte das Designer-HTML komplett.

### Die Zwei-Wege-Entscheidung

In der Decompose-Phase muss Yuno **einen Weg wählen**:

| Weg | Beschreibung | Wann | 
|-----|-------------|------|
| **A) Designer liefert finales HTML** | Designer baut vollständige, self-contained index.html. Engineer baut nur CI/CD + optional Serve-Config. Kein Template-Engine nötig. | Designer-Updates sind selten, Page ist einmalig, Render-Maschine wäre overkill |
| **B) Designer liefert Tokens + CSS** | Designer liefert style-tokens.json + ggf. CSS-Blöcke. Engineer baut Template + Build-Script. Writer's Copy + Style-Tokens fließen über Template-Engine zusammen. | Wiederkehrende Pages, dynamischer Content, A/B-Testing geplant, spätere Updates ohne Designer |

### Im konkreten Fall: Weg B war richtig, aber nicht kommuniziert

Der Engineer hatte Weg B implementiert (Template-Engine + CI/CD). Der Designer wusste nichts davon und lieferte Weg A (vollständiges HTML). **Beide haben gearbeitet, aber die Outputs waren inkompatibel.**

**Fix im Decompose-Briefing:**
```
Designer: Liefere style-tokens.json + CSS-Blöcke + Layout-Beschreibung.
          Kein finales HTML — das wird aus Template + Copy + Tokens gebuildet.
Engineer: Erwarte style-tokens.json + copy.json. Baue Template das beide merged.
```

## Pre-Verifier Integration Build Test

> **Gelernt aus dem E2E-Test vom 2026-07-08:** Der `make all`-Run VOR dem Verifier-Gate (ausgeführt vom Parent, nicht vom Verifier) fand 3 Integration-Issues: Schema-Mismatch, Designer-HTML ignored, Build-Script trunkiert. Ohne diesen Pre-Check hätte der Verifier diese Issues gefunden — aber einen FAIL + Fix-Loop verursacht.

### Warum ein Pre-Verifier Check?

Der Verifier-Subagent ist teuer (~200s + 40+ API-Calls). Wenn er nur "fail - schema mismatch, fix and resubmit" sagt, war das eine teure Runde für einen Fehler, den der Parent in 5s selbst finden konnte.

### Mandatory Step

```
Nach Subagent-Outputs (alle 4+ da) → BEVOR Verifier dispatched wird:

   1. Existence-Check:  Alle erwarteten Files da? (ls -la /tmp/project/)
   2. Schema-Check:     copy.json hat alle erwarteten Keys? (python3 -c "import json; d=json.load(...)")
   3. Build-Test:       make all erfolgreich? (cd /tmp/project && make all)
   4. Sanity-Check:     HTML <500kb? Keine unresolved Tokens? Doctype vorhanden?
   5. Integration-Gap:  Haben Designer + Engineer den gleichen Data-Path? (Weg A oder B)
   6. Log-Analysis:     Build-Output auf errors/warnings scannen

Nur bei PASS → Verifier dispatchen.
Bei FAIL → Fix selbst (Parent-Direct) und Re-Test, bevor Verifier losgeschickt wird.
```

### Spareffekt

| Subagent | Ohne Pre-Verifier | Mit Pre-Verifier | Ersparnis |
|----------|-------------------|------------------|-----------|
| Engineer | 205s + 21 Calls | 205s + 21 Calls (gleich) | — |
| Verifier | 200s + 40+ Calls | 0 (Pre-Catch → Parent-Direct Fix) | 200s + 40 Calls |
| Total | 405s + 60+ Calls | 205s + 21 Calls | **~50% Zeit** |

Check: `cd /tmp/project && make all` dauert <5s. Eine Verifier-Runde ~200s.

## Deployment-Readiness Snapshot (FINAL Gate)

> **Gelernt aus dem FINAL Quality-Gate vom 2026-07-08:** Der Verifier prüfte nicht nur Code-Qualität, sondern die **ganze Deployment-Pipeline** — und fand 1 BLOCKER + 4 MAJOR Issues.
> Kern aller BLOCKER: Designer-HTML (41 KB) und Pipeline-Output (6 KB) waren zwei verschiedene Seiten.

### Wann den Snapshot nehmen

Nachdem Verifier alle Subagent-Outputs gesammelt hat, **bevor** eine fix-loop oder deploy-entscheidung getroffen wird. Der Snapshot beantwortet: "Wenn ich jetzt deployed: was sehe ich im Browser?"

### Snapshot-Commands

```bash
# 1. Was landet auf dem Server?
ls -la dist/
wc -c dist/index.html
head -5 dist/index.html

# 2. Was hat der Designer gebaut?
wc -c index.html  # oder style-tokens.json + copy.json
wc -c style-tokens.json copy.json

# 3. Größen-Vergleich
# Pipeline < 25% von Designer-Größe → BLOCKER: deployed die falsche Seite
```

### HTML-Comparative Smell Tests

Wenn sowohl Designer- als auch Engineer-Artefakte existieren, prüfe diese 4 schnellen Checks:

```bash
# 1. Section-Count — Designer hat 5+, Pipeline hat 1: BLOCKER
grep -c "<section" index.html        # Designer's Sections
grep -c "<section" dist/index.html   # Was deployed wird

# 2. Bundle-Count — Designer listet 5, Pipeline listet 3: MISSING CONTENT
grep -cE "(bundle--|Skill.</h3>)" index.html
grep -cE "(bundle--)" dist/index.html

# 3. Bundle-Name-Check — Designer-Bundles müssen in Pipeline-Output reflektiert sein
python3 -c "
html = open('index.html').read()
bundles = ['Code', 'Design', 'Productivity', 'Security', 'Research']
deployed = open('dist/index.html').read()
missing = [b for b in bundles if b not in deployed]
print(missing)  # Leere Liste → OK
"

# 4. Copy-Schema-Mismatch — Writer-Keys müssen zu Designer-HTML-Section-Namen passen
python3 -c "
import json
keys = list(json.load(open('copy.json')).keys())
sections = [l for l in open('index.html') if 'id=\"' in l and '#' not in l]
print('copy.json keys:', keys)
print('HTML section ids:', sections[:6])
"
```

**Wenn mehr als 1 dieser Checks fehlschlägt → BLOCKER: Integration Bruch.**
Pipeline deployed eine andere Page als der Designer gebaut hat.

### Common BLOCKERs bei Landing-Page-Deploys

| Fehler | Erkennung | Fix |
|--------|-----------|-----|
| **Designer-HTML wird ignoriert** | `wc -c` Faktor >3× Differenz | Designer-HTML ins Template integrieren ODER Pipeline-Output durch Designer-HTML ersetzen |
| **Writer-Copy stimmt nicht mit Designer-Sections** | `grep -c section` ≠ Writer-Keys | Data-Contract in Decompose-Phase definieren (siehe oben) |
| **Cache-Key zeigt auf nicht-existierende Files** | `actions/setup-python@v5` mit `cache-dependency-path` auf fehlendes `requirements.txt` | Entfernen (stdlib-only) oder leere Datei anlegen |
| **Path-Filter unvollständig** | Änderungen an `style-tokens.json` triggern keinen CI-Run | Alle Build-Input-Files in `paths:` aufnehmen |

## Verifier-Gate Pre-Preparation

**Wichtigste Erkenntnis:** Erstelle das Verifier-Gate-Script **BEVOR** die Subagents fertig sind — nicht danach.

```python
# Vor dispatch:
write_file("/tmp/verify.sh", """
# Phase 1: Formate prüfen (alle Files da? JSON/HTML/YAML valid?)
# Phase 2: Inhalt prüfen (Stats stimmen? Keine Lücken?)
# Phase 3: Deployment-Readiness (Was landet auf dem Server? - siehe Snapshot oben)
# → PASS oder FAIL mit konkreten Fix-Items
""")

# Subagents dispatchen (parallel):
delegate_task(tasks=[...])

# Nachdem alle fertig:
bash /tmp/verify.sh  # automatischer Gate
```

### Warum Pre-Preparation?

1. **Sachliche Prüfung:** Das Gate wird definiert bevor man die Outputs kennt — kein "Hmm, das ist schon OK" Afterthought-Bias.
2. **Fix-Items sind konkret:** Der Gate sagt nicht nur "FAIL" sondern hat konkrete Checks mit Zeilen-Nummern.
3. **Wiederverwendbar:** Selbes Gate-Script kann in CI/CD wandern.
4. **Deployment-Fokus:** Der Snapshot sagt "was passiert wenn ich deployed" — kein rein technischer Gate.

## E2E-Quality-Bar (aus SOUL.md §Routing)

Bevor ein Multi-Domain-Output an den User geht:

- [ ] Jeder Subagent-Output hat Source-Citations / file-path:line_number / Test-Run-Output
- [ ] Alle Facts geprüft, kein Halluzination
- [ ] Format passt zum Medium (Code, Design-Artifact, Doc, ...)
- [ ] Verifier-Subagent hat PASS ausgesprochen mit konkreten Strengths + Issues
- [ ] Bei FAIL: Fix-Items aufgelistet, nicht stillschweigend durchgewunken
- [ ] Deployment-Readiness Snapshot genommen: `wc -c`-Vergleich, Section-Count, Bundle-Count
- [ ] Cache-Key + Path-Filter in CI geprüft (nicht nur Build, auch Pipeline-Konfiguration)

## Checklist vor jedem Parallel-Dispatch

```markdown
## Pre-Flight-Check

- [ ] Context-Layer 1–6 alle definiert → in delegate_task(task.context) injizieren
- [ ] Output-Format-Specs sind von allen Subagents gleich referenziert (keine Inkompatibilität)
- [ ] Stats sind zwischen Subagents konsistent (Single Source of Truth)
- [ ] Verifier-Gate-Script vor dispatch erstellt
- [ ] Mnemosyne-Pin gesetzt (bei session-switch-Risiko)
- [ ] todo-Liste mit task-ids angelegt (Trackbarkeit)
- [ ] Sprach-Direktive für Deutsch in jedem Context
- [ ] Pfade für Output-Dateien sind konsistent (/tmp/...)
- [ ] Data-Path-Wahl (Weg A oder B) explizit kommuniziert — nicht implizit
- [ ] Token-Naming-Spec im Data-Contract definiert ({{copy.X.Y}} vs {{X.Y}} vs ...)
- [ ] Dispatch-Form (Parallel / 2-Wave / Chained) anhand Decision Matrix gewählt
```

## Subagent Dispatch-Strategie

### Parallel-vs-Sequential Decision Matrix

> **Gelernt aus dem E2E-Test 2026-07-08 (v1→v2):** v1 dispatchete ALLE 4 Agents parallel → Designer + Engineer bauten kollidierende Deliverables. v2 dispatchete sequenziell: Designer → Writer → Engineer → Verifier. Die Wahl zwischen Parallel und Sequential ist der **kritischste Single-Point-of-Failure** in Multi-Agent-Orchestrierung.

#### Entscheidungsregeln

| Dispatch-Form | Output-Abhängigkeit? | Output-Format bekannt? | Beispiel |
|---|---|---|---|
| **🟢 Parallel** | Keine — jeder Agent liefert unabhängigen Output | Ja — Schema vorher definiert | Researcher findet arxiv-Links, Designer baut Style-Tokens |
| **🟡 Sequential (2 Waves)** | Welle 2 braucht Welle-1-Output | Ja — aber konkretes Data-Shape variiert | Researcher → Designer (Design braucht Research-Facts) |
| **🔴 Sequential (Chained)** | Output von Agent A ist Input für B, C nutzt B's Output | Nein — Data-Shape entsteht erst nach A's Output | Designer → Writer → Engineer (Template→Copy→Build) |

#### Detaillierte Entscheidungsschlüssel

```
Frage 1: Haben die Agent-Outputs Abhängigkeiten?
  ├─ Nein → PARALLEL. Dispatche alle gleichzeitig.
  │           Beispiel: Researcher + Researcher (2 verschiedene Topics) + Analyst (Daten-Sampling)
  │
  ├─ Ja, eine Richtung (A→B) → SEQUENTIAL 2-WAVES.
  │   Welle 1: Agent A. Welle 2: Agent B (mit A's Output als Kontext).
  │   Beispiel: Researcher → Designer (Design braucht Referenzen)
  │
  └─ Ja, verkettet (A→B→C) → SEQUENTIAL CHAINED.
      Welle 1: A. Nach A: Welle 2: B. Nach B: Welle 3: C.
      Beispiel: Designer (Template → Writer (Copy-Keys bekannt) → Engineer (Build-Script)

Frage 2: Ist das Data-Shape/Output-Format aller Agents vorher bekannt?
  ├─ Ja → PARALLEL möglich (jeder kann unabhängig arbeiten)
  │           Beispiel: 3 Researcher, jeder liefert Markdown-Report
  │
  ├─ Nein, teilweise → SEQUENTIAL EMPFOHLEN
  │   Beispiel: Writer + Engineer — Copy-Schema erst nach Writer-Output bekannt
  │
  └─ Nein, entsteht erst → SEQUENTIAL PFLICHT
      Beispiel: Designer liefert Template → Engineer muss darauf aufbauen

Frage 3: Wiederholungsrate (wird dieser Workflow >1× ausgeführt?)
  ├─ Nein, einmalig → PARALLEL ok (Risiko ist akzeptabel)
  └─ Ja, wiederkehrend → SEQUENTIAL EMPFOHLEN (Integration-Bugs sind teuer)
```

#### Wann PARALLEL gar nicht geht

Die folgenden Abhängigkeiten erzwingen **zwingend Sequential Dispatch**. Parallel-Dispatch führt hier garantiert zu Integration-Brüchen:

| Abhängigkeitstyp | Beispiel | Konsequenz bei Parallel-Dispatch |
|---|---|---|
| **Template + Daten** | Designer liefert HTML-Template, Writer liefert copy.json | Template-Tokens passen nicht zu Daten-Keys |
| **API-Contract** | Backend baut API, Frontend baut Client | Felder heißen anders → Mapping-Code nötig |
| **Build + Abhängigkeit** | Engineer baut CLI, Researcher erstellt README | README zitiert falsche Flags |
| **Schema-Definition** | Data-Schema entsteht in Agent A → B nutzt es | B arbeitet mit angenommenem Schema |

#### Empfohlene Standard-Strategie

Für die meisten Multi-Agent-Tasks (insbesondere wenn 3+ Agents beteiligt sind):

```
1. Welle 1 — Research/Design (unabhängig, parallel)
   → Researcher: Fakten sammeln
   → Designer: Style-Tokens + Layout-Beschreibung
   
2. Welle 2 — Content Production (abhängig von Welle 1)
   → Writer: Copy (basierend auf Research + Style-Tokens)
   
3. Welle 3 — Build (abhängig von Welle 1+2)
   → Engineer: Build-Pipeline (Template-Engine + Makefile + CI/CD)
   
4. Welle 4 — Verify (abhängig von allen)
   → Verifier: Gate (Prüft Integration von Welle 1-3)
```

**Warum?** Jede Welle produziert einen Output, der von der nächsten Welle konsumiert wird. Keine Welle kann fertig werden bevor die vorherige Output geliefert hat.

#### Wann die Standard-Strategie überschreiben

| Situation | Alternative | Begründung |
|---|---|---|
| Nur 2 Agents, unabhängige Topics | 🔄 **Parallel** | Keine Abhängigkeit = kein Sequential-Grund |
| Build braucht nur Git und CI-Workflow | 🔄 **Parallel** (nur Verifier als Gate) | Design + Copy können parallel laufen, Engineer braucht nur Git-Integration |
| Research + Design direkt + separater Writer | 🟡 **2 Waves** | Designer braucht Research, Writer braucht beides (zur Not mit Context ohne) |
| Zeitkritisch, Integration-Risiko akzeptabel | 🟡 **Parallel + fix-loop** | Schnellerer Start, aber Fix-Loop nötig |

#### Effizienz-Vergleich (aus dem Landing-Page-E2E)

| Dispatch-Methode | Wall-Time | Integration-Issues | Gesamt-Aufwand |
|---|---|---|---|
| **Parallel** (v1) | ~12 Min | 1 BLOCKER + 4 MAJOR + 5 MINOR | ~30 Min (inkl. Fix-Loop) |
| **Sequential Chained** (v2) | ~25 Min | 0 BLOCKER + 0 MAJOR + 2 MINOR | ~27 Min (inkl. Minor-Fixes) |
| **Ersparnis** | -13 Min | -100% kritische Issues | -10% Gesamt-Aufwand |

**Fazit:** Sequential dispatch kostet ~2× Wall-Time, spart aber den Fix-Loop → Gesamt-Zeit ist ähnlich oder besser UND die Qualität ist höher (keine Integration-Überraschungen).

### Single-Batch (alle parallel, unabhängig)

```python
delegate_task(tasks=[
    {"goal": "Research MiniMax.io", "context": "..."},     # Researcher
    {"goal": "Design Landing-Page", "context": "..."},     # Designer
    {"goal": "Write Marketing-Copy", "context": "..."},    # Writer
    {"goal": "Build Deploy Pipeline", "context": "..."},   # Engineer
])
# → Alle laufen parallel. Outputs re-entern als Messages automatisch.
```

**Wann:** Tasks sind unabhängig (kein Output voneinander abhängig) UND Output-Format ist vorher bekannt.

### Two-Wave (parallel, dann sequenziell)

```python
# Welle 1: Research + Content-Gathering (parallel, unabhängig)
# Nach Welle 1 fertig → Welle 2: Build (abhängig von Welle-1-Outputs)
```

**Wann:** Welle-2-Tasks brauchen konkreten Welle-1-Output als Input (z.B. Researcher-Ergebnisse für Designer, oder Engineer braucht Designer-Output als Build-Input).

### Chained Sequential

```python
# Welle 1: Designer fertig → Template bekannt
# Welle 2: Writer nutzt Template-Keys (bekannt nach Welle 1)
# Welle 3: Engineer baut Build-Script für Template + Copy
```

**Wann:** Verkettete Abhängigkeiten (A→B→C). Output von Agent A definiert Schema/Shape für Agent B.

### Report-Integration

Die Subagent-Outputs landen als neue Messages in der Conversation (nicht via `process`). Trackbar via:
- `todo`-Liste mit ids
- `mnemosyne_remember` mit delegation_id

## Siehe auch

- Haupt-SKILL.md: Multi-Persona Fix-Loop Pattern, Anti-Patterns
- `references/prompt-templates.md`: Subagent-Briefing-Patterns
- `references/fix-loop-pattern.md`: Engineer→Verifier→Fix→Re-Audit→PASS
- `references/landing-page-workflow.md`: Writer→Engineer Data-Shape-Handoff, Template-Engine-Pass-Ordnung, CI/CD
- `~/Downloads/team-roster.md`: Original-Source für Rollen-Definitionen

### Version

- **v1.3 (2026-07-08):** Added Token-Naming Convention Protocol ({{copy.X.Y}} vs {{X.Y}} decision, Backcompat-Strategie, Kritikalitätstabelle). Replaced simplified Dispatch-Strategie with full Parallel-vs-Sequential Decision Matrix (3 Entscheidungsfragen, Abhängigkeitstabelle, Standard-Strategie, Ausnahme-Regeln, Effizienz-Vergleich). Added 3 new Pre-Flight-Checklist items.
- **v1.2 (2026-07-08):** Added Deployment-Readiness Snapshot section with HTML-Comparative Smell Tests (4-Check-Pattern für Designer-vs-Pipeline-Output), BLOCKER-Tabelle für Landing-Page-Deploys, Cache-Key/Path-Filter-Check in E2E-Quality-Bar, Data-Path-Wahl in Pre-Flight-Checklist. Learning aus dem FINAL Gate: `wc -c`-Vergleich ist der schnellste BLOCKER-Detector.
- **v1.1 (2026-07-08):** Added Data-Contract Schema Definition (Decompose-Phase), Data-Path Decision (Designer-HTML vs Template-Engine), and Pre-Verifier Integration Build Test sections.