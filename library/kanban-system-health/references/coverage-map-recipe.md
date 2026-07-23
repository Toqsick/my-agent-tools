# Coverage-Map Recipe — "Nutzen wir Feature X?"

> **Wann nutzen:** User fragt "nutzen wir die komplette Kanban Matrix?", "do we actually use X?", "wie viel von Spec Y ist aktiv?". Braucht eine **faktenbasierte** Antwort statt Bauchgefühl.

> **Generalisiert:** Das Pattern funktioniert für jede Spec mit dokumentierten Features — Kanban, Hermes-CLI, ein Framework, ein API-Set. Das Kanban-Beispiel unten ist die Vorlage.

---

## Das Rezept (3-Schichten-Mix)

Eine ehrliche Coverage-Map braucht **drei Datenquellen** gleichzeitig:

### Schicht 1: Spec-Doc Feature-Inventur

Lies die Spec-Referenz (für Kanban: `~/.hermes/hermes-agent/website/docs/user-guide/features/kanban.md`, 940 Zeilen) und extrahiere alle dokumentierten Features mit Kategorie-Tags. Beispiel-Taxonomie:

| Kategorie | Beispiel Kanban |
|---|---|
| **CLI-Surface** | 37 Subcommands + 5 ergänzende (`boards`, `assignees`, `notify-*`) |
| **Core-Concepts** | Boards, Tasks, Links, Comments, Workspaces, Dispatcher, Tenants |
| **Advanced-Patterns** | Swarm, Decompose, Goal-Mode, Attachments, Notifications, Scheduled |
| **Worker-Lanes** | Profile-Lane, Orchestrator-Lane, External-CLI-Lane |
| **Dashboard-GUI** | Kanban-Tab, Drag-Drop, WebSocket-Live-Updates, Triage-Column |
| **Recovery** | Reclaim, Reassign, Stranded-Detection, Crash-Detection, Circuit-Breaker |

Pro Feature: **Name + Spec-Zitat** (1 Zeile). Kein Brainstorming — nur was in der Spec steht.

### Schicht 2: CLI-Help für aktuelle Subcommands

```bash
hermes kanban --help | grep -E '\b(init|boards|create|swarm|list|...)\b'
```

Plus pro Subcommand die `--help`-Ausgabe für die Feature-Flags (`--goal`, `--worktree`, `--tenant`, `--assignee`, etc.). Das ist die **wahre Implementierungs-Realität** — Spec und Code können auseinanderlaufen.

### Schicht 3: Live-State-Beweise aus SQLite

Pro Feature die SQLite-Stats. Beispiel:

```bash
# Workspace-Kinds: scratch, dir:, worktree, worktree:
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 "$db" "SELECT DISTINCT workspace_kind FROM tasks;"
done | sort -u
# → "scratch" only = worktree/dir-Features ungenutzt

# Tenant-Namespace:
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 "$db" "SELECT COUNT(*) FROM tasks WHERE tenant IS NOT NULL AND tenant != '';"
done

# Goal-Mode:
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 "$db" "SELECT COUNT(*) FROM tasks WHERE goal_mode = 1;"
done

# Assignee-Verteilung:
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 "$db" "SELECT DISTINCT assignee FROM tasks WHERE assignee IS NOT NULL;"
done | sort -u

# Failure-History (Circuit-Breaker-Beweis):
for db in ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 "$db" "SELECT COUNT(*) FROM tasks WHERE consecutive_failures > 0;"
done
```

**Wichtig:** Per-Board-DB-Loop nicht vergessen — jede Board hat eigene SQLite-Datei.

---

## Coverage-Bewertung (4 Stufen)

| Symbol | Kriterium |
|---|---|
| ✅ **Voll** | Feature konfiguriert UND durch Live-Daten bewiesen UND im Alltag benutzt |
| 🟡 **Teilweise** | Mechanik/Spec da, aber Coverage lückenhaft oder nur in Teilbereichen |
| ❌ **Ungenutzt** | Spec + Code vorhanden, 0 Live-Beweise in User-Daten |
| ⚠️ **Broken/Blockiert** | Spec sagt X, aber bei uns funktioniert X gerade nicht |

Pro Feature eines der 4 Symbole zuordnen + **Beweis notieren** (PID, Count, Config-Snippet, File-Path).

---

## Zusammenfassung als Tabelle

