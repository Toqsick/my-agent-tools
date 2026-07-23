# GreyHack Build-Fix Session Notes 2026-06-19

Session-specific reference for GreyHack/GreyScript research-to-code handoff.

## Branch policy observed

- `main` must not be touched or merged into without explicit user approval.
- Prefer a feature branch created from `develop` for experiments, even when `develop` itself is allowed.
- User explicitly approved: "`develop` not directly polluted; feature branch from `develop` is einwandfrei."

## P0/P1-P4 priority model

- P0 is the high-priority build/foundation block and comes before P1-P4 research roadmap work.
- P1-P4 are after P0: deeper research, tool candidate specs, knowledge-base/safety taxonomy, and review gates.
- After P0, continue research before implementation unless the user explicitly changes priority.

## GreyScript parser pitfalls encountered

Greybel rejected otherwise plausible code in these forms:

- One-line `if ... then ... end if` blocks containing:
  - `return`
  - assignment statements
  - function calls
- Ternary-style expressions:

```greyscript
prefix = (" d " if e.is_dir else " f ")
```

Normalize to explicit multi-line blocks:

```greyscript
if e.is_dir then
    prefix = " d "
else
    prefix = " f "
end if
```

## File cleanup pitfall

`filecore.src` contained orphan/duplicate blocks and a conflict marker:

- old `filecore` header/import block at top
- incomplete old `safeDelete`/`safeCopy` block before `fc_append`
- `=======` marker

Remove orphan blocks and conflict markers before blaming parser semantics.

## Validation commands

Targeted build:

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build src/filecore.src src/debugcore.src src/tools/recon.src tests/test_filecore.src
```

Expected output ends with:

```text
Build complete: 4 file(s) ok
```

Full active scan signal:

```text
built 5/15 active src/tools files
```

Remaining failures are outside the P0 scope unless the user promotes them.

## CI script fix

A stale `scripts/ci-build.sh` may only check `greybel-js`. Prefer a script that accepts both:

```bash
if command -v greybel-js >/dev/null 2>&1; then
  GREYBEL_CMD="greybel-js"
elif command -v greybel >/dev/null 2>&1; then
  GREYBEL_CMD="greybel"
else
  echo "ERROR: greybel-js/greybel not found. Install with: npm install -g greybel-js" >&2
  exit 127
fi
```
