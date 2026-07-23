# Deep-Mining Methodology — Vault-Analytics über mehrere Layer

> **Anlass:** 2026-07-16, 19-Tage-Daily-Notes-Audit
> **User-Preference:** Basti sagt "tiefer" → meint iterative Layer (nicht eine tiefe), also Schicht für Schicht bis zur Sättigung
> **Prinzip:** Gehe so tief, bis keine neue Erkenntnis-Klasse mehr auftaucht. Stopp-Kriterium: die letzte Schicht fand keine neue Muster-Kategorie.

## Die 3+1 Standard-Layer (bewährt ab 2026-07-16)

### Layer 1 — Oberflächen-Inventur (5 Min)
- Datei-Anzahl, Größen, Tage abgedeckt, System-Coverage
- "Was haben wir?" — Bestandsaufnahme, kein Muster

### Layer 2 — Temporal-Drift & Cluster (10 Min)
- Wiki-Link-Heatmap über Kalenderwochen
- Cluster-Dominanz (welches Thema pro Phase)
- Korrelations-Analyse (z.B. Wortzahl vs. Subagent-Dispatches)
- "Wann war was dominant?" — Muster-Erkennung

### Layer 3 — Evolutions-Analyse (15 Min + Subagent)
- Working-Agreement-Evolution (welche Klausel wann sichtbar)
- Discipline-Timeline (Lessons chronologisch)
- Pioneer-Patterns (erste Male = Pfadöffner)
- "Warum hat sich was wie entwickelt?" — Kausal-Muster

### Layer 4 — Synthese & Meta-Insight (5 Min)
- Phasen-Identifikation (Setup → Build → Deep-Work → Meta)
- Predictive: nächste Phase extrapolieren
- "Was bedeutet das für Morgen?" — Handlungs-Konsequenz

## Stopp-Kriterien pro Layer

| Layer | Stopp wenn... |
|-------|--------------|
| 1 | Alle Dateien gezählt + Systeme gecheckt |
| 2 | Keine neue Cluster-Verschiebung in den Daten |
| 3 | Keine neue Lesson/Pioneer-Klasse mehr auffindbar |
| 4 | Keine neue Meta-Erkenntnis (letzter Layer ist Meta, nicht weiter) |

## User-Preference Encoding

Wenn Basti sagt:
- **"tiefer"** → Layer 1 ist fertig, geh zu Layer 2 mit Subagent
- **"noch tiefer"** → Layer 2 ist fertig, Layer 3 braucht echte Daten-Mining-Code
- **"weite noch etwas aus"** → Layer 3 fertig, Layer 4 (Synthese + Predictive + Meta-Insight) + Visualisierung
- **"reicht"** → STOP. Layer 4 ist definitiv der letzte.

**Faustregel:** NIEMALS alle 4 Layer in einem monolithischen execute_code machen — Layer 3 braucht einen Subagent (Working-Agreement lesen, Mnemosyne-IDs validieren). Layer 4 ist reine Reflexion.

## Beleg-Vorfall

2026-07-16: Basti sagte "ja tiefer" → Layer 1→2. "ja noch tiefer" → Layer 3 mit Subagent. "ja weite noch etwas aus" → Fall-Study-Subagent + Cluster-Heatmap-Visualisierung (Layer 4). Drei Iterationen, jede brachte neue Erkenntnis-Klasse.
