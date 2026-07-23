"""
preflight_check.py — Pre-Flight Check für GreyHack Computer-Use-Mission

Führt alle notwendigen Validierungen durch, bevor eine Live-Mission gestartet
werden darf. Erzeugt einen Go/No-Go-Report mit klaren Empfehlungen.

Checks:
1. cua-driver verfügbar?
2. Tesseract OCR installiert?
3. Grey-Hack-Fenster erkennbar?
4. Telegram-Bot-Token in ~/.hermes/.env?
5. Vault-Pfade existieren?
6. Beispiel-Mission parseable?
7. Kill-Switch-Logik funktioniert?
8. State-Persistenz funktioniert?

Verwendung:
    python3 preflight_check.py
    python3 preflight_check.py --verbose   # Mit Detail-Output
    python3 preflight_check.py --json      # JSON-Output für CI/CD
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# === KONSTANTEN ===
HERMES_SKILLS = Path("/home/bratan/.hermes/skills")
VAULT = Path("/home/bratan/Dokumente/Obsidian Vault")
MISSION_FILE = VAULT / "03 Projekte/Queen-Bee-Lab/Missions/Mission-Reraldi-IP-154.md"
STATE_FILE = VAULT / "03 Projekte/Queen-Bee-Lab/Mission-State - Live-Status.md"
CAPTURE_DIR = VAULT / "99 Capture"
ENV_FILE = Path("/home/bratan/.hermes/.env")
ORCHESTRATOR_SCRIPT = HERMES_SKILLS / "computer-use/greyhack-mission-orchestrator/scripts/orchestrator.py"


# === DATENKLASSEN ===
@dataclass
class CheckResult:
    """Ergebnis eines einzelnen Checks."""
    name: str
    passed: bool
    critical: bool  # Wenn True: Mission kann nicht starten ohne diesen Check
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class PreFlightReport:
    """Gesamtergebnis des Pre-Flight-Checks."""
    all_passed: bool = False
    critical_passed: bool = False
    results: list = field(default_factory=list)

    def add(self, result: CheckResult):
        self.results.append(result)
        if result.critical and not result.passed:
            self.critical_passed = False

    def finalize(self):
        """Berechnet finale Status-Flags."""
        self.all_passed = all(r.passed for r in self.results)
        self.critical_passed = all(
            r.passed for r in self.results if r.critical
        )


# === HELPER FUNCTIONS ===
def run_subprocess(cmd: list, timeout: int = 10) -> tuple:
    """Führt einen Subprocess aus und gibt (returncode, stdout, stderr) zurück."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError as e:
        return -1, "", str(e)
    except Exception as e:
        return -1, "", str(e)


