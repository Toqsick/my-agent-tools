# Parallel Hive Triage (Fable Schwarm Pattern)

> Pattern: Mehrere Claude-Haiku/Haiku-Instanzen parallel für Triage/Analyse/Inventur als bash background processes.
> Discovered: 2026-07-05 (GitHub Hygiene Masterplan)
> Extended: 2026-07-05 (Fable + Subagent Cross-Check, Output-Verifikation)

## Wann verwenden

- Du hast 2-5 unabhängige Analyse-Tasks (verschiedene Repos, verschiedene Fragestellungen)
- Die Tasks brauchen KEINE Interaktion untereinander (pure parallele Ausführung)
- Der Output jedes Tasks überschreitet nicht ~5k Tokens (sonst wird der Background-Output schwer lesbar)
- Budget-Optimierung: Haiku/Haiku 4.5 ist günstig genug für 3-5 Parallel-Calls gleichzeitig

## Pattern

### 1. Briefings schreiben

Jeder Task bekommt sein eigenes Briefing-File (vollständig embedded — Claude Code hat keinen Skill-Zugriff):

```bash
mkdir -p /tmp/fable-out
cat > /tmp/fable/task-1.md << 'EOF'
# Task-Briefing: Repo-X Triage

Goal: Analysiere Repo-X auf Hygiene-Status.
Context: [embed ALLE relevanten skill_view() Outputs + Dateien hier]
Output: Strukturierte Markdown-Liste
EOF
```

**Briefing-Template:** Briefings immer strukturiert mit Goal/Context/Output-Format — Claude Code braucht klare Erwartungen.

### 2. Alle Tasks per Bash-Batch starten

```bash
bash -c '
cd /home/bratan/docs/system/<arbeits-ordner>/

claude -p "$(cat task-1.md)" \
  --model claude-haiku-4-5 \
  --max-turns 10 \
  --max-budget-usd 0.50 \
  > /tmp/fable-out/fable-1.txt 2>&1
echo "✅ #1 fertig: $(date)" >> /tmp/fable-out/progress.log

claude -p "$(cat task-2.md)" \
  --model claude-haiku-4-5 \
  --max-turns 10 \
  > /tmp/fable-out/fable-2.txt 2>&1
echo "✅ #2 fertig: $(date)" >> /tmp/fable-out/progress.log

touch /tmp/fable-out/ALL-DONE
'
```

Wichtig: in `terminal(background=true, notify_on_complete=true)` ausführen.

### 3. Output überwachen und VERIFIZIEREN (wichtig!)

```bash
# Während die laufen:
cat /tmp/fable-out/progress.log 2>/dev/null
ls -la /tmp/fable-out/

# Nach Fertigstellung: Output-Größe prüfen!
wc -c /tmp/fable-out/fable-*.txt
# → Outputs unter ~500 Bytes sind ALARM-Signale:
#   - "Not logged in" (OAuth-Probleme)
#   - "Reached max turns" (Turns zu niedrig)
#   - Output abgeschnitten (Budget-Cap bei Pro/OAuth)

# Bei verdächtig kleinen Outputs:
cat /tmp/fable-out/fable-X.txt | head -20
# → Zeigt sofort die Fehlermeldung
```

### 4. Optionale Erweiterung: Side-by-Side mit Subagenten

Für höhere Verlässlichkeit bei kritischen Analyse-Tasks (in dieser Session erfolgreich eingesetzt):

**Cross-Check-Prinzip:**
- **Fable Schwarm** (Claude CLI) = schnelle Triage, großzügig mit Turns (8-10)
- **delegate_task Subagenten** (Hermes intern) = detaillierte Read-only-Analyse
- **Synthese + Cross-Check:** Beide Ergebnisse vergleichen
- **Konsens = vertrauenswürdig**, Diskrepanz = nachfragen
- **Ergebnis dieser Session:** 3 Fable-Calls + 2 Subagenten → 100% Konsens bei allen Findings

**Parallel starten (beide unabhängig):**
```python
# Fable Schwarm (background processes)
terminal(command="bash -c '...'", background=True, notify_on_complete=True)

# Subagenten (delegate_task)
delegate_task(tasks=[
    {"goal": "Read-only Analyse Repo A"},
    {"goal": "Read-only Analyse Repo B"}
])

# Während beide laufen: andere Arbeit machen
# Dann: Fable-Outputs + Subagenten-Deliverables einsammeln →
# Synthese + Cross-Check
```

## Critical Configuration

### `--max-turns` — DER kritischste Parameter

| Task-Typ | Turns | Grund |
|----------|-------|-------|
| Mini-Triage (<5 Files) | 5-8 | Schnell, günstig |
| Analyse (Repo-Level) | 10-15 | Genug für Lesen + Urteilen |
| Big-Inventur (Multi-Repo) | 20+ | Verschiedene Quellen einsammeln |

**KRITISCH (aus dieser Session):** Turns zu niedrig = Output abgeschnitten.
Fable #1+#2 brachen bei `--max-turns 5` ab ("Reached max turns"), während #3 mit 5 Turns durchkam.
**Starte immer mit 8+ für Analyse-Tasks.** Lieber 1-2 Turns extra als Output verlieren.

