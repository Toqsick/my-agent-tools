# Design Systems, Slop Diagnostic & Source Fidelity

Lifted from the original `SKILL.md` (now slim). Load this when you need the full
slop-diagnostic procedure, design-system walkthrough (tokens → rules → verification),
source-code fidelity workflow, copyright guidance, document-reading rules, or the
list of hosted-only Claude Design tool concepts to ignore.

---

## Hosted-Only Tool Concepts to Ignore / Remap

Reference: SKILL.md §"Runtime Mode". When the source Claude Design prompt references
these hosted-only concepts, ignore or remap to local equivalents:

- `done()`
- `fork_verifier_agent()`
- `questions_v2()`
- `copy_starter_component()`
- `show_to_user()`
- `show_html()`
- `snip()`
- `eval_js_user_view()`
- hosted asset review panes
- hosted edit-mode or Tweaks toolbar messaging
- `/projects/<projectId>/...` cross-project paths
- built-in `window.claude.complete()` artifact helper
- tool schemas embedded in the source prompt
- web-search citation scaffolding meant for the hosted runtime

Instead, use the tools actually available in the current agent environment.

---

## Design-System Walkthrough (per artifact)

The workflow §4 in SKILL.md says "define the design system for this artifact." This
is the order to fill in:

1. **Colors** — brand or invented small palette (see `design-patterns.md` §Color).
2. **Type** — family, scale, weights (see `design-patterns.md` §Typography).
3. **Spacing** — base unit + scale (e.g. 4 px base, 4/8/12/16/24/32/48/64).
4. **Radii** — typically 0/2/4/8/12 or a single chosen posture.
5. **Shadows / elevation** — pick a posture (flat, subtle, layered) and stay there.
6. **Motion posture** — declarative choice: still, restrained, expressive.
7. **Component treatment** — buttons, inputs, cards, navigation; apply tokens
   consistently.
8. **Interaction rules** — hover, focus, disabled, loading, error, success states.

Define tokens as CSS variables in `:root`. Never hard-code the same value twice.

---

## Slop Diagnostic: Score Before You Fix (full)

Reference: SKILL.md §"Slop Diagnostic". AI design slop has a tiny, predictable failure
distribution — designers asked to label AI UIs collapse the "this is AI" signal down
to about ten tells. Before polishing or repairing an artifact, run this as an explicit
self-audit and write a short report. **Diagnose first, treat second** — auditing and
fixing in one breath fails, because the model's prior outweighs the instruction and
it repeats the mistake (recolors when it needed re-layout, polishes type on a
composition problem).

### The ten tells (presence of each = one point of slop; lower is better)

1. **Tech gradient** — blue/violet/indigo glossy gradient on everything.
2. **Generic tech hue** — the default accent is indigo/violet (not chosen for the
   brand, just the model's favorite).
3. **Feature-tile grid** — icon + heading + sentence × 3, all equal weight, nothing
   prioritized.
4. **Accent rail** — a colored left strip on cards: decoration pretending to be
   organization.
5. **Unearned blur** — glassmorphism with no real depth/elevation system behind it.
6. **Monument stat** — oversized numbers filling space that should carry product
   story.
7. **Icon topper** — a rounded-square icon centered above every heading
   (Tailwind-template filler).
8. **Center stack** — everything centered because no real composition was committed
   to.
9. **Default type** — Inter (or system-ui) used by default rather than chosen.
10. **Wrong surface** — the composition doesn't match the surface (e.g. a hero on a
    Monitor surface). **This is the root cause behind most of the others.**

### How to run it

- Score the artifact out of 10 (10 = maximum slop).
- State the score and list which tells fired, in one short report.
- Treat the report as **context, not a to-do list** — it tells you *where* to spend
  repair effort, it does not dictate edits.
- Then repair, matched to the diagnosis:
  - tells 3, 8, 10 → **re-layout / re-compose** (revisit the surface choice — do not
    recolor).
  - tells 1, 2, 9 → **recolor / re-typeset** (palette and type are genuinely the
    problem here).
  - tells 4, 5, 6, 7 → **remove the decoration**; replace it with real hierarchy
    (scale, weight, spacing).
- Re-score after repairing. Do not declare done while compositional tells (3, 8, 10)
  are still firing — those are causes, the rest are usually symptoms.

The point of separating diagnosis from treatment: let the audit complain first, then
fix only what it complained about, in the register the complaint calls for.

---

## Source-Code Fidelity

When recreating or extending a UI from a repo:

1. Inspect the repo tree.
2. Identify the actual UI source files.
3. Read theme / token / global style / component files.
4. Lift exact values where appropriate.
5. Match spacing, radii, shadows, copy tone, density, and interaction patterns.
6. Only then design or modify.

Do not build from memory when source files are available.

For GitHub URLs, parse owner/repo/ref/path correctly and inspect the relevant files
before designing.

### Reading Documents and Assets

- Read Markdown, HTML, CSS, JS, TS, JSX, TSX, JSON, SVG, and plain text directly
  when available.
- For DOCX/PPTX/PDF, use available local extraction tools if present. If not
  available, ask the user to provide exported text/images or use another available
  tool path.
- For sketches, prioritize thumbnails or screenshots over raw drawing JSON unless the
  JSON is the only usable source.

---

## Verification (full)

Before final response, verify as much as the environment allows.

**Minimum:**

- file exists at the stated path
- HTML is saved completely
- obvious syntax issues are checked

**Better:**

- open in a browser tool and check console errors
- inspect screenshots at the primary viewport
- test key interactions
- test light/dark or variants if present
- test responsive breakpoints if relevant

If verification is limited by environment, **say exactly what was and was not
verified**.

**Never say "done" if the file was not actually written.**

---

## Copyright and Reference Models

Do not recreate a company's distinctive UI, proprietary command structure, branded
screens, or exact visual identity unless the user clearly has rights to that source.

It is acceptable to extract general design principles:

- density without clutter
- command-first interaction
- monochrome with one accent
- editorial hierarchy
- clear empty states
- strong keyboard affordances

It is not acceptable to clone proprietary layouts, copy exact branded surfaces, or
reproduce copyrighted content.

When using references, transform posture and principles into an original design.