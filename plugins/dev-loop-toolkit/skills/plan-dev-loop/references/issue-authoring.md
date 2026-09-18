# issue-authoring.md — Issues, die ein Agent abarbeiten kann

## Body-Vorlage (Standard-Task)

```markdown
**T-9.3 — Parity-Report-Werkzeug**

## Ziel
Ein Satz, was fertiggesehen ist.

## Akzeptanz (ausführbar, je Kriterium ein Befehl)
1. `python3 tools/parity_report.py` → `out/parity_report.md` existiert, Exit 0
2. `python3 tools/verify.py --host-only` → Exit 0
3. Bericht listet fehlende/überzählige Einträge für species/moves/abilities/items

## Kontext
1–3 Sätze Szene-Setting: welche Interfaces/Entscheidungen vorheriger Tasks betreffen das.

## Grenzen
Was ausdrücklich NICHT enthalten ist (→ stattdessen idea:-Issue #NN).

Depends-on: #86
```

Regeln:

- **Akzeptanz = Befehl + erwarteter Output.** „Läuft" ist keine Akzeptanz. Der
  PR-Body des dev-loop zitiert später genau diese Zeilen mit den Beweisen.
- **Dep-Edges wörtlich** (`Depends-on: #N`) — frontier.sh parsiert dieses Muster
  (auch „Setzt #N voraus" versteht es). Kanten gehören in den Body, nicht nur in
  den Plan-Doc.
- **Grenzen explizit** — Scope-Creep beginnt im Issue-Body, nicht im Code.
- Task-ID im Titel (`T-<M>.<n> — Titel`) → Branchname `wip/T-<M>.<n>`, PR-Titel,
  Commit-Tag `[T-<M>.<n>]` speisen sich daraus.

## Label-Satz (Konvention des Loops)

| Label | Zweck | Wer legt an |
|---|---|---|
| `agent` | normaler, autonom abarbeitbarer Task | plan-dev-loop |
| `gate` | Gate-Review, Approval-Kommentar des Menschen | plan-dev-loop (Titel `gate:G-n — …`) |
| `idea` | geparkte Scope-Ideen (QoL/Nice-to-have) | plan-dev-loop, dev-loop (bei Creep-Versuch) |
| `blocked` | eskalierte Tasks nach 5 Iterationen | dev-loop |
| `agent-log` (Titelpräfix) | laufendes Status-Issue, ein Kommentar je Session | harness-bootstrap |

GitHub-Labels dürfen keine `:` enthalten — die Konvention führt das Präfix im **Titel**
(`gate:G7`, `idea:Touch-Scroll-Listen`); das Label ohne Doppelpunkt ist die Ergänzung
für Filter. frontier.sh prüft beides.

## Abnahme-Issues

Issues, deren Akzeptanz menschliches Urteil verlangt (Hardware, Optik, Freigabe):
Body-Marker `Abnahme: Mensch` — dev-loop implementiert, mergt, schließt aber **nicht**
und führt sie im agent-log als „Abnahme ausstehend".

## Emission (nach Plan-Freigabe)

```bash
gh api repos/OWNER/REPO/milestones -f title="M9 — Titel" -f state=open
gh issue create -R OWNER/REPO --title "T-9.3 — Parity-Report-Werkzeug" \
  --body-file t-9.3.md --milestone "M9 — Titel" --label agent
```

Reihenfolge: Milestones zuerst, dann Issues aufsteigend (Dep-Edges verweisen dann
schon auf existierende Nummern), dann Gate-Issues je Milestone, dann TASKS.md-Spiegel,
dann REIHENFOLGE-Handoff in den agent-log.
