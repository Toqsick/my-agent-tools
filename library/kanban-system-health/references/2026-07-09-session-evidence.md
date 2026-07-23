# 2026-07-09 Session Evidence & Live-Verified Data

**Zweck:** Diese Reference-Datei sammelt **echte Live-Daten** aus den 2026-07-09 Sessions, die das SKILL.md-Patchen rechtfertigen. Alle Zahlen/Prozesse/Findings wurden **durch Tool-Calls verifiziert**, nicht aus dem Gedächtnis.

---

## Session-Timeline

| Phase | Dauer | Coverage | Total Tasks | Done |
|---|---|---|---|---|
| Start (Baseline) | — | 40% | 51 | 22 |
| Phase 0+1 (Cleanup + Ready-Assignment) | ~1h 15min | 52% | 51 | 22 |
| Phase 2 (Worker-Maturity + Worktree) | ~45min | 62% | 51 | 33 |
| Phase 3 (Advanced Patterns + Auto-Decomp) | ~45min | 73% | 58 | 36 |
| Phase 4 (6-Bienen-2-Wellen-Dispatch) | ~45min | 88% | 68 | 49 |
| End of Session | — | 88% | 68 | 49 |

**Total Session:** ~3.5 Std, Coverage +48pp, +27 Done-Tasks.

---

## Live-Verifizierte Profile-Skill-Mapping (2026-07-09)

**Befund aus Goal-Mode-Output (`hermes-profile-skill-map-2026-07-09.md`):**

| Profil | Skills | Top-Level Kategorien | vs default |
|---|---|---|---|
| `default` | 72 | 17 | Baseline |
| `yuno` | 129 | 31 | +57 |
| `yuno-coder` | 72 | 17 | **+0** (= default!) |
| `yuno-vision` | 72 | 17 | **+0** |
| `yuno-flash` | 72 | 17 | **+0** |
| `local-9b` | 96 | 26 | +24 (Subset von yuno) |
| `yunoo` | 76 | 18 | +4 |

**Implikation:** `yuno-coder`, `yuno-vision`, `yuno-flash` sind aktuell **bit-identisch zu default** — Spezialisierung existiert nur über Modell-Wechsel (GLM vs M3 vs Flash), NICHT über Skill-Sets.

**Lösung:** Skill-Migration Variante B aus `skill-migration-plan-2026-07-09.md`.

---

## Worktree-Test (verifiziert 2026-07-09 Phase 2)

**Task:** `t_5e94e7e6` (suid_exploit.py Refactor mit Worktree)

**Initial-Failure (Circuit-Breaker trippte):**
```
Error: workspace: task t_5e94e7e6 has workspace_kind=worktree but no
workspace_path, and board 'greyhack' has no default_workdir set.
```

**Resolution:**
1. `hermes kanban boards set-default-workdir greyhack ~/10-Projekte/10-active/greyhack-tools`
2. `hermes kanban unblock t_5e94e7e6 --reason "default_workdir set"`
3. Worker dispatched, Worktree erstellt: `.worktrees/t_5e94e7e6/`
4. Branch `feat/suid-exploit-types` aktiv in Worktree
5. Worker-CWD = `/home/bratan/10-Projekte/10-active/greyhack-tools/.worktrees/t_5e94e7e6`
6. Task lief 2 Runs (517s + 651s), endete mit `timed_out` (Iteration-Budget 80/80)

**Verifiziert via:**
```bash
cd ~/10-Projekte/10-active/greyhack-tools && git worktree list
# /home/bratan/10-Projekte/10-active/greyhack-tools                        b200313 [main]
# /home/bratan/10-Projekte/10-active/greyhack-tools/.worktrees/t_5e94e7e6  b200313 [feat/suid-exploit-types]

git -C ~/10-Projekte/10-active/greyhack-tools branch --list
#   backup/develop-before-cherrypick-2026-07-05
# * main
# + feat/suid-exploit-types    ← NEU
```

---

## Auto-Decomp Live-Verification (2026-07-09 Phase 3)

**Input-Task:** `t_12a36b49` "Bau ein Loki-Log-Aggregator-Plugin für Yuno-Cockpit" (Status: triage)

**Decompose-Output (auto-generiert vom Decomp innerhalb von 60s):**
```
t_12a36b49 (root, yuno, todo, waiting for 6 children)
├─ t_f76c867d (Design architecture and data flow)         → yuno     → RUNNING
├─ t_7b471977 (Implement log collector + normalizer)      → yuno-coder → todo
├─ t_ace98dc7 (Implement Loki push client + query)        → yuno-coder → todo
├─ t_5f4cd974 (Build TUI widget renderer)                  → yuno-coder → todo
├─ t_f52972de (Build WebUI dashboard widget)              → ui-builder → todo  ← Brachliegendes Profil!
└─ t_ccc8c055 (Write plugin README and docs)               → yuno     → todo

Comment by auto-decomposer:
"Decomposed into t_f76c867d, t_7b471977, t_ace98dc7,
 t_5f4cd974, t_f52972de, t_ccc8c055. Root will wake
 when all children complete."
```

