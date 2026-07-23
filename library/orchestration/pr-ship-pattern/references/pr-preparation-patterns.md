# PR-Preparation Patterns (NEU 2026-07-13, proven Hermes-V7 Mission-B)

Zwei kleine, aber wertvolle Patterns die sich beim ersten 🅲️-Live-Test bewährt haben.
Beide gehören in Phase 6 (Push → PR → Merge) und Phase 7 (Post-Merge-Doku) des
`pr-ship-pattern`-Workflows.

---

## Pattern A: PR-Body im Branch committen (`.hermes/PR-BODY-<id>.md`)

**Trigger:** Feature-Branch hat ≥ 3 Commits oder komplexe Acceptance-Criteria.
Klassische PR-Bodies (manuell in GitHub UI eintippen) gehen verloren wenn:
- Branch lokal gelöscht wird bevor der PR gemerged ist
- Mehrere Iterationen nötig sind und der Body jedes Mal neu getippt werden muss
- Audit-Trail benötigt wird ("was war der ursprüngliche Plan?")
- `gh pr create` ohne `--body-file` flag benutzt wird und der Body zu lang ist

**Pattern:**
1. A6 (oder vergleichbarer Subagent) erstellt `<repo>/.hermes/PR-BODY-<id>.md`
   mit vollem PR-Description-Text
2. File wird in den Feature-Branch committed (zusammen mit den Code-Commits)
3. Beim PR-Create via `gh pr create --body-file .hermes/PR-BODY-<id>.md` referenzieren
4. Nach PR-Merge: PR-Body bleibt als Audit-Trail im Branch-Historie erhalten

**Proven (2026-07-13, Hermes-V7 Mission-B):**
- `.hermes/PR-BODY-A6.md` (4.6KB, 102 Zeilen) wurde in Welle 4 (A6-Biene) erstellt
- Enthielt: Verifikations-Evidenz, Coverage-Tabelle, Dateien-Tabelle, Rollback-Pfad
- Nach allen 4 Commits war PR-Body in Branch-Historie verfügbar
- Beim späteren `gh pr create` Body-File-Referenz möglich

**Vorteile:**
- Kein Datenverlust bei Branch-Recycling
- Diff-fähig (PR-Body-Änderungen sind in `git log -p` sichtbar)
- Audit-Trail: "was war der Plan?" = `git show <commit>:.hermes/PR-BODY-<id>.md`
- Code-Reviewer können PR-Body-Änderungen reviewen

**Anti-Pattern:** PR-Body als GitHub-Issue-Comment oder Wiki-Page → nicht versioniert, geht verloren.

---

## Pattern B: GitHub Issue-Numbering Reality (NICHT "Issue #2" annehmen)

**Trigger:** Issue-Tracking-Plan im Briefing sagt "Issue #N" oder "Issue #<feature>".

**Reality:** GitHub nummeriert Issues **fortlaufend global pro Repository**, nicht nach
Projekt/Milestone. "Issue #2 für Idempotenz-Key" wird zu Issue #12 wenn das Repo
schon 11 Issues hat (von anderen Projekten/Tests/Orphan-Issues).

**Konsequenz im Hermes-V7-Live-Test:**
- Issue-Vorlage sagte "Issue #2 für Idempotenz-Key" (in Anlehnung an Issue #1 = closed)
- GitHub-Realität: bekam **#12** weil 11 vorherige Issues existierten
- Verwechslungs-Risk: Skill-Doku + Issue-Referenzen + Plan-Biene-Output reden von "#2",
  GitHub-Render zeigt "#12" → Diskrepanz im Audit-Trail

**Fix (generalisiert):**

1. **NIEMALS** "Issue #N" als festen Identifier in Plänen/Briefings verwenden
2. Stattdessen: **Issue-Title als kanonische Referenz** ("Idempotency-Key support for TaskCard")
3. **Erst nach GitHub-Create:** echte Issue-Nummer in den Plan zurückpatchen
4. **PR-Title-Convention:** "Closes #<N>" oder "Closes <title-fragment>" verwenden,
   GitHub matched beides

**Briefing-Template (für Issue-Tracking-bezogene Briefings):**

```markdown
## Issue-Tracking
- Issue-Title (kanonisch): "Idempotency-Key support for TaskCard (P0)"
- Issue wird ERST im Workflow erstellt, NICHT vorher
- Im Plan/Commit-Messages: "Issue-Title-fragment" statt "#2" oder "#N"
- Nach Issue-Create: echte #N in PR-Body und Related-Links referenzieren
```

**Proven Workaround (Hermes-V7 2026-07-13):**
- Plan-Biene-Output sagte "Issue #2" 
- A6-Biene (PR-Body-Ersteller) sagte "Issue #2" in PR-Body
- Tatsächliche GitHub-Issue war #12
- Diff-Bericht dokumentierte die Diskrepanz als Königin-Pitfall-Fund (Pitfall-#26-variante)

**Proaktive Königin-Pflicht:** Nach Issue-Create sofort `gh issue view <title-fragment> --json number,title` ausführen und die echte Nummer in alle verwandten Docs (PR-Body, Mnemosyne-Items, Diff-Bericht) zurückpatchen.

---

## Integration in `pr-ship-pattern` (Workflow-Updates)

**Phase 6 (Push → PR → Merge):**
- Vor `gh pr create`: prüfen ob `.hermes/PR-BODY-*.md` im Branch existiert
- Wenn ja: `--body-file` flag benutzen
- Wenn nein: nur bei 1-Commit-PRs OK, sonst Pattern A anwenden

**Phase 7 (Post-Merge-Doku):**
- PR-Body bleibt im Branch-History (Pattern A Vorteil)
- Issue-Numbering-Diskrepanz im `~/docs/system/pr-ship-<name>-<date>/` dokumentieren
- Mnemosyne-Item mit `valid_until` für Follow-up-Tracking setzen

## Verwandte Pitfalls

- `multi-agent-pitfalls-cheatsheet` Pitfall #5: "Subagent says 'fixed' but file unchanged" — Pattern A löst das für PR-Body
- `multi-agent-pitfalls-cheatsheet` Pitfall #33: Frontmatter-Quoting — gleicher YAML-Parsing-Risk bei Issue-Frontmatter
- `multi-agent-cluster-patterns` Spec v1.5.1 Pitfall #26: Self-Commit-Pflicht — Pattern A funktioniert nur wenn Branch-Commits auch committed wurden
