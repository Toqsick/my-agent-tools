# GreyScript Bug Patterns — 2026-06-17 Round 4

New patterns discovered during automated scan of files 51–60 (backup copies, unique files not previously scanned).

> **Note on backups**: These files are from `backups/20260612_003843/` and `backups/20260612_023613/`.
> The bugs documented here exist in the active files too (already reported in earlier rounds).
> The patterns themselves are new additions to the catalog.

---

## NP-37: Wrong Type Check -- `is_binary` Used as Folder Detector

**Severity:** HIGH -- Misclassifies directories, causing skipped files or wrong error messages

`is_binary` checks whether a file's content is binary (true) or text (false). It does NOT
indicate whether a path is a file or a directory. Since directories also return `is_binary == true`,
using `is_binary` as a folder check produces false positives.

**Affected files:**
- `ransomeware/ransomeware.src:105` -- `if folder.is_binary then processFile(folder, ...)`
- `scp_upload/scp_upload.src:83` -- `if remoteDirObj.is_binary then fail("not a folder")`

```grey
# BEFORE (wrong -- is_binary doesn't detect folders):
if folder.is_binary then
    processFile(folder, mode, pass)
    return
end if

# AFTER (correct -- skip binaries, process text):
if f.is_binary then
    return
end if
```

---

## NP-38: chmod Only Applied to Target, Not to Contents

**Severity:** MEDIUM -- Files inside folder retain original permissions

**Affected file:** `ransomeware/ransomeware.src:150`

```grey
# BEFORE (only locks the folder):
lockResult = target.chmod("o-wrx", 1)

# AFTER (recursive -- lock contents too):
lockFolder = function(folder)
    for f in folder.get_files
        f.chmod("o-wrx", 1)
    end for
    for sub in folder.get_folders
        lockFolder(sub)
    end for
end function
target.chmod("o-wrx", 1)
if not target.is_binary then lockFolder(target)
```

---

## NP-39: Overly Complex Padding Logic

**Severity:** LOW -- O(n²) where O(1) string multiplication suffices

**Affected file:** `xmem/xmem.src:138-144`

```grey
# BEFORE:
add_space = []
for i in range(nbspace-1)
    add_space.push("_")
end for
return_string = add_space.join(" ").replace("_", "")

# AFTER:
return " " * nbspace
```

---

## NP-40: No Null Check on `pc.File()` Before Method Chain

**Severity:** HIGH -- Crash if path doesn't exist

**Affected file:** `alias-cli/alias.src:69-70`

```grey
# BEFORE:
l0 = list_map(@get_file_name, pc.File(paths[0]).get_files)

# AFTER:
binDir = pc.File(paths[0])
if not binDir then fail("Not found: " + paths[0])
l0 = list_map(@get_file_name, binDir.get_files)
```

---

## NP-41: Recursive User Input Without Retry Limit

**Severity:** MEDIUM -- Stack overflow risk

**Affected file:** `xmem/xmem.src:180-185`

```grey
# BEFORE:
ShellConnect = function(result, ...)
    ...
    ShellConnect(result, ...)  # unlimited recursion
end function

# AFTER:
ShellConnect = function(result, ..., retries = 0)
    if retries >= 3 then return
    ...
    ShellConnect(result, ..., retries + 1)
end function
```

---

## Summary Table

| ID | Pattern | Severity | Files |
|----|---------|----------|-------|
| NP-37 | Wrong type check: `is_binary` as folder detector | HIGH | ransomeware.src:105, scp_upload.src:83 |
| NP-38 | chmod only on target, not contents | MEDIUM | ransomeware.src:150 |
| NP-39 | Overly complex padding (array+join+replace) | LOW | xmem/xmem.src:138-144 |
| NP-40 | No null-check on `pc.File()` before method chain | HIGH | alias-cli/alias.src:69-70 |
| NP-41 | Recursive input without retry limit | MEDIUM | xmem/xmem.src:180-185 |