**Wichtig:** Decomp wählte `ui-builder` für WebUI-Widget — brachliegendes Profil wurde automatisch reaktiviert.

---

## 6-Bienen-2-Wellen-Dispatch Resultate

**Wave 1 (sofort):**
- `t_3b45665b` (Biene 1): Kanban-System-Health-Audit
- `t_f8fa2a24` (Biene 2): Hermes-Memory-Deep-Cleanup
- `t_797d14a1` (Biene 3): greyhack-tools Test-Coverage-Map

**Wave 2 (nach 5s Delay):**
- `t_6cc2c9ba` (Biene 4): Hermes-Skill-Migration-Plan
- `t_a8979c00` (Biene 5): Tool-Coverage-Audit
- `t_346d7dbd` (Biene 6): Hermes-Config-Secrets-Audit

**Resultate (alle done in ~10 Min):**
| Biene | Task | Summary |
|---|---|---|
| 1 | Kanban-Health-Audit | "All 5 checks PASS" |
| 2 | Memory-Cleanup | "14 von 20 invalidiert (44% → ~26%)" |
| 3 | Test-Coverage | "Inventur erstellt" |
| 4 | Skill-Migration | "3 Varianten, Empfehlung B" |
| 5 | Tool-Coverage | "32/47 Tools (68%) abgedeckt" |
| 6 | Secrets-Audit | **🚨 "1 CRITICAL + 4 HIGH + 2 MEDIUM"** |

---

## 🚨 Secrets-Audit Findings (Biene-6, 2026-07-09)

**File:** `~/.hermes/config.yaml` Zeile 727
**Mirror:** `~/.hermes/config.yaml.bak.20260708_003022` Zeile 730
**Pattern:** `gho_<40 chars>` GitHub OAuth/Classic PAT
**SHA256:** `0f8d2f8c08f5`
**Risk:** Docker `docker run -e GITHUB_PERSONAL_ACCESS_TOKEN` leakt Token in `ps`/`docker inspect`

**Recommendation (read-only audit, keine Fixes):**
1. Revoke at github.com/settings/tokens
2. Replace-PAT nur in `~/.hermes/.env`
3. Zeile 727 aus config.yaml + Backup entfernen
4. Docker liest dann GITHUB_PERSONAL_ACCESS_TOKEN aus .env

---

## Hermes Dashboard Auth-Block (Phase 4 dokumentiert)

**Versuch:** `hermes dashboard --port 8789 --no-open --host 127.0.0.1`
**Resultat:**
- HTTP 404 für `/`
- HTTP 401 für `/api/plugins/kanban/boards`
- HTTP 401 für `/api/plugins/kanban/tasks?board=...`

**Probierte Fixes (alle scheiterten):**
1. Basic-Auth mit scrypt-Hash + `dashboard_auth/basic` Plugin enabled
2. `dashboard_auth/nous` disabled
3. `--isolated` flag
4. Multiple restarts

**Code-Analyse (web_server.py:393):**
```python
def should_require_auth(host: str, allow_public: bool = False) -> bool:
    """Return True iff the dashboard auth gate must be active.
    Truth table:
      host == loopback        → False (no auth — local-only, trusted operator)
      host != loopback        → True  (gate engages)
    """
    return host not in _LOOPBACK_HOST_VALUES
```

**Trotz loopback-Bind 127.0.0.1 → 401.** Vermutung: Plugin-Loading-Order oder initialisierter State vor Config-Update.

**Workaround:** `hermes serve` (Port 34647, headless) oder Yuno UI (Port 8767).

---

## Hermes-Server-Inventar (alle 3 laufen parallel, 2026-07-09)

| Service | Port | PID | Zweck |
|---|---|---|---|
| `hermes-gh-api-server.py` | 8333 | 3985 | GitHub-API für Cron-Jobs |
| `yuno-ui/server.py` | 8767 | 2088 | Bastis Custom-Cockpit-Dashboard |
| `hermes-webui/server.py` (40-archive/) | 8787 | 2108 | Archiv-WebUI, Kanban-Tab im HTML |
| `hermes serve` (headless) | 34647 | 60215 | Hermes Backend mit Kanban-Plugin |
| `hermes dashboard` (--isolated Test) | 8789 | (versuch) | Browser-UI mit Auth-Gate |

---

## File-Attachment End-to-End Verification

