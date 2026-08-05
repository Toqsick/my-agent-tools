# Skill Packs

The `agent-toolkit` plugin ships **129 installed skills** grouped into **8 themed packs**. The
packs are a navigation/grouping layer over the installed skills — every skill still loads in
every session (it's one plugin), and is still invokable as `agent-toolkit:<name>`. Packs just
make the wall of 129 skills scannable: by domain, by count, by "when to use this pack".

- **Canonical manifest:** [`plugins/agent-toolkit/packs/manifest.json`](plugins/agent-toolkit/packs/manifest.json)
  (generated-validated by `scripts/build_packs.py`; never hand-edit the bundles).
- **Per-pack detail:** `plugins/agent-toolkit/packs/<pack>/README.md` (one per pack).
- **Routing bundles:** `routing/bundles/<pack>.yaml` (one per pack, emitted from the manifest).
- **Browse live:** run `/toolkit` (overview), `/toolkit <pack>` (a pack's skills), or
  `/toolkit doctor` (health check).

## The 8 packs

| Pack | Title | Category | Skills | When to use |
|---|---|---|---:|---|
| `core` | Core & Personal | productivity | 10 | Daily-driver layer: Obsidian second-brain, system cleanup, 3D printing, Yuno team orchestration/routing/preferences, model selection, folder tidy, daily briefing, skill↔MCP router. |
| `hermes-dev` | Hermes / Yuno Platform | development | 18 | Building on the Hermes/Yuno platform: CLI internals, gateway protocol/clients, mobile clients, Ariadne memory, gateway adapters, desktop plugins, messaging gateways, themes, ModelHub. |
| `cybersecurity` | Cybersecurity | security | 50 | Defensive security & DFIR: CIS hardening, Docker/K8s, network hunting (Zeek/Suricata/Wireshark), forensics (Volatility/IR), compliance & supply-chain (SBOM/SLSA/gitleaks). |
| `methodology` | Engineering Methodology | development | 18 | The Superpowers workflow set (brainstorm→plan→TDD→debug→verify→finish), subagent-driven development, ZCode SubAgent Team, Queen-Bee swarm dispatch, multi-agent master workflow. |
| `media` | Media & Generation | creative | 6 | MiniMax `mmx` CLI, MiniMax agent builder, crypto trading, DOCX/PDF, Nano Banana Pro image gen. |
| `docs-web-research` | Docs, Web & Research | productivity | 15 | Document gen (PPT/McKinsey/research papers), frontend design, web scraping, Excel, n8n, SEO/GEO, business research (job hunter, sales Power Maps, SaaS niches), NotebookLM, knowledge digest, prompt engineering. |
| `computer-use` | Computer-Use & GreyHack | automation | 3 | Desktop/game GUI automation: GreyHack Computer-Use suite + game and desktop-window reconnaissance. |
| `dev-essentials` | Dev Essentials | development | 9 | Engineering originals: debugging patterns, defensive programming, config-propagation bugs, reference-architecture research, open-source extraction, stealth web scraping, web-content recon, competitive-landscape research, ClickHouse best practices. |

**Total: 129 skills across 8 packs** — a clean partition (every installed skill in exactly one
pack, validated by `scripts/build_packs.py`, which exits non-zero on a partition error).

## How packs relate to the plugin today

Right now there is **one plugin** (`agent-toolkit`) and **one marketplace entry** that installs
all 129 skills. The packs are metadata — `manifest.json` + per-pack READMEs + routing bundles —
not separate install targets. The 8 themed marketplace entries in
`.claude-plugin/marketplace.json` (`agent-toolkit-core`, `-hermes-dev`, …) are **stubs**: each
points at the same `./plugins/agent-toolkit` source, so installing any themed handle today
installs the full toolkit. They exist so the split below is a one-line source repoint, not a
restructure.

> ⚠️ **Fallback note:** if Claude Code's `/plugin marketplace` rejects multiple entries sharing
> one `source` (the plugin's internal `name` is `agent-toolkit` regardless of the marketplace
> entry name), keep only the canonical `agent-toolkit` entry and treat this file as the durable
> record of the 8 future targets. The stubs are a convenience, not a requirement.

## Future split — "install only what you need"

When the toolkit grows or a user wants a lighter install, split each pack into its own plugin
directory and repoint its marketplace entry. The mechanical steps:

1. For each pack `P`, create `plugins/agent-toolkit-P/` with a `.claude-plugin/plugin.json` whose
   `skills` array lists only that pack's skills (copy them from
   `plugins/agent-toolkit/skills/<name>/` or symlink — keep copies self-contained per the repo's
   no-symlink-outside-repo rule).
2. Repoint the matching marketplace stub:
   ```jsonc
   // .claude-plugin/marketplace.json
   {
     "name": "agent-toolkit-cybersecurity",          // already a stub entry
     "source": "./plugins/agent-toolkit-cybersecurity", // was: "./plugins/agent-toolkit"
     "description": "Cybersecurity pack: 50 DFIR/defensive skills …",
     "category": "security",
     "homepage": "https://github.com/Toqsick/my-agent-tools/tree/main/plugins/agent-toolkit-cybersecurity"
   }
   ```
3. Keep the monolithic `agent-toolkit` entry as an "install everything" convenience, or retire it
   once the 8 themed plugins are stable.
4. Re-run `python3 scripts/build_index.py` (the manifest is the source of truth for pack
   membership; `build_packs.py` will re-emit bundles and validate the partition).

**Migration order (recommended):** split the largest/most-self-contained pack first
(`cybersecurity`, 50 skills — least overlap with daily-driver work), then `hermes-dev` (18) and
`methodology` (18). The small packs (`media`, `computer-use`, `dev-essentials`) can stay bundled
until there's a reason to split them.

## Maintenance

- **Adding a skill:** drop it under `plugins/agent-toolkit/skills/<name>/`, add it to the `skills`
  array in `plugin.json`, **and** add it to exactly one pack's `skills` list in
  `packs/manifest.json`. Then `python3 scripts/build_index.py` (which calls `build_packs`) —
  it validates the partition (union == installed set, no dupes) and re-emits the routing
  bundles. A non-zero exit means the manifest is out of sync with the installed skills; fix the
  manifest, don't silence the check.
- **Repacking:** to re-theme the packs, edit only `packs/manifest.json` and re-run
  `build_index.py`. Per-pack READMEs and routing bundles are derived; regenerate, don't hand-edit.
- **Never** hand-edit `routing/bundles/*.yaml`, `INDEX.json`, or `NAVIGATION.md`.