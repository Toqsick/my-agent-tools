# Pattern 3: Anti-Halluzinations-Tripwire

## Problem
Subagent soll Notes füllen, hat aber keinen Read-Zugriff auf Datenquellen (Repos, Configs, Logs).

## Lösung: Explizite Fallback-Regel im Briefing

> Wenn Datenquelle nicht lesbar → schreibe **"Status: ungeprüft (Quelle nicht zugreifbar am <Datum>)"** und lasse Felder leer oder TODO.

## Anti-Pattern
Subagent erfindet plausible Tech-Details (Dependencies, Versionsnummern, Befehls-Flags) → Müll im Vault.

## Best Practice
- **Immer Read-Zugriff** auf Quelldaten gewähren wenn möglich
- Fallback-Regel **explizit im Briefing** nennen (nicht implizieren)
- Beispiel-Tripwire in `obsidian-subagent-briefing-template` Skill

## Date-Stamp Refinement (Phase 6, 2026-07-05)

Erweitere Pattern 3 um die **"manuell erweitern" Date-Stamp-Konvention** für quantitative Daten in Vault-Notes:

> Wenn du Performance-Zahlen (tokens/s, Latenz ms, VRAM-Nutzung) **nicht aus Vault-Notes bestätigen kannst**:
> - Keine erfundenen Zahlen. Statt "~21.5 tok/s": `Je nach Modell (Stand YYYY-MM-DD, manuell erweitern).`
> - In der MOC-Quellen-Sektion: `**Mnemosyne-Recalls:** Keine Recalls zu konkreten [X]-Zahlen am [Datum]; manuell pflegen.`
>
> Warum besser als "Status: ungeprüft": Das genaue Datum + der manuelle Pfad gibt dem nächsten Agenten einen klaren Fix-Action-Plan.

## Proven (Phase 6, 2026-07-05)
18 Notes (3 MOCs + 15 Satelliten) — 0 halluzinierte Performance-Zahlen.