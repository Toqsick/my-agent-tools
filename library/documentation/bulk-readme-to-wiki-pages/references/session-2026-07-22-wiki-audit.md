# Wiki Coverage Audit — Worked Example (2026-07-22)

**Source:** Subagent H audit run on `/tmp/greyscripts-repo/wiki/` after the
bulk generation of 33 tool pages + Tools-Overview from `greyhack-tools/*/README.md`.

**Result:** 4/5 checks PASS, 1 NEEDS-FIX (6 broken cross-link targets). The
file-count check (Phase 5) passed cleanly but missed the broken links —
exactly the failure mode Phase 6 was added to catch.

## Numbers (the actual audit run)

| Metric | Value |
|---|---|
| Wiki pages | 58 |
| Tool-*.md pages | 33 |
| Verified patterns | 11 active |
| Pattern-*.md pages | 6 category pages + 1 index |
| Central docs | 20 (11 repo + 9 wiki-originals) |
| Cross-links (total) | 386 |
| Cross-links (unique targets) | 62 |
| External links (total) | 153 |
| External links (unique) | 101 |

## Five-check coverage result

| Check | Verdict |
|---|---|
| 1. Tool-Coverage (33/33) | PASS |
| 2. Pattern-Coverage (11/11 active) | PASS |
| 3. Doc-Coverage (11/11 + 5 extras) | PASS |
| 4. Cross-link validation | **NEEDS-FIX** |
| 5. External links (0 broken) | PASS |

## The 6 broken cross-link targets (root cause: snake_case vs kebab-case drift)

| Broken target | Resolves to | Appears in |
|---|---|---|
| `Home` | `INDEX` | `_Sidebar.md:3` |
| `Tool-build_all` | `Tool-build-all` | `INDEX.md:31`, `_Sidebar.md:33` |
| `Tool-fix_perms` | `Tool-fix-perms` | `INDEX.md:31`, `_Sidebar.md:34` |
| `Tool-scp_upload` | `Tool-scp-upload` | `INDEX.md:31`, `_Sidebar.md:37`, `Installation.md:138` |
| `Tool-smtp_enum` | `Tool-smtp-enum` | `INDEX.md:31`, `_Sidebar.md:38`, `Installation.md:162` |
| `Tool-wifi_crack` | `Tool-wifi-crack` | `INDEX.md:31`, `_Sidebar.md:40`, `Installation.md:114` |

**Root cause:** INDEX.md and Sidebar.md were written by a different agent
pass than the per-tool pages. The linker used `snake_case` while the
per-tool pages used `kebab-case`. None of this is visible from `ls | wc -l`.

## The reusable audit commands (copy-paste ready)

### Coverage diff (with normalization)

```bash
# Repo inventory (only folders with .src code)
real_tools=$(for d in /tmp/greyscripts-repo/greyhack-tools/*/; do
  if find "$d" -maxdepth 2 -name "*.src" 2>/dev/null | head -1 | grep -q .; then
    basename "$d"
  fi
done | sort -u)

# Wiki pages (normalized to kebab-case)
wiki_tools=$(ls /tmp/greyscripts-repo/wiki/Tool-*.md \
  | sed 's|.*/||;s|\.md$||;s|^Tool-||;s|_|-|g' | sort -u)

# Coverage diff
comm -23 <(echo "$real_tools") <(echo "$wiki_tools")
# (empty = 100% coverage)
```

### Cross-link extraction + resolution diff

```bash
cd /tmp/greyscripts-repo/wiki/

# Unique cross-link targets (extract text from [Text](Target))
grep -ohE '\]\([A-Za-z][A-Za-z0-9_\-]*\)' *.md \
  | sed 's/^](//;s/)$//' | sort -u > /tmp/wiki-links.txt

# Wiki page names (without .md)
ls *.md | sed 's|.*/||;s|\.md$||' | sort -u > /tmp/wiki-pages.txt

# Broken targets (in links but not in pages)
comm -23 /tmp/wiki-links.txt /tmp/wiki-pages.txt

# For each broken target, show which files contain it
while read t; do
  if ! grep -qxF "$t" /tmp/wiki-pages.txt; then
    grep -lH "]($t)" *.md
  fi
done < /tmp/wiki-links.txt
```

### External link validation

```bash
# 1. GitHub repo links -> check local file existence
grep -ohE 'https://github.com/[^/]+/[^/]+/blob/main/[^)]+' *.md \
  | sed 's|.*/blob/main/||' | sort -u > /tmp/repo-paths.txt

cd /tmp/greyscripts-repo/
while read p; do
  [ -f "$p" ] || echo "MISSING: $p"
done < /tmp/repo-paths.txt
# (empty = all repo URLs valid)

# 2. External domains -> HEAD-request check (exclude GitHub + LAN)
cd /tmp/greyscripts-repo/wiki/
grep -ohE 'https?://[^) ]+' *.md | sed 's/`$//;s/,$//' | sort -u \
  | grep -v 'github.com/Toqsick/greyscripts' \
  | grep -v '^http://192\.168\.' \
  | while read url; do
      status=$(curl -I -s -o /dev/null -w "%{http_code}" -m 10 "$url" 2>/dev/null)
      echo "$status  $url"
    done
# (200/302 = reachable, anything else = broken)
```

## The fix (5-Minuten-Patch)

```bash
cd /tmp/greyscripts-repo/

# Snake-case -> kebab-case in all 3 affected files
sed -i 's/Tool-build_all)/Tool-build-all)/g' \
       's/Tool-fix_perms)/Tool-fix-perms)/g' \
       's/Tool-scp_upload)/Tool-scp-upload)/g' \
       's/Tool-smtp_enum)/Tool-smtp-enum)/g' \
       's/Tool-wifi_crack)/Tool-wifi-crack)/g' \
       wiki/INDEX.md wiki/_Sidebar.md wiki/Installation.md

# Home -> INDEX in Sidebar
sed -i 's/\[Home\](Home)/[Home](INDEX)/' wiki/_Sidebar.md
```

After this patch: re-run the cross-link diff -> expect empty output -> all
checks PASS.

## Lessons captured

1. **Phase 5 is necessary but insufficient.** File-count and style checks
   pass cleanly even when the wiki has 6 broken cross-link targets.
   Phase 6 (cross-link + external-link audit) is required for any
   N >= 20 generation.

2. **Naming drift is the silent failure.** When multiple writer passes
   (per-tool pages vs INDEX/Sidebar/Installation) use different naming
   conventions, the file count is right but the link integrity is wrong.
   Audit must extract every `](Target)` and diff against page names.

3. **Normalization is asymmetric.** Coverage diff (Phase 6.1) MUST
   normalize snake_case <-> kebab-case on both sides. Cross-link resolution
   check (Phase 6.2) MUST NOT normalize -- wiki renderers are
   case-sensitive. Two different operations, two different normalization
   policies.

4. **LAN IPs are intentional in-game references, not broken external
   links.** Always filter `^http://192\.168\.` and document the exclusion.

5. **Audit report -> persistent file.** Write the audit report to
   `wiki/_Audit_Completeness.md` (underscore prefix to sort first) so
   future re-runs can diff against it.