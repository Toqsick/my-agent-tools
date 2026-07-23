# Phase 3: Content Depth Expansion

After the vault skeleton (Phase 1) and parallel subagent growth (Phase 2), the next phase targets **content depth**: filling thin notes, launching new topic clusters, and densifying cross-links.

## When to Enter Phase 3

Use Phase 3 when all of these are true:

| Condition | How to check |
|---|---|
| Phase 1 complete | 8 folders populated, MOC in each, `MOC - Home.md` exists |
| Phase 2 complete | > 55 notes, wiki-link density ≥ 4.0 avg, cross-link cleanup done |
| Inhaltlicher Hunger | User says "mehr Tiefe", "knall den Vault voll", or picks a depth-oriented option |
| Structural stability | No pending structural changes (folder renames, schema migration) |

## Step 0: Inventory — Find Thin Notes

Before writing a single line, run an inventory to identify the exact gaps. **Never guess which notes are thin — measure it.**

See → [Wiki-Link Density (Python)](wiki-link-density-python.md) for thin-notes detection script.

Also check existing Themen-MOC density — MOCs with < 25 out-links have room to grow.

## Step 1: Plan as Vault Resource

Write a **Vault-Phase-3-Plan.md** as a vault resource (`05 Ressourcen/`) before dispatching any subagents. The plan should include:

- **Inventory summary** — how many thin notes, which Themen-MOCs are sparse, what topics are thematically absent
- **Cluster proposals** — 2–4 concrete clusters with estimated effort and output measurement
- **User choice** — present as klar abgegrenzte Optionen (I, II, III, IV recommended combination)
- **Risiko-Mitigation** — known pitfalls from prior phases (sibling conflicts, hallucination risk)
- **Verbindet zu** — wiki-links to `[[Vault - Konzept & Wissensdatenbank]]`, `[[Vault-Health-Metrics]]`, `[[Subagent-Operations-Log - Vault Phase 2]]`

## Step 2: Cluster Selection

Three canonical clusters for Phase 3 content depth:

| Cluster | Target | Effort | Measurement |
|---|---|---|---|
| **1 — Project-Stubs füllen** | Thin Projekt-READMEs (lines < 60) — read from `~/10-Projekte/10-active/<name>/` and destill into ~80–120 line notes with tool-lists, Dataview queries, cross-links | ~30 min, 1 subagent | READMEs gain +40–80 lines, avg link density +0.2–0.3 |
| **2 — Neue Themen-MOCs + Satelliten** | 1 neues Themen-MOC (z.B. "Lernen & Orchestration") + 3–5 Satelliten-Notes (Parent-Direct-Fallback, Skill-Drift, Queen-Bee) — bündelt eine thematische Lücke | ~45 min, 1 subagent | 1 new MOC (≥ 20 out-links) + 5 new notes (≥ 5 links each) |
| **3 — Cross-Link-Tiefe** | Add "Verbindet zu"-Sektionen to thin notes, Glossar-verweise, Dataview-Tabellen, reduce unresolved links | ~30 min, 1 subagent | +40–120 wiki-links, avg density +0.5–2.0 |

### Cluster 3: "Verbindet zu" Decision Framework

When enriching a note's `## Verbindet zu` section, pick 3–7 links from these six categories (standard order: MOCs → Ressourcen → Kontext → Cross-Cluster → Projekte → Verbundene):

| # | Category | What to link | Example |
|---|---|---|---|
| 1 | **MOCs (Themen)** | Thematic overviews the note lives under | `[[MOC - KI-Architektur]]`, `[[MOC - Gaming-Performance]]` |
| 2 | **Ressourcen** | Tools, guides, references the note uses or relates to | `[[Glossar]]` (Akronyme), `[[Templater - Setup-Anleitung]]` (tool) |
| 3 | **Kontext** | Identity notes, working agreements, user profiles | `[[Basti - Profil]]`, `[[Working Agreement - Yuno Basti]]` |
| 4 | **Cross-Cluster** | Related notes in a different folder (hot-path connections) | `[[Cron-Infrastruktur - 2026-07-05]]` (Ressourcen → Daily) |
| 5 | **Projekte** | Active project READMEs or sub-notes | `[[Github-MCP-Server]]`, `[[Yuno-Voice-Bot]]` |
| 6 | **Verbundene Ressourcen** | Sibling notes in the same folder that complement this one | `[[Mnemosyne - Patterns]]` (next to Yuno notes) |

