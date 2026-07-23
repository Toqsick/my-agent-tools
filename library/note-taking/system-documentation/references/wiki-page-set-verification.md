# Wiki Page-Set Verification

Standalone verification script for **1-Index + N-Category wiki page sets** (e.g. `Patterns-Index.md` + 6 `Pattern-*.md` files). Captures the gotchas from the greyscripts-repo pattern-page authoring session (2026-07-22).

## Was es prüft

1. **Glob-Double-Count** — `Pattern*.md` und `Patterns*.md` matchen beide `Patterns-Index.md`. `wc -l` zählt Zeilen, nicht unique Files → liefert N+1 statt N.
2. **Per-Page Quality-Gates** — Em-Dash ≤ 1, En-Dash = 0, Cross-Links ≥ 3 (Category) bzw. ≥ 10 (Index), Anti-Patterns-Punkte ≥ 3.
3. **Code-Snippet-Länge** — Greyscript-Blöcke ≤ 30 Zeilen pro Pattern.
4. **Strukturelle Pflicht-Sektionen** — Jede Category-Page braucht: Score, Datei, Meta, Zweck, Code-Pattern, Wann nutzen, Anti-Patterns, Verwandte Kategorien.
5. **Index↔Category Roundtrip** — Jede Category-Page verlinkt auf den Index, und der Index verlinkt auf jede Category-Page.

## Aufruf

```bash
python3 /path/to/skill/references/wiki-page-set-verification.py /path/to/wiki/
```

Exit-Code: 0 = alle Tests grün, 1 = mindestens ein Test rot.

## Skript