| Schicht | Voll | Teilweise | Ungenutzt | Broken | Aktiv-Quote |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ...% |
| ... | ... | ... | ... | ... | ...% |
| **GESAMT** | **N** | **M** | **K** | **J** | **~X%** |

Aktiv-Quote pro Schicht + Gesamt. Die Prozent-Zahlen kommen aus `(Voll + 0.5*Teilweise) / Total`.

---

## Reaktivierungs-Plan (Anhang)

Nach der Coverage-Map kommt der Plan. 4-Phasen-Standard:

| Phase | Ziel | Aufwand | Wert |
|---|---|---|---|
| 0 | Stale files aufräumen, Baseline-Backup | 30 min | niedrig |
| 1 | Highest-ROI-Lücken schließen (typischerweise: Assignees) | 1-2 Std | ⭐⭐⭐⭐⭐ |
| 2 | Worker-Maturity (skills, max_runtime, worktree per Task) | 2 Std | ⭐⭐⭐⭐ |
| 3 | Advanced-Patterns aktivieren (auto-decompose, goal-mode) | 2 Std | ⭐⭐⭐ |
| 4 | GUI/Polish | 1-2 Std | ⭐⭐⭐ |

Pro Phase: **Was, Wie, Verification-Step**. Plus explizite Liste was **bewusst NICHT** aktiviert wird und warum.

---

## Bewährte Antwort-Struktur (gelernt 2026-07-09)

1. **TL;DR** (1-2 Sätze): Coverage-Quote + größte Lücke
2. **Inventur:** Schicht 1 (Spec-Features) + Schicht 2 (CLI-Subcommands) + Schicht 3 (Live-Daten)
3. **Coverage-Matrix:** Pro Schicht mit ✅/🟡/❌/⚠️-Symbolen
4. **Diagnose:** Welche Lücken sind akzeptabel, welche schaden aktiv
5. **Plan:** 4-Phasen mit konkreten Schritten + Verification-Steps
6. **Erwartete End-Coverage:** Pro Phase die voraussichtliche Quote

User will **ehrliche Faktenlage**, nicht "alles super". Prozent-Zahlen aus Messwerten ableiten, nicht schätzen.

---

## Pitfalls bei der Erstellung

- **Spec nicht komplett lesen:** Feature in Spec übersehen = fälschlich als ungenutzt markiert. Immer Spec komplett durchscannen (z.B. `grep -E '^##|^###' spec.md` für Outline).
- **Globale DB statt Per-Board-Loop:** Falls Multi-Board-System, sind Daten in separaten DBs. Globale Queries sehen nur einen Bruchteil.
- **Prozent ohne Nenner:** "Wir nutzen 40%" ist wertlos ohne "von 52 Features". Immer Total ausweisen.
- **Konfidenz ohne Beweis:** Jede Quote-Zahl braucht Beweis (PID, Count, Config). "Sieht so aus als ob" → lieber weg lassen.
- **Plan ohne Verification-Step:** Jeder Aktivierungs-Schritt muss einen verifizierbaren Check haben (Live-Query, Smoke-Test). Sonst lässt sich nicht feststellen ob der Schritt funktioniert hat.

---

## Beispiel: Coverage-Map Output Format

```markdown
## 📊 Coverage-Matrix

| Feature | Status | Beweis |
|---|---|---|
| Boards (multi-project) | ✅ Voll | 6 Boards in SQLite |
| Workspace: scratch | ✅ Voll | 51/51 Tasks |
| Workspace: worktree | ❌ Ungenutzt | 0 worktrees konfiguriert |
| Auto-Decomp | 🟡 Teilweise | config=true, aber 0 Triage-Tasks je erzeugt |
| Goal-Mode | ❌ Ungenutzt | 0/51 mit goal_mode=1 |

## Gesamt-Coverage

| Schicht | Voll | Teilweise | Ungenutzt | Aktiv-Quote |
|---|---|---|---|---|
| CLI-Surface | 8 | 4 | 28 | 30% |
| Core-Concepts | 7 | 4 | 8 | 52% |
| ... |
| **GESAMT** | **18** | **9** | **25** | **~40%** |
```

---

## Siehe auch

- `kanban-system-health` SKILL.md Section 1 (Live-State-Check) — was vor Coverage-Map laufen muss
- `kanban-orchestrator` SKILL.md §Pitfalls — was beim Erstellen von Kanban-Tasks zu beachten ist
- `~/docs/system/kanban-coverage-map-install-plan-2026-07-09.md` — Initial-Beispiel für Kanban (557 Zeilen)