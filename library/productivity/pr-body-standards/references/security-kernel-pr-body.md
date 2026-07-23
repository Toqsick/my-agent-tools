# Example: PR Body für feat/security-kernel

Branch: `feat/security-kernel` in `/home/bratan/30-Library/hermes-v7`
Base: `c07b058`

## Was dieser PR-Body zeigt

Dieses Beispiel demonstriert die 4-Abschnitt-Struktur aus `pr-body-standards` an einem realen Fall:
- Vollständige Was / Wie verifiziert / Architektur-Funde / Was bewusst NICHT gemacht - Aufteilung
- Pre-Existing-vs-Introduced-Trennung mit `git stash`-Verifikation
- Root-Cause-Tracing (task.owner='orchestrator' + fehlendes Pseudo-Tool)
- Live-Test-Execution statt Briefing-Assertions

## Session-Kontext

Der PR-Body wurde für `feat/security-kernel` erstellt — ein Branch der den `SecurityKernel`
in `hermes-v7` verdrahtet (4 Security-Ebenen + Rollen-Phasen-Audit). Das Daily-Briefing
behauptete "21/21 Tests grün" — die Live-Execution zeigte 20/21 + 1 pre-existing Failure.

## Gelieferter PR-Body (Auszüge)

### Section 1: Was

```
Neue Dateien:
- src/security/kernel.ts – SecurityKernel/KernelError-Klasse
- src/security/__tests__/kernel.test.ts – 16 Contract-Tests
- src/roles/__tests__/orchestrator.test.ts – 5 Integrationstests

Geänderte Dateien:
- src/security/tool-profiles.ts – 5 Pseudo-Tools ortschestrator-phase:{...}
- src/roles/orchestrator.ts – withKernel()-Helper
- package.json – ts-jest devDependencies
```

### Section 2: Wie verifiziert

```
Suite                        | Ergebnis
kernel.test.ts               | 16 passed / 16 total
orchestrator.test.ts         | 4 passed / 5 total (1 Test rot – s. Section 4)

Getestete Verträge:
- Bypass-Schutz: run() wirft wenn startup() nie lief
- Ebenen-Reihenfolge: Gateway-User vor Tool-Profile vor Egress
- failOpen ausschließlich auf Egress beschränkt
- Audit-Log: pro Call 1 Intent + 1 Result mit identischem inputHash
- Orchestrator ohne Kernel läuft unverändert durch
```

### Section 3: Architektur-Funde

```
1. Zwei parallele Orchestrator-Implementierungen
   - src/roles/orchestrator.ts (TS, KERNEL-ANGEBUNDEN)
   - src/modules/orchestrator/index.js (CommonJS, NICHT durch Kernel)

2. RunTime-Level-Audit existiert parallel in src/runtime/tool-runtime.ts

3. approval-hook-Modul fehlt – Slot im Kernel ist vorbereitet

4. tsconfig.json fehlt – Tests laufen nur via ts-jest-Inline-Compilation
```

### Section 4: Was bewusst NICHT gemacht wurde

```
Orchestrator-Audit-Test rot (1 von 5):
- Root Cause: task.owner='orchestrator' initial → withKernel übergibt
  role='orchestrator' + toolName='orchestrator-phase:plan' → orchestrator-Profil
  hat dieses Pseudo-Tool nicht → assertToolAllowed blockiert
- Option A: task.owner VOR erstem withKernel() auf 'planner' setzen
- Option B: role aus Phase ableiten statt aus task.owner
- Option C: Pseudo-Tools ins orchestrator-Profil aufnehmen
- Option D: Kernel-Context im Orchestrator mappen
- Empfehlung: Option B (semantisch sauber) — Entscheidung offen
```

## Lessons aus diesem Beispiel

1. **Briefing-Assertion vs Realität:** Das Daily-Briefing zeigte "21/21 grün" – nach Live-Execution waren es 20/21 + 1 pre-existing Failure auf cronjob-adapter
2. **Pre-Existing-Verifikation:** `git stash` → `jest --ci cronjob-adapter.test.js` auf base-commit zeigte: rot auch ohne Branch-Änderungen → Pre-Existing, raus aus PR-Body
3. **Root-Cause-Tracing:** Der orchestrator.test.ts-Failure wurde nicht als "Test fails" dokumentiert, sondern als "task.owner='orchestrator' → Pseudo-Tool fehlt im Profil"
4. **Fix-or-Defer:** Kein Fix im PR, aber 4 Optionen + Empfehlung → Reviewer kann entscheiden
