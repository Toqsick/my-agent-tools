# edge-cases.md — Edge-Case-Katalog (Detektion → Reaktion)

| # | Fall | Detektion | Reaktion |
|---|---|---|---|
| 1 | **Plan-Mode-Write-Block mitten im LAND** | Bash/Write verweigert mit plan-mode-Fehler | HALT; Resume-Note schreiben (Phase, PR-NR, was fehlt) und State so setzen, dass die Folge-Session mit re-autorisierten Writes genau dort fortsetzt. Fußangel aus pokerogue: ein LAND-Attempt starb so am 17.09. |
| 2 | **Branch-Protection 403 (privates Free-Repo)** | `merge-probe.sh` → 403 | agentenseitiges Watch+Squash ist first-class, kein Fehler. Probe-Ergebnis in WORKFLOW.md dokumentieren („nicht erneut danach suchen") |
| 3 | **gh `--auto -d` löscht Remote-Branch nicht** (cli#9073) | `git ls-remote --heads origin <branch>` nicht leer nach Merge | einmalig melden/löschen; im Loop-Output als bekannter Bug markieren |
| 4 | **Implementiert ≠ abgenommen** | Issue ist Abnahme-kritisch (Mensch-Abnahme laut Gate/Body) | Issue offen lassen; agent-log: „Implementation fertig (PR #X), Abnahme ausstehend". Auto-Close per „Closes" vermeiden |
| 5 | **Doc-Drift zwischen Regelwerken** | AGENTS.md sagt A, WORKFLOW.md sagt B (pokerogue: „Agent committet direkt auf main" vs. PR-Flow) | Nie still wählen: betroffene Datei benennen, Mensch entscheiden lassen, `gov:`-Fix-Commit mit DECISIONS-Eintrag |
| 6 | **Toter Vorwärtsverweis** | Doku behauptet, Datei/Tool existiere („emu_check.py läuft heute in CI") | Claims müssen Datei+Zeile zitieren; Plan-vs-Zustand trennen („Vorhaben von T-x.y", nicht Gegenwart). Beim Fund: Doku korrigieren, Issue anlegen |
| 7 | **Fake-Grün / Scheingrün** | Verify-Report verschleiert übersprungene Schritte (nur Exit-Code-Tabelle) | Report im Klartext: „target: ÜBERSPRUNGEN (keine Toolchain)"; Tabellenzeilen zählen nicht als Nachweis (pokerogue T-A.4-Befund) |
| 8 | **Rote Baseline** | Baseline-Verify Exit != 0 | Loop startet nicht. Baseline-Reparatur als eigener Fix-Loop (max. 5), sonst `blocked:` |
| 9 | **Neue Datei nicht in Build-Liste** | Verify bleibt grün, obwohl neue .cpp nie kompiliert (feste CORE_SOURCES/TEST_SOURCES-Listen) | 10-Sekunden-Gegenprobe: Syntaxfehler in die neue Datei → Verify muss rot werden; Listeneintrag in denselben Commit wie die Datei |
| 10 | **Golden-Vector-Selbstbestätigung** | Generator geändert + regeneriert adelt den Bug | Kategorie-Isolation (nur begründete Kategorien dürfen sich ändern, Rest byte-identisch) + Mutationstest (absichtliche Fehl-Mutation muss rot machen) + Versions-Bump |
| 11 | **Zwei Sessions, ein Repo** | `.dev-loop/lock` hält fremde session-id, jünger als 6 h | HALT mit Session-ID des Lock-Inhabers; Stale-Überschreibung erst nach 6 h oder mit `--force` |
| 12 | **Context-Verlust mid-Loop** (Kompaktion/Session-Ende) | State/agent-log jünger als die laufende Arbeit | Resume-Protokoll (state-contract.md): State lesen → agent-log lesen → Phase fortsetzen, Iterationszähler übernehmen — nie von Null |
| 13 | **CI rot nach Merge** | main rot nach agentenseitigem Merge (keine Queue) | `git revert --no-edit` auf main, Issue zurück in Frontier, Ursachen-Issue; pokerogue-M9-Präzedenz |
| 14 | **Rate-Limit / Bot-Loop** | gh-429, oder Bots triggern Bots | Backoff + kleinere Batches; nie Bot-Kommentare als Trigger werten (claude-code-action-Prinzip `exclude_comments_by_actor`); ein PR, ein Watch, ein Merge-Versuch |
| 15 | **CI baut anders als lokal** | CI-Artefakt ≠ lokal (md5/Verhalten) | Artefakt herunterladen, Summen vergleichen; Fail-closed statt stiller Fallbacks (pokerogue T-9.2: Ability-ID-Hash); environment-Parität als Issue |

## Übergreifende Haltung

Jeder dieser Fälle hat eine gemeinsame Wurzel: **ein Beweis, der lügt, multipliziert
sich durch den Loop** (pokerogue M-A-Titel, sinngemäß). Deshalb: Evidenz immer
vorbehaltlos zitierbar (Befehl, Exit-Code, Zahlen), HALTs sind billiger als
halbgemergte Vermutungen, und der agent-log ist die einzige Wahrheit über
Session-Grenzen.
