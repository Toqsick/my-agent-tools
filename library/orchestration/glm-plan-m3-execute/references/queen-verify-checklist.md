# Queen-Verify Checklist

> Konkrete Befehle für Phase 3 (Plan-Verify) und Phase 4b (Wave-Verify).
> Diese Checklist ist nicht verhandelbar — sie ist das Rückgrat der Pipeline.

## Phase 3: Plan-Verify (vor M3 Dispatch)

Nachdem GLM 5.2 den Plan geschrieben hat, aber **bevor** der erste Subagent
dispatched wird.

### 3.1 Quality-Gate Shell-Check (S1-S7)

```bash
#!/bin/bash
# Usage: bash queen-verify-plan.sh <plan-file>

PLAN="${1:-$HOME/.hermes/plans/last-plan.md}"
PASS=true

if [ ! -f "$PLAN" ]; then
    echo "❌ Plan-File nicht gefunden: $PLAN"
    exit 2
fi

echo "═══════════════════════════════════════════════════════════"
echo "  QUEEN-VERIFY: $PLAN"
echo "═══════════════════════════════════════════════════════════"

# ─── S1: Realitäts-Status-Tabelle ───
cnt=$(grep -c "Realitäts-Status\|Reality-Check\|Live-Verifik" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S1: Realitäts-Status-Tabelle ($cnt Treffer)"
else
    echo "❌ S1: Realitäts-Status-Tabelle FEHLT"
    PASS=false
fi

# ─── S2: SSOT-Audit-Tabelle (nur bei audit-driven Plänen) ───
# Optional — nicht jeder Plan ist audit-driven
cnt=$(grep -c "Geplanter Status\|Brief-Behauptung\|Tatsächlicher Status" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S2: SSOT-Audit-Tabelle ($cnt Treffer) [optional]"
elif echo "$PLAN" | grep -qi "audit\|refactor\|backlog"; then
    echo "⚠️ S2: SSOT-Tabelle fehlt, aber Plan scheint audit-driven — empfohlen"
else
    echo "➖ S2: SSOT-Tabelle (nicht erforderlich für nicht-audit-Plan)"
fi

# ─── S3: Konkrete Minuten-Schätzungen ───
cnt=$(grep -cE "[0-9]+ Min" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S3: Minuten-Schätzungen ($cnt Treffer)"
else
    wave_cnt=$(grep -cE "Welle|Wave" "$PLAN" 2>/dev/null || echo 0)
    if [ "$wave_cnt" -ge 1 ]; then
        echo "❌ S3: Minuten FEHLEN — brauchen Schätzungen für Wave-Planung"
        PASS=false
    else
        echo "⚠️ S3: Minuten fehlen — ok für trivialen Plan ohne Waves"
    fi
fi

# ─── S4: Atomic-Write Policy ───
# Wird implizit durch patch-vs-write_file Syntax geprüft
cnt=$(grep -c "Atomic-Write\|write_file.*not.*patch\|ein.*write_file" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S4: Atomic-Write Policy ($cnt Treffer)"
else
    echo "⚠️ S4: Atomic-Write Policy nicht explizit — bei Frontmatter-Edits prüfen"
fi

# ─── S5: Risiko-Sektion R1-Rn ───
cnt=$(grep -cE "^###? R[0-9]" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S5: Risiko-Sektion ($cnt Risiko-Items R1-Rn)"
else
    echo "❌ S5: Risiko-Sektion R1-Rn FEHLT"
    PASS=false
fi

# ─── S6: Wave-Strategie ───
cnt=$(grep -cE "Welle|Wave" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S6: Wave-Strategie ($cnt Treffer)"
else
    task_cnt=$(grep -cE "^### Task [0-9]" "$PLAN" 2>/dev/null || echo 0)
    if [ "$task_cnt" -ge 4 ]; then
        echo "❌ S6: Wave-Strategie FEHLT — $task_cnt Tasks brauchen Wave-Gruppierung"
        PASS=false
    else
        echo "➖ S6: Wave-Strategie (nicht benötigt bei ≤3 Tasks)"
    fi
fi

# ─── S7: Done-Kriterium Checkbox-Liste ───
cnt=$(grep -cE "^- \[ \]" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "✅ S7: Done-Kriterium ($cnt Checkboxen)"
else
    echo "❌ S7: Done-Kriterium Checkbox-Liste FEHLT"
    GLM_PASS=false
fi

echo "═══════════════════════════════════════════════════════════"
if $PASS; then
    echo "  ✅ ALL GATES GREEN — bereit für Phase 4 (M3 Dispatch)"
    exit 0
else
    echo "  ❌ GATES FAILED — Plan zurück an GLM mit spezifischem Feedback"
    exit 1
fi
```

