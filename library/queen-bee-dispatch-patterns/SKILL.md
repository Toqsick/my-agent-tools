---
name: queen-bee-dispatch-patterns
title: "Queen-Bee — Dispatch Patterns (Briefing, File-Affinity, Cross-Wave)"
description: "Use when setting up a queen-bee dispatch: briefing templates, file-affinity checks, cross-wave learning, or subagent limits. NOT for queen-verify patterns (use queen-bee-queen-verify)."
category: queen-bee-schwarm-dispatch
version: '1.0'
created: '2026-07-23'
author: Yuno (split from queen-bee-schwarm-dispatch)
lane: koenigin
agent: universal
trigger_keywords: ['dispatch', 'briefing', 'file-affinity', 'cross-wave', 'subagent', 'wave', 'pattern']
keywords: ['dispatch', 'briefing', 'file-affinity', 'cross-wave', 'subagent', 'queen-bee']
related_skills: ['queen-bee-queen-verify', 'queen-bee-advanced']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from queen-bee-schwarm-dispatch 2026-07-23)'

license: MIT
---

# Queen-Bee — Dispatch Patterns (Briefing, File-Affinity, Cross-Wave)

_Extracted from queen-bee-schwarm-dispatch on 2026-07-23._

## Wann dispatchen?

**Echte Fäden, klar abgegrenzte Outputs.** Beispiel-Muster:
- "Architektur-Recherche Stack A / Stack B / Stack C parallel"
- "Cross-Check: Skizze X vs. Live-State Y"
- "Docu-Audit: Skill-Konsistenz / Driftsuche / Patch-Vorbereitung"
- "Stub-Heilung: 3 Daily-Stubs parallel füllen mit Format-Constraints"
- "Vault-Vervollständigung: Manuals + Referenz-Doku + Live-DB-Extraktion parallel"
- "Audit: read-only DB-Extraktion + Drift-Matrix + Stale-Marker"
- "Queen-Mutation + orthogonaler Bienen-Schwarm": Queen macht Mutationen (Code-Edits, Config, Cron, Memory), Bienen machen parallel Read-Only-Audits in Bereichen die die Queen übersieht. **NEU (2026-07-15)** — siehe Section "Orthogonal Scout-Biene Pattern" unten.

**NICHT** dispatchen bei:
- Einer Frage mit klarer Antwort (einfacher `terminal` reicht)
- Reine Ausführungs-Tasks ohne Recherche (Cron fixen, Skills installieren)
- Tasks die aufeinander aufbauen (dann **eine** Biene mit Sub-Tasks, nicht 3 parallel)

## Muster-Welle

**Standard: 1 Welle mit 3-4 Bienen. Bei komplexem Scope: 2 Wellen.**

```
Welle 1 = P0+P1 Discovery (3-4 Bienen parallel)
  ├── Biene A: Architektur-Recherche / Manual-Synthese Topic A
  ├── Biene B: Architektur-Recherche / Hacking-Cookbook Topic B
  ├── Biene C: Architektur-Recherche / Library-Katalog Topic C
  └── Biene D: Audit / Drift-Check (read-only DB-Extraktion)

  ↓ Queen-Verify mit cross-source-check (Filesystem, nicht Self-Report)

Welle 2 = P1+P2 Vertiefung (nur wenn noetig)
  ├── Biene A: Patch / Stale-Marker / Vault-Update
  ├── Biene B: Diagnose / Cross-Reference-Validation
  └── Biene C: Queen-Artefakt-Verdichtung
```

**Max 6 Subagenten pro Dispatch-Session.** Mehr = Context-Bloat + laengere Verify-Runden.

**4-Bienen-Heuristik (validiert 2026-07-14):** Bei Vault-Vervollstaendigung mit 4 Topics (Sprachreferenz + Cookbook + Lib-Katalog + Audit) ist 1 Welle mit 4 Bienen optimal. Jede Biene bekommt eine eindeutige Output-Datei (file-affinity check vor Dispatch). Biene 4 (Audit) ist immer die kurzeste und praziseste, weil sie nur die Live-DB gegen bestehende Notes matched.

## Briefing-Template

Briefing muss enthalten:

