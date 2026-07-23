# Post-Result Vault-File Pipeline

> **Klassen-Level Reference:** Nachdem Perplexity-Deep-Research-Ergebnisse (oder andere Research-Outputs) zurückkommen und die 3-Stufen-Evaluierung durchlaufen haben: Übersetze die Ergebnisse in strukturierte, permanente Vault-Files + Memory. Validierte auf 5 Vault-Files in Session 2026-07-16 (Kategorie: 3D-Druck).
>
> **Dual-Path-Pattern:** Jeder Research-Pass produziert zwei Persistenz-Artefakte:
> 1. **User-facing Vault-File** — Basti kann es in `~/Dokumente/` lesen, referenzieren, erweitern
> 2. **Agent-facing Memory** — nächste Yuno-Session hat den synthetisierten Stand ohne Neu-Lesen
>
> **Counterpart:** `references/pre-research-subagent-pattern.md` (was VOR dem Prompt passiert)

## Trigger

Dieses Pattern aktivieren wenn:

1. **Perplexity-Result kommt zurück** — Egal ob per copy-paste, DM-forward oder direkt im Chat
2. **Du hast Subagent-Pre-Research gemacht** — Die PRE-VERIFIED SOURCES müssen mit Perplexity-Ergebnissen gemerged werden
3. **Das Topic ist wiederverwendbar** — Research-Output den Basti >1x braucht (Filament-Empfehlungen, Troubleshooting-Guides, Filament-Profile)
4. **Die 3-Stufen-Evaluierung ist abgeschlossen** — Nicht vorher!

