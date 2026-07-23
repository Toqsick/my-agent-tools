# A3 — Algorithmus-Wortliste DE-spezifisch

> **Trigger:** Vor dem ersten Upload (kann Phase-B-Tests überschreiben wenn falsche Wörter schon gepostet).
> **Wann:** ASAP — diese Frage schützt dich vor Shadowban.
> **Ziel:** Safe-Word-Liste für alle Card-1-Hooks in den Bulk-CSVs.

## Wann diese Frage stellen

✅ Du bist kurz vor dem ersten Upload
✅ Du hast `canva-bulk-create-{nische}.csv` schon draftet
✅ Du willst nicht 14 Posts hochladen und dann merken dass Card 1 shadowban-gefährdet ist
❌ NICHT parallel zu A1/A2 laufen lassen — diese Frage ist blocking, sie muss vor erstem Upload fertig sein

## Daten die du mitgeben musst

- 3-5 deiner aktuellen Card-1-Hooks (zum Gegencheck)
- Deine aktuelle Pitch-Variante ("Mehr in meinem Profil" o.ä.)

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
I need a German-language TikTok algorithm-safety audit. Compile:

1. BANNED-WORDS LIST (German): words/phrases that TikTok's 2026 algorithm flags as commercial intent and downranks. Include severity level (shadowban-risk vs reach-limit). Cross-reference with German UWG advertising law where relevant.

2. BOOST-WORDS LIST: phrases that get more reach in organic discovery (curiosity triggers, emotional hooks, save-prompt language).

3. NEUTRAL-BUT-USEFUL: hashtags that don't help but don't hurt vs hashtags that actively boost (German + English mix).

4. The "Mehr in meinem Profil" trick: is this actually safer than "Link in Bio"? Cite the 2026 evidence — TikTok has changed their commercial-language detection multiple times.

5. Case-study accounts: 3 German faceless accounts that got visibly shadowbanned, what they did wrong, what they changed to recover.
```

## Output-Format von Perplexity erwartet

- 3 Wortlisten-Tabellen (Banned/Boost/Neutral) mit Severity-Spalte
- Vergleich "Mehr in meinem Profil" vs "Link in Bio" mit Evidenz
- 3 Case-Studies mit @-Handles + Recovery-Strategie

## Was du mit der Antwort machst

1. **Banned-Words durchsuchen** in deiner `pitch-variants.json` — alle problematischen Texte markieren und patchen
2. **Card-1-Hooks** in `canva-bulk-create-{nische}.csv` checken — keine "Klick", "Kauf", "Gratis", "Sparen" (je nach Severity)
3. **Safe-Word-Block** als neuen Eintrag in `pitch-variants.json`:
   ```json
   {
     "algorithm_safety_2026": {
       "banned_words": [...],
       "boost_words": [...],
       "safe_alternative_to_link_in_bio": "Mehr in meinem Profil",
       "source": "Perplexity Deep Research 2026-07-XX"
     }
   }
   ```
4. **Pitch-Default-Text** updaten falls nötig (z.B. wenn "Mehr in meinem Profil" doch gefährlich ist)

## Pitfalls

- **"Verifiziert" ≠ "sicher"** — Perplexity kann die TikTok-Algorithmus-Doku nicht direkt lesen. Die Listen basieren auf Case-Studies und öffentlichen Berichten. Mit Skepsis lesen.
- **DACH-spezifisch**: Englische Listen ("Buy now", "Free", "Limited time") sind NICHT 1:1 auf Deutsch übertragbar. TikTok hat separate Modelle für DE-Inhalte.
- **UWG-Konflikt**: Manche Wörter sind UWG-rechtlich problematisch (z.B. "Kostenlos" für nicht-100%-gratis-Produkte). TikTok-Algorithmus + UWG sind zwei separate Layer — beide listen.

## Cross-Links

- Phase A: [`01-phase-a-pre-launch.md`](01-phase-a-pre-launch.md)
- Skill: `tiktok-design-assistant` (Pitch-Varianten-Generierung)
- Update-Target: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json`
- Update-Target: `~/10-Projekte/10-active/yuno-anon-tiktok-business/data/canva-bulk-create-{nische}.csv`