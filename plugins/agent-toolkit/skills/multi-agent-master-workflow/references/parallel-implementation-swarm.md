# Queen + Parallel Implementation Swarm (Bienen-Muster)

> 2026-07-09 — Hermes Improvement Vollplan, Welle 2
> Ergänzt `multi-agent-master-workflow` um das Dispatch-Pattern für
> **parallele Implementation durch autonome Sub-Agenten**, bei dem die
> Queen während des Flugs unabhängig weiterarbeitet.

## Abgrenzung zu bestehenden Patterns

| Pattern | Wann | Queen-Aktivität während Flug |
|---|---|---|
| **Cross-Repo GitHub Cleanup** (existing) | Analyse + Schließen von Issues/PRs | Wartet auf Welle-1-Ergebnisse |
| **Subagent-Driven Development** (existing) | Sequentiell mit 2-Stage-Review | Wartet auf jedes Subagent-Paar |
| **Parallel Implementation Swarm** (dieses Pattern) | Parallele Implementierung unabhängiger Skripte/Komponenten | **Queen arbeitet unabhängig weiter** (Docker, Docs, Cron) |

## Dispatch-Phasen

### Phase 0: Readiness-Check (vor Dispatch, Queen macht das)

Bevor Bienen losfliegen, prüft die Queen **lesend** (keine Side-Effects):

```python
# Typische Checks:
# 1. API-Shapes der Drafts gegen Live-System
grep -n "function\|def " draft.py  # Importe prüfbar?
python3 -c "from draft import main" --dry  # Import-Check

# 2. DB-Schema / existierende Daten
sqlite3 <db> ".schema <table>"

# 3. Disk / Ports
df -h /   # genug Platz?
ss -tlnp | grep :8080  # Port frei?

# 4. Abhängigkeiten
pip show <package> | grep Version

# 5. Harte Bugs in Drafts selbst fixen (1 min), nicht delegieren
```

**Ergebnis:** Ein Set von geprüften Briefings, jedes mit:
- Konkreten File-Pfaden zur Live-API
- Exakten Funktions-Signaturen
- Bekannten Pitfalls (nicht delegieren)
- E2E-Test-Verpflichtung im Briefing-Text

### Phase 1: Paralleler Dispatch

Queen dispatcht **N** unabhängige Bienen (typisch 3-6). Jede bekommt:

```python
delegate_task(
    goal="Implementiere <X> — muss E2E laufen (Exit 0) am Ende.",
    context="""
    BRIEFING: <kompakt, 60-70% der Draft-Länge>
    
    LIVE-API-SHAPE (vor Ort verifiziert, nicht geraten):
    - <file>: <funktion/klasse> mit <signature>
    - <db>: <schema>
    
    E2E-TEST-PFLICHT:
    - Schreibe und führe einen Komplettlauf aus
    - Ausgabe: <was muss sichtbar sein>
    - Bei Fehler: loggen + nicht aufgeben
    
    PITFALLS (von Queen vorab gefunden):
    - <fallstrick 1>
    - <fallstrick 2>
    """,
    toolsets=['terminal', 'file'],
)
```

**Briefing-Regel:** Kompakt halten (~60-70% der Draft-Länge). Kein "as you know"-Kontext. Die Biene teilt das gleiche Base-System-Prompt — sie braucht nur das spezifische Wissen.

### Phase 2: Queen arbeitet unabhängig

Während die Bienen fliegen (15-45 min) macht die Queen **strukturierte Nebenarbeit**:

```python
# Typische Queen-Arbeiten:
# 1. Docker-Setup (pull, start, test)
# 2. Cron-Installer schreiben
# 3. Anleitungen / Doku schreiben
# 4. Verzeichnisstruktur anlegen
# 5. Credentials ablegen
# 6. Mnemosyne-Memorys setzen
# 7. Todo-Liste pflegen
```

**Wichtig:** Queen darf nichts machen, was eine Biene braucht. Jede Biene ist ein abgeschlossener, unabhängiger Scope.

### Phase 3: Integration (nach Landung aller Bienen)

Sobald alle Subagent-Ergebnisse eingetroffen sind:

```python
# 1. Ergebnis-Summaries prüfen
# 2. Letzte Integration-Tests laufen lassen
# 3. Cron-Installer deployen
# 4. Memorys finalisieren
# 5. Zusammenfassung kommunizieren
```

## Briefing-Template (vollständig)

```
Goal: <1 Satz, mit E2E-Test-Commitment>

LIVE-API (von Queen verifiziert, nicht recherchiert):
- <file:linie> <signatur>
- <db-pfad> <schema>

IMPLEMENTIERUNG:
- Datei: <pfad>
- Format: <python/bash/yaml>
- Muss enthalten: <minimale Anforderungen>
- Muss liefern: <E2E-Prüfbarkeit>

PITFALLS:
- <fallstrick 1>
- <fallstrick 2>

VERIFIKATION:
```bash
<exakter CLI-Befehl zum Prüfen>
```

E2E-TEST:
1. Skript läuft durch ohne ImportError
2. Exit-Code ist 0
3. Erzeugt sichtbaren Output
4. <spezifische Prüfung>
```

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| Drafts ungeprüft delegieren | Queen prüft API-Shapes + Imports **vor** Dispatch |
| Biene bekommt Draft zum Lesen | Kompaktes Briefing schreiben, Draft-Inhalte abstrahieren |
| Queen wartet idle | Plan für Queen-Arbeit bereithalten (Nextcloud, Cron, Doku) |
| "alle Bienen gleich" | Jede Biene hat eigenen Scope, eigene Pitfalls |
| E2E-Test nicht verpflichtend | In Goal-Text "E2E Exit 0" als harte Anforderung |
| Bienen brauchen denselben Port/Ressource | Vor Dispatch prüfen: Können sie parallel laufen? |
| Zu viele Bienen (max. 6 für diesen User) | Auf Wellen aufteilen oder manche Queen selbst machen |
| Bienen-Summary blind glauben | Biene muss verifizierbaren Output liefern (Port-Response, Exit-Code, File-Content) |

## Siehe auch

- `subagent-driven-development/references/parallel-summary-staleness.md`
  (Staleness-Risiko bei parallelen Subagenten, mitigiert durch E2E-Test-
  Commitment in jedem Briefing)
- `multi-agent-pitfalls-cheatsheet` — den IMMER vor Dispatch laden
- `delegation-anti-patterns` — speziell: File-Affinity, Baseline-Build

## Herkunft

Dieses Pattern entstand im Vollplan MANIFEST.md (2026-07-09) für die
Hermes-Improvement-Welle 2: 4 Bienen implementierten parallel
`sync_engine.py`, `memory_audit_dashboard.py`, `obsidian_link_validator.py`,
und `nextcloud_skill_processor.py`, während die Queen Nextcloud-Docker
aufsetzte, den Cron-Installer schrieb und 2 HowTo-Anleitungen verfasste.