# Basti's Formatting Rules — Humanization Constraints

> Collated 2026-07-13 from two sessions: Daily Note humanization (2026-07-03.md) +
> Humanizer-Skill self-audit results (22 Em-Dashes, 65 Boldface, 25 Inline-Headers).

## Mandatory Checks Before Delivery

Every Daily Note, Report, Memo, or humanized text MUST pass these grep checks
BEFORE being reported as done. The user must see the verification output in the
chat before we move on.

### Quick-Check Table

| Rule | Target | Shell Command |
|------|--------|--------------|
| Em-Dashes (—) | ≤1 total (0 OK; 1 only in title or wiki-link) | `grep -c '—' file.md` |
| Mid-sentence Boldface (`**word**` preceded by non-whitespace) | 0 (code in tool-lists OK) | `grep -nP '(?<=\S)\*\*[^*]+\*\*' file.md` |
| Inline-Header Bullet-Listen (`-**Title:** content`) | 0 | `grep -cP '^- \*\*[A-Z]' file.md` |
| "kein X nötig" | 0 | `grep -cP 'kein \w+ nötig' file.md` |
| Negative Parallelism ("nicht nur X, sondern Y") | 0 | `grep -cPi 'nicht \w+, (sondern\|aber)' file.md` |
| AI-Vokabeln (crucial/pivotal/delve/showcase/tapestry/seamless/holistic/comprehensive) | 0 | `grep -ciP '\b(crucial\|pivotal\|delve\|showcase\|tapestry\|leverage\|seamless\|holistic\|comprehensive)\b' file.md` |

### Workflow

1. **Rewrite** → meet all formatting rules
2. **Grep** → run all 6 checks
3. **Fix** → any red → fix → go to step 2
4. **Verify** → green → proceed
5. **Report** → show test results IN the chat BEFORE saying "done"

### Traps & Edge Cases

- **Inline-Header trap:** `^- \*\*[A-Z]` misses mid-line boldface labels
  (e.g. `**L1:**` in the middle of a bullet). Always visual-scan the file after
  the grep says green. Counter-check: `grep -cP '\*\*' file.md` — if result > expected
  heading count, boldface lurks somewhere.
- **Em-Dash in code blocks:** `grep -c '—'` counts em-dashes in code fences too.
  If the file has code samples with dashed parameters, subtract those manually.
- **"Selbst-Tests vor Self-Report"** — this is an explicit user instruction
  from 2026-07-13. NEVER skip the report-before-done sequence.

## Source

Established in the 2026-07-13 session:
- Task: humanize `2026-07-03.md` with rules: 0 mid-bold, ≤1 em-dash, 0 inline-header
- Initial output had 16 em-dashes, needed 2 fix cycles (rewrite → grep → fix → grep → done)
- User explicitly wrote "Selbst-Tests vor Self-Report" as part of the task definition