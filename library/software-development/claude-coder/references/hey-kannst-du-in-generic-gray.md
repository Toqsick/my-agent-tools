# Hermes Workflow-Templates & Skills Refactor — 2026-07-06

## ⏸ FORTSCHRITT (Stand: Session pausiert 2026-07-06, "machen später weiter")

**Backup liegt in `~/backups/hermes-refactor-2026-07-06/` (62 MB, komplett).**
Config-Altbackups nach `~/backups/hermes-config-baks/` verschoben.

- ✅ **Phase 0** — Backup + Preflight fertig. Gateway läuft (PID 12620), Hot-Reload bestätigt.
- ✅ **Phase 1** — Workflow-Kern KOMPLETT:
  - jobs.json (via `hermes cron edit`): 6 GreyHack-Jobs → workdir `~/10-Projekte/10-active/greyhack-tools`;
    mobil-watchdog (`6003e431dad7`) → workdir `~/10-Projekte/20-experimental/hermes-v7-wt`, Prompt-Pfade gefixt;
    Duplikat `a167de38428d` (greyhack-ci-watch) ENTFERNT (jetzt 24 Jobs);
    morning-briefing (`fb4d5e448c51`) → workdir `~/10-Projekte/10-active/yuno-voice-bot`, morphreader-Pfade → `~/20-Workspace/scripts/`;
    Todoist-Job (`08ff393b7004`) → Name `yuno-weekly-todoist-review`, Prompt zeigt jetzt auf `~/10-Projekte/20-experimental/hermes-v7-todoist` statt `/tmp/hermes-v7`.
    **⚠ OFFEN**: Der stabile Clone `~/10-Projekte/20-experimental/hermes-v7-todoist` wurde vom Auto-Mode-Classifier BLOCKIERT (untrusted external repo clone). Der Prompt referenziert den Pfad + enthält weiter den `git clone`-Fallback — Basti muss den Clone selbst anstoßen ODER wir klonen mit Freigabe. Bis dahin läuft der Job in den git-clone-Fallback (funktioniert, aber klont nach jeder Ausführung neu). Job ist aktiv.
    `76039d75e57d` (master-workflow-8h) PAUSIERT bis Phase 2 fertig.
  - `grep maxclaw-clone jobs.json` → 0 Treffer ✅
  - config.yaml: comfyui v5.1.0 nach `skills/creative/comfyui` kopiert (löst jetzt auf ✅); Lane-Duplikate entfernt (koenigin: 2. `writing-plans`; worker-heavy: 2. `test-driven-development` + 3. `hermes-agent-skill-authoring`); YAML valide.
  - swarm-templates.sh: neu geschrieben (`set -euo pipefail`, `run_swarm()`-Funktion, Pfade gefixt, docs-Default → `greyhack-tools/greyhack-tools/lib_core/lib_core.src`); Syntax OK.
  - run-master-workflow.sh: auf manual-only umgebaut, SKILL_PATH → `orchestration/multi-agent-master-workflow/references/pipeline-spec.yaml` (Ziel entsteht in Phase 2).
- 🔄 **Phase 2** — IN ARBEIT (gerade gestartet, noch NICHTS editiert):
  - Struktur bereits gelesen: `SKILL.md` (196 Z.) hat den Phase-1→2→3-Kontrakt als ASCII-Block (Z.100-132) + Farblegende (Z.89-98).
  - Templates in `references/templates/`: 00-decision-tree, 01-05 + combinations. Kontrakt-Duplikate v.a. in `04-greyscript.md` (Phase 1/2 explizit, Z.51/68) und `02-repo-cicd.md` (Z.26/70). `03-security-cve.md` hat "Critic-Gate-Checkliste (Phase 2)".
  - `references/meta/`: changelog.md, color-legend.md, mnemosyne-hooks.md (existieren schon).
  - **NÄCHSTER SCHRITT**: `references/phase-contract.md` anlegen (Kontrakt aus SKILL.md Z.100-132 + Legende), dann SKILL.md verschlanken, dann in 02/03/04 (+01/05 prüfen) die Kontrakt-Prosa durch "Vertrag: siehe ../phase-contract.md" ersetzen, dann `multi-agent-master-workflow` SKILL.yaml → `orchestration/multi-agent-master-workflow/{SKILL.md,references/pipeline-spec.yaml}` konvertieren, dann Plan-Doc Plural→Singular, dann Job `76039d75e57d` per `hermes cron resume` reaktivieren.
