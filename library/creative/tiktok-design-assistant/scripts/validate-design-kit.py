#!/usr/bin/env python3
"""validate-design-kit.py — Validate a 4-file TikTok design kit for a given niche.

Usage: validate-design-kit.py <nische>
       PROJECT_ROOT=/custom/path validate-design-kit.py <nische>

Checks:
  1. All 4 expected files exist (brand-system, CSV, pitch-variants, anleitung)
  2. Brand-JSON valid + has required fields
  3. Pitch-JSON valid + has target nische + >= 10 variants
  4. CSV has 11 columns + >= 10 data rows
  5. No empty pitch cells (CSV-quoting-safe via csv module)
  6. CSV is ASCII (Umlauts correctly replaced ae/oe/ue/ss) OR UTF-8 with INFO
  7. Anleitung-MD has minimum content (>= 500 bytes + has headings)

Exit code: 0 = all checks pass, 1 = at least one error
"""

import csv
import json
import os
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <nische>")
        sys.exit(1)

    nische = sys.argv[1]

    project_root = Path(
        os.environ.get(
            "PROJECT_ROOT",
            "/home/bratan/10-Projekte/10-active/yuno-anon-tiktok-business",
        )
    )

    brand = project_root / "config" / "design" / f"brand-system-{nische}.json"
    csv_file = project_root / "data" / f"canva-bulk-create-{nische}.csv"
    pitch = project_root / "config" / "design" / "pitch-variants.json"
    anleitung = project_root / "docs" / "design" / f"canva-{nische}-anleitung.md"

    errors = 0

    print(f"=== TikTok Design Kit Validation: {nische} ===")
    print(f"Project root: {project_root}")
    print()

    # ---- 1. Existence ----
    files_to_check = [
        ("brand-system", brand),
        ("CSV", csv_file),
        ("pitch-variants", pitch),
        ("anleitung", anleitung),
    ]
    for name, path in files_to_check:
        if path.exists():
            print(f"[OK]   Found: {path}")
        else:
            print(f"[FAIL] Missing: {path}")
            errors += 1

    print()

    # ---- 2. Brand-JSON: valid syntax + required fields + schema drift ----
    REQUIRED_BRAND_FIELDS = [
        "brand_name_vorschlaege",
        "color_palette",
        "fonts",
        "voice",
        "logo_direction",
        "konsistenz_regeln",
    ]
    # Known-allowed extra fields (forward-compatible, non-error)
    BRAND_EXTRA_FIELDS = {
        "version",
        "created",
        "updated",
        "changelog",
        "description",
        "metadata",
        "tagline_vorschlaege",  # added in production 2026-07-15
        "nischen_spezifische_patterns",  # added in production 2026-07-15
    }
    if brand.exists():
        try:
            with open(brand) as f:
                brand_data = json.load(f)
            print("[OK]   brand-system JSON is valid")
            for field in REQUIRED_BRAND_FIELDS:
                if field not in brand_data:
                    print(f"[FAIL] brand-system missing required field: '{field}'")
                    errors += 1
                else:
                    print(f"[OK]   brand-system has '{field}'")
            # Warn on unknown fields (schema drift, not failure)
            unknown = set(brand_data.keys()) - set(REQUIRED_BRAND_FIELDS) - BRAND_EXTRA_FIELDS
            if unknown:
                print(
                    f"[INFO] brand-system has unknown fields (forward-compatible): "
                    f"{sorted(unknown)}"
                )
        except json.JSONDecodeError as e:
            print(f"[FAIL] brand-system JSON INVALID: {e}")
            errors += 1

    # ---- 3. Pitch-JSON: valid + target nische + >= 10 variants + schema drift ----
    PITCH_REQUIRED_NICHE_FIELDS = ["variants"]
    PITCH_EXTRA_FIELDS = {
        "version",
        "created",
        "updated",
        "changelog",
        "description",
        "metadata",
        "category",
        "current_pitch_for_bulk_csv",
    }
    if pitch.exists():
        try:
            with open(pitch) as f:
                pitch_data = json.load(f)
            print("[OK]   pitch-variants JSON is valid")
            niches = pitch_data.get("niches", {})
            if nische not in niches:
                print(
                    f"[FAIL] pitch-variants missing target nische '{nische}' "
                    f"(found: {list(niches.keys())})"
                )
                errors += 1
            else:
                variants = niches[nische].get("variants", [])
                if len(variants) < 10:
                    print(
                        f"[FAIL] pitch-variants['{nische}'].variants has only "
                        f"{len(variants)} entries (need >= 10)"
                    )
                    errors += 1
                else:
                    print(
                        f"[OK]   pitch-variants['{nische}'].variants has "
                        f"{len(variants)} entries (>= 10)"
                    )
                # Check nische-section schema drift
                unknown_nische_fields = (
                    set(niches[nische].keys())
                    - set(PITCH_REQUIRED_NICHE_FIELDS)
                    - PITCH_EXTRA_FIELDS
                )
                if unknown_nische_fields:
                    print(
                        f"[INFO] pitch-variants['{nische}'] has unknown fields "
                        f"(forward-compatible): {sorted(unknown_nische_fields)}"
                    )

            # Check top-level schema drift
            unknown_top = (
                set(pitch_data.keys()) - {"niches"} - PITCH_EXTRA_FIELDS
            )
            if unknown_top:
                print(
                    f"[INFO] pitch-variants has unknown top-level fields "
                    f"(forward-compatible): {sorted(unknown_top)}"
                )
        except json.JSONDecodeError as e:
            print(f"[FAIL] pitch-variants JSON INVALID: {e}")
            errors += 1

    # ---- 4. CSV: 11 columns + >= 10 data rows + no empty pitch + ASCII/UTF-8 ----
    if csv_file.exists():
        rows = []
        bom_detected = False
        try:
            # utf-8-sig auto-strips BOM if present
            with open(csv_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
            # Check if BOM was in file (heuristic: file starts with EF BB BF)
            with open(csv_file, "rb") as fb:
                first_bytes = fb.read(3)
                if first_bytes == b"\xef\xbb\xbf":
                    bom_detected = True
        except UnicodeDecodeError:
            # Fall back to latin-1 to still inspect
            with open(csv_file, newline="", encoding="latin-1") as f:
                rows = list(csv.reader(f))

        if not rows:
            print("[FAIL] CSV is empty (no header)")
            errors += 1
        else:
            header = rows[0]
            data_rows = rows[1:]
            n_cols = len(header)
            if n_cols != 11:
                print(f"[FAIL] CSV has {n_cols} columns (expected 11)")
                errors += 1
            else:
                print(f"[OK]   CSV has 11 columns")

            # Check row-width consistency (Schema-Drift-Detection)
            width_counts = {}
            for row in data_rows:
                w = len(row)
                width_counts[w] = width_counts.get(w, 0) + 1
            if len(width_counts) > 1:
                widths_str = ", ".join(
                    f"{w} cols x {c} rows"
                    for w, c in sorted(width_counts.items())
                )
                print(
                    f"[FAIL] CSV has inconsistent row widths: {widths_str}. "
                    f"All data rows must have exactly {n_cols} columns."
                )
                errors += 1
            elif data_rows:
                # Only report if we have data rows
                w = list(width_counts.keys())[0]
                if w != n_cols:
                    print(
                        f"[FAIL] CSV data rows have {w} columns but header has "
                        f"{n_cols}"
                    )
                    errors += 1
                else:
                    print(
                        f"[OK]   CSV data rows all have consistent {n_cols} columns"
                    )

            if len(data_rows) < 10:
                print(
                    f"[FAIL] CSV has {len(data_rows)} data rows (need >= 10)"
                )
                errors += 1
            else:
                print(f"[OK]   CSV has {len(data_rows)} data rows (>= 10)")

            # Check pitch column (index 8 in 0-indexed = "pitch")
            pitch_idx = header.index("pitch") if "pitch" in header else -1
            if pitch_idx < 0:
                print("[FAIL] CSV header missing 'pitch' column")
                errors += 1
            else:
                empty_pitch = sum(
                    1 for r in data_rows
                    if len(r) <= pitch_idx or not r[pitch_idx].strip()
                )
                if empty_pitch > 0:
                    print(
                        f"[FAIL] {empty_pitch} rows have empty pitch column "
                        f"(Canva bulk-create bug)"
                    )
                    errors += 1
                else:
                    print("[OK]   No empty pitch columns")

        # Encoding check
        raw = csv_file.read_bytes()
        if bom_detected:
            print(
                "[INFO] CSV has UTF-8 BOM (auto-stripped, Canva-import-safe)"
            )
        try:
            raw.decode("ascii")
            print(
                "[OK]   CSV is ASCII "
                "(Umlauts correctly replaced ae/oe/ue/ss, Canva-safe)"
            )
        except UnicodeDecodeError:
            # Check for naked umlauts (ä, ö, ü, ß)
            naked_umlauts = re.findall(b"[\\xc3\\xa4\\xc3\\xb6\\xc3\\xbc\\xc3\\x9f]", raw)
            # Bytes pattern for UTF-8 German umlauts (ä,ö,ü,ß) as escape codes
            # to keep source ASCII-clean while matching the actual bytes.
            if naked_umlauts:
                print(
                    f"[WARN] CSV has naked umlauts ({len(naked_umlauts)} found). "
                    f"Replace ae/oe/ue/ss for Canva-Import safety."
                )
                errors += 1  # treat as error since SKILL.md says replace umlauts
            else:
                print(
                    "[INFO] CSV is UTF-8 (no naked umlauts detected)"
                )

    # ---- 5. Anleitung-MD: minimum size + headings ----
    if anleitung.exists():
        size = anleitung.stat().st_size
        content = anleitung.read_text(encoding="utf-8-sig", errors="replace")
        has_heading = bool(re.search(r"^#{1,2}\s+\w", content, re.MULTILINE))
        if size < 500:
            print(
                f"[FAIL] anleitung is too small ({size} bytes, need >= 500)"
            )
            errors += 1
        elif not has_heading:
            print("[FAIL] anleitung has no markdown heading (# or ##)")
            errors += 1
        else:
            print(
                f"[OK]   anleitung has {size} bytes + markdown headings"
            )

    print()
    if errors > 0:
        print(f"=== Result: {errors} error(s) found ===")
        sys.exit(1)

    print(f"=== Result: Design kit for '{nische}' validated successfully ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
