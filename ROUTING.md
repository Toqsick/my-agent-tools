# ROUTING — how an agent finds the right skill

This repo is built so that **any** LLM agent — even one that does not have the `agent-toolkit` plugin
installed — can route itself to the right skill by reading a single file over a GitHub MCP server. Set
up the MCP once; everyone knows where, how, and what to find.

## The one thing to configure

Point a GitHub MCP server at **`Toqsick/my-agent-tools`** (this repo already ships that server
declaration in [`plugins/agent-toolkit/.mcp.json`](plugins/agent-toolkit/.mcp.json); the token stays an
`${GITHUB_PERSONAL_ACCESS_TOKEN}` env reference, never a literal). That is the whole setup.

## The routing loop (what an agent does)

1. **Fetch [`INDEX.json`](INDEX.json)** in one MCP call. It is the machine-readable source of truth:
   `{schemaVersion, generated_at, counts, tag_vocabulary, categories, skills[], agents[], workflows[]}`.
2. **Match** the task against each skill record using the algorithm below (`triggers[]`, `tags[]`,
   `category`, and `name`/`description` words).
3. **Rank** by match score and pick the top skill (or a small set for multi-domain tasks).
4. **Fetch the skill body** at its `path` (e.g. `library/cybersecurity/…/SKILL.md`) in one more MCP
   call, then follow it. If the skill is `tier: "installed"`, it is also directly invocable in-session
   as its `namespace` (e.g. `agent-toolkit:superpowers-writing-plans`) — no fetch needed.
5. **Multi-step work:** consult `workflows[]` first; a workflow names the ordered phases, the owner
   agent per phase, the skills each phase uses, and the exit criteria. Fetch the workflow's `path` for
   the full pattern.

## Two tiers

| Tier | Where | Loaded? | How to use |
|---|---|---|---|
| `installed` | `plugins/agent-toolkit/skills/` | Yes — in every Claude Code session with the plugin enabled | Invoke by `namespace` (`agent-toolkit:<id>`) |
| `library` | `library/<category>/…` | No — browsable reference only | Fetch by `path` via the MCP when the index points you there |

The split exists on purpose: ~1,400 skills would bloat every session's skill-matcher if all were
loaded. Installed = the curated fast-path; library = the comprehensive arsenal, pulled on demand.

## Match algorithm (deterministic — modeled on the Yuno routing table)

1. **Word-boundary match.** A trigger matches only as a whole word, not a substring — regex
   `\b{trigger}\b` with `IGNORECASE`. (`"api"` matches `"design the api"`, not `"rapidly"`.)
2. **Score = number of distinct triggers/tags matched.** More matches → higher rank.
3. **Category / domain boost.** If the task names a category present in `categories[]`
   (e.g. "cybersecurity", "software-development"), skills in that category get +1.
4. **Verifier/gate priority.** If the task contains a gate word
   (`audit`, `verify`, `validate`, `check this`, `is this done`, `review`, `qa`, `gate`), prefer the
   `security-auditor`/`zc-gate` agents and verification skills *before* raw score — a review request
   should route to a reviewer, not the thing being reviewed.
5. **Multi-domain detection.** Two or more strong matches from different `category` values → treat as a
   decomposition task and hand to a workflow (`multi-agent-master`) rather than a single skill.
6. **Multi-word trigger fallback.** If an exact multi-word trigger phrase does not match, split it into
   content words > 2 chars (drop stop-words `the a an is me of to`) and require all to word-match.
7. **No match → do not force one.** Chitchat or out-of-scope tasks route to nothing; answer directly.

```python
# reference ranking (mirror of the Yuno personas.py sort)
gate_words = {"verify", "audit", "validate", "check this", "is this done", "review", "qa", "gate"}
task_l = task.lower()

def score(skill):
    hits = sum(1 for t in skill["triggers"] + skill["tags"]
               if re.search(r"\b" + re.escape(t) + r"\b", task_l))
    if skill.get("category") and re.search(r"\b" + re.escape(skill["category"]) + r"\b", task_l):
        hits += 1
    return hits

gate = any(w in task_l for w in gate_words)
ranked = sorted(index["skills"], key=lambda s: (
    0 if (gate and s["category"] in {"cybersecurity", "verification"}) else 1,
    -score(s),
))
best = [s for s in ranked if score(s) > 0][:5]
```

## Keeping the index correct

`INDEX.json` and [`NAVIGATION.md`](NAVIGATION.md) are **generated** — never hand-edit them. After adding
or changing any skill/agent/workflow:

```bash
python3 scripts/build_index.py
```

It rescans both tiers, normalizes the (very inconsistent) frontmatter into uniform records, and rewrites
both files. `generated_at` is taken from the git HEAD commit time, so a re-run on an unchanged tree is a
no-op diff.