**Überspringen wenn:** Einmalige Faktenfrage („Wie spät ist es in Tokio?") → direkte Chat-Antwort reicht, kein Vault-File nötig.

---

## Workflow

### Phase 1: Input-Analyse (Parent, 2-5 Min)

Analysiere den Perplexity-Output + Subagent-Pre-Research + deine 3-Stufen-Evaluierung auf folgende Struktur-Merkmale:

| Merkmal | Finde heraus | Entscheidung |
|---------|-------------|--------------|
| Anzahl Kategorien | Wie viele Sections hat die Antwort? | Jede Section = 1 Tabelle im Vault-File |
| Format der Daten | Tabellen, Listen, Code-Blöcke? | Behalte natives Format bei |
| Konflikt-Items (Pitfall #15) | Welche Items haben unterschiedliche Status in verschiedenen Reports? | Markiere mit DISCREPANCY-Tag, dokumentiere Ursache |
| Custom-Stack-Overlap | Welche Items hat Basti schon? | Markiere als "OWNED / custom" |
| Verified vs. Unverified | Live-gecheckt oder subagent-claimed? | PRE-VERIFIED Tag vs. "needs manual check" |

**Trigger-Question:** Hat dieser Output Wert für >1 zukünftige Verwendung? Wenn Ja → Phase 2. Wenn Nein → Nur Memory (Phase 5), kein Vault-File.

### Phase 2: Vault-File-Struktur wählen

Wähle das passende Schema basierend auf dem Inhaltstyp:

| Inhaltstyp | Schema | Beispiel |
|------------|--------|----------|
| Empfehlungen mit Rank | `| # | Item | Feld1 | Feld2 | URL |` | Filament-Bible, Top-Prints |
| Entscheidungshilfe | `| Szenario | Empfehlung | Warum |` | AMS-Lite Buy/Don't |
| Failure-Modes / Troubleshooting | `| # | Symptom | Cause | Fix | HW/SW | URL |` | Playbook |
| Technische Spezifikation (1 Item) | Strukturiertes Prosa-Format | Filament-Settings pro Marke |
| Sequence / Timeline | `| Schritt | Aktion | Dauer |` | Maintenance-Schedule |

### Phase 3: Vault-File bauen (Parent, 5-10 Min)

**Standard-Template:**

```markdown
# {Emoji} {Title} — {Datum}

> Kurzbeschreibung (1-3 Sätze). Wofür dieses File gut ist.
> Quelle: Perplexity Deep Research ({Prompt-Name})
> Pre-Research Subagent: {ID oder Referenz-Datei-Pfad}

---

## {Category 1}

[Structure per schema above]

---

## {Category 2}

...

---

## 🔗 Verified Sources

| Source | URL | Status |
|--------|-----|--------|
| MakerWorld | makerworld.com/en/models/... | ✅ PARENT-VERIFIED |
| Bambu Wiki | wiki.bambulab.com/... | ✅ PARENT-VERIFIED |
| Reddit | reddit.com/r/.../... | ⚠️ Subagent-reported (Reddit blocks web_extract) |

---

## 🔗 Cross-Refs

- **Verwandtes File:** `related-vault-file.md`
- **Mnemosyne-IDs:** `{id1}`, `{id2}`
- **Original Research Prompt:** `~/.hermes/docus/research-prompts/{prompt-file}.md`
- **Perplexity Original Report:** `~/Dokumente/Perplexity/{report-name}.md`
- **Subagent Summary:** `~/.hermes/cache/delegation/{subagent-summary}.txt`
- **Skill:** `perplexity-followup-plan` (v2.4.0+)

---

**Tags:** `#{domain}` `#{topic}` `#{source}`
**Erstellt:** {YYYY-MM-DD}
**Update-Interval:** {wöchentlich/monatlich/nach Bedarf}
```

**Namenskonvention:**
```
{domain-slug}-{topic-slug}-{YYYY-MM-DD}.md
```

**Zielverzeichnis:** `~/Dokumente/{vault-domain}/` — z.B. `~/Dokumente/3D-CAD/`, `~/Dokumente/tiktok-business/`, `~/Dokumente/system/`, `~/Dokumente/finance/`

### Phase 4: URL-Verification + Cross-Report-Merge (Parent, 3-5 Min)

Führe die finalen Checks durch bevor das File als final markiert wird:

1. **TOP-3-URLs per web_extract checken** — Subagent-Claims sind self-reports (Pitfall #16). Dein eigener web_extract bestätigt ob der Server wirklich antwortet.
2. **Cross-Report-Diff (Pitfall #15)** — Wenn 2+ Perplexity-Reports zum selben Topic: Matrix aus Item + Status pro Report. ROT markieren bei Konflikt.
3. **Display-Name ≠ @Handle Check (Pitfall #14)** — MakerWorld/Platform-Creator-Namen via Model-ID verifizieren. Per Model-ID suchen, nicht per Display-Name.
4. **OBSOLETE-Check (Pitfall #13)** — Jede STL/Code-Empfehlung auf Obsolete-Flags prüfen. Besonders G-Code-Profile und Workarounds (werden oft durch native Features ersetzt).

**Verified-Tagging-Konvention:**

| Tag | Bedeutung | Wann setzen |
|-----|-----------|-------------|
| `✅ PARENT-VERIFIED` | Du hast web_extract selbst aufgerufen und Seite lebt | Immer für TOP-3-URLs |
| `✅ Subagent-VERIFIED` | Subagent hat web_extract gemeldet | Vertrauen aber restliche checken |
| `⚠️ Reddit (unverified)` | Subagent-reportet, Reddit blockt web_extract | Reddit-URLs nur so |
| `❌ NOT FOUND` | URL existiert nicht mehr oder Page 404 | Sofort aus Vault-File entfernen |
| `⚠️ OBSOLETE` | Model wurde als obsolete markiert | Im Vault-File auskommentieren + "replaced by X" notieren |

### Phase 5: Memory schreiben

Nach Finalisierung des Vault-Files:

**Memory-Entry-Struktur (1 Entry per Topic, nicht per File):**

```
{YYYY-MM-DD} {HH:MM} Final State {Topic Pass} — Insgesamt {N} Reports ({brief description}). 
Subagent-verified URLs: {N}. 
Vault-Files created: {file-list}. 
Insights: {key lesson 1}, {key lesson 2}. 
Use-Trigger für nächste Session: "{what Basti should ask next}".
```

**Global scope** (nicht session-scoped) — damit nächste Session den Stand hat.

**Skalierung:** Nicht für 1-2 Einzelfakten nutzen. Nur für >5 Items oder >2 Subagent-Dispatches oder >1 Vault-File.

### Phase 6: Consolidation-Check

Wenn >10 Memory-Items aus dieser Session stammen:

- Check vor Consolidation: `mnemosyne_diagnose()`
- Consolidate ALL sessions: `mnemosyne_sleep(all_sessions=true)`
- Verify nach Consolidation: `mnemosyne_diagnose()`

**Mindestens 1 Health-Check pro Woche.** Der Cron `memory-weekly-consolidate` (Sonntag 04:00) deckt das automatisch ab, aber manuell nach Big-Researches beschleunigt den Working-Memory-Refresh.

---

## Edge Cases

### Fall 1: Perplexity halluziniert → Vault dennoch nützlich?

**Ja — aber mit EXPLICIT DISCREPANCY-Tag.** Beispiel aus 2026-07-16: Perplexity Report #1 sagte "TuTu (@TuTu)", Live-Check zeigte @yujixun. Der Inhalt des Prints war korrekt (Creator existiert, Print existiert), nur der Handle war falsch. Im Vault-File: "Creator: TuTu (MakerWorld: @yujixun — siehe Discrepancy-Note: Perplexity zitierte @TuTu, Model-ID bestätigt @yujixun)".

**Regel:** Wenn Inhalt korrekt aber Metadaten falsch: Inhalt ins Vault-File übernehmen, Metadaten korrigieren + Discrepancy-Note anfügen. Wenn Inhalt selbst falsch (Objekte die nicht existieren): NICHT ins Vault-File.

### Fall 2: Subagent- und Perplexity-Daten widersprechen sich

Beispiel aus 2026-07-16: "Reduce purge by up to 45%" war in Report #1 als Top-Print. Subagent pre-research und Report #2 sagten **OBSOLETE** (Bambu Studio native Feature seit 2024).

**Auflösung:** Subagent/Report #2 hat recht. Report #1 übersah das Obsolete-Flag (Pitfall #13). Im Vault-File: Item aussortieren und unter "## Excluded (Obsolete)" dokumentieren mit Reason. In der Memory: "Cross-Report-Diff gefangen: OBSOLETE-Item von Report #1 ausgesiebt."

### Fall 3: 3+ Reports zu verschiedenen Aspekten des gleichen Topics

**Kein Einzelfile pro Report bauen.** Statt dessen: **Ein konsolidiertes Vault-File** mit Sections pro Report-Aspekt. Beispiel aus 2026-07-16: Statt 3 Files → 5 Files (Druck-Queue + Eval + Filament + Troubleshoot + AMS-Lite). Die Reports splitten sich auf unterschiedliche Vault-Domänen auf.

### Fall 4: Research-Output ist zu lang (>50 Zeilen)

**Teile auf:** Ein Überblicks-File + Detail-Files. Überblicks-File hat die Entscheidungs-Matrix + Top-3-Insights; Detail-Files haben die Tabellen + Verified-Sektion + Cross-Refs.

Beispiel aus 2026-07-16: Troubleshooting-Playbook wurde 235 Zeilen (10 Failure-Modes + ASCII Flowchart + Decision-Matrix + Logs-Sektion). Das ist am oberen Limit. Beim nächsten Mal: Überblicks-File (ASCII-Flowchart + Decision-Matrix) + Detail-File (Failure-Mode-Tabellen + Logs).

### Fall 5: Basti hat keine Zeit für Vault-File

**Fallback:** Nur Memory schreiben + das Subagent-Summary-File als .md im Cache belassen. Biete an: "Soll ich später ein Vault-File draus machen wenn du mehr Zeit hast?"

---

## Cross-Refs

- **Pre-Research Pattern:** `references/pre-research-subagent-pattern.md` (vor dem Prompt)
- **SKILL.md Hauptsektion:** Post-Result: Vault-File Creation (Stufe 4) + Post-Result: Memory Consolidation (Stufe 5)
- **Beispiel-Files (Session 2026-07-16):** `~/Dokumente/3D-CAD/` — 5 Files: druck-queue, eval, filament-bible, troubleshooting-playbook, amslite-decision
- **Subagent-Cache:** `~/.hermes/cache/delegation/`
- **Research-Prompts:** `~/.hermes/docus/research-prompts/`
- **Perplexity Orginal-Reports:** `~/Dokumente/Perplexity/`
