# Pre-Existing Error Verification — Full Workflow

## Kontext

Wenn ein PR in einem Repo mit TypeScript- und Jest-Tests arbeitet, müssen **beide** Checks auf Pre-Existing vs. Introduced getrennt werden. Ein Test-Suite-Pass (z.B. 21/21 grün) schließt nicht aus, dass `npx tsc --noEmit` 5+ Compile-Fehler wirft — und umgekehrt.

## Workflow

### 1. Baseline auf base-commit ermitteln

```bash
cd <repo>
git stash                          # eigene Änderungen weglegen

# 1a) Test-Suite auf base-commit
npx jest --ci 2>&1 | tail -20

# 1b) TypeScript-Check auf base-commit
npx tsc --noEmit 2>&1 | head -30
npx tsc --noEmit 2>&1 | wc -l      # Fehleranzahl (0 = sauber, >0 = pre-existing)

# Ergebnis notieren, z.B.:
#   Tests:   21 passed, 21 total
#   TS-Err:  5 errors (alle in src/depp/*)
```

### 2. Branch-Zustand prüfen

```bash
git stash pop                      # eigene Änderungen zurück

# 2a) Tests mit Branch-Code
npx jest --ci 2>&1 | tail -20

# 2b) TypeScript mit Branch-Code
npx tsc --noEmit 2>&1 | head -30
npx tsc --noEmit 2>&1 | wc -l
```

### 3. Vergleich

| Zustand | Tests | TS-Fehler | Bewertung |
|---------|-------|-----------|-----------|
| Base-commit | 21/21 | 5 | — |
| Branch | 21/21 | 5 | **Pre-Existing** → Section 3 Fund, kein PR-Blocker |
| Branch | 20/21 | 5 | **Introduced Test-Failure** → root-causen |
| Branch | 21/21 | 8 | **3 neue TS-Fehler** → fixen vor PR |

## Real-Beispiel (SecurityKernel, 2026-07-04)

```
# Base-commit (c07b058) — vor dem Branch:
Tests:   21 passed, 21 total
TS-Err:  5 (TS2367 in depp-worker.ts, TS2367 in truncation-detector.ts,
          TS2307 in depp-orchestrator.ts ×3, TS7006 in depp-orchestrator.ts)

# Branch (f704ff1):
Tests:   21 passed, 21 total    ← keine neuen Failures
TS-Err:  5 (exakt gleiche 5)    ← pre-existing, unverändert

# Fazit: PR führt 0 neue Fehler ein.
# Die 5 pre-existing depp-Fehler sind separat als Fund dokumentiert.
```

## Common Pitfalls

1. **Nur Tests ausführen, TS vergessen** — `ts-jest` kompiliert Inline, also können Tests grün sein während `tsc --noEmit` viele Fehler wirft.
2. **Nach `git stash` vergessen, `pop` zu machen** — dann läuft der Rest des Workflows ohne die Branch-Änderungen. Immer `stash pop` oder `stash apply` nach dem Check.
3. **Fehleranzahl aus `tsc --noEmit` nicht tracken** — wenn vorher 5 Fehler, nachher 8, sind 3 neu. Die Differenz ist entscheidend, nicht absolute Zahl.
4. **Briefing-Snapshot als Wahrheit akzeptieren** — Daily-Briefing kann "21/21 grün" zeigen obwohl die Suite den pre-existing Test nicht mit ausführt. Immer selbst laufen lassen.
