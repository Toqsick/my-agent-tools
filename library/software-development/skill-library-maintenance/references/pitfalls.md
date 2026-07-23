# Common Pitfalls — Full List (31 items)

1. **Modifying frontmatter during slim-down.** The YAML frontmatter contains `name`, `description`, `metadata` etc. Subagents may accidentally alter these. Always instruct: "YAML frontmatter stays EXACT as-is."

2. **Creating references/ files that are too small.** A reference file with 5 lines is wasteful. Merge small extractions into a single `references/<topic>.md` instead.

3. **Forgetting to add pointers in SKILL.md.** After extraction, the SKILL.md must link to each new reference file, otherwise agents won't know the detail exists. Add: `→ See references/<file>.md for details`

4. **Not excluding archives from the scan.** `~/.hermes/skills/.archive/` and `duplicates*` directories inflate the scan. Always exclude them.

5. **Delegating without target size.** Without a concrete KB target, subagents underperform. State: "Target: SKILL.md ≤12KB."

6. **Over-extracting small skills.** Skills <15KB don't need slimming. Extracting from them creates unnecessary file sprawl and makes the skill harder to read in one pass.

7. **Keeping both a phase overview table AND per-phase prose subheadings.** Phase-organized skills (e.g. 8-phase pipelines) tempt you to write an overview table with each phase as one row, then add a "Phase 0: Project Setup" subheading below the table with a 4-sentence summary. The prose duplicates the table. Decision: keep the table with one rich-sentence goal per row, drop the prose subheadings. Saves ~1.5-2KB and the table is easier to scan.

8. **Trying to hit a 10KB target when frontmatter+intro is already 4KB.** The realistic floor for a phase-organized skill is 12-15KB, not 10KB. Frontmatter (~2KB) + intro paragraph + ASCII diagram + When-To-Use + Philosophy + Overview table + Common Pitfalls + Hermes integration + Reviewer criteria + External sources adds up to ~12KB of irreducible skim material before any phase content. Below 12KB you start losing skim value; below 8KB the skill becomes a bare index. Communicate this to the user up front: "10KB target → realistic landing 14-16KB; 12KB target → realistic landing 14-16KB."

    **EXCEPTION for cheatsheet-style skills:** A skill whose body is structured as bullet lists, single-line pointers, and tables (rather than prose subheadings) CAN legitimately land near the 12KB target. Verified 2026-07-02: `greyhack-greyscript` slimmed 40,119 → 12,131 bytes in one pass by extracting all >10-line code blocks into references/, condensing function inventories into 2-column tables, and turning verbose prose into single-line pointer bullets. Pitfall #7 (drop redundant prose subheadings) is the lever — table + pointers form replaces prose paragraphs entirely.

9. **Verification of cross-links after restructure.** When slim-down produces many cross-references like `phase5 § Step 5.1`, run a quick loop that resolves every `[text](path)` against the file system before declaring done. Missing references are worse than over-extracted content. The Post-Slim-Down Verification section above gives the one-liner for both the cheatsheet-style bare path form (`references/X.md`) and the full markdown-link form (`text`).

