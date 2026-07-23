#!/usr/bin/env python3
"""yuno-slash-goal Manifest-Manager.

Verwaltet Goal-Manifests für Yuno's /goal-Slash-Command.

Subcommands:
  create   - Erstellt neues Goal-Manifest
  status   - Zeigt Status eines Goal-Manifests
  update   - Aktualisiert Goal-Manifest (current_iter, history)
  complete - Markiert Goal als erfüllt
  abort    - Markiert Goal als abgebrochen
  list     - Listet alle Goals (active/completed/aborted)

Manifest-Schema:
  {
    "goal_id": "uuid",
    "description": "Alle Tests grün im greyhack-tools/ pytest",
    "check_method": "cd ~/... && pytest",
    "check_expected": {"exit_code": 0},
    "max_iter": 10,
    "timeout_seconds": 1800,
    "created_at": "ISO-8601",
    "current_iter": 0,
    "status": "active|completed|aborted",
    "history": [
      {"iter": 1, "timestamp": "...", "action": "...", "check_result": "failed", "check_output": "..."}
    ]
  }
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


GOAL_DIR = Path("/tmp/yuno_goals")


def get_manifest_path(goal_id: str) -> Path:
    return GOAL_DIR / f"{goal_id}.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_create(args) -> int:
    """Erstellt neues Goal-Manifest."""
    GOAL_DIR.mkdir(parents=True, exist_ok=True)

    goal_id = args.goal_id or str(uuid.uuid4())[:8]
    manifest_path = get_manifest_path(goal_id)
    if manifest_path.exists() and not args.force:
        print(f"FEHLER: Goal {goal_id} existiert bereits ({manifest_path})", file=sys.stderr)
        print(f"  Nutze --force zum Überschreiben oder /goal update für Updates", file=sys.stderr)
        return 1

    manifest = {
        "goal_id": goal_id,
        "description": args.description,
        "check_method": args.check_method,
        "check_expected": {"exit_code": args.expected_exit_code},
        "max_iter": args.max_iter,
        "timeout_seconds": args.timeout,
        "created_at": now_iso(),
        "current_iter": 0,
        "status": "active",
        "history": [],
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"✓ Goal erstellt: {goal_id}")
    print(f"  Pfad:   {manifest_path}")
    print(f"  Goal:   {args.description}")
    print(f"  Check:  {args.check_method}")
    print(f"  Limits: max-iter={args.max_iter}, timeout={args.timeout}s")
    return 0


def cmd_status(args) -> int:
    """Zeigt Goal-Status."""
    manifest_path = get_manifest_path(args.goal_id)
    if not manifest_path.exists():
        print(f"FEHLER: Goal {args.goal_id} nicht gefunden", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    print(f"=== Goal {manifest['goal_id']} ===")
    print(f"  Status:      {manifest['status']}")
    print(f"  Description: {manifest['description']}")
    print(f"  Iter:        {manifest['current_iter']}/{manifest['max_iter']}")
    print(f"  Check:       {manifest['check_method']}")
    print(f"  Expected:    exit_code={manifest['check_expected']['exit_code']}")
    print(f"  Created:     {manifest['created_at']}")
    print(f"  History:     {len(manifest['history'])} Einträge")

    if manifest['history']:
        print(f"\n=== Letzte 3 Iterationen ===")
        for h in manifest['history'][-3:]:
            print(f"  Iter {h['iter']} [{h['timestamp']}]: {h['action'][:60]}... → {h['check_result']}")

    return 0


def cmd_update(args) -> int:
    """Aktualisiert Goal-Manifest nach einer Iteration."""
    manifest_path = get_manifest_path(args.goal_id)
    if not manifest_path.exists():
        print(f"FEHLER: Goal {args.goal_id} nicht gefunden", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())

    # Check: Goal bereits abgeschlossen?
    if manifest['status'] != 'active':
        print(f"WARN: Goal ist bereits {manifest['status']}, Update wird trotzdem gemacht")

    iter_entry = {
        "iter": manifest['current_iter'] + 1,
        "timestamp": now_iso(),
        "action": args.action,
        "check_result": args.check_result,
        "check_output": args.check_output or "",
    }
    manifest['history'].append(iter_entry)
    manifest['current_iter'] += 1

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"✓ Iteration {iter_entry['iter']} geloggt für Goal {args.goal_id}")
    print(f"  Result: {args.check_result}")
    return 0


def cmd_complete(args) -> int:
    """Markiert Goal als erfüllt."""
    manifest_path = get_manifest_path(args.goal_id)
    if not manifest_path.exists():
        print(f"FEHLER: Goal {args.goal_id} nicht gefunden", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    manifest['status'] = 'completed'
    manifest['completed_at'] = now_iso()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"✓ Goal {args.goal_id} als COMPLETED markiert nach {manifest['current_iter']} Iterationen")
    return 0


def cmd_abort(args) -> int:
    """Markiert Goal als abgebrochen."""
    manifest_path = get_manifest_path(args.goal_id)
    if not manifest_path.exists():
        print(f"FEHLER: Goal {args.goal_id} nicht gefunden", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    manifest['status'] = 'aborted'
    manifest['aborted_at'] = now_iso()
    manifest['abort_reason'] = args.reason or "Manueller Abbruch"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"✓ Goal {args.goal_id} als ABORTED markiert: {args.reason or 'Manuell'}")
    return 0


def cmd_list(args) -> int:
    """Listet alle Goals nach Status."""
    if not GOAL_DIR.exists():
        print(f"Keine Goals gefunden (Verzeichnis {GOAL_DIR} existiert nicht)")
        return 0

    by_status = {"active": [], "completed": [], "aborted": [], "unknown": []}
    for manifest_file in sorted(GOAL_DIR.glob("*.json")):
        try:
            m = json.loads(manifest_file.read_text())
            status = m.get('status', 'unknown')
            by_status.setdefault(status, []).append(m)
        except Exception as e:
            print(f"WARN: {manifest_file} nicht parsebar: {e}")

    for status in ["active", "completed", "aborted"]:
        goals = by_status.get(status, [])
        if goals:
            print(f"\n=== {status.upper()} ({len(goals)}) ===")
            for g in goals:
                iter_str = f"{g['current_iter']}/{g['max_iter']}"
                print(f"  {g['goal_id']} | iter={iter_str} | {g['description'][:80]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Yuno /goal Manifest-Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # create
    p_create = subparsers.add_parser('create', help='Erstellt neues Goal-Manifest')
    p_create.add_argument('--goal-id', help='Explizite Goal-ID (sonst auto-uuid)')
    p_create.add_argument('--description', required=True, help='Goal-Beschreibung')
    p_create.add_argument('--check-method', required=True, help='Check-Befehl (bash)')
    p_create.add_argument('--expected-exit-code', type=int, default=0, help='Erwarteter Exit-Code (default: 0)')
    p_create.add_argument('--max-iter', type=int, default=10, help='Max Iterationen (default: 10)')
    p_create.add_argument('--timeout', type=int, default=3600, help='Timeout in Sekunden (default: 3600)')
    p_create.add_argument('--force', action='store_true', help='Überschreibe existierendes Manifest')

    # status
    p_status = subparsers.add_parser('status', help='Zeigt Goal-Status')
    p_status.add_argument('--goal-id', required=True)

    # update
    p_update = subparsers.add_parser('update', help='Aktualisiert Goal nach einer Iteration')
    p_update.add_argument('--goal-id', required=True)
    p_update.add_argument('--action', required=True, help='Was wurde in dieser Iteration gemacht')
    p_update.add_argument('--check-result', required=True, choices=['success', 'failed', 'skipped'], help='Result des Check-Befehls')
    p_update.add_argument('--check-output', help='Output des Check-Befehls (optional)')

    # complete
    p_complete = subparsers.add_parser('complete', help='Markiert Goal als erfüllt')
    p_complete.add_argument('--goal-id', required=True)

    # abort
    p_abort = subparsers.add_parser('abort', help='Bricht Goal ab')
    p_abort.add_argument('--goal-id', required=True)
    p_abort.add_argument('--reason', help='Abbruch-Grund')

    # list
    p_list = subparsers.add_parser('list', help='Listet alle Goals')

    args = parser.parse_args()

    commands = {
        'create': cmd_create,
        'status': cmd_status,
        'update': cmd_update,
        'complete': cmd_complete,
        'abort': cmd_abort,
        'list': cmd_list,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())