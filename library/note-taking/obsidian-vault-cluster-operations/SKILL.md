---
name: obsidian-vault-cluster-operations
description: >-
  Use when user asks for expanding an Obsidian vault with parallel subagents, running a vault cluster phase, building a multi-level MOC hierarchy, or coordinating a vault fan-out. NOT for editing a single note or auditing backlinks without content expansion. Applies pre-flight path checks, conflict-safe read-patch retries, scoped worker ownership, verification, and recovery patterns.
category: note-taking
platforms:
- linux
- macos
- windows
version: 1.3.0
author: Yuno (Basti)
source: vault/05 Ressourcen/Skill-Ableitung - Vault-Phase-2-3.md
lane: koenigin
reasoning_effort: xhigh
metadata:
  hermes:
    tags:
    - obsidian
    - vault
    - cluster
    - subagent
    - delegation
    related_skills:
    - obsidian
    - vault-architecture
    - obsidian-subagent-briefing-template
    - multi-agent-cluster-patterns
    - delegation-anti-patterns
    - coding-agents
    - gemini-vault-worker
    triggers:
    - vault cluster
    - parallel subagents vault
    - vault phase 2
    - MOC hierarchie
    - Read→Patch-Retry
    - cross-link audit
    - cross-reference matrix
    - N Notes cross-link
triggers:
- vault cluster
- parallel subagents
- obsidian phase 2
- MOC-Hierarchie
- Read Patch Retry
license: MIT
trigger_keywords: ['vault', 'obsidian-vault-cluster-operations', 'expanding', 'obsidian', 'with']
keywords: ['vault', 'user', 'asks', 'expanding', 'obsidian']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['vault-architecture', 'vault-gemini-cluster-worker', 'obsidian']
---


# Obsidian Vault — Cluster Operations

Operate an Obsidian vault via **parallel subagent clusters**. Bündelt die 5 Patterns aus Phase 2/3 (`Skill-Ableitung - Vault-Phase-2-3.md`) zu einem operativen Skill.

## Trigger Conditions

Use this skill when the user asks to:
- "Befülle meinen Vault mit N Subagents parallel"
- "Cluster-Phase starten" / "Phase 2/3"
- "Vault durch parallele Subagenten wachsen lassen"
- "MOC-Hierarchie aufbauen" (3-stufig)
- "Vault-Expansions-Run" / "Vault-Fan-Out"
- "Subagents für Vault-Arbeit koordinieren"

Nicht für: einzelne Note-Edits (→ `obsidian` Skill), Architektur-Design (→ `vault-architecture` Skill), Quality-Audit (→ `obsidian-vault-quality-audit` Skill).

Neu (2026-07-05): Vault-Arbeit mit External-LLM-CLI (Gemini/Claude/Codex) als Worker-Tool statt reinen Subagents — siehe Pattern 9.

## Core Principles (8 Patterns)

### Pattern 0a: Pre-Flight Plan-Reality Check

**Problem:** Das Briefing/der Plan enthält eine dateibasierte Spec (Pfade, Zeilenzahlen, Inhaltsangaben), aber die tatsächliche Vault-Struktur ist davon bereits abgewichen — z. B. weil eine frühere Session eine Datei verschoben hat, ohne den Plan zu aktualisieren.

**Symptom im Briefing:** `05 Ressourcen/MOC - Daily Notes.md (0 Zeilen)` — aber die Datei liegt wirklich unter `/MOC - Daily Notes.md (0 Zeilen)` (root) oder existiert gar nicht.

**Lösung — vor Fan-Out IMMER ausführen:** 

```python
# 1. JEDEN Pfad aus dem Plan gegen das echte Filesystem prüfen
for path in plan.paths:
    if os.path.exists(path):
        lines = wc_l(path)    # echte Zeilenzahl
        if lines != plan.lines:
            document_deviation(path, plan.lines, real_lines)
    else:
        search_files(target="files", pattern=basename(path), path=vault_root)
        # → gefundenen Pfad protokollieren; Plan muss korrigiert werden
        raise PlanRealityMismatch(f"{path} not found → alternatives: {search_results}")

# 2. Zero-Content vs. Nicht-Existenz disambiguieren
#    read_file(path) bei 0-Zeilen → gibt 0 lines zurück
#    terminal("wc -l path") → gibt "0" zurück
#    beides sagt NUR "exists but empty", nicht "doesn't exist"
#    Fehler von read_file(path) oder search_files sagt "doesn't exist"
#    → Stat: terminal("stat --format=%s path") → bei 0 bytes = truly empty file
```

**Ergebnis:** Entweder Plan ist aktuell → weitermachen, oder Plan hat Stale-Einträge → korrigieren bevor ein Subagent ins Leere patcht.

**Praktisches Beispiel (Phase 6, 2026-07-05):**
- **Plan sagte:** `05 Ressourcen/MOC - Daily Notes.md` — existierte nicht an diesem Pfad
- **Reality:** Die Datei lag in `/MOC - Daily Notes.md` (root) mit 0 Bytes / 0 Zeilen
- **Abweichung dokumentiert** und Improvisation-Permission (Pattern 6) für write_file auf dem korrekten Pfad genutzt

→ Siehe auch `references/plan-reality-verification.md` für vollständige Worked Examples.

### Pattern 1: Read→Patch-Retry bei Sibling-Konflikten

