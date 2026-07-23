# Basti Home-Projects Scan — Reference Example
> Concrete output of the `project-landscape-audit` methodology, 2026-07-04.
> 28 project folders scanned, 14 Git repos, 14 No-Git folders.

## Key Relationships Discovered

### Hermes V7 Clone Family (3 repos, 1 remote URL)

| Repo | Branch | Commits | Role |
|---|---|---|---|
| `hermes-v7-wt/` | `feature/yuno-mobil-setup-bundle` | **15** | **🏆 MASTER** — voller Code, Orchestrator, Gates, Audit |
| `hermes-zorin/` | `Zorin-Hermes-alt` | **10** | Worktree-Fork (ZorinOS-spezifisch: Mnemosyne DB, Depp-Layer) |
| `hermes-v7-orphan/` | `main` | **1** | 🌱 Config-Only-Subset (Skills + Setup-Skript, kein Code) |

**All three** point to `https://github.com/Toqsick/hermes-v7.git` — identical remote.
Decision: `hermes-v7-wt` as master, others as worktrees/submodules.

### GreyHack Duplicate Repos (identical README, same maintainer)

Both `greyhack-tools/` and `greyscripts/` have **identical README header** ("GreyHack Tools — GreyScript Suite").
`greyhack-tools` is active (2026-07-04), `greyscripts` stagnated (2026-06-20).

Decision: Merge `greyscripts` → `greyhack-tools` via `git remote add` + `fetch`.

### Cross-Project Code Duplication

`telegram_helper.py` exists in **both** `yuno-voice-bot/` and `yuno-cleaner/`.
Decision: Extract into `shared/` subdirectory in a future Yuno monorepo.

## Git Init Candidates (by activity)

| Project | Last Activity | Size | Priority |
|---|---|---|---|
| `cp77-modding/` | 2026-07-04 | 1.2 GB | **P0** — no git, active, large |
| `steam_backup_toolkit/` | 2026-06-03 | 108K | P1 — mature, standalone |
| `yuno-voice-bot/` | 2026-07-02 | 200K | P0 — active, Docker-based |
| `yuno-cleaner/` | 2026-06-27 | 252K | P1 — well-structured |
| `yuno-dashboard/` | 2026-07-01 | 144K | P1 — with cockpit to merge first |

## Cleanup Targets Found

- `reports/` — empty (only `.` and `..`)
- `hermes-chat/` — 3 stub files from 2026-06-12 (bridge.pid, request.txt, response.txt all empty)

## Monorepo Candidates

1. **Yuno:** `yuno-{voice-bot,cleaner,cockpit,dashboard}` → `yuno/` with workspaces
2. **Hermes V7:** `hermes-v7-wt` as master, `hermes-zorin` + `hermes-v7-orphan` as worktrees
3. **GreyHack:** `greyhack-tools` as master, `greyscripts` merged in, `greyhack-repos` as submodules

## What NOT to Touch

- `Ausgaben/`, `logs/`, `results/`, `reports/` — output/data drops (not source repos)
- `minimax-install/` — binary Installer payload (115 MB .deb)
- `odysseus/` — 4.3 GB foreign fork (`pewdiepie-archdaemon/odysseus`)
- `hermes-webui-desktop-companion/` — foreign maintainer (`franksong2702`)
- `LenovoLegionLinux/` — foreign repo, Basti only consumes
