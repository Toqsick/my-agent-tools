# Audit-Report Drift Fix — Vault-Dokumentations-Patching mit Multi-Agent Cross-Verification

**Referenz für Pattern 11b (numerischen/zahlen-basierten Dokumentations-Drift)**

## Overview

Dieser Workflow patcht **stale numerische Werte** in Vault-Dokumentationen (Counts,
Timestamps, Splits), die durch einen **Audit-Report** als veraltet identifiziert wurden.
Kern-Innovation: Sub-Biene als unabhängiger Cross-Check einer Schwester-Datei parallel
zum QueenBee-Patch-Durchlauf.

**Abgrenzung zu Pattern 11 (Plugin-State-Drift):**
- Plugin-Drift = Doku sagt "Plugin X enabled" ↔ Live-Config sagt "disabled"
- Audit-Drift = Doku sagt "Files=247" ↔ Audit-Report sagt "Live=256"
- Beide sind Doku-vs-Realität, aber unterschiedliche Datenquellen

## Trigger Conditions

Use this workflow when:
- Ein Audit-Report (wie `GreyHack-Audit-YYYY-MM-DD.md`) eine Drift-Matrix enthält
- Du `old_value → new_value` Paare aus dem Report in Vault-Dokumentationen patchen musst
- Die Werte in mehreren Sektionen/Zeilen einer Datei vorkommen
- Eine Schwester-Datei (intel/systems/config) separat verifiziert werden muss

## 5-Phasen-Workflow

### Phase 0 — Inventur (READ-ONLY, Königin)

Lese **beide** Dateien parallel:
1. Das Target-Dokument
2. Den Audit-Report

Extrahiere die **Drift-Matrix** (Wert, Doku-stale, Live-korrekt).

### Phase 1 — Alle Vorkommen finden

Das häufigste Anti-Pattern: nur das erste Vorkommen eines Werts patchen.
`267` taucht typisch **4–6×** in derselben Datei auf (Tabelle, Header, Summary, Raw-Stats).

**Suchstrategie:** search_files mit regex-Oder pro Wert. False-Positives
(Transaktionszahlen `-247 withdraw`, Versionsnummern `1.2.47`, Ports)
separat filtern und dokumentieren.

### Phase 2 — Batch-Patching (Königin, sequentiell)

Patche ALLE Vorkommen. Jedes braucht eigenen `patch`-Aufruf mit Unique-Kontext
(genug Zeilen drumherum). `replace_all=true` ist zu breit.

**Sequentiell pro Datei** — nicht parallel zur Sub-Biene (Patch-Conflicts!).

Verifikation nach jedem Batch: `search_files` auf stale-Werte → 0 Treffer erwartet.

### Phase 3 — Sub-Biene Cross-Check (parallel dispatch)

Dispatch eine **Sub-Biene** (role='leaf') um die Schwester-Datei zu prüfen.
Briefing MUSS sagen: "Du bist eine Lese-Biene — NICHTS patchen, NUR reporten."

Self-Report: total_drift_values_found, file_created_mit_Pfad, confirm_via ls + wc.

Verifikation nach Rückkehr: `ls -la && wc -l` auf Output-File.

### Phase 4 — Diff-Log schreiben (Königin)

Strukturierter Log mit:
- Zusammenfassung (Tabelle: Drift-Wert + Status)
- Patch-Detail pro Wert (Datei, old_string, new_string, Bemerkung)
- Sub-Biene-Ergebnis (sub_call_count, File-Existenz, Befund)
- Self-Report (Anzahl gepatchter, Issues, False-Positives)

### Phase 5 — Finale Verifikation (Königin)

```bash
# Stale-Werte: 0 Treffer erwartet
search_files(pattern="247|267(?! refCount)|21 Einträge|13:58|14:54",
             target="content", path="<target.md>", output_mode="count")
# Neue Werte: ≥1 Treffer pro Wert erwartet
search_files(pattern="256|282|22 Einträge|2000-01-07",
             target="content", path="<target.md>", output_mode="content")
```

## Pitfalls

| # | Pitfall | Mitigation |
|---|---------|------------|
| 1 | Singular-Patch (nur erstes Vorkommen) | Phase 1: search_files mit ALLEN Kombinationen |
| 2 | False-Positive-Count | Jeden Match auf legitimen Kontext prüfen |
| 3 | Sub-Biene patcht statt zu lesen | Briefing: "NUR reporten, NICHTS editieren" |
| 4 | TokenTrace-Split kein Literal | Prüfe ob der Split als abgeleitete Größe in der Datei existiert |
| 5 | Kein Diff-Log → Königin kann nicht rekonstruieren | Phase 4 ist PFLICHT |
| 6 | Sub-Biene dispatcht obwohl Phase 2 läuft | Parallel erlaubt! Aber Phase 4 wartet auf beide |
| 7 | `patch`-Tool _warning ignoriert | Immer search_files zur Verifikation, nicht dem success-Flag vertrauen |

## Proven Example (2026-07-14)

| Metrik | Wert |
|--------|------|
| Target | `greyhack-deep-systems-2026-07-04.md` (694 Zeilen) |
| Audit | `GreyHack-Audit-2026-07-14.md` |
| Gepatcht | **6/6** (Files, Passwords×4, Logs×2, Clock, LastConnection, TokenTrace) |
| Sub-Cross-Check | Intel-Schwester → **10 harte Drift-Vorkommen** |
| Sub-Report | `/tmp/vault-patch-beta/<ts>-sub.md` (10 KB, 198 Zeilen) |
| Diff-Log | `/tmp/vault-patch-beta/<ts>.md` (7 KB, 112 Zeilen) |
| Verifikation | 0 stale-Treffer im Target |

## Related Skills

- `orchestration/multi-agent-cluster-patterns` — Dispatch-Mode für Stale-Fix-Workflow
- `orchestration/sub-sub-workflow` — wenn Sub-Biene nested delegation braucht