**Symptom:** Das `patch`-Tool gibt eine `_warning` im Ergebnis-Objekt zurück — genau dieses Format:

```json
{
  "_warning": "... was modified by sibling subagent 'sa-0-7f1728e2' at 18:33:47 — after this agent's last read at 18:30:39. Re-read the file before writing."
}
```

Tritt auf bei parallelen Subagents, die dieselbe Datei anfassen, obwohl disjunktes File-Scope vereinbart wurde — oder wenn zwei Cluster-Wellen überlappen.

**Lösung:**
```python
if result.get("_warning") and "sibling" in result["_warning"]:
    fresh_content = read_file(path)        # frischen Stand holen
    # Prüfen ob old_string noch im frischen Content existiert
    if old_string not in fresh_content:
        # WARNING: Sibling hat old_string bereits entfernt → Patch ungueltig
        # → neuen Stand analysieren, ggf. alternative old_string finden
        # oder den Patch komplett neu aufsetzen
    else:
        patch(path, old_string, new_string)  # 1× retry
    # bei 2× Fehlschlag: read erneut, dann ein letztes Mal retry
    # bei 3× Fehlschlag: im Final-Report als "Sibling-Konflikt nicht loesbar" dokumentieren
```

**Wichtige Nuance:** Der `_warning` sagt dir NICHT, ob der Patch fehlschlug — er sagt nur "dein read ist stale". Du MUSST re-read + re-patch. Einfach den selben Patch nochmal zu schicken (ohne re-read) funktioniert nicht, weil `patch` die Datei nach dem letzten bekannten Read-Stand vergleicht.

**Nicht verwechseln mit:** `success: false` im `patch`-Resultat. Das ist ein echter Patch-Fehler (old_string nicht gefunden o. ä.) — andere Behandlung.

**Verifikation:** Patch muss `success: true` liefern ODER der Inhalt muss nach erfolgreichem re-read + patch dem gewünschten Ergebnis entsprechen. Vor Final-Report das ganze File kurz nochmal lesen per `read_file`.

### Pattern 2: Additive Patches als Cluster-Disziplin

Wenn **mehrere Subagents parallel dieselbe Datei** patchen (typisch `MOC - Home.md`, Themen-MOCs):

| Regel | Warum |
|---|---|
| Jeder Subagent patcht eine **andere Sektion** | Vermeidet Race-Conditions auf String-Ebene |
| Reihenfolge egal | Patches sind kontextuell unabhängig wenn Sektionen disjunkt |
| Dokumentation | Welcher Subagent hat welche Sektion gepatcht? |

**Anti-Pattern:** Alle Subagents patchen die "Quick-Links"-Sektion gleichzeitig → Race Condition, "letzter gewinnt" → Quick-Links verschwinden.

**Best Practice:** Pro Cluster-Subagent **eigener Sektionen-Bereich** vorab definieren (siehe Template unten).

### Pattern 3: Anti-Halluzinations-Tripwire

**Problem:** Subagent soll Notes füllen, hat aber keinen Read-Zugriff auf Datenquellen (Repos, Configs, Logs).

**Lösung: Explizite Fallback-Regel im Briefing:**

> Wenn Datenquelle nicht lesbar → schreibe **"Status: ungeprüft (Quelle nicht zugreifbar am <Datum>)"** und lasse Felder leer oder TODO.

**Anti-Pattern:** Subagent erfindet plausible Tech-Details (Dependencies, Versionsnummern, Befehls-Flags) → Müll im Vault.

**Best Practice:**
- **Immer Read-Zugriff** auf Quelldaten gewähren wenn möglich
- Fallback-Regel **explizit im Briefing** nennen (nicht implizieren)
- Beispiel-Tripwire in `obsidian-subagent-briefing-template` Skill

**Date-Stamp Refinement (Phase 6, 2026-07-05):**

Erweitere Pattern 3 um die **"manuell erweitern" Date-Stamp-Konvention** für quantitative Daten in Vault-Notes:

> Wenn du Performance-Zahlen (tokens/s, Latenz ms, VRAM-Nutzung) **nicht aus Vault-Notes bestätigen kannst**:
> - Keine erfundenen Zahlen. Statt "~21.5 tok/s": `Je nach Modell (Stand YYYY-MM-DD, manuell erweitern).`
> - In der MOC-Quellen-Sektion: `**Mnemosyne-Recalls:** Keine Recalls zu konkreten [X]-Zahlen am [Datum]; manuell pflegen.`
>
> Warum besser als "Status: ungeprüft": Das genaue Datum + der manuelle Pfad gibt dem nächsten Agenten einen klaren Fix-Action-Plan.

**Proven (Phase 6, 2026-07-05):** 18 Notes (3 MOCs + 15 Satelliten) — 0 halluzinierte Performance-Zahlen.

### Pattern 4: Themen-MOC Hierarchie (3-stufig)

```
L1: MOC - Home (Root-Hub, einzige Entry-Point-Datei)
       ↓ verlinkt
L2: Themen-MOCs (~3–5, cluster-übergreifend, z. B. "Lernen", "Gaming", "System")
       ↓ verlinkt
L3: Folder-MOCs (08-cluster-spezifisch, je eine pro Julian-Ivanov-8-Folder)
```

**Vorteile:**
- Backlinks arbeiten auf 3 Ebenen (Dataview kann auf jeder filtern)
- Wiki-Crosslinks natürlich verteilt (kein Backlink-Stau in `MOC - Home`)
- Klare mentale Karte beim Dispensieren neuer Subagent-Clusters