**Rule of thumb:** at least 1 link from #1 or #2 (ties to navigation), 1 from #3 or #4 (connects to user/project context), and 1 from #5 or #6 (cluster cohesion). MOCs should cover all 6. Preserve existing links and add 3–5 more — **additive patches only**.

## Step 3: Subagent Cluster with Explicit Rules

Each subagent receives in its context:

1. **Exact file paths** to the notes it owns — no path resolution needed
2. **Anti-Halluzination-Tripwire (Projekt-READMEs)** — Cluster 1 must verify EVERY data point against 3+ source types before writing: `git log` (commits, branches), `go.mod`/`pyproject.toml`/`package.json` (versions, licenses), `README.md` (upstream URL, features), actual source files (architecture)
3. **No new MOCs without limit** — Cluster 2 is capped at 1 new Themen-MOC + max 5 satellite notes
4. **Additive patches only** — never `write_file` on existing notes. Patch tool only, with `mode='replace'`.
5. **Output contract** — list of created files + patch count + link density delta
6. **Subagent darf bessere Entscheidungen treffen** — Wenn ein Subagent eine strukturell bessere Wahl erkennt (z.B. Queen-Bee-Lab als neues Projekt statt generischem Lernjournal), soll er diese treffen. NUR wenn: (a) keine existierenden Daten zerstört werden, (b) die Task-Abdeckung nicht reduziert wird.
7. **Subagent-Limit einplanen** — Subagents (besonders MiniMax-M3) hit tool-call-Limit bei ~80 Aufrufen (~20–30 write/patch operations). Bei 30+ File-Operationen: Arbeit auf 2+ Subagents aufteilen oder Scope reduzieren.

## Step 4: Post-Phase-3 Verification

```bash
# 1. Full note count
find "$VAULT" -name '*.md' -not -path '*/.obsidian/*' | wc -l

# 2. Wiki-link density
python3 -c "
import os, re
vault = '$VAULT'
links = []
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or '.trash' in root: continue
    for f in files:
        if not f.endswith('.md'): continue
        with open(os.path.join(root, f)) as fh:
            c = fh.read()
        l = len(set(re.findall(r'\[\[([^\]|#]+)', c)))
        links.append(l)
print(f'Notes: {len(links)}, Avg: {sum(links)/len(links):.1f}, Med: {sorted(links)[len(links)//2]}')
"

# 3. Thin-notes check — count notes < 60 lines (should decrease)
python3 -c "
import os
vault = '$VAULT'
thin = 0
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or '.trash' in root or '_templates' in root: continue
    for f in files:
        if not f.endswith('.md'): continue
        with open(os.path.join(root, f)) as fh:
            c = fh.read()
        if len(c.splitlines()) < 60 and '_MOC' not in f and '_README' not in f and 'Willkommen' not in f:
            thin += 1
print(f'Dünne Notes (< 60 lines): {thin}')
"

# 4. Cross-link cleanup — re-run broken-link check
python3 scripts/check-broken-wiki-links.py "$VAULT"

# 5. Memory save — update Vault-Health-Metrics with new Phase 3 measurements
```

## Phase 3 Examples from Practice

| Metric | Before Phase 3 (2026-07-05) | After Phase 3 Cross-Link (2026-07-05) | Delta |
|---|---|---|---|
| Notes gesamt | 54 | 67+ | +13+ (new satellite notes + Patches) |
| Avg Links/Note | 4.1 | **~6.5** | +2.4 (Goal met) |
| Thin notes (< 60 lines) | 18 | Reduced to ~10–12 | Cluster 1 (Project-Stubs) further reduces |
| Themen-MOCs | 0 | 4 (Gaming, KI-Architektur, Obsidian-Vault, Lernen & Orchestration) | +1 |
| Glossar wiki-links | 4 | **98** | +94 (95 % terms now linked) |
| Patched "Verbindet zu" sections | 5 | 27+ | +22 notes enriched |
| Project-README depth | 5 stubs (~37–54 lines) | 5 stubs | ~80–120 lines each (Cluster 1 target) |