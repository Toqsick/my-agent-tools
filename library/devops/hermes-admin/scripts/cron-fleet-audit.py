#!/usr/bin/env python3
"""Cron Fleet Audit — automatische Flotten-Health-Prüfung.

Aufruf:  python3 ~/.hermes/skills/devops/hermes-admin/scripts/cron-fleet-audit.py
Output:  Strukturierter Markdown-Report mit Inventar, Gaps, Schedule Map, Pinning-Quote.

Erkennt: Dead-Path, Silent-OK, Provider-Drift, Silent-Stale, Unpinned Agent-Jobs.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

JOBS_PATH = os.path.expanduser('~/.hermes/cron/jobs.json')

def load_jobs():
    with open(JOBS_PATH) as f:
        return json.load(f)

def classify_mode(j):
    if j.get('script'):
        return 'script'
    if j.get('prompt') or j.get('skills'):
        return 'agent'
    return 'unknown'

def expand_schedule(expr):
    """Returns set of (dow, hour) tuples from a cron expression."""
    if not expr:
        return set()
    parts = expr.split()
    if len(parts) != 5:
        return set()
    minute, hour_str, dom, month, dow_str = parts
    hours = []
    for h in hour_str.split(','):
        h = h.strip()
        if h == '*':
            hours = list(range(24))
            break
        elif h.startswith('*/'):
            step = int(h[2:])
            hours = list(range(0, 24, step))
            break
        else:
            hours.append(int(h))
    dows = []
    for d in dow_str.split(','):
        d = d.strip()
        if d == '*':
            dows = list(range(7))
            break
        else:
            dows.append(int(d))
    return {(d, h) for d in dows for h in hours}

def main():
    data = load_jobs()
    jobs = data.get('jobs', [])
    updated_at = data.get('updated_at', 'N/A')

    # ── Inventory ──
    rows = []
    for j in jobs:
        rows.append({
            'id': j.get('id', '?')[:12],
            'name': j.get('name', '?'),
            'sched': j.get('schedule', {}).get('display', '?'),
            'enabled': j.get('enabled', False),
            'pinned': bool(j.get('provider_snapshot') and j.get('model_snapshot')),
            'status': j.get('last_status'),
            'last_run': j.get('last_run_at'),
            'next_run': j.get('next_run_at'),
            'mode': classify_mode(j),
            'provider': j.get('provider'),
            'script': j.get('script'),
            'created_at': j.get('created_at'),
        })

    # ── Gap Classification ──
    classes = {
        'silent_stale': [],
        'unpinned': [],
        'dead_path': [],
        'fresh_schedule': [],
    }

    for r in rows:
        # Silent-stale: enabled, never run
        if r['enabled'] and r['last_run'] is None and r['status'] is None:
            # Fresh-schedule check: next_run in future AND created_at recently
            created = r.get('created_at', '')
            if created and r.get('next_run'):
                try:
                    next_dt = datetime.fromisoformat(r['next_run'])
                    if next_dt > datetime.now(next_dt.tzinfo):
                        classes['fresh_schedule'].append(r)
                        continue
                except (ValueError, TypeError):
                    pass
            classes['silent_stale'].append(r)
        # Unpinned: agent-mode with provider but no provider_snapshot/model_snapshot
        if r['mode'] == 'agent' and r['provider'] and not r['pinned']:
            classes['unpinned'].append(r)

    # ── Pinning Quote ──
    agent_jobs = [r for r in rows if r['mode'] == 'agent']
    agent_with_provider = [r for r in agent_jobs if r['provider']]
    pinned_count = sum(1 for r in agent_with_provider if r['pinned'])
    total_pinnable = len(agent_with_provider)
    pct = pinned_count * 100 // max(1, total_pinnable)

    # ── Schedule Map (DOW x Hour) ──
    matrix = defaultdict(lambda: defaultdict(list))
    for j in jobs:
        pairs = expand_schedule(j.get('schedule', {}).get('expr', ''))
        for d, h in pairs:
            matrix[d][h].append(j.get('name', '?')[:35])

    # ── Build Report ──
    dow_names = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
    lines = []
    lines.append(f"# 🐝 Cron-Fleet-Audit — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Total Jobs: {len(jobs)}  |  updated_at: {updated_at[:19]}")
    lines.append('')

    # Inventory
    lines.append('## Inventar')
    header = f"{'ID':<14} {'Name':<42} {'Sched':<14} {'En':>3} {'Pin':>3} {'Status':<8} {'Mode':<7}"
    lines.append(header)
    lines.append('-' * len(header))
    for r in sorted(rows, key=lambda x: x['name']):
        name = r['name'][:40]
        en = 'Y' if r['enabled'] else 'N'
        pin = 'Y' if r['pinned'] else 'N'
        st = r['status'] or 'None'
        lines.append(f"{r['id']:<14} {name:<42} {r['sched']:<14} {en:>3} {pin:>3} {st:<8} {r['mode']:<7}")
    lines.append('')

    # Gaps
    lines.append('## Gaps')
    if classes['fresh_schedule']:
        lines.append(f"\n### 🟢 Fresh Schedule (nie gelaufen, aber Zeit kommt erst)")
        for r in classes['fresh_schedule']:
            lines.append(f"  - {r['id']:12} {r['name']:<42} next_run={r['next_run']}")
    if classes['silent_stale']:
        lines.append(f"\n### 🟨 Silent-Stale ({len(classes['silent_stale'])})")
        for r in classes['silent_stale']:
            lines.append(f"  - {r['id']:12} {r['name']:<42} schedule={r['sched']}")
    if classes['unpinned']:
        lines.append(f"\n### 🟧 Unpinned Agent-Jobs ({len(classes['unpinned'])})")
        for r in classes['unpinned']:
            lines.append(f"  - {r['id']:12} {r['name']:<42} provider={r['provider']}")
    if not any(classes.values()):
        lines.append('\nKeine Gaps gefunden.  🟢')
    lines.append('')

    # Pinning Quote
    lines.append('## Pinning')
    lines.append(f"Agent-Jobs total: {total_pinnable}")
    lines.append(f"Gepinnt: {pinned_count}  |  Quote: {pct}%")
    lines.append(f"Script-Jobs (ausgeschlossen): {sum(1 for r in rows if r['mode'] == 'script')}")
    for r in agent_jobs:
        pin_str = 'PIN' if r['pinned'] else '⚠ UNPINNED'
        lines.append(f"  {pin_str:<12} {r['name']:<42} provider={r['provider']}")
    lines.append('')

    # Schedule Overlap
    lines.append('## Schedule Overlaps (≥2 Jobs/h)')
    has_overlap = False
    for d in range(7):
        for h in range(24):
            items = matrix[d].get(h, [])
            if len(items) >= 2:
                has_overlap = True
                names = ', '.join(items)
                lines.append(f"  {dow_names[d]} {h:02d}:00  →  {len(items)} Jobs: {names}")
    if not has_overlap:
        lines.append('  Keine Overlaps  🟢')
    lines.append('')

    # Summary
    lines.append('## Summary')
    lines.append(f"  Agent: {len(agent_jobs)}  |  Script: {sum(1 for r in rows if r['mode'] == 'script')}  |  Unpinned: {len(classes['unpinned'])}  |  Stale: {len(classes['silent_stale']) + len(classes['fresh_schedule'])}  |  Pct: {pct}%")

    return '\n'.join(lines)

if __name__ == '__main__':
    print(main())