**Anti-Pattern:** Alle Notes hängen direkt an `MOC - Home` → Home wird unleserlich.

### Pattern 5: Subagent-Spec-Disziplin (Kurzfassung)

Jeder Subagent-Briefing MUSS enthalten:

1. **File-Scope** — exakt welche Files lesen, welche schreiben (KEINE Überschneidung mit anderen Subagents)
2. **Anti-Pattern** — was NICHT tun
3. **Output-Format** — was am Ende reportet werden soll
4. **Anti-Halluzinations-Regel** (Pattern 3)
5. **Patch-Konflikt-Hinweis** (Pattern 1+2)
6. **Wiki-Link-Syntax** — `[[Dateiname]]` + URL-Encoding für Leerzeichen bei Suchpfaden

**Spec-Größe:** 600–1000 Wörter pro Subagent-Briefing (zu kurz = zu vage, zu lang = Subagent überfordert / langsamer).

**Briefing-Compression-Finding (Phase 6, 2026-07-05):** Die ursprüngliche Annahme war 800–1500 Wörter. In der Praxis zeigten kürzere Briefings (500–700 Wörter) GLEICHE oder BESSERE Qualität bei KÜRZERER Laufzeit:

| Cluster | Wörter | Laufzeit | Quality |
|---------|--------|----------|---------|
| Cluster 1 | ~1400 | 6 Min | ⚠️ 2/9 Notes fehlgeschlagen |
| Cluster 4 | ~550 | 4 Min | ✅ vollständig |

**Empfehlung:** Für Basti's Präferenz "genau, prüf nach" → 60-70% der ursprünglich angenommenen Briefing-Länge. Starte mit 600 Wörtern, erstelle bei komplexerem Scope selten mehr als 900.

→ Siehe auch `references/phase-6-results.md` für vollständige Metrik-Tabelle.

**Vollständiges Spec-Template:** siehe Skill `obsidian-subagent-briefing-template`.

### Pattern 6: Subagent-Improvisation-Permission

**Problem:** Das Briefing sagt "erstelle 2 neue Notes" — aber der Subagent erkennt, dass das zu Duplikation führt, weil die Inhalte besser in eine bestehende Note passen.

**Lösung:** Subagent DARF von der Spec abweichen, wenn die Abweichung strukturell BESSER ist als die Anweisung.

**Drei Bedingungen (alle MÜSSEN erfüllt sein):**
1. **Keine existierenden Daten werden zerstört** — bestehende Inhalte bleiben erhalten oder werden angereichert, nie gelöscht
2. **Task-Abdeckung wird nicht reduziert** — alle Informationen, die in den geplanten neuen Notes stehen sollten, landen trotzdem im Vault (nur in einer anderen Datei)
3. **Abweichung wird im Summary dokumentiert** — der Final-Report sagt explizit: "Spec sagte X, aber ich habe Y gemacht, weil Z"

**Konkretes Beispiel (Phase 4, 2026-07-05):**
- **Spec:** Erstelle `05 Ressourcen/Obsidian-Plugin-Status-Live.md` + `05 Ressourcen/Dataview-Install-Anleitung.md` (2 neue Notes)
- **Bessere Wahl:** Die bestehende `05 Ressourcen/Obsidian - Plugin-Setup.md` (2,8 KB) mit Install-Anleitungen + Live-Status anreichern (→ 7,6 KB)
- **Warum besser:** Keine Fragmentierung des Plugin-Wissens auf 3 Notes, weniger "Siehe auch"-Verweise, Nutzer findet alles an einem Ort
- **Siehe auch:** `references/subagent-improvisation-pattern.md` für vollständige Worked-Examples

**Anti-Pattern:** Subagent weicht ab, dokumentiert es NICHT im Summary → Königin fragt sich "warum hat er meine Anweisung ignoriert?" und muss die Änderungen selbst rekonstruieren.

**Signal für Improvisation:** Wenn der Subagent im "Read"-Schritt merkt, dass eine bestehende Datei perfekt den Ziel-Content aufnehmen kann, OHNE die existierende Struktur zu zerstören.

### Pattern 7: Sub-Agent-Claim-Verification (Königin-Pflicht)

**Problem:** Sub-Agents retournieren plausible Self-Reports ("0→123 Zeilen, 18 Links"), aber die behauptete Aktion wurde **nicht** ausgeführt. Das `write_file`-Tool meldet dem Sub-Agent `success`, aber die Datei existiert nicht auf Disk.

**Fundiert in Phase 6 (2026-07-05):** Cluster 1 (Sub-Agent A) reportete `05 Ressourcen/MOC - Daily Notes.md` mit 123 Zeilen und 18 Links erstellt zu haben — die Datei EXISTIERTE NICHT. Yuno (Königin) hat die Lücke während der Verifikation entdeckt und die Datei inline nachgebaut.

**Lösung — Nach jedem Sub-Agent-Batch:**

