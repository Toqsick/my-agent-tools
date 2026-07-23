# Pattern 11 — Vault-Doku-vs-Plugin-State-Drift Audit (Proven 2026-07-10)

Wenn die Vault-Doku etwas über den Plugin-Zustand behauptet (z. B. "Dataview installiert", "Templater aktiv"), aber die Realität in `.obsidian/` davon abweicht — oder umgekehrt — ist diese Anleitung zuständig.

## Warum ein eigener Pattern

Backlink-/Orphan-Audit (Pattern 6/7) zählen Link-Topologie. Der Drift-Audit prüft die **Konsistenz zwischen Vault-Doku-Aussagen und drei Schichten Plugin-State**. Symptom: User oder Königin meldet "Doku-Drift" als P0-Ticket (z. B. `W1-A: Dataview-Doku-Drift fixen`).

## Drei-Schichten-Plugin-State-Modell

Eine Aussage wie "Plugin X ist aktiv" hat **drei verschiedene Wahrheits-Ebenen**. Alle drei abklären, bevor ein Befund steht.

| # | Schicht | Datei / Pfad | Was sie sagt |
|---|---|---|---|
| (a) | **Config-Flag** | `<vault>/.obsidian/community-plugins.json` (Array von Plugin-IDs) | "Diese Plugins sind in Obsidian aktiviert" — controlled by Restricted-Mode-Toggle + manuelle Enable-Clicks |
| (b) | **Physische Installation** | `<vault>/.obsidian/plugins/<id>/{manifest.json, main.js, styles.css, data.json}` | "Diese Dateien existieren auf der Festplatte" — controlled by Obsidian-Browse → Install |
| (c) | **Runtime-Aktivierung** | Obsidian-Interner State, **nicht datei-sichtbar** | "JS-Queries ON, Restricted Mode OFF, Refresh-Intervall konfiguriert" — controlled by Obsidian-Settings-UI |

**Faustregel:** (a) + (b) zusammen ≠ garantiert (c). Erst nach Obsidian-Restart + manuellem Check in `Settings → Community Plugins` ist (c) verifizierbar. Bei Drift-Berichten immer explizit nennen, welche Schicht gemeint ist.

## Fall-Klassifikation A / B / C

Vor jedem Patch entscheiden, welche der drei Konstellationen vorliegt:

| Fall | Plugin-State | Doku behauptet | Aktion |
|---|---|---|---|
| **A** | installiert + aktiviert | "Plugin nicht installiert" / "deaktiviert" | **PATCH DOKU** (behaupten ≥ Realität → falsche Aussage entfernen) |
| **B** | nicht installiert + deaktiviert | "Plugin aktiv" / "läuft" | **ENABLEN** (Doku ≥ Realität → User-Aktion nötig, dokumentieren) |
| **C** | ungewiss (z. B. nur Config ohne Files, oder vice versa) | widersprüchlich | **DOKUMENTIEREN + NICHT PATCHEN** → Basti fragen, oder `obsidian-restart + check` anstoßen |

**Verwechslungsfalle:** "Config-flag enabled" allein reicht NICHT für "Plugin installiert". Beispiel: Bastis `community-plugins.json` listet `"dataview"` UND `.obsidian/plugins/dataview/{manifest.json, main.js}` existieren → Plugin VOLLSTÄNDIG installiert + aktiviert (Fall A). Hätte nur eines von beiden existiert → Fall C.

## Verifikations-Rezepte (Read-only)

Diese Befehle IMMER vor einem Befund ausführen — Pitfall #19 zeigt, warum.

```bash
# 1. Plugins-Liste physisch vorhanden (KORREKT — listet echte Verzeichnisse)
ls -la "<vault>/.obsidian/plugins/"

# NICHT verlassen auf:
search_files pattern="obsidian-dataview" target="files" path="<vault>/.obsidian/plugins"
# → liefert 0 Treffer, obwohl Verzeichnis existiert (Tool-Limitation, Pitfall #19)
```

```bash
# 2. Config-Aktivierung
cat "<vault>/.obsidian/community-plugins.json"
# → Array von Strings. Plugin-IDs müssen EXAKT matchen (case-sensitive: "dataview" ≠ "Dataview")
```

