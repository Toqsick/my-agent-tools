#!/usr/bin/env python3
"""
verify_skeletons.py  —  Health-Check für die 3 Skeletons in deinem Projekt.

Prüft:
  1. Alle 3 Skeleton-Files existieren + Syntax-OK
  2. Hermes-Bridge funktioniert (entweder hermes_tools ODER subprocess ODER stub)
  3. Tests bestehen
  4. Config ist korrekt (max_spawn_depth wenn Skeleton B genutzt)

Usage:
  python3 verify_skeletons.py [--skeletons-dir PATH]

Exit-Code: 0 wenn alles ok, 1 sonst.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def colored(status: bool, message: str) -> str:
    color = GREEN if status else RED
    icon = "✅" if status else "❌"
    return f"{color}{icon}{RESET} {message}"


def warn(message: str) -> str:
    return f"{YELLOW}⚠️{RESET} {message}"


def info(message: str) -> str:
    return f"{BLUE}ℹ{RESET} {message}"


def check_file_exists(skeletons_dir: Path, filename: str) -> bool:
    """Prüft ob Skeleton-Datei existiert."""
    path = skeletons_dir / filename
    if not path.exists():
        print(colored(False, f"  {filename} nicht gefunden in {skeletons_dir}"))
        return False
    print(colored(True, f"  {filename} existiert ({path.stat().st_size} bytes)"))
    return True


def check_syntax(skeletons_dir: Path, filename: str) -> bool:
    """Prüft ob Skeleton-Datei syntaktisch valides Python ist."""
    path = skeletons_dir / filename
    try:
        ast.parse(path.read_text())
        print(colored(True, f"  {filename} syntax-OK"))
        return True
    except SyntaxError as e:
        print(colored(False, f"  {filename} syntax-fail: {e}"))
        return False


def check_hermes_tools() -> str:
    """Prüft ob hermes_tools verfügbar ist."""
    try:
        from hermes_tools import delegate_task  # noqa
        return "hermes_tools (Library)"
    except ImportError:
        pass

    # Fallback: subprocess hermes
    try:
        result = subprocess.run(
            ["hermes", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "hermes CLI (Subprocess)"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "stub-only (Dry-Run / Tests)"


def check_hermes_config() -> dict[str, Any]:
    """Prüft ~/.hermes/config.yaml auf relevante Settings."""
    config_path = Path.home() / ".hermes" / "config.yaml"
    result = {
        "config_exists": config_path.exists(),
        "max_spawn_depth": None,
        "max_concurrent_children": None,
        "model": None,
    }

    if not config_path.exists():
        return result

    try:
        import yaml
        config = yaml.safe_load(config_path.read_text())
        delegation = config.get("delegation", {})
        result["max_spawn_depth"] = delegation.get("max_spawn_depth")
        result["max_concurrent_children"] = delegation.get("max_concurrent_children")
        result["model"] = delegation.get("model")
    except ImportError:
        print(warn("  PyYAML nicht installiert — kann config.yaml nicht parsen"))
    except Exception as e:
        print(warn(f"  config.yaml parse-fail: {e}"))

    return result


def run_dry_run(skeletons_dir: Path, filename: str, args: list[str]) -> bool:
    """Führt Skeleton im Dry-Run-Modus aus und prüft Exit-Code."""
    path = skeletons_dir / filename
    cmd = [sys.executable, str(path), "--dry-run"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=skeletons_dir,
        )
        if result.returncode == 0:
            print(colored(True, f"  {filename} dry-run ok"))
            return True
        else:
            print(colored(False, f"  {filename} dry-run failed (exit {result.returncode})"))
            print(f"      STDERR: {result.stderr[-300:]}")
            return False
    except subprocess.TimeoutExpired:
        print(colored(False, f"  {filename} dry-run timeout (>60s)"))
        return False
    except Exception as e:
        print(colored(False, f"  {filename} dry-run error: {e}"))
        return False


def run_pytest(skeletons_dir: Path) -> bool:
    """Führt Pytest-Suite aus."""
    tests_dir = skeletons_dir / "tests"
    if not tests_dir.exists():
        print(warn("  tests/ Verzeichnis fehlt — keine Test-Validierung möglich"))
        return True   # kein Test-Fail, nur kein Test vorhanden

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q"],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=skeletons_dir,
        )
        if result.returncode == 0:
            # Parse pytest output für Test-Count
            lines = result.stdout.strip().split("\n")
            summary_line = next((l for l in lines if "passed" in l or "failed" in l), "")
            print(colored(True, f"  pytest {summary_line.strip()}"))
            return True
        else:
            print(colored(False, f"  pytest failed:\n{result.stdout[-500:]}"))
            return False
    except subprocess.TimeoutExpired:
        print(colored(False, "  pytest timeout (>180s)"))
        return False
    except Exception as e:
        print(colored(False, f"  pytest error: {e}"))
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="verify_skeletons.py",
        description="Health-Check für die 3 Skeletons",
    )
    parser.add_argument(
        "--skeletons-dir", type=Path, default=None,
        help="Pfad zum Skeletons-Verzeichnis (default: neben diesem Script)",
    )
    parser.add_argument(
        "--no-dry-run", action="store_true",
        help="Überspringe Dry-Run-Test (nur Syntax + Config-Check)",
    )
    parser.add_argument(
        "--no-pytest", action="store_true",
        help="Überspringe Pytest-Run",
    )
    args = parser.parse_args()

    if args.skeletons_dir:
        skeletons_dir = args.skeletons_dir.resolve()
    else:
        skeletons_dir = Path(__file__).resolve().parent

    if not skeletons_dir.exists():
        print(colored(False, f"Skeletons-Verzeichnis existiert nicht: {skeletons_dir}"))
        return 1

    print(f"\n{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}  Skeleton Health-Check{RESET}")
    print(f"{BLUE}  Verzeichnis: {skeletons_dir}{RESET}")
    print(f"{BLUE}═══════════════════════════════════════════════════════════════{RESET}\n")

    all_ok = True

    # Check 1: Files existieren
    print(f"{BLUE}[1/5] File-Existenz{RESET}")
    files_ok = all([
        check_file_exists(skeletons_dir, "master_worker.py"),
        check_file_exists(skeletons_dir, "hierarchical_tree.py"),
        check_file_exists(skeletons_dir, "critic_loop.py"),
    ])
    all_ok = all_ok and files_ok
    print()

    # Check 2: Syntax
    print(f"{BLUE}[2/5] Python-Syntax{RESET}")
    syntax_ok = all([
        check_syntax(skeletons_dir, "master_worker.py"),
        check_syntax(skeletons_dir, "hierarchical_tree.py"),
        check_syntax(skeletons_dir, "critic_loop.py"),
    ])
    all_ok = all_ok and syntax_ok
    print()

    # Check 3: Hermes-Bridge
    print(f"{BLUE}[3/5] Hermes-Bridge{RESET}")
    bridge_status = check_hermes_tools()
    if "Library" in bridge_status:
        print(colored(True, f"  Verfügbar via: {bridge_status}"))
    elif "Subprocess" in bridge_status:
        print(colored(True, f"  Verfügbar via: {bridge_status}"))
        print(warn("  Library nicht gefunden — Subprocess ist langsamer aber funktional"))
    else:
        print(warn(f"  Nur: {bridge_status}"))
        print(warn("  Echter Run benötigt hermes_tools oder hermes CLI"))
    print()

    # Check 4: Hermes-Config
    print(f"{BLUE}[4/5] Hermes-Config (~/.hermes/config.yaml){RESET}")
    config = check_hermes_config()
    if not config["config_exists"]:
        print(warn("  config.yaml nicht gefunden"))
    else:
        depth = config["max_spawn_depth"]
        print(info(f"  max_spawn_depth = {depth}"))
        if depth is None:
            print(warn("  Skeleton B (Tree) braucht max_spawn_depth >= 2"))
        elif depth < 2:
            print(colored(False, f"  max_spawn_depth={depth} zu klein für Skeleton B (braucht >= 2)"))
            all_ok = False
        else:
            print(colored(True, f"  max_spawn_depth={depth} OK für Skeleton B"))

        if config["max_concurrent_children"]:
            print(info(f"  max_concurrent_children = {config['max_concurrent_children']}"))
        if config["model"]:
            print(info(f"  delegation.model = {config['model']}"))
    print()

    # Check 5: Dry-Run + Tests (optional)
    if not args.no_dry_run:
        print(f"{BLUE}[5a/5] Dry-Run-Tests{RESET}")
        dry_run_ok = all([
            run_dry_run(skeletons_dir, "master_worker.py", ["Health-Check test"]),
            run_dry_run(skeletons_dir, "hierarchical_tree.py", []),
            run_dry_run(skeletons_dir, "critic_loop.py", ["Health-Check test"]),
        ])
        all_ok = all_ok and dry_run_ok
        print()

    if not args.no_pytest:
        print(f"{BLUE}[5b/5] Pytest-Suite{RESET}")
        pytest_ok = run_pytest(skeletons_dir)
        all_ok = all_ok and pytest_ok
        print()

    # Summary
    print(f"{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
    if all_ok:
        print(f"{GREEN}  ✅ ALLE CHECKS BESTANDEN — Skeletons sind ready{RESET}")
        print(f"{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
        return 0
    else:
        print(f"{RED}  ❌ MINDESTENS EIN CHECK FAILED — siehe oben{RESET}")
        print(f"{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())