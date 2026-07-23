# Deployment-Doc Example: YUNO V6 (2026-07-04)

**Concrete artefact from 2026-07-04 session.** See the full doc at:
`~/docs/system/greyhack-yuno-v6-deploy-2026-07-04.md` (438 lines, 16.9 KB)

## Context
Basti asked: "Erstelle die Deployment-Doku für YUNO V6 im Spiel: CodeEditor-Workflow, Build-Schritte, Troubleshooting."

This was a **subagent-orchestrated task** — the parent session waited for Agent 4 results which were still pending at the time of writing.

## What the doc covers
- **Why not pc.wget()** — GreyHack has NO in-game shell wget. CodeEditor is the only reliable path for .src files.
- **5-step workflow** — Host build → SCP/FTP transfer → CodeEditor (Ctrl+O/Ctrl+B/F5) → Run → Auto-Config
- **Module table** — 15 sections (CORE/SESSION/SCAN/FILES/NETWORK/CRYPTO/UTILS/MACROS/MISSIONS/...) with 60+ commands
- **Build steps** — `npx greybel build yuno_v6.src -u` with Mock-Env smoke-test checklist (12/12)
- **Troubleshooting** — 12 failure scenarios: build errors (Memory-limit, Index-bounds), runtime (Not-in-shell, Config-korrupt, MetaxploitLib fehlt, Coop-Simulation), in-game (Persistenz-Verlust, nmap tot)
- **Quick-Reference Card** — one-panel summary
- **Agent-4 Pending marker** — documented as still-awaited

## Sources consulted (3-source triangulation)
1. Build artifacts: `~/build/yuno_v6.src` (45.7 KB, 2183 lines)
2. Existing docs: `~/docs/system/greyhack-yuno-v6-2026-07-03.md` (feature overview, no deployment steps)
3. DB archaeology: `greyhack-deep-content-2026-07-04.md`, `greyhack-deep-systems-2026-07-04.md`, `greyhack-deep-research-2026-07-04.md` (in-game module lists, player PC at gregor@219.50.230.162, Config/ path, all 14 YUNO modules)

## Key learnings for future docs
- Always check Agent-X/Subagent results first — document the gap if absent
- The document template (Why-not → Steps → Module-Overview → Build → Troubleshooting → QuickRef) is reusable
- Player-PC details matter: `gregor@219.50.230.162`, hostname `ibm`, Config path `/home/gregor/Config/`
- In-game module sizes from DB dumps (yuno_v6: 78KB, ftp: 12KB) determine deployment method