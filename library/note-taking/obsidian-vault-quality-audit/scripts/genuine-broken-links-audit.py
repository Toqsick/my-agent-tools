#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genuine Broken Links Auditor for Obsidian Vaults
------------------------------------------------
Dieses Skript fuehrt einen praezisen Link-Audit im Obsidian-Vault durch.
Es eliminiert typische Fehlalarme (False Positives), indem es:
1. Alle YAML-Frontmatter-Aliase einliest und kartografiert.
2. Code-Bloecke (sowohl dreifache Backticks als auch Inline-Code) vor der Analyse entfernt.
3. Loescht oder ignoriert Platzhalter-Formate wie [[<Platzhalter>]] oder [[…]].
4. Alle .canvas-Dateien und statische Anhaenge (Bilder, PDFs) loest.

Verwendung:
  python3 genuine-broken-links-audit.py "/path/to/vault"
"""

import os
import re
import yaml
import sys

def strip_code_blocks(text):
    # Entfernt mehrzeilige Code-Bloecke (```...```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Entfernt einzeiligen Inline-Code (`...`)
    text = re.sub(r"`.*?`", "", text)
    return text

def audit_vault(vault_path):
    if not os.path.exists(vault_path):
        print(f"❌ Fehler: Pfad '{vault_path}' existiert nicht.")
        sys.exit(1)
        
    md_files = []
    canvas_files = []
    attachment_files = []
    
    # 1. Systematischer Verzeichnis-Scan
    for root, dirs, files in os.walk(vault_path):
        # Ignoriere versteckte Ordner und Papierkorb
        if ".obsidian" in root or ".trash" in root or "_templates" in root:
            continue
        for f in files:
            full_path = os.path.join(root, f)
            if f.endswith(".md"):
                md_files.append(full_path)
            elif f.endswith(".canvas"):
                canvas_files.append(f)
            else:
                attachment_files.append(f)
                
    # Stems und Aliase mappen
    all_stems = {os.path.basename(f).replace(".md", "").lower(): os.path.relpath(f, vault_path).replace(".md", "") for f in md_files}
    excalidraw_stems = {os.path.basename(f).replace(".excalidraw.md", "").lower(): os.path.relpath(f, vault_path).replace(".excalidraw.md", "") for f in md_files if f.endswith(".excalidraw.md")}
    canvas_stems = {c.lower(): c for c in canvas_files}
    attachment_stems = {a.lower(): a for a in attachment_files}
    
    aliases_map = {}
    file_contents = {}
    line_counts = {}
    
    # 2. YAML Frontmatter und Aliase parsen
    for f in md_files:
        rel_path = os.path.relpath(f, vault_path).replace(".md", "")
        try:
            with open(f, "r", encoding="utf-8-sig", errors="ignore") as fh:
                content = fh.read()
        except Exception as e:
            print(f"⚠️ Lesefehler bei {rel_path}: {e}")
            continue
            
        file_contents[rel_path] = content
        line_counts[rel_path] = len(content.splitlines())
        
        # Frontmatter auslesen
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                try:
                    fm = yaml.safe_load(fm_text)
                    if fm and "aliases" in fm:
                        aliases = fm["aliases"]
                        if isinstance(aliases, list):
                            for a in aliases:
                                aliases_map[str(a).lower()] = rel_path
                        elif isinstance(aliases, str):
                            aliases_map[aliases.lower()] = rel_path
                except Exception:
                    # Ignoriere YAML Syntaxfehler bei der Analyse
                    pass

    # 3. Echte kaputte Links ermitteln (Code-Bloecke bereinigen!)
    genuine_broken = {}
    total_checked_links = 0
    
    for rel_path, content in file_contents.items():
        clean_content = strip_code_blocks(content)
        matches = re.findall(r"\[\[([^\]]+)\]\]", clean_content)
        
        for m in matches:
            # Schritt 1: Escaped Pipes (\|) normalisieren -> literaler Pipe
            # In Obsidian-Wikilinks maskiert \| einen Pipe, der NICHT als
            # Alias-Trenner gemeint ist. Wir wandeln ihn zurueck zu | und
            # koennen danach sauber am ersten Pipe splitten. Übrig bleibt
            # ggf. ein Backslash am Zielende, den wir ebenfalls entfernen.
            normalized = m.replace("\\|", "|").replace("\\\\", "")
            # Schritt 2: Anzeigename (alles ab erstem ungeschuetzten |) abtrennen,
            # ebenso evtl. Section-Anker (#Section)
            link_target = re.split(r"[|#]", normalized)[0].strip()
            # Verbleibende einzelne Backslashes (z.B. bei "|INDEX"-Escape-Tabellen-
            # notation) entfernen -- sie gehoeren nicht zum Dateinamen.
            link_target = link_target.replace("\\", "")
            if not link_target:
                continue

            # Filter fuer bewusste Platzhalter-Notationen
            if link_target.startswith("<") and link_target.endswith(">") or link_target == "…":
                continue

            total_checked_links += 1
            target_lower = link_target.lower()

            # Aufloesungs-Reihenfolge:
            # a) Existiert die Note als Stammdatei?
            if target_lower in all_stems:
                continue
            # b) Existiert ein Frontmatter-Alias darauf?
            if target_lower in aliases_map:
                continue
            # c) Ist es ein Canvas-File? (per Basename, da Wikilinks volle Pfade tragen koennen)
            if target_lower in canvas_stems or target_lower + ".canvas" in canvas_stems:
                continue
            if target_lower.endswith(".canvas") and os.path.basename(target_lower) in canvas_stems:
                continue
            # c2) Ist es ein Excalidraw-File (mit oder ohne .excalidraw.md-Suffix)?
            #     Lookup sowohl ueber basename-only als auch ueber vollen Pfad.
            target_basename = os.path.basename(target_lower)
            bare_exc = target_basename[:-len(".excalidraw.md")] if target_lower.endswith(".excalidraw.md") else target_basename
            if bare_exc in excalidraw_stems:
                continue
            # zusaetzlich: voller Pfad ohne Suffix ist auch gueltig (relpath-key)
            if target_lower.endswith(".excalidraw.md"):
                if target_lower[:-len(".excalidraw.md")] in {k for k in all_stems}:
                    continue
            # d) Ist es ein sonstiger Anhang?
            if target_lower in attachment_stems:
                continue
                
            # Wenn keines greift, ist der Link definitiv defekt
            genuine_broken.setdefault(rel_path, []).append(m)
            
    # 4. Berichterstattung
    broken_count = sum(len(v) for v in genuine_broken.values())
    print("\n" + "="*50)
    print("      🌸 YUNO OBSIDIAN VAULT AUDIT-REPORT 🌸")
    print("="*50)
    print(f"  Notes gesamt:          {len(md_files)}")
    print(f"  Gepruefte Links:       {total_checked_links}")
    print(f"  Defekte Links (echt):  {broken_count}")
    print("="*50)
    
    if broken_count > 0:
        print("\n🚨 GEFUNDENE DEFEKTE LINKS:")
        for f, links in sorted(genuine_broken.items()):
            print(f"\n📂 In Datei: {f}.md")
            for l in links:
                print(f"  - [[{l}]]")
        sys.exit(1)
    else:
        print("\n🎉 Exzellent! Keine echten defekten Links im gesamten Vault gefunden.")
        sys.exit(0)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    audit_vault(path)
