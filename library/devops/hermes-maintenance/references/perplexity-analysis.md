# Perplexity-style Security Analysis — Reality-Filter

> Extracted from hermes-maintenance SKILL.md Section 4.

Wenn eine externe AI (Perplexity, GPT, etc.) eine Security-Analyse liefert:

**Was oft richtig ist:** strukturelle Lücken (Race-Conditions, missing features, audit-trail-Probleme)

**Was oft FALSCH/VERALTET ist:**
- "Tirith ist eingebaut" → check ob `tirith_enabled: true` (sonst nur Attrappe)
- "SSRF-Schutz vorhanden" → check ob `allow_private_urls: false`
- "Audit-Log fehlt" → check ob V7 schon Hash-Chain hat
- "Provider logged Prompts" → ist meistens unbegründet, nicht als gegeben hinnehmen

**Workflow:**
1. Externe Analyse als **Hypothese** lesen, nicht als Befund
2. Jeden Punkt im Hermes-Repo/Config **real-verifizieren** (grep, cat, code-read)
3. Reality-Check-Doc schreiben mit: "Was hat die Quelle richtig, was falsch"
4. **Erst dann** entscheiden welche Lücken echt sind