```bash
# 3. Plugin-Manifest (Version + ID-Verifikation)
cat "<vault>/.obsidian/plugins/<id>/manifest.json" | head -10
# Felder: id, name, version, minAppVersion, author
```

```bash
# 4. main.js-Größe = Sanity-Check, ob echtes Bundle oder nur Stub
stat -c '%s %n' "<vault>/.obsidian/plugins/<id>/main.js"
# < 50 KB → vermutlich nur Stub / Placeholder
```

## Permission-Tabelle (Was darf ich patchen?)

Vault-Edits unterliegen drei Zonen mit unterschiedlichem Freiheitsgrad. **Vor jedem Patch** die Ziel-Datei lokalisieren und Zone prüfen:

| Zone | Beispiele | Patchbar ohne Basti-Genehmigung? |
|---|---|---|
| **Erlaubt** | `<vault>/.obsidian/*`, `~/.claude/skills/**`, `~/.hermes/skills/**` | ✅ Ja |
| **Bedingt erlaubt** | `~/.claude/skills/second-brain/**`, `~/.hermes/skills/**` Doku-Skills | ✅ Ja, solange Skill selbst nicht "Tabu-Maintainer" ist |
| **Tabu (Basti only)** | `<vault>/01 Kontext/**`, **MOCs** (`MOC - *.md`, `**/MOC - *.md`) | ❌ Nein — Inbox-first-Regel + Working-Agreement §X |

**Tabu-Drift-Fix-Workaround:** Wenn der falsche Hinweis in einer MOC steht, NICHT die MOC patchen — stattdessen:
1. Inventur an Königin/Basti liefern (welche MOCs, welche Zeile, welche Falsch-Aussage)
2. Erlaubte-Zone-Patches ausführen (z. B. `~/.hermes/skills/`)
3. Patch-Welle-2 in Bastis Auftrag abwarten

**Konflikt-Detection:** Wenn eine Falschbehauptung NUR in Tabu-Zonen existiert → **Fall C greift**, kein auto-Patch. Königin muss genehmigen.

## Workflow: Drift-Fix-Run (Königin)

### Phase 1 — Drift-Detection (READ-ONLY)

```bash
# 1. Plugin-Live-State (siehe Verifikations-Rezepte oben)
ls -la "<vault>/.obsidian/plugins/"
cat "<vault>/.obsidian/community-plugins.json"

# 2. Doku-Behauptungen im Vault (Drift-Quellen)
search_files pattern="<Plugin-Name>" path="<vault>" target="content" context=2

# 3. Doku-Behauptungen in erlaubten Skills (~/.hermes/skills/, ~/.claude/skills/)
search_files pattern="<Plugin-Name>" path="~/.hermes/skills" target="content"
search_files pattern="<Plugin-Name>" path="~/.claude/skills" target="content"

# 4. Klassifizieren: für jeden Treffer Fall A / B / C zuordnen + Zone prüfen
```

### Phase 2 — Patch-Decision-Matrix

Für jeden Drift-Fall:

