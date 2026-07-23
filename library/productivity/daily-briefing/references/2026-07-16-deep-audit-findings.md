# Deep Audit Findings — Baseline 2026-07-16

> Erstellt: 16.07.2026 · Audit-Reichweite: 2026-06-28 → 2026-07-16 (19 Tage)
> Quelle: `daily-briefing` Skill §3 — Tägliches Vollständigkeits-Mining

## Vault Daily-Notes

| Metrik | Wert |
|---|---|
| Dateien | 21 (19 Haupt-Dailies + 2 Multi-File-Suffixe) |
| Lückenlose Coverage | ✅ 100% seit 2026-06-28 |
| Durchschnittsgröße | 7.268 B |
| Minimum | 3.113 B (2026-07-04) |
| Maximum | 17.715 B (2026-07-07) |
| Bimodale Verteilung | Setup-Phase (28.06–05.07): 3-5 KB · Arbeits-Phase (06.07–14.07): 8-17 KB |

### Größen-Drift (chronologisch)
```
2026-06-28   4,148 B  ████████
2026-06-29   5,651 B  ███████████
2026-06-30   5,298 B  ██████████
2026-07-01   4,143 B  ████████
2026-07-02   5,167 B  ██████████
2026-07-03   4,946 B  █████████
2026-07-04   3,113 B  ██████
2026-07-05   4,459 B  ████████
2026-07-06   8,597 B  █████████████████
2026-07-07  17,715 B  ███████████████████████████████████  ← PEAK
2026-07-08  10,406 B  ████████████████████
2026-07-09   5,874 B  ███████████
2026-07-10   7,227 B  ██████████████
2026-07-11   5,406 B  ██████████
2026-07-12   3,678 B  ███████
2026-07-13  16,918 B  █████████████████████████████████  ← PEAK
2026-07-14  17,679 B  ███████████████████████████████████  ← PEAK
2026-07-15   7,365 B  ██████████████
2026-07-16   8,317 B  ████████████████
```

## Wiki-Link-Vernetzung

| Metrik | Wert |
|---|---|
| Total Wiki-Links | 245 |
| Unique Targets | 92 |
| Avg Links/Daily | 12.8 |
| Discipline-Threshold (≥3) | ✅ Vielfach übertroffen |

### Top-10 verlinkte Notes

| Count | Target | Rolle |
|---|---|---|
| 16× | [[Working Agreement - Yuno Basti]] | Session-Hub |
| 16× | [[MOC - Home]] | Vault-Home |
| 12× | [[MOC - Daily Notes]] | Daily-Hub |
| 11× | [[MOC - KI-Architektur]] | Architektur |
| 8× | [[Subagent-Patterns - Delegation & Routing]] | Pattern-Resource |
| 8× | [[Mnemosyne Cleanup Report - 2026-07-05]] | Memory-Cleanup |
| 7× | [[Dev-Work - Lokal AI & Tools]] | Dev-Bereich |
| 7× | [[Mnemosyne - Patterns]] | Memory-Patterns |
| 7× | [[Daily-Note-Patterns - Vault-Format]] | Format-Doku |
| 6× | [[Yuno - Identität und Stil]] | Persona |

## Mood/Energy Inventory

| Mood | Count |
|---|---|
| fokussiert | 3× |
| konzentriert-neugierig | 1× |
| konzentriert | 1× |
| ruhig-strukturiert-then-flow | 1× |
| fokussiert-energiegeladen | 1× |
| fokussiert-mit-überraschung | 1× |

| Energy | Count |
|---|---|
| hoch | 3× |
| mittel-hoch | 3× |
| mittel | 1× |

**Nur 8 von 19 Tagen haben Mood/Energy.** Kein "niedrig" oder "erschöpft" je dokumentiert.

## Section-Header Inventar (Top 25)

| Count | Header |
|---|---|
| 17× | ## Erkenntnisse |
| 14× | ## Was lief |
| 13× | ## Wiki-Links |
| 7× | ## Review-Notiz |
| 7× | ## Offene Punkte |
| 7× | ## Auf einen Blick |
| 7× | ## Mood / Energy |
| 5× | ## Siehe auch |
| 4× | ## Offene Punkte (rolling) |
| 4× | ## Mögliche nächste Schritte |
| 3× | ## Was Basti heute explizit gewollt hat |
| 3× | ## Mnemosyne-Anker |
| 3× | ## Bezug zu Vortagen |
| 2× | ## Welche Tools konkret benutzt wurden |
| 2× | ## Lessons Learned |
| 2× | ## 20:00-Addendum: Yuno-Anon-TikTok-Business Evening-Reflect |
| 2× | ## 10:00-Addendum: Yuno-Anon-TikTok-Business Morgen-Plan |

## Trigger-Klassifikation (daily-note-health.py)

| Status | Count | Details |
|---|---|---|
| ✅ HEALTHY | 20 von 21 | Alle Haupt-Dailies + Abend-Suffixe |
| 📝 PARTIAL | 1 | `2026-07-05 - Phase 2 Final.md` (Cluster-Doku, keine echte Lücke) |
| 📝 STUB | 0 | — |
| ✗ MISSING | 0 | — |

**Trigger ist 95% still** — feuert nur bei echten Template-Stubs.

## Mnemosyne Daily-Track Memories

| ID | Importance | Recalls | Inhalt |
|---|---|---|---|
| `b14b658422f017aa` | 0.60 | 32+ | Daily-Discipline: Stub sofort heilen, ~7 Min Workflow |
| `38633f3e32adc109` | 0.85 | 3+ | Session-Start Trigger Pattern (NEU 16.07.) |
| `4845ce726ddace4a` | 0.88 | 16+ | Quality-Gate ist Pflicht, nicht Empfehlung |

## Bekannte Edge-Cases

1. **Phase-2-Final.md** — Cluster-Phase-Doku im Daily-Notes-Ordner → PARTIAL (falsch positiver)
2. **Multi-File-Dailies** (`2026-07-05`, `2026-07-05 - Abend`, `2026-07-05 - Phase 2 Final`) — Trigger prüft nur Haupt-File
3. **Bimodale Größe** — Kein Bug, erwartetes Verhalten (Setup-Phase ≠ Arbeits-Phase)

## Nächste Baseline-Aktualisierung

Nach 30 Tagen oder auf expliziten Audit-Wunsch aktualisieren.
