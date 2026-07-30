# MCP-aware routing layer

This directory is the `zcode-skills` routing layer adapted for the
`my-agent-tools` repository. It contains metadata and routing rules, not a
second copy of every skill body.

- `registry/registry.json` is generated from the installed plugin and library
  skill trees with repository-relative paths.
- `registry/routing.yaml` contains intent buckets, the meta-skill penalty, and
  configured/unconfigured MCP mappings.
- `registry/skill-to-mcp.csv` records identity-coupled skill-to-server hints.
- `config/mcp-template.json` is a sanitized GitHub MCP template. It is a
  documentation template, not a credential store.
- `bundles/` and `manifests/` preserve the imported bundle/provenance metadata.

Regenerate all catalogs after adding or changing a skill:

```bash
python3 scripts/build_index.py
```

The command writes `INDEX.json`, `NAVIGATION.md`, and all files under
`routing/registry/`. Never commit a filled `.env` or a literal GitHub PAT.
The `github` mapping is the only runtime MCP mapping declared by this repo;
other mappings remain explicit `configured: false` fallback hints until their
servers are installed and verified.