```python
# Queen Verification — NIEMALS überspringen
for subagent_claim in all_subagent_results:
    for path, claimed_stats in subagent_claims.file_creations.items():
        # Prüfen: Existiert die Datei wirklich?
        result = terminal(f"stat --format=%s {path}")
        if result.exit_code != 0:
            # Datei existiert nicht trotz Behauptung!
            log_warning(f"Sub-Agent behauptete {path} erstellt, existiert nicht")
            # → INLINE REPARIEREN: Königin erstellt die Datei selbst
            write_file(path, generate_minimal_content(subagent_claim))
        elif int(result.output) < 100:
            log_warning(f"Sub-Agent behauptete {path} mit 100+ Zeilen, Datei hat {result.output} Bytes")
    for path in subagent_claims.modifications:
        # Auch bei Patches: Stichprobe
        content = read_file(path)
        if subagent_claim.key_pattern not in content.content:
            log_warning(f"Sub-Agent behauptete Patch in {path}, key_pattern nicht gefunden")
```

**Drei Verifikations-Modi:**

| Modus | Wann | Befehl |
|-------|------|--------|
| **Exists** | write_file-Claim auf neuer Datei | `terminal("stat --format=%s <path>")` |
| **Size** | Zero-Content → befüllt | `wc -l <path>` + Inhalt stichprobenartig lesen |
| **Content** | Patch behauptet | `grep <expected_string> <path>` oder `read_file` |

**Wichtige Nuance:** Sub-Agents können `write_file` aufrufen und ein `success: true` bekommen — die Datei landet trotzdem nicht auf Disk. Das ist KEIN Sub-Agent-Bug, sondern ein bekanntes Hermes-Verhalten bei bestimmten Timing-/Cache-Bedingungen. Die Königin MUSS trotzdem verifizieren.

### Pattern 8: Leaf-Agent kann kein Mnemosyne (Queen-Hook-Pflicht)

**Problem:** `mnemosyne_remember` ist für leaf-role gesperrt. Wenn ein Sub-Agent einen Mnemosyne-Hook setzen soll, schlägt das fehl — der Hook wird nie gesetzt und die Session ist nach Modellwechsel ohne Memory-Anker.

**Lösung:** Sub-Agent gibt Hook als JSON-Struct im self-report aus. Die Königin setzt alle Hooks **inline** nach Batch-Completion.

```
```Sub-Agent Output:
  === Summary ===
  ...
  Mnemosyne-Hook-JSON: { "cluster": "4", "task": "Glossar", ... }

Königin Aktion:
  read_file("/home/bratan/.hermes/state/<cluster>-hooks.json")
  → Inhalt in mnemosyne_remember übernehmen
  → Hook setzen (importance, veracity, source, entities)
```

### Pattern 9: External-LLM-CLI als Worker-Tool für Vault-Arbeit

**Problem:** Vault-Expansion braucht Reasoning (Cross-Link-Vernetzung, Glossar-Enrichment, Themen-Lücken-Erkennung). Der Subagent (MiniMax-M3) hat zwar genug Kontext, aber sein Reasoning ist flacher als Gemini-Pro oder Claude-Sonnet. Gleichzeitig per Hand zu dispatchen ist aufwändig.

**Lösung — External-LLM-CLI als Worker-Tool in der Biene:**

```python
# Worker-Biene (MiniMax-M3) → ruft external CLI auf → backend LLM macht die Arbeit
delegate_task(
    goal="Vault-Strukturierung mit Gemini 3.1 Pro Preview",
    context="""
    Worker-Biene, deine Aufgabe:
    1. Lese den Plan-File (Vault-Phase-N-Plan.md), der Scope + Anti-Patterns enthält
    2. Führe aus: timeout 480 gemini -m gemini-3.1-pro-preview -p "$(cat <plan-file>)"
    3. Konvertiere das Briefing + den Plan in einen Prompt für Gemini
    4. Sammle das Gemini-Resultat ein
    5. Verifiziere Claims (Pattern 7): stat + read_file für jede behauptete Änderung
    6. Gib strukturierten Report zurück
    """,
    role="leaf"
)
```

**Architektur (3 Ebenen):**
```
Yuno (Queen, MiniMax-M3)
   │  plant, routet, konsolidiert, verifiziert Pattern 7
   ▼
Subagent Worker (MiniMax-M3 — die "Worker-Biene")
   │  isoliertes Terminal + Toolset, liest Plan, ruft CLI auf
   ▼
External LLM CLI (gemini -p / claude -p / codex exec — das Werkzeug)
   │  wird als Shell-Command vom Subagent aufgerufen
   ▼
Backend LLM (Gemini-3.1-Pro, Claude-Sonnet-5, GPT-5 — das eigentliche Brain)
   │  analysiert Vault, entscheidet was zu tun ist
