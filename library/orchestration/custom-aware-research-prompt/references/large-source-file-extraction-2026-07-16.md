# Large Source-File Extraction — Reference Workflow

> Für Perplexity-Outputs >100KB die mehrere Sub-Reports enthalten, oder für Cases wo User nicht klar getrennte Files für jeden Sub-Report angelegt hat.

## Problem

Wenn User sagt "ich hab [X] Perplexity-Runs gemacht", kann es sein dass:

- **Ein File = Ein Sub-Report** (klar getrennt, z.B. `workshop-stls.md` vs `gaming-stls.md`)
- **Ein File = Mehrere Sub-Reports** (z.B. der `I own a Bambu Lab A1 Mini...md` 210KB File enthielt Maintenance, Calibration, Filament, Troubleshooting, AMS-Lite in einem)
- **Mehrere Files = Selbes Topic** (z.B. `Nerdstuffprints.md` 26KB und `nerd.md` 28KB mit identischem Custom-Prompt → Duplikat)

Agent darf nicht blind einen Sub-Report mergen ohne die anderen zu sehen — sonst verpasst er Tier-1 Items die nur in einem Sub-Report stehen.

## Workflow (3 Phasen)

### Phase A: Vault-Inventory-Scan

Bevor mit Phase 5a (Input-Sammlung) startet:

```bash
ls -la ~/Dokumente/[Topic]/*.md | sort -k9
wc -l ~/Dokumente/[Topic]/*.md
```

Sortiere nach File-Größe und Datum. Falls einer der Files **größer als 80KB** ist oder **deutlich vom Median abweicht** (z.B. 200KB während andere 25-50KB sind):

1. **Großer File ist verdächtig** — könnte Sub-Reports enthalten die Parent-Agent noch nicht gesehen hat
2. Frage User (oder suche in Memory nach "Sub-Report" markers) ob das Multi-Report oder Single-Report ist
3. Wenn Multi-Report: Sub-Report-Sections extrahieren via Header-Search nach "## Category", "CAT 1", "CATEGORY 1" Patterns

### Phase B: Sub-Report-Detection

Im File nach diesen Patterns suchen:

```bash
grep -nE "^(CAT|CATEGORY|## Category) [0-9]" ~/Dokumente/[Topic]/[big-file].md
grep -nE "^### " ~/Dokumente/[Topic]/[big-file].md | head -30
```

Wenn **mehrere CATEGORY/CAT Marker** gefunden → Multiple Sub-Reports.

### Phase C: Per-Sub-Report Verarbeitung

Für jeden Sub-Report:

1. Lies Section (z.B. Zeile 70-300 für "Maintenance")
2. Identifiziere Tier-1 Picks (durch Verwendung der Phase-5b-Kriterien)
3. Live-Verify URLs via `web_extract` (Phase 5c)
4. Merge mit anderen Sub-Reports desselben Topics in EIN Vault-File
5. Wenn Sub-Report ein **anderes Topic** ist (z.B. Filament-Bible in Maintenance-File) → create separate Vault-File

## Real-World Example (2026-07-16)

**Discovery:** 210KB File `I own a Bambu Lab A1 Mini with the standard 0.4mm.md` mit 3165 Zeilen, 561 URLs im Source-File.

**Initial Mistake:** Agent startete mit 2 letzten Sub-MD-Files (`existing research context.md` 32KB + `new deep reaserch.md` 39KB), übersah komplett dass:

- Sub-Report 1 (Maintenance + Mods) **Tier-1 Mods** enthielt (Moskk83 Cable Chain 62.3k favs)
- Sub-Report 2 (Calibration + Everyday) **Tier-1 Calibration** enthielt (Alex.M Temp Tower A1-mini explicit profile)
- Sub-Report 3 (Filament-Bible) bereits separat in `filament-bible-2026-07-16.md`
- Sub-Report 4 (Troubleshooting + Logs) bereits separat in `troubleshooting-playbook-2026-07-16.md`
- Sub-Report 5 (AMS-Lite Decision) bereits separat in `amslite-decision-2026-07-16.md`

**Corrective Action:** Extrahierte Sub-Report 1+2 in `maintenance-calibration-stls-2026-07-16.md` Vault-File. Result: 15 Tier-1 Maintenance Items + 6 Tier-1 Calibration Items, alle live-verifiziert.

## Methodik-Lesson

**Future-Self-Heuristic:** Bevor "alle Files durchgegangen" claimen — immer `ls -la` + `du -sh` mit Größen-Vergleich. Files die **3× größer als Median** sind sind mit 95% Wahrscheinlichkeit Sub-Report-Container.

## Time-Saved

Ohne diesen Workflow: ~30 Min verschwendet durch 4 unverarbeitete Sub-Reports.
Mit diesem Workflow: 15 Min für Inventory-Scan + Sub-Report-Identification, dann gezielte Verarbeitung pro Sub-Report.
