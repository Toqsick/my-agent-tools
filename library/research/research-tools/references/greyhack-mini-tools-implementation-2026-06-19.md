# GreyHack Mini-Tools Implementation Notes (2026-06-19)

Session-specific reference for GreyHack/Awesome-Hacking research that has graduated into GreyScript implementation.

## Branch and priority policy

- `develop` is an experimentation area, but prefer a feature branch created from `develop` for concrete tool work.
- `main` must not be touched or merged into without explicit user approval.
- P0 has priority over P1-P4.
- P1-P4 are research/roadmap/spec work until P0 build foundations are stable.

## Implemented mini-tools

- `src/cli_core.src` — shared CLI/output helpers (`help`, `section`, `kv`, `table`, `require_param`, `bool_flag`).
- `src/tools/recon_lite.src` — safe recon/report tool using whois/router metadata and open ports only; no `mxwrap` or exploit automation.
- `src/tools/mission_report.src` — mission/writeup documentation tool for notes, ports, files, solution/result.
- Tests: `tests/test_cli_core.src`, `tests/test_recon_lite.src`, `tests/test_mission_report.src`.

## Validation command

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build src/cli_core.src src/filecore.src src/tools/recon_lite.src src/tools/mission_report.src tests/test_cli_core.src tests/test_recon_lite.src tests/test_mission_report.src
```

Expected successful output shape:

```text
Building 7 GreyScript file(s) into /tmp/greybel-build
Build complete: 7 file(s) ok
```

## GreyScript parser-safe patterns learned

- Convert one-line `if ... then ... end if` blocks to explicit multi-line blocks when the body contains `return`, assignment, or function calls.
- Rewrite ternary expressions such as `prefix = (" d " if e.is_dir else " f ")` as explicit `if/else/end if`.
- Remove orphan duplicate code blocks and conflict-marker debris before debugging parser errors.
- Ensure build scripts detect both `greybel-js` and `greybel`.

## Safety boundary

Allowed: game-internal recon, mission notes, local report files, CLI formatting.

Not allowed: real exploit chains, CVE/PoC text, credentials, payloads, external network targets, or ported real-world attack tooling.