```

**Vorteile dieser 3-Ebenen-Orchestrierung:**
| Ebene | Kostet Subagent-Tokens | Reasoning-Stärke | Timeout-Risiko |
|---|---|---|---|
| Queen (Yuno) | ✅ Ja (Planen, Verifikation) | MiniMax-M3 | Niedrig |
| Worker-Biene (Subagent) | ✅ Ja (Briefing, Koordination) | MiniMax-M3 | Mittel |
| Gemini/Claude (Tool) | ❌ Nein (Subagent-Tokens only für Dispatch) | Stark (1M Context) | Hoch |

**Goldene Regel:** Die Worker-Biene kostet Subagent-Tokens (MiniMax-M3). Das External-LLM-Kontingent (Gemini Pro Abo, Claude API) **läuft separat** — wird nicht im Hermes-Token-Budget verbucht. Tradeoff: Du verbrauchst Subagent-Tokens für den Dispatch, gewinnst aber besseres Reasoning.

**Vault-spezifische Vorteile:**
- Gemini 3.1 Pro Preview hat 1M Context → kann GANZEN Vault auf einmal "sehen"
- Bessere Cross-Link-Vernetzung als MiniMax (erkennt thematische Verwandtschaft zwischen Notes in verschiedenen Ordnern)
- Halluzinations-Risiko: External LLM sieht den `_warning`-Mechanismus von `patch` nicht → Queen MUSS Pattern 7-Verifikation machen

**Praktisches Beispiel (2026-07-05, Vault-Phase-7-Gemini-Audit):**
1. Queen erstellt Plan-File `05 Ressourcen/Vault-Phase-7-Plan - Gemini-Audit.md` (Scope, Anti-Patterns, File-Scopes)
2. Queen dispatcht Worker-Biene: "lies Plan, timeout 480 gemini -m gemini-3.1-pro-preview -p \"$plan\""
3. Worker-Biene startet Gemini-CLI — Gemini bekommt Plan + Vault-Inhalt als Prompt
4. Gemini macht Patches (Verbindet-zu Sektionen) + erstellt ggf. Satelliten-Notes
5. Worker-Biene sammelt Output, verifiziert Claims via `stat`, gibt Report zurück
6. Queen prüft Report, macht eigene Stichproben, reportet an Basti

**Siehe auch:** `coding-agents` Skill → `references/gemini-cli.md` für CLI-spezifische Auth-Pitfalls (URL-Mangling, Code-Assist-Deprecation, Fallback-Chain).

### Pattern 9b: Direct Queen→CLI Invocation (2-Tier-Variante)

**Problem:** Der 3-Tier-Ansatz (Queen → Subagent → CLI) braucht Subagent-Tokens für den Dispatch und dauert länger. Für einen schnellen, einmaligen Durchlauf ist das Overkill.

**Lösung — Direktdispatching durch die Königin:**

```python
# Variante B — Königin ruft CLI direkt auf, kein Subagent dazwischen
# Vorteil: weniger Token-Verbrauch, schneller
# Nachteil: Königin ist während des CLI-Laufs teils blockiert (polling)

# 0. Pre-Flight: Plan erstellen + Vault-Inventur
write_file(path="Vault-Phase-N-Plan.md", content=plan_content)
pre_file = "/tmp/gemini-pre-snapshot.txt"
terminal(f"find '{vault}' -name '*.md' -not -path '*/.obsidian/*' -not -path '*/.trash/*' | sort > {pre_file}")
pre_count = terminal(f"wc -l < {pre_file}").output.strip()

# 1. CLI im Hintergrund starten
result = terminal(
    command=f"timeout 600 gemini --yolo -m gemini-3.1-pro-preview -p \"$(cat '{plan_file}')\" > /tmp/run.log 2>&1",
    background=True,
    notify_on_complete=True
)

# 2. Auf Fertigstellung warten (oder mit process.poll() parallel arbeiten)
process(action="wait", session_id=result.session_id, timeout=600)

# 3. CLI-Output auswerten
log_content = terminal("cat /tmp/run.log")
if "EXIT=0" in log_content.exit_code:
    # Erfolg — strukturierten Bericht aus dem CLI-Output parsen
    pass

# 4. Verifikation (9-Schritt-Protokoll — siehe references/external-llm-verification.md)
```

**Wann Variante A (Subagent-vermittelt) vs. Variante B (Direkt):**

| Kriterium | A: 3-Tier (Subagent → CLI) | B: 2-Tier (Queen → CLI) |
|---|---|---|
| Token-Kosten | Subagent-Dispatch + Queen-Verifikation | Nur Queen-Tokens für Terminal-Call |
| Parallel-Arbeit | Queen kann während CLI-Lauf andere Tasks machen | Queen ist im Polling-Zyklus blockiert |
| Komplexität | Höher (Briefing, Verifikations-Chain) | Niedriger (ein Terminal-Call) |
| Fehler-Isolation | Subagent fängt CLI-Fehler ab | CLI-Fehler landen direkt bei Königin |
| Wann wählen | ≥2 CLI-Durchläufe parallel, oder User wünscht "gründlich" | 1 Durchlauf, schnell |

**Erfahrung (Phase 7, 2026-07-05):** Direkt-Invocation mit `background=true` + `process.wait()` (180s-Clamped durch Hermes), Gemini lief sauber durch (exit 0). Die Log-Redirection `> /tmp/run.log 2>&1` erzeugte leere stdout-Capture im Process-Stream (nur IOCTL-Warning), aber die Log-Datei enthielt den kompletten CLI-Output. Verifikation erfolgte via mtime-Diff-Pattern statt via Subagent-Claims.

### Pattern 9c: Duplicate-Drift bei External-LLM-CLI

**Problem:** Ein External-LLM mit `--yolo`-Schreibzugriff erstellt eine neue Datei mit einem **minimal abweichenden Dateinamen** statt die existierende Note zu patchen.

**Symptom:** Nach CLI-Run existieren zwei Notes mit fast identischem Inhalt:

```
05 Ressourcen/Obsidian-Plugins-Setup.md      (neu, 10 KB, Bindestrich-Variante)
05 Ressourcen/Obsidian - Plugin-Setup.md      (alt, 8 KB, Spatium-Variante)
```

**Warum das passiert:** External LLM bekommt das Verbot "keine Notes umbenennen" → es darf die Alt-Note nicht umbenennen. Stattdessen **erstellt** es eine neue Datei mit dem korrigierten Namen als Satelliten. Die neue Datei linkt sogar zurück: `[[Obsidian - Plugin-Setup]] (alt)`. Der CLI-Output sagt "Header-Rename + Links verifiziert" — wirkt harmlos, aber faktisch entsteht ein Duplikat.

**Warum gefährlich:** Doppelte Wartung, unklare Authoritative-Source, Graph-Blähung.

**Erkennung (Post-Run-Check in Verifikation):**

```bash
# 1. Neue Dateien aus Pre/Post-Diff identifizieren
# 2. Für JEDE neue Datei: Prüfen ob bestehende Datei mit ähnlichem Namen existiert
#    (Wortstamm-Vergleich, Trennzeichen-Varianten)
# 3. Wenn Near-Duplikat gefunden: Inhalt-Vergleich
diff <(head -30 "alt.md" | grep -v '^---$' | grep -v '^tags:' | grep -v '^quelle:') \
     <(head -30 "neu.md" | grep -v '^---$' | grep -v '^tags:' | grep -v '^quelle:')
