# GreyHack Mini-Tools — 2026-06-19 Reference

**Scope:** Feature-branch implementation pattern for safe GreyHack mini-tools.

## Context

- Repo: `/home/bratan/greyscripts`
- Branch: `feat/p0-build-fixes-develop`
- `main` remained untouched.
- P0 was treated as high priority; P1-P4 were follow-up research/roadmap blocks.

## Implemented tools

- `src/cli_core.src` — CLI/output helpers.
- `src/tools/recon_lite.src` — safe Whois/port recon without `mxwrap` or exploit automation.
- `src/tools/mission_report.src` — mission notes, ports, files, solution/result documentation.
- `tests/test_cli_core.src`
- `tests/test_recon_lite.src`
- `tests/test_mission_report.src`

## Validation command

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build \
  src/cli_core.src src/filecore.src \
  src/tools/recon_lite.src src/tools/mission_report.src \
  tests/test_cli_core.src tests/test_recon_lite.src tests/test_mission_report.src
```

Expected result:

```text
Build complete: 7 file(s) ok
```

## Safety notes

- `recon_lite` intentionally avoids `mxwrap`, exploit automation, payload lists, credentials, and brute-force logic.
- `mission_report` stores local mission documentation only.
- `cli_core` is pure CLI/output formatting.
- In-game runtime tests are still required before any `main` PR.

## Workflow lesson

Use `develop` only as a base and create a feature branch for experiments. Do not take changes into `main` until enough information has been gathered, tests pass, and the user explicitly approves.
