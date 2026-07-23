#!/usr/bin/env python3
"""Standalone repro template for proving test-failure classifications.

Use when pytest's behavior is too complex to reason about directly and you
need to demonstrate the mechanism without running the full test suite.
Copy this file, fill in the marked sections, run it.

Common pattern: capture a reference at "collection time", simulate a
sibling fixture that wipes the module, then observe that the captured
reference is now stale.
"""

import importlib
import os
import sys
import tempfile
from pathlib import Path

REPO = os.environ.get("REPO_ROOT", "/home/bratan/.hermes/hermes-agent")
TEST_FILE = os.environ.get(
    "TEST_FILE",
    f"{REPO}/tests/hermes_cli/test_kanban_lifecycle_hooks.py",
)
sys.path.insert(0, REPO)


def main() -> int:
    # 1. Collection-time import (replicates pytest collection).
    #    This binds module-scope `from X import Y` references.
    spec = importlib.util.spec_from_file_location(
        "audit_target_module", TEST_FILE
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # >>> CAPTURE reference (what the test does at module scope):
    captured_ref = mod.get_plugin_manager()
    print(f"captured_ref id: {id(captured_ref)}")
    print(f"captured_ref._hooks: {list(captured_ref._hooks.keys())}")

    # 2. Simulate a sibling fixture's pollution.
    #    Replace this with whatever the polluting fixture actually does.
    POLLUTION_PREFIX = "hermes_cli."
    for k in list(sys.modules.keys()):
        if k == POLLUTION_PREFIX.rstrip(".") or k.startswith(POLLUTION_PREFIX):
            del sys.modules[k]
    print(f"wiped sys.modules entries matching: {POLLUTION_PREFIX}")

    # 3. Apply the test fixture's setup.
    #    Replace with the test fixture's body.
    test_events: list = []
    captured_ref._hooks.setdefault(
        "kanban_task_claimed", []
    ).append(lambda **kw: test_events.append(kw))

    # 4. Run the test body — observe the result.
    #    Replace with the test's body, adapted to standalone context.
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / ".hermes"
        home.mkdir()
        original_home = Path.home
        Path.home = lambda: Path(td)
        try:
            mod.kb.init_db()
            conn = mod.kb.connect()
            try:
                tid = mod.kb.create_task(
                    conn, title="audit-task", assignee="worker"
                )
                mod.kb.claim_task(conn, tid)
            finally:
                conn.close()
        finally:
            Path.home = original_home

    print(f"events captured: {test_events}")

    # 5. Assert / report.
    expected = int(os.environ.get("EXPECTED_EVENTS", "1"))
    actual = len(test_events)
    if actual == expected:
        print(f"PASS: captured {actual} events as expected")
        return 0
    print(f"FAIL: expected {expected} events, got {actual}")
    print("→ This reproduces the test failure outside pytest.")
    return 1


if __name__ == "__main__":
    sys.exit(main())