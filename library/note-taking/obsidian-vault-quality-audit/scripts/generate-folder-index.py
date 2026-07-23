#!/usr/bin/env python3
"""
generate-folder-index.py - Generiert Folder-INDEX.md fuer einen Obsidian-Vault-Ordner.

Verwendung:
    python3 generate-folder-index.py <vault-root> <ordner-relativ> [optionen]

Optionen:
    --with-moc-hub <Name>   WikiLink-Bezugspunkt fuer MOC-Hub (Sektion "## Hub (MOC)").
                            Kann mehrfach angegeben werden fuer mehrere Sub-Hubs.
                            Alias: --moc <Name>
    --max-subdir-listing N  Maximalanzahl der Files pro Subdir in der Listing-Sektion
                            (default: 5). Rest wird als "... und M weitere" angezeigt.

Output:
    Erstellt/aktualisiert <ordner>/INDEX.md mit typ=index-note Frontmatter
    gemaess Frontmatter-Schema v1.4.0 Section 9.1.

Pitfalls:
- Frontmatter-Patch OHNE replace_all (Patch-Substring-Mehrdeutigkeit vermeiden)
- YAML-Frontmatter mit korrekten Datums-Formaten (ISO YYYY-MM-DD)
- file-count dynamisch berechnen
- Subdir-Section ueberspringen wenn leer
- --moc kann mehrfach genutzt werden; Reihenfolge der Hubs bleibt erhalten
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def scan_folder(folder: Path) -> dict:
    """Sammelt Strukturinformationen ueber einen Ordner (ohne INDEX.md selbst)."""
    md_files = []
    subdirs = {}
    last_mod_global = folder.stat().st_mtime

    for entry in sorted(folder.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            sub_md = list(entry.rglob("*.md"))
            subdirs[entry.name] = {
                "count": len(sub_md),
                "last_mod": max((f.stat().st_mtime for f in sub_md), default=entry.stat().st_mtime),
            }
            last_mod_global = max(last_mod_global, subdirs[entry.name]["last_mod"])
        elif entry.suffix == ".md" and entry.name != "INDEX.md":
            md_files.append(entry)

    return {
        "md_files": md_files,
        "subdirs": subdirs,
        "last_mod_global": last_mod_global,
    }


def render_index(
    folder: Path,
    info: dict,
    vault_root: Path,
    moc_hubs: list = None,
    max_subdir_listing: int = 5,
) -> str:
    """Generiert den INDEX.md-Inhalt.

    Args:
        folder: Vault-Ordner, dessen INDEX erstellt wird.
        info: Ergebnis von scan_folder().
        vault_root: Wurzel des Obsidian-Vaults (fuer Frontmatter-Bezug).
        moc_hubs: Liste von MOC-Namen, die als WikiLink in der "## Hub (MOC)"-Sektion
            verlinkt werden. Reihenfolge bleibt erhalten.
        max_subdir_listing: Max. Anzahl Files pro Subdir-Listing, Rest als "... und M weitere".
    """
    if moc_hubs is None:
        moc_hubs = []

    folder_rel = folder.relative_to(vault_root)
    md_files = info["md_files"]
    subdirs = info["subdirs"]
    last_mod = datetime.fromtimestamp(info["last_mod_global"]).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    file_count = len(md_files) + sum(s["count"] for s in subdirs.values())

    # Folder-slug fuer Tags ableiten
    folder_slug = str(folder_rel).lower().replace(" ", "-").replace("/", "-")
    if folder_slug == ".":
        folder_slug = "vault-root"

    lines = []
    lines.append("---")
    lines.append("tags:")
    lines.append(f"  - index")
    lines.append(f"  - {folder_slug}")
    lines.append("  - backup")
    lines.append("typ: index-note")
    lines.append(f"erstellt: {today}")
    lines.append(f"letzter-check: {today}")
    lines.append(f"zweck: backup-listing-{folder.name.lower()}")
    lines.append(f"ordner: {folder_rel}")
    lines.append(f"file-count: {file_count}")
    lines.append("version: 1.0.0")
    lines.append("status: aktiv")
    lines.append("---")
    lines.append("")
    lines.append(f"# INDEX — {folder.name}/")
    lines.append("")
    lines.append(f"> Backup-Listing fuer `{folder_rel}/`. Vollstaendige Inhaltsverdichtung: MOC-System (siehe WikiLinks unten).")
    lines.append("")

    # MOC-Hub-Sektion (vor Struktur, damit sie prominent erscheint)
    if moc_hubs:
        lines.append("## Hub (MOC)")
        lines.append("")
        lines.append("Verknuepfung mit dem Map-of-Content-System dieses Bereichs:")
        lines.append("")
        for hub in moc_hubs:
            lines.append(f"- `[[{hub}]]`")
        lines.append("")
        # Frontmatter-Eintrag nur setzen, wenn genau ein Hub vorhanden ist
        if len(moc_hubs) == 1:
            lines.append(f"*Single-Hub-Modus: `[[{moc_hubs[0]}]]`*")
        else:
            lines.append(f"*Multi-Hub-Modus: {len(moc_hubs)} Sub-Hubs verknuepft.*")
        lines.append("")

    # Strukturkarte
    lines.append("## Struktur")
    lines.append("")
    lines.append(f"| Pfad | Files | Letzte Aenderung |")
    lines.append(f"|---|---|---|")
    if md_files:
        last_mod_root = max((f.stat().st_mtime for f in md_files), default=folder.stat().st_mtime)
        last_mod_root_str = datetime.fromtimestamp(last_mod_root).strftime("%Y-%m-%d")
        lines.append(f"| (root) | {len(md_files)} | {last_mod_root_str} |")
    for sd, info_sd in subdirs.items():
        last_mod_sd = datetime.fromtimestamp(info_sd["last_mod"]).strftime("%Y-%m-%d")
        lines.append(f"| `{sd}/` | {info_sd['count']} | {last_mod_sd} |")
    lines.append(f"| **Total** | **{file_count}** | {last_mod} |")
    lines.append("")

    # Files im Root
    if md_files:
        lines.append("## Files (root)")
        lines.append("")
        for f in md_files:
            mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            size = f.stat().st_size
            lines.append(f"- `[[{f.stem}]]` ({size} bytes, zuletzt geaendert {mod})")
        lines.append("")

    # Subdirs mit Files (cap durch max_subdir_listing)
    for sd, info_sd in subdirs.items():
        sd_path = folder / sd
        sd_md = sorted(sd_path.rglob("*.md"))
        if sd_md:
            lines.append(f"## {sd}/")
            lines.append("")
            for f in sd_md[:max_subdir_listing]:
                rel = f.relative_to(folder)
                mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
                lines.append(f"- `[[{f.stem}]]` ({rel.parent if rel.parent != Path('.') else 'root'}) ({mod})")
            if len(sd_md) > max_subdir_listing:
                lines.append(f"- ... und {len(sd_md) - max_subdir_listing} weitere")
            lines.append("")

    # Pflege
    lines.append("## Pflege")
    lines.append("")
    lines.append("- Generiert via `generate-folder-index.py`")
    if moc_hubs:
        lines.append(f"- MOC-Hub(s): {', '.join(f'`[[{h}]]`' for h in moc_hubs)}")
    lines.append(f"- Max Subdir-Listing: {max_subdir_listing}")
    lines.append("- Manuell nur fuer Spezial-Notizen (Hubs, Archiv-Marker)")
    lines.append(f"- Generiert am {today}")
    lines.append("")

    return "\n".join(lines)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generiert Folder-INDEX.md fuer einen Obsidian-Vault-Ordner.",
    )
    parser.add_argument("vault_root", help="Wurzel-Pfad des Obsidian-Vaults")
    parser.add_argument("folder_rel", help="Relativer Pfad zum Ordner innerhalb des Vaults")
    parser.add_argument(
        "--with-moc-hub",
        "--moc",
        dest="moc_hubs",
        action="append",
        default=[],
        metavar="NAME",
        help="WikiLink-Bezugspunkt fuer MOC-Hub (mehrfach nutzbar fuer Sub-Hubs)",
    )
    parser.add_argument(
        "--max-subdir-listing",
        dest="max_subdir_listing",
        type=int,
        default=5,
        metavar="N",
        help="Max. Files pro Subdir-Listing (default: 5)",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    vault_root = Path(args.vault_root).resolve()
    folder_rel = args.folder_rel
    folder = (vault_root / folder_rel).resolve()

    if not folder.exists():
        print(f"Fehler: Ordner {folder} existiert nicht")
        sys.exit(1)

    if args.max_subdir_listing < 1:
        print(f"Fehler: --max-subdir-listing muss >= 1 sein (war: {args.max_subdir_listing})")
        sys.exit(1)

    info = scan_folder(folder)
    content = render_index(
        folder,
        info,
        vault_root,
        moc_hubs=args.moc_hubs,
        max_subdir_listing=args.max_subdir_listing,
    )

    output = folder / "INDEX.md"
    output.write_text(content, encoding="utf-8")
    print(f"OK: {output} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
