# `import_code` Absolute-Path to Relative-Path Fix (2026-07-07)

## Problem Statement

In a multi-tool GreyHack repo where each tool imports shared libs (e.g. `lib_core`),
a common build-failure pattern arises: source `.src` files use **absolute in-game paths**
like `import_code("/home/Bratan/bin/lib_core")` instead of repo-relative paths. When you
try to build the project via `greybel build -dbf` (offline, no game state) the compiler
fails with:

```
Build error: Dependency <absolute-path-rewritten-as-rel-path> does not exist...
```

The root cause: **greybel resolves all `import_code` paths — even absolute-looking
strings — relative to the source file's directory**, then fails if the file isn't there.

## The greybel Path-Resolution Rule (Critical Gotcha)

Empirically verified 2026-07-07 with greybel-js v3.7.x:

| Input in `.src` | greybel interprets as | Resolves to (example) |
|---|---|---|
| `"/home/Bratan/bin/lib_core"` | relative path | `<src-file-dir>/home/Bratan/bin/lib_core` |
| `"../lib_core/lib_core.src"` | relative path | `<src-file-dir>/../lib_core/lib_core.src` |
| `"lib_core.src"` | relative path | `<src-file-dir>/lib_core.src` |

There is **no** "absolute filesystem path" interpretation for absolute-looking strings —
greybel always treats them as relative to the source file's directory. This is why
absolute in-game paths (which are meaningful at runtime in GreyHack) break the offline
build entirely. In-game, the file `/home/Bratan/bin/lib_core` resolves via the
game's virtual filesystem; in greybel, there's no `/home/Bratan/bin/` to find it in.

### Implication: the installer/`subdir-imports` gotcha

