# Completed Simulation — Post Extraction & Analysis

> Reference for extracting and analyzing simulation data after worker crash/completion.
> Based on Sim09 Run A (Fresh) — 29 posts from ~8 min runtime.

## When to Use This

After a simulation crashes (OASIS worker dead, backend may be dead too) or officially completes, and the user says "wenn die sim nicht mehr läuft darfst du lesen" — extract all data from the SQLite databases for analysis.

## Extraction Script

```python
import sqlite3, json
from datetime import datetime

SIM_ID = "sim_xxx"  # replace
BASE = f"/home/bratan/10-Projekte/20-experimental/MiroFish/backend/uploads/simulations/{SIM_ID}"

# Twitter posts
c = sqlite3.connect(f"{BASE}/twitter_simulation.db")
cur = c.cursor()
cur.execute("SELECT post_id, user_id, content, num_likes, num_dislikes, num_shares, num_reports, created_at FROM post ORDER BY post_id")
twitter_posts = [{
    'post_id': r[0], 'user_id': r[1], 'content': r[2],
    'num_likes': r[3], 'num_dislikes': r[4], 'num_shares': r[5],
    'num_reports': r[6], 'created_at': r[7]
} for r in cur.fetchall()]

# Reddit posts (if present)
try:
    c2 = sqlite3.connect(f"{BASE}/reddit_simulation.db")
    cur2 = c2.cursor()
    cur2.execute("PRAGMA table_info(post)")
    cols = [r[1] for r in cur2.fetchall()]
    print("Reddit post columns:", cols)
    cur2.execute(f"SELECT * FROM post ORDER BY post_id")
    reddit_posts = [dict(zip(cols, r)) for r in cur2.fetchall()]
except Exception as e:
    print(f"No Reddit DB or error: {e}")
    reddit_posts = []

# Save backup
output = {
    'sim_id': SIM_ID,
    'backup_at': datetime.utcnow().isoformat(),
    'twitter': {'count': len(twitter_posts), 'posts': twitter_posts},
    'reddit': {'count': len(reddit_posts), 'posts': reddit_posts},
}
with open('/tmp/sim-extracted-posts.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Extracted: {len(twitter_posts)} Twitter + {len(reddit_posts)} Reddit posts")
```

## Analysis Template

After extraction, write a findings document with:

1. **Summary table** — Total posts per platform
2. **Top-N analysis** — Most substantive posts with author, content snippet, engagement
3. **Persona mapping** — Which user_id maps to which persona role
4. **Cluster identification** — Group posts into 3-6 clusters (themes)
5. **Surprising/divergent content** — Posts that disagree or surface unexpected positions
6. **Data gaps** — What questions weren't addressed (for next run)

## Run A Example

From a Fresh run (no skill constraints, parallel mode, 8 min runtime before crash):

- **Twitter**: 22 posts, 8 unique users (all 8 personas active)
- **Reddit**: 7 posts (same personas, same topics, no new findings)
- **Top content**: Personas discussed 6-core-skeleton bias, Jaccard-overlap validation, hidden weight drift from NeurIPS 2025 paper, and setup-cost vs drift-cost trade-off
- **Data quality**: Sufficient for analytical purposes despite early crash