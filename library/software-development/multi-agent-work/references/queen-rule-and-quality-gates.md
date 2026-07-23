# Claude-Flow Transfer, Queen-Rule & Implementierungs-Regeln

## Claude-Flow-Transfer für Hermes

Wenn der User ein Video oder eine Analyse zu Orchestrierung bringt, extrahiere nicht nur eine Zusammenfassung, sondern übersetze die Lernpunkte in:

1. **Rollenmodell** — enge Spezialisierung statt generischer Allround-Agenten
2. **Guardrails** — Workers dürfen nicht committen, pushen oder Secrets ausgeben
3. **Persistente Reports** — jeder Worker schreibt ein Artefakt, nicht nur Fließtext
4. **Parent-Synthese** — Parent sammelt, prüft und entscheidet
5. **Iterative Qualität** — Tests, Review, Refactoring und Doku vor Freigabe

Für `greyscripts` gilt als Default:

```
Issue → Rollen-Paket → Parent-Synthese → Implementierung → Quality-Gate → PR/Doku → kontrollierte Freigabe
```

Nutze diesen Transfer, wenn der User sagt, dass ein Video als "Prompt-Richtwert" oder "Orchestrierungs-Lernquelle" dienen soll.

---

## Queen-Rule: Niemals inline arbeiten! (KRITISCH — User-Korrektur 2026-06-23)

**Die Queen (Parent) tut NIE inline-Arbeit, die ein Subagent erledigen kann.**

### Warum?

- Queen läuft auf teurem Modell (deepseek-v4-pro), Worker auf gratis (Owl Alpha = 0€)
- Jede `delegate_task()` kostet die Queen ~200 Tokens. Inline-Code kostet 1000+ Tokens
- Parallel-Delegation skaliert horizontal (3+ Worker gleichzeitig), die Queen ist Single-Threaded

### Erkennungsregel

Wenn du als Queen merkst, dass du:

- Code schreibst, liest, analysierst
- Lange Diffs durchgehst
- Tiefe Research-Ergebnisse zusammenfasst
- Builds/Installs machst

**→ STOPP. Das ist Arbeit für Subagenten.** Delegiere sofort an 2-3 parallele Owl-Alpha-Worker.

### Was die Queen machen SOLL

| Erlaubt                                                                | Verboten                                                          |
|------------------------------------------------------------------------|-------------------------------------------------------------------|
| Subagenten spawnen + konfigurieren                                     | Code schreiben/patchen (inline)                                   |
| Subagent-Claims verifizieren (kurz)                                    | Code lesen + analysieren (20+ Zeilen)                             |
| Synthese aus Subagent-Reports                                          | Lange Terminal-Outputs manuell parsen                             |
| Gate-Entscheidungen (ACCEPTED/DENIED)                                  | Mehrere Dateien nacheinander lesen                                |
| Committen + Pushen (nach Freigabe)                                     | Builds/Installs inline laufen lassen                              |
| Skill-Upload + Memory speichern                                        | Komplette Pipeline inline durchziehen                             |
| **Git-Operationen (mv, rm, .gitignore, add)**                          | —                                                                 |
| **Repo-Restrukturierung (Datei-Moves, Ordner-Merges)**                 | —                                                                 |
| AUSNAHME: Phase 2 (mkdir, venv), Git-Operationen, File-Restrukturierung — alles unter 3 Zeilen/Stück | Nur diese Ausnahmen — alles andere delegieren |

### Token-Budget (Hard-Regel)

```
Queen:   ~200 Tokens pro delegate_task() + ~50 Tokens claim-check
Worker:  ~500-5000 Tokens pro Task, aber auf 0€ Modell (Owl Alpha)
→ Empfehlung: Max 5 Inline-Zeilen pro Queen-Turn. Alles größer → delegate_task()
```

### Beispiel-Entscheidungsbaum

```
Aufgabe kommt rein
├── Dauert < 2 Zeilen / < 5 Sekunden? → Queen macht inline
├── Dauert > 2 Zeilen? → delegate_task() an Owl Alpha Worker
│   ├── Kann parallelisiert werden? → Batch delegate_task (up to 3 parallel)
│   └── Lineare Abhängigkeit? → Sequential-Pipeline (Research → Implement → Review)
└── Braucht Queen-Entscheidung (Gate)? → Synthese + ACCEPTED/DENIED
```

---

## Implementierungs-Regeln (aus ki-murks-verhindern)

### Quality Gates (MÜSSEN geprüft werden)

- [ ] **Code läuft** — Nicht nur "sollte funktionieren"
- [ ] **Tests vorhanden** — Mindestens Smoke-Test
- [ ] **Keine Secrets** — Keine API-Keys im Code
- [ ] **Dokumentiert** — README oder Inline-Kommentare
- [ ] **Verifiziert** — Queen prüft Subagent-Claims konkret:
  - Behauptete Testergebnisse: `npm test`, `greybel build`, `pytest` **selbst re-runen**
  - Behauptete Dateien: `ls -la <pfad>` auf Existenz + Größe prüfen
  - Behauptete Commits: `git log --oneline -3` im Ziel-Repo
  - Behauptete PR-URLs: `gh pr view <n> --json body -q '.body'` — 404 bei privaten Repos fangen
- [ ] **Git-Guardrails aktiv** — Worker dürfen nicht committen, pushen oder Secrets ausgeben; Parent entscheidet über Commit/Push/PR

### Subagent-Review-Tool (Live-Lesson 2026-07-04)

Nach Subagent-Rückkehr diese 4 Checks in **einem gebatchten terminal()-Call**:

```bash
# Batch-Check für einen Subagent-Report
echo "=== Files ===" && ls -la pfad/behauptete/datei 2>&1
echo "=== Tests ===" && cd /pfad/zum/repo && npm test 2>&1 | tail -10
echo "=== Commits ===" && git log --oneline -5
echo "=== PR ===" && gh pr view <nr> --json body 2>&1 | head -5
```

**1 Call, 4 Checks, ~15 Sekunden. Verhindert Phantom-Fixes.**

### Anti-Patterns (verboten)

1. **Phantom-Implementierung** — "Hab ich gebaut" ohne Nachweis
2. **Halbfertiger Code** — Kompiliert nicht oder crashed
3. **Keine Tests** — "Wird schon funktionieren"
4. **Undokumentiert** — Nur der Builder versteht es