# Skill-Curator Audit — Tier 1+2 (2026-07-11)

**Vollständiger Bericht:** `~/.hermes/docus/audits/skill-curator-2026-07-11-tier-1-2.md`

## Kurzfassung

Read-only Audit der 14 Tier 1+2 Skills aus `references/skill-tiers.md` gegen Hermes-Inventar, Frontmatter-Quality und Cross-Reference-Drift.

### Befunde

| Severity | Finding | Status |
|---|---|---|
| ✅ | Alle 14 Tier-Skills existieren im aktiven Tree | Keine Lücken |
| 🚨 MEDIUM | 4 Skills ohne `agent:`-Tag im eigenen YAML (`ideation`, `self-improving`, `skill-creator`, `mcp-server-authoring`) | Wartet auf Implement-Trigger |
| ⚠️ LOW | `plan` vs `writing-plans` Ambiguität in skill-tiers.md (beide existieren, beide nutzen) | Dokumentiert |
| ⚠️ LOW | 0 interne Markdown-Links in skill-tiers.md zu referenzierten Skills | Optionaler Pass |

### Offene Empfehlung (Option A)

4 YAMLs patchen mit `agent:` + `routing_hint:` — additive Änderung, kein Risiko, schließt Tier-Drift komplett.

### Worktree-Management

Lücke in Tier 2 #7 wurde als Skill-DRAFT dokumentiert. Trigger-Counter: 1/3 (Mnemosyne `63d4c331169e97f4`). Workaround-Helper in `~/.hermes/docus/audits/worktree-helper.sh` (bash -n verified).