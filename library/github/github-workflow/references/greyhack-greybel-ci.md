# GreyHack Greybel CI - Session Reference

Session-specific GreyHack Greybel CI reference for `Toqsick/greyscripts`.

## Issue/PR URLs

- CI Issue #30: Greybel build failures
- CI Issue #43: Lint-yaml failures

## Changed Files

- `.github/workflows/ci.yml` - Added yamllint override
- `scripts/ci-build.sh` - Fixed source directory scanning

## Validation Commands

```bash
# Verify yamllint override
grep -A5 "yamllint" .github/workflows/ci.yml

# Verify build script scans correct dirs
grep "find" scripts/ci-build.sh

# Run local build test
bash scripts/ci-build.sh --out-dir .ci-test
```

## Pitfalls

- Issue tables listed stale paths (`bin/ps.src`) that no longer existed
- Real fixes were in `greyhack-tools/` subdirectories
- `needs:` chain meant greybel-build job was skipped, not failed
- `lint-yaml` was the actual failing job due to missing override