1. **Identity** — "Du bist Biene N von 3-4 in Yunos Schwarm-Research zu <Topic>."
2. **Context** — Kurz, prazise. Name Basti, Tooling-Stack, Bezug zur laufenden Quest.
3. **Tasks** — nummeriert, jedes Task mit Pfad-WHERE und Aktion-WHAT.
4. **Output-Format** — Quantitative Constraints, nicht nur "Markdown-Struktur". Beispiele:
   - `0 mid-sentence **boldface**` — keine mechanischen Hervorhebungen
   - `<=1 em-dash (—)` — maximal ein Gedankenstrich, Kommas oder Punkte bevorzugen
   - `0 inline-header bullet lists` — kein `**Header:** text` in Bullet-Listen
   - `>=3 Wiki-Links` — bei Daily-Notes: mindestens 3 `[[Wiki-Link]]` Referenzen
   - `>=1 eigenes Insight` — nicht nur Facts sammeln, eine Erkenntnis oder Meinung formulieren
   - Max-Wortzahl und Markdown-Struktur (Heading + Bullets), Sprache (Deutsch!)

**Quality-Gate als PFLICHT (validiert 2026-07-14):** Die Output-Format-Constraints sind NICHT optional. Setze sie als harte Grenzen im Briefing-Text, nicht als "Empfehlung" oder "Hinweis". Formuliere sie als: "0 mid-sentence boldface — NICHT ERLAUBT. 0 em-dash — VERBOTEN. >=3 Wiki-Links — PFLICHT."

Validierte Faustregel: Bienen mit PFLICHT-Formulierung im Briefing hatten 0 Verstoesse ab erstem Wurf (Biene 1+4 am 2026-07-14). Bienen mit Empfehlungs-Formulierung (Biene 2+3) brauchten 2-3 Nachbesserungs-Runden. Die Wortwahl im Briefing ist der groesste Einzelfaktor fuer Output-Qualitaet.

Empfohlenes Format fuer die harten Grenzen im Briefing:
```
OUTPUT-CONSTRAINTS (PFLICHT - NICHT VERHANDELBAR):
- 0 mid-sentence boldface
- 0 em-dashes, Kommas oder Punkte statt Gedankenstrichen
- 0 Inline-Header-Bullet-Listen
- >=5 Wiki-Links zu verwandten Notes (im Vault existierend)
- >=1 eigenes Insight / Erkenntnis
- Max 1000 Woerter
- Sprache: Deutsch
```

**Wichtig (validiert 2026-07-13):** Biene 2 hat im Self-Report "All criteria met" behauptet, aber die Koenigin-Verifikation live im Filesystem fand 17 mid-sentence Boldface + 5 Inline-Header-Listen. **Quantitative Constraints ohne Verification-Schritt sind wirkungslos** — die Biene prueft nicht selbst nach, sie halluziniert "alles OK".
5. **Toolset-Restrictions** — was darf benutzen (read_file, terminal, write_file, patch), was tabu (sudo, git push, service-restart ausser explizit).
6. **Self-Verify-Anweisung** — "Alle Fakten mit Quelle markieren. Nichts erfinden. Lieber 'unbekannt, weil kein web_search verfuegbar' als halluzinieren."
7. **No-Write-Out** — "Dein Output ist REIN TEXT in deiner Antwort. Datei-Schreiben nur wenn im Briefing explizit erlaubt."

**Laengen-Tipp:** Briefing **60-70% der Queen-Detail-Laenge**. YAML-Frontmatter weglassen, pragnante Prosa, klar strukturierte Listen.

## File-Affinity Check (validiert 2026-07-14)

**VOR** dem Dispatchen jeder Welle: prüfe, ob jede Biene eine **eindeutige Output-Datei** bekommt:

```bash
# Check: keine zwei Bienen schreiben in dieselbe Datei
echo "Biene 1 -> GreyScript-Sprachreferenz-2026-07-14.md"
echo "Biene 2 -> GreyHack-Hacking-Cookbook-2026-07-14.md"
echo "Biene 3 -> GreyHack-Lib-Katalog-2026-07-14.md"
echo "Biene 4 -> GreyHack-Audit-2026-07-14.md"
# Manuell prüfen: alle 4 Dateinamen unterschiedlich? Ja -> dispatch
```

Wenn zwei Bienen in dieselbe Datei schreiben wuerden: Scope anpassen oder eine Biene umwidmen. Overlap führt zu Lost-Writes und Merge-Konflikten.

**Referenz:** `references/audit-bee-pattern.md` enthaelt das vollstaendige Briefing-Beispiel aus der 2026-07-14 Session (4 Bienen, non-overlap file-scope).

