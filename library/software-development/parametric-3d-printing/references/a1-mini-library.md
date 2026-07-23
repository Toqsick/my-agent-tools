# A1 Mini SCAD Library — Parameter Reference

> Basti's Bambu Lab A1 Mini OpenSCAD Library.
> Single source of truth: `a1mini_params.scad`
> Source: `~/Dokumente/3D-CAD/Templates/drucker-a1mini/`

## Printer Specs

| Parameter | Wert |
|---|---|
| Bauraum (SCAD) | 180 × 180 × 180 mm |
| Düsendurchmesser | 0.4 mm |
| Normwand (4 Bahnen) | 1.6 mm |
| Filamentdurchmesser | 1.75 mm |
| Rundungsqualität `$fn` | 96 |
| Präzision Lasercutter-Schnitte | DXF, unter `schnitt_*.dxf` |

## Spool Specs (Bambu-Standard)

| Parameter | Wert |
|---|---|
| Außendurchmesser | 200 mm |
| Breite inkl. Flansche | 66 mm |
| Flanschdicke | 2.4 mm |
| Kernbohrung | 54.5 mm |

## Design Conventions

**Support-Free:**
- Alle Teile sind OHNE Support druckbar
- Überhänge ≤45° gegen die Horizontale (PoopEimer-Kragen, SpulenRoller-Kegel)
- FDM-optimierte Geometrie (keine Bridging-Overhänge, Löcher von oben)

**Druck-Orientierung:**
- SpulenRoller: Hälften stehend auf Flachseite (flat auf der Bauplatte)
- Werkzeug-Caddy: liegend, Lochleiste oben
- Filament-Clip: seitlich, Extrusion in Clip-Längsrichtung
- PoopEimer: stehend, Kragen oben
- Hotend-Box: flach, Fächer nach oben

## Verzeichnis-Baum (Verifiziert 2026-07-16)

```
~/Dokumente/3D-CAD/Templates/
├── bitjoint/
│   ├── bitjoint_params.scad     (126 Zeilen, Shared-Params)
│   ├── bitjoint_gabel1.scad     (74 Zeilen)
│   ├── bitjoint_gabel2.scad     (71 Zeilen)
│   ├── bitjoint_centerpart.scad (32 Zeilen)
│   └── bitjoint_bitstick.scad   (33 Zeilen)
│   STLs: BitJoint1_V2.stl (7.3 MB), BitJoint2_V2.stl (1.4 MB), ... 
│   Templates: BitJoint1_V2_template.stl, ..., Tubenhalter_D28_template.stl
│   Vergleichs-PNGs (vergleich_gabel1.png, etc.)
│
└── drucker-a1mini/
    ├── a1mini_params.scad        (25 Zeilen — SOURCE OF TRUTH)
    ├── spulen_roller.scad        (91 Zeilen — Tischroller ohne Lager)
    ├── werkzeug_caddy.scad       (53 Zeilen — 2 Fächer + Lochleiste + Schlitz)
    ├── poop_eimer.scad           (41 Zeilen — Freistehend mit Kragen)
    ├── hotend_box.scad           (44 Zeilen — 2×2 Fächerraster)
    └── filament_clip.scad        (48 Zeilen — U-Clip mit Snap-Kanal)
    STLs: (fertige STLs unter stl/ und direkt im Ordner)
```

## Perplexity-Verification (2026-07-16 Report)

**Report-Ordner:** `~/Dokumente/Perplexity/`
**Datei:** `I own a Bambu Lab A1 Mini with the standard 0.4mm.md`

**Bewertung der 15 Empfehlungen:**

### 🟢 ROBUST — Already in Print Queue
| # | Print | Creator | Verifiziert |
|---|---|---|---|
| 1 | PTFE Tube Remover V2.2 | R3DPanda | ✅ Handle + Modell-ID existieren |
| 7 | Accessories Toolbox Gridfinity | Nova | ✅ Handle + Modell-ID existieren |
| 11 | AMS Purge Calibration V2 | Ciuf_Ciuf | ✅ Handle + Modell-ID existieren |
| 12 | Benchy Bambu PLA Basic | Bambu Lab | ✅ Offiziell (Bambu's eigener Account) |
| 13 | Adjustable Camera Holder | mlodybuk | ✅ Handle + Modell-ID existieren |
| 15 | Anti-Vibration Feet (TPU) | Sebo Witt | ✅ Handle + Modell-ID existieren |

### 🟡 PLAUSIBEL — Needs creator search
| # | Print | Creator | Anmerkung |
|---|---|---|---|
| 8 | Stackable Storage V3 | Sam67c | Perplexity konnte keine Modell-ID finden |
| 9 | Hex Key Grips | Andi M | Perplexity konnte keine Modell-ID finden |

### 🔴 KRITISCH — Skip
| # | Print | Grund |
|---|---|---|
| G3 | Reduce purge by up to 45% | **OBSOLETE** — per Creator selbst markiert. Feature jetzt nativ in Bambu Studio. |

### Already covered by Basti's SCAD library
| Category | Perplexity recommendation | Warum überspringen |
|---|---|---|
| Cat 2 #4-6 (AMS-Lite) | Spool-Adapter, PTFE-Saver, Labels | Basti braucht diese nur wenn er AMS-Lite hat (oder Multicolor macht) |
| Cat 1 #2 (Lube Nozzle) | fifindr | Nützlich, aber Basti's Werkzeug-Caddy hat das nicht spezifisch drin → kann später dazu |
| Cat 5 #14 (Cable Chain) | Moskk83 | Nützlich für Vibration-Reduktion, kein SCAD-Ersatz → STL-Empfehlung bleibt |
