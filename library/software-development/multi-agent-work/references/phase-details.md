# Phasen-Details

Detaillierte Anleitungen für die einzelnen Phasen des 6-Phasen-Workflows. SKILL.md gibt die Übersicht; hier stehen die Befehle, Tabellen und Code-Beispiele.

---

## Phasen-Timeouts (V1.3 — differenziert & durchgesetzt)

Jede `delegate_task()`-Instanz MUSS den Timeout explizit setzen. Die Default-600s sind für alle Phasen außer Execution zu lang / zu kurz.

| Phase            | Timeout  | Token-Budget | delegate_task Param  | Begründung                            |
|------------------|----------|--------------|----------------------|---------------------------------------|
| Research (1–2)   | 300 s    | 8.000        | `timeout=300`        | RAG-Lookups sind kurz oder hängen     |
| Planning (3)     | 300 s    | 4.000        | `timeout=300`        | Decomposition ist billig              |
| Execution (4)    | 900 s    | 16.000       | `timeout=900`        | Code-Gen darf lange laufen            |
| Evaluation (5)   | 600–900 s| 6.000        | `timeout=900` (Script)| Lokaler R1 braucht Zeit für Reasoning |
| Finalizing (6)   | 300 s    | 4.000        | `timeout=300`        | Nur Zusammenfassen                    |

**Praktisches Beispiel:**

```python
delegate_task(
    role="leaf",
    goal="Recherchiere RSS-Libraries",
    context="...",
    toolsets=["terminal", "file", "web"],
    # timeout=300 statt default 600
)
# Achtung: delegate_task hat aktuell keinen timeout-Parameter.
# Falls nicht unterstützt, timeout im Context vermerken:
context="""
...
TIMEOUT: 300s — wenn Recherche länger dauert, mit head/wc-l einschränken
"""
```

**Ollama-Timeout beachten:** Der lokale Critic (Script) hat `timeout=300s` hart verdrahtet. Wenn Ollama auf GPU ausgelastet ist, kann ein einzelner Critic-Call bis zu 300s dauern. Das ist normal — der Reasoning-Trace von R1:8b braucht Zeit.

---

## Experten-Scopes

### Standard-Assignment (anpassbar an Aufgabe)

| Expert             | Scope                              | Toolsets              |
|--------------------|------------------------------------|-----------------------|
| 1 — Architekt      | Design, API-Struktur, Datenmodell  | terminal, file, web   |
| 2 — Implementierer | Code, Tests, Dependencies          | terminal, file, web   |
| 3 — Validator      | Edge Cases, Security, Performance  | terminal, file, web   |

### Claude-Flow-inspiriertes Rollenmodell

Für komplexe Aufgaben mit viel Kontext oder vielen Dateien nicht nur 3 generische Worker nehmen, sondern enge Rollen mit kleinen Deliverables:

| Rolle                    | Aufgabe                                          | Artefakt            |
|--------------------------|--------------------------------------------------|---------------------|
| Issue-Analyst            | Ziel, Reproduktion, betroffene Dateien klären    | `analysis.md`       |
| Architekt                | Datei-, Branch-, Test- und Integrationsplan      | `plan.md`           |
| Implementierer           | Minimaler Patch                                  | Code-Diff           |
| GreyScript-/CI-Validator | Build/Syntax/Lint prüfen                         | Build-Report        |
| Security-Reviewer        | Secrets, Permissions, Git-Risiken                | Security-Report     |
| Dokumentations-Spezialist| Build-/Workflow-Doku                             | Markdown-Doku       |
| Release-Koordinator      | Milestone, Changelog, PR-Body                    | Release-Plan        |

**Regel:** Mehr Rollen nur, wenn der Kontext sonst verschmutzt wird. Für normale Tasks bleibt 3 Experten der Default.

### Für spezifische Aufgaben anpassen

**Web-App:**
- Expert 1: Backend (API, DB)
- Expert 2: Frontend (UI, UX)
- Expert 3: DevOps (Deploy, CI/CD)

**Data Pipeline:**
- Expert 1: Datenquellen & ETL
- Expert 2: Transformation & Storage
- Expert 3: Monitoring & Alerting

**Security Audit:**
- Expert 1: Auth & Credentials
- Expert 2: Network & Ports
- Expert 3: Code & Dependencies

---

## Kontext-Template für delegate_task (KRITISCH)

**Jede `delegate_task()`-Instanz MUSS einen expliziten `context`-Block enthalten.**

Subagents sehen **nur** `goal` und `context`. Ohne vollständigen Kontext liefern sie inkonsistente Ergebnisse.

### Required Context-Block