A file like `installer/master_installer.src` cannot use `import_code("lib_core.src")`
because greybel will look in `installer/lib_core.src` (the source file's directory).
Repo-Libs at the repo root require a `../` prefix:

```greyscript
// ❌ Resolves to installer/lib_core.src — does NOT exist
import_code("lib_core.src")

// ✅ Resolves to ../lib_core/lib_core.src — exists at repo root
import_code("../lib_core/lib_core.src")
```

## The 3-Group Fix Strategy

When fixing a batch of `import_code` absolute-paths, classify each file into one of 3
groups based on whether the target library already exists in the repo:

### Group 1: Target exists at repo root (e.g. `lib_core/lib_core.src`)

Tool lives at `greyhack-tools/<tool>/<tool>.src`. Repo-root lib lives at
`greyhack-tools/lib_core/lib_core.src`.

```diff
- import_code("/home/Bratan/bin/lib_core")
+ import_code("../lib_core/lib_core.src")
```

One-line sed/find-replace fix. No new files needed.

### Group 2: Target exists in a sibling subdir (e.g. `minitest/libs/listLib.src`)

Tool lives at `greyhack-tools/minitest/minitest.src`. Targets live at
`greyhack-tools/minitest/libs/listLib.src` and `greyhack-tools/minitest/manager.src`
(both already in repo, no stubs needed).

```diff
- import_code("/home/guest/minitest/libs/listLib.src")
- import_code("/home/guest/minitest/manager.src")
+ import_code("libs/listLib.src")
+ import_code("manager.src")
```

The relative path is relative to the tool's own directory, NOT the repo root.

### Group 3: Target does NOT exist in repo (e.g. `/root/deadlockbuild/libs/chat.src`)

Two-step fix:

1. **Create a minimal stub** in the tool's own directory (or a sibling) with only the
   symbols the importing file actually uses. Stub size: ~10-20 lines.

```greyscript
// chat.src — minimal stub
Chat = {}
Chat.init = function()
    // no-op stub for repo build
end function
```

2. **Rewrite the import** to point at the stub:

```diff
- import_code("/root/deadlockbuild/libs/chat.src")
+ import_code("chat.src")
```

**Stub philosophy:** Minimum to make greybel resolve the dependency. Stub functions
should return sensible defaults (null, empty list, etc.) so the build succeeds. Real
runtime behavior comes from the in-game install, not the stub.

### Group 4: Installer with relative paths but wrong directory

A pre-existing mistake: someone already changed `import_code("lib_core.src")` to a
relative path but the file is in `installer/master_installer.src` (a subdirectory).
The path is wrong because greybel resolves to `installer/lib_core.src`.

**Fix:** Add `../` prefix. Applies to every entry in the installer's import list.

## The Verification Loop

After applying fixes, verify every affected file builds. The batch verification
script is at `scripts/verify_greybel_builds.sh`:

```bash
cd /home/bratan/10-Projekte/10-active/greyhack-tools
./scripts/verify_greybel_builds.sh \
  greyhack-tools/backdoor/backdoor.src \
  greyhack-tools/chat-app/ChatInput.src \
  greyhack-tools/installer/master_installer.src
# Output: ✅/❌ per file + summary
```

**Pass criterion:** Build exits cleanly (no stderr) AND the build directory contains
the expected `lib_core/lib_core.src` (or other dependency) as a resolved file. This
proves the dependency was found and inlined — not just that the file compiled.

## The Batch Fix Workflow (Proven Recipe, 14/14 in 1 Session)

```bash
# 1. Backup all affected files with a wave-specific suffix
cd greyhack-tools && STAMP=$(date +%Y%m%d-%H%M%S)
for f in backdoor/build_all/.../greetings.src; do
  cp -p "$f" "$f.bak-agent-g-$STAMP"
done

# 2. Apply fixes (group-by-group)
#    - Group 1: sed 's|import_code("/home/Bratan/bin/lib_core")|import_code("../lib_core/lib_core.src")|'
#    - Group 3: write_file for each stub, then patch the import
#    - Group 4: sed 's|import_code("|import_code("../|' for installer/*

# 3. Verify all builds in one batch
cd .. && ./scripts/verify_greybel_builds.sh <all-14-files>

# 4. Confirm resolved dependencies in build directories
find /tmp/build-<wave>/<tool>/build -type f | head -20
```

## Pitfalls (Hard-Won Lessons)

### P1: Backup suffix matters in a multi-wave setup

If the repo already has backups from prior waves (`.bak-20260707-095031`,
`.bak-20260707-095447`), use a wave-identifiable suffix like
`.bak-agent-g-20260707-101902`. This makes rollback and diff comparison trivial
without confusing old backups with new ones.

### P2: Forgetting the `../` in installers/subdir-relative files

It's tempting to write `import_code("lib_core.src")` thinking "the project root has
lib_core.src — that's relative." But greybel doesn't know "project root" — it
knows "the directory of the file containing the import." Always check:

```bash
# Worst case: test from the file's directory
cd greyhack-tools/installer && greybel build master_installer.src /tmp/x -dbf -si
# If you see "Dependency installer/lib_core.src does not exist", you need ../.
```

### P3: Strings (not calls) inside `manager.src` are NOT resolved at build time

In the minitest case, `manager.src` contains:

```greyscript
MiniManager.prepend.push("import_code("""+MiniManager.instalation_path+"/libs/listLib.src"")")
```

This is a **string** that gets concatenated to source code at runtime — not an actual
`import_code` AST node. greybel ignores it during build. So fixing the entry-point
file (`minitest.src`) is sufficient for build-resolution. Runtime execution would
still need the in-game paths to resolve, but that's outside the build-fix scope.

If you want belt-and-suspenders correctness, also fix the strings — but expect the
build to pass without it.

### P4: Stubs should be minimal, not full re-implementations

When creating stubs (Group 3), export only the symbols the importing file uses.
Reasoning: stubs are scaffolding for build-resolution, not runtime-correctness
fixtures. The real behavior comes from the in-game deployment. A 12-line stub beats
a 200-line re-implementation because:

1. Less code to maintain
2. Fewer surfaces for the real lib to drift from
3. Build-verification is faster (less inlined code)

### P5: `greybel build` resolves relative paths via filesystem, not stub-source

If you write a stub at `chat-app/chat.src` and use `import_code("chat.src")` from
`chat-app/ChatInput.src`, greybel finds `chat-app/chat.src` on the real filesystem
(within the repo checkout). It's not looking for `chat.src` "as if ChatInput.src were
in some install location" — it's the literal file path on disk. This means:

- Don't put stubs in `/tmp/` — they must live in the repo
- Stub filename must match the import string exactly
- Casing matters if the filesystem is case-sensitive (Linux)

## The Conversation That Produced This Pattern

14 GreyScript files were failing `greybel build` with `Dependency ... does not exist`
errors. Root cause: absolute in-game paths in `import_code` directives that greybel
silently reinterprets as relative to the source file. The 14-file fix landed in
~12 tool calls with 100% build success and produced `/tmp/fix-report-agent-g.md` as
the structured output.

The agent (Agent G) worked in a multi-wave setup alongside other agents (Queen,
parallel A/B/C/...). Wave-2 backups used `.bak-agent-g-$STAMP` to avoid colliding with
prior wave backups. This isolation pattern matters when several agents share the same
repo checkout.

## Cross-References

- `scripts/expand_one_line_ifs.py` — Different category of fix (Pattern (a) one-line ifs),
  but the same backend (greybel). Run before this fix if a file has both patterns.
- `scripts/verify_greybel_builds.sh` — Re-runnable batch verifier, accepts N file
  paths, runs `greybel build -dbf -si` on each, prints pass/fail summary.
