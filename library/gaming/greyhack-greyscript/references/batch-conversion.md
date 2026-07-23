# Python Regex Batch Conversion for One-Line Ifs

Bei >20 Funden ist das manuelle Patchen per `patch`-Tool pro Edit zu zeitaufwändig. Stattdessen Python-Regex-Batch-Conversion:

```python
import re, shutil, os

def expand_one_line_ifs(filepath):
    """Expand ALL single-line `if/then/end if` to multi-line blocks in one pass."""
    with open(filepath) as f:
        text = f.read()

    # Pattern 1: Pure one-line-if with `end if` on same line
    pat1 = re.compile(
        r'^(\s*)if\s+(.+?)\s+then\s+(.+?)\s+end\s+if\s*$',
        re.MULTILINE
    )
    def repl1(m):
        indent, cond, body = m.groups()
        body = body.strip()
        if ';' in body:
            lines = [f'{indent}\t{stmt.strip()}' for stmt in body.split(';') if stmt.strip()]
            return f'{indent}if {cond} then\n' + '\n'.join(lines) + f'\n{indent}end if'
        else:
            return f'{indent}if {cond} then\n{indent}\t{body}\n{indent}end if'

    # Pattern 2: One-line-if WITHOUT `end if` — implicit body
    # if cond then body (rest of line is the body, no end if needed)
    pat2 = re.compile(
        r'^(\s*)if\s+(.+?)\s+then\s+(\S+(?:\s+\S+)*?)\s*$',
        re.MULTILINE
    )
    # Deduplicate: skip lines already matched by pat1 (have end if)
    existing = set()
    for m in pat1.finditer(text):
        existing.add(m.start())

    def repl2(m):
        if m.start() in existing:
            return m.group(0)
        indent, cond, body = m.groups()
        body = body.strip()
        if ';' in body:
            lines = [f'{indent}\t{stmt.strip()}' for stmt in body.split(';') if stmt.strip()]
            return f'{indent}if {cond} then\n' + '\n'.join(lines) + f'\n{indent}end if'
        else:
            return f'{indent}if {cond} then\n{indent}\t{body}\n{indent}end if'

    text = pat1.sub(repl1, text)
    text = pat2.sub(repl2, text)

    # Backup + write
    shutil.copy2(filepath, filepath + '.bak')
    with open(filepath, 'w') as f:
        f.write(text)

# Usage
expand_one_line_ifs('yuno_viper_net.src')
```

## Verification after batch conversion

```bash
grep -nE '\bif\b.*\bthen\b.*\bend if\b' file.src          # Should be 0
grep -nE ';\s*if\b' file.src                                # Should be 0
echo "if: $(grep -cE '\bif\b' file.src)"
echo "end if: $(grep -cE '\bend if\b' file.src)"           # end if should have increased
```

## Real-world benchmark

yuno_viper_net.src (553 lines): 79 one-line-ifs converted in ~2 seconds via Python script. 6 additional edge cases (e.g. `if cond then body` WITHOUT `end if` on the same line) needed manual fixing afterward. Total: 85 conversions, 738 line final file, build verified via `greybel build`.

## Edge cases not caught by batch regex (check these manually after conversion)

1. `for/while` combined termination: `if Dp then for Cd in Dp ... end for end if` — the two terminators on one line confuse the `;`-split logic.
2. `;` chains inside then-body: `if cond then statement; next_statement; end if` — the regex splits on `;` but may mis-handle statements that naturally contain `;`.
3. **Nested if inside one-line if**: `if file then tmp = f.get_content; if typeof(tmp) == "string" then old = tmp end if end if` — outer `end if` matches inner `if`'s `end if`, leaving the outer without terminator. **Fix:** expand outer first, then inner separately.
4. **Concurrent sibling subagent edits**: If `delegate_task` spawned agents also refactor the same file, they may insert/delete lines between your patches. Re-read the file before each patch batch. Focus on non-overlapping line ranges. Verify `if`/`end if` balance after EVERY batch, not just at the end.

## Nested `if` inside one-line-if

`if file then tmp = f.get_content; if typeof(tmp) == "string" then old = tmp end if end if`: Expand OUTER `if` first, then the inner `if` separately. Don't try to do both in one edit — the inner `if` references `end if` which gets consumed by the outer expansion.

## Pitfall: Concurrent sibling subagent edits

When `delegate_task` spawns parallel refactoring agents working on the SAME `.src` file, they may insert or delete lines between your patches. This causes `patch` to fail because the `old_string` no longer matches the current file state. **Mitigation:**

- Re-read the file fresh before every patch batch (don't cache `old_string` targets from earlier reads)
- Each patch batch should target non-overlapping line ranges (e.g. one agent handles lines 1-200, another lines 201-400)
- After every batch, re-run the `if`/`end if` balance check. A shift of >expected line-count means a competing edit intruded
- Verify `result.start_terminal` null-check and similar known divergence patterns AFTER all patches land, not during — competing edits may shift the line numbers
- The sibling may also fix one-liner ifs. If the sibling already converted some of your targets, your patch will fail. That's OK — skip and verify balance instead of forcing the edit.

## Real-world case

yuno_viper_scan.src (55 one-liner conversions): A sibling subagent (`sa-1-93602c80`) restructured `dump_lib` calls and moved T2-check logic during the conversion. Mitigation: fresh re-read before each batch, non-overlapping line ranges. All 55 one-liners + `result.start_terminal` null-check landed cleanly. Final verification: 89 `if`/89 `end if` ✅, 0 remaining one-liners.

## Real-world benchmark

yuno_viper_util.src (660→683 lines):
- 6 findings fixed: 3 pure one-line-ifs (Zeilen 242, 389, 569), 2 combined `if/for/end for/end if` (Zeilen 539, 541), 1 nested-if within one-line-if (auch in Zeilen 242/389/569 — jede war ein `if file then tmp=...; if typeof(...)==I.FO then old=tmp end if end if`)
- +23 lines added (660→683)
- Verification pass 1: `grep -nE 'end for end if|if.*;.*then'` → 0 remaining. Pass 2: counter balance check → plausible shift.
- Backup retained: `yuno_viper_util.src.bak-20260704-061358`