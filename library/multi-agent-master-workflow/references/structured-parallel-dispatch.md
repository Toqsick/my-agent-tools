# Structured Parallel Dispatch (Greytrix-Pattern)

> Gelernt aus Greytrix-NetRunner-Wave-1 (2026-07-09): 3 unabhängige Bienen parallel dispatched, jede mit eigenem Goal/Kontext/Constraints/Verifikation.

## Wann nutzen?

- **Mehrere unabhängige Workstreams**, die nichts miteinander zu tun haben (kein File-Overlap, keine Abhängigkeiten)
- Jeder Stream hat eigenen Output-Ordner, eigene Toolsets, eigene Risiken
- Queen arbeitet währenddessen an eigener Tech-Infrastruktur (Doku, Credentials, Plan-Updates)

**Nicht nutzen wenn:** Tasks denselben File-Scope haben, sequentielle Abhängigkeiten bestehen, oder ein Task den Output eines anderen braucht.

## Spec-Template (Goal + Context)

Jede Biene bekommt ein **Goal** + **Context**-Paar mit dieser Struktur:

### Goal (kurz, prägnant)
```
Phase X — [Domain] aufsetzen/analysieren/bauen
```

### Context (alles was die Biene braucht)

```
**Working Directory:** /home/bratan
**Language:** Deutsch (Antwort), technische Begriffe Englisch
**Mission:** [Worüber der ganze Dispatch geht]

**Live-Environment (verifiziert [DATE]):**
- Relevante Pfade, Ports, Credentials (soweit nicht geheim)
- Bereits laufende Services / bestehende Codebasis
- Constraints aus dem System (max File-Size, Pfad-Sichtbarkeit, etc.)

**Deine konkreten Tasks (bite-sized, je 2-5 Min):**

[Nummerierte Tasks, jede klar als eigene Aktion]

**Verifikation (am Ende aller Tasks):**
- [ ] Check 1
- [ ] Check 2
- [ ] Check 3

**WICHTIG — nicht kaputtmachen:**
- Greift NICHT in [geschützte Pfade]
- Greift NICHT in [konfigdateien/envs]
- KEINE [verbotenen Operationen]
- [Was stattdessen tun]

**Wenn etwas fehlschlägt:**
Sag ehrlich was nicht ging + welcher Workaround, statt zu erfinden.
```

### GOAL vs CONTEXT Trennung

| Feld | Enthalten | Nicht enthalten |
|---|---|---|
| **Goal** | Output-Erwartung, Deliverable-Pfad | Live-Env-Daten, Constraints |
| **Context** | Environment-Kontext, Tasks, Checkliste, Anti-Patterns | Die Erwartung ans Ergebnis |

## 3-Bienen Dispatch Pattern

### Wave 1 (parallel, unabhängig)

```markdown
🐝 Biene Alpha: Phase A — Co-Pilot reaktivieren + Skripte bauen + Coach-Test
🐝 Biene Beta: Phase B — Orchestrator-Pipeline + Bee-Templates + State-Tracker  
🐝 Biene Gamma: Phase C.0 — READ-ONLY Infrastructure Recon
```

**Queen während Wave 1:**
- Worked on docs, memory, plan-patching
- Dispatcht keine weiteren Tasks (max 6 concurrent, lass Luft)
- Notiert Ergebnisse wenn sie reinrollen

### Wave 2 (sequentiell nach Wave 1)

Nur dispatchen wenn:
- Alle Wave-1-Bienen gelandet
- Queen hat Results konsolidiert
- Basti hat grünes Licht gegeben

## Spacing Rule (Anti-Thundering-Herd)

```yaml
# Nicht alle 6 in einem delegate_task batch
# Stattdessen:
Wave 1: 3 Bienen parallel  ← dispatch
  [5-10s Pause — dispatcher settles]
Wave 2: 3 Bienen parallel  ← dispatch (nach Signal)
```

Warum:
- spawn_failed Patterns früher erkennen
- Tool-/Port-Resource-Contention reduzieren
- Fehlerdiagnose im laufenden Batch einfacher

Vgl. `yuno-team-orchestrator` → Anti-Patterns → "Bienen-Dispatch works best as 2-wellen fan-out (3+3)"

## READ-ONLY Recon Pattern (Gamma-Biene)

Ein Spezialfall der strukturierten Dispatchs: **Infrastruktur-Totalschonung**.

### Spec-Zusätze für READ-ONLY Bees

**Goal-Zusatz:**
```
READ-ONLY MISSION: Du sollst NUR Informationen sammeln, NICHTS an der Ziel-Infrastruktur ändern!
```

**Constraint-Block:**
```markdown
**WICHTIG — STRIKT READ-ONLY:**
- NUR [read-command-1], [read-command-2]-Befehle
- KEIN [write-command]
- KEINE [create/delete/update]
- NUR [read-only-access-cmd] --command='harmless_command' für read-only-Inspektion erlaubt
- Bei Unsicherheit: lieber NICHT ausführen und dokumentieren
```

**Output-Template:**
```
- Sicherheits-Status klar (PASS/FAIL/DEGRADED)
- Handlungsempfehlungen (KEINE auto-Anwendung!)
- Was sind die nächsten Schritte? (als Vorschlag, nicht als Plan)
```

## Beispiel-Task-Struktur

```
**C.0.1: VM-Specs komplett erfassen**
```bash
# Vollständige VM-Info
gcloud compute instances describe ... --format='yaml'
```

Sammle alles in einem Report.

**C.0.2: Connectivity-Test (NUR prüfen, nicht einloggen)**
```bash
timeout 5 bash -c 'cat < /dev/tcp/HOST/PORT' && echo "OPEN" || echo "CLOSED"
```

NICHT wirklich einloggen! Nur testen ob Verbindung prinzipiell möglich.
```

## Changelog

- `2026-07-09` — Initial: Greytrix-NetRunner-Wave-1 Pattern dokumentiert