#!/usr/bin/env python3
"""Wait for MiroFish report to complete — polls GET /api/report/{id} every 30s.
Usage: python3 report-waiter.py <report_id> [output_path]

Writes to LOG: /tmp/mirofish_report_<id>.log
Saves report to: output_path or MiroFish/report_<id>.md
"""
import subprocess, json, time, sys, os

RID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MIROFISH_REPORT_ID")
if not RID:
    print("Usage: report-waiter.py <report_id> [output_path]")
    sys.exit(1)

OUT = sys.argv[2] if len(sys.argv) > 2 else None
LOG = f"/tmp/mirofish_report_{RID}.log"
BASE = os.path.expanduser("~/10-Projekte/20-experimental/MiroFish")
URL = f"http://localhost:5001/api/report/{RID}"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def get_json():
    try:
        r = subprocess.run(["curl", "-s", "-m", "15", URL],
                           capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout).get("data", {})
    except Exception as e:
        return {"status": "network_error", "error": str(e)}

log(f"=== Report-Waiter for {RID} Started ===")

for i in range(60):  # 30 min max
    d = get_json()
    status = d.get("status", "?")
    md_len = len(d.get("markdown_content", ""))
    outline = d.get("outline", {})
    sections = len(outline.get("sections", [])) if isinstance(outline, dict) else 0

    # Markdown content available OR outline has content
    has_content = md_len > 500 or (status == "completed" and md_len > 100)

    log(f"poll {i+1:2}: status={status:10} md_len={md_len:5} outline_sections={sections}")

    if status == "completed" and has_content:
        out_path = OUT or f"{BASE}/report_{RID}.md"
        with open(out_path, "w") as f:
            f.write(d.get("markdown_content", ""))
        log(f"DONE: saved {md_len} chars to {out_path}")
        print(f"SAVED:{out_path}", flush=True)
        break
    if status == "failed":
        log(f"FAIL: {d.get('error','?')[:200]}")
        sys.exit(1)

    time.sleep(30)
else:
    log("TIMEOUT: report not completed after 30 min")
    sys.exit(1)

log(f"=== Done: {time.strftime('%H:%M:%S')} ===")
