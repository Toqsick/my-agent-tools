# Three-Phase Build Protocol (2026-07-08)

Established in MaxHermes Cloud Config session (Alibaba ECI Pod, Branch `MaxHermes` on `Toqsick/hermes-v7`).

## Trigger

Basti said: "mach erstmal eine architektur review und wo du was rein tuen würdest dann evaluiere alles und setze es 'neu' auf"

## The Three Phases

### PHASE 1 — Architecture Review (Ist-Zustand erfassen)
- Live-Umgebung checken (nicht nur Doku lesen)
- Hardware/Software/Netzwerk-Status feststellen
- Vorhandene Ressourcen und Konflikte identifizieren
- SSH-Erreichbarkeit, Ports, Services, Abhängigkeiten prüfen
- Alles dokumentieren bevor Optionen kommen

### PHASE 2 — Evaluation (Optionen + Scorecard)
- 2-4 Optionen mit klaren Trade-offs
- Jede Option: Aufwand/Nutzen/Risiko/Security-Bewertung
- Scorecard mit ⭐⭐⭐⭐⭐ Systematik
- Klare Empfehlung + Begründung warum andere rausfallen

### PHASE 3 — Clean Build (sauber neu aufsetzen)
- Nicht patchen/reparieren — neu bauen
- Git-Branch statt Live-Änderungen (Default)
- Reviews und Doku vorher im Branch committen
- Verifikation nach jedem Schritt
- Erklärung warum die Architektur so gewählt wurde

## Anti-Patterns
- Phase 2 überspringen und direkt bauen, weil "die Architektur ist klar"
- Phase 1 überspringen und auf veraltete Doku vertrauen
- Phasen sind strikt sequentiell — Phase 2 darf erst beginnen wenn Basti Phase 1 abgesegnet hat

## When NOT to apply
Quick-Fixes, One-Off-Debugging, Copy-Paste-Tasks, triviale Config-Änderungen (< 5 Zeilen).
Protocol ist für neue Einrichtungen und Refactoring, nicht für tägliche Wartung.
