#!/usr/bin/env bash
# plan-mass-audit.sh — Quantitative scan all plans against quality gates
# Part of better-plan-strategy (v0.1.1+)
# Scans every plan in ~/.hermes/plans/, scores it against 6 gates from
# better-plan-strategy's S1-S7 (gates: RealityCheck, SSOT, Effort, Risk,
# Waves, Done), groups by date, and shows the trend.
#
# Usage:
#   bash scripts/plan-mass-audit.sh                    # default: ~/.hermes/plans/
#   PLANS_DIR=~/other/plans bash scripts/plan-mass-audit.sh
#
# Output: date-grouped table + overall stats (stdout, no side effects)
# Requires: python3, bash

set -euo pipefail

PLANS_DIR="${PLANS_DIR:-$HOME/.hermes/plans}"

if [ ! -d "$PLANS_DIR" ]; then
  echo "ERROR: Plans directory not found: $PLANS_DIR" >&2
  exit 1
fi

echo "=== Plan Health Dashboard (Mass-Audit) ==="
echo "Directory: $PLANS_DIR"
echo ""

python3 << 'PYEOF'
import os, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

plans_dir = Path(os.environ.get('PLANS_DIR', os.path.expanduser('~/.hermes/plans')))
if not plans_dir.exists():
    print(f"ERROR: {plans_dir} not found")
    exit(1)

plans = sorted(plans_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)
print(f"Plans found: {len(plans)}")
print()

results = []
for p in plans:
    content = p.read_text(errors='replace')
    mtime = datetime.fromtimestamp(p.stat().st_mtime)
    date_key = mtime.strftime("%Y-%m-%d")

    gates = {
        'S1_RealityCheck': bool(re.search(
            r"Realitäts-Status|Reality-Check|Pre-Plan|Live-Verifik", content, re.I)),
        'S2_SSOT_Table': bool(re.search(
            r"Geplanter Status|Tatsächlicher Status|Brief-Behauptung", content)),
        'S3_EffortEstimate': len(re.findall(r'\d+\s*Min', content)) > 0,
        'S5_RiskSection': len(re.findall(r'^###?\s+R\d+', content, re.M)) > 0,
        'S6_WaveStrategy': bool(re.search(r"Welle|Wave", content)),
        'S7_DoneKriterium': len(re.findall(r'^-\s*\[.\]', content, re.M)) > 0,
    }
    score = sum(1 for v in gates.values() if v)
    results.append({
        'date': date_key,
        'score': score,
        'max_score': 6,
        'gates': gates,
        'name': p.name,
    })

# Group by date
by_date = defaultdict(list)
for r in results:
    by_date[r['date']].append(r)

print("=== Trend by Date ===")
for date in sorted(by_date.keys()):
    entries = by_date[date]
    avg = sum(e['score'] for e in entries) / len(entries)
    max_s = max(e['score'] for e in entries)
    bar = "█" * int(avg * 3 + 0.5)
    print(f"  {date} | avg={avg:.1f}/6 max={max_s}/6 | {bar}")
    for e in entries:
        print(f"    {e['score']}/6  {e['name']}")

print()
print("=== Overall Stats ===")
scores = [r['score'] for r in results]
total = len(scores)
avg = sum(scores) / total
weak = sum(1 for s in scores if s <= 1)
strong = sum(1 for s in scores if s >= 4)
print(f"  Total plans:     {total}")
print(f"  Average score:   {avg:.1f}/6")
print(f"  Strong (≥4/6):   {strong} ({100 * strong // total}%)")
print(f"  Weak (0-1/6):    {weak} ({100 * weak // total}%)")
print(f"  Span:            {results[0]['date']} to {results[-1]['date']}")
print()

# Gate-level breakdown
print("=== Gate Coverage (across all plans) ===")
gate_names = {
    'S1_RealityCheck': 'S1 Reality-Check',
    'S2_SSOT_Table':   'S2 SSOT-Table',
    'S3_EffortEstimate':'S3 Effort Est.',
    'S5_RiskSection':  'S5 Risk Section',
    'S6_WaveStrategy': 'S6 Wave Strategy',
    'S7_DoneKriterium':'S7 Done-Kriterium',
}
for key, label in gate_names.items():
    count = sum(1 for r in results if r['gates'][key])
    bar = "█" * count
    print(f"  {label:18s} {count:3d}/{total} ({100*count//total:2d}%) {bar}")

print()
print("=== Bottom 5 (priority candidates for retro-fit) ===")
sorted_weak = sorted(results, key=lambda r: (r['score'], r['date']))
for r in sorted_weak[:5]:
    print(f"  {r['score']}/6  {r['date']}  {r['name']}")
PYEOF
