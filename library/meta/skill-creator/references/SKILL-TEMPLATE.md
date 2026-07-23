<!-- ============================================================
     TWO FILES REQUIRED:
     1. SKILL.md  — agent runtime (name + description + system prompt body)
     2. meta.yaml — display metadata (display-name-zh, version, tag, summary, desc)
     ============================================================ -->

<!-- ===== SKILL.md ===== -->
---
name: <skill-name>
description: |
  <One-sentence summary of what this skill does>. <Elaboration on the workflow: input -> key transformations -> output>.
  Use whenever the user wants to <trigger phrase 1>, <trigger phrase 2>, or <trigger phrase 3>.
---

<!-- ===== meta.yaml (separate file) ===== -->
<!--
display-name-zh: <中文名，≤10字符>
version: 0.1.0
tag-en: "<垂类> / <阶段>"
tag-cn: "<垂类> / <阶段>"
summary-en: "<≤30 words>"
summary-cn: "<≤25 汉字>"
desc-en: "<50-80 words>"
desc-cn: "<80-150 汉字>"
-->

# <Skill Name>

When the user wants to <do X>, follow this workflow.

<!-- ============================================================
     TEMPLATE NOTES (delete this block when using)

     This template is extracted from the music-mv skill. It captures
     the structural patterns that make a production-quality skill:

     0. PRE = obtain auth token via MCP (if workflow needs API calls)
     1. STEP 0 = prerequisites & resource check
     2. STEP 1 = analysis / understanding input
     3. STEP 2 = planning / script generation (LLM task)
     4. STEP 3 = asset generation (batch, parallel)
     5. STEP 4 = user confirmation checkpoint
     6. STEP 5 = main production (substeps, batch strategy)
     7. STEP 6 = assembly / post-processing
     8. STEP 7 = present result

     Not every skill needs all 8 steps. A simpler workflow might
     only need 4-5. But the ORDERING is important:
     check -> analyze -> plan -> generate -> confirm -> produce -> assemble -> present

     The PRE step is optional -- only needed when the workflow
     calls external APIs that require authentication. If your
     skill is purely local (ffmpeg, LLM planning, file I/O),
     skip it.

     Key principles from music-mv:
     - Batch everything: collect all items, then one call per agent
     - Never interleave: don't alternate between agents per item
     - Validate before proceeding: catch errors early
     - Explain WHY behind constraints, not just WHAT
     - Include technical details ONLY when the agent wouldn't know
     - Add user checkpoints at creative decision points
     ============================================================ -->


## PRE: OBTAIN HILO TOKEN

Before starting the workflow, obtain the Hilo API token via MCP:

1. **Call MCP `get_token`**, store the returned `access_token`.
2. This token will be used in subsequent video generation steps (Hilo/Official).
3. **Token lifetime**: If the workflow is long-running (>30 min), check token expiry before each API call and refresh if needed.

**Why obtain early**: Getting the token upfront avoids interrupting the creative flow mid-workflow. If auth fails, the user knows immediately -- rather than after expensive generation steps have already run.


## STEP 0: CHECK RESOURCES

<!-- What does the skill need before it can start? -->
<!-- List required inputs, optional inputs, and how to obtain missing ones. -->

1. **<Required input 1>**: If not provided, ask the user to provide one or <describe fallback>.
2. **<Required input 2>**: Ask the user: "<clarifying question>".
3. **<Optional preprocessing>**: If user specifies <condition>, do <preprocessing> first.
4. Get <metadata> from the input (e.g., duration, dimensions, format).


## STEP 1: ANALYZE INPUT

<!-- Understand the source material before making creative decisions. -->
<!-- This step feeds into ALL subsequent steps. -->

Analyze the input to understand:
- <Dimension 1> (e.g., mood, style, structure)
- <Dimension 2> (e.g., content breakdown, sections)
- <Dimension 3> (e.g., technical properties)

Use this analysis throughout the workflow:
- **Step 2**: Guide <planning decisions>
- **Step 3**: Determine <generation parameters>


## STEP 2: GENERATE PLAN / SCRIPT

<!-- This is an LLM planning task -- the orchestrator does this itself. -->
<!-- Define the creative structure that drives all downstream generation. -->

Generate a complete <plan/script/storyboard> that includes:

### <Component A> (e.g., Characters, Themes, Sections)

```json
{
  "<id_field>": "<unique_id>",
  "<name_field>": "<display name>",
  "<prompt_field>": "<generation prompt or description>"
}
```

<!-- List constraints and rules for this component. -->
- <Rule 1>: <what to do> -- <why it matters>
- <Rule 2>: <what to do> -- <why it matters>

