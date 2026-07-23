# Anleitung — Wie du diesen Skill nutzt

> Schritt-für-Schritt-Anleitung für die 13 Perplexity-Folge-Fragen aus dem Yuno-Anon-TikTok-Business.

## TL;DR (1-Satz)

Lade den passenden Phase-X-Prompt aus `references/`, ergänze die nötigen Daten, pasten in Perplexity Deep Research, warte 3-5 Min, integriere die Antwort in dein Repo.

---

## 1. Wann nutze ich welche Frage?

Schau in die **Quick-Reference-Card** in der SKILL.md oder in den Phasen-Übersichten (`01-Phase-A-pre-launch.md`, `02-Phase-B-during-test.md`, etc.). Jede Phase hat eine Tabelle:

```
| Datei | Frage | Trigger | Output |
```

Wenn du nicht sicher bist: Lade den Skill und frag Yuno ("Yuno, welche Perplexity-Frage passt zu meinem aktuellen Stand?").

---

## 2. Standard-Workflow (Schritt-für-Schritt)

### Schritt 1 — Frage wählen
Entscheide: Welche Phase-Datei passt zu meinem aktuellen Stand?
- Pre-Launch → `references/01-phase-a-pre-launch.md`
- Tag 5-14 (Test läuft) → `references/02-phase-b-during-test.md`
- Tag 14+ (Entscheidung) → `references/03-phase-c-post-test.md`
- Monat 2-6 (Skalierung) → `references/04-phase-d-scale-mode.md`

### Schritt 2 — Konkrete Prompt-Datei laden
Lade die `.md` der konkreten Frage (z.B. `A1-niche-white-space.md`).

Du siehst darin:
- **Wann diese Frage stellen** (Trigger-Bedingungen)
- **Daten die du mitgeben musst** (Variablen zum Ausfüllen)
- **Den Prompt** (im Code-Block, 1:1 copy-paste-ready)
- **Output-Format** (was Perplexity zurückgeben sollte)
- **Was du mit der Antwort machst** (Integration in Repo)
- **Pitfalls** (häufige Fehler)

### Schritt 3 — Prompt mit Daten füllen
Ersetze alle `[PLATZHALTER]` im Prompt mit deinen konkreten Daten.

Beispiel:
- Vorher: `[paste top 5 from master prompt]`
- Nachher: `1. Kreditkarten (Navy+Gold, @finanzfreiraum), 2. Produktivität (Schwarz+Orange, @fokusfabrik), 3. Geld sparen für Anfänger, 4. Meal Prep, 5. Home Office Setup`

### Schritt 4 — In Perplexity einfügen
1. Gehe zu https://www.perplexity.ai/ (Deep Research Modus)
2. Füge den fertigen Prompt ein
3. Klicke "Submit" / "Research"
4. Warte 3-5 Min (Perplexity Deep Research braucht Zeit)

### Schritt 5 — Antwort verarbeiten
1. Lese die Perplexity-Antwort kritisch (siehe Pitfalls in der jeweiligen Frage-Datei)
2. Verifiziere alle @-Handles selbst auf TikTok
3. Pasten die Kern-Insights in Yunos Chat
4. Yuno übersetzt auf Deutsch, schlägt Action-Items vor, integriert in:
   - `pitch-variants.json` (neue Hook-/Pitch-Varianten)
   - `brand-system-{nische}.json` (Design-Updates)
   - `canva-bulk-create-{nische}.csv` (neue Posts)
   - Tracking-Sheet (Entscheidungen)

### Schritt 6 — Action innerhalb 24h
**Wichtig:** Jeder Perplexity-Run sollte genau EINE umsetzbare Aktion produzieren, die du innerhalb 24h umsetzt. "Insight generiert aber nichts gemacht" = verschwendete Research-Zeit. (Perplexity-Output ist Pre-Flight-Check, nicht Strategie.)

---

## 3. Übersicht aller 13 Fragen

### Phase A — Pre-Launch (JETZT)

| # | Datei | Zweck |
|---|---|---|
| A1 | `A1-niche-white-space.md` | Top-3-Nischen mit echtem White-Space finden |
| A2 | `A2-visual-trend-audit.md` | 2026-Design-Trends für faceless TikTok |
| A3 | `A3-algorithmus-wortliste.md` | Safe-Word-Liste gegen Shadowban |

### Phase B — During Test (Tag 1-14)

| # | Datei | Zweck |
|---|---|---|
| B1 | `B1-halbzeit-hook-audit.md` | Top-Hook-Patterns + Posts 8-14 planen |
| B2 | `B2-save-rate-diagnose.md` | Warum Save-Rate flach + A/B-Test-Varianten |
| B3 | `B3-comment-mining.md` | Product-Ideen aus echten Kommentaren |

### Phase C — Post-Test Decision (Tag 14+)

| # | Datei | Zweck |
|---|---|---|
| C1 | `C1-kill-vs-double-down.md` | Skalieren oder Killen? Entscheidung + 30-Tage-Plan |
| C2 | `C2-winning-post-forensik.md` | Winning-Post-Pattern extrahieren + Template |

