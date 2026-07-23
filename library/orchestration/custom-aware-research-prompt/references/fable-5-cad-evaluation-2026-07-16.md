# Fable 5 CAD Tool Evaluation — 2026-07-16

## TL;DR

Basti fragte nach KI-CAD-Tool "Fable" für A1-Mini-Vorlagen.
Gesucht: Text-to-STL Tool für einfaches 3D-Print-Design.
**Gefunden: Fable ist KEIN Tool — es ist Claude Fable 5 LLM + CadQuery.**

## Was Fable WIRKLICH ist

| Behauptet (User) | Realität |
|-----------------|----------|
| "Fable" = eigenständiges Text-zu-CAD Tool | Fable = **Anthropic Claude Fable 5** (ein LLM, kein Tool) |
| Direkter STL Output | Output = **CadQuery Python Code** (kein STL) |
| Sofort nutzbar | Braucht **FreeCAD MCP Plugin** oder **SolidWorks + MecAgent** |
| "Fable" = Tool-Name | Fable = Anthropic-Modell-Name (Claude-Version), VibeCAD = browser Demo (nicht öffentlich) |

## Pipeline die wirklich nötig wäre

```
Text-Prompt → Fable 5 LLM → CadQuery Code → FreeCAD MCP Exec → Export STL → A1 Mini drucken
```

**Jeder Pfeil ist ein Break-Point**:
- Fable 5 API: $10/M input, $50/M output Tokens (Claude Pro/Max Abo nötig)
- FreeCAD MCP: muss installiert + konfiguriert sein (~1h Setup)
- CadQuery Pipeline: F5 erzeugt CadQuery-Code, MCP führt ihn in FreeCAD aus → STL Export
- VibeCAD: ist **nur Demo-Showcase**, kein veröffentlichtes Produkt

## Pricing Reality Check

| Quelle | Aussage | Quellenangabe |
|--------|---------|---------------|
| Reddit r/ClaudeCode 2026-06 | "Fable pricing is a joke — 100-300k USD equivalent for 50-day Codex workload" | reddit.com/r/ClaudeCode/comments/1unfp0j/ |
| 3D Printing Journal 2026-06-10 | "The world's most expensive free designer" | 3dprintingjournal.com/p/the-worlds-most-expensive-free-designer |
| Medium (Mike Kuniavsky) 2026-06-15 | "Slopject Fables: AI CAD is kinda here — still early, Vibecad is a demo" | medium.com/@mikekuniavsky/slopject-fables-ai-cad-is-kinda-here |

## Echte Alternativen für STL-Output

| Tool | Output | Setup | Kosten | Bewertung |
|------|--------|-------|--------|-----------|
| **Meshy AI** | STL/OBJ direkt | Browser → Download | Free Tier + Pro | ✅ Einfachster Weg text-to-3D-print |
| **PrintPal.io** | CAD-ready STL | Browser → Download | Freemium | ✅ Für funktionale Teile optimiert |
| **Zoo.dev Zookeeper** | CadQuery → STL | Open Source, lokal | Free | ✅ Parametric, OpenSCAD-ähnlich |
| **MakerWorld MakerLab** | STL Community | Browser | Free | ✅ A1-Mini-Community, kein KI-Output |

## Lesson learned: "Assumed AI Tool" Pitfall

### Symptom
User sagt "ich lass die CAD mit fable kreieren" → nimmt an Fable sei ein CAD-Tool, das STL liefert.

### Reality
Fable ist ein LLM (teuer). Braucht FreeCAD/SolidWorks MCP als Middleware. Liefert Code, nicht STL.

### Pattern Recognition
Folgende Claims sollten immer hinterfragt werden:
- "Ich lass KI XYZ machen" → **Was genau ist der Workflow?**
- "[Tool-Name]" + "generiert STL" → **Welche Pipeline? Direkt oder mit Middleware?**
- "Kostenlos/niedrigpreisig" → **Token-Kosten? API-Pricing? Setup-Kosten?**

### Fix in Custom-Aware-Prompt
Bevor ein Custom-Aware-Prompt um ein KI-Tool gebaut wird:
1. Immer **Live-Recherche** starten (web_search + web_extract)
2. **Pipeline vollständig durchdenken**: Prompt → Modell → Middleware → Export → Druck
3. **Alternativen checken**: Gibt es einfachere Wege zum gleichen Ziel?
4. **Pricing realistisch bewerten**: Token-Kosten + Setup-Zeit + Lizenz-Kosten

## Verwandte Sessions

- A1-Mini-Perplexity-Pass 2026-07-16 (Mnemosyne: be302754122c4e02)
- Subagent-Verification-Gate (Schwester-Skill)
