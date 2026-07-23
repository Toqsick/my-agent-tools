#!/usr/bin/env python3
"""
generate-download-helper.py — Generiert HTML-Download-Helper für Mod-Collections

Verwendung:
    python3 generate-download-helper.py <mods-json> <output-html>

Input-JSON-Format (Liste von Dicts):
    [{"id": 11359, "cat": "Visuals", "name": "Mod-Name"}, ...]

Output: Selbstständige HTML-Datei mit allen Mod-Links + Progress-Tracker.
User öffnet sie im Browser, klickt jeden Link → Nexus-Page → "Manual Download".
Klickt auf ✓ done für Überblick. Status wird im localStorage gespeichert.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{title} — Download Helper</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: #e0e0e0; }}
h1 {{ color: #fcee0a; }}
.mod {{ display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-bottom: 1px solid #333; }}
.mod:hover {{ background: #2a2a2a; }}
.mod a {{ color: #00d4ff; text-decoration: none; flex: 1; }}
.mod a:hover {{ text-decoration: underline; }}
.cat {{ font-size: 0.75em; color: #888; padding: 2px 6px; background: #2a2a2a; border-radius: 3px; white-space: nowrap; }}
.done {{ opacity: 0.4; }}
.done a {{ text-decoration: line-through; }}
button {{ padding: 4px 8px; background: #333; color: #fff; border: 1px solid #555; cursor: pointer; }}
button:hover {{ background: #555; }}
.controls {{ position: sticky; top: 0; background: #1a1a1a; padding: 12px; border-bottom: 2px solid #fcee0a; z-index: 100; }}
#progress {{ color: #fcee0a; font-weight: bold; }}
.id {{ color: #666; font-family: monospace; }}
</style>
</head>
<body>
<h1>🐝 {title} — {count} Mods zum Klicken</h1>
<div class="controls">
<span id="progress">0 / {count}</span> erledigt |
<button onclick="markAll()">Reset (alle auf offen)</button>
<button onclick="exportList()">Liste exportieren</button>
</div>
<div id="mod-list"></div>
<script>
const STORAGE_KEY = 'cod-download-progress-v1';
const mods = {mods_json};
const list = document.getElementById('mod-list');

// Load saved state
const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');

mods.forEach((m, i) => {{
    const div = document.createElement('div');
    div.className = 'mod' + (saved[m.id] ? ' done' : '');
    div.id = 'mod-' + m.id;
    div.innerHTML = `
        <span class="id" style="width:50px;">${{i+1}}.</span>
        <span class="cat">${{m.cat}}</span>
        <a href="https://www.nexusmods.com/cyberpunk2077/mods/${{m.id}}?tab=files" target="_blank">${{m.name}}</a>
        <button onclick="markDone(${{m.id}})">✓ done</button>
    `;
    list.appendChild(div);
}});

function markDone(id) {{
    document.getElementById('mod-' + id).classList.add('done');
    const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
    state[id] = true;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    updateProgress();
}}

function updateProgress() {{
    const done = document.querySelectorAll('.done').length;
    document.getElementById('progress').textContent = done + ' / ' + mods.length;
}}

function markAll() {{
    if (!confirm('Wirklich alle zurücksetzen?')) return;
    document.querySelectorAll('.mod').forEach(d => d.classList.remove('done'));
    localStorage.removeItem(STORAGE_KEY);
    updateProgress();
}}

function exportList() {{
    const done = Array.from(document.querySelectorAll('.done')).map(d => d.id.replace('mod-', ''));
    const todo = mods.filter(m => !done.includes(String(m.id)));
    const text = 'DONE:\\n' + done.join('\\n') + '\\n\\nTODO:\\n' + todo.map(m => `${{m.id}}\\t${{m.cat}}\\t${{m.name}}`).join('\\n');
    navigator.clipboard.writeText(text).then(() => alert('Liste in Clipboard kopiert!'));
}}

updateProgress();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("Verwendung: python3 generate-download-helper.py <mods-json> <output-html>")
        sys.exit(1)

    mods_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    with open(mods_file) as f:
        mods = json.load(f)

    # Kompakte Liste
    simple = [{"id": m["id"], "cat": m.get("category", "Unknown"), "name": m["name"]} for m in mods]

    title = mods_file.stem.replace("-", " ").replace("_", " ").title()
    html = HTML_TEMPLATE.format(
        title=title,
        count=len(simple),
        mods_json=json.dumps(simple),
    )

    output_file.write_text(html)
    print(f"✅ Download-Helper erstellt: {output_file}")
    print(f"   Mods: {len(simple)}")
    print(f"   Öffne im Browser: file://{output_file.absolute()}")


if __name__ == "__main__":
    main()