- ⬜ **Phase 3** — Stale-Path-Fixes (11 Skills) — noch nicht begonnen.
- ⬜ **Phase 4** — Library-Strukturbereinigung — noch nicht begonnen.
- ⬜ **Phase 5** — 8 Monolithen verschlanken — noch nicht begonnen.
- ⬜ **Phase 6** — NAVIGATION.md-Regen + Endverifikation — noch nicht begonnen.

**Wichtig für Wiederaufnahme:** jobs.json NUR via `hermes cron edit/remove/pause/resume` ändern
(Hot-Reload + Locking). Nie `~/.hermes/.env` lesen/ausgeben. Task-Liste (#1–#7) spiegelt die Phasen.

---

## Context

Basti will, dass Hermes einen schnelleren und besseren Workflow bekommt. Die Exploration von
`~/.hermes` (Workflow-Templates + Skills-Library, 224 aktive Skills) ergab: Das Design des
`workflow-template`-Skills ist solide, aber die operative Ebene ist seit der Home-Restrukturierung
vom 2026-07-04 kaputt — tote Pfade in Cron-Jobs und Skills, unauflösbare Skill-Referenzen,
3-fach duplizierter Phasen-Kontrakt, ein Schattenbaum `skills/skills/`, ein aktiv Lookups
brechendes Skill-Duplikat und 90-KB-Monolithen, die unnötig Kontext fressen.

**Basti hat explizit autorisiert, direkt in `~/.hermes` zu editieren** (hebt die
CLAUDE.md-Konvention "report, don't edit" für diese Session auf) — mit Backup jeder Datei vorher.

### Entscheidungen (von Basti)
- Direkt editieren, Backups nach `~/backups/hermes-refactor-2026-07-06/`
- Voller Scope: Workflow-Kern + Skill-Pfad-Fixes + Library-Strukturbereinigung + **alle 8** Monolithen
- GreyHack-Jobs: workdir auf `~/10-Projekte/10-active/greyhack-tools` umbiegen (deaktivierte bleiben deaktiviert)
- Todoist-Job + master-workflow-8h: **beide voll reparieren** (nicht nur pausieren)
- comfyui: gebundelte v5.1.0 aus `hermes-agent/skills/creative/comfyui` in die Haupt-Library kopieren

### Verifizierte Fakten (Planungsphase, read-only)
- `hermes-gateway.service` läuft; Scheduler liest `jobs.json` **pro Tick neu** (Hot-Reload,
  `hermes-agent/cron/scheduler.py:3387`), File-Locking in `cron/jobs.py:20` →
  **jobs.json NUR über `hermes cron edit/remove/pause/resume` ändern, kein Neustart nötig.**
- `config.yaml`-Skill-Config ist mtime-gecacht → Edit invalidiert automatisch. `skill_lanes` hat
  keine Code-Konsumenten (reine Prompt-Konvention).
- Skill-Namensauflösung (`tools/skills_tool.py:1040-1082`): `category/name`-Pfad ODER
  Dir-Basename ODER Frontmatter-`name:`. `.archive` wird ausgeschlossen, der Schattenbaum
  `skills/skills/` wird MIT gescannt.
- `ideation` + `audiocraft-audio-generation` in den Lanes sind NICHT kaputt (lösen via
  Frontmatter auf) — nur `comfyui` ist tot.
- Kaputt entdeckt: Job-Refs auf `skill-navigator` + `multi-agent-orchestration` lösen nicht auf
  (Slash-Präfix im Frontmatter-`name:`, 7 Skills betroffen); `multi-agent-master-workflow` ist
  nur eine SKILL.yaml ohne SKILL.md → scanner-unsichtbar; Duplikat `llm-evaluation-troubleshooting`
  (mlops-evaluation/ vs mlops/evaluation/) bricht `skill_view` per Disambiguierungs-Fehler.
- Alle neuen Zielpfade existieren (verifiziert): `~/10-Projekte/10-active/greyhack-tools`
  (+ build/yuno_v6.src, yuno_viper), `~/10-Projekte/10-active/yuno-voice-bot`,
  `~/20-Workspace/scripts/morphreader_summary_v6.py` + `morphreader-briefing.md`,
  `~/30-Library/greyscripts` (+ docs, + scripts/monitor-setup.sh), `~/20-Workspace/fix-scripts`,
  `~/50-System/bin/{greyhack-deploy,greyhack-build,hermes-gh-api-server.py}`, `~/hermes-v7-work`.

**Sicherheitsregel für die ganze Ausführung:** Nie Inhalte von `~/.hermes/.env` (oder andere
Secrets) lesen/ausgeben. Prompt des Todoist-Jobs sourct `.env` — Pfade referenzieren, nie zitieren.

---

## Phase 0 — Backup + Preflight

1. `mkdir -p ~/backups/hermes-refactor-2026-07-06`, dann `rsync -aR` (relativ ab `~/.hermes`) für
   alle zu ändernden Dateien/Dirs: `cron/jobs.json`, `config.yaml`, `scripts/swarm-templates.sh`,
   `scripts/run-master-workflow.sh`, `plans/2026-07-05_workflow-templates-skill.md`,
   `skills/orchestration/workflow-template/`, `skills/multi-agent-master-workflow/`,
   `skills/skills/`, `skills/orchestration/{orchestration,navigator,multi-agent-code-gen-pipeline,pitfalls}/`,
   `skills/productive/`, `skills/mlops-evaluation/`, `skills/mlops/evaluation/`, `skills/gaming/`,
   `skills/devops/{linux-system,linux-display-setup,github-grayhack-workflow}/`,
   `skills/note-taking/{system-documentation,vault-architecture}/`,
   `skills/software-development/skill-library-maintenance/`, `skills/creative/ui-factory/`,
   `skills/productivity/daily-briefing/`, `skills/NAVIGATION.md`.
2. Preflight: `hermes cron status`; JSON-Parse-Check `jobs.json`; YAML-Parse-Check `config.yaml`.

## Phase 1 — Workflow-Kern (Live-Config)

### 1a. jobs.json — nur via `hermes cron edit`, nach jedem Edit `hermes cron list`
| Job | Änderung |
|---|---|
| `136adfd9b583` db-watcher, `313b46f3c5a2` mission-tracker, `72b7ea3ca966` basti-checkin, `d4badeb9a4da` knowledge-distiller, `f4901b88ee45` tool-builder (disabled) | `--workdir /home/bratan/10-Projekte/10-active/greyhack-tools` |
| `6003e431dad7` greyhack-mobil-watchdog (disabled) | `--workdir /home/bratan/hermes-v7-work`; im Prompt `~/greyhack-tools/src/` → `~/10-Projekte/10-active/greyhack-tools/src/` |
| `a167de38428d` greyhack-ci-watch (Duplikat) | `hermes cron remove` (das reichere `0de66e3162ec` behalten, dessen workdir auf greyhack-tools setzen) |
| `fb4d5e448c51` yuno-morning-briefing | `--workdir ~/10-Projekte/10-active/yuno-voice-bot`; im Prompt beide morphreader-Pfade auf `~/20-Workspace/scripts/` umschreiben (Prompt via python aus jobs.json extrahieren, string-replace, per `--prompt` zurück) |
| `08ff393b7004` (Name = Prompt) | `--name yuno-weekly-todoist-review`; **voll reparieren**: kaputten `/tmp/hermes-v7/src/plugins`-Bootstrap analysieren, stabilen Ersatzpfad finden (Kandidat: `~/hermes-v7-work` — bei Ausführung verifizieren), Prompt umschreiben, aktiviert lassen. `.env`-sourcende Zeile: Pfad ok, Inhalt nie ausgeben |
| `76039d75e57d` multi-agent-master-workflow-8h | Nach Phase 2 (Skill wird auflösbar) reaktiviert lassen/reaktivieren; bis dahin pausieren |

Verify: `grep -c maxclaw-clone jobs.json` → 0; Smoke-Run `hermes cron run fb4d5e448c51`, Output unter `~/.hermes/cron/output/` prüfen.

### 1b. config.yaml (eine Edit-Session)
- comfyui: `cp -r ~/.hermes/hermes-agent/skills/creative/comfyui ~/.hermes/skills/creative/comfyui` → Lane-Ref löst wieder auf (kein config-Edit nötig).
- Lane-Duplikate dedupen: `koenigin` 2× `writing-plans`; `worker-heavy` 2× `test-driven-development`, 3× `hermes-agent-skill-authoring`.
- `ideation`/`audiocraft-audio-generation` NICHT anfassen (funktionieren).
- 19 `config.yaml.bak*`/`*.corrupt.*` aus `~/.hermes/` root nach `~/backups/hermes-config-baks/` verschieben.
- Verify: YAML-Parse, `hermes doctor`, `hermes skills list >/dev/null`.

### 1c. Scripts
- `swarm-templates.sh`: Rewrite mit `set -euo pipefail`, eine `run_swarm()`-Funktion + Daten-Tabelle statt 5 kopierter Blöcke; `~/greyhack-tools/` → `~/10-Projekte/10-active/greyhack-tools/` (Existenz von `lib_core.src` dort prüfen); `~/docs/system/`-Ziel prüfen (existiert), firecrawl-web-Caveat-Kommentar behalten.
- `run-master-workflow.sh`: toten `localhost:5000`-POST-Branch entfernen (oder hinter explizit gesetztem `HERMES_ENDPOINT` gaten), Header-Kommentar "manual-only", `SKILL_PATH` an Phase-2-Move anpassen.

## Phase 2 — workflow-template: Single Source of Truth

1. `references/phase-contract.md` neu: kanonischer Phase-1(Plan/Freigabe)→2(Auto-Mode+Queen-Verification)→3(Reflection/Mnemosyne)-Kontrakt + Farblegende (Inhalt aus SKILL.md gehoben).
2. `SKILL.md` verschlanken: Frontmatter, Overview, Decision-Tree-Pointer, 1-Absatz-Kontrakt-Summary + `skill_view(..., file_path="references/phase-contract.md")`-Pointer.
3. Alle `references/templates/0*.md`: duplizierte Kontrakt-Prosa strippen, nur Domain-Deltas + eine Zeile "Vertrag: siehe ../phase-contract.md" (04-greyscript hat 4 Kopien, 02-repo-cicd 2).
4. `multi-agent-master-workflow` konvertieren: nach `orchestration/multi-agent-master-workflow/` verschieben, echtes `SKILL.md` (Frontmatter `name: multi-agent-master-workflow`, Rollenbeschreibung, Kontrakt-Pointer) + alte YAML als `references/pipeline-spec.yaml`. Macht Job `76039d75e57d` erstmals funktionsfähig → danach Job reaktivieren.
5. `plans/2026-07-05_workflow-templates-skill.md`: `workflow-templates` (Plural) → `workflow-template` (Dir bleibt Singular, kein Trigger-Rewiring).
- Verify: `hermes skills list | grep -E "workflow-template|multi-agent-master-workflow"`.

## Phase 3 — Stale-Path-Fixes in Skills (prompt-only, per sed)

Verifizierte Mapping-Tabelle:
| Alt | Neu |
|---|---|
| `~/bin/greyhack-{deploy,build}` | `~/50-System/bin/greyhack-{deploy,build}` |
| `~/build/yuno_v6.src` | `~/10-Projekte/10-active/greyhack-tools/build/yuno_v6.src` |
| `~/greyhack-tools/...` | `~/10-Projekte/10-active/greyhack-tools/...` |
| `~/greyscripts(/docs)` | `~/30-Library/greyscripts(/docs)` |
| `~/fix-scripts` | `~/20-Workspace/fix-scripts` |
| `~/bin/monitor-setup.sh` | `~/30-Library/greyscripts/scripts/monitor-setup.sh` |
| `~/bin/hermes-gh-api-server.py` | `~/50-System/bin/hermes-gh-api-server.py` |
| `~/scripts/morphreader_*` | `~/20-Workspace/scripts/morphreader_*` |

Betroffene Dateien (11): `gaming/greyhack`, `gaming/greyhack-greyscript` (~Z.1254), `gaming/greyhack-sandbox` (~Z.129), `gaming/greyhack-hermes-api` (~Z.86), `devops/github-grayhack-workflow`, `devops/linux-system`, `devops/linux-display-setup`, `note-taking/system-documentation`, `orchestration/multi-agent-code-gen-pipeline`, `productivity/daily-briefing` (Z.227-228) — jeweils `SKILL.md`.
Plus: `productive/filesystem-restructure-execution/` komplett nach `skills/.archive/productive/` (abgeschlossene Einmal-Migration, Pfade dort NICHT fixen).

Verify: `grep -rnE '~/greyhack-tools|~/greyscripts|~/fix-scripts|/home/bratan/scripts/|~/bin/(greyhack|monitor|hermes-gh)|~/build/yuno' ~/.hermes/skills --include=SKILL.md | grep -v .archive` → leer.

## Phase 4 — Library-Strukturbereinigung

1. **Schattenbaum `skills/skills/` mergen** (8 Skills, 0 Basename-Kollisionen verifiziert):
   `hermes-s6-container-supervision`, `multi-agent-research` → `software-development/`;
   `openhue` → neues `smart-home/`; `xurl` → neues `social-media/`;
   `voice-assistant-bots`, `web-design-guidelines`, `yuanbao`, `yuno-cleaner` → `skills/`-Root.
   `skills/skills/.archive/*` → `skills/.archive/from-shadow-tree-20260706/`; danach `skills/skills/` löschen.
2. **`orchestration/orchestration/`** → umbenennen in `orchestration/multi-agent-orchestration/`,
   Frontmatter `name: multi-agent-orchestration` → fixt Job `d4badeb9a4da`.
3. **Slash-Namen-Fixes** (7 Frontmatter-`name:` ohne `category/`-Präfix): `navigator` →
   `name: skill-navigator` (fixt 2 Job-Refs), `pitfalls` → `multi-agent-pitfalls-cheatsheet`,
   plus `deployment-landing-zone`, `fable-orchestration-pattern`, `multi-agent-code-gen-pipeline`,
   `ui-design-system`. Vor jedem Fix: grep auf den alten Slash-Namen.
4. **mlops-Duplikat**: beide `llm-evaluation-troubleshooting` diffen, die reichere Version unter
   `mlops/evaluation/` behalten, andere nach `.archive/`, `rmdir mlops-evaluation`.
5. **`productive/` → `productivity/`**: `directory-structure-audit` verschieben, `rmdir productive`
   (0 externe Refs verifiziert).
6. `.archive`-Zwillinge in Ruhe lassen (Curator verwaltet die).

Verify: `hermes skills list` — keine Kategorie "skills" mehr, verschobene Skills korrekt kategorisiert, keine Namens-Kollisionen.

## Phase 5 — Monolithen verschlanken (alle 8)

Reihenfolge: `gaming/greyhack-greyscript` (94KB, Exemplar), `note-taking/vault-architecture` (91KB),
`software-development/skill-library-maintenance` (53KB), `gaming/greyhack-sandbox` (49KB),
`gaming/cp77-modding-linux` (42KB), `creative/ui-factory` (40KB), `gaming/greyhack` (39KB),
`orchestration/pitfalls` (37KB).

Muster pro Skill:
1. H2-Sektionen mappen, in 3–8 `references/NN-topic.md`-Chunks gruppieren (verbatim verschieben).
2. `SKILL.md` neu auf ≤8–10KB: Frontmatter (`name:` UNVERÄNDERT), Purpose, Trigger,
   Decision-Tree, Index-Tabelle "Thema → `references/NN-topic.md`" (`references/` ist als
   Support-Dir anerkannt, `agent/skill_utils.py:SKILL_SUPPORT_DIRS`).
3. Verify pro Skill: `hermes skills list` zeigt ihn; `wc -c` SKILL.md unter Budget;
   Summe Chunks + SKILL.md ≈ alte Größe (kein Inhaltsverlust).

## Phase 6 — NAVIGATION.md-Regen + Endverifikation

1. `skills/NAVIGATION.md` aus Live-Scan regenerieren (python: Kategorien + Counts; real ~222 aktiv nach Merges/Archivierung — aktuelle Datei behauptet ~100).
2. Verifikations-Suite:
```bash
python3 -c "import yaml;yaml.safe_load(open('/home/bratan/.hermes/config.yaml'))"
python3 -c "import json;d=json.load(open('/home/bratan/.hermes/cron/jobs.json'));print(len(d['jobs']),'jobs OK')"
hermes doctor
hermes cron status && hermes cron list
hermes skills list | head -50
hermes cron run fb4d5e448c51    # Smoke: Morning-Briefing; danach ~/.hermes/cron/output prüfen
grep -rn "maxclaw-clone\|/home/bratan/greyhack-tools\|/home/bratan/scripts/" ~/.hermes/cron/jobs.json  # → leer
```
3. Abschlussreport an Basti: was geändert, was pausiert/reaktiviert, Backup-Pfad.

## Offene Punkte zur Ausführungszeit
- Todoist-Job-Rework: stabilen Ersatz für `/tmp/hermes-v7/src/plugins` finden (Kandidat `~/hermes-v7-work`) — falls kein funktionierender Bootstrap auffindbar: Job pausiert lassen + melden.
- `monitor-setup.sh` liegt untypisch in `~/30-Library/greyscripts/scripts/` — Referenz dorthin; Umzug nach `~/50-System/bin/` wäre separater Task außerhalb `.hermes`.
- `hermes-memory`-Ref in 2 deaktivierten Jobs existiert nicht — nur notieren, fixen falls je reaktiviert.
- `vault-architecture`/`skill-library-maintenance`: exakte Pfade bei Ausführung lokalisieren.