### 3.2 3-Fragen-Regel (Plan-Annahmen-Verify)

Zusätzlich zum Gate-Check: beantworte die 3 Fragen aus
`plan-glm/references/post-plan-queen-verify.md`:

```bash
# Frage 1: Datei-Realität
echo "=== F1: Datei-Existenz aller Plan-Pfade ==="
# Extrahiere alle Pfade die der Plan mit ls/test/find erwähnt und verifiziere
grep -oE '(src|tests|docs|~)/[^\s")\]]+' "$PLAN" | sort -u | while read path; do
    expanded=$(eval echo "$path" 2>/dev/null)
    if [ -e "$expanded" ]; then
        echo "  ✅ $path"
    else
        echo "  ❌ $path (MISSING)"
    fi
done

# Frage 2: Struktur-Realität (bei Heuristik-Tasks)
echo "=== F2: Section-Header-Inventar ==="
# Nur wenn der Plan Heuristiken erwähnt
if grep -qiE "detect|heurist|classif|parse" "$PLAN"; then
    echo "  Plan erwähnt Heuristik/Detection — Section-Inventar prüfen:"
    echo "  (Führe aus: find <target> -name '*.md' | xargs grep -hE '^## ' | sort | uniq -c | sort -rn)"
fi

# Frage 3: Health-Realität (bei Status-Klassifikation)
echo "=== F3: Health-Klassifikation (falls relevant) ==="
if grep -qiE "HEALTHY|PARTIAL|STUB|MISSING" "$PLAN"; then
    echo "  Plan verwendet Status-Klassifikation — führe Detection auf ALLEN Files aus"
    echo "  und vergleiche Output mit Plan-Annahmen"
fi
```

## Phase 4b: Wave-Verify Gate (zwischen Subagent-Wellen)

Nach jeder Welle, **bevor** die nächste dispatched wird. Maximal 3 Befehle —
nicht mehr, sonst wird es ein Mini-Audit.

### 4b.1 File-Existenz-Verify

```bash
# Für jeden File den die Subagents behaupten erstellt/modified zu haben:
for f in \
    "src/models/user.py" \
    "tests/models/test_user.py" \
    "src/core/crypto.rs"; do
    full=$(eval echo "$f" 2>/dev/null)
    if [ -f "$full" ]; then
        size=$(stat -c%s "$full" 2>/dev/null || stat -f%z "$full" 2>/dev/null)
        echo "  ✅ $f ($size bytes)"
    else
        echo "  ❌ $f MISSING (Subagent hat es nicht erstellt)"
    fi
done
```

### 4b.2 Mnemosyne-Anchor-Verify (Pitfall #36, kritisch)