# 4. Bei >60% Overlap in head-30: Duplikat im Report markieren
```

**Mitigation (im External-LLM-Briefing):**

> **Anti-Pattern: Keine Dual-Citizenship.** Wenn eine Datei existiert (egal ob Bindestrich, Spatium, CamelCase oder underscore), dann:
> - **Verbessere** (patch) die existierende Datei
> - **Erstelle KEINE** neue Datei mit abweichendem Dateinamen
> - Ausnahme: Dateiname ist so falsch, dass er Suchbarkeit massiv einschränkt → im Report markieren, Königin entscheidet

**Behandlung:** Duplikat löschen (`rm ...`) ODER Content in Alt-Note mergen + Duplikat löschen.

**Fundiert in Phase 7 (2026-07-05):** Gemini 3.1 Pro Preview erstellte `Obsidian-Plugins-Setup.md` (neu) parallel zu `Obsidian - Plugin-Setup.md` (alt). Erkannt durch Post-Run mtime-Check + filename-similarity scan. Kein Vollrollback nötig — Königin löscht das Duplikat.

## Workflow: Vault-Cluster-Run (5 Phasen)

### Pattern 10: Cross-Reference-Matrix für N verwandte Notes

**Problem:** N thematisch verwandte Notes existieren nebeneinander ohne gegenseitige Wiki-Links. Manuelles Cross-Linken ist aufwändig und fehleranfällig. Ein einfacher Backlink-Roundtrip (Phase D) findet keine Lücken, weil die Notes noch gar nicht aufeinander zeigen.

**Lösung — Systematischer 5-Phasen-Audit:**

```
Königin          Phase 1: Locate + Extract (find + grep -oE '\[\[...\]\]')
Königin          Phase 2: Matrix bauen (N×(N-1) Paare, EXISTS/BROKEN/MISSING)
Königin          Phase 3: Action-Liste schreiben → /tmp/vault-patch-gamma/<ts>.md
Sub-Bee (leaf)   Phase 4: Patches ausführen → /tmp/vault-patch-gamma/<ts>-sub.json
Königin          Phase 5: Unabhängige Verifikation (grep EVERY link, nicht auf Self-Report vertrauen)
```

**Broken-Link-Erkennung (kritisch):** Obsidian-Wiki-Links mit Spaces (`[[GreyHack - Audit 2026-07-14]]`) resolven NICHT zu Dateien mit Minus-Bindestrichen (`GreyHack-Audit-2026-07-14.md`). Die Matrix muss Broken-Links als MISSING markieren. Der Patch muss ersetzen statt duplizieren. Typisches Broken-Link-Muster: Subagent erstellt Link mit human-readable Spaces, aber die Datei hat Maschinen-Bindestriche.

**Anti-Halluzinations-Regel (Phase 5 ist PFLICHT):** Sub-Bees reporten `38/38 success`, aber Section-Boundary-Bugs können Links in falschen Abschnitten platzieren (z.B. vor `###`-Subheadern statt am Ende der `##`-Sektion). Nur ein unabhängiger Grep-Check deckt das auf. Erster Patcher-Lauf hatte diesen Bug → nach Re-Run behoben.

**Self-Report-Pflicht f. Sub-Bee:** `patches_executed = N`, `skipped_duplicates = M`, `json_valid = True/False`

→ Vollständige Details + Worked Example in `references/cross-reference-matrix-pattern.md`

### Phase A — Spec-Splitting (Königin)

**Pre-Flight: Pattern 0a ausführen** — jeden Pfad aus dem Plan gegen das echte Filesystem prüfen. Das ist KEIN optionaler Schritt — ohne diesen Check schreiben Subagents ins Leere.

```python
# PHASE 0: PRE-FLIGHT PLAN-REALITY CHECK (NEU — IMMER AUSFÜHREN)
# 1. Vault-Inventur (Phase 0)
search_files(pattern="*.md", path="<vault>/03 Projekte")
search_files(pattern="*.md", path="<vault>/05 Ressourcen")

# 2. JEDEN Pfad aus dem Plan validieren
#    - Existiert die Datei an genau diesem Pfad?
#    - Wenn nein: search_files nach dem Dateinamen → Alternative finden
#    - Wenn gar nicht: dokumentieren, Subagent-Briefing anpassen
# Siehe Pattern 0a + references/plan-reality-verification.md

# 3. Zero-Content-Dateien identifizieren
#    wc -l <path> + stat --format=%s <path>
#    Nur wenn BEIDE 0 ergeben: write_file
#    Sonst: patch (auch wenn der Plan "empty" sagt)

# 4. Cluster-Specs entwerfen (Pattern 5)
#    pro Subagent: file_scope, anti_pattern, output_format

# 5. File-Scope-Conflict-Table erstellen
# (welcher Subagent darf welche Files anfassen — NIE überlappend!)
```

