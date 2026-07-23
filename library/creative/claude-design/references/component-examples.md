# Component Examples & Format Rules

Detailed format rules and component guidance lifted from the original `SKILL.md`
(now slim). Load this file when you are actually building the artifact — HTML/CSS/JS
standards, deck rules, prototype rules, Tweaks panel, React guidance.

---

## Artifact Format Rules (detailed)

**Default: local files.**

For standalone artifacts:

- Create a descriptive filename, e.g. `Landing Page.html`, `Command Palette Prototype.html`,
  `Design System Board.html`.
- Embed CSS in `<style>`.
- Embed JS in `<script>`.
- Keep the artifact openable directly in a browser.
- Avoid remote dependencies unless they are explicitly useful and stable.
- Include responsive behavior unless the format is intentionally fixed-size.

For significant revisions:

- Preserve the previous version as `Name.html`.
- Create `Name v2.html`, `Name v3.html`, etc.
- Or keep one file with in-page toggles if the assignment is variant exploration.

For repo implementation:

- Follow the repo's actual stack.
- Use existing components and tokens where possible.
- Do **not** create a standalone artifact if the user asked for production code.

---

## HTML / CSS / JS Standards

Use modern CSS well:

- CSS variables for tokens.
- CSS grid for layout.
- Container queries when helpful.
- `text-wrap: pretty` where supported.
- Real focus states.
- Real hover states.
- `prefers-reduced-motion` handling for non-trivial motion.
- Responsive scaling.
- Semantic HTML where practical.

Avoid:

- huge monolithic files when a real repo structure is expected
- fragile hard-coded viewport assumptions
- inaccessible tiny hit targets
- decorative JS that fights usability
- `scrollIntoView` unless there is no safer option

---

## React Guidance for Standalone HTML

Use plain HTML/CSS/JS by default.

Use React only when:

- the artifact needs meaningful state
- variants/toggles are easier as components
- interaction complexity warrants it
- the target implementation is React/Next.js and fidelity matters

If using React from CDN in standalone HTML:

- Pin exact versions.
- Avoid unpinned `react@18` style URLs.
- Avoid `type="module"` unless necessary.
- Avoid multiple global objects named `styles`.
- Give global style objects specific names, e.g. `commandPaletteStyles`, `deckStyles`.
- If splitting Babel scripts, explicitly attach shared components to `window`.

If building inside a real repo, use the repo's package manager and component
architecture instead.

---

## Deck Rules (1920×1080)

For slide decks, use a fixed-size canvas and scale it to fit the viewport.

- Default slide size: **1920×1080, 16:9**.
- Keyboard navigation required.
- Visible slide count.
- localStorage persistence for current slide.
- Print-friendly layout when practical.
- Screen labels or stable IDs for important slides.
- No speaker notes unless the user explicitly asks.

Do not hand-wave a deck as markdown bullets. Create a designed artifact if asked
for a deck.

Use 1–2 background colors max unless the brand system requires more.

Keep slides sparse. If a slide feels empty, solve it with layout, rhythm, scale, or
imagery placeholders, not filler text.

---

## Prototype Rules

For interactive prototypes:

- Make the primary path clickable.
- Include key states: default, hover/focus, loading, empty, error, success where relevant.
- Expose variations with in-page controls when useful.
- Keep controls out of the final composition unless they are intentionally part of
  the prototype.
- Persist important state in localStorage when refresh continuity matters.

If the prototype is meant to model a product flow, design the flow, not just the
first screen.

---

## Variation Rules

When exploring, default to **at least three options**:

1. **Conservative** — closest to existing patterns / lowest risk.
2. **Strong-fit** — best interpretation of the brief.
3. **Divergent** — more novel, useful for discovering taste boundaries.

Variations can explore: layout, hierarchy, type scale, density, color posture,
surface treatment, motion, interaction model, copy structure, component shape.

Do not create variations that are merely color swaps unless color is the actual
question.

When the user picks a direction, **consolidate**. Do not leave the project as a
pile of options forever.

---

## Tweaks Panel (CLI/API substitute for hosted edit-mode)

The hosted Claude Design edit-mode toolbar does not exist here. Still preserve the
idea: when useful, add in-page controls called `Tweaks`.

A good `Tweaks` panel can control:

- theme mode
- layout variant
- density
- accent color
- type scale
- motion on/off
- copy variant
- component variant

Keep it small and unobtrusive. The design should look final when tweaks are hidden.

Persist tweak values with localStorage when helpful.

---

## Final Response Format (example)

```text
Created: /path/to/Prototype.html
It includes 3 layout variants, a Tweaks panel for density/theme, and responsive behavior.
Verified: file exists and opened cleanly in browser, no console errors.
Next: pick the strongest direction and I'll tighten copy + motion.
```

---

## Portable Opening Prompt Pattern

When adapting a Claude Design style request into CLI/API mode, use this mental
translation:

```text
You are running in CLI/API mode, not hosted Claude Design. Ignore references to
hosted-only tools or preview panes. Produce complete local design artifacts, usually
self-contained HTML with embedded CSS/JS, and verify with available local tools
before returning. Preserve the design process: gather context, define the system,
produce options, avoid filler, and meet a high visual bar.
```