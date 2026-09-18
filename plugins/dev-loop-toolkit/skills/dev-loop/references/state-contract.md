# state-contract.md — State, Lock und Resume

## `.dev-loop/state.json` (im Ziel-Repo, untracked)

`.dev-loop/` muss in `.gitignore` stehen (harness-bootstrap setzt das). Verwaltet von
`scripts/loop-state.sh`; direkt lesen ist ok, direkt schreiben nicht.

```json
{
  "version": 1,
  "repo": "OWNER/REPO",
  "milestone": "M-A — Automations-Harness",
  "session": {
    "id": "2026-09-17T20:41-zcode",
    "started": "2026-09-17T20:41:00+02:00",
    "baseline_sha": "710f4ae…",
    "baseline_verify": "verify.py --baseline: Exit 0 (300 Cases / 45.020 Assertions)"
  },
  "current": {
    "issue": 123,
    "task_id": "T-A.9",
    "phase": "IMPL",
    "impl_iterations": 2,
    "verify_result": null,
    "pr": null,
    "brief_file": ".dev-loop/brief-T-A.9.md",
    "evidence_last": "verify.py --host-only: Exit 0 (Iteration 2, Hypothese: Buffer-Grenze)"
  },
  "frontier_seen": [123, 124, 125, 128],
  "gates_open": ["gate:G-A (#128)"],
  "updated": "2026-09-17T22:03:00+02:00"
}
```

Felder mit Bedeutung:

- `phase` ∈ `BASELINE | FRONTIER | BRIEF | IMPL | VERIFY | LAND | LOG | HALT`
- `impl_iterations` — der 5er-Zähler aus loop-phases.md; über Sessions kumulieren
- `evidence_last` — einzeiliger letzter Beweis (für Resume-Report und agent-log)
- `frontier_seen` — Issues, die diese Session bereits gesehen/übersprungen hat
- `gates_open` — spiegel prominent den HALT-Grund für die nächste Session

## Lock (`.dev-loop/lock`)

- Angelegt von `loop-state.sh <repo> lock <session-id>`; enthält session-id + Zeit
  (bewusst **keine PID** — das Script ist kurzlebig, Agenten-Sessions sind stundenlang;
  Begründung: docs/DESIGN.md).
- **Single-Writer**: fremder Lock jünger als 6 h → kein zweiter Loop (Exit 1).
  Älter als 6 h → Stale, wird überschrieben (mit Log-Zeile). Erneutes `lock` mit der
  **eigenen** session-id ist Heartbeat und verlängert den Lock.
- Freigabe am Sessionende: `loop-state.sh <repo> unlock <session-id>` — fremder
  frischer Lock nur mit `--force`. Plus agent-log als Fallback, falls die Session
  hart stirbt.

## Resume-Protokoll (nach Sessionverlust/Kompaktion)

1. `loop-state.sh <repo> get` — Phase, Issue, Iterationszähler lesen.
2. Letzten `agent-log`-Kommentar lesen (`gh issue view <agent-log-NR> --comments`,
   letzter Block) — Done/NEXT abgleichen.
3. Divergenz State vs. agent-log → **agent-log gewinnt** (er ist merged/öffentlich),
   State korrigieren, Divergenz im neuen agent-log-Block erwähnen.
4. Phase fortsetzen: `IMPL` mit übernommenem Zähler, `LAND` mit PR-NR aus State,
   `HALT` → Grund prüfen (Gate inzwischen approved? Entscheidung inzwischen beantwortet?).
5. Resume-Block als erster agent-log-Eintrag der neuen Session ("Resume von <session-id>
   bei <phase>, Zähler <n>/5").

## Warum Datei und nicht nur GitHub

Der agent-log ist öffentlich und merge-sicher, aber zäh (API-Roundtrips) und für
Mid-Phase-Zustände zu grob. Die State-Datei ist der billige, präzise Tacho; der
agent-log ist der amtliche Bericht. Beide zu führen kostet Sekunden und rettet
Session-Grenzen — der pokerogue-Loop lief 19 PRs über genau diese Kombination.
