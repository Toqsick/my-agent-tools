# Build Pipeline CI Quirks — greybel flag effects

**Session:** Multi-Agent Orchestration Review 2026-06-19
**Branch:** `feat/p0-build-fixes-develop`

## The `-u` (uglify) flag and parser strictness

`greybel build` without `-u` uses a **stricter parser** than with `-u`. This manifests as:

| Build command | Parser strictness | Catches `if/end if` mismatch? |
|--------------|-------------------|-------------------------------|
| `greybel build file.src -u` | Lax | May pass with bugs |
| `greybel build file.src -u -dbf` | Lax | May pass with bugs |
| `greybel build file.src` (no flags) | Strict | Catches them |
| `greybel build file.src target/` | Strict | Catches them |

**Real-world impact:** On the `feat/p0-build-fixes-develop` branch, running the CI script (`scripts/ci-build.sh`) which builds WITHOUT `-u` caused **10/18 files** to fail with `no matching open if block`, even though all 18 files built clean with `greybel build -u -dbf`.

### Root cause

Files that have `if ... then action \n end if` (multi-line form with `end if`) are fine under both modes. But files with the **wrong pattern** — single-line `if cond then action` followed by an extra `end if` — pass with `-u` but fail without it because the stricter parser catches the mismatched block.

### Recommendation

The CI build script should build **both ways** — once with `-u -dbf` for the lenient check (what the game's actual runtime sees) and once without `-u` for the stricter syntax verification. This catches latent `if/end if` mismatches before they cause subtle runtime issues.

## CI script (`scripts/ci-build.sh`) notes

The script uses `greybel build "$src" "$target_dir"` — no `-u` or `-dbf` flags.

- **Without `-dbf`:** output goes into a `build/` subdirectory under `$target_dir`, which the current code doesn't expect.
- **Without `-u`:** stricter parsing catches more bugs (see above), but also blocks the build on files that work fine in-game.

**Fix candidate:**
```bash
# In build_file():
# Try strict first, fall back to lax:
"$GREYBEL_CMD" build "$src" "$target_dir" 2>/dev/null || \
  "$GREYBEL_CMD" build "$src" "$target_dir" -u -dbf
```

Or use separate strict/lax build passes in CI.

## Build order

The two-tier dependency chain:

1. **Tier 1 (no dependencies):** `lib_core`, `cli_core`
2. **Tier 2 (import lib_core):** `debugcore`, `filecore`, `cliFeedback`
3. **Tier 3 (import filecore + cli_core):** `recon_lite`, `mission_report`, `recon`
4. **Tier 4 (other dependencies):** `netcore`, `mxwrap`, `portmon`

greybel follows `import_code()` automatically during build, so building any file pulls in its dependencies — no manual ordering needed beyond ensuring the dependency exists at the expected relative path.

## `-dbf` (disable build folder) output behavior

With `-dbf`, greybel writes the compiled output directly into the target directory WITHOUT wrapping it in a `build/` subfolder.

Without `-dbf`:
```
greybel build src/cli_core.src .ci-build/src/
→ Output: .ci-build/src/build/cli_core    (wrapped in build/)
```

With `-dbf`:
```
greybel build src/cli_core.src -dbf
→ Output: ./cli_core    (in current directory, no build/ subfolder)
```