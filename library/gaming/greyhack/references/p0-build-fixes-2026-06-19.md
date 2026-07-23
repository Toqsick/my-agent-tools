# P0 Greybel Build Fixes — 2026-06-19

## Scope

Branch used for experiments:

```text
feat/p0-build-fixes-develop
```

Policy: experimental tool/script changes are allowed on `develop` or a feature branch from `develop`; `main` must not be modified or merged without explicit user approval.

## Files changed

- `src/filecore.src`
- `src/debugcore.src`
- `src/tools/recon.src`
- `scripts/ci-build.sh`

## Root causes fixed

### `src/filecore.src`

- Orphan duplicate old block at the top of the file.
- Second orphan block before `fc_append`.
- Merge conflict marker `=======`.
- Unsafe one-line `if ... then BODY end if` forms.
- Invalid ternary expression:

```greyscript
prefix = (" d " if e.is_dir else " f ")
```

Replaced with:

```greyscript
if e.is_dir then
    prefix = " d "
else
    prefix = " f "
end if
```

### `src/debugcore.src`

- Expanded label-default one-line `if` blocks in assertion/guard helpers:
  - `dc_assert`
  - `dc_assertEq`
  - `dc_assertNull`
  - `dc_assertNotNull`
  - `dc_assertType`
  - `dc_assertNoError`
  - `dc_assertStr`
  - `dc_guard`

### `src/tools/recon.src`

- Expanded one-line `if` blocks in `recon_full`, `recon_lan_full`, and save handling.

### `scripts/ci-build.sh`

- Replaced stale develop-branch build script.
- New script supports:
  - `greybel-js` package name and `greybel` executable.
  - `--out-dir`.
  - Direct `.src` paths.
  - Tool-name resolution from `tools/`, `src/`, or `bin/`.
  - Full active build over `src/` + `tools/`.

## Validation

Targeted P0 build:

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build src/filecore.src src/debugcore.src src/tools/recon.src tests/test_filecore.src
```

Result:

```text
Building 4 GreyScript file(s) into /tmp/greybel-build
  → src/filecore.src -> /tmp/greybel-build/src/build
Build done. Available in /tmp/greybel-build/src/build.
  → src/debugcore.src -> /tmp/greybel-build/src/build
Build done. Available in /tmp/greybel-build/src/build.
  → src/tools/recon.src -> /tmp/greybel-build/src/tools/build
Build done. Available in /tmp/greybel-build/src/tools/build.
  → tests/test_filecore.src -> /tmp/greybel-build/tests/build
Build done. Available in /tmp/greybel-build/tests/build.
Build complete: 4 file(s) ok
```

Full active scan:

```text
built 5/15 active src/tools files
```

Remaining failures outside P0 scope:

- `src/buildcore.src`
- `src/crypto/decypher.src`
- `src/crypto/grsa_v2.src`
- `src/libcore.src`
- `src/netcore.src`
- `src/security/grsa_v2.src`
- `src/security/hardening.src`
- `src/tools/mxwrap.src`
- `src/tools/portmon.src`
- `tools/setup.src`

## System documentation

- `/home/bratan/docs/system/greyscripts-p0-build-fixes-2026-06-19.md`

## Reusable rule

When greybel reports parse errors like `no matching open if block`, `where ")" is required`, or `where number, string, or identifier is required`, inspect for:

1. orphan duplicate code blocks,
2. merge conflict markers,
3. one-line `if ... then BODY end if`,
4. ternary expressions,
5. unclosed `if`/`for`/`while` blocks.