10. **Dangling references discovered during slim-down — CREATE the file, don't delete the link.** When slim-down reveals that a SKILL.md links to `references/<file>.md` that doesn't exist on disk (a common side effect: previous editing left references as forward-looking expectations but never actually created the file), the link is a user-facing expectation. The slim-down protocol should CREATE the referenced file with whatever minimum content the link implies, rather than deleting the broken link. Verified 2026-07-02: `greyhack-greyscript` referenced `references/p0-pattern-reference-2026-06-25.md` which didn't exist; created it with the auto-fix recipes that the surrounding prose described, keeping the SKILL.md link graph intact.

    **ALTERNATIVE: Block-replace with note (better for bulk broken refs).** When the broken refs are inside a "Siehe auch" / "Related" / "Session-Referenzen" bullet-list (no workflow dependency) and there are MANY of them (e.g. 17 in one block), **prefer** the block-replace approach over creating N stub files: a single `> **Note:**` line replaces the whole block, no ghost files, semantically honest about the history. Decision rule:
    - **1-3 broken refs in workflow-linked inline text** → CREATE the file (Pitfall #10 default)
    - **4+ broken refs in pure "Siehe auch" bullet-lists** → block-replace with note (alternative pattern)
    - **Mixed source (some pre-existing, some introduced by subagent)** → block-replace

    Verified 2026-07-02 Skill-Slim-Down mission: 26 broken refs in 2 skills (multi-agent-work: 17, research-paper-writing: 9), all in pure bullet-list form, all fixed via block-replace in 2 single-file edits. Master report at `~/docs/system/skill-slim-down-2026-07-02.md`. Cross-ref: `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` Pitfall #34.

    **Why block-replace wins at scale:** 26 stub files = 26 ghost files forever. 26 inline-edit lines that all read the same `> **Note:**` template = honest documentation of history, no future agents confused by "what's in this stub?". The block-replace is also reversible — if a future session creates the actual content, the bullet-list can be restored.

11. **Bare-path references (`references/X.md`) vs full markdown links (`X`) — pick one form per skill.** Mixing both forms in the same SKILL.md makes the Post-Slim-Down Verification loop need both regexes (see Post-Slim-Down section). Cheatsheet-style skills tend toward bare path ("see `references/X.md`") because it reads as flow-text; tutorial-style skills tend toward full markdown links because they support richer anchors. Standardize on one for the whole skill.

12. **First `write_file` of the slimmed SKILL.md always overshoots the target — plan for 2-3 iterative trim-down rounds.** Writing complete sentences is easier than compressing them. The initial write typically lands 15-25% over target (e.g. 14KB when targeting 12KB). After the initial write, run `wc -c`, identify low-value prose blocks (verbose descriptions, multi-line command examples that can be condensed to one-liners, redundant "See references/X" lines that can be merged), and `patch` them down. Each round removes ~500-800 bytes. Verified 2026-07-02: `hermes-admin` initial write = 14,165 bytes → 3 patch rounds → 12,246 bytes.

13. **Adjacent-region `patch` calls can merge headings with content.** When two simultaneous patches touch nearby regions (e.g. one removes a blank line before a heading, another removes the newline after the same heading), the heading marker can lose its trailing newline and fuse with the content: `## Providers (20+)OpenRouter...` instead of a clean heading + body. **Always re-read affected sections after a batch of patches**, or run patches touching the same region sequentially rather than in parallel.

14. **`skill_manage(action='delete', file_path='references/X.md')` archives the ENTIRE skill, not just the file.** This is catastrophic — the action parameter `delete` operates at the skill level regardless of whether `file_path` is specified. To remove a single reference file, use `skill_manage(action='remove_file', file_path='references/X.md')` instead. If you accidentally archive a skill, you must immediately recreate it via `skill_manage(action='create')` with the full SKILL.md content, then re-create each reference file via `skill_manage(action='write_file')`. The archive copy at `~/.hermes/skills/.archive/<name>/` contains the original files but skill tools cannot read from `.archive/` — you must have the content in your conversation context. Verified 2026-07-02.

15. **Skill-slim-down missions of >5 skills need Multi-Wave Pattern, not single-batch.** When you have more candidates than `max_concurrent_children` (default 5), split into waves. Verified 2026-07-02: 9 skills slimmed in 2 waves (5+4), ~25 min total. Pattern:
    - **Wave 1:** Delegate first 5 in parallel via `delegate_task(tasks=[...])` (BATCH MODE)
    - **Verify Wave 1:** broken-ref check + frontmatter-check + size-check + content-intact
    - **Fix any issues inline** (Pitfall #10 alternative for broken refs, manual patch for broken frontmatter)
    - **Wave 2:** Delegate next batch. Each subagent in each wave gets the SAME briefing template with skill-specific substitutions.
    - **Final verify + master report** combining all waves.

    **Why not just one big batch?** Either: (a) `max_concurrent_children` limits parallelism, (b) sequential 1-by-1 takes 5x longer, (c) parent loses opportunity to catch issues early and re-brief Wave 2 if Wave 1 reveals a pattern.

    Cross-ref: `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §2.

16. **Subagent can leave broken references silently — verify post-wave, don't trust summary.** Even when subagent says "all references intact" in the summary, run the broken-ref check (`grep -oE 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | while read f; do [ ! -f "$f" ] && echo BROKEN; done`) before declaring done. Verified 2026-07-02: 9 skills slimmed, 26 broken refs detected. Only subagent #4 transparently mentioned its broken refs in the summary; the other 8 were silent. The fix is parent-side verification, not relying on subagent honesty.

    **Hardening:** Add this to every slim-down briefing to make broken refs visible in the subagent's own summary:

    ```
    META-CHECK: Before reporting success, run:
      for r in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | sort -u); do
        [ ! -f "$r" ] && echo "BROKEN: $r"
      done
    Report any broken refs in your summary. Parent will fix them — your
    job is to honestly report, not to silently preserve or hide them.
    ```

    Cross-ref: `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §3 (4-Tier Verification).

17. **Re-scan between rounds — top-N candidates change after each slim-down.** A skill that was 45KB two days ago might be 13KB today. Don't reuse last round's candidate list; always re-run the size inventory. Verified 2026-07-03 Skill-Slim-Down Round 2: Round 1 (2026-07-02) slimmed 9 skills from 33-105KB. Round 2 (2026-07-03) immediately targeted the NEXT 10 candidates from the *current* scan (22-29KB), not stale Round 1 data. Each round is a fresh state. The Round-1 candidates are now mostly in the 6-14KB healthy range and should NOT be re-slimmed.

18. **Exclude `multi-agent-pitfalls-cheatsheet` from scan-driven slim-down candidates.** This skill grows by ~5-15KB every time new patterns are added (it's the canonical pattern bank). Treating its size growth as "needs slim-down" would create a feedback loop that erases exactly the patterns we just learned. Add it to the scan **exclusion list** alongside `.archive/` and `duplicates*`. Its size is a feature, not a bug. Verified 2026-07-03.

19. **Stub-File vs Block-Replace — table-column broken refs need stubs, not block-replace.** Pitfall #10 alternative handles bulk broken refs in "Siehe auch" bullet-lists with a single `> **Note:**`. But broken refs **inside Markdown tables** (e.g. a reference column with `| p5.js API | \`references/core-api.md\` |`) cannot be block-replaced without rewriting the whole table — the table structure must be preserved. Decision rule:
    - **Broken refs in bullet-list ("Siehe auch")** → block-replace with single `> **Note:**` (Pitfall #10 alternative)
    - **Broken refs in Markdown tables / inline flow text** → CREATE the file as a stub with TODO-status header

    Verified 2026-07-03 Wave 1: `creative/p5js` had 8 broken refs all in table-column "Reference" cells. Block-replace would have destroyed the table. Solution: 8 stub files (~600-800 bytes each) with `> **Status:** Stub — geplant für Ausbau. Subagent #N (Wave X, DATE) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.` + topic-relevant Quick-Reference. Stubs document the gap, preserve link structure, and provide genuine starter content.

20. **Accept "Subject Index" stubs as legitimate output.** When a subagent says "I created 5 of the 13 needed reference files; the remaining 8 are listed as 'Subject Index' for future expansion", that's NOT failure — it's an honest scoping decision. The slim-down budget (12KB target) couldn't accommodate all 13 extractions; subagent chose the highest-value ones and left TODO pointers. Verify the 5 created files are non-trivial (>500 bytes each) and that the "Subject Index" is honest about being a future-expansion list (not silently broken links). Verified 2026-07-03 p5js: 5 substantive files (sketches.md 3.8KB, performance.md 3.9KB, etc.) + 8 stub/Subject-Index entries.

21. **Subagent honesty calibration — transparent reports are features.** A subagent that reports "I left these 17 references as bullet-list because they had no workflow dependency" or "I created 5 of 8 needed files, see Subject Index section" is showing good judgment, not failure. Don't interpret transparent limitations as incompetence; the parent-side fix is cheap when the subagent honestly reports what it didn't do. Verified 2026-07-02 (subagent #4 on multi-agent-work) and 2026-07-03 (subagent #5 on p5js).

22. **Smaller candidate skills (22-29KB) tolerate less aggressive slimming — target 12KB, not ≤10KB.** Round 1 (2026-07-02) candidates were 33-105KB monoliths where the target could be ≤12KB with huge extraction headroom. Round 2 (2026-07-03) candidates were already healthier (22-29KB) with less extraction headroom. Final landing sizes: 8.6-12.3KB (vs Round 1's 6-14KB). Same protocol works, but realistic target is "around 12KB" not "as small as possible". Communicate this to subagents: "Target: SKILL.md ≤12KB. Landing 12-14KB is acceptable for smaller candidates."

23. **After slim-down, the SKILL.md might briefly exceed its target — verify, don't immediately reject.** Round 2 (2026-07-03) had multiple subagents land at 12.1-12.3KB when target was ≤12KB (12KB = 12,288 bytes technically, 12.0-12.3 KB = 12,288-12,595 bytes). That's within 3% of target and well within healthy skill range. Don't re-spawn subagents for sub-KB overshoots; accept and move on. Re-spawn only when the result is structurally wrong (broken frontmatter, missing content, broken refs).

24. **`head -1` confirms `---` is present; PyYAML confirms it PARSES — different checks.** After slim-down or any patch operation on SKILL.md, the verification checklist above checks `head -1 ... SKILL.md` for the `---` marker. That's a syntactic check (is the frontmatter delimited?), not a semantic one (does it actually parse as YAML?). Subagent or patch operations can leave syntactically-delimited but semantically-broken frontmatter — e.g., an unescaped colon inside a `description:` value, or a list item with a wrong indent, will produce a parse error that `head -1` happily ignores. Pattern that catches this:

    ```python
    import yaml
    with open('SKILL.md') as f:
        parts = f.read().split('---', 2)
    fm = yaml.safe_load(parts[1])  # raises yaml.YAMLError if broken
    print('Keys:', list(fm.keys()))  # confirms expected fields present
    ```

    Verified 2026-07-03 single-skill slim-down: `ollama-local-hosting` 24.8KB → 7.6KB, PyYAML round-trip confirmed all 9 frontmatter keys (`name`, `description`, `version`, `platforms`, `metadata`, `author`, `license`, `lane`, `reasoning_effort`) parsed. Add this to the Verification Checklist below — the existing `head -1` step is necessary but not sufficient.

25. **Partial-extraction case — adding markdown refs to a skill that already has code refs.** The Monolith/Partial/OK table classifies "Partial" as "has references/ already, move more content out", but doesn't give a concrete recipe. Verified 2026-07-03 single-skill slim-down: `hermes-mcp-integration` had `references/{mcp-transport-nodejs-production.js, plugin-registry-nodejs-production.js}` (production *code* references intended for runtime `require()`) and `templates/` (boilerplate), but NO markdown references. The slim-down added 4 markdown references alongside the existing code refs. Pattern:

    - **Don't merge** markdown extractions into existing code-reference files. Production JS in `references/*.js` is for runtime re-use (drop-in `require()`); markdown in `references/*.md` is for agent context. Different audiences, different files. Same directory, distinct semantics.
    - **Link from SKILL.md with one-line pointers** that name the *kind* of reference: "Drop-in `PluginRegistry` + `PluginManifest` production code" (code) vs. "Health-Score pattern with telemetry hook + pitfalls" (markdown).
    - **Keep existing JS/Python reference blocks in SKILL.md untouched.** The slim-down's job is to add markdown refs around them, not to reorganize code refs.
    - **Decision rule:** if a skill's `references/` contains JS/Python code intended for runtime import, leave those files untouched. Extract *prose* content into new markdown files in the same `references/` directory. They coexist cleanly because they serve different consumers.
    - "Skip the file-type prefix convention" that Round-1 patterns assumed (e.g. `mcp-server-setup.md` vs. `plugin-registry-nodejs-production.js`). The filename suffix carries the kind hint implicitly. README structure stays consistent across the directory.

26. **Read the actual source code before extracting technical details — SKILL.md paraphrases are not source-of-truth.** When slimming a skill that documents a *code system* (TypeScript server, Python lib, CLI tool, etc.), the original SKILL.md describes behavior at a high level: function names, conceptual flow, brief snippets. It usually MISSES small but load-bearing details that an experienced engineer would notice:
    - Defensive parses like `parseInt(e.id || '0', 10)` (the `|| '0'` prevents `NaN > N` from silently filtering out the wrong events).
    - Use of `Map` insertion order as LRU (`clients.keys().next().value` IS the oldest — no separate timestamp needed).
    - Cleanup casts like `(client as any)._heartbeat` to attach `setInterval` refs for later `clearInterval`.
    - Invariants like "ID generation must be at the broadcaster, not the writer" — only obvious once you've read `broadcastSSEv2()` and `writeEventToClient()` side-by-side.
    - "Buffer-push runs BEFORE the client broadcast loop" — explains why events still land in the retention buffer when no client is subscribed.

    **Recipe:** Before writing any reference file, run a parallel batch to read the actual source files referenced from SKILL.md's "Files of Interest" section. Use `read_file` (full file is fine for files ≤500 lines) or `search_files` (for specific function bodies). This took ~4 reads in the hermes-v7-sse case (`sse-server-v2.ts`, `rate-limiter.ts`, `auth-gate.ts`, `error-handler.ts`) and yielded 4 reference files that ADD information beyond what the SKILL.md already contained — e.g. ring-buffer-overflow behavior, exact LRU eviction order, the defensive parse in event-ID replay.

    **What you DON'T do:** Don't extract details from SKILL.md into references/ verbatim. That just moves text without adding value. If a reference file could be written without reading any source code, it's probably redundant — the SKILL.md already has it.

    **Verified 2026-07-03:** Single-skill slim-down of `hermes-v7-sse` (23.0KB → 12.0KB). Read `src/api/sse-server-v2.ts` (364 lines), `src/middleware/rate-limiter.ts` (99 lines), `src/middleware/auth-gate.ts` (106 lines), `src/middleware/error-handler.ts` (45 lines) before writing 4 new references totaling 29KB. Each reference contains code blocks, invariants, and trade-offs that did NOT exist in the original SKILL.md.

27. **Compression tactics that actually move bytes — table conversion, row folding, layer prefix-coding.** When the target is tight (12KB), these specific levers reliably remove bytes without losing information:

    - **Prose → table conversion.** Phase-organized prose sections (e.g. "Layer 1: CORS_ORIGINS" with 4 paragraphs explaining symptom/cause/verify/fix) compress to a single 4-column table row (`# | Layer | Symptom | Fix`). The 8-layer section in hermes-v7-sse went from ~3KB prose to ~1KB table while keeping every diagnostic detail. Rule: if the section has parallel structure across N items with the same 3-4 sub-fields each, table it. If sub-fields differ per item, prose it.
    - **Folding similar ENV rows.** When a skill documents 4 rate-limiters each with `_MAX` and `_WINDOW_MS`, fold into one row: `<NAME>_LIMITER_MAX / _WINDOW_MS ×4 (GENERAL, CANARY, SYSTEM, SSE)` with defaults in a single slash-separated value. Don't lose the per-limiter defaults — put them in the "Default" column as `100/30/120/10 per 900000/900000/900000/60000 ms`.
    - **Prefix-code pitfalls by their canonical identifier.** When pitfalls correspond to numbered layers/cases/phases (Layers 5/6/7/8 in the 8-layer pattern), prefix the pitfall bullet with `Layer N —`: `**Layer 6 — fixed-interval reconnect → death-spiral after 429**`. This lets the reader scan for "Layer N" pitfalls quickly AND lets you drop the trailing "See Layer 6" or "See references/X.md" — the prefix is the cross-reference.
    - **Remove redundant "→ see references/foo.md" trailers.** If a row/line already mentions the reference file by name, don't add a separate "Deep-dives → see references/X.md" line at the end of the section. The trailing trailer is meta-navigation noise.
    - **Use bare-path refs consistently within a skill.** Pick one of either ``references/X.md`` (bare path in backticks) or `X` (full markdown link) and use it throughout the skill. Mixing forces the verification loop to use both regexes (see Pitfall #11). Cheatsheet-style skills favor bare paths; tutorial-style skills favor full links.

    **Iteration pattern:** Write the initial slimmed SKILL.md with full sentences. Run `wc -c`. If over target, apply ONE lever per patch round. Check `wc -c` again. Repeat 2-4 rounds. Each lever typically removes 200-600 bytes. Verified 2026-07-03 hermes-v7-sse: 5 patch rounds, starting at 15.4KB and converging to 12.3KB (target ≤12.3KB achieved with 4 bytes to spare).

28. **Wave-Clock-Variance: content-dense skills take 5-10x longer than expected.** When the same N=5 wave uses wildly different wall-clock time across skills, it's almost always because some skills are MORE content-dense (creative-class skills, code-documenting skills) and require proportionally more subagent API calls. Verified 2026-07-03 Round 2: Wave 2 subagent durations were 132s (hermes-mcp-integration), 210s (ollama-local-hosting), **1896s claude-design (80 calls)**, **1757s hermes-v7-sse (42 calls)**, 273s (hermes-v7-sse-server). Wave 2 took **33 min** vs Wave 1's **8 min** for the same N=5.

    **Heuristic for wall-clock estimation:**
    - **Tutorial/Wiki-style skill** (mostly text, minimal code): ~10-25 API calls, ~3-5 min
    - **Creative-class skill** (decision tables, multi-line bullets, prose): ~30-80 API calls, ~10-30 min
    - **Code-documenting skill** (TypeScript/Python source code, complex architecture): ~40-60 API calls, ~25-35 min

    **Plan accordingly:** Round 2's "5+5 parallel" took 41 min wall-clock total, not the 25 min Round 1 took. Communicate timing expectations to the user BEFORE dispatch: "Wave 2 will take ~30-40 min because 3 of the 5 candidates are creative/code-documenting class."

    **Mitigation options if wall-clock is too long:**
    - Split Wave 2 into 2 sub-waves (creative/code-documenting in Wave 2a, others in Wave 2b)
    - Use Parent-Direct for the content-dense skill (saves dispatch overhead, ~30-50% wall-clock)
    - Accept the wall-clock and document it in the master report's "Lessons Learned" section

    Cross-ref: `multi-agent-pitfalls-cheatsheet` v1.1.0 "Smaller-Candidate Tolerance" pattern (R1 learning); see also "Wall-Clock-Variance" entry in `references/round-2-log-2026-07-03.md`.

29. **MD5-Frontmatter-Verifikation is stricter than `diff` for byte-identity checks.** The Post-Slim-Down Verification section uses `sed -n '1,10p' SKILL.md > /tmp/fm.txt && diff <(cat /tmp/fm.txt) <(expected-fm)` for frontmatter byte-identity. This works but `diff` reports line-level differences without cryptographic certainty. For high-confidence verification, MD5-hash the frontmatter:

    ```bash
    head -50 ~/.hermes/skills/<skill>/SKILL.md | grep -A100 '^---$' | sed '/^---$/q' | md5sum
    # Compare against pre-slim hash from git/snapshot
    ```

    Verified 2026-07-03 by hermes-mcp-integration subagent: hash `282410bc...` matched pre-slim hash byte-for-byte. Use MD5 when:
    - Auditing a critical skill where frontmatter drift would silently break skill loading
    - Verifying multi-skill slim-downs where frontmatter drift across many skills is a known failure mode
    - Pre/post comparison where `diff` output would be too noisy (e.g. trailing whitespace, line-ending differences)

    Don't use MD5 for routine verification — `diff` is fine for most cases and more readable when something actually breaks.

    Cross-ref: `multi-agent-pitfalls-cheatsheet` "Skill-Slim-Down Pattern" §"Verifizieren" (R1 pattern, mentions `diff` only — R2 update adds MD5 as stronger alternative).

30. **Pre-Existing-Reference-Audit — distinguish real references from run-artifacts.** When the briefing claims "skill has N reference files", verify N by direct count BEFORE delegating. Sometimes the briefing includes counts that conflate:
    - `references/*.md` — real skill content
    - `memory/runs/*.json` — execution artifacts (NOT skill content)
    - `.archive/duplicates-*/...` — duplicate copies (NOT skill content)

    Verified 2026-07-03 hermes-orchestration: briefing said "63 reference files", actual `references/` count was 7 (+ 56 run-artifacts in `memory/runs/`). Subagent correctly identified the discrepancy and avoided creating duplicate reference files for content that already existed.

    **Heuristic for the parent:**
    ```bash
    # Real reference count
    ls ~/.hermes/skills/<category>/<skill>/references/*.md 2>/dev/null | wc -l
    # vs claimed count in briefing
    ```

    If the briefing claim is wrong, correct it BEFORE dispatching the subagent — the subagent will spend extra calls discovering the discrepancy themselves.

31. **Active-skill integrity snapshot — SHA256 before, not after.** When restructuring the library (deleting duplicates, moving unique skills to new categories), snapshot the active skills' SHA256 hashes BEFORE any destructive operation. This lets you verify post-op that no active skill was accidentally modified:

    ```bash
    # Before any rm/cp/mv
    for path in category/skill-a category/skill-b; do
      sha256sum ~/.hermes/skills/$path/SKILL.md >> /tmp/active_hashes_before.txt
    done

    # After all operations
    for path in category/skill-a category/skill-b; do
      new_sha=$(sha256sum ~/.hermes/skills/$path/SKILL.md | cut -c1-12)
      old_sha=$(grep -F "$path/SKILL.md" /tmp/active_hashes_before.txt | awk '{print $1}')
      echo "$new_sha == $old_sha ? $([ "$new_sha" = "$old_sha" ] && echo '✓ UNCHANGED' || echo '✗ CHANGED')"
    done
    ```

    **Why SHA256, not modification timestamp?** Timestamps can shift from cp operations (`cp -r` changes mtime). SHA256 is content-based and immune to metadata noise.

    **Why snapshot BEFORE not after?** If a destructive operation (rm -rf) goes wrong and corrupts an active skill, a post-only hash has no reference point. The pre-snapshot is the forensic baseline.

    **Trigger:** Any session that modifies the skill library structure (delete, move, rename) — not just slim-downs.

    **Verified 2026-07-04:** 21 skills resolved in hub-imported/ (13 deleted, 8 moved). Active skill hashes (13 targets) all matched pre-op — 0 drift.