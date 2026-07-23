---
name: evidence-gated-comparison-workflow
description: Use when comparing two or more software installations, versions, or configurations on a live Linux system with strict no-fabrication requirements. Triggers on "compare", "benchmark", "performance difference", "evidence-based", "no estimates", or when user demands phased user-gated access to a live target system. Catches the pattern where a sandbox/test environment exists alongside a target host and the agent must NEVER confuse the two.
trigger_keywords: ['live', 'system', 'user', 'target', 'comparing']
keywords: ['live', 'system', 'user', 'target', 'comparing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Evidence-Gated Comparison Workflow

A class-level skill for comparing two or more software installations on a live Linux system when the user demands verifiable evidence, explicit status taxonomy, and phased user-gated access. First exercised on the Brave-vs-Brave-Origin benchmark (2026-07-23, Zorin 18.1) — but the pattern is general: any time a target host exists alongside the agent's own runtime, and the user wants claims distinguished from evidence, this skill applies.

## When to use this skill

- User asks to compare two installations (Flatpak vs .deb, two versions, two configs)
- User explicitly demands evidence, "no estimates", "UNVERIFIED markers"
- A target host is mentioned (live Zorin machine, server, dedicated workstation) but the agent's terminal may or may not be on that host
- Multi-artifact deliverable expected (plan, risk register, gate report, comparison table, tuning plan, addon integration)
- User says "verifiziert am Zielsystem" / "no fabrication" / "Phase 0+1+2 zuerst"

**Do NOT use** for simple file comparisons, pure code review, or performance work where the user already runs benchmarks themselves.

## Core principle: NO FABRICATION

Every claim falls into exactly one of five buckets. Use these labels verbatim in every artifact:

| Label | Meaning | Example |
|---|---|---|
| **VERIFIED_TARGET_EVIDENCE** | Read or measured on the actual target host | `brave-browser --version` → `150.1.92.143` |
| **GENERAL_RESEARCH** | Authoritative source, not from target host | Brave GitHub release notes for v1.93.126 |
| **RECOMMENDATION** | Action proposal, pending validation | "Switch Origin to hardened profile" |
| **UNVERIFIED** | Insufficient evidence, blank slot | Cold-Start time, FCP, JS-Heap (not measured) |
| **FAILED** | Test ran but failed/aborted | CDP WebSocket refused connection |

A blank cell is wrong. UNVERIFIED is correct.

## Eight-phase workflow (strict order)

### Phase 0 — Scope, access, risk gate (always first)

Create three artifacts before touching anything:

1. **`plan.md`** — scope, target hosts, browser/tool paths, phases, no-fabrication rule reminder
2. **`risk-register.md`** — classify risks by damage × likelihood, document mitigations
3. **`gate-report.md`** — list each gate (G1, G2, ...) with required user approval

Use the gate pattern: **never assume access**. Each phase that touches a live system has a numbered gate the user must explicitly approve. Default state for every gate is BLOCKED.

### Phase 1 — General research via subagent

Delegate research to a leaf subagent with:
- Clear instruction: **NO target-host claims** (no localhost, no /home/user, no reading files)
- Method allowed: web_search, web_extract, curl HEAD checks, GitHub REST API
- Required output: URL list with status tags ([VERIFIED], [PHANTOM], [BOT-BLOCKED])
- **NEVER** have the subagent write to the target host

Use subagent-live-transcript monitoring: tail the log file under `~/.hermes/cache/delegation/live/<deleg_id>/task-N.log` for progress without burning context on polling.

### Phase 2 — Collector bundle (sandbox-test only)

Build a non-destructive collector that runs read-only by default:

```
comparison/
├── README.md
├── collect.sh                    # wrapper with common flags
├── collect_inventory.py          # read-only inventory
├── run_benchmarks.py             # gated measurement
├── redact.py                     # nachträgliche Redaktion
├── verify-output.py              # schema validation
├── benchmark-config.yaml
├── requirements.txt
├── schemas/
│   ├── inventory.schema.json
│   ├── benchmarks.schema.json
│   └── manifest.schema.json
└── output/                       # JSON + checksum files
```

Test the bundle in the sandbox ONLY for syntax/runtime errors. **Sandbox-test output is NOT target evidence.** Mark any sandbox-test runs explicitly.

### Phase 3 — Inventory on target (G1)

With G1 explicitly granted:
- `readlink -f`, `file -L`, `sha256sum`, `dpkg -S`, `flatpak info`
- For wrapper scripts: `head -n 80` ONLY if `file` reports text
- For ELF binaries: `ldd` for dynamic deps
- For systemd units: `systemctl cat`
- Record every command + exit code + timestamp

### Phase 4 — Extension/profile/addon scan (G3+G4)

Critical: **extension directory presence ≠ activation**. Use the status taxonomy:

| Status | Trigger |
|---|---|
| `VERIFIED_ENABLED` | `disable_reasons: []` in Preferences AND from_webstore: true |
| `VERIFIED_INSTALLED_DISABLED` | Manifest present AND `disable_reasons` non-empty |
| `VERIFIED_PRESENT_STATE_UNKNOWN` | Directory exists but no Preferences entry |
| `NOT_DETECTED` | No directory, no Preferences entry |
| `UNVERIFIED` | Can't determine |

Parse every `manifest.json` for: name, version, manifest_version, permissions, host_permissions, optional_permissions. For Chrome Web Store forks vs. official extensions, cite the canonical ID and verify against `chromewebstore.google.com`.

### Phase 5 — Benchmark plan

Write `benchmark-plan.md` BEFORE running measurements. Pin down:
- Browser-start commands (which binary, which profile path, which flags)
- Stabilization time (60-120s for idle, explicit for cold-start)
- Sampling interval + duration + repetition count (≥5 recommended)
- Workload pages with versioning
- Process-attribution logic (see psutil pattern in references)
- Network/login/cache/autoplay conditions
- Order randomization across runs
- FAILED/UNVERIFIED handling rules

### Phase 6 — Measurement (G2)

Run measurements with user-granted gate. Default G2 grants:
- psutil reading of running processes (no kill, no start)
- Network probing of localhost-only CDP endpoints (read-only targets)

G2 should NEVER default-grant browser start/stop or profile mutation. Each of those is a separate gate (G6, G7).

### Phase 7 — Two measurement modes

Always report two modes separately:

| Mode | Profile | Goal |
|---|---|---|
| **Normalized** | Fresh test profile, identical settings | Isolate engine/build differences |
| **Everyday** | Real user profile (tabs, cache, extensions, accounts) | Measure real-world usage |

Never interpret everyday-mode numbers as product/engine ratings — they conflate too many user-specific variables.

### Phase 8 — Validation and final artifacts

Before declaring done:
- Run `verify-output.py` on every JSON file
- Cross-check version strings, hashes, process counts between raw and computed
- Mark FAILED tests explicitly (don't omit)
- Compute SHA-256 on every output file
- Produce `final-comparison-table.md` with each cell containing: value, unit, mode, conditions, evidence_status, run_id, raw_reference, remarks

## Critical pitfalls (from real sessions)

1. **Sandbox data ≠ target evidence.** When `collect_inventory.py` runs in the test sandbox, its output is sandbox-runtime data. Mark every sandbox-run explicitly or rename the output directory.

2. **Flatpak process tree needs traversal.** Chromium-based Flatpaks wrap in `bwrap` parents. A naive `psutil.process_iter(['name'])` matching "brave" will miss the actual renderer processes. Use both name AND `exe` path; traverse children of matched processes recursively.

3. **Phantom-URL trap in tech docs.** Many Doku sites serve lowercase singular paths (`/tot/runtime/`, `/timeline/`) that 404 — the real endpoints are mixed-case plural (`/tot/Runtime/`, `/tot/Performance/`). Always verify with `curl -I` and have a fallback path. See `references/phantom-urls-known-patterns.md`.

4. **CDP needs WebSocket, not urlopen.** A naive `http://localhost:PORT/json` only returns the page target list. Real FCP/Heap measurement needs `Runtime.evaluate` and `Performance.getMetrics` via WebSocket (`websockets` library or `python-socks`). Mark FCP/Heap as UNVERIFIED if WebSocket client isn't in requirements.txt.

5. **execute_code can be blocked mid-session.** Some environments refuse `execute_code` after a timeout or security review. Have a fallback ready: `terminal` for commands, `read_file` for file contents, `search_files` for grep, manual JSON parsing in `terminal` with `python3 -c` (but expect similar scrutiny). See pitfall note.

6. **Subagent tool failures.** When delegating URL verification, set explicit fallback to `curl -I` + `curl` + grep when `web_extract` is unavailable. Cite the bot-block status (`HTTP 403 Cloudflare`) so the user knows the gap.

7. **Don't conflate Brave variants.** "Brave Origin" is NOT a wrapper for "Brave Stable". It's a separate `.deb` package (`brave-origin`) from the official Brave APT repo. The `/usr/bin/brave-origin` script is the standard Chromium wrapper pattern (Copyright "Chromium Authors", exports `CHROME_WRAPPER`, ends in `exec -a "$HERE/brave"`). Verify with `dpkg -S`, `file -L`, `sha256sum` before assuming variant relationships.

8. **Perplexity fake-extension campaign is real.** Officially published Chrome Web Store extension ID is `hlgbcneanomplepojfcnclggenpcoldo`. Verify against the canonical URL. User-installed forks with similar names ("Complexity | Perplexity AI Supercharged") have different IDs and different permission profiles.

## Reusable knowledge files in `references/`

- `chromium-wrapper-pattern.md` — how to recognize and analyze standard Chromium launcher wrappers (bash, ~80 lines, "Chromium Authors" copyright header)
- `phantom-urls-known-patterns.md` — known 404 paths and their working alternatives
- `psutil-flatpak-process-tree.md` — battle-tested pattern for matching browser processes inside `bwrap` containers
- `cdp-websocket-vs-urlopen.md` — why CDP measurement needs WebSocket, not HTTP, and what to ship in requirements.txt

## Templates in `templates/`

- `collector-bundle-tree.md` — file tree skeleton + minimum viable structure for a new comparison project

## Success criteria

A run is complete when:
- Every numerical cell in `final-comparison-table.md` carries a status label (VERIFIED_TARGET_EVIDENCE / UNVERIFIED / FAILED)
- Sandbox-test outputs are clearly separated from target-host outputs
- Every UNVERIFIED cell has a note explaining what gate would close it
- Gate report is up to date with explicit user approvals
- All output JSON has schema validation + SHA-256
- The user can re-run the collector bundle and get matching numbers (or knows exactly what changed)