```python
# Subagent behauptet "Mnemosyne-Anker gesetzt mit ID abc123"
# Königin MUSS verifizieren — 4/4 Subagents halluzinierten IDs am 2026-07-17

claimed_ids = ["abc123", "def456"]  # aus Subagent-Report extrahieren
verified = []

for mid in claimed_ids:
    result = mnemosyne_get(memory_id=mid)
    if result["status"] == "ok":
        print(f"  ✅ {mid} — recallbar")
        verified.append(mid)
    else:
        print(f"  ❌ {mid} — NOT FOUND (halluziniert)")
        # Königin setzt den Anker selbst
        queen_anchor = mnemosyne_remember(
            content=f"### [YYYY-MM-DD] {task_name} — Queen-Anker (Subagent-ID war halluziniert)\n{task_summary}",
            importance=0.7,
            source="self-improving"
        )
        print(f"  🔧 Queen hat Anker selbst gesetzt: {queen_anchor['memory_id']}")

assert len(verified) + len(queen_set) >= len(claimed_ids), "Nicht alle Anker gesichert"
```

### 4b.3 Spec-Compliance-Check

```bash
# Falls die Welle einen Heuristik/Detection-Task hatte:
# Laufe die Heuristik gegen ALLE echten Files, nicht nur Test-Fixtures

echo "=== Spec-Compliance: Real-World Cross-Check ==="
total=0
correct=0
mismatches=0

for f in $(find <target-dir> -name "*.md" | sort); do
    total=$((total + 1))
    output=$(python3 <detection-script> --date "$(basename "$f" .md)" --json 2>/dev/null)
    expected="<expected-class>"
    actual=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
    if [ "$actual" = "$expected" ]; then
        correct=$((correct + 1))
    else
        echo "  ❌ MISMATCH: $f expected=$expected actual=$actual"
        mismatches=$((mismatches + 1))
    fi
done

echo "  Ergebnis: $correct/$total korrekt, $mismatches Mismatches"
if [ "$mismatches" -eq 0 ]; then
    echo "  ✅ Spec-Compliance OK"
else
    echo "  ❌ Spec-Compliance FAILED — Fix-Subagent nötig"
fi
```

### 4b.4 Test-Run (bei Code-Tasks)

```bash
# Falls die Welle Code-Implementation enthielt
echo "=== Test-Run ==="
cd <project-dir>

# Python
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    pytest tests/ -q --tb=short 2>&1 | tail -5
fi

# Rust
if [ -f "Cargo.toml" ]; then
    cargo test 2>&1 | tail -5
fi

# Node
if [ -f "package.json" ]; then
    npm test 2>&1 | tail -5
fi
```

## Wave-Verify Decision Matrix

| Befund | Aktion |
|---|---|
| ✅ Alle Files existieren, Tests grün, Anker verifiziert | Nächste Welle dispatchen |
| ❌ 1-2 Files fehlen | Fix-Subagent mit spezifischem Feedback für diese Files |
| ❌ Tests rot | Fix-Subagent mit Test-Output als Kontext |
| ❌ Mnemosyne-ID halluziniert | Königin setzt Anker selbst (kein Subagent nötig) |
| ❌ Spec-Drift (Heuristik missklassifiziert) | Fix-Subagent mit kompletter Gap-Inventur |
| ❌ Subagent baute etwas völlig anderes als im Plan | **Zurück zu GLM** — Plan-Spec ist unklar |
| ⚠️ Subagent berichtet "grün" aber Spec-Compliance unklar | `critic-gate` Script aufrufen (deterministisches Review) |

## Timing-Budget

| Phase | Max-Dauer | Wenn überschritten |
|---|---|---|
| Phase 3 (Plan-Verify) | 3 Min | Wenn länger → die Königin macht ein Mini-Audit daraus (anti-pattern) |
| Phase 4b (Wave-Verify) | 2 Min pro Welle | Wenn länger → zu viele Files/Anker in einer Welle, Welle aufteilen |
| Fix-Subagent-Dispatch | 1 Min Decision | Wenn länger → Königin context-polluted, neu fokussieren |

**Anti-Pattern:** Ein Wave-Verify der 10 Minuten dauert bedeutet, dass die
Königin anfängt die Subagent-Arbeit selbst zu debuggen. Das ist Context-Pollution.
Stattdessen: Fix-Subagent mit klarem Feedback, Königin bleibt clean.
