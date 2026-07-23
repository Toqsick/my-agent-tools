# Obsidian Vault Scaffold — Verzeichnis-Aufbau & MOC-Pattern

> Begleitung zu `scripts/scaffold-julian-ivanov-vault.sh` und für die Frage
> „wie legt man ein KI-Betriebssystem-Vault von Hand an?".
> Stand 2026-07-05 (Yuno Session: RTX 5060 Performance-Tuning Vault-Aufbau).

## Vault-Pfad auflösen — die volle Leiter

Wenn du nicht weißt, wo der Vault liegt, geh top-down:

```bash
# 1. dokumentierte Env-Variable
echo "OBSIDIAN_VAULT_PATH=${OBSIDIAN_VAULT_PATH:-UNSET}"

# 2. kanonischer Fallback (existiert auf DE-System oft nicht!)
ls -d ~/Documents/Obsidian\ Vault 2>/dev/null

# 3. Firmenweite Suche — deckt Linux (Snap/Flatpak), macOS, Custom-Setups ab
find ~ -maxdepth 4 -type d -iname "*obsidian*" 2>/dev/null

# 4. Obsidian-Config nach registrierten Vaults untersuchen
grep -r "vault" ~/.config/obsidian 2>/dev/null | head
# (Flatpak: ~/.var/app/md.obsidian.Obsidian/config/obsidian/)
```

**Häufigster Fail-Case:** env-var ist leer UND `~/Documents/Obsidian Vault` existiert nicht
(z. B. auf deutscher Zorin-Ubuntu-Installation ist es `Dokumente/Obsidian Vault`,
auf macOS anderswo). Wenn die Suche mehrere Kandidaten zurückgibt (Vault-Root +
`.obsidian`-Config + Sk-Addons), ist das **übergeordnete Verzeichnis mit einer
`.obsidian/`-Unterordner** der Vault-Root — den nimmst du.

## Julian-Ivanov-8-Ordner-Struktur (DE-Variante mit Nummern-Präfix)

```
~/Dokumente/Obsidian Vault/
├── MOC - Home.md                      # Hub mit Dataview-Queries
├── Willkommen.md                      # Obsidian-Default (kann weg)
├── 01 Kontext/                        # Onboarding-Material
├── 02 Inbox/                          # Schnelle Notizen
├── 03 Projekte/                       # Aktive Vorhaben
│   └── <Projekt-Name>/
│       ├── README.md                  # Hub-Status
│       ├── Plan - <Thema>.md          # Befehle, Stufen
│       ├── CHANGELOG.md               # Eintrag-Vorlage pro Aktion
│       └── Troubleshooting - <Thema>.md  # Risiko-Szenarien
├── 04 Bereiche/                       # Lebensbereiche
├── 05 Ressourcen/                     # Skripte, How-tos
├── 06 Daily Notes/                    # YYYY-MM-DD.md
├── 07 Archiv/                         # abgeschlossen
└── 08 Anhaenge/                       # Bilder, PDFs, Binärdateien
```

**Ohne Nummern-Präfix** (Julian-Original, englisch-lokalisierte Systeme):
einfach die führende Zwei weg.

## MOC - Home (Hub-Seite mit Dataview)

Datei `MOC - Home.md` in Vault-Root anlegen, sobald die Ordnerstruktur steht.
Dataview-Plugin muss installiert sein (`Settings → Community plugins → Dataview → Enable`):

```markdown
---
tags:
  - moc
  - hub
  - navigation
---

# MOC — Home (Vault-Übersicht)

> Willkommen im Vault. 8-Ordner-Struktur, aufgesetzt am YYYY-MM-DD.

## Die 8 Ordner

| # | Ordner | Zweck |
|---|---|---|
| 01 | `01 Kontext/` | Onboarding-Material: Hardware-Stand, Profil, CLAUDE.md-Spiegel |
| 02 | `02 Inbox/` | Schnelle Notizen, Dinge die später sortiert werden |
| 03 | `03 Projekte/` | Längerfristige Vorhaben |
| 04 | `04 Bereiche/` | Lebensbereiche (z. B. Gaming, Dev, System-Wartung) |
| 05 | `05 Ressourcen/` | Externe Wissens-Sammlungen |
| 06 | `06 Daily Notes/` | Tagesjournale (YYYY-MM-DD.md) |
| 07 | `07 Archiv/` | Alte / abgeschlossene Notizen |
| 08 | `08 Anhaenge/` | Bilder, PDFs, Binärdateien |

## Aktive Projekte

\`\`\`dataview
LIST from "03 Projekte"
WHERE contains(file.tags, "projekt")
SORT file.name ASC
\`\`\`

## Quick Links

- [[MOC - Home]] (diese Seite)
- [[Willkommen]] (Obsidian-Default)
```

