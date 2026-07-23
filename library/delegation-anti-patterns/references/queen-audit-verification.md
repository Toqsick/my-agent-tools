# Queen-Audit Verification Pattern

> **Live-Manifestation:** 2026-07-16, Daily-Report-Trigger Implementation
> **Mnemosyne-Anker:** `38633f3e32adc109` (importance 0.85, scope global)
> **Self-Improving Cross-Ref:** Pitfalls #38, #39, #40 (self-improving SKILL.md v1.2.0)

## Kernproblem

Subagent-Self-Reports sind **NICHT** Beweis für Korrektheit. Ein Subagent der "N/N Tests grün" meldet, hat möglicherweise nur künstliche Test-Doubles gegen seine eigenen Annahmen getestet — nicht gegen den echten Datenbestand.

## Der Vorfall (2026-07-16)

| Ebene | Tests | Ergebnis | Realität |
|-------|-------|----------|----------|
| Subagent Eigenbau (Welle 1) | 6 künstliche Test-Files, alle mit identischen `## Was lief`-Headern | 6/6 grün | ❌ 5/21 Daily-Files falsch klassifiziert |
| Queen-Audit (Parent) | 21 echte Vault-Files gelesen | 5 Deviations gefunden | ✅ Korrekte Klassifikation |
| Welle 2 (Multi-Marker) | 9 Tests (3 neue) + Real-Vault-Integration | 9/9 grün | ✅ Alle 21 Files korrekt |

**Was der Subagent nicht wusste:** Die 21 Vault-Daily-Notes hatten **11 verschiedene Section-Header-Varianten** von `## Was lief` bis `## Was lief (vermutet aus Mnemosyne-Recall)`. Seine künstlichen Test-Files deckten nur **eine** Variante ab — seine eigene Erwartung.

## Die 3-Ebenen-Test-Architektur

```
Ebene 1: Subagent-Test-Helper  → Testet künstliche Doubles gegen Subagent-Code
                                 Fängt: Syntax-Fehler, Logik-Fehler im engen Modell
                                 Verpasst: Vault-Varianz, Echt-Daten-Deckung

Ebene 2: Queen-Test-Suite      → Testet künstliche Doubles + Regression
                                 Fängt: Methoden-Fehler, Regression durch Multi-Marker
                                 Verpasst: Immer noch künstliche Daten

Ebene 3: Real-Vault-Integration → Testet alle echten Vault-Files
                                  Fängt: Section-Header-Varianz, Encoding-Edge-Cases
                                  NIEMALS durch Ebenen 1-2 abgedeckt
```

**Faustregel:** Jede Ebene fängt eine andere Bug-Klasse. Ebene 3 ersetzt KEINE der anderen.

## Queen-Audit-Checkliste

Nach jedem Subagent-Dispatch der "fertig" meldet:

1. **Output verifizieren** — existiert die Datei mit der behaupteten Größe?
2. **Gegen Real-State testen** — lauf den Code gegen echte Vault-Files, nicht gegen Test-Doubles
3. **Dokumentierte Varianz checken** — hat der Subagent dokumentierte Edge-Cases bedacht? (Section-Header-Varianten, Encoding, Symlinks, etc.)
4. **Seltenen Pfad testen** — Subagent hat vermutlich den Happy-Path getestet. Teste einen Datei-Typ der NICHT seinem Modell entspricht.
5. **Regression prüfen** — was vorher funktioniert hat, muss noch funktionieren (pytest vorher/nachher)

## Wann Queen-Audit zwingend ist

- Subagent hat **selbst Test-Daten generiert** (künstliche Test-Files) → **IMMER Queen-Audit**
- Subagent hat **echte Vault-Files gelesen** → optional (Subagent hatte echte Datenbasis)
- Subagent hat **nur Subagent-Report zurückgegeben** (keine Datei, kein Code, keine Tests) → Queen-Audit unmöglich, Fehler im Dispatch-Design

## Mnemosyne-Record

```yaml
id: 38633f3e32adc109
content: "Queen-Audit-Pflicht nach Subagent-Welle: Subagent-Self-Reports sind NIEMALS
  Beweis für Korrektheit. Welle 1 meldete 6/6 Tests grün, aber der Test-Helper
  deckte nur künstliche Files ab. 5 von 21 echten Dailies falsch klassifiziert.
  Immer Real-State-Verify nach Subagent-Dispatch."
importance: 0.85
scope: global
veracity: stated (live-manifested 2026-07-16)
```

## Verwandte Pitfalls (self-improving SKILL.md)

- **Pitfall #38:** Strikte String-Matches ohne Vault-Reality-Check führen zu False-PARTIALs
- **Pitfall #39:** Subagent-Self-Report + enge Test-Annahmen = False-Green  
- **Pitfall #40:** Daily-Quality-Gate fehlte WikiLink-Count — Section-Detection allein reicht nicht
