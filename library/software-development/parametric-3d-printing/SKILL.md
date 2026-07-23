---

name: parametric-3d-printing
description: |
  Use when you design parametric OpenSCAD models for 3D printing — support-free shapes, reusable SCAD libraries, variable-driven dimensions that users can tweak — and want a tested parametric-design workflow.
  NOT for organic or mesh-based modeling (use Blender), slicing/g-code generation (use PrusaSlicer/OrcaSlicer), or non-parametric static STLs.
  Parametric OpenSCAD design workflow for 3D printing: support-free primitives, tunable parameters, reusable library conventions, print-ready export.
version: 1.0.0
author: Basti + Yuno (2026-07-16)
license: MIT
agent: Yuno
lane: koenigin
trigger_keywords:
- 3d druck
- 3d print
- 3d-printer
- a1 mini
- bambu lab
- openscad
- scad
- parametric
- stl
- makerworld
- printables
- thangs
- filament
- drucker
- support-free
- parametrisch
- düse
- düsengröße
- layer height
- schichthöhe
- bitjoint
- bit holder
- tool holder
- caddy
- spool holder
- filament clip
- purge bucket
- poop eimer
- hotend box
- werkzeug caddy
related_skills:
- perplexity-followup-plan
last_curated: 2026-07-16
curated_by: "Yuno (v1.0.0 — first cut from 2026-07-16 session: A1 Mini SCAD library discovered + Perplexity verification pipeline)"
routing_hint: >
  Trigger when Basti mentions 3D printing, SCAD files, STL downloads, or
  any of his custom prints (HotendBox, PoopEimer, SpulenRoller,
  WerkzeugCaddy, FilamentClip, BitJoint). Load this skill first, then
  `skill_view('parametric-3d-printing', 'references/a1-mini-library.md')`
  for his exact SCAD parameters. Pair with `perplexity-followup-plan` when
  evaluating STL recommendations from a Deep Research run.
keywords: ['parametric', 'design', 'openscad', 'printing', 'support']
---

# Parametric 3D Printing — OpenSCAD Library Design Workflow

> Strukturierter Ansatz für parametrisches OpenSCAD-Design: zentrale Printer-Parameter
> in einer `params.scad`, pro-Teil-Overrides, stützfreie Orientierung,
> Material-spezifische Wandstrategien.

## Wann diesen Skill laden

Trigger bei:
- „Hilf mir einen [Drucker-Teil] zu designen" — egal welcher Drucker
- „Ich brauche ein neues OpenSCAD-Teil für den [Printer]"
- „Welche STLs soll ich runterladen?"
- „Kannst du meine SCAD-Lib verbessern?"
- „Perplexity-Report zu Drucker-Tools ist da" (dann Pair mit `perplexity-followup-plan`)

Nicht laden bei: reiner Filament-Kaufberatung, Drucker-Kauf-Beratung,
Slicer-Tuning ohne SCAD-Bezug.

---

## Prinzipien

### 1. Single-Source-of-Truth Param-File

Jede parametrische SCAD-Library braucht EXAKT EINE Datei mit allen
druckerspezifischen Konstanten. Beispiel aus Basti's A1-Mini-Lib:

```openscad
// a1mini_params.scad — zentrale Drucker-Maße
bett_x = 180;      // Bauraum (mm)
bett_y = 180;
bett_z = 180;
duese  = 0.4;      // Düsendurchmesser (mm)
wand_norm = 1.6;   // Normwand = 4 Bahnen à 0.4 mm
filament_d = 1.75; // Filamentdurchmesser (mm)
$fn = 96;          // Rundungsqualität
```

- Jedes Teil includiert diese Datei (`include <params.scad>`)
- Bei Druckerwechsel oder Düsen-Upgrade GENAU EINE Datei editieren
- Schützt vor Inkonsistenzen zwischen Teilen

### 2. Support-Free Design Pattern

Alle Teile müssen STÜTZFREI druckbar sein (kein Support, keine organischen
Stützen). Das erreicht man durch:

