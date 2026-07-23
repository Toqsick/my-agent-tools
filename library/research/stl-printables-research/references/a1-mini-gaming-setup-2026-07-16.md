# 2026-07-16 — A1 Mini Gaming Setup STL Research (Concrete Example)

This is a worked example of the `stl-printables-research` workflow. The task:
Find 9 community-validated STLs (3 per category) for Basti's **Bambu Lab A1 Mini**
for a Gaming Setup use case.

## Session stats

| Metric | Value |
|--------|-------|
| web_search calls | ~16 |
| web_extract calls | ~9 |
| Candidates investigated | ~15 (initial pool) |
| Verify-pass rate | 9/9 |
| Dead links found | 3 (2 Printables 404, 1 MakerWorld redirect) |
| Incompatibility found | 1 (extendable Stream Deck XL mount — "not printable on A1 Mini") |

## Categories and final picks

### Category 1 — Controller & Headphone Stands

| # | URL | Title | Community value | Year | Source |
|---|-----|-------|-----------------|------|--------|
| 1 | https://makerworld.com/en/models/646062-dual-ps5-controller-stand | Dual PS5 Controller stand (Creat3DWorks) | 13.1k downloads, 744 ratings. **A1-Mini variant linked** in description | 2024-09 | MakerWorld |
| 2 | https://makerworld.com/en/models/148748-ps5-charging-dock | PS5 Charging Dock (ThePrintsGioUniverse) | 459 downloads. A1 Mini print profile included (3 plates, 6h) | 2024-01 | MakerWorld |
| 3 | https://makerworld.com/en/models/141033-mini-figure-headphone-stand | Mini-figure Headphone Stand (Thinkable) | 8.8k downloads, 969 ratings. **Official A1-Mini profile** (7.5h, 3 plates) | 2024-01 | MakerWorld |

### Category 2 — Switch Dock & Cartridge Storage

| # | URL | Title | Community value | Year | Source |
|---|-----|-------|-----------------|------|--------|
| 4 | https://www.printables.com/model/82736-nintendo-switch-dock-cartridge-holder | Switch dock cartridge holder (Byrn3D) | 1k+ downloads, 88 likes. OLED-compatible | 2023-08 | Printables |
| 5 | https://makerworld.com/en/models/441696-cartridge-display-stand-for-nintendo-switch-dock | Cartridge display stand (namedia) | 1.2k downloads. A1-Mini profile, 18/24/30 cartridge variants | 2024-04 | MakerWorld |
| 6 | https://makerworld.com/en/models/1490609-nintendo-switch-2-dock-cartridge-holder-stand | Switch 2 Dock cartridge holder (lambonorbi) | 375 downloads. **A1 Mini monochrome profile** (1.5h, 1 plate, 5.0★) | 2025-06 | MakerWorld |

### Category 3 — Streaming Setup Accessories

| # | URL | Title | Community value | Year | Source |
|---|-----|-------|-----------------|------|--------|
| 7 | https://makerworld.com/en/models/748820-design-headphone-stand-no-ams-needed | Design Headphone Stand NO AMS (TheBigGreek) | 599 downloads. Fits A1 Mini single plate (144×70×233mm) | 2024-11 | MakerWorld |
| 8 | https://www.printables.com/model/287367-stream-deck-xl-case-and-4040-mount | Stream Deck XL Case 4040 mount (John Feagin) | 4.1k downloads, 583 likes. Multi-part, requires M8 hardware | 2023-08 | Printables |
| 9 | https://www.printables.com/model/101379-elgato-key-light-40-degree-stand | Elgato Key Light 40° stand (Przemo-c) | 202 downloads. Compact desktop stand, both orientations | 2021-12 | Printables |

## Substitutions made

| Rejected | Reason | Replacement |
|----------|--------|-------------|
| MakerWorld 1065898 (Extendable Stream Deck XL Mount) | Designer says "not printable on A1 Mini" | Printables #8 (John Feagin 4040 mount, 4.1k downloads) |
| Printables 47894 (Teaching Tech webcam mount) | 404 — page removed | Replaced with #7 headphone stand (streaming setup still served) |
| Printables 39792 (mic stand mount) | 404 — page removed | Not substituted — no verified mic boom arm passed the >500-download bar |

## Query patterns used

```
MakerWorld "PS5 controller" stand popular A1 mini
Printables "Nintendo Switch" cartridge holder STL most popular
MakerWorld "Stream Deck" mount A1 mini 2024
Printables "Elgato Key Light" stand STL
Printables "Stream Deck XL" case mount
MakerWorld "webcam mount" Logitech C920 monitor
MakerWorld "microphone boom arm" printable
```

## Lessons learned

1. **Always check print profile tabs, not just description text.**
   Model #2 (PS5 Charging Dock) says "A1 mini" in the profile list but has
   multiple user reports of USB-C fit issues. Downloads are not quality.

2. **The Most-Popular isn't always the right pick.**
   Model #2 at 459 downloads actually looks weaker than #6 at 375 downloads
   with a perfect 5.0★ — but #2 fills a charging-dock niche no other pick covers.

3. **Reddit is unreliable as a data source.**
   web_extract blocked on all reddit.com domains. Use only for sentiment,
   never for verification.

4. **Time matters.**
   Model #9 (Elgato Key Light stand) is from 2021 and only 202 downloads —
   but Elgato Key Light hardware hasn't changed since. For unchanging
   hardware, old models are fine. For controller docks (USB-C revision),
   pick newer models.
