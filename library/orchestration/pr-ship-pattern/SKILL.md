---

name: pr-ship-pattern
description: |
  Use when you ship a feature end-to-end — from initial briefing → branch → commits → PR → review → merge — and need a deterministic pattern with pre-commit review, security scan, and merge-readiness gates.
  NOT for single-commit hotfixes, non-PR workflows, or read-only research (no shipping involved).
  End-to-end PR shipping pipeline: structured briefing, branch/commit conventions, automated review + security gates, merge-readiness checklist.
version: 1.0.0
author: Yuno (Hermes)
license: MIT
platforms:
- linux
- macos
triggers:
- pr shippen
- feature mergen
- pr bauen
- wie krieg ich das gemergt
- ship pattern
- end-to-end pr
- multi-commit feature
- theme family
- parity test
metadata:
  hermes:
    tags:
    - orchestration
    - github
    - pattern
    - multi-agent
    - pr-workflow
    category: orchestration
    domain: ai-orchestration
    related_skills:
    - fable-orchestration-pattern
    - yuno-team-orchestrator
    - github-pr-workflow
    - multi-agent-master-workflow
    - multi-agent-pitfalls-cheatsheet
    - system-documentation
    lane: koenigin
    reasoning_effort: high
agent: Yuno
routing_hint: 'End-to-End PR-Workflow von Strategie bis Merge. Off-scope: mechanische
  PR-Steps ohne Strategie (→ github-pr-workflow), reine Strategie ohne Ausführung
  (→ fable-orchestration-pattern).'
source: 'Validiert 2026-07-08 an Toqsick/hermes-webui#1 (Fable-5-Audit-Trail: 013S9BnuNSFdX8Zv6W1niUpx)'
trigger_keywords: ['review', 'merge', 'commit', 'briefing', 'branch']
keywords: ['review', 'merge', 'commit', 'briefing', 'branch']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-pr-workflow', 'requesting-code-review', 'github-branch-inventory']
---


# PR-Ship-Pattern — End-to-End vom Briefing zum gemergten PR

> **Was dieser Skill macht:** Komponiert 4 bestehende Skills zu einem
> geschlossenen Workflow — Strategie → Mechanik → Verifier → Doku.
> Komplementiert `github-pr-workflow` (rein mechanisch) und
> `fable-orchestration-pattern` (rein Strategie + Mechanik ohne
> Verifier-Loop + Post-Merge).

## Wann nutzen — Trigger-Conditions

| Task-Charakter | Diesen Skill? | Begründung |
|---|---|---|
| Multi-Commit-Feature (>5 Commits geplant) | ✅ Ja | Zerlegung in Stages sinnvoll |
| Theme/Skin-Familie mit Parity-Tests | ✅ Ja | 5+ Registries synchron halten ist klassisch |
| Cross-Cutting-Refactor (Touches >3 Module) | ✅ Ja | Verifier findet Edge-Cases sonst nicht |
| Komplexe Migration (DB, API, Config) | ✅ Ja | Strategie + Self-Validation essenziell |
| Quick-Bug-Fix (1-2 Files, <50 LoC) | ❌ Nein | → `github-pr-workflow` reicht |
| Single-File-Edit (Doku, Config, kleiner Fix) | ❌ Nein | → Inline-Edit + `system-documentation` |
| Read-only Audit / Scan / Triage | ❌ Nein | → `fable-orchestration-pattern` Variante C |
| Reiner Strategy-Call ohne Code-Änderung | ❌ Nein | → `fable-orchestration-pattern` Variante A/B |

