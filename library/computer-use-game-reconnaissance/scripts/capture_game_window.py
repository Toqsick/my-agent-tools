#!/usr/bin/env python3
"""
capture_game_window.py — Reusable Computer-Use game-window capture + OCR.

Proven on Grey Hack V0.9.6771 (Wayland+Xwayland), reusable for any canvas-rendered
game running under Steam/Flatpak/X11. Drops a timestamped PNG into the vault's
99 Capture folder and prints OCR output.

Usage:
    python3 capture_game_window.py <window_id> <pid> <label>
    python3 capture_game_window.py 12582985 4563 manual_firststeps

Outputs:
    - PNG to $VAULT/99 Capture/game_<label>_<timestamp>.png
    - OCR text to stdout (psm 6, eng+deu)
    - TSV coords to stderr (for click-target mapping)
"""
import subprocess, os, json, sys, time, base64
from pathlib import Path

# === Configuration ===
VAULT = Path("/home/bratan/Dokumente/Obsidian Vault")
CAPTURE_DIR = VAULT / "99 Capture"
DISPLAY = ":1"
XAUTHORITY = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"
OCR_LANGS = "eng+deu"
OCR_PSM = "6"
OCR_CONF_MIN = 60  # filter out very-low-confidence OCR hits


def gh_env():
    """Return env with DISPLAY/XAUTHORITY set for Wayland+Xwayland."""
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    env["XAUTHORITY"] = XAUTHORITY
    return env


def capture_via_cuadriver(pid, wid, env):
    """Capture via cua-driver get_window_state."""
    result = subprocess.run(
        ["cua-driver", "call", "get_window_state", json.dumps({
            "pid": pid, "window_id": wid, "include_screenshot": True
        })],
        capture_output=True, text=True, env=env, timeout=20
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return base64.b64decode(data["screenshot_png_b64"]), "cua-driver"
    return None, None


def capture_via_xwd(wid, env):
    """Fallback: xwd + convert."""
    subprocess.run(["xwd", "-id", str(wid), "-silent", "-out", "/tmp/screen.xwd"],
                   capture_output=True, env=env, timeout=10)
    subprocess.run(["convert", "/tmp/screen.xwd", "/tmp/screen.png"],
                   capture_output=True, env=env, timeout=10)
    p = Path("/tmp/screen.png")
    if p.exists():
        return p.read_bytes(), "xwd"
    return None, None


def ocr_text(png_path, env):
    """Plain OCR text."""
    r = subprocess.run(
        ["tesseract", str(png_path), "-", "-l", OCR_LANGS, "--psm", OCR_PSM],
        capture_output=True, text=True, env=env, timeout=20
    )
    return r.stdout.strip()


def ocr_tsv(png_path, env, conf_min=OCR_CONF_MIN):
    """OCR with TSV output → list of (word, x, y, w, h, conf)."""
    r = subprocess.run(
        ["tesseract", str(png_path), "-", "-l", OCR_LANGS, "--psm", OCR_PSM, "tsv"],
        capture_output=True, text=True, env=env, timeout=20
    )
    coords = []
    for line in r.stdout.split("\n")[1:]:  # skip header
        cols = line.split("\t")
        if len(cols) >= 12:
            try:
                conf = float(cols[10])
                if conf < conf_min:
                    continue
                word = cols[11].strip()
                if not word:
                    continue
                coords.append({
                    "word": word,
                    "x": int(cols[6]),
                    "y": int(cols[7]),
                    "w": int(cols[8]),
                    "h": int(cols[9]),
                    "cx": int(cols[6]) + int(cols[8]) // 2,  # click center
                    "cy": int(cols[7]) + int(cols[9]) // 2,
                    "conf": conf,
                })
            except (ValueError, IndexError):
                continue
    return coords


def detect_anti_cheat(action_result_json):
    """Returns True if cua-driver signaled unverifiable (anti-cheat)."""
    try:
        data = json.loads(action_result_json)
        return data.get("effect") == "unverifiable"
    except:
        return False


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    wid = int(sys.argv[1])
    pid = int(sys.argv[2])
    label = sys.argv[3]

    env = gh_env()
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = CAPTURE_DIR / f"game_{label}_{timestamp}.png"

    # Try cua-driver first
    png, method = capture_via_cuadriver(pid, wid, env)
    if png is None:
        print(f"⚠️ cua-driver failed, falling back to xwd...", file=sys.stderr)
        png, method = capture_via_xwd(wid, env)

    if png is None:
        print("❌ Both capture methods failed", file=sys.stderr)
        sys.exit(2)

    out_path.write_bytes(png)
    print(f"📸 {out_path} ({len(png)} bytes via {method})")

    text = ocr_text(out_path, env)
    print(f"📝 OCR ({len(text)} chars):")
    print(text)

    coords = ocr_tsv(out_path, env)
    print(f"\n📐 {len(coords)} word-coords (conf ≥ {OCR_CONF_MIN}):", file=sys.stderr)
    for c in coords[:20]:  # first 20 only to stderr
        print(f"   {c['cx']:>4},{c['cy']:>4} ({c['conf']:.0f}) {c['word']}", file=sys.stderr)
    if len(coords) > 20:
        print(f"   ... {len(coords) - 20} more", file=sys.stderr)


if __name__ == "__main__":
    main()