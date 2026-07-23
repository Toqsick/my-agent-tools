#!/usr/bin/env python3
"""
fake_hermes_harness.py — reproduzierbare Smoke-Test-Harness für Hermes-Kanban-Bundles.

Erzeugt einen isolierten Fake-Hermes-Bin-Dir, eine Fake-Home-Dir mit `.env`,
und einen Plan-Stub mit Dummy-Assets. Nach `python3 scripts/bootstrap_pipeline.py`
kann das Setup-Script direkt gegen die Fake-Hermes gefahren werden, ohne
`~/.hermes/` zu berühren.

Verwendung in einer Smoke-Session:

    python3 ~/.hermes/skills/third-party-bundle-patch-release/scripts/fake_hermes_harness.py \
      --bundle-dir /home/bratan/20-Workspace/<bundle>-fix \
      --plan examples/example-plan-product-teaser.json \
      --tenant q3-product-teaser

Output: smoke_dir mit setup.sh, brief.md, TEAM.md, fakebin/, fakehome/, hermes-calls.log.
Manuell danach:

    HOME="$SMOKE_DIR/fakehome" PATH="$SMOKE_DIR/fakebin:$PATH" \
      HERMES_HOME="$SMOKE_DIR/fakehome/.hermes" \
      bash "$SMOKE_DIR/setup.sh"
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path


FAKE_HERMES_TEMPLATE = """#!/usr/bin/env bash
# Auto-generated fake hermes wrapper for smoke-testing bundles.
# Logs every invocation, implements just enough subcommands for setup.sh to complete.
set -euo pipefail
log="${HERMES_FAKE_LOG:?HERMES_FAKE_LOG not set}"
echo "hermes $*" >> "$log"

case "${1:-} ${2:-}" in
  "profile create"*)
    name="${3:-}"
    [ -n "$name" ] || { echo "fake hermes: profile create without name" >&2; exit 1; }
    mkdir -p "$HOME/.hermes/profiles/$name"
    printf '{}\\n' > "$HOME/.hermes/profiles/$name/config.yaml"
    exit 0
    ;;
  "profile describe"*)
    exit 0
    ;;
  "kanban init"|"kanban stats"|"kanban watch")
    exit 0
    ;;
  "kanban create"*|"kanban swarm"*)
    echo "t_fake_smoke_001"
    exit 0
    ;;
  "kanban list"*|"kanban ls"*)
    echo "[]"
    exit 0
    ;;
  "kanban show"*|"kanban tail"*|"kanban runs"*|"kanban log"*|"kanban heartbeat"*)
    echo "{}"
    exit 0
    ;;
esac

