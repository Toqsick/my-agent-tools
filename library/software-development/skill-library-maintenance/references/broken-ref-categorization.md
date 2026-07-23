# Broken-Reference Categorization Framework

## The Three Categories

| Category | Trigger | Root Cause | Recommended Action |
|---|---|---|---|
| **BUNDLE_MISSING** | Skill has no `references/` AND no `scripts/` dir, but mentions files inside those paths | Single-file skill in a bundle-only format. The skill was authored with planned extraction that never happened, or was slimmed without creating the subdirs | **Delete the ref** from SKILL.md (lowest effort, keeps the skill usable standalone), OR create the directory + a stub file. P0 when count >3: delete all refs. |
| **FILE_MISSING** | `references/` or `scripts/` dir EXISTS, but the specific file named inside it does not | Bundle dir was created for one file, others were documented but never written. Common pattern: hub skills that cross-ref many sibling skills | Create the file (if the content is documented elsewhere) or remove the one-line pointer. P0 if the skill is frequently loaded (e.g. daily-briefing, voice-assistant-bots). |
| **TEMPLATE_PLACEHOLDER** | Ref path contains `example`, `sample`, `todo`, `placeholder` or a `<ANGLE_BRACKET>` token | Placeholder never resolved to an actual file. The author intended to write it later | Remove the ref from SKILL.md. If the placeholder is documented content with value, promote to a real file. P2 — low urgency. |

## Priority Scheme (P0/P1/P2)

### P0 — Fix Now
- BUNDLE_MISSING on a skill with >=3 broken refs
- FILE_MISSING on a frequently-loaded productivity/infra skill
- Any ref that is a clear typo (double path, wrong extension)
- **Goal:** eliminate ~60% of broken refs with low cognitive cost

### P1 — Review and Decide
- BUNDLE_MISSING on a skill with 1-3 refs
- FILE_MISSING on a mid-tier skill (loaded <1x/week)
- Hub/cross-skill links that may be intentionally external (verify: does the target file exist in a sibling skill?)
- **Goal:** verify intent, then either create the file or remove the ref

### P2 — Opportunistic
- TEMPLATE_PLACEHOLDER only (4 found in audit)
- FILE_MISSING on rarely-loaded skills or archive candidates
- **Goal:** sweep when cleaning anyway

## Bundle-Skill Distinction

A critical distinction surfaced by this framework:

| Property | Count (2026-07-16) |
|---|---|
| Skills TOTAL (active, ex archive) | 491 |
| Bundle-Skills (no references/ + no scripts/) | 203 |
| Bundle-Skills with broken refs in SKILL.md | 54 |
| Skills with bundle dir that have FILE_MISSING | 29 |
| Bundle-Skills that are CLEAN (no refs in SKILL.md, no bundle dir) | 149 |

The 149 clean Bundle-Skills are correct by design: they are single-file skills that never claimed to have external resources. They need no action.

The 54 Bundle-Skills with refs are the "type error" — they were documented as if they were multi-file skills. Fix them by deleting the refs from SKILL.md (or, optionally, creating the directories).

## Cross-Skill Resolution

When a ref does not resolve in the skill's own directory, check the wider library:

```python
# Does the file exist in another skill?
for p in ROOT.rglob(target.name):
    if str(p.relative_to(ROOT)).endswith("/" + ref.rsplit("/", 1)[-1]):
        # found elsewhere — likely a cross-skill link, not broken
```

This matters for **FILE_MISSING**: a ref to `references/something.md` may be referencing a sibling skill's documentation rather than claiming to own that file. Such refs should be reclassified as "intentional cross-link" and left alone.

## Pitfall

**Pitfall #37 — Bundle-Skill type error.** Skills without `references/` or `scripts/` dirs MUST NOT reference paths inside those dirs. When a skill was extracted (slimmed) and all content was moved into the SKILL.md, remaining `references/X.md` pointers are dead — delete them. Do not keep the ref "just in case" the directory is created later.
