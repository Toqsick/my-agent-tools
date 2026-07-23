# Greybel CI Build Verification — 2026-06-19

## What was implemented

P0 CI for `Toqsick/greyscripts` added a local build script and GitHub Actions job:

- `scripts/ci-build.sh`
- `.github/workflows/ci.yml`
- `.gitignore`
- `docs/hermes-automation.md`

Branch/PR:

- Branch: `feat/p0-ci-greybel-build`
- PR: #29 — `feat(ci): add Greybel build verification`

Related issues:

- #27 — Greybel build verification in CI
- #28 — `ci-build.sh` active directory scan
- #30 — Fix Greybel build failures in active `src/` and `tools/`

## Greybel CLI finding

`greybel-js` is installed as an npm package, but the executable name is `greybel`.

Check:

```bash
npx greybel-js --version
PATH="$(npm config get prefix)/bin:$PATH" greybel --version
```

Build syntax for `greybel-js@3.7.12`:

```bash
greybel build <source.src> <output-dir>
```

It writes the compiled output under:

```text
<output-dir>/build/<basename>.src
```

## `ci-build.sh` behavior

Default build scope:

```text
src/**/*.src
tools/**/*.src
```

Do **not** include `greyhack-tools/` by default. Those are imported/stale in this repo and cause CI to fail before active sources are evaluated.

Optional opt-in:

```bash
bash scripts/ci-build.sh --include-greyhack-tools
```

The script supports:

```bash
bash scripts/ci-build.sh --out-dir .ci-build
bash scripts/ci-build.sh --out-dir /tmp/build src/filecore.src tools/portscan.src
bash scripts/ci-build.sh --include-greyhack-tools
```

It prefers `greybel-js` if present and falls back to `greybel`.

## Validation commands

```bash
bash -n scripts/ci-build.sh
bash scripts/ci-build.sh --help
PATH="$(npm config get prefix)/bin:$PATH" bash scripts/ci-build.sh --out-dir /tmp/greybel-ci-build-default
bash .github/workflows/lint-workflows.sh
git diff --check
```

On 2026-06-19, real Greybel verification built 15 active files:

- Passed:
  - `src/cliFeedback.src`
  - `tools/portscan.src`
- Failed: 13 files due to existing GreyScript syntax/source issues.

## Common failure pattern

`greybel-js@3.7.12` rejects one-line `if ... then ... end if` constructs, e.g.:

```greyscript
if label == null then label = src end if
```

Minimal reproduction:

```bash
npx greybel-js@3.7.12 greybel build /tmp/grey-test.src /tmp/grey-test-out
```

Expected error shape:

```text
Build error: no matching open if block at ...
```

## CI expectation

The new CI job is intentionally fail-fast for active source build failures. It should not be weakened to green-pass stale sources; instead, fix active `src/` and `tools/` under #30.
