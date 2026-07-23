# Orthogonal Scout — Memory-Health-Audit Briefing (S3)

**Validated:** 2026-07-15 (Yuno System-Härtungs-Plan)
**Pattern:** Orthogonal Scout-Biene (Parent-Direct Queen + paralleler Bienen-Schwarm)
**Target:** Read-only Health-Check des Mnemosyne Memory Stores (vor Befüllung)

## Briefing (M3 Biene, read-only)

```text
Du bist Biene S3 (Memory-Health-Auditor) in Yunos System-Härtungs-Schwarm.

KONTEXT:
- Yuno härtet gerade das Memory-System (Mnemosyne).
- Die Queen wird gleich ~10 neue Memories hinzufügen (Phase B3).
- Deine Aufgabe: BESTANDSAUFNAHME der existierenden Memories vor der Befüllung.

DEINE TASKS (ALLE READ-ONLY):
1. Rufe mnemosyne_stats() auf und dokumentiere: working_count,
   episodic_count, char_usage_pct.
2. Suche nach Duplikaten: mnemosyne_recall für diese Queries (je limit=5):
   - "Basti communication German"
   - "Zorin OS Ubuntu NVIDIA"
   - "Telegram routing decision"
   - "cron crontab scheduled"
   - "skill-polisher audit"
3. Pro Query: liste die Top-3 Treffer mit importance + content[:100].
4. Identifiziere potenzielle Duplikate (gleicher Fakt, unterschiedliche
   Formulierung) oder stale Memories (bezogen auf alten Systemstand).
5. Prüfe Memory-Budget: wie viel Platz bleibt für die neuen 10 Memories?
6. Empfehlung: welche Memories sollten konsolidiert/gelöscht werden?

TOOLSET:
- terminal (für mnemosyne-stats, mnemosyne-recall falls CLI verfügbar)
- mnemosyne_recall (via tool-call falls verfügbar)
- read_file (zum Lesen von ~/.hermes/SOUL.md Memory-Sektion)
- KEIN write_file, KEIN mnemosyne_remember, KEIN sudo

OUTPUT-CONSTRAINTS (PFLICHT - NICHT VERHANDELBAR):
- Output: REIN TEXT in deiner Antwort (kein File-Write)
- Sprache: Deutsch
- Max 800 Wörter
- Struktur: Markdown mit H2 pro Task (6 Sections)
- 0 em-dashes (—), Kommas statt Gedankenstrichen
- 0 mid-sentence boldface
- Pro Finding: importance-Wert + content-Snippet
- SELF-REPORT am Ende: "Bienen-Self-Report: N tool-calls, M findings"

MAX 10 tool-calls. Nach 10 → Synthese mit was du hast.

Self-Verify: Alle Fakten mit Zahlen belegt. Nichts erfinden.
```

## Learnings

1. **S3 hat das engste Toolset:** Nur mnemosyne_recall + terminal. Kein web_search, kein write.
2. **Duplicate-Finding ist der wertvollste Task (Task 2+4):** Die Biene kann Pattern in den Memories erkennen die der Queen entgehen (unterschiedliche Formulierungen für denselben Fakt).
3. **Memory-Budget-Check (Task 5):** Vor der Befüllung zu prüfen ob überhaupt Platz ist, ist essentiell für die Queen-Planung.
4. **Tool-Call-Limit niedriger (10 statt 12):** Weil mnemosyne_recall als tool-call zählt, ist der Arbeitsvorrat geringer — 5 Queries + Stat + Budget = 7 calls, Reserve 3 für follow-ups.