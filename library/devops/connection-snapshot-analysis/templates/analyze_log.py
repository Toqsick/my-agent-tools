#!/usr/bin/env python3
"""
connection-snapshot-analysis — reusable skeleton.

Usage:
    python3 analyze_log.py <path_to_capture.log>

Output:
    - analysis.json (intermediate data)
    - analysis-report.md (human-readable Markdown)
    Both written to <capture_dir>/analysis/ by default.
"""
import re, sys, json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from statistics import median
from pathlib import Path

TS_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+\-]\d{2}:\d{2})$')
SEP_RE = re.compile(r'^---\s*$')
SS_HEADER_RE = re.compile(r'^\s*State\s+Recv-Q\s+Send-Q', re.IGNORECASE)
CONN_RE = re.compile(
    r'(?P<proto>\w+)\s+'
    r'(?P<recv_q>\d+)\s+(?P<send_q>\d+)\s+'
    r'(?P<local>\S+)\s+(?P<remote>\S+)\s+'
    r'users:\(\((?P<proc>[^,]+),pid=(?P<pid>\d+),fd=(?P<fd>\d+)\)\)'
)

def parse_log(path):
    """Yield (datetime, [connections]) from an ss -tlnp capture log."""
    snaps = []
    ts, conns = None, []
    with open(path) as f:
        for raw in f:
            line = raw.rstrip('\n\r')
            if TS_RE.match(line):
                if ts is not None:
                    snaps.append((ts, conns))
                ts = datetime.fromisoformat(line)
                conns = []
            elif SEP_RE.match(line):
                pass  # skip separator
            elif SS_HEADER_RE.match(line):
                pass  # skip header
            elif ts is not None and CONN_RE.match(line):
                m = CONN_RE.match(line)
                conns.append({
                    'proc': m.group('proc'),
                    'proto': m.group('proto'),
                    'local': m.group('local'),
                    'remote': m.group('remote'),
                    'pid': int(m.group('pid')),
                    'fd': int(m.group('fd')),
                })
    if ts is not None:
        snaps.append((ts, conns))
    return snaps

def dedup_key(c):
    return (c['proto'], c['local'], c['remote'], c['pid'], c['fd'])

def rport(c):
    """Extract remote port from '1.2.3.4:443' or '[::1]:443'."""
    return int(c['remote'].rsplit(':', 1)[-1])

# ---- Analysis phases ----
# Each phase is a function taking (snaps, top_procs) → dict
# See references/2026-07-15-session-implementation.md for full phase code.

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdin'
    snaps = list(parse_log(path))
    print(f"Parsed {len(snaps)} snapshots.", file=sys.stderr)

    # TODO: Phase 2-7 implementation
    # See SKILL.md phases 2-7 and references/ session detail
    # Output: analysis.json + analysis-report.md