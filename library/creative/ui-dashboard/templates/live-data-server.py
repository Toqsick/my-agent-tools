#!/usr/bin/env python3
"""
Live-Data-Provider Template für Dashboards.
Sammelt Daten aus: Hermes-API, CLI-Output, psutil, File-Scans.
Liefert JSON unter /api/data aus.

Usage:
  python3 server.py                # Startet auf Port 8767
  curl http://127.0.0.1:8767/api/data  # JSON abrufen

Customization:
  - PASST DIE FUNCTIONS unten an deine Datenquellen an
  - Ändere PORT falls belegt
  - Setze CACHE_TTL je nach Datenqualität
"""

import json
import subprocess
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path

# === CONFIG ===
PORT = 8767
CACHE_TTL = 30  # Sekunden — CLI-Output cachen

# === DEPS CHECK ===
try:
    import psutil
except ImportError:
    print("⚠️  psutil fehlt: pip install psutil --user")
    psutil = None

try:
    import urllib.request
except ImportError:
    urllib = None

# === CACHE ===
_cache = {}
_cache_ts = {}

def cached(key, fn, ttl=CACHE_TTL):
    """Cache-Wrapper — verhindert dass CLI-Befehle bei jedem Request ausgefuehrt werden.

    WARNING KNOWN BUG PATTERN: _cache_ts[key] = ttl  (speichert TTL-Zahl statt Timestamp)
         FIX:              _cache_ts[key] = now   (aktueller Unix-Timestamp)
         Symptom: Cache niemals getroffen -> jede Antwort 2-3s -> Browser zeigt skeleton.
         Diagnose: _cache_ts-Werte < 1000 -> Bug aktiv. Immer MITTIG pruefen!
    """
    now = time.time()
    if key in _cache and (now - _cache_ts.get(key, 0)) < ttl:
        return _cache[key]
    val = fn()
    _cache[key] = val
    _cache_ts[key] = now    # <-- HIER: IMMER `now`, NIEMALS `ttl` (!!)
    return val


# ================================================================
# DATA SOURCES — passe diese an deine Bedürfnisse an
# ================================================================

def get_api_status(url="http://127.0.0.1:9119/api/status"):
    """Holt Daten von einem offenen API-Endpoint (kein Auth nötig)."""
    if not urllib:
        return None
    try:
        r = urllib.request.urlopen(url, timeout=5)
        return json.loads(r.read())
    except Exception:
        return None


def run_cli(args, binary="hermes", timeout=10):
    """Führt einen CLI-Befehl aus und gibt stdout zurück."""
    try:
        r = subprocess.run([binary] + args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def get_system_stats():
    """System-Stats via psutil."""
    if not psutil:
        return {}
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    load1, load5, load15 = psutil.getloadavg()
    try:
        temps = psutil.sensors_temperatures()
        cpu_temp = list(temps.values())[0][0].current if temps else None
    except Exception:
        cpu_temp = None

    return {
        "cpu": {
            "cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.5),
            "load_1m": round(load1, 2),
            "load_5m": round(load5, 2),
            "load_15m": round(load15, 2),
        },
        "memory": {
            "total_gb": round(vm.total / (1024**3), 1),
            "used_gb": round(vm.used / (1024**3), 1),
            "percent": vm.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": round(disk.used / disk.total * 100, 1),
        },
        "cpu_temp": cpu_temp,
        "uptime": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
    }


def build_payload():
    """Sammelt alle Datenquellen in ein JSON-Payload."""
    api_data = get_api_status() or {}
    system = get_system_stats()

    # === HIER DEINE DATENQUELLEN ERGÄNZEN ===
    # Beispiel:
    # skills_count = cached("skills", lambda: run_cli(["skills", "list"]).count("enabled"), ttl=60)
    # profiles = cached("profiles", lambda: parse_profiles(run_cli(["profile", "list"])), ttl=60)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "api": api_data,
        "system": system,
        # "skills": {"enabled": skills_count},
        # "profiles": profiles,
    }


# ================================================================
# HTTP HANDLER — nicht ändern除非 Port anders sein soll
# ================================================================

class DataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/data", "/api/data/"):
            try:
                payload = build_payload()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")  # CORS für Browser
                self.end_headers()
                self.wfile.write(json.dumps(payload, ensure_ascii=False, indent=2).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Leise — nur Errors


if __name__ == "__main__":
    print(f"🚀 Data-Provider auf Port {PORT}")
    print(f"   GET /api/data  — JSON-Daten")
    print(f"   GET /health    — Health-Check")
    print(f"   Ctrl+C zum Stoppen")
    server = HTTPServer(("127.0.0.1", PORT), DataHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Gestoppt")
