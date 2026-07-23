#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════════════
# Wine Registry Env-Var Injector
# Erstellt: 2026-07-03 für Basti (MiniMax Hub Setup)
# Zweck: Setzt Env-Vars (insbesondere OAuth-Tokens) persistent
#        in einer Wine-Bottle via HKCU\Environment, weil die
#        Shell-zu-Wine Env-Var-Durchreichung fuer lange Tokens mit
#        Sonderzeichen unzuverlaessig ist.
# ════════════════════════════════════════════════════════════════════
"""
Benutzung:
  wine-registry-envvar-inject.py VAR VALUE        # Einzelne Variable
  wine-registry-envvar-inject.py --from-file PATH # Mehrere Vars aus JSON
  wine-registry-envvar-inject.py --delete VAR     # Variable loeschen
  wine-registry-envvar-inject.py --list            # Aktuelle Vars anzeigen

Konfiguration (automatisch erkannt, kann ueberschrieben werden):
  WINEPREFIX: aus Bottles-Standard oder ENV
  WINE_BIN:   kron4ek-wine-11.11-amd64 (Bottles-Flatpak-Pfad)
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Standard-Pfade fuer Bottles-Flatpak
DEFAULT_WINE_BIN = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wine"
DEFAULT_WINEPREFIX = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/bottles"


def find_bottle_paths():
    """Sucht Wine-Binary und WINEPREFIX basierend auf Bottle-Defaults."""
    wine_bin = Path(os.environ.get("WINE_BIN", DEFAULT_WINE_BIN))
    if not wine_bin.exists():
        # Fallback: Bottles runner alternatives
        runners = list(DEFAULT_WINEPREFIX.parent.glob("runners/*/bin/wine"))
        if runners:
            wine_bin = runners[0]

    wineprefix = Path(os.environ.get("WINEPREFIX", DEFAULT_WINEPREFIX))
    if wineprefix.exists() and wineprefix.is_dir():
        # WINEPREFIX zeigt auf parent of bottle? Falls ja, suche Bottle-Dir
        if not (wineprefix / "drive_c").exists():
            bottles = list(wineprefix.glob("*/drive_c"))
            if bottles:
                wineprefix = bottles[0].parent

    return wine_bin, wineprefix


def run_wine(wine_bin, cmd_args, env=None):
    """Fuehrt wine mit den uebergebenen Args aus und gibt (rc, stdout, stderr) zurueck."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    full_env["WINEDEBUG"] = "-all"
    result = subprocess.run(
        [str(wine_bin)] + cmd_args,
        env=full_env, capture_output=True, text=True, timeout=30
    )
    return result.returncode, result.stdout, result.stderr


def list_env(wine_bin, wineprefix):
    """Listet alle Env-Vars in HKCU\\Environment auf."""
    rc, out, err = run_wine(wine_bin, ["reg", "query", "HKEY_CURRENT_USER\\Environment"],
                            env={"WINEPREFIX": str(wineprefix)})
    if rc != 0:
        print(f"❌ Konnte Registry nicht lesen: {err}")
        return
    print(f"📋 HKCU\\Environment in {wineprefix.name}:")
    for line in out.splitlines():
        line = line.strip()
        if "REG_SZ" in line or "REG_EXPAND_SZ" in line:
            kv = line.split("REG_SZ", 1)[-1].strip() if "REG_SZ" in line else line
            name = kv.rsplit("    ", 1)[0].strip() if "    " in kv else kv.split("   ")[0].strip()
            value = kv.replace(name, "").strip()
            # Begrenze lange Werte (z.B. JWT-Tokens) in der Anzeige
            display_value = value if len(value) < 80 else value[:77] + "..."
            print(f"  {name} = {display_value}")


def set_env(wine_bin, wineprefix, name, value):
    """Setzt einen Env-Var in HKCU\\Environment."""
    rc, out, err = run_wine(wine_bin, [
        "reg", "add", "HKEY_CURRENT_USER\\Environment",
        "/v", name, "/t", "REG_SZ", "/d", value, "/f"
    ], env={"WINEPREFIX": str(wineprefix)})
    if rc == 0:
        print(f"✅ {name} gesetzt ({len(value)} Zeichen)")
        return True
    else:
        print(f"❌ Fehler beim Setzen von {name}: {err}")
        return False


def delete_env(wine_bin, wineprefix, name):
    """Loescht einen Env-Var in HKCU\\Environment."""
    rc, out, err = run_wine(wine_bin, [
        "reg", "delete", "HKEY_CURRENT_USER\\Environment",
        "/v", name, "/f"
    ], env={"WINEPREFIX": str(wineprefix)})
    if rc == 0:
        print(f"✅ {name} geloescht")
        return True
    else:
        print(f"⚠️  {name} konnte nicht geloescht werden: {err}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Wine Registry Env-Var Injector")
    parser.add_argument("name", nargs="?", help="Env-Var-Name (z.B. HILO_USER_TOKEN)")
    parser.add_argument("value", nargs="?", help="Env-Var-Wert (z.B. JWT-Token)")
    parser.add_argument("--from-file", metavar="PATH", type=str,
                        help="JSON-Datei mit mehreren Var/Value-Paaren")
    parser.add_argument("--delete", action="store_true", help="Variable loeschen")
    parser.add_argument("--list", action="store_true", help="Aktuelle Vars anzeigen")
    parser.add_argument("--wine", metavar="PATH", type=str,
                        help=f"Wine-Binary (default: {DEFAULT_WINE_BIN})")
    parser.add_argument("--prefix", metavar="PATH", type=str,
                        help=f"WINEPREFIX (default: {DEFAULT_WINEPREFIX})")
    args = parser.parse_args()

    wine_bin = Path(args.wine) if args.wine else None
    wineprefix = Path(args.prefix) if args.prefix else None
    if wine_bin is None or wineprefix is None:
        wb, wp = find_bottle_paths()
        wine_bin = wine_bin or wb
        wineprefix = wineprefix or wp

    if args.list:
        list_env(wine_bin, wineprefix)
        return

    if args.delete:
        if not args.name:
            print("❌ Name der zu loeschenden Variable fehlt")
            sys.exit(1)
        sys.exit(0 if delete_env(wine_bin, wineprefix, args.name) else 1)

    # Einzel-Variable
    if args.name and args.value:
        sys.exit(0 if set_env(wine_bin, wineprefix, args.name, args.value) else 1)

    # Multi aus JSON
    if args.from_file:
        try:
            data = json.loads(Path(args.from_file).read_text())
        except Exception as e:
            print(f"❌ Konnte {args.from_file} nicht als JSON lesen: {e}")
            sys.exit(1)
        all_ok = True
        for name, value in data.items():
            ok = set_env(wine_bin, wineprefix, name, str(value))
            all_ok = all_ok and ok
        sys.exit(0 if all_ok else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
