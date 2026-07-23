# Tool-Cost Hierarchy & API-Key Security (2026-07-15)

## Tool-Cost Preference

**Trigger-Sätze:** "schalte den verbrauch bei nous auf nur tool use kein flash", "wenn möglich lokal nutzen", "bei nous kein deepseek".

**Hierarchie:**
1. Lokal first (Ollama)
2. Free-Modelle (GLM-5, StepFun Free)
3. Nous Portal nur Notfall, dann NUR günstigste (StepFun Free)
4. KEIN DeepSeek auf Nous

**Subagent-Briefings MÜSSEN Tool-Tier spezifizieren.**

## API-Key Security Rule

**Trigger-Satz:** "alle API in memory zensieren nur in .env"

**Regeln:**
1. Keys NUR in `~/.hermes/.env` — nie in Memory, DB, Chat, Briefings
2. Vor `mnemosyne_sleep`: Pre-Scan auf Key-Patterns
3. Bei Fund: `mnemosyne_invalidate`, User informieren
4. False Positives erkennen (Regeltexte matchen sich selbst)
5. Subagent-Briefings: nur Variablen-Namen, nie Values
6. False-Positive trotzdem vermerken ("nur Regeltext, kein Leak")

**Technik:** Siehe `~/.hermes/skills/devops/mnemosyne-memory-provider/references/pre-consolidation-secret-scan.md`