### Phase B — Fan-Out (parallel ODER gestaffelt)

**Standard:** Subagents parallel feuern (schnellster Durchsatz).
**Bei 4+ Clustern oder User-Wunsch "staffeln":** Subagents in Wellen feuern.

```python
# PARALLEL (Default für ≤3 Cluster):
# Beispiel: 3 Subagents parallel für 3 Folder
results = delegate_task(tasks=[
    subagent_spec_projects,
    subagent_spec_ressourcen,
    subagent_spec_bereiche,
])
# WICHTIG: keine Fixer parallel zu Scouts im selben Batch
# (siehe delegation-anti-patterns Skill Pattern 1)

# GESTAFFELT (Staffel-Variante für ≥4 Cluster):
# Welle 1: kritischen Cluster zuerst (Zero/Thin-Fix, Basisarbeit)
delegate_task(task=cluster_1)   # läuft im Background
# warte auf Resultat (kommt als Message zurück)
# Welle 2: restliche Cluster parallel (skalierbare Arbeit)
delegate_task(tasks=[cluster_2, cluster_3, cluster_4, cluster_5])
# Welle 3: Königin inline (Strategie, Summary, Cleanup)
# → Cluster 6 inline nach allen Subagents
```

**Regeln für Staffel-Entscheidung:**

| Kriterium | Parallel | Gestaffelt |
|-----------|----------|------------|
| Cluster-Anzahl | ≤3 | ≥4 |
| Cluster-Typen | homogeneous | mixed (zero + expansion + polish) |
| User-Präferenz | "mach schnell" | "sei genau, prüf nach" |
| Rollback-Risiko | niedrig | mittel-hoch (mehr Files touched) |
| File-Scope-Konflikte | gering (gut partitioniert) | möglich (viele parallele Patches) |

**Erfahrungswert (Phase 6, 2026-07-05):**
- 5 Cluster → User wählte "staffeln"
- Cluster 1 (Zero/Thin-Fix, sequenziell) → Clusters 2-5 parallel → Cluster 6 inline
- Ergebnis: überschaubare Queue, Königin konnte nach jeder Welle eingreifen
- Siehe `references/staggered-vault-deployment.md` für vollständiges Worked Example

### Phase C — Konsolidierung (Königin)

```python
# Nach allen Subagents zurück:
# 1. Per-Cluster-States sammeln
# 2. WICHTIG: Sub-Agent-Claims verifizieren (Pattern 7)
#    Für JEDE behauptete Datei-Erstellung: stat --format=%s <path>
#    Wenn nicht existent → Königin erstellt inline
# 3. Wiki-Link-Spread prüfen (Pattern 6 → obsidian-vault-quality-audit)
# 4. Verwaiste Notes prüfen (Pattern 7 → obsidian-vault-quality-audit)
# 5. Konflikte dokumentieren (welche Files, wie gelöst)
# 6. QUEEN setzt ALLE Mnemosyne-Hooks (Pattern 8):
#    - Sub-Agent hat Hook-JSON im self-report geliefert
#    - Königin: mnemosyne_remember(source="vault-<phase>", ...)
#    - Leaf-Agent kann mnemosyne_remember NICHT selbst aufrufen
```

### Phase D — Backlink-Roundtrip (Pattern 6)

```dataview
LIST FROM "<neuer-note-name>"
WHERE contains(this.file.outlinks, this.file.name)
```

**Wenn 0 Backlinks:** Sackgassen-Detection → Wiki-Link-Spread nötig.

### Phase E — Reporting an Basti

