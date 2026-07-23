# Vault File Template — A1 Mini STL Research Output

> Angewendet am 2026-07-16 für 3 Use-Cases (Workshop, Gaming, Nerd & Hobby).
> Diente als Format-Vorlage für Phase 5d im SKILL.md.

## Kernschema (12 Felder pro Pick)

1. **Exakter Model-Name** (wie auf Platform gelistet)
2. **Creator @Handle** (live-verifiziert, KEIN Display-Name)
3. **Direkt-URL** (MakerWorld / Printables / Thangs)
4. **Community-Signal** (Downloads, Likes, Reviews, Contest-Awards)
5. **Print-Zeit** auf A1 Mini (in Stunden)
6. **Empfohlenes Material** (PLA / PETG / TPU) + Warum
7. **Schwierigkeit** (beginner / intermediate / advanced)
8. **Print-Orientierung** (flat, on side, multi-part)
9. **Supports nötig** (yes / no / organic-only)
10. **AMS-Lite-Kompatibel** (yes / no / partial)
11. **Why this beats alternatives** (1-3 Sätze)
12. **Bekannte A1 Mini Issues** (Vibration, adhesion, warping, Profile-Fit)

## Vault-File-Kopf

```markdown
# [Use-Case] — A1 Mini STL Picks (Datum)

> [1-Satz-Beschreibung] — Cross-Validation aus [Quellen].
> Tier-1 Picks live via web_extract verifiziert.
> Quellen: [Pfad zu Prompt 1], [Pfad zu Perplexity Output]

---
```

## Vault-File-Abschnitte (in Reihenfolge)

```
## 🏆 Tier-1 Picks (in BOTH [Quelle A] + [Quelle B])
  12-field table per pick

## 🔹 Hidden-Gems — [Quelle A]
  12-field table, Quelle markieren

## 🔹 Hidden-Gems — [Quelle B]
  12-field table, Quelle markieren

## 📋 Honorable Mentions
  Kürzere Einträge, 6 fields, ohne Volltabelle

## 📊 Cross-Validation Matrix
  Tabelle: Modell | Subagent | PerplexityA | PerplexityB | Tier | Rec

## 🎯 Empfohlene Druck-Reihenfolge
  Phase 1 (~10h, diese Woche): Nur Tier-1
  Phase 2 (~12h, nächste Woche): Hidden-Gems
  Phase 3 (nach Bedarf): Honorable Mentions

## ⚠️ A1-Mini-Warnung
  Build-Volume-Check, Nozzle-Warnung, Open-Frame-Constraint

## 🔗 Cross-Refs
  Absolute Pfade zu allen Quellen
```

## Erkenntnisse aus 2026-07-16 Anwendung

**Cross-Validation lieferte konkrete Tier-1-Signale:**
- squinn PCB Holder: in Subagent-Pre-Research (Workshop) UND Perplexity-Output (Nerd) 🏆
- Creat3DWorks Dual PS5 Stand: in Subagent-Pre-Research (Gaming) UND Perplexity-Output (Gaming) 🏆
- addohm Pi 5 Snap Fit: in Subagent-Pre-Research (Nerd) UND Perplexity-Output (Nerd) 🏆
- Tangibility Helping Hands: in Workshop UND Nerd (übergreifender Use-Case) 🏆

**Live-Verifikation deckte Diskrepanzen auf:**
- Perplexity sagte `@SyphenGuitarWorks` → live zeigte `@RobSGW`
- Perplexity sagte `@BambuLab` als Creator → live war `Bambu Lab Official`
- MakerWorld Model URLs sind stabiler als Creator-Seiten

**A1-Mini-Profil-Prüf-Pattern:**
- Auf MakerWorld-Seite: Suchwort "A1 mini" in Print Profile list
- Printables: "A1 mini" als Suchfilter im Model-Tag
- Factory-Profile = ⭐ hohe Vertrauenswürdigkeit
- User-GCode = ⚠️ mittlere Vertrauenswürdigkeit
- Kein A1-mini-Profil = ❌ skalieren/adaptieren nötig