# Unhandled: return success with empty output
exit 0
"""


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle-dir", required=True, type=Path,
                    help="Working-copy des Patches (mit scripts/bootstrap_pipeline.py)")
    ap.add_argument("--plan", required=True, type=Path,
                    help="Pfad zum Plan-JSON innerhalb des bundle-dir")
    ap.add_argument("--tenant", default="smoke-tenant", help="Tenant-Name (für Debug-Sichtbarkeit)")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Output-Dir (default: /tmp/<bundle>-smoke-$$)")
    ap.add_argument("--env-keys", nargs="*", default=["ELEVENLABS_API_KEY", "OPENROUTER_API_KEY"],
                    help="API-Keys, die im Fake-.env als 'dummy' gesetzt werden")
    ap.add_argument("--asset-fixtures", action="store_true",
                    help="Plan mit Dummy-Asset-Pfaden patchen, damit Asset-Copy nicht crasht")
    return ap.parse_args()


def write_dummy_assets(out_dir: Path) -> dict[str, str]:
    """Erzeugt Mini-Dummy-Assets für die gängigen Asset-Keys und gibt die Pfade zurück."""
    asset_dir = out_dir / "dummy-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "track.mp3": b"dummy audio",
        "logo.svg": b"<svg xmlns='http://www.w3.org/2000/svg'/>",
        "Inter-Regular.ttf": b"dummy font",
        "demo-capture.mp4": b"dummy video",
        "ref-frame-01.png": b"dummy png",
    }
    paths: dict[str, str] = {}
    for name, data in fixtures.items():
        p = asset_dir / name
        p.write_bytes(data)
        paths[name] = str(p)
    return paths


def patch_plan_assets(plan_path: Path, out_path: Path, asset_paths: dict[str, str]) -> None:
    """Setzt die Assets-Sektion des Plans auf lokale Dummy-Pfade."""
    plan = json.loads(plan_path.read_text())
    plan["assets"] = {
        "audio_track": asset_paths["track.mp3"],
        "logos": [asset_paths["logo.svg"]],
        "fonts": [asset_paths["Inter-Regular.ttf"]],
        "existing_footage": [asset_paths["demo-capture.mp4"]],
        "style_frames": [asset_paths["ref-frame-01.png"]],
    }
    out_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")


def write_fake_hermes(bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    p = bin_dir / "hermes"
    p.write_text(FAKE_HERMES_TEMPLATE)
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def write_fake_env(home_dir: Path, keys: list[str]) -> Path:
    home_dir.mkdir(parents=True, exist_ok=True)
    p = home_dir / ".hermes" / ".env"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(f"{k}=dummy" for k in keys) + "\n")
    return p


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir or Path(f"/tmp/{args.bundle_dir.name}-smoke-{os.getpid()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = args.bundle_dir.resolve()
    plan_in = (bundle / args.plan).resolve()
    if not plan_in.exists():
        print(f"ERROR: plan nicht gefunden: {plan_in}", file=sys.stderr)
        return 2

    # 1) Assets + gepatchter Plan
    asset_paths = write_dummy_assets(out_dir)
    patched_plan = out_dir / "plan.smoke.json"
    patch_plan_assets(plan_in, patched_plan, asset_paths)

    # 2) Generator laufen lassen
    gen_script = bundle / "scripts" / "bootstrap_pipeline.py"
    if not gen_script.exists():
        print(f"ERROR: Generator nicht gefunden: {gen_script}", file=sys.stderr)
        return 2

    import subprocess
    setup_path = out_dir / "setup.sh"
    rc = subprocess.run(
        [
            sys.executable, str(gen_script), str(patched_plan),
            "--out", str(setup_path),
            "--brief-out", str(out_dir / "brief.md"),
            "--team-out", str(out_dir / "TEAM.md"),
        ],
        check=False,
    ).returncode
    if rc != 0:
        print(f"ERROR: Generator exited {rc}", file=sys.stderr)
        return rc

    # 3) bash -n auf das generierte setup.sh
    bash_n = subprocess.run(["bash", "-n", str(setup_path)], check=False).returncode
    if bash_n != 0:
        print(f"ERROR: bash -n failed on {setup_path}", file=sys.stderr)
        return bash_n

    # 4) Fake-Hermes + Fake-Home
    write_fake_hermes(out_dir / "bin")
    write_fake_env(out_dir, args.env_keys)

    # 5) Runbook ausgeben
    log_path = out_dir / "hermes-calls.log"
    env_setup = (
        f'export HERMES_FAKE_LOG="{log_path}"\n'
        f'export HOME="{out_dir}/fakehome"\n'
        f'export HERMES_HOME="{out_dir}/fakehome/.hermes"\n'
        f'export PATH="{out_dir}/bin:$PATH"\n'
    )
    runbook = out_dir / "RUNBOOK.sh"
    runbook.write_text(
        "#!/usr/bin/env bash\n"
        "# Auto-generated runbook for smoke-testing the bundle.\n"
        "set -euo pipefail\n"
        + env_setup +
        f'bash "{setup_path}"\n'
        f'echo "=== exit=$? ==="\n'
        f'echo "--- Profile marker files ---"\n'
        f'for d in "$HOME/.hermes/profiles/"*/; do\n'
        f'  [ -f "$d/.kanban-video-orchestrator-owner" ] && echo "  $(basename $d) -> $(cat $d/.kanban-video-orchestrator-owner)"\n'
        f'done\n'
        f'echo "--- Profile config sample ---"\n'
        f'cat "$HOME/.hermes/profiles/director/config.yaml"\n'
        f'echo "--- Asset copy result ---"\n'
        f'ls -la "$HOME/projects/video-pipeline/" 2>/dev/null\n'
    )
    runbook.chmod(runbook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"\nSmoke harness ready in {out_dir}\n")
    print("Run with:")
    print(f"  bash {runbook}")
    print("\nEvidence streams after run:")
    print(f"  rc            : in stdout (last line)")
    print(f"  hermes-calls  : {log_path}")
    print(f"  profile cfg   : {out_dir}/fakehome/.hermes/profiles/<name>/config.yaml")
    print(f"  owner markers : {out_dir}/fakehome/.hermes/profiles/<name>/.kanban-video-orchestrator-owner")
    print(f"  asset copies  : {out_dir}/fakehome/projects/video-pipeline/<slug>/...")
    return 0


if __name__ == "__main__":
    sys.exit(main())