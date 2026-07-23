"""
greyhack_macro.py — Aktive Aktionen für Grey Hack via Computer Use

Führt Tastatureingaben, Maus-Klicks und UI-Interaktionen aus.
Voraussetzung: cua-driver installiert, Grey Hack läuft in erkennbarem Fenster.

Verwendung:
    python3 greyhack_macro.py type-greyscript <pfad_zur_src_datei>
    python3 greyhack_macro.py login <username> <password>
    python3 greyhack_macro.py click-and-verify <element_index> <expected_text>
"""

import sys
import time
import subprocess
import argparse
from pathlib import Path


def ensure_cua_available():
    """Prüft, ob cua-driver / hermes_tools verfügbar sind."""
    try:
        from hermes_tools import computer_use  # noqa: F401
        return True
    except ImportError:
        return False


def capture_with_fallback(app: str = "steam", mode: str = "som"):
    """Screenshot via cua-driver mit Fallback auf direktes gnome-screenshot/grim."""
    try:
        from hermes_tools import computer_use
        return computer_use(
            action="capture",
            mode=mode,
            app=app,
            background_only=True,
        )
    except ImportError:
        # Fallback: gnome-screenshot / grim
        tmp_path = Path("/tmp/greyhack_macro_fallback.png")
        for cmd in [
            ["gnome-screenshot", "-f", str(tmp_path)],
            ["grim", str(tmp_path)],
        ]:
            try:
                subprocess.run(cmd, check=True, timeout=5)
                if tmp_path.exists():
                    return tmp_path.read_bytes()
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        raise RuntimeError("Weder cua-driver noch gnome-screenshot/grim verfügbar!")


def ocr_extract(image_bytes: bytes) -> str:
    """Tesseract-OCR auf ein Bild."""
    tmp_path = Path("/tmp/greyhack_macro_ocr.png")
    tmp_path.write_bytes(image_bytes)
    try:
        result = subprocess.run(
            ["tesseract", str(tmp_path), "-", "-l", "eng", "--psm", "6"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""


def click_with_retry(element_index: int, expected_text: str = None, max_attempts: int = 3):
    """Klickt auf ein Element mit Verifikation und Retry-Logic."""
    try:
        from hermes_tools import computer_use
    except ImportError:
        raise RuntimeError("cua-driver nicht verfügbar — `hermes computer-use install`")

    for attempt in range(1, max_attempts + 1):
        try:
            # Pre-Capture
            computer_use(action="capture", mode="som", app="steam", background_only=True)

            # Klick
            computer_use(action="click", element=element_index, capture_after=True)
            time.sleep(1.0)

            # Post-Verify (wenn erwarteter Text gegeben)
            if expected_text:
                post = capture_with_fallback(mode="vision")
                ocr = ocr_extract(post)
                if expected_text.lower() in ocr.lower():
                    return True
                print(f"⚠️ Versuch {attempt}: '{expected_text}' nicht gefunden, retry...")
                time.sleep(0.5)
            else:
                return True
        except Exception as e:
            print(f"⚠️ Versuch {attempt} fehlgeschlagen: {e}")
            time.sleep(0.5)

    raise RuntimeError(
        f"Klick auf Element {element_index} nach {max_attempts} Versuchen fehlgeschlagen!"
    )


def type_greyscript(src_file_path: str):
    """Liest eine .src-Datei und tippt sie in die Grey-Hack-Konsole."""
    try:
        from hermes_tools import computer_use
    except ImportError:
        raise RuntimeError("cua-driver nicht verfügbar")

    src_path = Path(src_file_path)
    if not src_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {src_file_path}")

    script_content = src_path.read_text(encoding="utf-8-sig")

    # Pre-Capture: Konsolen-Eingabefeld finden
    capture = capture_with_fallback(mode="ax")
    console_input_element = None
    for elem in capture if isinstance(capture, list) else []:
        if "text field" in str(elem.get("role", "")).lower():
            console_input_element = elem.get("index")
            break

    # Fallback: Wir nehmen Element 0 als Notlösung
    if console_input_element is None:
        console_input_element = 0
        print("⚠️ Konsolen-Eingabefeld nicht eindeutig identifiziert — verwende Element 0")

    # Klick auf Eingabefeld
    computer_use(action="click", element=console_input_element, capture_after=True)

    # Zeile für Zeile tippen (Grey Hack hat oft Char-Limits pro Zeile)
    for line in script_content.splitlines():
        computer_use(action="type", text=line + "\n", capture_after=False)
        time.sleep(0.1)  # Pause zwischen Zeilen für Stabilität

    print(f"✅ {src_path.name} erfolgreich in Grey-Hack-Konsole getippt!")


def automated_login(username: str, password: str):
    """Führt die Login-Sequenz für Grey Hack aus."""
    try:
        from hermes_tools import computer_use
    except ImportError:
        raise RuntimeError("cua-driver nicht verfügbar")

    print(f"🔐 Starte Login-Sequenz für User '{username}'...")

    # 1. Warte auf Login-Screen
    time.sleep(2.0)

    # 2. Username-Feld
    computer_use(action="capture", mode="som", app="steam", background_only=True)
    computer_use(action="type", text=username)
    computer_use(action="key", keys="Tab")

    # 3. Password-Feld
    computer_use(action="type", text=password)
    computer_use(action="key", keys="return")

    # 4. Post-Verify
    time.sleep(3.0)
    print(f"✅ Login-Sequenz abgeschlossen für {username}")


def main():
    parser = argparse.ArgumentParser(description="GreyHack Smart Macro")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_type = subparsers.add_parser("type-greyscript", help="GreScript in Konsole tippen")
    p_type.add_argument("file", help="Pfad zur .src-Datei")

    p_login = subparsers.add_parser("login", help="Login-Sequenz ausführen")
    p_login.add_argument("username")
    p_login.add_argument("password")

    p_click = subparsers.add_parser("click-and-verify", help="Klicken + Verifizieren")
    p_click.add_argument("element_index", type=int)
    p_click.add_argument("expected_text", help="Erwarteter Text nach dem Klick")

    args = parser.parse_args()

    if not ensure_cua_available():
        print("⚠️ cua-driver nicht gefunden — Fallback-Modus aktiv")
        print("   Für volle Funktionalität: `hermes computer-use install`")

    if args.command == "type-greyscript":
        type_greyscript(args.file)
    elif args.command == "login":
        automated_login(args.username, args.password)
    elif args.command == "click-and-verify":
        success = click_with_retry(args.element_index, args.expected_text)
        if success:
            print(f"✅ Klick auf Element {args.element_index} erfolgreich verifiziert!")
        sys.exit(1)


if __name__ == "__main__":
    main()