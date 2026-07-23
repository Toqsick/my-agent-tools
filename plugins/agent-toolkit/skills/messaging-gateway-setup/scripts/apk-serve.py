#!/usr/bin/env python3
"""Minimaler Static-File-Server NUR fuer genau eine erlaubte APK-Datei.

Pattern aus 2026-07-10 Hermes-Android-Hybrid-Hosting-Session:
Wenn kein `adb` im Setup ist und die APK via Tailscale Serve aufs Handy soll,
serviert dieser Server die Datei hinter `tailscale serve --bg --https=<PORT>`.

Sicherheit:
- KEIN Directory-Listing
- KEIN Path-Traversal (alle Requests ausser exakt ALLOWED_FILES -> 404)
- Bound auf 127.0.0.1 (nicht 0.0.0.0) -- nur ueber Tailscale Serve exponieren

ASCII-only Bytes-Literals verwenden! (Sonst SyntaxError: em-dash etc.)

Usage:
    python3 apk-serve.py                       # default Port 8445
    python3 apk-serve.py --port 9445           # custom Port
    python3 apk-serve.py /path/to/dir          # custom Verzeichnis

Voraussetzung: Datei liegt im ROOT und exakter Name steht in ALLOWED_FILES.
"""
import argparse
import http.server
import os
import socketserver
import sys

DEFAULT_ROOT = "/home/bratan/Downloads/hermes-android"
DEFAULT_PORT = 8445
# Default-Dateiname fuer v1.0.9. Bei neueren Versionen erweitern.
DEFAULT_ALLOWED = {"hermes-android-v1.0.9-arm64.apk"}

class APKHandler(http.server.SimpleHTTPRequestHandler):
    allowed = DEFAULT_ALLOWED

    def do_GET(self):
        filename = self.path.lstrip("/")
        if filename in self.allowed:
            filepath = os.path.join(self.ROOT, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.android.package-archive")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                with open(filepath, "rb") as f:
                    while chunk := f.read(64 * 1024):
                        try:
                            self.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError):
                            return
                return
        # 404 fuer alles andere (kein Listing, kein Traversal)
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"404 - only " + ", ".join(
            name.encode("ascii") for name in self.allowed
        ) + b" served here\n")

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[apk-serve] {fmt % args}\n")

    def __init__(self, *args, **kwargs):
        self.ROOT = APKHandler.root
        super().__init__(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (default 8445)")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Verzeichnis (default {DEFAULT_ROOT})")
    parser.add_argument("--file", action="append", default=[], help="Erlaubte Datei (mehrfach --file foo --file bar)")
    args = parser.parse_args()

    allowed = set(args.file) if args.file else DEFAULT_ALLOWED
    APKHandler.allowed = allowed
    APKHandler.root = args.root

    if not os.path.isdir(args.root):
        sys.stderr.write(f"[apk-serve] ERROR: root directory not found: {args.root}\n")
        sys.exit(1)

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", args.port), APKHandler) as httpd:
            sys.stderr.write(
                f"[apk-serve] serving on 127.0.0.1:{args.port} from {args.root}\n"
                f"[apk-serve] allowed files: {sorted(allowed)}\n"
            )
            httpd.serve_forever()
    except OSError as e:
        sys.stderr.write(f"[apk-serve] ERROR: cannot bind 127.0.0.1:{args.port}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()