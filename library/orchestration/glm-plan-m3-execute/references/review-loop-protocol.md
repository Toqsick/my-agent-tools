# Review-Loop Protocol

> Wann zurück zu GLM 5.2 (neuer Plan)? Wann Fix-Subagent (gleicher Plan)?
> Wann Real-World Cross-Check? Wann Critic-Gate? Wann einfach weiter?

Dieses Protocol verhindert die zwei häufigsten Anti-Patterns:
1. **Königin fixt selbst** → Context-Pollution, Königin verliert den Plan-Faden
2. **Bei jedem kleinen Fail zurück zu GLM** → Quota-Burn, 20% Kontingent in 1 Std

## Die 4 Review-Pfade

```
Queen-Verify Gate (Phase 3 oder 4b) hat ein Problem gefunden.
Welcher Pfad?

├── PATH A: Fix-Subagent (häufigster Fall)
│   Problem ist lokal, Plan ist korrekt, Subagent hat Fehler gemacht
│
├── PATH B: Zurück zu GLM (selten, aber kritisch)
│   Plan selbst ist falsch/unklar, Subagent konnte nicht richtig arbeiten
│
├── PATH C: Real-World Cross-Check (Heuristik-spezifisch)
│   Subagent-Tests grün aber Spec-Compliance unklar
│
└── PATH D: Critic-Gate (deterministische Prüfung)
    Output ist da, aber Qualität unklar
```

## PATH A: Fix-Subagent

**Wann:** Subagent hat einen lokalen Fehler gemacht, aber der Plan ist korrekt.

**Trigger:**
- ❌ File fehlt (Subagent hat es vergessen zu erstellen)
- ❌ Tests rot (Subagent hat Bug eingebaut)
- ❌ Mnemosyne-ID halluziniert (aber: Königin setzt Anker selbst, kein Subagent!)
- ❌ Quality-Gate fehlgeschlagen (z.B. EmDashes > 1, WikiLinks < 3)
- ❌ File-Inhalt entspricht nicht der Spec (aber Spec ist klar)

**Aktion:**

```python
delegate_task(
    goal=f"Fix Task {n}: {specific_problem_description}",
    context=f"""
    PROBLEM: {exact_error_message_or_finding}
    
    ORIGINAL TASK: {original_task_spec}
    
    FIX REQUIRED:
    - {specific_fix_1}
    - {specific_fix_2}
    
    VERIFICATION (führe aus VOR deinem Self-Report):
    {exact_verification_commands}
    
    SELF-REPORT MUSS enthalten:
    - Output der Verification-Commands
    - File-Größe in Bytes
    - Bestätigung dass Tests grün sind (mit Test-Output)
    """,
    toolsets=['terminal', 'file'],
)
```

**Wichtig:**
- Fix-Subagent bekommt **exakten** Fehler, nicht "mach es besser"
- Verification-Commands sind im Briefing **eingebettet** (Self-Test Protocol)
- Königin verifiziert den Fix mit denselben Befehlen nach

**Nach dem Fix:** Wave-Verify wiederholen (Phase 4b). Nicht überspringen.

## PATH B: Zurück zu GLM

**Wann:** Der Plan selbst ist falsch, unklar, oder die Realität hat sich geändert.

**Trigger:**
- ❌ Subagent baut etwas völlig anderes als im Plan (Spec ist mehrdeutig)
- ❌ Plan-Annahmen waren falsch (File existiert nicht, API hat sich geändert)
- ❌ 3+ Subagents in Folge scheitern am selben Task (Plan ist das Problem)
- ❌ Tasks sind nicht unabhängig obwohl Plan sagt sie wären (File-Overlap)
- ❌ User ändert Anforderungen mittendrin

**Aktion:**

1. **Sammle Feedback** — was genau ist am Plan falsch?

```markdown
## GLM Feedback-Report

### Was ist passiert?
- Welle 1, Task 2: Subagent sollte `tests/test_crypto.py` erstellen
- Problem: Plan sagt "erstelle Tests für RSA-Logik" aber `src/core/crypto.rs`
  enthält gar keine RSA-Logik (nur AES). Plan-Annahme war falsch.

### Was ist falsch am Plan?
- Plan-Zeile 47: "Teste RSA encrypt/decrypt Funktionen"
- Realität: `src/core/crypto.rs` hat nur AES, RSA ist in `src/core/rsa.rs`

### Was braucht der neue Plan?
- Entweder: Task aufteilen (AES-Tests + RSA-Tests in separaten Files)
- Oder: Task auf RSA-Modul umleiten
```

2. **Dispatche GLM neu** via `plan-glm` mit dem Feedback-Report:

```bash
hermes chat -q "$(cat /tmp/plan-glm-feedback.md)" \
  -m glm-5.2 \
  --provider zai \
  -s plan \
  -Q --yolo \
  --max-turns 20
```

**Wichtig:**
- GLM bekommt den **Originalplan + Feedback-Report**, nicht nur das Feedback
- Neuer Plan überschreibt nicht den alten — beide bleiben für Audit-Trail
- Max 1 Review-Loop pro Task — bei 2. Fail: User fragen (Plan ist grundlegend falsch)

**Nach dem neuen Plan:** Zurück zu Phase 3 (Queen-Verify des neuen Plans).

## PATH C: Real-World Cross-Check

**Wann:** Subagent-Tests sind grün, aber Spec-Compliance ist unklar — speziell
bei Heuristik/Detection/Klassifikations-Tasks.

