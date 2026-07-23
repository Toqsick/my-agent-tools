# Zep Cloud API Quirks Reference

> Collects Zep Cloud-specific behavior patterns discovered during Sim09 (Skill-Chaining) runs. Covers the deployed Zep Cloud backend (not the local MiniMax backend).

## Backend Architecture

The Zep Cloud deployment uses **Zep's Cloud API** for graph storage, vector search, and entity/edge management, with a local Python backend as middleware:

```
Local Backend → Zep Cloud API (api.zep.com) → Zep GraphRAG → Vector DB
```

This is a different architecture from the local MiniMax backend, which runs everything in-process.

## API Endpoints (Zep Cloud Deployment)

| Method | Endpoint | Purpose | Zep Specifics |
|---|---|---|---|
| POST | `/api/graph/project` | Upload ontology+files as multipart | 56.7s typical, returns project_id |
| POST | `/api/graph/build` | Build knowledge graph | Has `force=true` (destructive) |
| GET | `/api/graph/project/list` | List all projects | 8 projects typical after 3 runs |
| POST | `/api/simulation/create` | Create simulation | Body: `{"project_id","graph_id","enable_twitter":true,"enable_reddit":false}` |
| POST | `/api/simulation/prepare` | Generate personas + config | Task-based, ~3-5 min on M3 |
| POST | `/api/simulation/prepare/status` | Check prepare progress | Returns `progress%`, `message`, stage info |
| POST | `/api/simulation/start` | Start the run | Body: `{"simulation_id","platform":"twitter","max_rounds":N}` |
| GET | `/api/simulation/<id>` | **STALE** — only `runner_status` is live | See pitfall 21 |
| GET | `/api/graph/<graph_id>/entities` | List graph entities | Works post-build |

## File Upload Behavior

**Upload time:** 56.7s for a 21 KB seed file (Sim09 Run A). The Zep cloud processes the file (chunking, entity extraction) server-side.

**State verification after upload:**
```bash
# Check project has files attached
curl -s http://localhost:5001/api/graph/project/list | python3 -m json.tool
# Expected: project shows in list with correct file count
```

**Large file handling:** Files up to 21 KB work reliably. Larger files (>100 KB) may hit timeout or memory issues.

## Graph Build Duration

**With rate limiting (Free Tier):**
| Run | Chunks | Duration | Notes |
|---|---|---|---|
| Run A (first build) | 119 chunks | ~26 min | Hit rate limit at 70%, paused 7 min |
| Run A (force rebuild) | 119 chunks | ~16 min | Zep quota already recovering |

**Without rate limiting:** Expect 5-8 min for ~60 chunks, 8-12 min for ~119 chunks.

## OASIS Worker Lifecycle

**PID persistence:** The OASIS worker (Python subprocess) survives backend restarts thanks to `start_new_session=True`. After killing the Flask backend, the worker keeps running as an orphaned process.

**Worker state flags:**
| Flag | Meaning | Example |
|---|---|---|
| `R<sl` | Running, multi-threaded, low-latency | Expected state during active sim |
| `S` | Sleeping (idle) | Between rounds |
| `D` | Uninterruptible sleep | Waiting for LLM response |

**Detection:**
```bash
# Check if simulation worker is alive
ps -p $WORKER_PID -o pid,stat,etime,cmd

# Real-time progress check
grep -oE "\[Day [0-9]+, [0-9:]+\] Round [0-9]+/[0-9]+ \([0-9.]+%\)" \
  backend/uploads/simulations/$SIM_ID/simulation.log | tail -1
```

## DB Growth Patterns (Health Indicator)

**Twitter-only simulation (10 personas, 60 rounds):**
| Time after start | DB size | Actions | Round (approx) |
|---|---|---|---|
| 0 min | ~61 KB (from prepare) | 0 | 0/60 |
| 2 min | ~200 KB | ~3-5 | ~3/60 |
| 5 min | ~330 KB | ~12-15 | ~15/60 |
| 7 min | ~400 KB | ~17 | ~20/60 |
| 10 min | ~600 KB | ~25 | ~25-30/60 |
| 30 min (estimate) | ~2-3 MB | ~100+ | ~60/60 |

**Growth rate:** ~30-60 KB per minute during active rounds. A frozen DB size for 5+ minutes (with the worker still running) indicates a stuck round (usually an LLM call that's taking unusually long).

## Simulation State Machine

```
created → preparing → ready → running → completed
                                              ↓
                                         (report generates)
```

**State transitions from disk observation:**
1. **created**: After `POST /api/simulation/create`
2. **preparing**: After `POST /api/simulation/prepare` (3-5 min, LLM generates 10 profiles + config + initial posts)
3. **ready**: Prepare complete, waiting for start
4. **running**: After `POST /api/simulation/start` — OASIS worker spawns, DB initializes
5. **completed**: Worker exits after `max_rounds` reached

## Zep Cloud vs Local Backend Differences

| Aspect | Local MiniMax Backend | Zep Cloud Backend |
|---|---|---|
| Graph storage | In-process SQLite | Zep Cloud API |
| Rate limiting | None | 300 req/day (Free Tier) |
| run-status accuracy | `run_state.json` is truth | API endpoint is stale; `simulation.log` is truth |
| Entity limits | None | Max 10 entity types, 10 edge types |
| Force rebuild | `reset=true` (safe) | `force=true` (destructive, creates new graph_id) |
| Upload endpoint | `/api/graph/ontology/generate` | `/api/graph/project` (multipart) |
| File processing | Local LLM | Zep server-side + LLM |
| Prepare time | ~3-5 min | ~3-5 min (same via M3) |

## Quota Budget for Simulation Campaigns

Given Zep Free Tier limit of 300 req/day:

| Activity | Requests consumed | % of daily quota |
|---|---|---|
| 1 ontology upload | ~1 | 0.3% |
| 1 graph build (119 chunks) | ~119 | 40% |
| 1 simulation lifecycle (create+prepare+start+monitor) | ~30 | 10% |
| **1 full run (upload+build+sim)** | ~150 | **50%** |
| **2 full runs (back-to-back)** | ~300 | **100%** ⚠️ |

To stay within quota for multi-run campaigns (e.g., 3-run A/B/C comparison):
- Run simulations **sequentially** (not parallel)
- Allow 7+ min between builds for quota recovery
- Use smaller seeds (6-10k chars) to reduce chunk count
- Consider a staged approach: build all 3 graphs in separate sessions over 3 days