```python
#!/usr/bin/env python3
"""
wiki-page-set-verification.py — Self-Tests für 1-Index + N-Category Page-Sets.

Aufruf: python3 wiki-page-set-verification.py <wiki-verzeichnis>
Exit:   0 = OK, 1 = mindestens ein Test fehlgeschlagen
"""
import os
import re
import sys
from pathlib import Path


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {label}{(' — ' + detail) if detail else ''}")
    return ok


def main(wiki_dir: str) -> int:
    wiki = Path(wiki_dir)
    if not wiki.is_dir():
        print(f"ERROR: {wiki_dir} ist kein Verzeichnis")
        return 1

    # ── Test 1: Glob-Double-Count-Pitfall ───────────────────────────────
    print("Test 1: Glob-Double-Count-Pitfall (Pattern*.md + Patterns*.md)")
    raw_glob = sorted(
        list(wiki.glob("Pattern*.md")) + list(wiki.glob("Patterns*.md"))
    )
    unique = sorted(set(raw_glob))
    raw_count = len(raw_glob)
    unique_count = len(unique)
    ok = check(
        f"unique files = {unique_count}, raw glob = {raw_count}",
        unique_count == raw_count or raw_count - unique_count <= 1,
        f"diff={raw_count - unique_count}",
    )

    # ── Test 2: Struktur pro Page ────────────────────────────────────────
    print("\nTest 2: Per-Page Quality-Gates")
    all_ok = True
    for page in unique:
        text = page.read_text(encoding="utf-8")
        em = text.count("—")
        en = text.count("–")
        cross = len(re.findall(r"\]\((Pattern-[A-Za-z]+|Patterns-Index)\)", text))
        is_index = page.name.startswith("Patterns-") and not page.name.startswith(
            ("Pattern-A", "Pattern-B", "Pattern-C", "Pattern-D", "Pattern-E",
             "Pattern-F", "Pattern-G", "Pattern-H", "Pattern-I", "Pattern-L",
             "Pattern-M", "Pattern-N", "Pattern-R", "Pattern-S", "Pattern-T",
             "Pattern-V", "Pattern-W")
        )
        # Heuristic: Index-Page ist Patterns-Index.md
        is_index = page.name == "Patterns-Index.md"

        em_ok = check(f"{page.name}: em={em}", em <= 1, "≤ 1 erlaubt")
        en_ok = check(f"{page.name}: en={en}", en == 0, "0 erlaubt")
        link_min = 10 if is_index else 3
        link_ok = check(
            f"{page.name}: cross-links={cross}",
            cross >= link_min,
            f"≥ {link_min} erlaubt",
        )
        all_ok = all_ok and em_ok and en_ok and link_ok

    # ── Test 3: Code-Snippet-Länge ───────────────────────────────────────
    print("\nTest 3: Code-Snippet-Länge (≤ 30 Zeilen pro Block)")
    code_ok_all = True
    for page in unique:
        text = page.read_text(encoding="utf-8")
        for m in re.finditer(r"```greyscript\n(.*?)```", text, re.DOTALL):
            block = m.group(1).rstrip("\n")
            lines = block.count("\n") + 1 if block else 0
            if lines > 30:
                code_ok_all = False
                check(f"{page.name}: snippet {lines} Zeilen", False, "≤ 30")
    if code_ok_all:
        check("alle Snippets ≤ 30 Zeilen", True)

    # ── Test 4: Pflicht-Sektionen pro Category-Page ──────────────────────
    print("\nTest 4: Pflicht-Sektionen (nur Category-Pages, nicht Index)")
    required = ["Zweck", "Code-Pattern", "Wann nutzen", "Anti-Patterns", "Verwandte Kategorien"]
    sec_ok_all = True
    for page in unique:
        if page.name == "Patterns-Index.md":
            continue
        text = page.read_text(encoding="utf-8")
        for sec in required:
            ok = check(f"{page.name}: '{sec}'", sec in text)
            sec_ok_all = sec_ok_all and ok

    # ── Test 5: Index↔Category Roundtrip ─────────────────────────────────
    print("\nTest 5: Roundtrip-Links")
    idx = wiki / "Patterns-Index.md"
    if idx.exists():
        idx_text = idx.read_text(encoding="utf-8")
        for page in unique:
            if page.name == "Patterns-Index.md":
                continue
            stem = page.stem
            in_idx = f"({stem})" in idx_text
            in_page = "Patterns-Index" in (wiki / page.name).read_text(encoding="utf-8")
            check(
                f"Index ↔ {stem}",
                in_idx and in_page,
                f"idx→page={in_idx}, page→idx={in_page}",
            )

    # ── Gesamtergebnis ───────────────────────────────────────────────────
    print("\n" + ("=" * 50))
    print("ERGEBNIS: alle Tests grün" if all_ok and ok else "ERGEBNIS: FEHLER — siehe oben")
    return 0 if all_ok and ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <wiki-verzeichnis>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
```

## Pitfalls bei der Anwendung

1. **Nicht pro Page aggregiert prüfen** — eine Page mit 5 Em-Dashes fällt durch, auch wenn die anderen 0 haben. Das Skript printet pro Page einzeln.
2. **Nicht `grep` statt Skript nutzen** — die Tests sind aufeinander aufgebaut (Roundtrip braucht sowohl Index als auch Category); grep allein erwischt das nicht.
3. **Nicht bei Exit-Code 0 automatisch committen** — auch wenn das Skript grün ist, sollte der Mensch die Pages kurz querlesen (Em-Dash-Limit gilt pro Page, aber Stil-Konsistenz ist subjektiv).
4. **Glob-Double-Count ist erwartetes Verhalten** von `ls`/`Path.glob()` — das Skript meldet es als Warnung, nicht als Fehler, weil manche Setups bewusst beide Globs nutzen.

## Siehe auch

- `system-documentation/SKILL.md` → "1-Index + N-Category Page-Set Authoring" — Workflow und Template
- `system-documentation/SKILL.md` → "GitHub-Wiki vs Obsidian-Vault" — Format-Unterscheidung
- `system-documentation/SKILL.md` → "Qualitätskriterien für Audit-Reports" — Aggregat-Quality-Gates
- `self-test-document-generation.md` — allgemeine Markdown-Self-Tests