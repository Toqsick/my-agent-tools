# Pattern 2: Additive Patches als Cluster-Disziplin

Wenn **mehrere Subagents parallel dieselbe Datei** patchen (typisch `MOC - Home.md`, Themen-MOCs):

| Regel | Warum |
|---|---|
| Jeder Subagent patcht eine **andere Sektion** | Vermeidet Race-Conditions auf String-Ebene |
| Reihenfolge egal | Patches sind kontextuell unabhängig wenn Sektionen disjunkt |
| Dokumentation | Welcher Subagent hat welche Sektion gepatcht? |

## Anti-Pattern
Alle Subagents patchen die "Quick-Links"-Sektion gleichzeitig → Race Condition, "letzter gewinnt" → Quick-Links verschwinden.

## Best Practice
Pro Cluster-Subagent **eigener Sektionen-Bereich** vorab definieren (siehe Template unten).