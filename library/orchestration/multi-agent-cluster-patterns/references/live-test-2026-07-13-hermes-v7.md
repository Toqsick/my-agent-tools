# 🅲️ Live-Test Lessons 2026-07-13 — Hermes-V7 Mission-B

**Origin:** Erster echter 🅲️ Rolling-Wave Live-Test der Hermes-V7 Idempotenz-Key Mission.
**Spec-Version:** v1.4.0 → v1.5.0
**Status:** Phase 3 Welle 1 lief zum Zeitpunkt der Lessons-Dokumentation; Eval-Status TEIL-Fix.

---

## Setup der Mission

- **Mission:** Hermes-V7 Idempotenz-Key Patch (P0-Item aus MiroFish-Werkstatt 2026-07-12)
- **Repo:** `/home/bratan/30-Library/hermes-v7/` (read-only-Heimat, ABER Hermes-V7 read-only-Ausnahme vom User)
- **Workflow:** PR-First (Branch `feat/idempotency-key-patch`, push, kein lokaler Merge-Commit)
- **Issue-Tracking:** GitHub `Toqsick/hermes-v7` (Issue #2 für Idempotenz-Key)
- **Phasen-Status:** Phase 0.5 ✅ → Phase 1 (3 Scouts parallel, 93s) ✅ → Phase 2 (Plan-Biene sequentiell, 67s) ✅ → Phase 3 Welle 1 (A1+A2, 5m59s) ✅ → Welle 2 (A3∥A4, 8m36s) ✅ → Welle 3 (A5, 8m39s) ✅ → Welle 4 (A6) 🔄

## Commit-History der Mission

| Commit | Welle | Anforderung | Self-Commit? |
|---|---|---|---|
| `110f7a9` | 1 | A1 (Branch+Cleanup) + A2 (Schema additiv, +52/-0 in types.ts) | ✅ A1-Biene (Briefing forderte es) |
| `2920e93` | 2 | A3 (Cache-Lookup in tool-runtime.ts) + A4 (Audit-Log cache_hit-Event) | ❌ **Königin-Commit** (Bienen haben nicht gepusht) |
| `c4f092f` | 3 | A5 (Feature-Flag HERMES_IDEMPOTENCY_ENABLED, Dual-Layer env>config>default) | ✅ A5-Biene (Briefing sagte explizit "PFLICHT") |

**Kumulativer Diff-Stand vor Welle 4:** 7 files, +785/-5.

**Lehre aus Welle 2:** Worker-Bienen committen NICHT selbst wenn nicht explizit gefordert. A3+A4 Bienen haben gearbeitet, tsc grün, Tests grün, ABER working-tree war dirty als sie zurückkamen. Königin musste manuell committen + pushen → **Pitfall #26** (gepatcht in v1.5.1).

**Lehre aus Welle 3:** Briefing-Verstärkung funktioniert. A5-Briefing sagte "AM ENDE — PFLICHT: git add, git commit, git push" → A5-Biene hat self-committed. → **Generalisierung:** Die Lösung für Self-Commit-failures ist Briefing-Disziplin, nicht Biene-Disziplin.

## Was funktioniert hat ✅

1. **Decision-Tree (Scope klar → 🅲️)** hat den richtigen Modus ohne Diskussion gewählt
2. **Phase 0.5 Königin-Vor-Scout** hat den `feat/security-kernel`-Branch + 3 unversionierte Files + `tsc --noEmit grün`-Baseline erkannt BEVOR Bienen scouten mussten
3. **3 Scout-Bienen parallel (93s)** mit sauberer Pitfall-#5-Disziplin (alle haben Lücken explizit zugegeben statt halluziniert, und TaskCard ≠ LaneTask korrigiert)
4. **Plan-Biene sequentiell (67s)** destillierte 6 Anforderungen A1-A6 mit vollständigen Acceptance-Criteria, Rollback-Strategie, Pitfall-Watchlist, Diff-Bericht-Format-Spec und 4 expliziten Lücken-Disclosures
5. **Pitfall-Lücken-Disclosure → Königin-Lücken-Schluss**: Mit 3 fokussierten terminal-Calls (`find src -name "audit*log*"`, `grep process.env config/`, `git status --porcelain`) wurden die 2 echten Lücken vor Phase 3 geschlossen

## Was nicht funktioniert hat ❌

1. **Tech-Inspector-Biene hat ins read-only-Repo geschrieben** (`~/30-Library/hermes-v7/.hermes/phase1-tech-inspector-report.md`) → AGENTS.md-Konventionsbruch → **Pitfall #20**
2. **`process(action='wait', session_id='deleg_X')` schlug fehl** — delegation-IDs sind keine process-IDs → **Pitfall #21**
3. **Phase 3 Wave 1 mit A1+A2 parallel dispatcht** obwohl A2 von A1 abhängt → Race-Risk → **Pitfall #22**
4. **Plan-Biene sagte "2 unversionierte Files"** — Königin fand 3 (Off-by-one) → **Pitfall #24**
5. **Briefing sagte "LaneTask"** — Domain-Scout korrigierte zu "TaskCard" → **Pitfall #25**
6. **Welle 2: A3+A4-Worker-Bienen haben NICHT selbst commit'tet** — Working-tree war dirty als sie zurückkamen. Königin musste manuell committen + pushen → **Pitfall #26** (gepatcht in v1.5.1)

## Was Welle 2-3 zusätzlich gezeigt hat (über Welle 1 hinaus)

- **A3 hat defensiven Cache-Lookup implementiert:** `reconstructCachedArtifacts()` akzeptiert 3 Formen (nacktes Array / einzelnes Artifact / `{artifacts:[]}`-Wrapper) → robust gegen Migration
- **A3-Hook-Position:** Cache-Lookup in Schritt 2a (vor Tool-Profil-Check, nach Split-Brain-Guard) → Idempotency ist orthogonal zu Security, Cache-Hits sparen Security-Checks
- **A4 hat `intentHash` + `inputHash` als getrennte Felder** in `AuditEvent` — ReviewerA-Attestkette bleibt valide, kein Doppelt-Event
- **A4 hat `logCacheHit()` No-Op ohne Config** — defensive Variante, kein Event wenn Aufrufer keine Config übergibt
- **A5 hat Dual-Layer-Feature-Flag** implementiert (process.env > config > default off) — **Generalisierbares Pattern** für additive Hermes-V7-Features
- **A5 hat 35 NEUE Tests in 6 describe-Blöcken** geschrieben — Coverage 100% für neue Module
- **A5 hat `HERMES_IDEMPOTENCY_ENABLED` Truthy-Parser** mit case-insensitive + whitespace-trim + defensiv `false` bei unbekannten Werten — robust gegen Migrations-Schlampigkeit
- **Briefing-Verbesserung funktioniert:** Welle 3 hat self-committed weil Briefing explizit "PFLICHT" sagte → **Lösung für Pitfall #26 ist: Briefing-Verstärkung, nicht Biene-Disziplin**

## Spec-Updates (v1.4.0 → v1.5.0 → v1.5.1)

- **Pitfall #26** in SKILL.md ergänzt: Worker-Biene Self-Commit muss im Briefing explizit gefordert werden
- **Königin-Fallback-Pattern** dokumentiert: wenn Worker-Biene nicht committed → Königin committed manuell, dokumentiert als Königin-Commit im Diff-Bericht
- **Dual-Layer-Feature-Flag-Pattern** in `rolling-wave-live-test-pickup.md` ergänzt: env > config > default, truthy values `true|1|yes|on` (case-insensitive, whitespace-trimmed), defensiv `false` bei unbekannten Werten
- **Welle-1-Default = sequentiell** wenn A→B-Dependency existiert (gilt für A1→A2; A3∥A4 sind ok weil nur A2-abhängig)
- **Briefing-Must-Have** für Worker-Bienen ab Welle 2: "AM ENDE — PFLICHT: git add, git commit, git push" + "Im Self-Report: EXAKTE Commit-SHA"

## Königin-Fallback-Pattern (NEU v1.5.1, proven Hermes-V7 Welle 2)

**Symptom:** Worker-Biene returned mit "Done, tsc grün, Tests grün" aber `git status` zeigt modified files. Working-tree ist dirty.

**Sofort-Fix:**
```bash
cd <repo>
git add <files>
git -c user.email='queen-bee@hermes-v7.local' -c user.name='Yuno-Queen-Bee' \
  commit -m "<type>(<scope>): <was-die-Biene-gemacht-hat>

Welle N: A_n wurde als Worker-Biene dispatched, tsc grün, Tests grün,
aber kein self-commit. Königin resolved."
git push origin <branch>
```

**Im Königin-Diff-Bericht:** Commit als "Königin-Commit" markieren, nicht als Biene-Commit. Spur-Klarheit ist wichtiger als Schuldzuweisung.

**Generalisierungs-Lesson:** Briefing-Verstärkung ("PFLICHT: git commit + push") > Biene-Disziplin-Erwartung. Welle 3 hat das befolgt, Welle 4 wird's befolgen.

## Eval-Status (v1.5.1)

- ✅ Test durchgeführt (Hermes-V7 Mission-B, 2026-07-13, Phase 0.5 → Phase 3 Welle 4 läuft)
- ✅ Was lief gut (5 Punkte oben + Welle 2-3 zusätzlich: defensiver Cache-Lookup, intentHash-Attestkette, Dual-Layer-Feature-Flag, 35 neue Tests, Briefing-Verbesserung funktioniert)
- ✅ Was lief nicht (6 Punkte oben — Pitfalls #20-26)
- ✅ Was anpassen (Pitfalls #20-26 in Skill aufgenommen, Dual-Layer-Flag-Pattern dokumentiert, Briefing-Must-Have-Sektion für Self-Commit, Königin-Fallback-Pattern)
- 🟡 **Fix werden oder zurück zu 🅱️? — TEIL-Fix, aber STARKES Signal:** Skill v1.5.1 aktualisiert, 🅲️ bleibt formal in Evaluation-Mode bis 3 echte Missionen durch sind. **Aber:** Welle 3 (Self-Commit) zeigt, dass die Mitigation funktioniert. Eval-Status verbessert von "Welle 1 lief" auf "Welle 1-3 lief, Welle 4 läuft" — substantiell besser validiert. **Mission-B ist die erste echte 🅲️-Mission, der Test ist nicht gescheitert — die Pattern-Reife ist da.**

## Folge-Aktionen (für die Königin nach Phase 4)

1. **Skill-Library-Cross-Check:** Ist die Pitfalls-Cheatsheet (35 Pitfalls) konsistent mit den neuen #20-25 im Cluster-Patterns-Skill? Wenn nicht, welche Pitfalls gehören in beide?
2. **Spec-Re-Read:** Nach jeder Mission die rolling-wave-live-test-pickup.md mit den neuen Lessons updaten
3. **Issue-Vorlage vorbereiten:** GitHub Issue #2 Template für Idempotenz-Key Patch mit Phase-4-Diff als Body
4. **Mnemosyne-Update:** Memory-Items `[evaluation-mode]` + `[dispatch-pattern]` updaten wenn Mission abgeschlossen

## Verwandte Files

- **SKILL.md** (Pitfalls #20-25)
- **references/rolling-wave-live-test-pickup.md** (Spec v1.4.0, vor diesem Live-Test geschrieben)
- **Mnemosyne-Items:** `[dispatch-pattern]` (id=abaa5f6309f05697), `[evaluation-mode]` (id=8df2aa3bb2c52b7e)
- **Plan-Datei:** `~/.hermes/cache/delegation/subagent-summary-0-20260713_123843_760070.txt` (Plan-Biene-Output)