### <Component B> (e.g., Scenes, Layouts, Segments)

```json
{
  "<id_field>": "<unique_id>",
  "<timing_fields>": "<start/end or ordering>",
  "<content_field>": "<what happens>",
  "<reference_fields>": "<links to Component A>"
}
```

**Timing / ordering rules**:
- <Continuity rule>: e.g., segments must be continuous, no gaps
- <Duration rule>: e.g., each segment 3-15 seconds
- <Preferred range>: e.g., 7-10 seconds per segment -- fewer, longer segments produce more coherent results

**Type / category rules**:
- `<type_1>`: <when to use, what it means>
- `<type_2>`: <when to use, what it means>

**Ratio / balance rules**:
- <Distribution guideline>: e.g., ~60% type_1, ~40% type_2 by total duration
- <Anti-pattern>: e.g., never place two <type_2> segments back-to-back

### Validate

After generating the plan, validate it:
- <Validation check 1>
- <Validation check 2>
- Fix all errors and re-validate until passed.


## STEP 3: GENERATE ASSETS

<!-- Batch-generate all intermediate assets in as few calls as possible. -->
<!-- Group by asset type, NOT by downstream usage. -->

Generate all <asset type> in one batch:

1. **<Asset category 1>** (e.g., character images): Use each item's `<prompt_field>`. <Key parameter>: `<value>`.
2. **<Asset category 2>** (e.g., scene images): Use each item's `<prompt_field>`. <Key parameter>: `<value>`.

Include ALL prompts in one task to minimize round-trips.

<!-- Pitfall callout: things that seem obvious but cause real failures. -->
**Pitfall**: Do NOT <common mistake> -- <what happens if you do>.


## STEP 4: CONFIRM WITH USER

<!-- Creative checkpoint: user reviews intermediate assets before expensive production. -->

Present all generated assets to the user. Ask if any need adjustments. Regenerate as needed.

<!-- This step is cheap (just showing images/text). -->
<!-- Skipping it risks wasting expensive generation in Step 5. -->


## STEP 5: MAIN PRODUCTION

<!-- The most complex step. Break into substeps (5a, 5b, 5c...). -->
<!-- Key principle: batch ALL items per substep, then move to next substep. -->
<!-- NEVER interleave: generate-one -> process-one -> generate-next. -->

### Step 5a: Prepare <intermediate assets> (batch)

<!-- Transform Step 3 assets into production-ready inputs. -->

For each <item>, prepare its <production input>:
- <How to compose/transform the asset>
- <Key parameter>: `<value>` -- <why this value>

**Batch**: Process ALL items in one call, then proceed to 5b.

### Step 5b: Generate <primary outputs> (batch)

<!-- The main generation pass. -->

Generate <outputs> for all items:
- <Input>: from Step 5a
- <Key parameter>: <value or strategy>

**Model selection**: <Which model/tool to use and why>.

**Duration / size strategy**: <How to handle variable output sizes>:
- <Condition 1> -> <approach>
- <Condition 2> -> <approach>

### Step 5c: Adjust / Post-process

<!-- Fix discrepancies between generated output and target specs. -->
<!-- This step is often the difference between "demo quality" and "production quality". -->

Adjust every output to match its target specification:

#### Case 1: <Output exceeds target> -> <Fix strategy>

<!-- Include specific commands/techniques only when non-obvious. -->

#### Case 2: <Output falls short of target> -> <Fix strategy>

<!-- Explain the technique and WHY it's needed. -->

**Verification**: After adjusting all outputs, verify the total matches expectations.
If drift exceeds <threshold>, fix before proceeding.

### Step 5d: Generate <secondary outputs> (different technique)

<!-- When some items need a fundamentally different generation approach. -->
<!-- Explain WHY this subset uses a different method. -->

For <subset of items>, use <different approach> because <reason>.

**Sub-step 1**: Prepare inputs for this subset.
**Sub-step 2**: Generate in one batch call.
**Sub-step 3**: Post-process to match target specs.


## STEP 6: FINAL ASSEMBLY

<!-- Combine all produced assets into the final deliverable. -->

Assemble the final output:
- <Input 1>: ALL produced outputs in order
- <Input 2>: Original source material (e.g., audio track)
- <Input 3>: Metadata (e.g., credits, annotations)

<!-- Specify the format/structure of metadata if non-trivial. -->


## STEP 7: PRESENT RESULT

Show the final output to the user with a summary:
- <Input summary> (e.g., source info)
- <Production summary> (e.g., asset counts, techniques used)
- <Output path / location>
