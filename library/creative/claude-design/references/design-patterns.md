# Design Patterns & Visual Rules

Detailed patterns lifted from the original `SKILL.md` (now slim). Load this file when
you need the full rule sets for typography, color, layout, motion, or images — or when
you want worked examples for the seven surface archetypes.

---

## Surface Archetypes (extended)

Reference: SKILL.md §"Surface-First: Commit to a Composition Before Touching Tokens".

The seven archetypes are the most leveraged constraint in the entire skill. Every
artifact should state one in a single line before any tokens are written:

| # | Surface | Composition signature | Hero correct? |
|---|---|---|---|
| 1 | **Monitor** | Dashboards, status pages, observability. Density, glanceable hierarchy, no marketing framing. | No |
| 2 | **Operate** | Consoles, admin panels, queues, inboxes. Action affordances and selection state dominate. | No |
| 3 | **Compare** | Pricing, plans, spec tables, search results. Aligned columns, parity of structure, one differentiator emphasized. | No |
| 4 | **Configure** | Settings, forms, wizards, onboarding. Progressive disclosure, clear save/validation states, low decoration. | No |
| 5 | **Decide / Learn** | Landing pages, docs, marketing. One idea lands per section. | **Yes (only here)** |
| 6 | **Explore** | Galleries, maps, search-and-filter, catalogs. Filters, result grids, zoom/peek. | No |
| 7 | **Command / Inspect** | Command bars, inspectors, detail panes, property editors. Speed and focus over breadth. | No |

**Hard rule:** the hero-plus-three-cards composition is correct for **Decide/Learn only**.
Reaching for it anywhere else is the #1 tell of AI design slop.

If a screen genuinely spans two surfaces, name the **primary** one and treat the other
as secondary — do not average them into mush.

---

## Typography (detailed)

Use the existing type system if one exists. If not, choose deliberately:

- **Editorial:** serif or humanist headline with restrained sans body.
- **Software / productivity:** precise sans with strong numeric treatment.
- **Luxury / minimal:** fewer weights, more spacing discipline.
- **Technical:** mono accents only, not mono everywhere.
- **Deck:** large, clear, high contrast.

Rules:

- Avoid overused defaults when a stronger choice is appropriate.
- If using web fonts, keep the number of families and weights low.
- Use type as hierarchy **before** adding boxes, icons, or color.
- For 1920×1080 slide decks, text should generally be 24 px or larger.
- For print documents, text should be at least 12 pt.
- Mobile hit targets should be at least 44 px.

---

## Color (detailed)

- Use brand / design-system colors first.
- If no palette exists, define a small system: neutrals, surface, ink, muted text,
  border, accent, danger / success if needed.
- Use one primary accent unless the assignment calls for a broader palette.
- Prefer `oklch` for harmonious invented palettes when browser support is acceptable.
- Check contrast for important text and controls.
- Do not invent lots of colors from scratch.

---

## Layout and Composition (detailed)

Design with rhythm:

- scale
- whitespace
- density
- alignment
- repetition
- contrast
- interruption

Avoid making every section the same card grid.

- **For product UIs:** prioritize speed of comprehension over decoration.
- **For marketing surfaces:** make one idea land per section.
- **For dashboards:** avoid "data slop." Only show data that helps the user decide or act.

---

## Motion (detailed)

Use motion as discipline, not theater.

**Good motion:**

- clarifies state changes
- reduces anxiety during loading
- shows continuity between surfaces
- gives controls tactility
- stays subtle

**Bad motion:**

- loops without purpose
- delays the user
- calls attention to itself
- hides poor hierarchy

Respect `prefers-reduced-motion` for non-trivial animation.

---

## Images and Icons (detailed)

- Use real supplied imagery when available.
- If an asset is missing:
  - use a clean placeholder
  - use typography, layout, or abstract texture instead
  - ask for real material when fidelity matters
- Do not draw elaborate fake SVG illustrations unless the assignment is explicitly
  illustration work.
- Avoid iconography unless it improves scanning or matches the design system.

---

## Anti-Slop Rules (full list)

Reference: SKILL.md §"Anti-Slop Rules". These are the *symptoms*; the root cause
is usually the surface-choice failure (tell #10).

Avoid:

- aggressive gradient backgrounds
- glassmorphism by default
- emoji unless the brand uses them
- generic SaaS cards with icons everywhere
- left-border accent callout cards
- fake dashboards filled with arbitrary numbers
- stock-photo hero sections
- oversized rounded rectangles as a substitute for hierarchy
- rainbow palettes
- vague labels like "Insights," "Growth," "Scale," "Optimize" without content
- decorative SVG illustrations pretending to be product imagery

**Minimal is not automatically good. Dense is not automatically cluttered.** Choose
intentionally.

---

## Content Discipline

- Do not add filler content. Every element must earn its place.
- Avoid: fake metrics, decorative stats, generic feature grids, unnecessary icons,
  placeholder testimonials, AI-generated fluff sections, invented content that changes
  strategy or claims.
- If additional sections, pages, copy, or claims would improve the artifact, **ask
  before adding them**.
- When copy is necessary but not final, mark it as draft or placeholder.