### Phase D — Scale Mode (Monat 2-6)

| # | Datei | Zweck |
|---|---|---|
| D1 | `D1-content-multiplikation.md` | 30 Posts/Woche ohne Burnout |
| D2 | `D2-monetization-deep-dive.md` | Funnel + Pricing + Platform-Wahl |
| D3 | `D3-cross-niche-pivot.md` | Account #2 Nische wählen |
| D4 | `D4-risk-audit-pre-scale.md` | Compliance + Burnout + TikTok-Risk |

---

## 4. Zeitplan-Empfehlung

### Woche 0 (JETZT)
- Master-Prompt (Initial-Session) → 1 Run
- A1 + A2 parallel → 2 Runs (1 Tag)
- A3 vor erstem Upload → 1 Run (vor Tag 1 des Tests)

### Tag 5-7 des 14-Tage-Tests
- B1 → 1 Run

### Tag 7-10 des 14-Tage-Tests
- B2 (falls Save-Rate flach) → 1 Run
- B3 (parallel wenn Comments kommen) → 1 Run

### Tag 14 (Final-Decision)
- C1 → 1 Run
- C2 (direkt danach) → 1 Run

### Monat 2
- D1 → 1 Run

### Monat 2-3
- D2 → 1 Run

### Monat 3-4
- D3 → 1 Run (falls Account #2 geplant)

### Monat 4-6
- D4 → 1 Run (vor Job-Exit-Entscheidung)

**Total Perplexity-Runs: ~13-15 über 6 Monate** — das ist die minimale Research-Last für daten-getriebenes Skalieren.

---

## 5. Wie du nicht in die "Research-Falle" läufst

Die größte Gefahr bei Perplexity-Research ist **endlose Insight-Sammlung ohne Action**. Hier die Anti-Pattern:

❌ **Falsch:** "Lass mich nochmal A1 fragen, vielleicht sind die Sub-Nischen anders" (ohne neuen Input)
✅ **Richtig:** Einmal A1, Entscheidung treffen, Posts draften, hochladen, B1 nach Tag 5-7

❌ **Falsch:** "Perplexity sagt €29 Pricing, aber lass mich nochmal D2 fragen mit anderen Zahlen" (ohne Test)
✅ **Richtig:** Pricing-Entscheidung treffen, 1 Monat testen, bei Bedarf D2 nochmal mit echten Conversion-Daten

❌ **Falsch:** "12 Perplexity-Runs bevor ich den ersten Post hochlade" (over-research)
✅ **Richtig:** Master + A1 + A3 = 3 Runs bevor erster Upload. A2 + B-Fragen kommen später.

**Faustregel:** Pro Perplexity-Run sollte genau 1 Action-Item resultieren, das innerhalb 24h umgesetzt wird.

---

## 6. Tipps für bessere Perplexity-Results

1. **Konkrete Zahlen mitgeben**: Statt "Save-Rate ist flach" → "Save-Rate 0.8% über 7 Posts, Durchschnitt 1200 Views, höchster Post 2400 Views"
2. **@-Handles selbst verifizieren**: Perplexity halluziniert manchmal Accounts
3. **"2026" + "current data" + "DACH"** immer explizit nennen (sonst zieht Perplexity 2022-US-Listen)
4. **Erst den Master-Prompt, dann die Folgenschritte** — sonst fragst du A1 ohne Top-5 zu haben
5. **Bei großen Perplexity-Antworten**: Nur die Top-3-Insights pasten, nicht die ganze Wand

---

## 7. Verwandte Skills

- `tiktok-design-assistant` — Generiert Brand-System + Canva-CSV + Pitch-Varianten (Output-Integration für die meisten A/B/C/D-Prompts)
- `tiktok-business-self-improve` — Cron-Job Mo-Fr 19:00 für Self-Improve-Loop
- `self-improving` — Yuno lernt aus Fehlern (gleiche Logik für dich als Solo-Operator)

---

## 8. Wenn etwas nicht klappt

- **Perplexity antwortet mit 2022-Daten?** → Prompt schärfer machen, "EXCLUSIVELY 2026 data" ergänzen
- **Perplexity halluziniert @-Handles?** → Manuell verifizieren, Perplexity-Fundstellen mit deutschen Beispielen abgleichen
- **Perplexity empfiehlt was dir unsicher vorkommt?** → Frage 2-3 Tage später nochmal, vergleiche Antworten. Konsistente Antwort = wahrscheinlich korrekt. Widersprüchlich = mehr Daten sammeln.
- **Du weißt nicht welche Frage passt?** → Frag Yuno ("Yuno, basierend auf meinem Stand [X], welche Perplexity-Frage?"). Yuno lädt den Skill und schlägt vor.

---

## 9. Cross-Links

- Skill-Hauptfile: `~/.hermes/skills/creative/perplexity-followup-plan/SKILL.md`
- Kurzfassung in: `~/.hermes/skills/creative/tiktok-design-assistant/references/perplexity-research-framework.md`
- Projekt-MOC: `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business.md`
- Tracking-Sheet: `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business/14-Tage-Test-Tracking.md`