| Technik | Beispiel (Basti's Lib) |
|---|---|
| **45°-Regel** — alle Überhänge ≤45° gegen Horizontale | PoopEimer-Kragen: `kragen_h` so gewählt dass Flare ≤45° |
| **Druckorientierung** — Teil so ausrichten dass Überhänge entfallen | SpulenRoller-Hälften: stehend auf der Flachseite |
| **Integrierte Stützen vermeiden** — lieber ein zusätzliches Kleinteil | BitJoint-System: CenterPart + Gabel + Stick als separate STLs |
| **Offene Nuten statt Löcher** — Bohrungen von oben statt unten | Werkzeug-Caddy: Lochleiste von oben, keine Support-Brücken |
| **Filigrane Elemente nach außen** — dünne Stege/Wangen die frei enden | Hotend-Box: Fächerraster kein Überhang weil Kastenform |

### 3. Material-bewusste Wandstrategie

| Düse | Normwand (4 Bahnen) | 2 Bahnen | 3 Bahnen |
|---|---|---|---|
| 0.4 mm | 1.6 mm | 0.8 mm | 1.2 mm |
| 0.6 mm | 2.4 mm | 1.2 mm | 1.8 mm |

- **Normwand = Düse × 4** — strukturelle Festigkeit
- **Dünnwand = Düse × 2** — für Clips, Federelemente, Snap-Fits
- **Boden = Düse × 6** — ≥2.4 mm für Stabilität bei funktionalen Teilen

### 4. Filament-Philosophie

- **PETG** — functional parts, Werkzeug, Teile mit Spannung
- **PLA** — Prototypen, Deko, low-stress, schnell
- **TPU** — Vibration damping, Grips, flexible Clips
- **Kein matte/silk PLA** für Teile unter Last — Layer-Adhesion zu schwach
- **AMS-kompatibel** wo sinnvoll → accent-colour Links, Labels, Numbering

---

## 3D Printing Perplexity-Evaluation (Pair mit `perplexity-followup-plan`)

Wenn ein Perplexity-Deep-Research-Report zu STL-Empfehlungen reinkommt,
füge diese 3D-Druck-spezifischen Checks zur Standard-3-Stufen-Evaluierung
hinzu:

### Zusätzliche Quellen-Checks

| Check | Warum | Fehler-Beispiel (2026-07-16) |
|---|---|---|
| **Creator-Handle auf MakerWorld suchen** | Perplexity halluziniert Handles | — (alle 10 verifiziert ✅) |
| **Model-Seite auf Obsolete-Flag prüfen** | Perplexity übersieht Creator-Markierungen | "Reduce purge by up to 45%" → **(Obsolete)** im Titel |
| **Download:Likes-Ratio checken** | Downloads sind aufgebläht (Bambu Studio zählt Prepare-for-Print-Taps) | 28k downloads : 5k likes → gesund. 50k:200 = tot. |
| **Print-Profile auf A1 Mini existieren** | Nur weil's A1 Mini im Tag hat, muss kein gutes Profil mitgeliefert sein | Moskk83 Cable Chain → A1 Mini-Profile in der Liste ✅ |
| **Letztes Update-Datum** | Alte Modelle oft nicht mehr maintained | Fisher-Skipper purge: 2023, nicht geupdated |

### Evaluations-Schema (erweitert um Druck-Context)

```markdown
### 🟢 ROBUST — Sofort in Print-Queue
• [Print] — verifizierter Create, aktuell ≥2025, gesundes Download:Likes
  → Nächster Druck

### 🟡 PLAUSIBEL — Erst prüfen
• [Print] — Handle existiert, Modell-ID nicht verifiziert (nur in Collection)
  → Erst auf MakerWorld suchen, dann in Queue

### 🔴 KRITISCH — Überspringen
• [Print] — Obsolete / Creator inaktiv / Braucht 0.2mm Düse
  → Grund nennen
```

### Warum das wichtig ist (Lessons from 2026-07-16)

1. **MakerWorld Download-Counts sind keine echten Drucke.** Bambu Studio zählt
   jeden Klick auf "Prepare for Print" als Download — auch wenn nie gedruckt.
   Ein Modell kann 28k Downloads aber nur 2k Likes haben. Die Likes sind der
   echte Community-Vote.
2. **Perplexity gibt keine Obsolete-Warnung.** Der Title "(Obsolete)" auf der
   MakerWorld-Seite taucht im Perplexity-Output nicht prominent auf.
   Immer die LIVE-Seite laden, nicht Perplexitys Zusammenfassung vertrauen.
3. **Print-Profile sind keine Garantie.** Ein Modell kann für A1 Mini getaggt
   sein, aber das mitgelieferte Profil kann für den Sidewinder X2 optimiert
   sein. Immer die Print-Profile-Liste checken.
4. **Alte Modelle (2023-2024) sind nicht tot** — aber Creator für Bug-Fixes
   und Updates zu erreichen ist schwer. Bevorzuge aktiv maintained oder
   OpenSCAD-generierte Modelle (wie Basti's eigene Lib).

---

## Basti's Workflow (aus der Session 2026-07-16)

1. **Problem identifizieren** — "Ich brauche [Teil] für den A1 Mini"
2. **SCAD-Lib-Check** — `ls ~/Dokumente/3D-CAD/Templates/drucker-a1mini/`
   — Teil schon da? → ggf. anpassen statt neu designen
3. **Perplexity Deep Research** — wenn noch nicht selbst designed, per prompt
   STL-Empfehlungen holen (Pair mit `perplexity-followup-plan`)
4. **3-Stufen-Evaluierung** — Quellen-Triage mit obigen 3D-Druck-Checks
5. **Print-Queue priorisieren** — Bench → Maintenance → Mods → Nice-to-Have
6. **Gedruckte STLs ablegen** — `~/Dokumente/3D-CAD/` als Struktur behalten
7. **Perplexity-Report dokumentieren** — in `~/Dokumente/Perplexity/`
   (Dateiname: `Bambu Lab A1 Mini ... .md`)

### Verzeichnis-Struktur

```
~/Dokumente/3D-CAD/
├── Templates/
│   ├── bitjoint/          # BitJoint-System
│   │   ├── bitjoint_params.scad
│   │   ├── bitjoint_gabel1.scad
│   │   ├── bitjoint_gabel2.scad
│   │   ├── bitjoint_centerpart.scad
│   │   └── bitjoint_bitstick.scad
│   └── drucker-a1mini/     # A1 Mini Zubehör
│       ├── a1mini_params.scad  # SINGLE SOURCE OF TRUTH
│       ├── spulen_roller.scad
│       ├── werkzeug_caddy.scad
│       ├── poop_eimer.scad
│       ├── hotend_box.scad
│       └── filament_clip.scad
├── README.md              # Projekt-Beschreibung (noch leer)
└── Perplexity/            # Research-Reports
    └── Bambu Lab A1 Mini ... .md
```

---

## Cross-Links

- **Skill:** `perplexity-followup-plan` (Pair für STL-Research-Evaluierung)
- **Vault:** (noch kein Eintrag — anlegen bei nächster SCAD-Iteration)
- **Repo:** `~/Dokumente/3D-CAD/`
- **Perplexity Reports:** `~/Dokumente/Perplexity/`
