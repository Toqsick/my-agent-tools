import os
import re
import yaml
import pathlib

def run_vault_audit(vault_path):
    vault = pathlib.Path(vault_path)
    if not vault.exists():
        print(f"❌ Vault path does not exist: {vault_path}")
        return

    md_files = list(vault.rglob("*.md"))
    # Skip .obsidian, .trash, _templates
    md_files = [f for f in md_files if not any(p in f.parts for p in [".obsidian", ".trash", "_templates"])]

    # 1. Map stems
    all_stems = {f.stem.lower(): str(f.relative_to(vault)).replace(".md", "") for f in md_files}

    # 2. Map aliases and parse files
    aliases_map = {}
    file_contents = {}
    line_counts = {}

    for f in md_files:
        rel_path = str(f.relative_to(vault)).replace(".md", "")
        try:
            content = f.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception as e:
            continue
        
        file_contents[rel_path] = content
        line_counts[rel_path] = len(content.splitlines())
        
        # Parse frontmatter yaml aliases
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
                    pass

    # 3. Map canvas files
    canvas_files = list(vault.rglob("*.canvas"))
    canvas_stems = {c.stem.lower(): c.name for c in canvas_files}

    # 4. Map other attachments
    attachment_files = [f for f in vault.rglob("*") if f.is_file() and f.suffix not in [".md", ".canvas"]]
    attachment_stems = {a.name.lower(): a.name for a in attachment_files}

    def strip_code_blocks(text):
        # Remove triple backtick code blocks
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        # Remove single backtick inline code
        text = re.sub(r"`.*?`", "", text)
        return text

    genuine_broken = {}
    outlinks_by_file = {}
    inlinks_by_file = {r: set() for r in file_contents}

    for rel_path, content in file_contents.items():
        clean_content = strip_code_blocks(content)
        matches = re.findall(r"\[\[([^\]]+)\]\]", clean_content)
        resolved_links = set()
        
        for m in matches:
            link_target = re.split(r"[|#]", m)[0].strip()
            if not link_target:
                continue
            if link_target.startswith("<") and link_target.endswith(">") or link_target == "…":
                continue
                
            target_lower = link_target.lower()
            if target_lower in all_stems:
                resolved_links.add(all_stems[target_lower])
            elif target_lower in aliases_map:
                resolved_links.add(aliases_map[target_lower])
            elif target_lower in canvas_stems or target_lower + ".canvas" in canvas_stems:
                # Valid canvas reference
                continue
            elif target_lower in attachment_stems:
                # Valid attachment reference
                continue
            else:
                genuine_broken.setdefault(rel_path, []).append(m)
                
        outlinks_by_file[rel_path] = resolved_links
        for rl in resolved_links:
            inlinks_by_file.setdefault(rl, set()).add(rel_path)

    # 5. Find orphans
    orphans = []
    for rel_path in inlinks_by_file:
        in_cnt = len(inlinks_by_file.get(rel_path, []))
        out_cnt = len(outlinks_by_file.get(rel_path, []))
        if in_cnt == 0 and out_cnt == 0:
            if "Willkommen" not in rel_path and "_moc" not in rel_path.lower() and "_readme" not in rel_path.lower():
                orphans.append(rel_path)

    # 6. Find thin notes
    thin_notes = []
    for rel_path, l_count in line_counts.items():
        if l_count < 40 and "_moc" not in rel_path.lower() and "moc -" not in rel_path.lower() and "_readme" not in rel_path.lower() and "willkommen" not in rel_path.lower():
            thin_notes.append((l_count, rel_path))

    # Output stats
    print(f"--- VAULT QUALITY AUDIT REPORT ---")
    print(f"Total Markdown Notes: {len(md_files)}")
    print(f"Genuine Broken Links: {sum(len(v) for v in genuine_broken.values())}")
    for f, links in sorted(genuine_broken.items()):
        print(f"  In [{f}]: {links}")
    print(f"Orphan Notes: {len(orphans)}")
    for o in sorted(orphans):
        print(f"  - {o}")
    print(f"Thin Notes (< 40 lines): {len(thin_notes)}")
    for count, o in sorted(thin_notes):
        print(f"  - {o} ({count} lines)")

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/home/bratan/Dokumente/Obsidian Vault"
    run_vault_audit(path)
