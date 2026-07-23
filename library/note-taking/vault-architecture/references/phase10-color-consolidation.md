# Phase 10 — Color Consolidation Worked Example

> **Source:** 2026-07-05 session. Part of the Vault-Phase-10-Plan (research → plan → gate → implementation workflow).
> **Finding:** 16 graph.json colorGroups with 3 RGB-duplication clusters collapsed to ~8 distinct colors.

## Context

During Phase 10 planning research for Basti's Obsidian vault, an audit of `graph.json` revealed that while there were 16 configured `colorGroups`, only **8-9 visually distinct color categories** were actually active. Three RGB-duplication clusters were identified where multiple tag groups shared identical RGB integer values.

## Raw Data

| Tag | Query | RGB (dec) | Color Family |
|-----|-------|-----------|--------------|
| `#daily` | `tag:#daily` | 16638023 | Coral-Orange |
| `#moc` | `tag:#moc` | 9133302 | Purple-deep |
| `#wiki` | `tag:#wiki` | 10980346 | Pink |
| `#glossar` | `tag:#glossar` | 10980346 | Pink (collision with #wiki) |
| `#kontext` | `tag:#kontext` | 6333946 | Green |
| `#projekt` | `tag:#projekt` | 16486972 | Sky-Blue |
| `#ressource` | `tag:#ressource` | 16019894 | Pink-magenta |
| `#bereich` | `tag:#bereich` | 3462041 | Mint |
| `#skill` | `tag:#skill` | 16486972 | Sky-Blue (collision with #projekt) |
| `#hermes` | `tag:#hermes` | 3462041 | Mint (collision with #bereich) |
| `#ai` | `tag:#ai` | 3462041 | Mint (collision with #bereich) |
| `#ki` | `tag:#ki` | 3462041 | Mint (collision with #bereich) |
| `#vault` | `tag:#vault` | 6333946 | Green (collision with #kontext) |
| `#archiv` | `tag:#archiv` | 7041664 | Gray-blue |
| `#todo` | `tag:#todo` | 16638023 | Coral-Orange (collision with #daily) |
| `#offen` | `tag:#offen` | 16638023 | Coral-Orange (collision with #daily) |

## RGB Collision Clusters

### Cluster 1: `#kontext` + `#vault` — 6333946 (Green)
2 tags, same RGB. Semantically related but distinct: "Kontext" = identity notes, "Vault" = meta-notes about the vault itself. These should either:
- Be merged into one tag (`#vault` → `#kontext`, or find a common parent)
- Get distinct colors (e.g., `#vault` gets purple, `#kontext` stays green)

### Cluster 2: `#bereich` + `#hermes` + `#ai` + `#ki` — 3462041 (Mint)
4 tags, same RGB. The strongest collapse candidate. `#bereich` is a folder tag, `#hermes`/`#ai`/`#ki` are all agent/AI tags. Recommendation:
- Collapse `#ai` + `#ki` into one (duplicate term — German + English for same concept)
- Keep `#hermes` distinct (specific framework)
- Keep `#bereich` distinct (structural folder tag)

### Cluster 3: `#daily` + `#todo` + `#offen` — 16638023 (Coral-Orange)
3 tags, same RGB. Status/action tags. `#todo` and `#offen` are near-synonyms. Recommendation:
- Collapse `#todo` + `#offen` into `#offen`
- Keep `#daily` distinct (time-based tag)

## Collision Detection Script

```python
def audit_color_groups(graph_json_path):
    """Read graph.json and report RGB collisions."""
    import json
    with open(graph_json_path) as f:
        data = json.load(f)
    
    groups = data.get('colorGroups', [])
    by_rgb = {}
    
    for g in groups:
        rgb = g['color']['rgb']
        tag = g['query'].replace('tag:#', '')
        by_rgb.setdefault(rgb, []).append(tag)
    
    print(f"Total colorGroups: {len(groups)}")
    print(f"Unique RGB values: {len(by_rgb)}")
    print(f"Distinct colors used: {len(set(by_rgb.keys()))}")
    print()
    
    for rgb, tags in sorted(by_rgb.items(), key=lambda x: -len(x[1])):
        symbol = " ⚠️ COLLISION" if len(tags) > 1 else " ✅"
        print(f"  {rgb:>12}{symbol}: {', '.join(tags)} ({len(tags)} tags)")
    
    print(f"\nCollisions: {sum(1 for t in by_rgb.values() if len(t) > 1)} clusters")
```

## Key Insight

16 colorGroups with only 8 distinct colors means the graph visualization appears less differentiated than the tag structure suggests. When the user looks at the knowledge graph, tags that look the same color ARE the same color — the graph.json is "lying" about its granularity.

This was caught because of **advisory voice ground-truth verification**: an advisor claimed "graph.json hat schwarze Nodes" (was true in Phase 5.5 before colorGroups were added), but by Phase 10 the colorGroups were already configured — just with duplication.
