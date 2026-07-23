# 🅰️🅱️🅲️ Dispatch-Mode Guide — Worked Context

> Origin: 2026-07-09 23:23 Berlin, Basti-Feedback nach Greytrix-Phase-A.
> Siehe `multi-agent-cluster-patterns/SKILL.md` für die Kurzfassung.
> Dieses File enthält den rohen Kontext, aus dem der Guide destilliert wurde.

## Basti's Original-Anforderung (telegram 23:22 Berlin)

> "ja genau kümere dich gut um den Stock, den auf ihm baut alles! (drama bby)
> ahh also haben alle worker die du dispatched hast alle die info da gelassen?
> ja der scope und das thema / task könnten einzelnd behandelt werden
> aber ich finde denn flow richtig nice 2x3...
> mir kommt gerade die idee um es zu..."

→ Basti findet den **2x3-Flow** ("zwei Wellen à 3 Bienen") nice, aber er hat eine **Verfeinerungsidee**.

## Der Verfeinerte Dispatch (Basti's Antwort auf Rolling-Wave-3-Vorschläge)

Basti wählte **Option B** (Rolling-Wave) mit Zusätzen:

### Was Bestand hatte (Standard-Default)
- **Für Mini-Fixes (1-2 Tasks):** Quick inline, keine Plan-Phase → 🅰️
- **Für Standard-Tasks (3 Tasks):** 3 Worker + Verify-Biene parallel → 🅱️

### Was NEU dazukam 🅲️ (Basti's Rolling-Wave)

> "bei großen tasks 3 worker + verify Biene die plan schreibt mit den gesamten
> anforderungen im kopf und dann nach plan worker für worker abgeht die infos
> sammelt mit zum schluss bericht anforderung und gemachte arbeit 1:1
> gegenübersteht dann musst du weniger im nach hinein forschen"

### Kern-Insights aus diesem Feedback

1. **"weniger im Nachhinein forschen"** — das ist der primäre Pain Point. Rekonstruktion ist teurer als Vorn-Planung.
2. **Plan-Biene ≠ Worker-Biene** — die Plan-Biene ist ein eigener Purpose: sie produziert NUR den Plan (Anforderungs-Liste), keine Implementation.
3. **1:1 Mapping** — der Schluss-Bericht ist ein Diff zwischen Plan-Items und Done-Items. Jedes Plan-Item bekommt einen Status: ✅ Done, ⚠️ Partial, ❌ Not Started.
4. **Verify-Biene ist Standard** — auch bei 🅱️ (Standard) ist eine Verify-Biene PFLICHT. Das war vorher nicht explizit.

### Abgrenzung zu Legacy-2x3

Vor diesem Feedback wurde der 2x3-Dispatch so praktiziert:
- **Welle 1:** 3 Bienen parallel
- **Yuno:** Quick-Fixes während Welle 1 läuft
- **Welle 2:** 3 Bienen parallel
- **Yuno:** Konsolidierung NACH beiden Wellen

Die Probleme:
- Königin konnte nicht zwischen den Wellen planen (weil Phase C erst NACH Welle 2)
- Schluss-Bericht war Rekonstruktion aus Memory
- Keine Verify-Biene → Fehler erst in Phase C aufgefallen

Der neue 🔲️-Modus adressiert ALLE drei Probleme.

## Pattern-Zuordnung (Detail)

| Dispatch-Phase | Pattern(s) |
|---|---|
| Phase 0: Inventur (READ-ONLY aller Modi) | kein Pattern, aber bewährte Praxis |
| 🅰️ Dispatch (1-2 Bienen parallel) | Pattern 1 (Read→Patch), Pattern 3 (Anti-Halluz.) |
| 🅱️ Phase A: Spec schreiben (Königin) | Pattern 5 (Subagent-Spec) |
| 🅱️ Phase B: Fan-Out (3 Worker + 1 Verify) | Pattern 2 (Fan-Out) + Pattern 6 (Verify!) |
| 🅱️ Phase C: Königin Quick-Fixes | — |
| 🅱️ Phase D/E: Verifikation + Reporting | Pattern 7 + Pattern 8 |
| 🅲️ Phase 1: Parallel-Recon (3+1) | Pattern 2 + Pattern 6 |
| 🅲️ Phase 2: Plan-Biene | Pattern 11 (Plan schreiben, NUR Plan) |
| 🅲️ Phase 2.5: Königin reviewed Plan | Pattern 9 (Improvisation erlaubt wenn nötig) |
| 🅲️ Phase 3: Worker gestaffelt (1→1→1) | Pattern 1 + Pattern 2 (sequentiell!) |
| 🅲️ Phase 4: Diff-Report | Pattern 8 (angepasst) |

## Beispiel: Wie 🅲️ auf Greytrix angewandt wird

```
Phase 1:  3 Worker + 1 Verify parallel
          ┌──────────────────────────────┐
          │ Worker 1: Recon-Skripte lesen │
          │ Worker 2: Dependencies prüfen │
          │ Worker 3: Configs scannen     │
          │ Verify: Validierung aller 3  │
          └──────────────────────────────┘
Phase 2:  Plan-Biene schreibt A1..A5
          ┌──────────────────────────────┐
          │ A1: Skript A deployen        │
          │ A2: Skript B deployen        │
          │ A3: Log-Cleaner installieren │
          │ A4: Tests durchführen        │
          │ A5: Doku schreiben           │
          └──────────────────────────────┘
Phase 3:  Worker gestaffelt
          Biene-A1: deployt A1 → verifiziert → A1 ✅
          Biene-A2: deployt A2 → verifiziert → A2 ✅
          Biene-A3: ...
Phase 4:  Bericht
          A1 ✅ Done → /home/bratan/bin/recon.sh
          A2 ✅ Done → ...
          A3 ⚠️ Partial 80% → Blocked by dependency Y
          A4 ❌ → Prioritized down after A3 block
          A5 ✅ Done → ...
```

## Verwandte Files

- `SKILL.md` — der Selection Guide (Kurzfassung)
- `references/merger-worker-pattern.md` — Pattern 10 (MERGER, nicht Rolling-Wave)
- `~/00-Meta/navigation.md` — canonical cluster map (Vault-Location)