1. Inventur: Notes, Wiki-Links, Avg-Link/Note
2. Per-Cluster-Stats
3. Konflikte dokumentiert + Lösungen
4. Lessons extrahiert
5. Telegram-Bericht (falls nötig)

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Alle Subagents patchen `MOC - Home.md` Quick-Links → Race-Condition | File-Scope disjunkt definieren (Pattern 2) |
| 2 | Subagent erfindet Tech-Details statt "Status: ungeprüft" zu schreiben | Anti-Halluzinations-Tripwire explizit im Briefing (Pattern 3) |
| 3 | Cluster scheitert ohne sichtbares Symptom weil Subagents isolated returnen | Königin MUSS selbst Phase-0-Inventur + Phase-C-Verifikation machen |
| 4 | Wiki-Link-Encoding vergessen (`[[Mein Note.md]]` statt `[[Mein%20Note.md]]`) → Dataview findet nichts | Briefing muss URL-Encoding-Syntax vorgeben |
| 5 | Subagent-Briefing zu kurz (<400 Wörter) → Subagent macht was er will | Briefing-Gerüst 600–1000 Wörter (Pattern 5, Compression-Finding beachten) |
| 6 | Fixer parallel zu Scouts (Context-Isolation) | Nie im selben Batch (delegation-anti-patterns #1) |
| 7 | 5+ Cluster ungestaffelt feuern → Patch-Konflikte, Überlast, schweres Rollback | Staffel-Entscheidung vor Fan-Out treffen (siehe Phase B Regeltabelle) |
| 8 | Plan-Inventar stimmt nicht mit Filesystem überein (Stale-Pfade) → Subagent schreibt ins Leere | Pattern 0a: Pre-Flight Check vor Fan-Out — jeden Pfad der Spec gegen das echte Filesystem prüfen |
| 9 | Zero-Content-Datei (0 Bytes, existiert) wird fälschlich als "nicht vorhanden" behandelt → write_file statt patch → Inhalt der vorherigen Session verloren | Vor write_file auf existierenden Files IMMER `terminal("wc -l <path>")` UND `terminal("stat --format=%s <path>")` ausführen — erst wenn beides 0 ergibt, ist write_file safe |
| 10 | `_warning`-Feld im patch-Resultat wird ignoriert (Sibling-Konflikt nicht erkannt) → naechster Patch auf veraltetem Stand → silent corruption | Pattern 1: IMMER auf `_warning`-Key prüfen, re-read + re-patch ausführen |
| 11 | Sub-Agent behauptet write_file-Erfolg auf neuer Datei, aber Datei existiert nicht → Lücke im Vault | Pattern 7: Nach Batch jede behauptete Datei mit `terminal("stat --format=%s")` prüfen. Bei Fehlen: Königin erstellt inline. *Fundiert in Phase-6, Cluster 1: MOC-Daily-Notes.md behauptet aber nicht existent.* |
| 12 | Leaf-Agent kann `mnemosyne_remember` nicht aufrufen → Mnemosyne-Hook fehlt → memory loss beim nächsten Modellwechsel | Pattern 8: Sub-Agent gibt Hook als JSON-Struct aus, Königin setzt alle Hooks inline nach Batch-Completion. *Fundiert in Phase-6, Cluster 4: Hook-JSON abgelegt, Königin musste nachsetzen.* |
| 13 | External-LLM-CLI (Gemini/Claude/Codex) erstellt neue Datei mit abweichendem Dateinamen statt existierende Note zu patchen → Duplikat-Drift | Pattern 9c: Post-Run filename-similarity scan aller neuen Files. Wenn Near-Duplikat → Königin löscht oder merged. *Fundiert in Phase 7 (2026-07-05): `Obsidian-Plugins-Setup.md` vs `Obsidian - Plugin-Setup.md`.* |

## Connecting Skills

- **`obsidian`** — Low-Level File-Ops (read/search/patch/write)
- **`vault-architecture`** — 8-Folder-Schema, MOC-Pattern (Design-Schicht)
- **`obsidian-subagent-briefing-template`** — Spec-Blueprint für jeden Subagent
- **`obsidian-vault-quality-audit`** — Pattern 6+7 (Backlinks, Verwaiste Notes)
- **`multi-agent-cluster-patterns`** — Pattern 1–8 als Multi-Agent-Grundlage
- **`delegation-anti-patterns`** — Hermes-spezifische Pitfalls (Scout+Fixer-Isolation, FP-Flood)
- **`coding-agents`** — External-LLM-CLIs (Gemini, Claude, Codex) als Worker-Tools für Vault-Arbeit mit Deep-Reasoning (Pattern 9)
- **`gemini-vault-worker`** — Gemini-CLI-spezifische G-Patterns 1-5 (Auth Check, --yolo, Müll-Prävention, Telemetrie, Model-Override), Backup-Strategie, Anti-Pattern-Checkliste, gemini-3.1-pro-preview als Default (User-Präferenz). Add-On Skill für Gemini als External-LLM.

## Reference Files

| Datei | Inhalt |
|-------|--------|
| `references/staggered-vault-deployment.md` | Staffel-Plan Worked Example (Phase 6) |
| `references/plan-reality-verification.md` | Pre-Flight Check Worked Example |
| `references/subagent-improvisation-pattern.md` | Subagent-Improvisation Permission Beispiel |
| `references/obsidian-flatpak-setup.md` | Flatpak-Obsidian-Pfad-Konvention, Theme+Snippet+Plugin-Pfade |
| `references/phase-6-results.md` | Phase-6-Gesamtmetriken (109 Notes) + Briefing-Compression-Finding |
| `references/obsidian-sanctum-theming.md` | Sanctum-CSS-Theming: `app.json igneredCssClasses` via `no-sanctum-icons`, Multi-Level-Folder-Farben (8 Top-Level + Sub + Tree-Indent), Defense-in-Depth, Visual-Fix-Feedback-Loop |
| `references/external-llm-verification.md` | 9-Schritt-Verifikationsprotokoll für External-LLM-CLI-Läufe (Phase 7 Worked Example) |
| `references/cross-reference-matrix-pattern.md` | Pattern 10: Cross-Reference-Matrix für N Notes — Broken-Link-Erkennung, Sub-Bee-Dispatch, 5-Phasen-Audit, Worked Example (7 GreyHack-Notes, 2026-07-14) |

## Source

- Vault: `Skill-Ableitung - Vault-Phase-2-3.md` (05 Ressourcen, 2026-07-05)
- Patterns 1–5 dokumentiert aus Phase-2 + Phase-3-Erfahrungen
- Pattern 6 dokumentiert aus Phase-4 (Subagent K, deleg_f40ae395)
