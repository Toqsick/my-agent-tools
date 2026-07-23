# Cron-Fleet-Audit Run #N+1 — 2026-07-23 16:00 MESZ

**Aufgerufen durch:** `multi-agent-master-workflow-8h` (Schedule `0 0,8,16 * * *`)
**Output gespeichert:** `~/.hermos/cron/output/76039d75e57d/2026-07-23_16-*.md`

## Inventar-Snapshot

- **27 Jobs** total (+2 seit 25 → 2 neue Vault-LLM-Jobs)
- **13 echte LLM-Jobs** (`no_agent=false + provider`)
- **Pinning-Quote:** 6/13 = 46.2% (strukturell, nicht bug-bedingt — siehe 20.5b)
- **Drift-Guard:** 0
- **Silent-OK bestätigt:** 1 (memory-weekly-consolidate)
- **Disabled:** 0

## NEUE Findings

### ① Silent-OK-F2 (CLI-Subcommand-Mismatch)

**Job:** `memory-weekly-consolidate` (`54073f40`)
**Schedule:** `0 4 * * 0` (Sonntag 04:00)
**Last-Run:** 2026-07-19 07:25:50 → `last_status=ok`, **Output sagt `(unavailable)`**

**Script-Inhalt (`~/.hermes/scripts/memory_weekly_consolidate.sh`):**
```bash
sleep_out=$(mnemosyne-sleep --all-sessions 2>&1 | tail -5 || echo "(unavailable)")
STATS=$(mnemosyne-stats 2>/dev/null | head -5 || echo "(unavailable)")
```

**Beweis dass CLI-Syntax falsch ist:**
```bash
$ which mnemosyne-sleep
(not found)

$ /home/bratan/.hermes/hermes-agent/venv/bin/mnemosyne --help
Commands:
  stats    Show statistics
  sleep    Run consolidation
  ...
```

**Auswirkung:** Wochenlang wurde Sonntags-Mnemosyne-Consolidate nicht ausgeführt. Daily-Sleep (`f31e9bc2`, separates `mnemosyne-sleep.sh`) lief weiter — aber weekly consolidation ist effektiv tot.

**Fix:** Script-Zeilen editieren zu:
```bash
sleep_out=$(/home/bratan/.hermes/hermes-agent/venv/bin/mnemosyne sleep 2>&1 | tail -5 || echo "(unavailable)")
STATS=$(/home/bratan/.hermes/hermes-agent/venv/bin/mnemosyne stats 2>/dev/null | head -5 || echo "(unavailable)")
```

**Verifikation:** `bash -x ~/.hermes/scripts/memory_weekly_consolidate.sh` — sollte Stats und Sleep-Output zeigen, **nicht** `(unavailable)`.

### ② Brand-new LLM-Jobs (Smoke-Test Pflicht)

**2 neue Vault-LLM-Jobs heute morgen angelegt** — noch nie live gelaufen:

| ID | Name | Schedule | Erster Trigger |
|---|---|---|---|
| `124fc5d9dec3` | Vault Bridge-Audit (Phase 8) | `0 4 * * *` | 2026-07-24 04:00 |
| `b43ee298534b` | Vault INDEX-Regeneration (Welle 8) | `0 5 * * *` | 2026-07-24 05:00 |

**Referenzierte Scripts (alle existent, validiert 2026-07-23 16:00):**
- `~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/excalidraw-canvas-bridge-audit.py`
- `~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/genuine-broken-links-audit.py`
- `~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/generate-folder-index.py`

**Smoke-Test-Pflicht (vor 24.07. 04:00):**
```bash
python3 ~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/excalidraw-canvas-bridge-audit.py "/home/bratan/Dokumente/Obsidian Vault" 2>&1 | head -30
python3 ~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/generate-folder-index.py "/home/bratan/Dokumente/Obsidian Vault" "01 Kontext" --with-moc-hub "MOC - Kontext" --max-subdir-listing 10 2>&1 | head -30
```

### ③ Bulk-Pinning-Empfehlung (Pinning-Quote 46.2% → 100%)

**Unpinned echte LLM-Jobs (7):**

| ID | Name | Schedule | Trigger |
|---|---|---|---|
| `3b92e310` | yuno-tiktok-evening-reflect | `0 20 * * 1-5` | täglich 20:00 |
| `64a80e7f` | Kimi Token Cup Reminder T-5d | once 2026-07-26 18:00 | in 3 Tagen |
| `8c12538d` | Kimi Token Cup Reminder T-2d | once 2026-07-29 18:00 | in 6 Tagen |
| `61902126` | Kimi Token Cup Reminder T-12h | once 2026-07-31 12:00 | in 8 Tagen |
| `822287c0` | Kimi Token Cup Reminder T-4h | once 2026-07-31 13:59 | in 8 Tagen |
| `8a0eb26e` | Kimi Token Burn Daily Check T-5d | once 2026-07-26 10:00 | in 3 Tagen |
| `1ed9483c` | Kimi Token Burn Phase 3 Start | once 2026-07-28 10:00 | in 5 Tagen |

**Bulk-Pinning-Rezept (siehe §20.5b in SKILL.md):** Eine Python-Schleife über alle 7 + defensiv auch `8605cc06` (24h-audit Provider-Relikt).

## Schedule-Density (DOW × Hour)

| Slot | Anzahl Jobs | Lane |
|---|---|---|
| So 04:00 | 3 | 2 scripts + 1 LLM (Vault Bridge-Audit) |
| Mo-So 08:00 | 3 | 2 LLM (Briefing + Workflow-Audit) + 1 script (24h-audit) |

Alle anderen Slots ≤2 Jobs. **Sonntag 22:00 = 1 Job** (yuno-self-improve-PINNED), entgegen älterer Audits entspannt.

## Lessons Learned v4 (2026-07-23)

- **CLI-Subcommand-Mismatch ist eine eigene Silent-OK-Klasse (F2).** Bisher kannte ich nur F (CWD-relativer Pfad). Mnemosyne-CLI hat ein einzelnes Binary mit Subcommands, nicht separate Binaries. Scripts die `mnemosne-<x>` rufen, scheitern silent.
- **Brand-new LLM-Jobs sind keine Pending-First-Run.** LLM-Jobs müssen vor dem ersten Live-Run dry-getestet werden — der erste echte Run ist der erste Crash-Test, und Crash manifestiert sich hart (Telegram-Spam oder Vault-Writes).
- **Inventory-Growth = strukturelle Pinning-Regression.** Audit-Quoten ohne Delta-Report sind irreführend. Immer Quote-Delta ausweisen.
- **CLI-Lücken-Insight:** `hermes cron create` setzt keinen `provider_snapshot`. Workflow-Lücke: Pinning muss nach jedem Cron-Create manuell/programmatisch erfolgen.

## Cross-Skill-Notiz

Diese Findings sind in SKILL.md §20.5 / §20.5a / §20.5b + die neue Fehler-Klasse F2 in §20.2 dokumentiert. Bei der nächsten Cron-Fleet-Audit-Session diese Reference für den Vergleich mit neuen Runs laden.