## Cross-Wave Learning (NEU 2026-07-13 — validiert 19 Files, 4 Wellen)

Wenn du **mehrere Wellen** nacheinander dispatchst (z.B. 6+6+3 Bienen), nutze die Findings aus Welle 1, um Welle 2+3 zu schaerfen — noch bevor du sie dispatchst:

```python
# Pattern:
Welle 1 dispatch → verify → A6 OVERRIDE noetig (Boldface)
  ↓ Queen analysiert: "Der Mid-Line-Inline-Header wird immer noch von den Bienen gemacht"
  ↓ Queen patcht Briefing: "Achtung: `**L1:**` mid-line in Bullets ist verboten — nicht `- **L1:** text` schreiben"
Welle 2 dispatch (mit geschaerftem Briefing) → verify → 0 Overrides
Welle 3 dispatch (gleiches Briefing) → 0 Overrides
```

**Warum das funktioniert (Beweis 2026-07-13):**
- Wave 1 hatte 1 Override (A6, Mid-Line-Inline-Header in aeltester Daily 03.07.)
- Nachdem ich das Briefing für Wave 2 mit einem expliziten Hinweis auf das Pattern ergaenzt hatte: **6 Bienen in Wave 2, 0 Overrides**
- Wave 3 (3 Bienen): ebenfalls 0 Overrides
- Insgesamt: 15 Bienen, 3 Wellen, 2 Overrides (1 in Stub-Welle + 1 in Wave 1), 19 Files, ~10 Min Wall-Time

**Faustregel:** Die aeltesten/komplexesten Files zuerst dispatchieren (Wave 1 = schwierigste Arbeit). Wenn da was schiefgeht, lernst du es frueh und die naechsten Wellen profitieren. Wenn Wave 1 clean durchkommt, kannst du Waves 2+3 leichteren Herzens dispatchen.

**Nicht machen:** Alle Wellen parallel dispatchen. Dann findest du Overrides erst NACH Abschluss aller Arbeit — und musst entscheiden, ob du nachbesserst (mehr Wall-Time) oder ertraegst (schlechtere Qualitaet).

## Subagent Over-Reporting Pitfall (NEU 2026-07-17 — validiert Welle 1+2)

**Validierung:** Biene 1 Welle 1 meldete "2 hardcoded Pfad-Listen gefunden". Queen Pre-Scout vor Welle 2 fand **3** (1 zusätzlich in Vault-Phase-4-Plan.md:40).

### Das Problem

Wenn ein Subagent sagt "N files with issue X found", ist das ein **Self-Report**, kein verifizierter Fakt. Der Subagent scannt so schnell wie möglich, übersieht dabei oft:
- Dateien mit abweichendem Format (Range-Listing statt Single-File-Referenz)
- Pfade in anderen Quellen als den offensichtlichen (z.B. Plan-Dokumente statt Daily-Notes)
- Files die der Subagent als "irrelevant" klassifiziert hat (implizites Urteil)

### Die Regel

Bevor du eine Fix-Welle dispatchst: ALWAYS Pre-Scout die Subagent-Behauptung "N files":

```text
Biene sagt: "2 files gefunden"
  ↓ Queen macht schnelles grep ("finde alle Referenzen auf X")
  ↓ Ergebnis: 3 files
  ↓ Welle 2 dispatchen mit korrektem Count, nicht mit Biene-1-Count
```

**Warum das funktioniert:** Ein grep/scout von der Queen dauert 10-30 Sekunden und deckt die Biene-Lücken auf. Ohne Pre-Scout dispatchst du eine Welle die entweder:
- Nur 2 von 3 Files patched (Lücke)
- Oder die Biene-1-Ergebnisse wiederholt (doppelte Arbeit)

### Spezifische Heuristiken (validiert 2026-07-17)

| Biene-Report | Pre-Scout-Check | Warum |
|---|---|---|
| "N hardcoded Pfade" | `grep -rn "alter/pfad"` über Domain | Biene scannt nur offensichtliche Quellen |
| "N MOCs mit Issue" | `find ... -name "MOC*.md" \| wc -l` + stichproben | Biene klassifiziert schnell |
| "N Daily-Stubs" | `python3 daily-note-health.py --json` | Biene hat eigene Heuristik |
| "N Format-Verletzungen" | `grep -c` auf ALLE betroffenen Files | Biene prüft nur ihren Sample |

