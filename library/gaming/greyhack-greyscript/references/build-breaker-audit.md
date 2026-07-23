# 5-Build-Breaker Pattern Audit

When a user asks you to scan `.src` files across a project for specific syntax patterns that break the build (e.g. "scan modules for patterns (a)-(e)"), this is a **multi-file structured auditing task**, not a single-file debugging session. Run the scan in this order:

## Trigger

User phrases like "scan all patterns that break the build", "audit for [pattern list]", "find [specific syntax] across modules".

## The 5 build-breaker patterns

| # | Pattern | GreyScript Status | Regex |
|---|---------|-------------------|-------|
| (a) | Einzeilige `if X then Y end if` | ❌ Breaks greybel-js build; in-game GreyScript tolerates it but greybel rejects | `\bif\b.*\bthen\b.*\bend\s+if\b` |
| (b) | Ternary `X if cond else Y` | ❌ NOT supported at all | `\bif\b.*\belse\b` (on same line without `then`) |
| (c) | `\n` statt `char(10)` | ❌ `\n` is literal backslash-n, not newline | `\\n` in string context |
| (d) | Single-quotes `'text'` | ❌ `Invalid character 39` if used in code-strings | `'[^']*'` — **but only flag in code context, not in user-facing print text** |
| (e) | Inline-if assignment `X = (Y if C else Z)` | ❌ NOT supported — same as ternary | `=\s*\(.*\bif\b.*\belse\b` |

## Scan workflow (repeatable across any set of `.src` files)

### 1. Count files first

`wc -l *.src` to scope the effort. Report total lines per file and total lines.

### 2. Run per-pattern scans individually

Independent `search_files` or `grep` calls, batched in parallel. For each pattern, collect:
- Match count per file
- Match content with line numbers
- Classification (pure vs statement-chain for Pattern (a))

### 3. Distinguish pure one-line-if from statement-chain one-line-if (Pattern a)

```greyscript
# Pure one-line-if — single-statement body:
if v == null then v = "[null]" end if

# Statement-chain one-line-if — multi-statement body after ";":
if not ports or ports.len == 0 then warn("Keine Ports"); exit end if

# Statement-chain with assignment before if:
nodes = topo["nodes"]; if typeof(nodes) != "list" then nodes = [] end if
```

Both are build-breaking. The distinction matters for fix-strategy (pure one-line-if needs simple expansion; statement-chain needs careful multi-line refactoring with the `;` split into separate lines).

### 4. Validate clean patterns

For patterns that return 0 results, explicitly report them as ✅ to show they were checked (not skipped). Use `search_files` regex that cross-verify: e.g., `char\(10\)` confirms Pattern (c) is correctly handled, `if.*else` (excluding `else if` chains) confirms Pattern (b)+(e).

### 5. For single-quote detection (Pattern d)

Don't just report the count — classify every match. Print messages (`print(N("[i] Use 'save <NAME>'.", I.FG))`) are legal because the quotes are German typographic convention inside user output. Only flag single-quotes in code strings like `if x == 'value' then`.

### 6. Deliver a structured report

```markdown
## Zusammenfassung
| Pattern | Beschreibung | Funde | Severity |
|---------|--------------|-------|----------|
| (a) | Einzeilige if/then/end if | **N** | 🔴 CRITICAL |
| (b) – (e) | ... | **0** | ✅ OK |

## Pattern (a) — Detail-Report
### file1.src — N Funde
**Zeilen:** L123, L456, L789

### file2.src — M Funde
...
```

## Real-world benchmark (2026-07-04, Yuno Viper modules, 5 files, 3008 lines)

- Pattern (a): 142 findings across 3 of 5 modules (net.src:81, scan.src:55, util.src:6)
- Patterns (b)–(e): 0 findings each (clean)
- 21 single-quote matches → all reclassified as print-messages (✅ OK), 0 code-string violations
- Total scan time: ~30 seconds using batched `search_files` + `grep` calls

Full case study with exact line-level findings: `references/yuno-viper-build-breaker-audit-2026-07-04.md`.