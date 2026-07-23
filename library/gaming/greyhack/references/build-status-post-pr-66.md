# Build Status post-PR-#66 (2026-07-22)

**Stand:** 2026-07-22 nach PR #63 (Starter-Kit), #66 (Pattern-Governance),
#67 (Batch 2), #68 (Quality Hardening), #77 (Wiki Initial).

**Working-Tree:** `/home/bratan/ZCodeProject/greyscripts` auf Branch
`modernize/python-and-guards` (lokal aktiv, kein PR).

## Branch-Übersicht

| Branch | Status | Inhalt |
|--------|--------|--------|
| `main` | sauber | enthält #60-#68, #77 (Pattern-Governance, Wiki, Quality-Hardening) |
| `develop` | sauber | enthält #63 (Starter-Kit), folgt `main` |
| `feature/starter-kit-2026-07-14` | MERGED | war am 14.07. aktiv, jetzt in `develop` |
| `modernize/python-and-guards` | LOKAL | 3 frische Commits: `_LIBCORE_LOADED`, `_extract.py`, `greysync.py` |
| `refactor/2026-07-05-cleanup` | MERGED-IN | xmem-Branch-Merge-Gap ist geheilt |

## Build-Status-Tabelle

| Komponente | Status | Pattern | Quelle |
|------------|--------|---------|--------|
| `src/core/buildcore.src` | ✅ buildable | Pattern | PR #60 (debug-cycle), Imports-Guard #1717812 |
| `src/core/filecore.src` | ✅ buildable | Pattern | PR #60, Imports-Guard #1717812 |
| `src/core/netcore.src` | ✅ buildable | Pattern (validated-IP) | PR #60, API-Fix #61 |
| `src/core/libcore.src` | ✅ buildable | Pattern | PR #60 |
| `src/core/cli_core.src` | ✅ buildable | Pattern (cli-output, cli-table) | PR #60, #66 |
| `src/core/debugcore.src` | ✅ buildable | Pattern | PR #60 |
| `src/recon/recon.src` | ✅ buildable | Bug-Fixes BUG-RC-01..03 | PR #60, Imports-Guard #1717812 |
| `src/recon/recon_lite.src` | ✅ buildable | Recon-Lite Fix (Timestamp) | PR #68, Imports-Guard #1717812 |
| `src/recon/mission_report.src` | ✅ buildable | Imports-Guard | #1717812 |
| `src/crypto/decypher.src` | ✅ buildable | 3 inline-ternary Fixes | PR #60 |
| `src/security/hardening.src` | ✅ buildable | BUG-HD-01..03 + list_children/chmod_recursive als Pattern | PR #60, #66 |
| `src/security/grsa_v2.src` | ✅ buildable | BUG-GRSA-01..03 + n<=255 als Pattern | PR #60, #66 |
| `src/tools/suid_exploit.src` | ✅ buildable | BUG-PS-01/02 + suid_scan_local als Pattern | PR #60, #66 |
| `src/tools/portmon.src` | ✅ buildable | BUG-PM-01/02 + Imports-Guard | PR #60, #1717812 |
| `src/tools/mxwrap.src` | ✅ buildable | BUG-MX-01/02 + Imports-Guard | PR #60, #1717812 |
| `tools/setup.src` | ✅ buildable | BUG-ST-01 | PR #60 |
| `tools/portscan.src` | ✅ buildable | BUG-PS-01/02, Mock-safe Port-Property-Guards | PR #60, #63 |
| `tools/greysync.py` | ✅ argparse-subparsers | Modernize | #9dab76c |
| `greyhack-tools/docs/_extract.py` | ✅ real CLI | Modernize | #5bebfe8 |
| `greyhack-tools/xmem/xmem.src` | ✅ buildable | Branch-Merge-Gap GEFIXT | zwischen #66 und #77 |
| `greyhack-tools/yuno_bootstrap.src` | ✅ buildable | Starter-Kit | PR #63 |
| `greyhack-tools/yuno_localrecon.src` | ✅ buildable | Starter-Kit | PR #63 |
| `greyhack-tools/yuno_nscan.src` | ✅ buildable | Starter-Kit | PR #63 |
| `greyhack-tools/controlcenter.src` | ✅ buildable | Starter-Kit | PR #63 |
| `greyhack-tools/uicore.src` | ✅ buildable | Starter-Kit | PR #63 |
| `greyhack-tools/configcore.src` | ✅ buildable | Starter-Kit | PR #63 |

## In-Game Start-Chain (post-PR-#63)

```
yuno_bootstrap        → First-Run Layout Check + Tool-Chain Anzeige
yuno_localrecon       → Host-Inventur (Users, Libs, Ports, Bin)
yuno_nscan            → Portscan IP/LAN/local mit Mock-safe Port-Property-Guards
hardening_audit       → File-Permissions + SUID-Scan
controlcenter         → Terminal-Hauptmenü, Themes, key=value-Persistenz
  oder yuno_v6        → Full-Feature-Frameworks (Theme, Macros, multi-instance)
```

## Wiki-Status (PR #77)

65 Pages initial aus dem Repo-Stand extrahiert. +6.129 Zeilen, 66 Files,
0 Deletions, 0 broken Cross-Links.

**Cross-Layer zu beachten:** Vault-Notes (`05 Ressourcen/System-Doku/GreyHack/`)
+ Repo-Wiki sind jetzt zwei Layer. Stale-Check muss beide prüfen.

## CI-Pipeline

- **`make check-all`** — Single-Source-of-Truth für Pattern-Governance
  - check-doc-links, check-meta, check-naming, check-pattern-layout,
    check-verified-index
- **`pytest -q`** — 9 Tests in `tests/test_src_regressions.py`
- **`bash scripts/ci-build.sh --dry-run`** — Build-Dry-Run
- **`bash scripts/ci-build.sh`** — Full-Build (83/83 OK nach PR #68)

## Pitfall-Hinweise

1. **`git branch --show-current` VOR Build-Status-Tabelle.** Branch-Merge-Gaps
   sind real (xmem-Case 9+ Tage unentdeckt).
2. **PR-Merges via `gh pr list` verifizieren**, nicht nur lokal.
3. **Wiki-Stale-Check beide Layer** (Vault + Repo-Wiki).
4. **`make check-all` als lokaler Quality-Gate** statt einzelner Scripts.