| Fall | Zone | Aktion |
|---|---|---|
| A | Erlaubt | Patch Doku sofort (Pitfall #19 beachten — search_files vs. ls verifizieren!) |
| A | Bedingt erlaubt | Patch, dann Skill-Wartung dokumentieren |
| A | Tabu | Inventur an Basti, KEIN Patch |
| B | egal | ENABLEN, in Reply an Basti dokumentieren (User-Aktion) |
| C | egal | Doku der Lücke an Basti, KEIN auto-Patch |

### Phase 3 — Patch-Ausführung

```bash
# Beispiel: Pitfall #1 in obsidian-vault-quality-audit Skill — Plugin-Status präzisieren
# ALT: "| 1 | Dataview-Plugin nicht installiert → Reports leer | Fallback-Python-Script …"
# NEU: "| 1 | Dataview-Plugin deaktiviert oder JS-Queries off → Reports leer | Fallback-Python-Script …; Plugin-Status prüfen via community-plugins.json + manifest.json |"

# Niemals write_file auf existierende Skills — immer patch mit alt_string/neu_string.
# Diff muss im Bericht erscheinen.
```

### Phase 4 — Verify-Post-Conditions

Nach jedem Drift-Fix-Run:

- [ ] `ls -la .obsidian/plugins/` zeigt weiterhin alle erwarteten Plugin-Dirs
- [ ] `grep -r "Plugin nicht installiert" ~/.hermes/skills/` liefert 0 Treffer in erlaubter Zone
- [ ] Tabu-Zonen-Drift als Königin-Inventur dokumentiert mit: Datei + Zeile + Falsch-Aussage
- [ ] JS-Queries-Runtime-Status explizit als "(c) ungewiss — Obsidian-Restart + Settings-Check nötig" markiert

## Pitfalls (zusätzlich zu SKILL.md #19, #20)

### P-11.1 — Inbox-Verwechslung

`02 Inbox/` zählt NICHT zur "Tabu-MOC"-Zone, ist aber per Vault-Konvention **Inbox-first** — d.h. neue Notizen gehen dorthin, bestehende werden editiert. `MOC - Inbox.md` ist trotz Ordnernamens ein MOC → tabu.

### P-11.2 — Reine SKILL-Doku vs. Snapshot-Doku

Manche Skills haben **historisch korrekte** Aussagen, die heute falsch sind. Beispiel: `system-documentation/SKILL.md` Z.160 sagt "Dataview-Plugin MUSS manuell aktiviert werden" — historisch korrekt (Installationsanleitung), heute irreführend. Belassen weil Workflow-Erinnerung, nicht Drift zwingend patchen.

### P-11.3 — Plugin-ID vs. Verzeichnisname driftet manchmal

Beispiel: `community-plugins.json` listet `"calendar-beta"`, aber Verzeichnis heißt `calendar` (kein `-beta`-Suffix). Pitfall #19 / Verifikations-Rezept #3 mit `manifest.json` zeigt die Wahrheit: `id`-Feld im Manifest ist die Source-of-Truth.

### P-11.4 — JS-Queries-Setting nicht datei-sichtbar

`Enable JavaScript Queries` lebt in Obsidian-`localStorage`, nicht in `.obsidian/`. Drift-Audit kann nur "Config enabled + Files vorhanden" verifizieren — nicht den Runtime-Toggle. Königin muss im Reply an Basti explizit erwähnen, dass diese Spalte unbestätigt bleibt.

## Beispiel-Realfall (W1-A, 2026-07-10)

**Symptom:** Basti reportet P0-Ticket: "Dataview-Doku-Drift fixen"
**Inventur:**
- Plugin-State: `community-plugins.json` listet `"dataview"` ✅, `.obsidian/plugins/dataview/{main.js 2.3MB, manifest.json v0.5.68, styles.css, data.json}` ✅ → Fall A
- Doku-Behauptungen in Vault: 10 MOCs sagen `<!-- Hinweis: Dataview-Plugin ist aktuell nicht installiert. -->` (alle tabu, Basti-Genehmigung nötig)
- Doku-Behauptungen in erlaubten Skills: 3 Stellen in `~/.hermes/skills/` (patchbar)

**Durchgeführte Patches:**
1. `~/.hermes/skills/note-taking/obsidian-vault-quality-audit/SKILL.md` Z.243 (Pitfall-Tabelle Zeile 1)
2. `~/.hermes/skills/note-taking/vault-architecture/references/phase8-workflow.md` Z.43 (Don't-Liste Item 8)
3. `~/.hermes/skills/obsidian-vault/vault-gemini-cluster-worker/SKILL.md` Z.129 (Known Quirks)
4. `~/.hermes/skills/note-taking/obsidian-vault-quality-audit/references/final-verification-pattern.md` Z.70 (Plugin-Count 3→4)

**Verbleibende Tabu-Zonen-Drift:** 10 MOC-Kommentare (Inventur an Königin — Patch-Welle-2 in Bastis Auftrag).

**Verify-Resultat:**
```
grep -r "Plugin nicht installiert" ~/.hermes/skills/  → 0 Treffer ✓
ls .obsidian/plugins/                                 → 4 dirs ✓
cat dataview/manifest.json | head -5                 → id=dataview, v0.5.68 ✓
```

**Lessons:**
- Pitfall #19 (search_files-Limitation) hätte den Run fast mit falschem Befund beendet — Verifikation per `ls` rettete.
- Tabu-Zonen-Disziplin verhinderte überstürzte MOC-Patches (10 Drift-Quellen noch offen, dokumentiert).
- Plugin-Count-Correction (3 → 4) fand einen separaten, vorher nicht vermuteten Drift.