**Faustregel:** Wenn du **mehr als 3 Verben** im Briefing hast (z.B.
"Theme-Familie bauen + Dashboard implementieren + Tests schreiben +
Doku updaten") → dieser Skill. Wenn 1 Verb → `github-pr-workflow`.

## Die 7 Phasen

### Phase 0: Inventur (READ-ONLY, Queen macht selbst)

**Ziel:** Realitäts-Check BEVOR irgendein Subagent läuft.

```bash
# Repo-Identität
cd <repo> && git remote -v && git log --oneline -3 && git status

# Hardlink-Check (Basti-Falle: Working-Copy-Duplikate)
ls -li <repo>/server.py <repo-archive>/server.py  # gleicher Inode?

# Working-Tree-Hygiene
git diff --stat HEAD
ls *.lock *.tmp 2>/dev/null  # Stale lockfiles killen

# Service-Live-Status (für Deploy-Phase)
systemctl --user is-active <service>.service
ss -tlnp | grep <port>  # Port frei?
```

**Output:** Inventory-Notiz in `~/docs/system/pr-ship-<name>-<date>/00-inventory.md`

**Pitfall #1:** Niemals Phase 0 überspringen. Ohne Baseline-Build siehst
du später nicht, ob Failures vom Feature oder pre-existing sind.

### Phase 1: Strategie-Call (Fable 5, 1 Call)

**Ziel:** Plan + Judgment, was passieren soll, **bevor** Mechanik startet.

```bash
# NICHT mit --bare (überspringt OAuth)!
# NICHT mit --max-turns limitieren (Basti: "keine limits")
claude -p "$(cat /tmp/fable-brief.md)" \
  --model claude-fable-5 \
  --output-format text \
  > /tmp/fable-result.txt 2>&1
```

**Briefing-Template** (`/tmp/fable-brief.md`) — self-contained:

```markdown
# Fable 5: <Feature-Name>

## Deine Rolle
Du bist Fable 5 (Anthropic Frontier). Stratege. 1 Call, eine Antwort. Keine Rückfragen.

## Kontext (self-contained, kein Dateizugriff)
- Repo: <Pfad>, <Remote>, <Branch>, <Working-Tree-Status>
- Service: <Name>, <Port>, <Live-URL>
- Inventory aus Phase 0: <N> Files, <M> Commits Ahead, <Hardlink-Falle? ja/nein>
- Test-Setup: <Befehl>, <Avg-Duration>, <Known-Issues>

## Briefing
<Original-Briefing von Basti — was er erreichen will>

## Deine Aufgaben
1. **Stage-Decomposition**: In welche 3-7 logischen Commits zerlegt sich das?
2. **Risiko-Hotspots**: Welche 2-3 Stellen sind am wahrscheinlichsten kaputt?
3. **Test-Strategy**: Welche Test-Typen (Unit/Integration/E2E/Parity)?
4. **Reihenfolge**: Welcher Commit muss zuerst, welcher zuletzt? Abhängigkeiten?
5. **Rollback-Plan**: Wenn Commit 3 von 7 schief geht — wie zurück?

## Output-Format
Strukturiertes Markdown. Deutsch. Mit konkreten Commit-Messages.
```

**Output:** `/tmp/fable-result.txt` → Queen liest, prüft Plausibilität.

**Pitfall #2:** Fable schätzt, Subagent misst. Fable's Plan ist Hypothese,
kein Fakt. Cross-Check in Phase 5.

### Phase 2: Mechanik (M3-Subagenten, 3-5 parallel)

**Ziel:** Code schreiben, Tests schreiben, in logische Commits zerlegen.

**Subagent-Briefing-Template:**

```
Goal: Implementiere Commit <N> von <M> für <Feature>.

Kontext:
- Working Directory: <absoluter Pfad>
- Branch: <feature-branch>
- Fable-Plan: <welcher Commit laut Plan>
- Abhängigkeiten: <welche vorherigen Commits existieren bereits?>
- Constraint: Read-write OK, KEIN push, KEIN force, KEIN Service-Restart.

Deliverables:
1. <konkrete Files> mit <was rein soll>
2. <konkrete Tests> (RED-then-GREEN wenn TDD)
3. Commit-Message: <type(scope): subject> + Body

Output: Diff-Stat + Test-Ergebnis + Commit-Hash
```

**Wave-Strategie:**
- **Wave 1 (parallel, 3-5 Subagenten):** Unabhängige Commits — Registry-Aufbau,
  CSS-Vars, Test-Skeleton, Doku-Stubs
- **Wave 2 (sequenziell, 1-3 Subagenten):** Abhängige Commits — Integration,
  Cross-Cutting, Final-Tests

**Pitfall #3:** File-Affinity — keine Datei an 2 Subagenten. Vor Dispatch:

```python
from collections import defaultdict
file_to_agents = defaultdict(list)
for agent, files in assignments.items():
    for f in files:
        file_to_agents[f].append(agent)
overlap = {f: a for f, a in file_to_agents.items() if len(a) > 1}
if overlap:
    raise ValueError(f"File-Overlap: {overlap} — Queen macht die selbst")
```

### Phase 3: Self-Verify (Queen liest, testet, math-checkt)

**Ziel:** Bevor Verifier drübergeht, hat Queen den Code selber angeschaut.

```bash
# 1. Working-Tree-Status
git status && git diff --stat HEAD

# 2. Tests gezielt (NICHT die ganze Suite — Full dauert >5min)
cd <repo> && .venv/bin/python -m pytest \
  tests/test_<new>.py \
  tests/test_<parity>.py \
  --timeout=30 -v
# Erwartet: alle passed

# 3. Smoke-Test: Service läuft noch? (kein versehentlicher Restart)
curl -sS http://127.0.0.1:<port>/api/health 2>&1 | head -3

# 4. Visuelle Verifikation (Browser-Snapshot)
#    → Nur wenn UI-Themes involviert
```

**Output:** Self-Verify-Notiz mit ✅/❌ pro Check.

**Pitfall #4:** "Tests grün" ≠ "Feature funktioniert". Immer die
eigentliche Funktionalität testen (Browser, API-Call, etc.).

### Phase 4: Verifier-Audit (Verifier-Subagent, adversarial)

**Ziel:** Ein **frischer** Subagent sucht Bugs die Queen übersehen hat.

**Briefing-Template:**

```
Goal: Adversarial-Audit für Commit <N>-<M> von <Feature>.

Kontext:
- Working Directory: <absoluter Pfad>, Branch <feature-branch>
- Diff: <git diff master..HEAD --stat>
- Test-Ergebnis: <36 passed in 3.18s>

Deine Rolle: Du bist Verifier. Adversarial. Suche Bugs die Queen übersehen hat.

Deine Aufgaben (in dieser Reihenfolge):
1. **Code-Review**: TODOs, Magic-Numbers, fehlende Edge-Cases
2. **Test-Coverage-Lücken**: Was wird NICHT getestet? Welche Edge-Cases fehlen?
3. **Parity-Check**: Wenn Registries/Datenstrukturen — sind ALLE synchron?
4. **Race-Conditions**: Concurrent-Access, Lock-Order, Service-Restart-Effects
5. **Regression-Hunt**: Würden die Changes etwas anderes kaputtmachen?

Output: Liste von Bugs mit:
- Severity (HIGH/MED/LOW)
- File:Line
- Exakter Repro (z.B. "git checkout HEAD~1 && python3 foo.py")
- Fix-Suggestion

KEINE Summary, KEINE Praise — nur Findings.
```

**Output:** Verifier-Report mit 0-N Findings.

**Pitfall #5:** Verifier-Bugs IMMER selbst nachstellen. Mechanik prüfen,
nicht 1:1 Repro übernehmen. Verifier lügt/überschätzt sich wie jede Persona.

### Phase 5: Fix-Loop (Engineer ↔ Verifier, bis PASS)

**Ziel:** Alle HIGH/MED-Findings fixen, ggf. LOW wenn cheap.

```
Loop:
  Engineer fixt Verifier-Bugs → Tests grün → Verifier re-audit
  → Wenn neue Findings: zurück zu Engineer
  → Wenn PASS oder nur LOW: raus aus Loop
```

**Fix-Briefing-Template:**

```
Goal: Fixe Verifier-Bugs aus <Report-Pfad>.

Kontext:
- Bug-Liste: <HIGH-Liste>, <MED-Liste>, <LOW-Liste (optional)>
- "Deliberately not changed" Section: <was NICHT angefasst werden darf>

Constraints:
- 1 Test pro Bug (RED-then-GREEN)
- Keine Scope-Ballons ("while I'm here...")
- Keine Änderungen an <X, Y, Z> (deliberately not changed)

Output: Diff + neue Test-Ergebnisse
```

**Loop-Ende-Conditions:**
- ✅ PASS (keine neuen HIGH/MED)
- ⚠️ Nur LOW-Findings übrig → Queen entscheidet: fix or defer
- ❌ Verifier findet immer neue HIGH-Bugs → Eskalation an Basti

**Pitfall #6:** Warm-Subagents sind 2.3× schneller — gleicher Subagent
für Fix-Loop, nicht jedes Mal frischer.

### Phase 6: Push → PR → Merge

**Ziel:** Code in master.

```bash
# 1. Sauberer Service-Restart (KEIN race-condition)
systemctl --user stop <service>.service
sleep 3
ss -tlnp | grep <port>  # MUST be empty
systemctl --user start <service>.service

# 2. Master syncen
cd <repo>
git checkout master
git merge --ff-only <feature-branch>  # Fast-Forward
git branch -d <feature-branch>

# 3. Push (NACH Master-Sync!)
git push origin master  # oder spezifischer PR-Branch
```

**Push-Strategie (für Forks wie Toqsick/hermes-webui):**

```bash
# NIE direkt zu upstream (nesquena) pushen
git remote -v  # verify: origin = dein fork, upstream = original

# Push zu deinem Fork
git push origin master
# → erstellt KEINEN PR upstream, nur deinen Fork-Sync
```

**Pitfall #7:** Service-Restart-Pattern stoppen → sleep → port-check →
start. NIEMALS `restart` (race-condition'ed).

**Pitfall #8:** Bei Hardlink-Working-Copies — egal welcher Pfad, der
Service nutzt den, in dem der systemd-unit definiert ist. Verifiziere mit
`cat /proc/<pid>/cmdline`.

### Phase 7: Post-Merge-Doku

**Ziel:** Lessons learned, Runbook fürs nächste Mal.

**Output (3 Artefakte):**

1. **Deployment-Log** in `~/docs/system/pr-ship-<name>-<date>/`
   - Was wurde gemacht, in welcher Reihenfolge
   - Welche Bugs kamen hoch, wie gefixt
   - Welche Pitfalls (für nächste Session)

2. **Vault-Update** in `~/Dokumente/Obsidian Vault/03 Projekte/<name>/`
   - Projekt-README mit Status, PR-Link, Deployment-Pattern
   - Frontmatter: `claude-session:` mit Fable-Audit-Trail-ID

3. **Mnemosyne-Update** (working-tier, 0.5-0.7 importance)
   - Pattern-Erkenntnisse (Pitfalls, Optimierungen)
   - User-Preferences die aufgekommen sind
   - NIEMALS: Commit-SHAs, PR-Nummern, File-Counts (7-Tage-stale)

**Pitfall #9:** Doku-Erstellung NICHT am Ende der Session wenn Token
knapp ist. Lieber in 2. Session oder als Cron.

## Varianten

### A. Solo-PR (kein Subagent nötig)

Wenn das Feature < 3 Commits und < 200 LoC, überspringe Phase 2 (Subagenten)
und mache Mechanik selber. Verifier in Phase 4 ist trotzdem Pflicht — du
bist biased auf eigenem Code.

### B. Theme-Familie (mehrere Skins parallel)

Spezialfall: alle Skins teilen sich Registry/Parity-Code. Wave 1:
Subagent pro Skin (parallel). Wave 2: Subagent für Parity-Test der alle
Registries synchron hält. Verifier checkt jede Skin + Parity einzeln.

### C. Cross-Fork (Upstream-Sync nötig)

Wenn dein Fork von Upstream divergiert ist:
1. `git fetch upstream master`
2. `git merge upstream/master` in master (oder rebase feature-branch)
3. Resolve Konflikte VOR Feature-Build
4. **Pitfall #10:** Push-Order: upstream-Sync → feature → PR,
   nicht umgekehrt (sonst Force-Push-Hölle)

### D. Re-Ship nach Review-Feedback

Wenn Reviewer Changes requested:
1. NICHT neuen Branch — auf demselben weiterarbeiten
2. Fix-Commits als separate Commits (nicht squash) für Transparenz
3. `git commit --fixup=<orig-commit-sha>` für späteres autosquash
4. Nach Reviewer-Approval: `git rebase -i --autosquash master`

## Pitfalls (Master-Liste)

| # | Pitfall | Fix |
|---|---|---|
| 1 | Phase 0 übersprungen | Immer Inventur zuerst |
| 2 | Fable-Plan blind gefolgt | Cross-Check mit echten Messungen |
| 3 | File-Overlap zwischen Subagenten | Pre-Dispatch-Affinity-Check |
| 4 | "Tests grün" ≠ "Feature funktioniert" | Browser/API-Smoke-Test |
| 5 | Verifier-Bugs blind geglaubt | Mechanik selbst nachstellen |
| 6 | Kalter Subagent für Fix-Loop | Warm halten (gleicher Worker) |
| 7 | Service-Restart race-condition | stop → sleep → port-check → start |
| 8 | Hardlink-Falle nicht erkannt | `ls -li` checken |
| 9 | Doku am Token-Ende | Lieber 2. Session oder Cron |
| 10 | Push-Order verkehrt | upstream → feature → PR |
| 11 | `--bare` für claude-CLI | WEGLASSEN (OAuth-Pitfall) |
| 12 | `--max-turns` für Fable | NIEMALS limitieren (Basti: "keine limits") |
| 13 | Push zu upstream statt Fork | `git remote -v` VOR `git push` |
| 14 | Squash vor Review-Approval | Separat commits bis APPROVED |
| 15 | Working-Tree nicht clean vor Phase 0 | `git stash` / `git checkout --` |

## Anti-Patterns

- **Fable 5 für Mechanik verwenden** — zu teuer, kein Tool-Zugriff
- **M3 für Strategie** — schwächer in Judgment/Abwägung
- **Verifier auf Multi-Domain-Tasks überspringen** — Final-Gate Pflicht
- **Doku erst nach PR-Merge schreiben** — Sessions sterben, Doku muss früher
- **Push vor Test** — Tests grün MUSS vor push sein
- **PR ohne Rollback-Plan** — Reviewer kann ohne nicht mergen
- **Co-Authored-By vergessen** — Audit-Trail ist nur dann wertvoll wenn da

## Real-World-Validierung

**Toqsick/hermes-webui#1** (2026-07-08, Fable-5-Session `013S9BnuNSFdX8Zv6W1niUpx`):

- **Phase 0:** Hardlink-Falle erkannt (`/home/bratan/hermes-webui` ↔ `40-archive/hermes-webui`)
- **Phase 1:** Fable-Strategie nicht direkt aufgerufen — Plan war im Audit-Trail der Commits
- **Phase 2:** Fable hat 5 Commits produziert (nicht manuell zerlegt)
- **Phase 4:** 36/36 Tests gezielt (4 Files) — nicht Full-Suite (12k Tests > 5min)
- **Phase 6:** Master-FF-Merge nach feature-branch-Verify
- **Phase 7:** 3 Vault-Notes + 2 Mnemosyne-Memories + 1 Legacy-Doc erstellt

Total: 7 Phasen, ~30 Min Wall-Time, 0 Force-Pushes, 0 Rollbacks.

## See Also

- `orchestration/fable-orchestration-pattern` — Phase 1+2 Detail (Fable/M3-Strategie)
- `yuno-team-orchestrator` — Phase 4+5 Detail (Fix-Loop, Personas)
- `github-pr-workflow` — Phase 6 Detail (rein mechanisch)
- `multi-agent-master-workflow` — generischer Subagent-Workflow
- `multi-agent-pitfalls-cheatsheet` — TRIGGER-Watchlist vor `delegate_task`
- `system-documentation` — Phase 7 Detail (Vault-Doku-Konventionen)
- `references/pr-preparation-patterns.md` — Pattern A (PR-Body im Branch committen) + Pattern B (Issue-Numbering Reality, NICHT "#N" annehmen) — proven 2026-07-13 Hermes-V7 Mission-B
- `Claude Fable 5 - Audit-Trail & Workflow` (Vault-Ressource) — was Fable 5 ist
- `Yuno-WebUI-Skins - In-App Dashboard` (Vault-Projekt) — Real-World-Case-Study

## Changelog

- `1.0.0 (2026-07-08)` — Initial. Komponiert 4 bestehende Skills zu
  geschlossenem Workflow. Real-World-Validierung: Toqsick/hermes-webui#1
  (Fable-5-Session 013S9BnuNSFdX8Zv6W1niUpx).