**Test-Pattern (2026-07-09 Welle 2A):**
```python
import sqlite3
from hermes_cli import kanban_db

conn = sqlite3.connect("~/.hermes/kanban/boards/routing-lanes/kanban.db")
task_id = kanban_db.create_task(
    conn, title="...", assignee="yuno", workspace_kind="scratch",
    initial_status="blocked"  # NICHT "ready"!
)
# → status="ready" via SQL UPDATE
task_dir = kanban_db.task_attachments_dir(task_id, board="routing-lanes")
stored = str(task_dir / "file.md")
with open(stored, "wb") as f: f.write(content)
att_id = kanban_db.add_attachment(
    conn, task_id, filename="file.md",
    stored_path=stored, content_type="text/markdown",
    size=len(content), uploaded_by="user"
)
```

**Verifizierte Outputs:**
- Task-ID generiert: `t_52ee599e`
- Attachment-ID: 1
- Storage-Pfad: `~/.hermes/kanban/boards/routing-lanes/attachments/t_52ee599e/test-doc.md`
- Size: 113 bytes
- SHA256: `0aaa96c301c4fd27...`
- Round-trip: `content == file_content` ✅

**Pitfall:** `kanban_db.create_task()` nimmt **conn-Objekt, NICHT db_path**. Auch `create_task`'s `initial_status` muss `blocked` oder `running` sein — `ready` ist nicht erlaubt!

---

## Memory.md Status

**Biene-2 hat Memory-Cleanup gemeldet:**
- "14 von 20 Top-Working-Memory-IDs invalidiert (alle tiny-importance Conversation-Echos / One-Liner ohne dauerhaften Fakt)"
- "6 hochwertige Einträge" blieben

**ABER:** `~/.hermes/memory.md` (Hermes-Memory-File, nicht Mnemosyne) existiert nicht. Biene-2 hat wohl **Mnemosyne-Bank** aufgeräumt (siehe `mnemosyne-memory-provider` Skill):
- 3173 working-memory entries (vorher mehr)
- 462 episodic-memory entries

---

## Quellen für SKILL.md-Patch-Begründung

Diese Reference-Datei ist die **empirische Grundlage** für die Patches in `SKILL.md` v2.0.0:
- Pitfall #9 (Per-Profile Skill-Lookup): belegt durch Worktree-Test und Goal-Mode-Output
- Pitfall #11 (Worktree-Board-Default-Workdir): belegt durch `t_5e94e7e6` Initial-Failure
- Pitfall #15 (Live-Tokens): belegt durch Biene-6 Secrets-Audit (🚨 CRITICAL)
- Pitfall #6 (`hermes config set` Listen als String): belegt durch `notification_sources`-Test
- Pitfall #13 (Pro-Board DB): belegt durch initiale Inventur mit SQL-Loop
- Phase-3 Auto-Decomp-Verifikation: belegt durch `t_12a36b49`-Swarm-Decomposition
- 2-Wellen-Bienen-Pattern: belegt durch 6-Task-Dispatch in dieser Session

---

## Memory-Notizen (Mnemosyne, 2026-07-09)

7 neue Memory-Einträge gespeichert:
1. Phase 0+1 Resultat (Coverage 40%→52%)
2. Skill-Fix-Pattern (Per-Profile Skill-Lookup)
3. Phase 2 (Worker-Maturity, alle Templates)
4. Phase 3 (Auto-Decomp + Config-Pitfalls)
5. Phase 4 (Bienen-Dispatch + Dashboard-Analyse)
6. Phase 5 Plan (6 Subphasen)
7. **🚨 Security-Finding** (GitHub PAT hardcoded in config.yaml) — `importance: 0.95`

---

## Doku-Inventar (15 Files, ~210 KB)

Alle in `~/docs/system/`:
- `kanban-session-final-2026-07-09.md` (10 KB) — Final-Report
- `kanban-phase-5-plan-2026-07-09.md` (13 KB) — 6 Subphasen-Plan
- `secrets-audit-2026-07-09.md` (11 KB) — 🚨 Security-Findings
- `kanban-health-audit-2026-07-09.md` (14 KB) — 5/5 PASS Baseline
- `skill-migration-plan-2026-07-09.md` (20 KB) — 3 Migrations-Varianten
- `tool-coverage-audit-2026-07-09.md` (16 KB) — 32/47 Tools
- `hermes-profile-skill-map-2026-07-09.md` (16 KB) — Goal-Mode-Output
- `kanban-coverage-map-install-plan-2026-07-09.md` (26 KB) — Coverage-Matrix
- `kanban-multi-agent-status-2026-07-09.md` (12 KB) — Initial-Inventur
- `kanban-best-practices-2026-07-09.md` (6 KB) — 5 Task-Templates
- `kanban-phase-2-4-run-2026-07-09.md` (8 KB) — Phase 2-4 Log
- `kanban-phase-0-1-run-2026-07-09.md` (8 KB) — Phase 0+1 Log
- `greyhack-test-coverage-2026-07-09.md` (8 KB) — Biene-3 Output
- `greyhack-suid-exploit-remote-2026-07-09.md` (7 KB) — Worker-Output
- `yuno-cleaner-cron-setup-2026-07-09.md` (5 KB) — Biene-2 Output