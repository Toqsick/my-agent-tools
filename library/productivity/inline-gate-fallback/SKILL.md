---
name: inline-gate-fallback
description: |
  Use when a required user approval or decision cannot be routed through Telegram DM, the messaging channel is unavailable, or work must pause behind an inline chat gate.
  NOT for low-risk informational questions, silently assuming consent, or bypassing an available required approval channel.
  Provides a state-aware blocking prompt with explicit options, consequences, timeout behavior, and safe resume instructions.
version: 1.0.0
author: Yuno (Basti)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - fallback
    - gate
    - input-flow
    - working-agreement
    related_skills:
    - yuno-user-preferences
    - telegram-clarification-prompt
trigger_keywords: ['required', 'approval', 'channel', 'user', 'decision']
keywords: ['required', 'approval', 'channel', 'user', 'decision']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['telegram-clarification-prompt']
---


# Inline Gate Fallback

## Overview
Dieses Pattern regelt das blockierende Einholen von Benutzerentscheidungen direkt im Chatfenster, falls das Telegram-DM-Routing (Working Agreement §1) ausfällt oder nicht verfügbar ist und eine Aktion eine ausdrückliche Freigabe erfordert.

## When to Use
- **Trigger**: Das `send_message`/`telegram`-Tool liefert Fehler oder ist in der aktuellen Session nicht konfiguriert.
- **Trigger**: Systemkritische Operationen (z.B. Konfigurations-Edits) erfordern laut Working Agreement §3 eine explizite Entscheidung durch Basti.
- **Trigger**: Komplexe, mehrstufige Aufgaben mit echten Trade-offs (z.B. Pakete A/B/C) müssen verhandelt werden.
- **Nicht verwenden für**: Triviale Entscheidungen (führe diese proaktiv aus und melde das Ergebnis) oder wenn Basti explizit eine Benachrichtigung via Telegram wünscht und das Tool funktioniert.

## Implementation Steps

### 1. System-Status erfassen (Pattern 7)
Bevor du das Inline-Gate formulierst, prüfe den tatsächlichen System-Zustand live ab (Daten schlagen Annahmen).
```bash
# Beispiel: Prüfen ob Obsidian-Prozesse laufen
ps aux | grep -i 'md.obsidian.Obsidian' | grep -v grep
```

### 2. Strukturierten Inline-Gate formulieren
Präsentiere die Situation sachlich und biete **2 bis 4 klar abgegrenzte Optionen** mit Buchstaben (Option A, Option B) oder römischen Ziffern an.

```
## 🔴 Befund: [Live-Systemzustand]

[Wahrheit über das Problem, präzise und knapp]

---

## ⚠️ Konsequenzen & Risiken

[Auswirkungen auf Links, Dateien oder Systemstabilität]

---

## Konkrete Optionen:
**Option A — [Name 1]** (Vorteile, Aufwand/Nutzen: ⭐⭐⭐)
**Option B — [Name 2]** (Vorteile, Aufwand/Nutzen: ⭐⭐⭐⭐)

---

## Empfehlung & Nächster Schritt
Ich empfehle Option A. Ich warte kurz auf deine Wahl (A/B), um fortzufahren!
```

### 3. Sicheres Pre-Flight & Backup vor Ausführung
Sobald der User geantwortet hat (z.B. mit "A"), erstelle ein Sicherheitsbackup aller betroffenen Ordner und führe den Patch atomar aus.

## Common Pitfalls
1. **Vage Rückfragen**: Vermeide schwammige Fragen wie "Was soll ich tun?". Basti entscheidet am liebsten aus einer Liste definierter Optionen.
2. **Keine Backups vor der Ausführung**: Systemeingriffe oder Massen-Patches ohne vorheriges `tar` gefährden den Datenstand.
3. **Vergessen der Systemprüfung**: Blindes Vertrauen auf Berichte von Sim-Stimmen (Advisors) statt Live-Systemabfrage via Terminal.

## Verification Checklist
- [ ] Telegram-Status wurde auf Ausfall geprüft
- [ ] Befund wurde mit realen System-Readings (Pattern 7) untermauert
- [ ] Gate bietet genau 2 bis 4 eindeutige Optionen
- [ ] Vor dem Schreiben kritischer Dateien wurde ein manuelles Backup angelegt
- [ ] Nach der Wahl des Benutzers wurde der Patch atomar und verifiziert angewendet

## Verbindet zu
- [[Patterns & Workflows - Innovationsraum]] — Fallback-Kaskade
- [[Parent-Direct-Fallback - Pattern]] — Schwester-Fallback
- [[Subagent-Patterns - Delegation & Routing]] — Delegations-Kontext
- [[Working Agreement - Yuno Basti]] — Arbeitsvereinbarungen