## Per-Projekt 4-Notizen-Split (Pattern)

Für jedes Projekt unter `03 Projekte/<Name>/` werden **vier** Notizen angelegt.
Nicht eine — vier. Begründung: jede Notiz ist in Obsidian eine eigene Seite,
somit einzeln verlinkbar, einzeln durchsuchbar, einzeln navigierbar; lange
Walls-of-Text zerstören die Browserbarkeit.

### README.md (Hub)

```markdown
---
tags:
  - projekt
  - <topic>
status: in-arbeit | abgeschlossen | archiviert
prioritaet: hoch | mittel | niedrig
erstellt: YYYY-MM-DD
---

# <Projektname> — Projekt-Hub

> Eindeutiges Zielbild in 1–2 Sätzen.

## Status

| Stufe | Status |
|---|---|
| <Komponente 1> | offen / done |
| <Komponente 2> | offen / done |

## Struktur dieses Projekts

\`\`\`dataview
LIST from "03 Projekte/<Name>"
SORT file.name ASC
\`\`\`

## Quick-Wins / Top-5

1. ...
2. ...
```

### Plan - <Thema>.md (vollständiger Plan)

```markdown
---
tags:
  - plan
  - anleitung
prioritaet:
  - rot: ["<stufe-X>", ...]
  - orange: [...]
  - gelb: [...]
---

# Plan — <Thema>

> Vollständiger, priorisierter Stufen-Plan.

**Legende:** 🟥 kritisch · 🟧 hoch · 🟨 mittel · 🟩 optional

---

## 🟥 STUFE 1 — <Name>

### Schritte

\`\`\`bash
# Befehle hier
\`\`\`

| Nutzen | Risiko | Rollback |
|---|---|---|
| ... | ... | ... |
```

### CHANGELOG.md (Eintrag-Vorlage)

```markdown
---
tags:
  - changelog
projekt: "[[README]]"
---

# CHANGELOG — <Projektname>

> Vorlage pro Schritt: **Datum · Stufe · Befehl · Erwartung · Vorher/Nachher · Rollback**.

---

## Vorlage

\`\`\`markdown
## YYYY-MM-DD · Stufe X.Y · <Kurztitel>

- **Befehl:** `...`
- **Erwartung:** ...
- **Vorher (Messwert):** ...
- **Nachher (Messwert):** ...
- **Reboot nötig:** ...
- **Rollback-Befehl:** `...`
- **Bemerkung:** ...
\`\`\`

---

## Stufen-Logger

| Datum | Stufe | Status |
|---|---|---|
| YYYY-MM-DD | 1.1 <Titel> | offen |
```

### Troubleshooting - <Thema>.md (Risiko-Szenarien)

```markdown
---
tags:
  - troubleshooting
  - risikomanagement
projekt: "[[README]]"
risiken:
  - R1: <Name>
  - R2: <Name>
---

# Troubleshooting — <Thema>

## Tabelle: Häufige Fehler

| Fehler | Symptom | Ursache | Quick-Fix |
|---|---|---|---|

## Eskalations-Baum

\`\`\`
Symptom
├─ Stufe 1
├─ Stufe 2
└─ Stufe 3
\`\`\`
```

## Wikilinks zwischen den vier Notizen

- README: → Plan, → CHANGELOG, → Troubleshooting
- Plan: → CHANGELOG (Vorlage), → Troubleshooting (Querverweis)
- CHANGELOG: → Plan (Befehle), → Troubleshooting (Eskalation)
- Troubleshooting: → README (Hub)

Obsidian rendert die `[[Note Name]]`-Links als Auto-Suggestion, sobald die
Zieldatei existiert — auch mit Bindestrichen im Dateinamen, solange der
Wikilink-Text exakt dem Dateinamen entspricht.
