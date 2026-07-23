# Staggered Vault Deployment — Worked Example (Phase 6, 2026-07-05)

## Ausgangslage

Basti wollte Obsidian-Vault "riesig ausbauen" — 5 Cluster geplant:
1. Zero/Thin-Notes-Fix (3 Zero + 8 Thin)
2. Project-README-Expansion (5 thin → 180z+)
3. 3 neue Themen-MOCs + 15 Satelliten
4. Glossar 80+ Akronyme + Wiki-Link-Spread
5. 3 CSS-Snippets + Plugin-Setup-Notes

## Entscheidungsbaum

```
Hat der User explizit "staffeln" gesagt?
  → JA → gestaffelt (diese Session)
Hat der User "mach schnell" gesagt?
  → NEIN → gestaffelt (Vorsicht gewinnt)
Sind es ≥4 Cluster?
  → JA → gestaffelt
Sind Cluster-Typen gemischt (zero + expansion + polish)?
  → JA → gestaffelt
```

## Staffel-Plan

```
Welle 1: Cluster 1 (Zero/Thin-Fix)
  → Subagent A, sequenziell
  → Kritischste Basisarbeit zuerst
  → Wenn das schiefgeht, sind die anderen Cluster sinnlos (Fundament fehlt)

Welle 2: Cluster 2-5 (parallel)
  → Subagenten B, C, D, E
  → Alle disjunkt (kein File wird von 2 Agents gleichzeitig angetastet)
  → Königin vertraut auf File-Scope-Conflict-Table

Welle 3: Cluster 6 (inline durch Königin)
  → Aktualisierungs-Strategie-Doc
  → Final-Verifikation (Wiki-Link-Density, Broken-Links)
  → Mnemosyne-Hook
  → Report an User

Optional: Hotfix-Welle nach Verifikation
  → Falls Broken-Links oder Isolation gefunden
  → Kleiner Subagent oder Königin inline
```

## Warum gestaffelt besser war

| Aspekt | Parallel (gedacht) | Gestaffelt (gemacht) |
|--------|-------------------|---------------------|
| Queue-Übersicht | 5 unbekannte Rückmeldezeiten | Welle 1 → prüfen → Welle 2 |
| Eingriffsmöglichkeit | Keine, bis alle fertig | Nach jeder Welle stoppen/ändern |
| Rollback-Komplexität | 5 Cluster rückgängig machen | Nur letzte Welle falls nötig |
| User-Feedback | "Wann ist es fertig?" | Klar "Welle 1 läuft, dann Welle 2" |

## Empfohlenes Vorgehen ab 4+ Clustern

1. **Cluster sortieren** (critical first: Zero/Thin-Fix → expansion → polish)
2. **Welle 1 feuern** = critical cluster(s), sequenziell
3. **Auf Rückmeldung warten** (kommt automatisch via Background-Message)
4. **Welle 1 verifizieren** (Quick-Check: existieren die Files? richtige Größe?)
5. **Welle 2 feuern** = restliche Cluster parallel
6. **Welle 3 inline** = Königin macht Strategie/Summary/Verifikation
7. **Final-Report** an User mit Vorher-Nachher-Metriken

## User-Sprache erkennen

| User sagt | Bedeutung |
|-----------|-----------|
| "staffeln" | Welle 1 → Welle 2, nicht alle auf einmal |
| "mach schnell" | Parallel, Risiko in Kauf nehmen |
| "sei genau, prüf nach" | Gestaffelt, mehr Vorsicht |
| "hive mind, Queen" | Volle Kontrolle bei der Königin, Workers folgen |
