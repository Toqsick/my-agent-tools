# Stufe-3-Schwarm Worker 3 Lessons — "Wertvollster Worker"

Session 2026-07-09 (pvhphecd70Y Run) hat empirisch gezeigt: **Worker 3
(Faktencheck) ist der wertvollste Worker im 4-Worker-Bienen-Schwarm.**

## Empirische Evidenz (pvhphecd70Y Run)

| Worker | Output | Findings geliefert | Davon NEU (nicht von Worker 1+2 abgedeckt) |
|--------|--------|--------------------|---------------------------------------------|
| 1 (Inhalt) | 4964 Wörter, 9 Inhalt-Fixes | 9 Korrekturen | nur sprachliche (Wortbrüche, Anmolde, züllen) |
| 2 (Stil) | 4902 Wörter, 69 Eigenname-Fixes | 69 Korrekturen | nur Eigennamen (Cloud→Claude, T-Max→tmux, etc.) |
| 3 (Faktencheck) | 13 KB Report | **27 Findings, davon 12 kritisch** | **14 NEUE Patterns die Worker 1+2 NICHT kannten** |
| 4 (Merger) | 4905 Wörter, NULL Restfehler | kombiniert + Post-Verify | fängt Restfehler aus den 3 vorigen |

## Welche 14 NEUEN Patterns Worker 3 gefunden hat

Diese waren NICHT in der Heuristik-Liste (`references/known-hearing-errors.md`),
bevor Worker 3 sie identifiziert hat:

1. `SLRemote` → `/remote Control` (Slash-Command-Verhunzung)
2. `slem Control` → `Remote Control` (phonetisch kollabiert)
3. `SlashG` → `/goal` (Endsilben-Kollaps)
4. `Slash Clear` → `/clear` (ausgeschriebene Form)
5. `Rustinger` → `Hostinger` (Endsilben-Vertauschung)
6. `Hey Claud` → `Hey Claude` (Eigenname-Anrede verhunzt)
7. `Hey Clud` → `Hey Claude`
8. `Clode` → `Claude`
9. `Cludier` → `Claude`
10. `Clot` → `Claude` (nur im Tech-Kontext, nicht "blood clot")
11. `closed starten` → `claude starten` (Kommandozeile)
12. `Anmoldeformular` → `Anmeldeformular` (sachlicher Hörfehler)
13. `züllen` → `füllen`
14. `erknüpfen` → `verknüpfen`
15. `debugen` → `debuggen`
16. `Impressummatte` → `Impressumsmaske`

Plus 4 Ambiguitäten dokumentiert die konservativ belassen wurden:
- `KFM2 Plan` → vermutlich `KVM 2 Plan` (Hostinger Tarif)
- `Resent` → vermutlich `Resend` (E-Mail-API)
- `[musik]` → vermutlich Auto-Mode-Setting
- `Textag` → vermutlich `Text` oder `Textvorschlag`

## Warum Worker 3 diese Lücken findet, Worker 1+2 aber nicht

**Worker 1 (Inhalt)** operiert auf Sprach-Ebene:
- Satzzeichen, Wortbrüche, Absatz-Struktur
- Hat KEINEN Zugang zur Heuristik-Liste für Eigennamen
- Hat KEINEN Cross-Reference-Mechanismus zur Description

**Worker 2 (Stil)** operiert auf Heuristik-Ebene:
- Bekannte Patterns aus `context.md` werden abgearbeitet
- **Limitation**: kennt nur Patterns die im Briefing stehen
- Findet keine NEUEN Patterns, die der Briefing-Autor nicht kannte

**Worker 3 (Faktencheck)** operiert auf Discovery-Ebene:
- Liest die **Description** (vom Briefing-Autor unbewusst übersehene Features)
- Liest den **Raw-Caption**-Blob (zeigt was Auto-Caption wirklich sagt)
- Macht **grep-Sweep** über das polierte Transkript mit Pattern-Familien
- Macht **Timestamp-Cross-Check** (passt Minute X zu Topic Y?)
- Macht **Tag-Cross-Reference** (welche Description-Tags kommen im Transkript vor?)

→ Worker 3 ist **konzeptionell** der einzige Worker der gegen die Description
   arbeitet. Worker 1+2 arbeiten rein am Transkript-Text. Deshalb findet
   Worker 3 zwangsläufig Dinge die die anderen nicht sehen können.

## Methodik-Erkenntnis: Worker 3 hat drei Reports-Typen

| Report-Typ | Was er liefert | Wert für Merger |
|------------|----------------|------------------|
| **Description-Cross-Check** | Welche Description-Features kommen im Transkript vor? | Mittel — wenn was fehlt, ist es entweder ein Hörfehler oder der Sprecher hat das Feature nicht erwähnt (Creator-Recht) |
| **Resthörfehler-Check** | Welche bekannten Hörfehler sind noch im polierten Transkript? | **Sehr hoch** — direkte Fix-Liste für Merger |
| **Zusätzliche Findings** | Patterns die der Briefing-Autor nicht kannte | **Höchster Wert** — diese werden in `known-hearing-errors.md` für künftige Sessions eingepflegt |

## Praxis-Empfehlung für künftige Schwärme

1. **Worker 3 NIEMALS überspringen**, auch wenn Worker 2 stark wirkt. Worker 3 ist die
   einzige systematische Lücken-Suche.
2. **Worker 3 MUSS Zugang zur Description UND zum Raw-Caption-Blob haben** — sonst
   kann er nicht cross-referenzieren.
3. **Worker 3 Output NIEMALS nur als "Report" behandeln** — der Report muss in den
   Merger-Flow integriert werden, sonst verpufft der Wert.
4. **Worker 3 Findings mit `references/known-hearing-errors.md` synchronisieren** —
   jeder neue Fund wird dort eingepflegt für künftige Sessions.

## Skill-Update nach Worker-3-Findings

Nach jedem Schwarm-Run mit substantiellen Worker-3-Findings:

1. Neue Patterns in `references/known-hearing-errors.md` POST_MERGE_PATTERNS ergänzen
2. SKILL.md Heuristik-Liste (5c) erweitern
3. Session-History-Block am Ende von `known-hearing-errors.md` aktualisieren
4. Memory-Update mit den neuen Pattern-Counts

## Königinnen-Disziplin: Worker 3 ernst nehmen

Auch wenn Worker 3 nur ein Report-Worker ist (kein Polisher), ist sein Beitrag
quantitativ und qualitativ oft größer als der von Worker 1+2 zusammen. Die
typische 4-Worker-Verteilung im Output:

| Worker | Output-Größe | User-sichtbarer Wert |
|--------|--------------|---------------------|
| 1 (Inhalt) | ~30 KB polierter Text | mittel — Sprachfluss-Verbesserung |
| 2 (Stil) | ~30 KB polierter Text + Fix-Liste | hoch — Eigennamen-Korrektur |
| 3 (Faktencheck) | ~13 KB Report | **am höchsten** — Lücken-Findung + Skill-Hardening |
| 4 (Merger) | ~30 KB konsolidierter Text | mittel — Kombination |

→ Der Faktencheck-Report ist **das wertvollste Artefakt** im ganzen Schwarm.

## Siehe auch

- `youtube-transcript-saver/SKILL.md` → Stufe 3: Multi-Agent-Pipeline
- `references/known-hearing-errors.md` → Pattern-Datenbank
- `references/merger-methodology.md` → Wie Worker 4 die Findings integriert
- `templates/stufe3_schwarm_delegation_prompts.md` → Copy-pastefertiger Faktencheck-Briefing