```python
delegate_task(
    goal="Implementiere RSS-Fetcher für Esports-News",
    context="""
SYSTEM:
  OS: Zorin OS 18.1 (Ubuntu 22.04 base)
  Hardware: ERAZER 17 P1, i7-13620H, RTX 5060 8GB VRAM, 15GB RAM
  User: bratan (home: /home/bratan)
  Python: 3.11.15
  Node: 22.22.3

AKTUELLER STATE:
  Hermes: 0.16.0, Gateway PID 43797
  Ollama: 0.30.6, deepseek-r1:8b + nomic-embed-text
  TokenTelemetry: Port 3000/8000, ~700MB RAM

NEU SEIT LETZTER SESSION:
  - Hermes update durchgeführt (7 Commits)
  - Neue Skills: ki-murks-verhindern, rag-pipeline-python, multi-agent-work

AUFGABE:
  1. Recherchiere beste Python RSS-Library (feedparser vs. rss2json)
  2. Prüfe ob python-telegram-bot installiert ist
  3. Erstelle Projektstruktur unter ~/projects/esports-news/
  4. Schreibe fetcher.py mit Error-Handling
  5. Schreibe telegram.py mit async Bot
  6. Erstelle config.yaml für Feed-URLs

TRENNUNG:
  Sofort (< 30 Min):
    - Projektstruktur erstellen
    - Requirements.txt schreiben
    - Grundgerüst fetcher.py
  Großprojekt:
    - Mehrere Feeds parallel
    - Datenbank für Historie
    - Web-Interface

OUTPUT:
  ~/docs/system/rss-fetcher-research-2026-06-06.md
  ~/projects/esports-news/

SOURCE-CODE-PFADE (falls relevant):
  - ~/.hermes/hermes-agent/tools/delegate_tool.py (Z. 2487ff)
  - ~/.hermes/config.yaml (Delegation-Config)

TEST-KOMMANDO:
  cd ~/projects/esports-news && python3 -m pytest tests/ -v

FEHLER (falls vorhanden):
  [Keine aktuellen Fehler]
""",
    toolsets=["terminal", "file", "web"]
)
```

### Was passiert ohne expliziten Kontext

**Schlecht (Subagent rät):**

```python
delegate_task(
    goal="Baue RSS-Fetcher",
    context="Für Esports-News"  # Zu wenig!
)
# → Subagent: "Ich nehme an du meinst..."
# → Ergebnis: Inkonsistent, nicht reproduzierbar
```

**Gut (Subagent weiß alles):**

```python
delegate_task(
    goal="Baue RSS-Fetcher",
    context="""SYSTEM: Zorin OS 18.1, Python 3.11.15...
AKTUELLER STATE: Hermes 0.16.0, Ollama läuft...
AUFGABE: 1. Recherchiere... 2. Prüfe... 3. Erstelle...
OUTPUT: ~/projects/esports-news/
TEST-KOMMANDO: pytest tests/ -v
"""
)
# → Subagent: "Verstanden, ich arbeite mit den gegebenen Pfaden..."
# → Ergebnis: Konsistent, reproduzierbar, verifizierbar
```

---

## Beispiel-Durchlauf

### Aufgabe: "RSS-News-Fetcher für Esports"

**Phase 1 — Research:**

```
Expert 1 (Architekt):
  → Feedparser für RSS, Schedule für Cron, python-telegram-bot
  → Architektur: fetcher.py → parser.py → telegram.py

Expert 2 (Implementierer):
  → Code-Beispiel für feedparser
  → Telegram-Bot Setup mit async
  → Error-Handling für down Feeds

Expert 3 (Validator):
  → Edge Case: Feed ändert URL
  → Edge Case: Telegram Rate-Limit
  → Edge Case: Speicher wächst unendlich
```

**Phase 2 — Fixes (Parent):**

```bash
mkdir -p ~/projects/esports-news
python3 -m venv ~/projects/esports-news/venv
```

**Phase 3 — Synthese:**

```
P0: Grundstruktur (fetcher + telegram)
P1: Mehrere Feeds parallel
P2: Datenbank für Historie
P3: Web-Interface
```

**Phase 4 — Implementierung:**

```
Grounding: Lies existierende Telegram-Bot Config
Execution: Schreibe fetcher.py, telegram.py, config.yaml
Evaluation:
  → Output-Validator: Syntax-Check OK
  → Critic-Gate: Error-Handling fehlt → RETRY
  → Worker erneut → Critic-Gate: PASS
Finalizing: Zeige User, frage nach OK, git commit
```

**Phase 5 — Dokumentation:**

```
~/docs/builds/2026-06-06-esports-news-fetcher.md
~/projects/esports-news/README.md
```

**Phase 6 — Retrospective:**

```
✓ 3 Experten waren ausreichend
✓ Phase 2 (Fixes während Research) hat Zeit gespart
✗ Expert 3 hätte früher Security-Check machen sollen
→ Nächstes Mal: Security-Expert als Phase-2-Fix
```

---

## Output-Struktur

```
~/projects/<projekt-name>/
├── src/                    # Quellcode
├── tests/                  # Tests
├── README.md               # Projekt-Doku
└── requirements.txt        # Dependencies

~/docs/builds/
└── YYYY-MM-DD-<projekt>.md # Build-Doku
```