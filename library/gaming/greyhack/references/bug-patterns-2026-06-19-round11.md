# Bug Patterns 2026-06-19 Round 11 — Deep Grep Scan

**Systematic grep-based pattern discovery for patterns NOT in BUG-PATTERNS.md**

## Method

1. Read existing BUG-PATTERNS.md (2101 lines, 61 categories)
2. Run targeted grep scans for undocumented patterns
3. Verify each finding is genuinely new (not in existing categories)
4. Document with examples, affected files, and detection commands

## New Patterns Found

### NP-63: `range(0, x.len - 1)` Off-by-One

**Schweregrad:** HOCH

In GreyScript, `range(a, b)` produces values from `a` to `b-1`. Therefore
`range(0, x.len - 1)` produces `0..x.len-2`, skipping the last element.

**Differs from NP-54:** NP-54 covers the empty list edge case (`range(0, -1)`).
NP-63 is the general off-by-one error in non-empty list iteration.

**Affected files (15+):**
- `grsa/grsa.src:133,143` — RSA encryption/decryption skips last character
- `decypher/decypher_v2.src:48`, `decypher/decypher_v3.src:65` — last entry not decrypted
- `parse-exploit-reqs/parseExploitReqs.src:4,22,33` — last exploit/requirement skipped
- `bltings/bltings.src:116,183,463,468` — applyFunction, GCF, Base64 skip last element
- `lib_core.src:250`, `includes/networking.src:9,62`, `includes/ftzi_std.src:533`

**Detection:** `grep -rn 'range.*\.len.*-.*1' --include="*.src" ~/greyhack-tools/ | grep -v '/backups/'`

### NP-64: `map.count` Returns String Length, Not Occurrence Count

**Schweregrad:** MITTEL

`bltings.src:76-77`: `map.count(item)` returns `str(self[item]).len` — the
string length of the value, not the count of occurrences.

**Affected:** `bltings/bltings.src:76-77`

**Detection:** `grep -rn 'map\.count.*function' --include="*.src" ~/greyhack-tools/`

### NP-65: `list.applyFunction` Off-by-One

**Schweregrad:** MITTEL

`bltings.src:115-119`: `list.applyFunction` uses `range(self.len - 1)`, skipping
the last element when applying a transformation function.

**Affected:** `bltings/bltings.src:115-119`, `parse-exploit-reqs/parseExploitReqs.src:30` (caller)

**Detection:** `grep -rn 'applyFunction' --include="*.src" ~/greyhack-tools/`

### NP-66: `.join("char(10)")` String Literal Instead of Newline

**Schweregrad:** MITTEL

`ps.src:73`: Uses `.join("char(10)")` — joins with the literal string `"char(10)"`
instead of a newline character `char(10)`.

**Affected:** `ps/ps.src:73`, `bin/ps.src:62`

**Detection:** `grep -rn 'join.*"char(10)"' --include="*.src" ~/greyhack-tools/`

### NP-67: `show_procs` Split Result Indexed Without Length Check

**Schweregrad:** MITTEL

`ps.src:24-28`: Directly accesses `line[2]` and `line[3]` after splitting
`show_procs` output without checking if the line has enough elements.
Contrast with `htop/script.src:32` which has proper length guards.

**Affected:** `ps/ps.src:24-28`, `bin/ps.src:24-28`

**Detection:** `grep -rn 'show_procs.*split' --include="*.src" ~/greyhack-tools/`

## Master Detection Grep Commands

```bash
cd ~/greyhack-tools

# NP-63: Off-by-One range
grep -rn 'range.*\.len.*-.*1' --include="*.src" | grep -v '/backups/'

# NP-64: map.count definition
grep -rn 'map\.count.*function' --include="*.src"

# NP-65: applyFunction
grep -rn 'applyFunction' --include="*.src"

# NP-66: join char(10) literal
grep -rn 'join.*"char(10)"' --include="*.src"

# NP-67: show_procs split
grep -rn 'show_procs.*split' --include="*.src"
```
