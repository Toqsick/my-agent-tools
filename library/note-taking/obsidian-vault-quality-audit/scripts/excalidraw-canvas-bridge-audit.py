#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excalidraw/Canvas Bridge Auditor for Obsidian Vaults
---------------------------------------------------
Dieses Skript ergaenzt genuine-broken-links-audit.py um drei Bruecken:

1. excalidraw_stems: Mappt Note-Basename auf .excalidraw.md Pfad.
   Erlaubt Wikilinks wie [[Subagent-Briefing-Flow]] auf
   Subagent-Briefing-Flow.excalidraw.md aufzuloesen.

2. canvas_file_refs: Sammelt alle file-Referenzen aus Canvas-JSON.
   Prueft ob jede referenzierte Datei tatsaechlich existiert.

3. canvas_edge_targets: Sammelt alle edge-Ziele aus Canvas-JSON.
   Prueft ob sie auf existierende Notes/Canvases zeigen.

Verwendung:
  python3 excalidraw-canvas-bridge-audit.py "/path/to/vault"
"""

import os
import re
import json
import sys

def audit_bridges(vault_path):
    if not os.path.exists(vault_path):
        print("FEHLER: Pfad '" + vault_path + "' existiert nicht.")
        sys.exit(1)

    md_files = []
    canvas_files = []
    excalidraw_files = []

    # 1. Verzeichnis-Scan
    for root, dirs, files in os.walk(vault_path):
        if ".obsidian" in root or ".trash" in root or "_templates" in root:
            continue
        for f in files:
            full_path = os.path.join(root, f)
            if f.endswith(".canvas"):
                canvas_files.append(full_path)
            elif f.endswith(".excalidraw.md"):
                excalidraw_files.append(full_path)
            elif f.endswith(".md"):
                md_files.append(full_path)

    # 2. Excalidraw-Stems (ohne .excalidraw.md)
    excalidraw_stems = {}
    for ef in excalidraw_files:
        rel = os.path.relpath(ef, vault_path)
        # basename ohne .excalidraw.md
        stem = os.path.basename(ef).replace(".excalidraw.md", "").lower()
        excalidraw_stems[stem] = rel

    # 3. MD-Stems
    md_stems = {}
    for m in md_files:
        stem = os.path.basename(m).replace(".md", "").lower()
        md_stems[stem] = os.path.relpath(m, vault_path).replace(".md", "")

    # 4. Canvas-Stems
    canvas_stems = {}
    for c in canvas_files:
        stem = os.path.basename(c).lower()
        canvas_stems[stem] = os.path.relpath(c, vault_path)

    # 5. Pruefe Canvas-File-Refs
    canvas_file_refs_broken = []
    canvas_edge_targets_broken = []
    canvas_count = 0
    edge_total = 0
    file_ref_total = 0

    for cf in canvas_files:
        canvas_count += 1
        try:
            with open(cf, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except Exception as e:
            canvas_file_refs_broken.append({
                "canvas": os.path.relpath(cf, vault_path),
                "error": "file read: " + str(e)
            })
            continue

        # YAML-Frontmatter behandeln: falls Datei mit --- beginnt,
        # JSON steckt hinter dem zweiten ---
        stripped = raw
        if stripped.startswith("---"):
            parts = stripped.split("---", 2)
            if len(parts) >= 3:
                stripped = parts[2]

        try:
            d = json.loads(stripped)
        except Exception as e:
            canvas_file_refs_broken.append({
                "canvas": os.path.relpath(cf, vault_path),
                "error": "json parse: " + str(e)
            })
            continue

        rel_canvas = os.path.relpath(cf, vault_path)

        # File-Refs
        for node in d.get("nodes", []):
            if node.get("type") == "file":
                file_ref_total += 1
                fref = node.get("file", "")
                target = os.path.join(vault_path, fref)
                if not os.path.exists(target):
                    canvas_file_refs_broken.append({
                        "canvas": rel_canvas,
                        "missing_file_ref": fref
                    })

        # Edge-Targets
        for edge in d.get("edges", []):
            edge_total += 1
            # Edge hat 'endNode' oder 'fromNode'/'toNode'
            for key in ["endNode", "toNode"]:
                target_id = edge.get(key, "")
                if not target_id:
                    continue
                # Suche Node mit dieser ID
                target_node = None
                for n in d.get("nodes", []):
                    if n.get("id") == target_id:
                        target_node = n
                        break
                if target_node is None:
                    canvas_edge_targets_broken.append({
                        "canvas": rel_canvas,
                        "edge_id": edge.get("id", "?"),
                        "missing_target_id": target_id
                    })
                    break

    # 6. Pruefe Excalidraw-Stem-Aufloesung
    excalidraw_stem_check = []
    # Sammle Wikilinks aus MD-Files (ohne Code-Bloecke)
    wikilink_pattern = re.compile(r"\[\[([^\]]+)\]\]")
    for m in md_files:
        try:
            with open(m, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            continue
        # Code-Bloecke entfernen
        clean = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        clean = re.sub(r"`.*?`", "", clean)
        rel_path = os.path.relpath(m, vault_path).replace(".md", "")
        for match in wikilink_pattern.findall(clean):
            link_target = re.split(r"[|#]", match)[0].strip().lower()
            if not link_target or link_target.startswith("<"):
                continue
            # Wenn Wikilink nur als bare Basename existiert und NICHT als MD-Stem
            # aber ALS Excalidraw-Stem existiert: das ist die Bridge-Aufloesung
            if link_target not in md_stems and link_target in excalidraw_stems:
                excalidraw_stem_check.append({
                    "source": rel_path,
                    "wikilink": match,
                    "resolves_to": excalidraw_stems[link_target]
                })

    # 7. Bericht
    print("")
    print("=" * 60)
    print("  EXCALIDRAW/CANVAS BRIDGE AUDIT (Phase 7, 2026-07-22)")
    print("=" * 60)
    print("  Canvases gefunden:        " + str(canvas_count))
    print("  Excalidraws gefunden:     " + str(len(excalidraw_files)))
    print("  Canvas-File-Refs Total:   " + str(file_ref_total))
    print("  Canvas-Edges Total:       " + str(edge_total))
    print("  Canvas-File-Refs Broken:  " + str(len(canvas_file_refs_broken)))
    print("  Canvas-Edge-Targets Broken: " + str(len(canvas_edge_targets_broken)))
    print("  Excalidraw-Bridge-Aufloesungen: " + str(len(excalidraw_stem_check)))
    print("=" * 60)

    if canvas_file_refs_broken:
        print("")
        print("BROKEN CANVAS FILE-REFS:")
        for b in canvas_file_refs_broken:
            if "error" in b:
                print("  " + b["canvas"] + ": " + b["error"])
            else:
                print("  " + b["canvas"] + " verweist auf fehlende Datei: " + b["missing_file_ref"])

    if canvas_edge_targets_broken:
        print("")
        print("BROKEN CANVAS EDGE-TARGETS:")
        for b in canvas_edge_targets_broken:
            print("  " + b["canvas"] + " Edge " + b["edge_id"] + " zeigt auf unbekannte Node-ID: " + b["missing_target_id"])

    if excalidraw_stem_check:
        print("")
        print("EXCALIDRAW-BRIDGE-AUFLOESUNGEN (Wikilink ohne .excalidraw.md-Suffix):")
        for b in excalidraw_stem_check:
            print("  " + b["source"] + ": [[" + b["wikilink"] + "]] -> " + b["resolves_to"])

    # Exit-Code: 0 wenn alles clean, 1 wenn Bridges defekt
    if canvas_file_refs_broken or canvas_edge_targets_broken:
        sys.exit(1)
    else:
        print("")
        print("STATUS: Alle Bruecken intakt.")
        sys.exit(0)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    audit_bridges(path)