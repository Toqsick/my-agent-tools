# 🟥🟧🟨🟩 Farb-Legende (Standard für ALLE workflow-template-Outputs)

## Standard-Skala

| Marker | Stufe | Definition | Trigger |
|--------|-------|------------|---------|
| 🟥 | **Kritisch** | Blockiert Nutzung/Lockout-Risiko/Datenverlust/Sicherheitslücke | Sofort, vor allem anderen |
| 🟧 | **Hoch** | Spürbarer Mehrwert kurzfristig / wichtiges Risiko / wichtige Effizienz | Nach 🟥-Block abgeschlossen |
| 🟨 | **Mittel** | Alltag/Polish/Komfort | Wenn 🟥🟧 durch sind |
| 🟩 | **Optional** | Nice-to-have / kosmetisch | Wenn überhaupt Zeit übrig |

## Verwendung

**Innerhalb eines Templates**: Markiert die Phase, in die der Schritt gehört.
**Im finalen Plan/Report**: Klassifiziert den Schweregrad eines Findings/Befunds.
**In Mnemosyne-Calls**: Informiert das `importance`-Level (🟥 = 0.8-0.95, 🟧 = 0.6-0.7, 🟨 = 0.4-0.5, 🟩 = 0.2-0.3).

## Pitfalls

- ⚠️ 🟥 als 🟨 darstellen → kritische Risiken verschwinden im Output. Risiko-Skala ist **kein** Vorschlag, sondern Standard.
- ⚠️ Skala auf Findings anwenden ohne Implikation: "🟥" ohne Begründung "warum kritisch?" wertlos.
- ⚠️ Misch-Masch mit anderen Skalen (z.B. CVSS 1-10) im selben Plan → Verwirrung. Pro Plan **eine** Skala.

## Kombinations-Hinweis

Falls Domain-eigene Skala existiert (CVSS, Severity-CVSS-v3, etc.), beide parallel nutzen mit klarer Marker-Differenzierung:

- 🟥 = "in dieser Session sofort"  
- CVSS = "industriestandard für Vulnerability-Wert"

Beispiel:
```markdown
- 🟥 Sofort patchen (Lockout-Risiko)
- CVSS: 7.5 ⚠️ estimated (Begründung: vector unvollständig)
```
