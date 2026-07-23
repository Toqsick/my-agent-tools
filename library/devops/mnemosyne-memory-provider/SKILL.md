---

name: mnemosyne-memory-provider
description: |
  Use when configuring Mnemosyne as the native memory provider for Hermes Agent, switching from another memory backend, or troubleshooting Mnemosyne-backed memory in a Hermes profile.
  NOT for using Mnemosyne standalone (not as a Hermes provider) or configuring a non-Hermes memory backend.
  Configure Mnemosyne as Hermes Agent's native memory provider.
version: 1.3.0
author: Yuno (Basti's assistant)
platforms:
- linux
- macos
tags:
- hermes
- memory
- mnemosyne
- embeddings
- fastembed
- sqlite
- vector-search
lane: worker-heavy
reasoning_effort: xhigh
license: MIT
trigger_keywords: ['memory', 'hermes', 'mnemosyne', 'provider', 'configuring']
keywords: ['memory', 'hermes', 'mnemosyne', 'provider', 'configuring']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-memory', 'local-ai-security-hygiene']
---
# Mnemosyne Memory Provider

Hermes Agent's native local memory backend (`provider: mnemosyne` in config.yaml). Covers embedding generation, vector search setup, consolidation, and troubleshooting.

## Quick Reference

| Task | Command |
|------|---------|
| Check status | `mnemosyne_stats` |
| Consolidate | `mnemosyne_sleep(all_sessions=True)` |
| Recall | `mnemosyne_recall(query, top_k=5)` |
| DB path | `~/.hermes/mnemosyne/data/mnemosyne.db` |
| Config | `~/.hermes/config.yaml` → `provider: mnemosyne` |

## Architecture

```
~/.hermes/mnemosyne/
├── data/
│   ├── mnemosyne.db          # Haupt-DB (working_memory, episodic_memory, facts, memory_embeddings)
│   ├── mnemosyne.db-wal      # WAL journal
│   └── triples.db            # Knowledge Graph
└── mnemosyne.db              # Symlink oder Backup

~/.hermes/config.yaml
└── provider: mnemosyne
    user_char_limit: 4094
    user_profile_enabled: true
    write_approval: true/false
```

### Key Tables (live counts as of 2026-07-10; always re-verify — counts drift)

| Table | Purpose | Typical live size |
|-------|---------|-------------------|
| `working_memory` | Rohe Session-Memories (BEAM soft-delete via `valid_until` + `superseded_by`) | 2.000–3.500 |
| `episodic_memory` | Konsolidierte Zusammenfassungen (Tier 1/2/3 via `tier` column) | 400–500 |
| `memoria_facts` | Strukturierte Fakten (fact_type: metric/date/sequence/version) | 2.500–3.000 |
| `memoria_instructions` | Verhaltensanker | 50–300 |
| `memoria_preferences` | Benutzerpräferenzen | 50–100 |
| `memoria_kg` | Knowledge-Graph (subject/predicate/object, separate from `triples`) | 20–50 |
| `triples` | Strukturiertes Wissens-Graph (subject/predicate/object, valid_from/valid_until) | 30–100 |
| `graph_edges` | Untyped edges (source/target/edge_type/weight) | 50–150 |
| `scratchpad` | Freitext-Workspace pro Session (id, content, session_id) | 1–10 (oft stale) |
| `memory_embeddings` | Vektor-Speicher (bge-small-en-v1.5, 384 dim, JSON float arrays) | ≤ working count |
| `vec_episodes_*` | ANN-Vektor-Index (vec0 Extension, int8[384]) | 0–400, optional |
| `fts_working_data` / `fts_episodes_data` | Full-Text Search Indizes (FTS5) | implicit, parallel zu Tabellen |
| `memories` (SQLite root) | **Nicht** der Working-Memory! Nur ~4–10 Einträge typisch | 4–10 |

**Counts sind nicht statisch.** Vor jeder Audit-Aussage Counts frisch aus der DB ziehen — `SELECT COUNT(*) FROM <table>` oder via `mnemosyne stats`.

## Embedding Engine Setup

### Problem: `available: False`

Mnemosyne's Embedding Engine requires `fastembed` for local embeddings. Without it, no embeddings are generated and `mnemosyne_recall` falls back to FTS5 only.

### Fix: Install fastembed

```bash
uv pip install fastembed --python ~/.hermes/hermes-agent/venv/bin/python
```

After install, verify:
```python
from mnemosyne.core import embeddings
assert embeddings.available() == True
```

### Generate Missing Embeddings

When `memory_embeddings` has gaps (e.g., 127/659 working memories have embeddings):

```python
import sqlite3, json, numpy as np
from fastembed import TextEmbedding

embedder = TextEmbedding('BAAI/bge-small-en-v1.5')

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.floating,)):
            return round(float(obj), 6)
        return super().default(obj)

db = sqlite3.connect('/home/bratan/.hermes/mnemosyne/data/mnemosyne.db')
cur = db.cursor()

# Find working_memory rows without embeddings
cur.execute("""
    SELECT wm.id, wm.content 
    FROM working_memory wm
    LEFT JOIN memory_embeddings me ON wm.id = me.memory_id
    WHERE me.memory_id IS NULL AND wm.content IS NOT NULL
""")

for mem_id, content in cur.fetchall():
    vec = list(embedder.embed(content[:500]))[0]
    vec_json = json.dumps(vec.tolist(), cls=NpEncoder)
    cur.execute(
        "INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding_json, model) VALUES (?, ?, ?)",
        (mem_id, vec_json, 'BAAI/bge-small-en-v1.5')
    )

db.commit()
```

**⚠️ Pitfall:** `numpy.float32` is not JSON-serializable. Always use `json.dumps(vec.tolist(), cls=NpEncoder)` or convert to Python floats manually.

**Performance:** ~70 embeddings/second. 659 memories take ~10 seconds.

## Vector Search (vec0 Extension)

### Setup

The `vec0` virtual tables require the sqlite-vec extension. It may exist in the uv cache but not be loadable directly:

```python
import sqlite3
db = sqlite3.connect('/home/bratan/.hermes/mnemosyne/data/mnemosyne.db')
db.enable_load_extension(True)
db.load_extension('/home/bratan/.cache/uv/archive-v0/KPdxUjNCRk5M-gly/sqlite_vec/vec0.so')
```

### vec0 Schema

```sql
CREATE VIRTUAL TABLE vec_episodes USING vec0(embedding int8[384]);
```

**⚠️ vec0 requires `int8` quantized vectors, not float32.** The `memory_embeddings` table stores JSON float arrays for portability. The `vec_*` tables are optional ANN indices for performance.

### Current State After Fix

| Metric | Before | After |
|--------|--------|-------|
| `memory_embeddings` total | 127 | 886 |
| Working with embedding | 0 | 659 |
| Episodic with embedding | 0 | 100 |
| `embeddings.available()` | False | True |
| `mnemosyne_stats.vectors` | 0 | 100 |

## Consolidation Workflow

### What It Does

`mnemosyne_sleep` consolidates unconsolidated working memories into episodic summaries:
- Groups related working memories
- Creates `episodic_memory` entries (summaries)
- Updates `memory_embeddings` for new summaries
- Tracks consolidation in `consolidation_log`

### Run Consolidation

```python
from hermes_tools import mnemosyne_sleep
result = mnemosyne_sleep(all_sessions=True)
# Returns: {"status": "consolidated", "items_consolidated": N, "summaries_created": M}
```

### Stats After Consolidation

```python
from hermes_tools import mnemosyne_stats
stats = mnemosyne_stats()
# working.consolidated: 609/660
# episodic.total: 100
# episodic.vectors: 100
```

## Troubleshooting

### `vectors: 0` in stats

**Cause:** `fastembed` not installed or `available()` returns False.
**Fix:** Install fastembed (see above), then regenerate embeddings.

### Mnemosyne API: trust_tier statt veracity

Die Mnemosyne `remember()`-API nutzt **`trust_tier`**, NICHT `veracity`. Das `hermes_tools.mnemosyne_remember()`-Interface hat andere Parameter.

**Korrekte Parameter für `mnemosyne.remember()` (direct import):**
```
content: str, source: str = 'conversation', importance: float = 0.5,
metadata: Dict = None, scope: str = 'session', valid_until: str = None,
extract_entities: bool = False, extract: bool = False,
bank: str = None, trust_tier: str = None
```

**Korrekte Parameter für `mnemosyne.recall()` (direct import):**
```
query: str, top_k: int = 5, *, from_date, to_date, source, topic,
temporal_weight, vec_weight, fts_weight, importance_weight, bank
```

### API Auto-Detection Pattern

Der `hermes-orchestration` Skill verwendet `inspect.signature()` um automatisch zwischen `mnemosyne.remember()` (top_k), `hermes_tools.mnemosyne_remember()` (limit), und Plugin-Varianten zu unterscheiden:

```python
import inspect
params = inspect.signature(remember_fn).parameters
kwargs = {"top_k": 3} if "top_k" in params else {"limit": 3}
results = remember_fn(query=query, **kwargs)
```

Immer drei Fallback-Stufen probieren: (1) `mnemosyne_hermes` → (2) `hermes_tools` → (3) direktes `mnemosyne`.

**Cause:** Direct `json.dumps()` on numpy arrays.
**Fix:** Use custom `NpEncoder` or `vec.tolist()` with float conversion.

### `no such module: vec0`

**Cause:** sqlite-vec extension not found or not loaded.
**Fix:** Load from uv cache path explicitly (see Vector Search section).

### `database is locked`

**Cause:** Multiple processes accessing the DB (e.g., Hermes agent + manual script).
**Fix:** Close other processes or use WAL mode (already enabled).

### Embeddings exist but recall doesn't use them

**Cause:** `mnemosyne_recall` needs `vec_weight` parameter to use vector search.
**Fix:** Call `mnemosyne_recall(query, vec_weight=0.5, fts_weight=0.5)` for hybrid search.

### `TypeError: unexpected keyword argument 'veracity'` / `'limit'`

**Cause:** Three different import paths exist (`mnemosyne`, `hermes_tools`,
`mnemosyne_hermes`) and each has a **different signature**:
- Direct `mnemosyne.remember` uses `trust_tier`, not `veracity`
- Direct `mnemosyne.recall` uses `top_k`, not `limit`
- `hermes_tools.mnemosyne_*` wrappers use `veracity` / `limit`

**Fix:** Auto-detect kwargs via `inspect.signature()` before calling. Full
pattern with auto-detection helpers: see `references/api-signature.md`.

### ISO-text dates in created_at — NOT unixepoch

**`created_at` in `working_memory`, `episodic_memory`, `consolidation_log` and `memory_embeddings` is ISO-8601 TEXT** (e.g. `'2026-07-11 18:23:00'`), NOT a unixepoch integer. The `degraded_at` column in `episodic_memory` is also ISO-text.

```sql
-- WRONG: returns NULL
SELECT datetime(created_at, 'unixepoch') FROM working_memory LIMIT 5;

-- RIGHT: substr for date parts
SELECT substr(created_at,1,10) AS date_only FROM working_memory LIMIT 5;

-- RIGHT: comparison with ISO string
SELECT * FROM working_memory WHERE created_at >= '2026-07-08';

-- RIGHT: date arithmetic via string comparison
SELECT substr(created_at,1,10) AS tag, COUNT(*)
FROM working_memory
WHERE substr(created_at,1,10) BETWEEN '2026-07-08' AND '2026-07-11'
GROUP BY tag;
```

**Pitfall:** `datetime(created_at, 'unixepoch')` runs without error but returns NULL for all rows — silently empty, not an error message. When in doubt, run `SELECT typeof(created_at) FROM table LIMIT 1;` before doing datetime math.

**Workaround for date math:** Use `substr(created_at,1,10)` for day-level or direct ISO string comparison for range queries. Mnemosyne stores `created_at` in local time (not UTC), so `date('now')` comparisons are approximate — use `substr(created_at,1,10) >= '2026-07-08'` for explicit date windows instead.

### Stable content-hash for dedup trackers

`hash(content)` returns a different value on every Python run
(`PYTHONHASHSEED` randomization). Using it as a dedup ID means cron jobs
re-import the same content every time.

**Fix:** Use `hashlib.md5(content.encode("utf-8")).hexdigest()[:16]`.

### See Also

- `hermes-agent` skill: Memory provider configuration
- `system-documentation` skill: System state documentation
- Mnemosyne source: `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/mnemosyne/`
- `references/api-signature.md` — Full signature differences, auto-detect helpers, kwarg-name table
- `references/mnemosyne-readonly-audit.md` — Read-only audit recipe: SQLite queries, recall smoke-test, importance-histogram, contradiction-finding (2026-07-10)
- `references/beam-working-cleanup.md` — Bulk Working-Memory Cleanup Procedure (2026-07-05)

```yaml
# ~/.hermes/config.yaml
provider: mnemosyne
user_char_limit: 4094
user_profile_enabled: true
write_approval: true  # Set to false for auto-write without confirmation
```

**Note:** `write_approval: true` requires user confirmation for every memory write via the `memory` tool. Set to `false` for normal operation.

## Memory Hygiene: Was NICHT in Mnemosyne speichern (2026-06-30)

Mnemosyne hat `write_approval: false` als Default für normale Sessions. Trotzdem landen manche Memory-Schreibe in der Working-Memory-Tabelle die dort nichts verloren haben. Die wichtigsten Anti-Patterns aus 2026-06-30:

### Background-Process-Quittungen NICHT speichern

**Schlecht:** `[IMPORTANT: Background process proc_X terminated normally (exit 0). Command: timeout 15 curl ... Output: ...bash: IOCTL...FIN]` als `[USER]`-Message → Mnemosyne persistiert das als Working-Memory Eintrag (importance 0.30). Nach 9 SSE-Test-Quittungen sind das 18 Memories (9 vom User + 9 von meinen Antwort-Memos), Recalls werden vom Lärm dominiert.

**Workaround:** Solche Quittungen gar nicht erst mit `mnemosyne_remember` bestätigen — schweigend quittieren (kurze Acknowledge im User-Facing Output, nicht in Memory persistieren). Wenn doch passiert, siehe Cleanup-Pattern unten.

**Wenn's schon passiert ist (Cleanup-Pattern):**
```python
# 1. Konsolidiert: 1 hoher-importance Memory, fasst die Episode zusammen
mnemosyne_remember(
    content="Session 2026-06-30 — N Background-Process-Quittungen mit Bash-IOCTL-Diagnose. Ursprüngliche proc-IDs: [list]. Lesson: System-Receipts sind ephemeral.",
    importance=0.4, source='insight', scope='session', veracity='tool'
)

# 2. Alle Quittungs-Originale + dazu gehörige Antwort-Memos chainen
for old_id in [list_of_proc_quittance_memory_ids]:
    mnemosyne_invalidate(memory_id=old_id, replacement_id='<neue_id>')

# 3. Eigene Antwort-Memos ("passt alles, Exit 0") ebenfalls invalidieren
```

### Auch nicht speichern

| Quitting-Type | Warum nicht | Stattdessen |
|---|---|---|
| `[IMPORTANT: Background process X completed]` | Ephemeraler Diagnose-Lärm | Schweigen oder 1-Satz-Ack im Output |
| "Alles ok, Sigterm sauber durchgegangen"-Bestätigungen | Repetitive noise | Nur persistieren wenn neue Erkenntnis |
| Memory-Probe-Logs aus AutoConsolidation | Internal state | Mnemosyne-Stats hat das schon |
| "Permission to commit granted" Receipts | User-Memo nicht nötig | git output gibt Antwort |

### Mnemosyne-API-Wahl: invalidate vs forget

- `mnemosyne_invalidate(memory_id, replacement_id=...)` — setzt `valid_until` + chain via `superseded_by`. Andere Memories die drauf verwiesen haben werden redirected. **Wenn** der Fakt noch bedingt relevant ist (z.B. "war falsch, neuer Fakt ist X").
- `mnemosyne_forget(memory_id)` — hard delete. **Wenn** der Fakt komplett unwichtig ist und keinen Replacement hat.

Default im Cleanup: `invalidate` mit `replacement_id` zur Konsolidierungs-Memory. So bleibt die Recall-Chain konsistent.

## § Mnemosyne Direct Recall in Dashboard Backends (2026-07-08)

For data-provider backends that need memory recall (e.g. `server.py` for live dashboards), use **direct import** instead of `hermes recall` CLI — it's faster, structured, and doesn't suffer from ENV-path issues.

### Import Pattern

```python
import sys
# Mnemosyne lives in Hermes venv; add it to path
HERMES_VENV = "/home/bratan/.hermes/hermes-agent/venv"
sys.path.insert(0, f"{HERMES_VENV}/lib/python3.11/site-packages")

from mnemosyne.mcp_tools import _handle_recall

def get_memories(query, top_k=5):
    results = _handle_recall(query=query, top_k=top_k)
    # Each result: {content, score, tier, time, memory_type, weight_type, topic, importance}
    return results
```

### What Direct Import Gives You

| Field | Type | Example |
|-------|------|---------|
| `content` | str | Full memory text |
| `score` | float (0-1) | Similarity score |
| `tier` | str | "high" / "mid" / "low" |
| `time` | timestamp | ISO format, allows recency ordering |
| `importance` | float (0-1) | As stored during `remember()` |
| `memory_type` | str | "episodic" / "working" / "fact" |

### When to Use vs `hermes recap` (CLI)

| Criterion | Direct Import (`_handle_recall`) | CLI (`hermes recap`) |
|-----------|----------------------------------|----------------------|
| Speed | ~200ms | ~2-5s (subprocess overhead) |
| Structured output | Dict with score/tier/time | Raw text, needs parsing |
| ENV-dependency | None (same Python process) | Needs HOME + HERMES_HOME |
| Error-handling | Standard try/except | subprocess timeout/exit-code |
| Works in background workers | ✅ | ❌ (steals FDs) |
| Thread-safe | ✅ (read-only) | ⚠️ (DB-lock risk) |

### Pitfalls

- **Import path**: Mnemosyne is installed in Hermes venv. Use `sys.path.insert(0, ...)` before import, or run the server from within the Hermes venv.
- **Function name**: `_handle_recall` starts with underscore — it's technically "private". If it moves between versions, fall back to CLI.
- **Thread safety**: `_handle_recall` is read-only (query only), so it's safe in http.server threads. But if any thread also calls `remember()` (write), use a `threading.Lock`.
- **Version pin**: As of 2026-07-08, `_handle_recall` signature is `(query, top_k=5, *, ...)` — keyword-only args after top_k.

## § Mnemosyne Python MCP API (handle_tool_call)

> **Gelernt 2026-07-17 (Bee F, Task 4):** Die `_handle_*` privaten Funktionen
> sind fragil — Signatur kann sich zwischen Versionen ändern. Die korrekte
> **public API** ist `handle_tool_call(name, arguments)` aus
> `mnemosyne.mcp_tools`.

### Warum handle_tool_call statt _handle_*?

| Aspekt | `_handle_remember()` (privat) | `handle_tool_call()` (public) |
|---|---|---|
| API-Stabilität | Kein Vertrag — Underscore = intern | MCP-Vertrag, Teil des Tool-Dispatchers |
| Versionstolerant | Bei Signatur-Änderung bricht der Import | Router matched gegen `_TOOL_HANDLERS` dict |
| Alle Tools | Nur eine Funktion | Alle 30+ Mnemosyne-Tools über einen Entry-Point |

### Korrekte Import- und Aufruf-Patterns

```python
from mnemosyne.mcp_tools import handle_tool_call

# --- mnemosyne_remember ---
result = handle_tool_call("mnemosyne_remember", {
    "content": "### [2026-07-17] Memory Recall Top-10 Weekly Cron",
    "source": "self-improving",
    "importance": 0.70,
    "metadata": {"tags": ["memory", "cron", "audit-recovery"], "status": "verified"},
})
# Rückgabe: {"status": "stored", "memory_id": "a533c92cc5a946e7", ...}

# --- mnemosyne_get (Pitfall #36 Verify) ---
verify = handle_tool_call("mnemosyne_get", {"memory_id": mid})
# Erfolg:  {"status": "ok", "memory": {id, content, importance, ...}}
# Fehlschlag: {"status": "not_found", "memory_id": mid}

# --- mnemosyne_recall ---
results = handle_tool_call("mnemosyne_recall", {
    "query": "memory cron recall top",
    "limit": 5, "vec_weight": 0.4, "fts_weight": 0.6,
})
# Rückgabe: {"status": "ok", "results": [{content, score, ...}]}

# --- mnemosyne_invalidate ---
handle_tool_call("mnemosyne_invalidate", {
    "memory_id": old_id, "replacement_id": new_id,
})
# Status: "invalidated" oder "ok"

# --- mnemosyne_stats ---
stats = handle_tool_call("mnemosyne_stats", {})
# Liefert Dict mit Tier-Counts, Embedding-Counts, Banks
```

### Pitfall #36 Verification Pattern (vollständig)

Nach jedem `mnemosyne_remember` MUSS ein sofortiger `mnemosyne_get` folgen:

```python
# 1. Remember
result = handle_tool_call("mnemosyne_remember", arguments)
mid = result.get("memory_id")
assert mid, f"Keine ID: {result}"

# 2. Verify (sofort)
verify = handle_tool_call("mnemosyne_get", {"memory_id": mid})
assert verify.get("status") == "ok", \
    f"Pitfall #36: memory_id={mid} nicht persistiert! {verify}"

# 3. Optional: Content-Gegenlesen
mem = verify.get("memory", {})
assert arguments["content"][:50] in mem.get("content", ""), \
    f"Content-Mismatch für {mid}"
```

**Warum das nötig ist (2026-07-17, Welle 1+2):** In einer Session halluzinierten
4 von 4 Subagenten die Memory-ID beim Formatieren ihres Erfolgsreports —
`mnemosyne_remember` wurde nie aufgerufen, die ID war erfunden. Der `get`-Verify
fängt das systemisch.

### Unterschied zu _handle_recall (bisher dokumentiert)

Die bisherige Referenz in § "Mnemosyne Direct Recall" nutzt `_handle_recall`
— eine private Funktion. Für **Produktiv-Code** (Dashboard-Backends, Cron-Skripte,
Health-Checks) ist `handle_tool_call("mnemosyne_recall", ...)` der richtige Weg:

```python
# EMPFOHLEN (public API):
from mnemosyne.mcp_tools import handle_tool_call
results = handle_tool_call("mnemosyne_recall", {"query": q, "limit": 5})

# FUNKTIONIERT AUCH, aber privat:
from mnemosyne.mcp_tools import _handle_recall
results = _handle_recall(query=q, top_k=5)
```

Beide geben ähnliche Dicts zurück, aber `handle_tool_call` ist versionstolerant
und der offizielle Entry-Point.

### Wichtige Tool-Namen

| Tool-Name | Wichtige Arguments | Returns |
|---|---|---|
| `mnemosyne_remember` | content, source, importance, metadata, scope, bank | `{status, memory_id}` |
| `mnemosyne_get` | memory_id | `{status, memory}` oder `{status: not_found}` |
| `mnemosyne_recall` | query, limit, vec_weight, fts_weight | `{status, results}` |
| `mnemosyne_update` | memory_id, content, importance, metadata | `{status}` |
| `mnemosyne_invalidate` | memory_id, replacement_id | `{status}` |
| `mnemosyne_stats` | {} | Vollständige Statistiken |
| `mnemosyne_sleep` | all_sessions (bool) | `{status, items_consolidated}` |
| `mnemosyne_forget` | memory_id | `{status}` |

### Siehe auch

- `self-improving/references/mnemosyne-anchor-hallucination-2026-07-17.md` — Background zu Pitfall #36
- `self-improving/SKILL.md` § Pitfall #36 — Vollständige Beschreibung mit Erkennungs-Markern
- `references/api-signature.md` — Auto-Detection-Pattern für verschiedene Import-Pfade

## § Bulk Working Memory Cleanup (2026-07-05)

**Wann:** Wenn `mnemosyne_stats` viele unconsolidated Working-Memory-Einträge zeigt (z. B. `working.unconsolidated >> 200`), Recalls von tiny-Conversation-Echos dominiert werden, oder du regelmäßige Memory-Hygiene-Cadence fährst (monatlich empfohlen).

### Architektur-Verständnis vorausgesetzt

Mnemosyne hat mehrere Speicherschichten — die wichtigsten für Cleanup:

| Tabelle | Zweck | Typische Größe |
|---------|-------|----------------|
| `working_memory` (BEAM) | Rohe Session-Memories via `mnemosyne_remember()` | 2.000+ Einträge |
| `episodic_memory` | Konsolidierte Zusammenfassungen via `mnemosyne_sleep` | 100-400 Einträge |
| `memoria_facts` | Strukturierte Fakten | 200-300 Einträge |
| `memoria_instructions` | Verhaltensanker | 50-300 Einträge |
| `memoria_preferences` | Benutzerpräferenzen | 10-50 Einträge |
| `consolidation_log` | Audit-Trail der Konsolidierung | ~250 Einträge |
| `memories` (SQLite root) | **Nicht** der Working-Memory! Nur ~4 Einträge typisch | ~4 |

**Wichtig:** Der `memories`-Table (den das `memory`-Tool anspricht) ist NICHT der Working-Memory. Die 2.000+ Einträge leben ausschließlich in der BEAM `working_memory`-Tabelle. `mnemosyne_stats().working.total` berichtet die BEAM-Zahlen, nicht den `memories`-Count. Bei erstem DB-Connect mit `sqlite3` siehst du nur 4 Memories — das ist KEIN Fehler.

### Der BEAM Unterschied: `valid_until` + `superseded_by`

Working-Memory in BEAM hat ein **soft-delete**-Schema statt harter Löschung:

```sql
SELECT id, importance, valid_until, superseded_by FROM working_memory LIMIT 5;
-- valid_until IS NULL → alive
-- valid_until IS NOT NULL → invalidated (soft-deleted, aus Recalls ausgeschlossen)
-- superseded_by = 'mnemosyne:cleanup:<Datum>:tiny-importance-bulk' → bulk-Token
```

**Vorteil:** Kein `DELETE`, kein VACUUM nötig. Vollständig reversibel per `UPDATE SET valid_until=NULL, superseded_by=NULL`.

**Nachteil:** DB-File-Größe ändert sich nicht (Zeilen bleiben). Der Vorteil ist: **Rollback ist immer möglich.**

### Drei-Schicht-Safety-Net

Jeder Bulk-Cleanup besteht aus **drei unabhängigen Sicherungen**:

| Layer | Was | Wo | Reversibilität |
|-------|-----|----|----------------|
| ① DB-Snapshot | `shutil.copy2` der mnemosyne.db | `~/50-System/backups/mnemosyne/mnemosyne-pre-cleanup-<Datum>.db` | Vollständige DB-Wiederherstellung |
| ② Backout-ID-Liste | JSON mit allen 2.000+ IDs + fertigem Rollback-SQL | `cleanup-<Datum>-backout-ids.json` | `UPDATE SET valid_until=NULL, superseded_by=NULL WHERE id IN (...)` |
| ③ Audit-Trail | `consolidation_log`-Eintrag mit Session-ID, Anzahl, Token | `consolidation_log.id = <n>` | Nachvollziehbarkeit |

### Schritt-für-Schritt-Procedure (Code)

Vollständiger, kopierbarer Code pro Schritt — siehe `references/beam-working-cleanup.md`. Die SKILL.md enthält hier die Kurzform:

1. **Snapshot + Kandidaten-IDs exportieren** → `shutil.copy2` der DB + SQL-Query: `SELECT id, importance, content FROM working_memory WHERE valid_until IS NULL AND importance < 0.5 ORDER BY importance ASC` + JSON-Backout-Datei mit Rollback-SQL
2. **Transaktionale Invalidierung** → `BEGIN IMMEDIATE`, 1x Audit in `consolidation_log`, UPDATE in Chunks à 500 IDs, `COMMIT`. **Pitfalls:** `BEGIN IMMEDIATE` statt DEFERRED (WAL-Deadlock), Chunks à 500 IDs, `WHERE importance < 0.5` im UPDATE wiederholen
3. **Verifikation** → `PRAGMA integrity_check`, `mn.beam.get_working_stats()`, Recall-Test, Importance-Verteilung alive vs invalidated
4. **Sleep-Pass** → `mn.beam.sleep(dry_run=False)` → erwartet `no_op` (Memories < 24h alt)

### Nach Cleanup — Sleep-Pass

```python
result = mn.beam.sleep(dry_run=False)
# → {"status": "no_op", "message": "No old working memories to consolidate"}
```

zwischenzeitlich erstellt wurden.

**Zusätzlich: Immer `AND valid_until IS NULL` anfügen.** Der erste Bulk-Cleanup (2026-07-05) hatte diesen Filter nicht — was dazu führte, dass der Cron-Lauf bereits invalidierte IDs erneut einsammelte und einen Count-Mismatch verursachte. Fix: `valid_until IS NULL` in **beide** Queries — den SELECT-Sammler **und** den UPDATE-Invalidator.

### Aggressivere Varianten (nur nach User-Abgleich)

| Variante | Erklärung | Risiko |
|----------|-----------|--------|
| Mid+ Low purge | `importance < 0.7` statt 0.5 | Entfernt auch mid-quality Memories — nur tun wenn Recall aus Episodic+Memoria lebt |
| Full BEAM reset | `DELETE FROM working_memory WHERE valid_until IS NOT NULL` | Physische Löschung — **macht Rollback unmöglich** |
| VACUUM | `VACUUM;` nach DELETE | Schrumpft DB-File — Daten physikalisch weg |

### Wartungs-Cadence

| Intervall | Aktion | Aufwand |
|-----------|--------|---------|
| Monatlich | Tiny-Purge-Pass (< 0.5 → invalidate) | 5 Min |
| Quartalsweise | Mid-Audit (≥ 0.5 < 0.7), ggf. purgen | 20 Min |
| Halbjährlich | Memoria-Instructions + Preferences review | 1 h |

### Anti-Pattern: Identische Memories aus verschiedenen Sessions

Wenn `mnemosyne_remember` bei jedem Session-Start mit denselben Fakten aufgerufen wird (gleicher Inhalt + gleiche importance), entstehen mehrere identische Einträge in `working_memory`. Mnemosyne dedupliziert NICHT automatisch.

**Fix:** Hash-basierte Dedup:
```python
import hashlib
content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
# Vor mnemosyne_remember: prüfen ob content_hash schon in working_memory.content_hash existiert
```

## § Monatlicher Cron Cleanup (Script + Betriebshygiene)

### Architektur

Ein **selbstständiges Bash-Skript** (`scripts/mnemosyne-monthly-cleanup.sh`) das:

| Komponente | Beschreibung |
|---|---|
| 25-Tage-Sperre | `.last-mnemosyne-cleanup`-Datei mit Datum → verhindert Mehrfachausführungen pro Monat |
| Pre-Flight | DB existiert? sqlite3? venv? Sperre gültig? → alles vor erstem Schreibzugriff |
| Layer ① Snapshot | `cp` der DB → `~/50-System/backups/mnemosyne/mnemosyne-pre-cleanup-<Datum>.db` |
| Layer ② Backout | Python sammelt `importance < 0.5 AND valid_until IS NULL` → JSON mit fertigem Rollback-SQL |
| Layer ③ Audit | `BEGIN IMMEDIATE` → `consolidation_log`-Eintrag → Chunked UPDATE (500 IDs) → `COMMIT` |
| Telegram-Report | Lädt Credentials aus `~/.hermes/.env` (NIE im Crontab!) |
| Cron | `0 9 1 * *` → Log nach `~/logs/mnemosyne-monthly-cleanup.log` |

### Idempotenter UPDATE (defensiv, bug-frei getestet)

```sql
UPDATE working_memory
SET valid_until = ?, superseded_by = ?
WHERE id IN (?) AND importance < 0.5 AND valid_until IS NULL
```

Wenn ein Eintrag bereits invalidiert wurde (vorheriger Lauf, manuelle Aktion), wird er nicht erneut angetastet.

### Pitfalls aus erster Ausführung (2026-07-05)

| # | Problem | Symptom | Fix |
|---|---------|---------|-----|
| 1 | `.env`-Variable heisst `TELEGRAM_HOME_CHANNEL`, nicht `TELEGRAM_CHAT_ID` | Telegram-Report nie gesendet | Im Skript tatsächliche Variable aus `.env` verwenden, nicht raten |
| 2 | `WHERE importance < 0.5` ohne `valid_until IS NULL` | Sammelt bereits invalidierte IDs → Count-Mismatch | Immer `AND valid_until IS NULL` an SELECT **und** UPDATE |
| 3 | `BEGIN DEFERRED` statt `BEGIN IMMEDIATE` | WAL-Deadlock bei Hermes-TUI-Lesezugriff | Immer `BEGIN IMMEDIATE` bei Bulk-Schreibzugriffen |
| 4 | Credentials im Crontab hartcodiert | Secret-Leak in `crontab -l` | Niemals Credentials im Crontab; immer aus `.env` laden |

### Manuelle Ausführung

```bash
# Normal (überspringt wenn < 25 Tage seit letztem Lauf)
bash ~/50-System/bin/mnemosyne-monthly-cleanup.sh

# Force (Sperre zurücksetzen)
rm ~/50-System/backups/mnemosyne/.last-mnemosyne-cleanup
bash ~/50-System/bin/mnemosyne-monthly-cleanup.sh

# Logs
tail -f ~/logs/mnemosyne-monthly-cleanup.log
```

### Template-Wiederverwendung

Das Skript in `scripts/mnemosyne-monthly-cleanup.sh` ist als **Vorlage für andere DB-Hygiene-Crons** nutzbar. Anpassungspunkte:

1. `DB_PATH` → Ziel-DB
2. `IMPORTANCE_MAX` → Schwellwert (z. B. `0.7` für Mid-Cleanup)
3. SQL-Inline-Blöcke → andere WHERE-Bedingungen

### Siehe auch

- `scripts/mnemosyne-monthly-cleanup.sh` — ausführbares Template
- `references/beam-working-cleanup.md` — Bulk-Cleanup-Procedure mit Code
- `note-taking/obsidian` — Vault-Operationen (Notes anlegen, Wikilinks)

## § Obsidian-Vault-Sync (Memory-Hygiene-Begleitung)

Basti's Betriebspraxis: **Mnemosyne ist Runtime-Memory, Obsidian ist das persistente menschliche Wissen.** Relevante Erkenntnisse aus Memory-Operationen gehören in beide Systeme — sie bedienen unterschiedliche Lese-Schnittstellen und schaffen gegenseitige Fehlerresilienz.

### Was synchronisieren

| Mnemosyne-Inhalt | Obsidian-Ziel | Timing |
|---|---|---|
| Cleanup-Reports (importance ≥ 0.85) | `07 Archiv/` | Nach jedem Bulk-Cleanup |
| Wartungs-SOPs (Scripts, Cron, Procedures) | `03 Projekte/` oder Skill-Verzeichnis | Einmalig nach Ersteinrichtung |
| Session-übergreifende Kontext-Fakten | `01 Kontext/` | Wenn Fakt stabil und referenzierbar ist |

### Was NICHT synchronisieren

- Working-Memory-Rohdaten (Einzelfakten aus einer Session)
- Temporäre Kontext-Notizen („gerade getestet")
- Low-importance Conversation-Echos (die ja gerade invalidiert wurden)

### Mnemosyne-Triple zur Auffindbarkeit

```python
mnemosyne_triple_add(
    subject="mn-hygiene-sync",
    predicate="dokumentiert-in",
    object="Obsidian Vault/07 Archiv/Mnemosyne Cleanup Report - 2026-07-05.md",
    valid_from="2026-07-05"
)
```

## § Stale Memory Detection + Invalidation Workflow (2026-07-17)

**Wann:** Regelmäßige Memory-Hygiene (z.B. nach einem System-Audit, der
Coverage-Drift in CLAUDE.md / AGENTS.md offenbart hat), oder wenn Recall-Ergebnisse
Behauptungen enthalten die vom Live-System widerlegt werden. Komplementär zur
§ Bulk Working Memory Cleanup (importance-basiert) — hier geht es um
**fact-accuracy**, nicht um importance-threshold.

**Prinzip:** Memory-Einträge können inhaltlich veralten, auch wenn ihre Importance
hoch ist. Eine Memory "ProtonVPN aktiv" mit importance=0.6, die 54x recalled
wurde, ist gefährlicher als eine importance=0.3-Entry, denn sie wird bei
künftigen Recalls dominant ranken und die falsche Antwort liefern.

### 5-Schritt-Workflow

```
Schritt 1: mnemosyne_sleep (Konsolidierung)
  ├── Dry-Run zuerst: mnemosyne_sleep(all_sessions=True, dry_run=True)
  ├── Live: mnemosyne_sleep(all_sessions=True)
  └── Erwartung: 10-30 items_consolidated → 3-8 summaries_created

Schritt 2: Recall nach Themengebieten die von Drift bedroht sind
  ├── mnemosyne_recall(query="<thema>", limit=10)
  ├── Pro Ergebnis: Stimmt die Aussage noch mit dem Live-System überein?
  ├── Kategorien die häufig stale werden:
  │     - Service-States ("X läuft auf Port Y" → verify via systemctl/ss)
  │     - VPN/Network-Setup ("ProtonVPN aktiv" → verify via systemctl/wg)
  │     - Disk-Zahlen ("74% belegt" → verify via df -h)
  │     - Pfad-Existenz ("~/pfad" existiert → verify via ls)
  └── Cross-Check: AGENTS.md / CLAUDE.md Behauptungen vs Live (bekannte Drift-Quellen)

Schritt 3: Stale Memory invalidieren + Replacement schreiben
  ├── mnemosyne_invalidate(memory_id=<stale_id>, replacement_id=<new_id>)
  ├── mnemosyne_remember(content="<korrekte Aussage>", importance=0.7+, ...)
  └── Graph-Link: mnemosyne_graph_link(source=<new>, target=<old>, relationship="supersedes", weight=0.85+)

Schritt 4: sys-* ID Quirk Handling (siehe Troubleshooting unten)
  ├── sys-*-IDs (z.B. sys-tt, sys-llama) sind in memoria_facts-Tabelle
  ├── NICHT erreichbar via mnemosyne_update / mnemos_get / mnemosyne_validate
  └── Workaround: neue Memory mit höherer Importance + korrektem Inhalt anlegen

Schritt 5: Scratchpad-Notiz für nächste Session
  └── mnemosyne_scratchpad_write(content="Memory-Hygiene <Datum>: N invalidated, M replaced, ...")
```

### Wann invalidate vs forget vs update

| Aktion | Wann | Effekt |
|--------|------|--------|
| `mnemosyne_invalidate(memory_id, replacement_id)` | Fakt war richtig aber ist veraltet (z.B. "ProtonVPN aktiv" → jetzt Tailscale) | soft-delete via valid_until + superseded_by-Kette. Recall redirected. |
| `mnemosyne_forget(memory_id)` | Fakt war immer falsch (Hallucination) | hard delete. Kein Replacement. |
| `mnemosyne_update(memory_id, ...)` | Fakt war fast richtig, nur kleine Zahl/Datum korrigieren | In-place Edit. Kein Graph-Link nötig. |
| Neue Memory + invalidate old | sys-* IDs oder komplexe Mehrfach-Korrektur | Höchste Sicherheit, aber dupliziert Eintrag. |

### Graph-Link als Verkettung (wichtig für Recall-Qualität)

Nach jedem invalidate+replace MUSS der Graph-Link gesetzt werden:

```python
mnemosyne_graph_link(
    source_id="<new_memory_id>",
    target_id="<stale_memory_id>",
    relationship="supersedes",
    weight=0.85
)
```

**Warum:** Ohne Graph-Link weiß das Recall-System nicht, dass die neue Memory
die alte ersetzt. Der `superseded_by`-Wert in working_memory wird zwar respektiert,
aber der KG-Edge schafft zusätzliche Connectivity für künftige Recalls.

### Identifikation von Stale-Kandidaten — Heuristiken

| Signal | Beispiel | Verify-Methode |
|--------|----------|----------------|
| Memory erwähnt Service/Port der im Audit als "gone" markiert ist | "TokenTelemetry Port 3000" | `systemctl --user is-active <svc>` + `ss -tlnp \| grep :PORT` |
| Memory enthält absolute Zahlen (Disk%, RAM, Model-Count) | "Disk 74%, 156G free" | `df -h` live vergleichen — > 5% Drift = stale |
| Memory erwähnt Tool/Service der in AGENTS.md als "likely-stale" gelistet ist | "ProtonVPN aktiv" | `systemctl is-enabled <svc>` live checken |
| Memory ist älter als 14 Tage UND handelt von System-State (nicht User-Präferenz) | "System-Check 04.07" | Inhalt gegen Live verifizieren |
| Episodic Memory mit hohem recall_count (> 20) UND alterer als 2 Wochen | "System-Check 04.07" 54x recalled | Höchste Priorität — wird bei künftigen Recalls dominant |

**Wichtig:** User-Präferenzen und Identitäts-Fakten altern NICHT nach Zeit
allein — sie sind erst stale wenn der User sie aktiv korrigiert oder das
zugrundeliegende System sich geändert hat. System-State-Fakten altern durch
System-Veränderung.

### Troubleshooting: sys-* IDs nicht update-bar (2026-07-17)

Einige Legacy-/Seed-Memories haben IDs wie `sys-tt`, `sys-llama`, `sys-<name>`.
Diese liegen in der `memoria_facts`-Tabelle, nicht in `working_memory`.

**Symptom:** `mnemosyne_update(memory_id="sys-tt", ...)` und
`mnemosyne_validate(action="update", memory_id="sys-tt", ...)` und
`mnemosyne_get(memory_id="sys-tt")` geben alle `not_found` / `memory_not_found`,
obwohl `mnemosyne_recall` den Eintrag findet und anzeigt.

**Ursache:** Die `mnemosyne_update` / `mnemosyne_get` / `mnemosyne_validate`
Hermann-Tools operieren auf `working_memory` und `episodic_memory`. Die
`memoria_facts`-Tabelle ist über diese Tools nicht erreichbar (Stand 2026-07-17).

**Workaround:** Leg eine neue Memory mit korrektem Inhalt und höherer Importance
an. Die neue Memory wird bei künftigen Recalls höher ranken als die stale sys-*
Memory. Die alte sys-* Memory bleibt zwar da, wird aber verdrängt. Beispiel:

```python
mnemosyne_remember(
    content="Service-Drift-Korrektur 2026-07-17: TokenTelemetry inaktiv+disabled (sys-tt stale), llama.cpp Server inaktiv (sys-llama stale). Verify: systemctl --user is-active tokentelemetry + ss -tlnp | grep 3000",
    importance=0.7,
    scope="global",
    source="fact",
    veracity="tool"
)
```

### Real-Beispiel (Session 2026-07-17)

Drei stale Memories in einer Hygiene-Session identifiziert und korrigiert:

| Stale ID | Was drin war | Verify-Befund | Aktion |
|---|---|---|---|
| `8eecb0f9fab7037c` | "Syslog-Drift oft self-resolving, 30-60min abwarten" | 3 Vorfälle (16.07, 17.07) widerlegen das | invalidate → `3390948fcec5ef9b` |
| `d6d621d631f349cd` | "System-Check 04.07: ProtonVPN aktiv, Port 3000 world-bound, Disk 74%" | ProtonVPN: service not-found; Port 3000: kein Listener; Disk: 85% | invalidate → `24488e751c48bdf4` |
| `sys-tt`, `sys-llama` | "TokenTelemetry läuft Port 3000", "llama.cpp Server aktiv Port 8332" | Beide inaktiv, Ports nicht belegt | sys-* Quirk → neue Memory `3c3f9f63f312aeb9` |

**Ergebnis:** 17 Working → 4 Episodic konsolidiert, 3 stale invalidated, 3
Replacement-Memories + 2 Graph-Edges gesetzt, Shared Surface clean.

### Siehe auch

- `references/stale-memory-invalidation.md` — Vollständiges Session-Protokoll 2026-07-17
- § Bulk Working Memory Cleanup — importance-basierter Cleanup (diese Sektion hier ist fact-accuracy-basierter Cleanup)
- § Read-only Mnemosyne Audit Recipe — Schritt 6 (Graph-Konsistenz) ist der read-only Einstiegspunkt für diesen Workflow

## § Read-only Mnemosyne Audit Recipe (2026-07-10)

**Wann:** Wenn der User nach „Memory-Stand", „Mnemosyne-Audit", „was weißt du über mich", „warum findet Recall X nicht", oder einem Phasen-Check (Phase 1 / Phase 6 / Memory-Health) fragt — oder als regelmäßiger Quartals-Hygiene-Pass.

**Wichtig:** Read-only. **Keine** `mnemosyne_remember` / `_handle_store` / Cleanup-UPDATE aufrufen. Nur lesen + analysieren. Schreibende Aktionen sind ein separater Folge-Task.

### Was die `mnemosyne` CLI kann — und was NICHT

| CLI-Subcommand | Audit-relevant? | Deckt … |
|----------------|----------------|---------|
| `mnemosyne stats` | ✅ | Tier-Counts, Embedding-Vector-Count, Banks, DB-Path |
| `mnemosyne diagnose` | ✅ | Sanity-Checks (7/25 passed = normal) |
| `mnemosyne recall <q> [top_k]` | ✅ | Recall-Pipeline smoke-test, Score-Spread |
| `mnemosyne backup [dir]` | ✅ | Read-only-Snapshot vor jedem schreibenden Folge-Task |
| `mnemosyne verify [--quick]` | ✅ | DB-Integrität |
| `mnemosyne sleep` | ❌ **WRITE** | NICHT aufrufen im Audit |
| `mnemosyne store / update / delete` | ❌ **WRITE** | dito |
| `mnemosyne import / import-hindsight` | ❌ **WRITE** | dito |
| `mnemosyne bank create/delete` | ❌ **WRITE** | dito |

**Kritische Lücke:** Die CLI hat **kein** Subcommand für `triples`, `graph_edges`, `memoria_facts`, `memoria_preferences`, `memoria_kg`, `scratchpad`. Für diese ist **raw SQLite** zwingend (siehe Reference).

### 6-Schichten-Standard-Audit (eine Reihenfolge, alles read-only)

1. **Stats + Diagnose** → `mnemosyne stats` + `mnemosyne diagnose` (gibt Tier-Counts, Embedding-Count, Sanity-Checks aus)
2. **SQLite-Live-Counts** (für jede Tabelle frisch): `SELECT COUNT(*) FROM working_memory / episodic_memory / memoria_facts / triples / memoria_kg / graph_edges / scratchpad / memoria_preferences`
3. **Importance-Histogramm (working_memory)** → siehe Reference. Liefert sofort das „Noise-Volumen" (% mit imp ≤ 0.30) und den Anteil der hochrelevanten Memories (imp ≥ 0.85). Realistisch: 80–90 % sind Noise.
4. **Konsolidierungs-Health** → Count der `working_memory WHERE consolidated_at IS NULL` + jüngster Sleep + Tier-Wanderung im letzten Sleep-Log (`tail ~/.hermes/logs/mnemosyne-sleep.log`)
5. **Recall-Smoke-Test (4 Queries)** → siehe Reference. Deckt Identity-Frage, User-Vorlieben-Frage, Pattern-Frage, Episoden-Frage ab. Score-Spread zeigt, ob Recall kalibriert ist.
6. **Graph-Konsistenz** → `triples` ↔ `working_memory` cross-check: gibt es Widersprüche? Z.B. ein Triple behauptet Pfad X, working_memory mit imp=0.95 verbietet X.

**Output-Format:** Strukturierte Markdown-Datei unter `/tmp/mnemosyne-audit-<datum>.md` mit den 6 Sektionen + Read-only-Bestätigung am Ende. Nicht in `~/.hermes/` schreiben (gehört User, nicht Audit-Output).

### Pitfalls

- **„Mnemosyne hat 4 Memories" — kein Fehler.** Der `memories`-SQLite-Root-Table hat ~4–10 Einträge; die 2.000+ Working-Memories leben in BEAM `working_memory`. Beim ersten Connect nicht verwirren lassen.
- **`recall` mit Score 0.4 ist nicht „schlecht"** — Vektor-Recall ist nicht 0/1. Score-Spread zwischen Top-Hit und #5 zeigt, ob das Top-Ergebnis wirklich dominant ist. Wenn alle Hits bei 0.35–0.45 kleben, ist die Frage off-topic oder die Embedding-Reichweite zu eng.
- **`superseded_by` ≠ gelöscht.** Einträge mit `valid_until IS NOT NULL` sind soft-deleted, aus Recalls ausgeschlossen, aber physisch noch da. Bei Bulk-Cleanup-Counts muss man immer `AND valid_until IS NULL` mitfiltern (auch dokumentiert in § Bulk Working Memory Cleanup).
- **WAL-Mode aktiv**: `mnemosyne.db-wal` zeigt an, dass jemand schreibt. Vor eigenen Schreib-Aktionen immer `mnemosyne verify` laufen lassen. Read-only-Audit ist trotzdem sicher.
- **Banks ≠ Tables.** `mnemosyne stats` listet `default` und `vault-phase-6` als Banks — das sind logische Partitionen, NICHT 1:1 zu SQLite-Tables. Vault-Phase-6-Bank hat eine eigene `mnemosyne.db` unter `~/.hermes/mnemosyne/data/banks/vault-phase-6/`.

### Siehe auch

- `references/mnemosyne-readonly-audit.md` — Vollständige SQL-Queries, Recall-Smoke-Test-Queries, Importance-Histogramm-Queries, Graph-Cross-Check-Recipes, Session-Output 2026-07-10

## See Also (cross-skill)

- `devops/hermes-maintenance` §13 "Memory-Hygiene: System-Receipts NICHT in Memory"
- `devops/hermes-maintenance` §11.4 — Hermes-CLI bash-background IOCTL-Quirk
- `note-taking/obsidian` — Obsidian Vault-Operationen (Sync zu Mnemosyne beachten)
- `references/beam-working-cleanup.md` — Vollständige Procedure mit Code + Session-Output + Debug-Erkenntnisse
- `scripts/mnemosyne-monthly-cleanup.sh` — Produktions-Cron-Skript (Template für weitere Hygiene-Crons)

### See Also

- `hermes-agent` skill: Memory provider configuration
- `system-documentation` skill: System state documentation
- Mnemosyne source: `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/mnemosyne/`
- `references/api-signature.md` — Full signature differences, auto-detect helpers, kwarg-name table
- `references/cli-parameter-gap.md` — CLI vs Python-API Parameter-Gap: scope/metadata/bank/trust_tier fehlen in `mnemosyne store` und `recall`, Workaround Structured Content Encoding (2026-07-17)
- `references/mnemosyne-readonly-audit.md` — Read-only audit recipe: SQLite queries, recall smoke-test, importance-histogram, contradiction-finding (2026-07-10)
- `references/beam-working-cleanup.md` — Bulk Working-Memory Cleanup Procedure (2026-07-05)
- `scripts/mnemosyne-monthly-cleanup.sh` — Monatliches Cron-Cleanup-Skript