### Integration mit Pitfall #36 (REVIDIERT 2026-07-17 — Tool-Bug, nicht Subagent-Halluzination)

Pitfall #36 wurde am 2026-07-17 revidiert: die ursprünglich vermutete "Subagent-Halluzination von Mnemosyne-IDs" (Variante d) stellte sich als **Tool-Bug** heraus (Pitfall #44: `mnemosyne_get` liefert `not_found` für ALLE IDs, selbst von der Queen gesetzte). SQLite-Direkt-Query und `mnemosyne_recall` bestätigen dass alle 7/7 Subagent-Anker real sind. Subagent Over-Reporting ist eine verwandte, aber unterscheidbare Variante: "subagent reports accurate but incomplete data" vs. "reports hallucinated data" (die nie eintrat — der Vorwurf war false positive). Beide erfordern Queen Verify — aber Over-Reporting erfordert einen **eigenständigen Pre-Scout-Scan**, nicht nur Verifikation der Bienen-Outputs. Für Mnemosyne-Anker-Verifikation: `mnemosyne_recall(query=...)` statt `mnemosyne_get(id=...)` verwenden (Dual-Verification Workflow).

### Referenzen

- `references/full-system-audit-plan-example.md` — der Full-System-Audit-Plan von 2026-07-17 zeigt die P0-P3-Struktur die aus der Welle-1→Welle-2-Verbesserung entstanden ist.

---

## Subagent-Limits (was Subagents NICHT haben)

| Tool | Verfuegbar? | Begruendung |
|------|------------|-----------|
| `web_search`, `web_extract` | ⚠️ toolset-abhängig | Historisch im MiniMax-M3-Worker-Setup nicht enabled. **Das ist ein `toolsets`-Config-Fakt, kein M3-Modell-Fakt** — Toolsets driften; vor Annahme gegen das aktive Worker-Profil prüfen (`hermes -p <profil> ...` bzw. `toolsets`/`disabled_toolsets` in config). Wenn nicht enabled: externe Recherche macht die Queen vorher oder markiert sie explizit als 'allowed'. |
| `web_fetch` (curl direkt) | ✅ (ueber `terminal`) | Workaround wenn web_search fehlt — aber langsamer |
| `delegate_task` | ❌ Default — Subagent ist immer LEAF. | AND-Gate: `delegate_task` bleibt im Toolset NUR wenn `role='orchestrator'` **UND** `max_spawn_depth >= 2`. Ein leaf-Biene hat delegate_task nicht, selbst bei max_spawn_depth=10. Config-Änderung: `hermes config set delegation.max_spawn_depth 2` + Backup + `hermes config check` verify. ⚠️ Config wird beim Hermes-Process-Start gecached — Änderungen wirken erst im NEUEN Session-Start, nicht im laufenden Dispatch. **Wichtigster Pitfall:** der erste Sub-Sub-Test scheiterte weil `role='leaf'` dispatcht wurde (selbst bei max_spawn_depth=2). Fix: IMMER `role='orchestrator'` setzen. |
| `clarify` | ❌ | Subagents fragen NICHT — sie geben Self-Report, Queen bewertet |
| **sudo / root / system-mutation** | ❌ **HART VERBOTEN** | Subagents laufen mit `delegate_task` als User bratan — kein sudo, kein root, kein Service-Restart (ausser mit Briefing-Override UND User-Bestaetigung im Briefing-Text). **Biene-Auftrag mit sudo-Bedarf = Queen-Task, NICHT dispatchen.** Validierte Heuristik (2026-07-14): Task braucht `sudo`/`grub-set-default`/`systemctl restart`/`apt`/`update-grub` → Queen-only. Task ist read-only inspection / doc-creation → Biene okay. Gemischt: Biene fuer read-only + Queen macht Mutationen mit User-Confirm. |
| Mnemosyne recall | ✅ | Persistente Memories wirken auch für Subagents |
| `terminal(background=true)` | ✅ | Wie Queen |
| File-Write | ✅ (wenn erlaubt) | Default: READ-ONLY ausser Briefing erlaubt es |

## Pitfalls