**Trigger:**
- Subagent berichtet "6/6 Tests grün" bei einem Detection-Task
- Tests decken aber nur die Plan-Template-Variante ab (Pitfall #39)
- Königin ist unsicher ob die Heuristik gegen echte Daten funktioniert

**Aktion:** (siehe `subagent-driven-development` Phase 5 Real-World Cross-Check)

```bash
# Schritt 1: Inventarisiere echte Variation
find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20

# Schritt 2: Laufe Detection gegen ALLE echten Files
total=0; correct=0; mismatches=0
for f in $(find <target-dir> -name "*.md" | sort); do
    total=$((total + 1))
    output=$(python3 <detection-script> --date "$(basename "$f" .md)" --json 2>/dev/null)
    expected="<expected>"
    actual=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
    if [ "$actual" = "$expected" ]; then
        correct=$((correct + 1))
    else
        echo "❌ $f: expected=$expected actual=$actual"
        mismatches=$((mismatches + 1))
    fi
done
echo "Result: $correct/$total correct, $mismatches mismatches"
```

**Wenn Mismatches > 0:** Fix-Subagent mit kompletter Gap-Inventur (PATH A).

**Wann überspringbar:** Task ist reine CRUD/Backend/UI-Implementation ohne
Klassifikation/Detection. Dann reicht PATH A (File-Existenz + Test-Run).

## PATH D: Critic-Gate

**Wann:** Output ist da, File-Existenz ok, Tests grün — aber die Qualität
des Outputs ist unklar (z.B. komplexe Logik, Security-relevanter Code).

**Trigger:**
- Königin ist unsicher ob der Code gut ist (nicht nur ob er funktioniert)
- Task ist Security-relevant (Crypto, Auth, Input-Validation)
- Output ist komplex genug dass manuelle Review teuer wäre

**Aktion:**

```bash
# Critic-Gate Script aufrufen (lokal, via Ollama DeepSeek R1:8b)
export HERMES_CRITIC_ENABLED=true

cat > /tmp/critic-input.json << 'EOF'
{
  "output": "<code or content to review>",
  "task_description": "<was der Output enthalten sollte>",
  "schema": {"type": "code", "language": "python", "required_sections": ["Error-Handling"]},
  "assertions": [
    {"id": "retry", "text": "Retry-Logik für Connection-Error vorhanden", "critical": true},
    {"id": "timeout", "text": "Timeout-Parameter konfigurierbar", "critical": false}
  ]
}
EOF

cat /tmp/critic-input.json | python3 ~/.hermes/skills/software-development/critic-gate/scripts/critic-gate-ollama.py
```

**Verdikte:**
- `PASS` → Task done, weiter zur nächsten Welle
- `RETRY` → Fix-Subagent mit `feedback_for_worker` (PATH A)
- `FAIL` → Eskalation (kritischer Mangel), zurück zu GLM oder User fragen

## Decision Flowchart (Complete)

```
Queen-Verify hat ein Problem gefunden
│
├─ Problem ist lokal (Subagent-Fehler)?
│  ├─ JA → PATH A: Fix-Subagent mit spezifischem Feedback
│  └─ NEIN
│     │
│     ├─ Plan selbst ist falsch/unklar?
│     │  ├─ JA → PATH B: Zurück zu GLM mit Feedback-Report
│     │  └─ NEIN
│     │     │
│     │     ├─ Task ist Heuristik/Detection?
│     │     │  ├─ JA → PATH C: Real-World Cross-Check
│     │     │  └─ NEIN
│     │     │     │
│     │     │     ├─ Qualität unklar / Security-relevant?
│     │     │     │  ├─ JA → PATH D: Critic-Gate
│     │     │     │  └─ NEIN → ✅ Weiter zur nächsten Welle
```

## Loop-Limits (Quota-Schutz)

| Pfad | Max-Loops pro Task | Bei Überschreitung |
|---|---|---|
| PATH A (Fix-Subagent) | 3 | Task als "needs human review" markieren, überspringen |
| PATH B (Zurück zu GLM) | 1 | User fragen — Plan ist grundlegend falsch |
| PATH C (Real-World Cross-Check) | 2 | Heuristik komplett neu designen (PATH B) |
| PATH D (Critic-Gate) | 2 | Code-Architektur-Frage → User fragen |

**Total Review-Loops pro Plan:** max 5. Bei Überschreitung → Pause, User
konsultieren. Ein Plan der 5+ Review-Loops braucht ist fundament kaputt.

## Anti-Patterns

| Anti-Pattern | Symptom | Fix |
|---|---|---|
| **Königin fixt selbst** | Königin dispatched `patch` oder `write_file` um Subagent-Fehler zu beheben | IMMER Fix-Subagent. Königin bleibt Orchestration-Only. |
| **Bei jedem Fail zurück zu GLM** | 3 GLM-Calls für einen Task | Nur PATH B (Plan falsch) geht zurück zu GLM. PATH A (Subagent-Fehler) bleibt lokal. |
| **Review-Loop ohne Verification** | Fix-Subagent dispatched ohne Verification-Commands im Briefing | Verification-Commands IMMER im Briefing (Self-Test Protocol aus `multi-agent-master-workflow`) |
| **Wave-Verify wird zu Mini-Audit** | Wave-Verify dauert 10+ Minuten | Max 3 Befehle. Wenn mehr nötig → Welle war zu groß, aufteilen. |
| **Critic-Gate für triviale Tasks** | Critic-Gate aufgerufen für einen 5-Zeilen Config-Change | Critic-Gate nur für Security/Komplexität. Trivial = File-Existenz-Check reicht. |
