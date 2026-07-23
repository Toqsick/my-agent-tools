#!/usr/bin/env bash
# Julian-Ivanov-8-Ordner-Obsidian-Vault-Scaffold
# Legt die deutsche Variante (mit numerischem Präfix) in einem existierenden
# Vault-Verzeichnis an und schreibt eine MOC-Hub-Seite.
#
# Verwendung:
#   ./scaffold-julian-ivanov-vault.sh /pfad/zum/vault
#   ./scaffold-julian-ivanov-vault.sh                    # nutzt $OBSIDIAN_VAULT_PATH
#
# Idempotent: bestehende Ordner werden nicht überschrieben, MOC nur angelegt
# wenn noch nicht da. Backup alter MOC unter *.bak-YYYYMMDD-HHMMSS.

set -euo pipefail

VAULT_PATH="${1:-${OBSIDIAN_VAULT_PATH:-}}"

if [[ -z "$VAULT_PATH" ]]; then
  echo "Fehler: Kein Vault-Pfad angegeben." >&2
  echo "  Aufruf: $0 /pfad/zum/vault" >&2
  echo "  oder:  OBSIDIAN_VAULT_PATH=/pfad/zum/vault $0" >&2
  exit 1
fi

if [[ ! -d "$VAULT_PATH" ]]; then
  echo "Fehler: Verzeichnis existiert nicht: $VAULT_PATH" >&2
  echo "  Lege es vorher an oder übergebe den Pfad zu einem existierenden Vault-Root." >&2
  exit 1
fi

cd "$VAULT_PATH"

echo "→ Vault-Root: $(pwd)"

# 8 Ordner mit deutschem Nummern-Präfix anlegen (idempotent)
ORDNER=(
  "01 Kontext"
  "02 Inbox"
  "03 Projekte"
  "04 Bereiche"
  "05 Ressourcen"
  "06 Daily Notes"
  "07 Archiv"
  "08 Anhaenge"
)
for d in "${ORDNER[@]}"; do
  if [[ -d "$d" ]]; then
    echo "  ✓ $d (existiert)"
  else
    mkdir -p "$d"
    echo "  + $d (angelegt)"
  fi
done

# MOC - Home.md anlegen oder Backup machen
MOC_FILE="MOC - Home.md"
if [[ -f "$MOC_FILE" ]]; then
  BACKUP="${MOC_FILE}.bak-$(date +%Y%m%d-%H%M%S)"
  cp "$MOC_FILE" "$BACKUP"
  echo "  ⚠ $MOC_FILE existiert → Backup: $BACKUP"
fi

cat > "$MOC_FILE" <<'MOC'
---
tags:
  - moc
  - hub
  - navigation
---

# MOC — Home (Vault-Übersicht)

> Willkommen im Vault. Julian-Ivanov-8-Ordner-Struktur, aufgesetzt am YYYY-MM-DD
> (Datum manuell eintragen).

## Die 8 Ordner

| # | Ordner | Zweck |
|---|---|---|
| 01 | `01 Kontext/` | Onboarding-Material: Hardware-Stand, Profil, CLAUDE.md-Spiegel |
| 02 | `02 Inbox/` | Schnelle Notizen, Dinge die später sortiert werden |
| 03 | `03 Projekte/` | Längerfristige Vorhaben — pro Projekt ein Unterordner mit 4 Notizen |
| 04 | `04 Bereiche/` | Lebensbereiche (z. B. Gaming, Dev, System-Wartung) |
| 05 | `05 Ressourcen/` | Externe Wissens-Sammlungen, Skripte, How-tos |
| 06 | `06 Daily Notes/` | Tagesjournale (YYYY-MM-DD.md) |
| 07 | `07 Archiv/` | Alte / abgeschlossene Notizen |
| 08 | `08 Anhaenge/` | Bilder, PDFs, Binärdateien |

## Aktive Projekte

```dataview
LIST from "03 Projekte"
WHERE contains(file.tags, "projekt")
SORT file.name ASC
```

## Letzte Daily Notes

```dataview
LIST from "06 Daily Notes"
SORT file.name DESC
LIMIT 7
```

## Quick Links

- [[MOC - Home]] (diese Seite)
- [[Willkommen]] (Obsidian-Default, kann irgendwann weg)
MOC

echo "  ✓ $MOC_FILE angelegt"
echo ""
echo "→ Fertig. Empfohlene nächste Schritte:"
echo "    1. Dataview-Plugin aktivieren (Settings → Community plugins)"
echo "    2. Erstes Projekt unter 03 Projekte/ anlegen (4-Notizen-Split)"
echo "    3. Daily Notes heute starten unter 06 Daily Notes/$(date +%Y-%m-%d).md"