- **❌ Biene-Auftrag mit Halluzinations-Risiko.** Wenn du nicht weisst, wie die Antwort aussehen soll, dispatch NICHT.
- **❌ Biene darf Service restarten ohne explizite Anweisung.** Auch nicht "fire and forget" — Restart = User-Confirm.
- **❌ Biene darf sudo.** Niemals.
- **❌ Lang-Briefings mit YAML-Frontmatter u.ae.** Werden gekuerzt oder ignoriert. Prost.
- **❌ MiniMax-M3 Biene fuer Hard-Logic-Debug.** Fuer "welcher Cron-Eintrag ist falsch" oder "warum crashed der Python Import" → Queen direkt machen, nicht Biene.
- **❌ Mechanik-Tasks an Bienen delegieren (NEU 2026-07-15).** Python-Scripte schreiben, Config-Edits, Cron setzen, Memory schreiben, Backup machen — das sind Parent-Direct Tasks. Bienen sind READ-ONLY AUDITORS, nicht Mutatoren. Validierte Heuristik: Task ist Mechanik (deterministisch, single-file, kein Reasoning) → Queen. Task ist Judgment (Cross-Check, Klassifikation, Duplikat-Suche) → Biene. Gemischt: Biene fuer den Audit-Teil, Queen fuer den Mechanik-Teil (Orthogonal Scout Pattern).
- **❌ Memory als Grund fuer Action-Blockade ohne Fresh-Check (NEU 2026-07-11).** Memory-Zitat aus alter Session ("PR #55 Review nach Rabat") → Basti wusste nicht wovon ich rede, PR war bereits gemerged. Vor jeder "halt, weil Memory sagt X"-Entscheidung: **FRESH-CHECK** mit `git log`, `gh pr list`, `systemctl status`, `read_file`, whatever aktuellen State zeigt. Wenn stale: alte Info nicht erwachnen — auf aktuellem Stand weitermachen. **Validated 2026-07-11:** Koenigin zoegerte Push auf vermeintlich Rabat-pending Branch — PR war bereits gemerged. Kosten: 3 unnoetige Clarify-Runden + User-Verwirrung.
- **❌ Biene-Self-Report zu Format-Constraints glauben (NEU 2026-07-13).** "All criteria met" im Self-Report ≠ alle Kriterien erfuellt. Validierter Fall: Biene behauptete 0 Boldface, grep zeigte 17. **Immer live-filesystem pruefen, nie Selbstauskunft.**
- **❌ Bei Format-Verletzungen sofort neu dispatchen (NEU 2026-07-13).** Targeted Patches als Queen sind schneller und praeziser (2 Min vs 3-5 Min). Nur bei > 20 Verletzungen oder strukturellen Fehlern neu dispatchen.
- **❌ Bienen nur ihre Slice des Briefings geben (NEU 2026-07-14).** Bei Coordinated-Multi-File-Document-Dispatch (Specs, Reports, Briefings) mit Cross-Referenzen MUSS jede Biene den VOLLSTAENDIGEN Brief lesen — sonst verlinken sie ins Leere. Validated: 5 Specs, 88 KB, 3 Bienen, alle Cross-Refs korrekt.
- **❌ Cross-Reference-Self-Reports der Bienen glauben (NEU 2026-07-14).** Eine Biene die sagt "alle Cross-Refs korrekt" ist nicht verifiziert. Queen MUSS `grep` auf die tatsaechlichen Output-Files machen: `grep -ohP 'lesson-\d+-[\w-]+' *.md | sort -u` vs. `ls lesson-*.md`. Validated: Biene A lieferte 2 nuetzliche Cross-Ref-Hinweise fuer Biene B+C, die nur durch manuelle Befund-Uebernahme auffindbar waren.
- **❌ Stale-Marker erst am Ende setzen (NEU 2026-07-14).** Wenn Audit-Biene Drift identifiziert: sofort Stale-Marker setzen, nicht warten bis alle Bienen-Outputs gelesen sind. Sonst verlinken die anderen Bienen auf eine stale Note und der Drift wird durch Cross-Refs weitergetragen.
- **❌ `role='orchestrator'` vergessen (CRITICAL — NEU 2026-07-14).** `max_spawn_depth=2` allein reicht NICHT. Der Toolset-Strip in `tools/delegate_tool.py:705` prüft `role != 'orchestrator' AND max_spawn_depth < 2` — beide Bedingungen müssen erfüllt sein damit delegate_task entfernt wird. Heißt: EIN `role='leaf'` genügt, um delegate_task zu killen, selbst bei max_spawn_depth=10. **Immer `role='orchestrator'` im delegate_task-Call setzen wenn Sub-Sub gewünscht ist.** Validated: erste Runde mit leaf = 0 Subs, zweite Runde mit orchestrator = 3/3 Subs.
- **❌ Orchestrator-Biene ohne "DU MUSST Sub-Sub spawnen" im Briefing (NEU 2026-07-14).** Wenn das Briefing Sub-Sub nur als Option erwähnt ("kannst auch Beta spawnen"), macht die Biene alles selbst. sub_call_count = 0. **Fix:** "Du MUSST Sub-Sub Beta aktiv spawnen für Task X" als harte Anforderung.
- **❌ Parallel-Math ignorieren (NEU 2026-07-14).** 3 Parent + 3 Sub-Sub = 6 = exakt max_concurrent_children. Wenn auch nur ein weiterer Background-Job läuft → Dispatch schlägt mit "too many children" fehl. **Fix:** vor Sub-Sub-Dispatch `process(action='list')` checken wie viele background-Jobs laufen. "Bevorzuge 0 boldface" fuehrt zu 17 Boldface-Stellen. "0 boldface — NICHT ERLAUBT" fuehrt zu 0. Die Wortwahl im Briefing ist der groesste Einzelfaktor fuer Output-Qualitaet. Immer PFLICHT/NICHT ERLAUBT/VERBOTEN, nie empfehlen/bevorzugen/ideal.
- **❌ Erste Hypothese selbst testen statt Code-Trace Bee dispatchen (NEU 2026-07-16).** Queen rät "API-Key fehlt" und verbringt 3-5 Min mit .env-Prüfung. Code-Trace Bee findet in 87s den echten Fehler (Import-Fail). **Regel:** Interne Code-Pfad-Diagnose → zuerst Code-Trace Bee dispatchen. Netzwerk/Port-Diagnose → Queen direkt. Siehe `references/hypothesis-falsification-biene-x-worked-example.md`.
- **❌ Skip-Entscheidung nicht dokumentieren (NEU 2026-07-16).** Wenn User "skip D" sagt: sofort im Report vermerken mit Zeitstempel + Runbook-Ziel. Memory-Notiz schreiben ohne Runbook-Datum = vergessen. Siehe Skip-Decision Protocol oben.
- **❌ Queen Baseline "Confidently Wrong" — gleiche Quantität ≠ gleiche Ursache (NEU 2026-07-16, Skill-Audit).** Queen misst "12 Descriptions <30 chars". Biene A misst auch "12". Queen denkt "100% Match — alles korrekt". Aber Biene A sagt: "Die 12 sind leere/falsche YAML-Descriptions, nicht nur kurze." Queen hatte die richtige METRIK, aber die falsche URSACHE. **Fix: Triple-Gate Cross-Check** — (1) Metrik-Vergleich, (2) Root-Cause-Validierung (Listen der Skills vergleichen!), (3) Bienen-Methodik-Stichprobe. Faustregel: Wenn Queen + Biene gleiche Zahl aber unterschiedliche Ursache nennen → vertraue Biene für Ursache. Biene hatte 2-4 Min Zeit und Live-YAML-Parse, Queen nur 40s Surface-Scan. Siehe `references/skill-audit-4-bee-workflow.md` § Confidently-Wrong-Pitfall.

### Memory-Freshness erweitert Queen-Verify (NEU 2026-07-11)

Die beste Queen-Verify checkt **nur Subagent-Claims** gegen das Live-Filesystem. **Fehlt: QUEEN'S EIGENE Memory-Claims frisch zu checken, bevor sie als Entscheidungsgrundlage dienen.**

| Phase | Was Queen checkt | Bisher | Neu |
|-------|-----------------|--------|-----|
| Nach Welle 1 | Subagent-Befunde ✅ | `systemctl status`, `ss -tlnp`, `ls` | ✅ vorhanden |
| Vor Action-Delay | Eigene Memory-Claims ❌ | Kein Check — alte Memory zitiert | `git log`, `gh pr list`, `df -h`, `ls`, whatever |

**Pattern:** Jede Queen-Entscheidung die sich auf "Memory sagt X" stuetzt → zuerst: `git fetch origin && git log --oneline origin/main..HEAD`, `gh pr list --head X`, oder den konkreten Dienst/Datei live pruefen. **Memory ist eine RICHTUNG, kein Beweis.**
