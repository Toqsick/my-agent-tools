# Claude Pro Plan — Budget & Session Strategy

> **Stand:** 2026-07-04
> **Gültig für:** Basti (bastick123@gmail.com), CLI v0.2.70 pre-release

## Auth-Architektur

| Merkmal | Pro/OAuth | API-Token-Plan |
|---------|-----------|----------------|
| Auth | `claude auth login` → Browser OAuth | `ANTHROPIC_API_KEY` env var |
| Billing | Kein Token-Limit, **5h Hard Session** | Pay-per-Token |
| Budget Cap | `--max-budget-usd` **killt Output** mittendrin | Funktioniert normal |
| Verfügbarkeit | Nach 5h → 3h Cooldown, dann fresh | Unbegrenzt (solange Token) |
| Reset | Mi 17:00 deutscher Zeit (weekly) | N/A |
| Modelle | Opus 4.8, Sonnet 5, Haiku 4.5, Fable 5 | Alle Modelle (je nach API-Level) |

## Verbrauchs-Monitoring

```bash
claude auth status --text
# Zeigt subscriptionType: "pro" + session usage
```

- **90% Warnung:** Keine neuen Langzeit-Tasks starten (Task stirbt mittendrin)
- **Nach Reset:** 2 frische 5h-Sessions verfügbar (Mi 17:00)
- Kein `$`-Limit pro Session, nur Time-Limit

## Model-Auswahl

| Model | Display Name | `--model` Flag | Best für | Budget |
|-------|-------------|----------------|----------|--------|
| Fable 5 | "Fable 5" | `sonnet-5-20260622` | Analyse, Inventur, Triage | KEIN Limit |
| Opus 4.8 | "Opus 4.8" | N/A (nur auf Anfrage) | Architektur-Review | KEIN Limit |
| Sonnet 5 | "Sonnet 5" | `sonnet-5-20260622` | Refactor, Coding | $0.50-1.00 |
| Haiku 4.5 | "Haiku 4.5" | `claude-haiku-4-5` | Mini-Edit, Triage | $0.20 |

> **⚠️ Achtung:** `claude -m` zeigt Display-Namen (Fable 5, Opus 4.8). Der `--model` Flag akzeptiert andere Strings (`sonnet-5-20260622`). Vor Delegation testen: `claude -p "test" --model <name>`.

## Budget-Strategie (Basti)

### "C sei am anfang jetzt nich geizig" (2026-07-04)

**Regel:** Wenn ein Task neu startet und Analyse/Lesen braucht, **KEIN Budget-Limit setzen**. Budget-Caps sind für Coding-Sprints (klar definierter Output, Schutz vor Loops). Für Research/Triage/Inventur ist Output-Verlust durch Budget-Limit teurer als ein paar extra $0.50.

### Konkrete Anwendung

```bash
# ✅ Analyse/Audit — KEIN Budget, nur max-turns
claude -p "Scanne 298 Skills, finde Duplikate" --model sonnet-5-20260622 --max-turns 20

# ✅ Coding Refactor — Budget + turns
claude -p "Refactoriere auth module" --model sonnet-5-20260622 --max-turns 10 --max-budget-usd 0.50

# ✅ Mini-Fix — Sparsam
claude -p "Fix Syntax Error Zeile 42" --max-turns 3 --max-budget-usd 0.20
```

### Budget-Verlust: Wenn's passiert

Wenn `--max-budget-usd` zuschlägt und Output mittendrin abbricht:
1. **Nicht sofort neu starten** — der Output liegt vielleicht noch im Buffer
2. Prüfe `/tmp/` auf den Briefing-Output-File: `cat /tmp/<briefing-result>.txt`
3. Manchmal ist das Ergebnis trotz Budget-Cap fertig, nur die letzte Zeile fehlt
4. Wenn Output wirklich weg: höheres Budget + gleiches Briefing + `--resume` nicht möglich (komplett neu)

### Skills-Vorladen (CRITICAL)

Claude Code **hat keinen Skill-Zugriff**. Jeder Task-Brief muss `skill_view()` Ergebnisse embedded enthalten:

```
✅ RICHTIG:
cat > /tmp/briefing.txt << 'EOF'
Kontext (aus skill_view(name)):
- 298 Skills gefunden
- 3 Duplikat-Kategorien
- ...
EOF
claude -p "$(cat /tmp/briefing.txt)" ...

❌ FALSCH:
claude -p "Lade skill_view('orchestration') und mach was damit"
```

## Session-Lifecycle

```
┌─────────────────────────────────┐
│ Neue Session (nach Reset/Cooldown) │
│ Fable 5 für Analysis → ~$0.95     │
│ Sonnet 5 für Coding  → ~$0.50     │
│ Total pro Session    → ~$1.50-3.00 │
├─────────────────────────────────┤
│ Bei 90% Warnung (>4.5h): STOP    │
│ Keine neuen Tasks starten        │
│ Nur noch kleine Edits / Doku     │
├─────────────────────────────────┤
│ 3h Cooldown → frische 5h-Session │
│ Oder: Weekly Reset Mi 17:00       │
│ → 2 frische Sessions verfügbar    │
└─────────────────────────────────┘
```