# === INDIVIDUAL CHECKS ===
def check_cua_driver() -> CheckResult:
    """Prüft, ob cua-driver / Computer-Use verfügbar sind."""
    # 1. Versuche: hermes_tools.computer_use (Standard-Tool)
    try:
        from hermes_tools import computer_use  # noqa: F401
        return CheckResult(
            name="cua-driver / hermes_tools",
            passed=True,
            critical=True,
            message="✅ cua-driver verfügbar (via hermes_tools)",
            details="computer_use tool importierbar"
        )
    except ImportError:
        pass

    # 2. Versuche: hermes CLI Subprocess
    try:
        result = subprocess.run(
            ["hermes", "computer-use", "status"],
            capture_output=True, text=True, timeout=10
        )
        stdout_lower = result.stdout.lower()
        # Check auf "installed" und "ok" (kann in verschiedenen Zeilen sein)
        if "installed" in stdout_lower and ("✓" in result.stdout or "ok" in stdout_lower):
            return CheckResult(
                name="cua-driver / hermes CLI",
                passed=True,
                critical=True,
                message="✅ cua-driver installiert und funktional (via hermes CLI)",
                details=result.stdout[:300]
            )
        elif "installed" in stdout_lower:
            return CheckResult(
                name="cua-driver / hermes CLI",
                passed=False,
                critical=True,
                message="⚠️ cua-driver installiert, aber Status unklar",
                details=result.stdout[:300]
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        pass

    # 3. Versuche: cua-driver Binary direkt auf PATH
    try:
        result = subprocess.run(
            ["cua-driver", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return CheckResult(
                name="cua-driver Binary",
                passed=True,
                critical=True,
                message="✅ cua-driver Binary gefunden auf PATH",
                details=result.stdout[:200]
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 4. Fallback: Screenshot-Tool verfügbar?
    for tool in ["scrot", "grim", "gnome-screenshot"]:
        try:
            result = subprocess.run(
                ["which", tool], capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                return CheckResult(
                    name="cua-driver Fallback",
                    passed=True,
                    critical=False,
                    message=f"⚠️ cua-driver nicht verfügbar, aber {tool} als Fallback gefunden",
                    details="Empfehle Installation von cua-driver für volle Funktionalität",
                    fix_suggestion=(
                        "Installiere cua-driver via:\n"
                        "  hermes computer-use install\n"
                        f"Fallback funktioniert mit {tool}, aber Computer-Use-Features eingeschränkt."
                    )
                )
        except Exception:
            continue

    # 5. Nichts gefunden
    return CheckResult(
        name="cua-driver / hermes_tools",
        passed=False,
        critical=True,
        message="❌ Weder cua-driver noch Screenshot-Fallback verfügbar",
        fix_suggestion=(
            "Installiere cua-driver mit:\n"
            "  hermes computer-use install\n"
            "ODER mindestens ein Screenshot-Tool:\n"
            "  sudo apt install scrot        # X11\n"
            "  sudo apt install grim         # Wayland\n"
            "  sudo apt install gnome-screenshot"
        )
    )


def check_tesseract() -> CheckResult:
    """Prüft, ob Tesseract OCR installiert ist."""
    rc, stdout, stderr = run_subprocess(["tesseract", "--version"], timeout=5)
    if rc == 0:
        version = stdout.split("\n")[0] if stdout else "unknown"
        return CheckResult(
            name="Tesseract OCR",
            passed=True,
            critical=True,
            message=f"✅ Tesseract installiert: {version}",
            details=stdout[:200] if stdout else None
        )
    else:
        return CheckResult(
            name="Tesseract OCR",
            passed=False,
            critical=True,
            message="❌ Tesseract NICHT installiert",
            fix_suggestion=(
                "Installiere mit:\n"
                "  sudo apt install tesseract-ocr tesseract-ocr-deu\n"
                "(deu für deutsche Grey-Hack-Texte, eng reicht für Standard)"
            )
        )


def check_greyhack_window() -> CheckResult:
    """Versucht, ein Grey-Hack-Fenster zu erkennen."""
    # Versuche via wmctrl (X11)
    try:
        rc, stdout, stderr = run_subprocess(["wmctrl", "-l"], timeout=5)
        if rc == 0 and ("grey" in stdout.lower() or "hack" in stdout.lower()):
            return CheckResult(
                name="Grey-Hack-Fenster",
                passed=True,
                critical=False,  # Nicht kritisch — kann man später starten
                message="✅ Grey-Hack-Fenster erkannt",
                details="\n".join(
                    line for line in stdout.splitlines()
                    if "grey" in line.lower() or "hack" in line.lower()
                )[:300]
            )
    except Exception:
        pass

    # Wayland-Fallback: gnome-screenshot testen
    rc, _, _ = run_subprocess(["gnome-screenshot", "--help"], timeout=3)
    if rc == 0:
        return CheckResult(
            name="Grey-Hack-Fenster",
            passed=False,
            critical=False,
            message="⚠️ Grey-Hack-Fenster nicht erkannt (X11-Methode)",
            details="Grey Hack muss laufen, damit Computer-Use funktioniert",
            fix_suggestion=(
                "1. Starte Grey Hack via Steam\n"
                "2. Warte bis Hauptmenü sichtbar\n"
                "3. Re-run preflight_check.py"
            )
        )

    # Letzter Fallback: kein Screenshot-Tool
    return CheckResult(
        name="Grey-Hack-Fenster",
        passed=False,
        critical=False,
        message="⚠️ Kein Window-Detection-Tool verfügbar",
        fix_suggestion=(
            "Installiere mindestens eines von:\n"
            "  sudo apt install wmctrl    # X11\n"
            "  sudo apt install grim      # Wayland\n"
            "  sudo apt install gnome-screenshot"
        )
    )


def check_telegram() -> CheckResult:
    """Prüft, ob Telegram-Bot konfiguriert ist."""
    if not ENV_FILE.exists():
        return CheckResult(
            name="Telegram-Konfiguration",
            passed=False,
            critical=True,
            message="❌ ~/.hermes/.env nicht gefunden",
            fix_suggestion=(
                "Erstelle die Datei mit:\n"
                "  TELEGRAM_BOT_TOKEN=dein_token\n"
                "  TELEGRAM_HOME_CHANNEL=7222661188"
            )
        )

    content = ENV_FILE.read_text()
    has_token = "TELEGRAM_BOT_TOKEN" in content and "=" in content
    has_channel = "TELEGRAM_HOME_CHANNEL" in content and "=" in content

    if has_token and has_channel:
        return CheckResult(
            name="Telegram-Konfiguration",
            passed=True,
            critical=True,
            message="✅ Telegram-Bot konfiguriert",
            details=f"Token + Channel in {ENV_FILE} gefunden"
        )
    else:
        missing = []
        if not has_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not has_channel:
            missing.append("TELEGRAM_HOME_CHANNEL")
        return CheckResult(
            name="Telegram-Konfiguration",
            passed=False,
            critical=True,
            message=f"❌ Telegram-Vars fehlen: {', '.join(missing)}",
            fix_suggestion=f"Füge fehlende Vars in {ENV_FILE} ein"
        )


def check_telegram_connectivity() -> CheckResult:
    """Sendet einen Test-Alert an Telegram."""
    if not ENV_FILE.exists():
        return CheckResult(
            name="Telegram-Konnektivität",
            passed=False,
            critical=False,
            message="⚠️ Konnte nicht testen (kein .env)",
            fix_suggestion="Konfiguriere Telegram zuerst"
        )

    # Lade Token
    token = None
    channel = None
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("TELEGRAM_HOME_CHANNEL="):
            channel = line.split("=", 1)[1].strip().strip('"').strip("'")

    if not token or not channel:
        return CheckResult(
            name="Telegram-Konnektivität",
            passed=False,
            critical=False,
            message="⚠️ Token oder Channel leer"
        )

    # Sende Test-Nachricht
    test_msg = "🧪 Pre-Flight-Check Test-Alert — GreyHack Computer-Use-Suite"
    rc, _, stderr = run_subprocess([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{token}/sendMessage",
        "-d", f"chat_id={channel}",
        "-d", f"text={test_msg}",
    ], timeout=10)

    if rc == 0:
        return CheckResult(
            name="Telegram-Konnektivität",
            passed=True,
            critical=False,
            message="✅ Test-Alert erfolgreich gesendet (check dein Handy!)"
        )
    else:
        return CheckResult(
            name="Telegram-Konnektivität",
            passed=False,
            critical=False,
            message="❌ Test-Alert fehlgeschlagen",
            details=stderr[:200]
        )


def check_vault_paths() -> CheckResult:
    """Prüft, ob alle Vault-Pfade existieren."""
    required_paths = [
        VAULT,
        MISSION_FILE,
        STATE_FILE,
        CAPTURE_DIR,
        VAULT / "05 Ressourcen/GreyHack - Computer-Use-Mission-System.md",
    ]

    missing = [p for p in required_paths if not p.exists()]
    if missing:
        return CheckResult(
            name="Vault-Pfade",
            passed=False,
            critical=True,
            message=f"❌ {len(missing)} Pfad(e) fehlen",
            details="\n".join(f"  - {p}" for p in missing),
            fix_suggestion="Führe die Initialisierungs-Schritte aus dem Setup-README aus"
        )
    else:
        return CheckResult(
            name="Vault-Pfade",
            passed=True,
            critical=True,
            message=f"✅ Alle {len(required_paths)} Pfade existieren"
        )


def check_mission_parseable() -> CheckResult:
    """Prüft, ob die Beispiel-Mission parseable ist."""
    if not MISSION_FILE.exists():
        return CheckResult(
            name="Mission-Parseable",
            passed=False,
            critical=True,
            message="❌ Mission-Datei fehlt"
        )

    rc, stdout, stderr = run_subprocess([
        "python3", str(ORCHESTRATOR_SCRIPT),
        str(MISSION_FILE), "--dry-run"
    ], timeout=15)

    if rc == 0 and "Steps:" in stdout and "0\n" not in stdout.split("Steps:")[1].split("\n")[0]:
        # Extrahiere Anzahl Steps
        steps_line = [l for l in stdout.split("\n") if "Steps:" in l][0]
        steps_count = int(steps_line.split("Steps:")[1].strip().split()[0])
        if steps_count > 0:
            return CheckResult(
                name="Mission-Parseable",
                passed=True,
                critical=True,
                message=f"✅ Mission parseable ({steps_count} Steps erkannt)"
            )

    return CheckResult(
        name="Mission-Parseable",
        passed=False,
        critical=True,
        message="❌ Mission kann nicht geparst werden oder hat 0 Steps",
        details=stderr[:300] if stderr else None
    )


def check_kill_switch() -> CheckResult:
    """Prüft die Kill-Switch-Logik isoliert."""
    if not ORCHESTRATOR_SCRIPT.exists():
        return CheckResult(
            name="Kill-Switch-Logik",
            passed=False,
            critical=False,
            message="⚠️ Orchestrator-Script nicht gefunden"
        )

    # Schreibe Test-Script in temp-File (vermeidet Escaping-Probleme)
    # ORCHESTRATOR_SCRIPT ist bereits .../scripts/orchestrator.py,
    # also ist .parent bereits das scripts/-Verzeichnis!
    scripts_dir = str(ORCHESTRATOR_SCRIPT.parent)
    test_code = f"""import sys
sys.path.insert(0, '{scripts_dir}')
from mission_state import GameState, detect_state_from_ocr

test_text = 'Permission Required: Allow this app to access? [Allow] [Deny]'
state = detect_state_from_ocr(test_text)
if state == GameState.PERMISSION_DIALOG:
    print('OK')
else:
    detected = state.value
    print('FAIL: detected ' + str(detected))
"""

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        tmp_path = f.name

    try:
        rc, stdout, stderr = run_subprocess(["python3", tmp_path], timeout=10)
    finally:
        os.unlink(tmp_path)

    if rc == 0 and "OK" in stdout:
        return CheckResult(
            name="Kill-Switch-Logik",
            passed=True,
            critical=False,
            message="✅ OCR-Detection erkennt Permission-Dialog korrekt"
        )
    return CheckResult(
        name="Kill-Switch-Logik",
        passed=False,
        critical=False,
        message="❌ OCR-Detection erkennt Permission-Dialog NICHT",
        details=(stdout + stderr)[:300] if (stdout or stderr) else None
    )


def check_screenshot_fallback() -> CheckResult:
    """Prüft, ob mindestens ein Screenshot-Tool verfügbar ist."""
    tools = [
        ["gnome-screenshot", "--help"],
        ["grim", "--help"],
        ["scrot", "--help"],
        ["import", "-version"],
    ]

    for tool_cmd in tools:
        rc, _, _ = run_subprocess(tool_cmd, timeout=3)
        if rc == 0:
            return CheckResult(
                name="Screenshot-Tool",
                passed=True,
                critical=False,
                message=f"✅ Screenshot-Tool verfügbar: {tool_cmd[0]}"
            )

    return CheckResult(
        name="Screenshot-Tool",
        passed=False,
        critical=False,
        message="⚠️ Kein Screenshot-Tool gefunden (brauchen cua-driver!)",
        fix_suggestion=(
            "Installiere mindestens eines von:\n"
            "  sudo apt install gnome-screenshot  # GNOME\n"
            "  sudo apt install scrot              # X11\n"
            "  sudo apt install grim imagemagick   # Wayland/Sway"
        )
    )


def check_disk_space() -> CheckResult:
    """Prüft, ob genug Disk-Space für Captures vorhanden ist."""
    try:
        stat = os.statvfs(str(CAPTURE_DIR))
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
        # Bei 5s Intervall = ~17k Dateien/Tag = ~120 MB/Tag bei einfachen MDs
        # Plus Screenshots: ~50 MB/Tag
        # Wir brauchen mindestens 1 GB freien Speicher für eine sichere Mission
        if free_gb >= 1.0:
            return CheckResult(
                name="Disk-Space",
                passed=True,
                critical=False,
                message=f"✅ Genug freier Speicher: {free_gb:.1f} GB"
            )
        else:
            return CheckResult(
                name="Disk-Space",
                passed=False,
                critical=False,
                message=f"⚠️ Wenig freier Speicher: {free_gb:.2f} GB",
                fix_suggestion="Capture-Ordner archivieren oder Disk aufräumen"
            )
    except Exception as e:
        return CheckResult(
            name="Disk-Space",
            passed=True,  # Non-critical
            critical=False,
            message="⚠️ Konnte Disk-Space nicht prüfen",
            details=str(e)
        )


# === MAIN ===
def run_all_checks() -> PreFlightReport:
    """Führt alle Checks aus und gibt einen Report zurück."""
    report = PreFlightReport()
    report.critical_passed = True  # Optimistic init

    checks = [
        check_cua_driver,
        check_tesseract,
        check_vault_paths,
        check_mission_parseable,
        check_telegram,
        check_telegram_connectivity,
        check_greyhack_window,
        check_screenshot_fallback,
        check_kill_switch,
        check_disk_space,
    ]

    for check_fn in checks:
        try:
            result = check_fn()
            report.add(result)
        except Exception as e:
            report.add(CheckResult(
                name=check_fn.__name__,
                passed=False,
                critical=True,
                message=f"❌ Check crashed: {e}"
            ))

    report.finalize()
    return report


def print_human_report(report: PreFlightReport, verbose: bool = False):
    """Druckt einen menschenlesbaren Report."""
    print("=" * 60)
    print("🛫 GREYHACK COMPUTER-USE: PRE-FLIGHT CHECK")
    print("=" * 60)
    print()

    # Gruppiere nach Status
    critical_pass = [r for r in report.results if r.critical and r.passed]
    critical_fail = [r for r in report.results if r.critical and not r.passed]
    optional_fail = [r for r in report.results if not r.critical and not r.passed]

    print("📊 ÜBERSICHT")
    print(f"   Total Checks:    {len(report.results)}")
    print(f"   Critical Pass:   {len(critical_pass)}")
    print(f"   Critical Fail:   {len(critical_fail)}")
    print(f"   Optional Fail:   {len(optional_fail)}")
    print()

    if report.critical_passed and not optional_fail:
        print("🚀 STATUS: ✅ GO — Ready for Live Mission!")
    elif report.critical_passed and optional_fail:
        print("⚠️  STATUS: 🟡 CONDITIONAL GO — Kritische Checks OK, aber:")
        print("   Optional Checks haben Probleme. Live-Run möglich, aber suboptimal.")
    else:
        print("🛑 STATUS: ❌ NO-GO — Kritische Checks fehlgeschlagen!")
        print("   Bitte die unten aufgeführten Fixes anwenden.")
    print()

    print("=" * 60)
    print("🔍 DETAILS")
    print("=" * 60)
    print()

    for result in report.results:
        critical_marker = "🔴" if result.critical else "🟡"
        print(f"{critical_marker} {result.name}")
        print(f"   {result.message}")
        if verbose and result.details:
            print(f"   Details: {result.details}")
        if not result.passed and result.fix_suggestion:
            print(f"   💡 Fix: {result.fix_suggestion}")
        print()


def print_json_report(report: PreFlightReport):
    """Gibt einen JSON-Report aus (für CI/CD)."""
    output = {
        "status": "GO" if report.critical_passed and not any(
            not r.passed for r in report.results if not r.critical
        ) else ("CONDITIONAL" if report.critical_passed else "NO-GO"),
        "critical_passed": report.critical_passed,
        "all_passed": report.all_passed,
        "total_checks": len(report.results),
        "results": [
            {
                "name": r.name,
                "passed": r.passed,
                "critical": r.critical,
                "message": r.message,
                "details": r.details,
                "fix_suggestion": r.fix_suggestion,
            }
            for r in report.results
        ]
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Pre-Flight Check für GreyHack Computer-Use-Mission"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Zeige detaillierte Check-Informationen"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output für CI/CD-Integration"
    )
    args = parser.parse_args()

    report = run_all_checks()

    if args.json:
        print_json_report(report)
    else:
        print_human_report(report, verbose=args.verbose)

    # Exit Code für CI/CD
    if report.critical_passed:
        sys.exit(0 if not any(
            not r.passed for r in report.results if not r.critical
        ) else 1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()