# Subagent-Improvisation-Pattern — Worked Example

> Concrete Phase-4-Beispiel (2026-07-05) von Subagent K (deleg_f40ae395).

## Spec vs. Better Choice

| Aspekt | Spec (Cluster K Briefing) | Tatsächliche Ausführung |
|---|---|---|
| **Anweisung** | Erstelle 2 neue Notes: `Obsidian-Plugin-Status-Live.md` + `Dataview-Install-Anleitung.md` | Patch der bestehenden `Obsidian - Plugin-Setup.md` (2,8 KB → 7,6 KB) |
| **Files geschrieben** | 2 neue Notes | 0 neue Notes, 1 gepatchter existierender |
| **Zeit** | ~61s | ~61s (keine Zeitersparnis — Qualitätsentscheidung) |
| **Qualität** | Fragmentiertes Plugin-Wissen auf 3 Notes | Alle Plugin-Infos an einem Ort |

## Warum die Improvisation besser war

1. **Keine Duplikation** — Die bestehende `Obsidian - Plugin-Setup.md` hatte bereits die Überschrift "Installierte Plugins" + Setup-Infos. Zwei neue Notes hätten zu 3 parallelen Plugin-Wissensquellen geführt.
2. **Nutzer findet alles an einem Ort** — Statt "Wo war nochmal die Dataview-Anleitung?" → "Ich schau in die Plugin-Setup.md".
3. **Kein Datenverlust** — Alle geplanten Inhalte (Live-Status, Install-Schritte, Stolperfallen) sind in der gepatchten Datei enthalten.
4. **Future-Proof** — Nächster Plugin wird in derselben Datei ergänzt.

## Wie subagent die Entscheidung traf

Basierend auf dem Read-Schritt (Phase-B-Check-in-vault-architecture-Principle: "Jede Note verdient ihren Platz"): die bestehende Note war dünn (2,8 KB) und hatte Lücken → sie anreichern war strukturell besser als neue Dateien zu schaffen.

## Trigger für künftige Subagents

Im Briefing sollte ein Satz stehen wie:

> "Du darfst von der Spec abweichen, wenn (a) du vorher gelesen hast dass\* eine bessere Lösung existiert, (b) keine Daten zerstört werden, (c) die Abweichung im Summary dokumentiert wird."

## Siehe auch

- `obsidian-vault-cluster-operations` SKILL.md — Pattern 6: Subagent-Improvisation-Permission
- `05 Ressourcen/Obsidian - Plugin-Setup.md` (Vault-Datei) — das konkrete Resultat
- `note-taking/vault-architecture` SKILL.md — Phase 4 Metriken