**Strike-Logik:** Nach einem Abbruch neu starten mit +5 Turns.
Der erste Lauf hat Kontext aufgebaut — der zweite hat mehr Spielraum.

### `--max-budget-usd` — NICHT für Analyse/Triage

Bei **Pro/OAuth** (nicht API-Key) gilt:
- Budget-Cap killt Output mitten in der Analyse (Session-Budget ≠ Token-Billing)
- Analyse/Read-only = Budget **weglassen**
- Nur für Coding-Sprints setzen (klar definierter Output, z.B. Refactor)
- Siehe `coding-agents/references/claude-pro-plan-budget.md` für Details

### `--bare` vermeiden (bei Pro/OAuth)

`--bare` skippt OAuth-Keychain → "Not logged in" Fehler.

**Symptom:** Output-File winzig (z.B. 28 Bytes, 747 Bytes) mit Inhalt `"Not logged in · Please run /login"`.
**Fix:** `--bare` weglassen — dann nutzt Claude den bestehenden OAuth-Keychain-Eintrag (`claude auth status`).

Nur verwenden wenn `ANTHROPIC_API_KEY` gesetzt ist (CI/CD-Kontext).

### Model-Auswahl

| Model | Flag | Kosten | Best für | Turns |
|-------|------|--------|----------|-------|
| Haiku 4.5 | `--model claude-haiku-4-5` | ♨️ günstig | Triage, Inventur, Mini-Analyse | 8-10 |
| Sonnet 5 / Fable 5 | `--model sonnet-5-20260622` | 💰💰 höher | Big-Inventur, Deep-Analyse, Coding | 10-20 |

**Hinweis:** Display-Name im UI (`claude -m` zeigt "Fable 5") ≠ CLI-Flag (`--model sonnet-5-20260622`).

### Start-Parameter-Matrix

| Task-Mix | Modell | Turns | Budget-Cap | Parallelität |
|----------|--------|-------|------------|--------------|
| 3x Mini-Triage (Code-Qualität) | Haiku 4.5 | 8 | Keiner | 3 gleichzeitig |
| 2x Analyse + 1x Deep-Review | Sonnet 5 | 15 | Keiner (Analyse) / $0.50 (Review) | 3 gleichzeitig |
| 1x Big-Inventur (Multi-Repo) | Sonnet 5 | 20-30 | $1.00 | Single (mehr Turns nötig) |

## Output-Verifikation

### Normale Output-Größen

| Task-Typ | Typische Größe | Anmerkung |
|----------|---------------|-----------|
| Mini-Triage (1-2 Repos) | 2-5 KB | Klare Empfehlungen |
| Analyse (Repo-Level) | 5-15 KB | Detaillierte Liste |
| Big-Inventur (Multi-Repo) | 15-50 KB | Verschiedene Findings |
| Fehlerfall (OAuth) | < 100 Bytes | "Not logged in" |
| Fehlerfall (zu wenig Turns) | < 500 Bytes | "Reached max turns" |
| Budget-Cap-Kill | < 1 KB | Output abgeschnitten |

### Schnell-Check-Script

```bash
for f in /tmp/fable-out/fable-*.txt; do
    [ ! -f "$f" ] && continue
    size=$(wc -c < "$f")
    echo "$f: $size Bytes"
    if [ "$size" -lt 500 ]; then
        echo "  ⚠️  Output ungewöhnlich klein — Fehler prüfen:"
        head -5 "$f"
    fi
done
```

### Exit-Code vs Output (wichtige Diskrepanz)

**Der Background-Process kann exit 0 melden, obwohl alle Claude-Instanzen fehlgeschlagen sind!**

In dieser Session: Fable-Schwarm meldete `exit 0`, aber alle 3 Outputs waren < 1 KB mit "Not logged in" oder "Reached max turns". Der `bash -c` Wrapper hatte keine Fehler (Claude CLI ist sauber exited), aber die Ergebnisse waren unbrauchbar.

**Faustregel:** Output-Größe ist der primäre Indikator. Exit-Code kann irreführen.

## Troubleshooting

| Symptom | Ursache | Fix |
|---------|---------|-----|
| Output 28 Bytes: "Not logged in" | `--bare` unter Pro/OAuth | `--bare` weglassen |
| Output 200 Bytes: "Reached max turns" | `--max-turns` zu niedrig | Neu starten mit +5 Turns |
| Output 800 Bytes, mittendrin abgeschnitten | Budget-Cap zu niedrig | Budget weglassen (Analyse) / erhöhen (Coding) |
| Output 0 Bytes (leer) | Prozess nie gestartet | `bash -c` validity prüfen |
| Output existiert, exit 0 | Claude hat nichts ausgegeben | Progress-Logs + wc -c prüfen |

## Referenzen

- **`coding-agents` Umbrella-Skill** — Cross-Agent Pitfalls (Budget-Strategie je Auth-Methode)
- `coding-agents/references/claude-pro-plan-budget.md` — Budget-Details für Pro/OAuth
- `coding-agents/references/claude-code.md` — Vollständige Flag-Referenz
- `orchestration/multi-agent-orchestration` — Multi-Agent-Orchestrierungs-Patterns
