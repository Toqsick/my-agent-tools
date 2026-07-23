# Wiki Cross-Link Strategy (NEU 2026-07-22)

Seit PR #77 (gemerged 2026-07-22) hat `Toqsick/greyscripts` ein **Wiki mit 65 Pages**.
Es gibt jetzt **zwei parallele Doku-Layer**:

1. **Obsidian Vault** (`~/Dokumente/Obsidian Vault/05 Ressourcen/System-Doku/GreyHack/`)
2. **Repo-Wiki** (`https://github.com/Toqsick/greyscripts/wiki`)

Dieses Dokument beschreibt die **Cross-Link-Strategie** zwischen beiden Layern.

## Warum zwei Layer?

| Layer | Zweck | Audience |
|-------|-------|----------|
| Obsidian Vault | Strategische Wissensbasis, persönliche Reflexion, Working-Notes | Basti intern |
| Repo-Wiki | Community-facing, Developer-Dokumentation, API-Reference | Public / Contributors |

Vault ist die **primäre** Doku (Working Agreement: "Vault-Notes sind Source-of-Truth"),
Repo-Wiki ist die **abgeleitete** für externe Sichtbarkeit.

## Cross-Link-Inventar (Stand 2026-07-22)

### Vault-Notes die Repo-Inhalt spiegeln

| Vault-Note | Repo-Quelle | Wiki-Mirror |
|-----------|-------------|-------------|
| [[GreyScript-Sprachreferenz-2026-07-14]] | `greyscript-language.md` (referenziert im Skill) | Ja (vermutlich `Wiki/Home.md` oder `GreyScript-Language.md`) |
| [[GreyHack-Hacking-Cookbook-2026-07-14]] | `in-game-hacking-workflow.md`, `ctf-mission-workflow.md` | Ja |
| [[GreyHack-Lib-Katalog-2026-07-14]] | `greyscript-api-reference.md`, `lib_core/` | Ja |
| [[GreyHack-Audit-2026-07-14]] | `db-internal-filesystem-audit.md` + Audit-Befunde | Ja |
| [[GreyHack-Starter-Kit-2026-07-14]] | `feature/starter-kit-2026-07-14` Branch, PR #63 | Ja (PR-Referenz) |
| [[GreyHack-Tool-Arsenal-Audit-2026-07-14]] | `greyhack-tools/` Inventur | Teilweise |
| [[GreyHack-Tool-Workflow-CheatSheet-2026-07-14]] | `yuno-project-versions.md` + `greyhack-tools/NAVIGATION.md` | Ja |
| [[GreyHack-Known-Bugs-Katalog-2026-07-14]] | `known-bugs.md`, `bug-fix-history.md` | Ja |

### Cross-Links die explizit dokumentiert sind

- [[GreyHack-Repo-Struktur-Update-2026-07-22]] — dieses Update-Dokument,
  mit allen 5 gemergten PRs (#63, #66, #67, #68, #77)
- [[GreyHack - Werkzeugkasten & Patterns]] — bestehende Doku (W28-Wiki-Stand)
- [[04 Bereiche/Gaming - GreyHack]] — Bereichs-MOC mit Wiki-Links auf die 8
  obigen Notes

## Wiki-Mirror-Strategie

**Wenn Repo-Wiki aktualisiert wird:**
1. Wiki-Seite in PR-Review mit Vault-Note als Cross-Reference
2. Vault-Note bekommt `Wiki-Mirror: <URL>` Eintrag im Frontmatter
3. Working Agreement §Doku-Discipline: "Wiki-Mirror-Links sind
   keine Duplikation, sondern explizite Cross-Links"

**Wenn Vault-Note aktualisiert wird:**
1. Bei substanziellen Änderungen (Pattern-Update, neue Tool-Version):
   Wiki-Seite auf Repo prüfen
2. Falls Wiki veraltet: PR im Repo öffnen
3. Pattern-Governance-Score (≥90/100) gilt für beide Layer

## Stale-Detection-Workflow

Bei jedem Repo-Update oder Vault-Update mit GreyHack-Bezug:

```bash
# 1. Wiki-Pages holen
gh api repos/Toqsick/greyscripts/wiki/pages > /tmp/greyhack-wiki.json

# 2. Vault-Notes mit Repo-Stand verlinkt?
ls "/home/bratan/Dokumente/Obsidian Vault/05 Ressourcen/System-Doku/GreyHack/"

# 3. Cross-Check: Vault-Notes deren Wiki-Mirror im Repo fehlt
for note in GreyScript-Sprachreferenz-2026-07-14 \
            GreyHack-Hacking-Cookbook-2026-07-14; do
  if ! grep -q "$note" /tmp/greyhack-wiki.json; then
    echo "STALE: $note hat Wiki-Mirror-Drift"
  fi
done
```

## Pattern-Governance-Integration

Beide Layer müssen die Pattern-Governance-Konventionen einhalten:

- **Unterstrich-API** in allen Code-Beispielen
- **Score ≥90/100** für promoted Patterns
- **`make check-all`** als lokaler CI-Entry-Point

Vault-Notes mit Code-Beispielen sollten die gleiche Konvention nutzen,
damit Copy-Paste zwischen Vault → Repo funktioniert.

## Lessons aus PR #77

1. **0 Deletions + 6129 Additions** = additives Wiki-Setup, kein Rewrite
2. **65 Pages** in einem PR ist viel — vermutlich Script-generiert
3. **0 broken Cross-Links** belegt dass Pattern-Governance + Recon-Hardening greift
4. **Wiki-Initial ist Architektur-Schritt**, nicht Doku-Append

## Empfehlung für nächste Schritte

1. Wiki-Stand vs. Vault-Stand monatlich cross-checken (Cron? manuell?)
2. Bei jedem Pattern-Promotion: Wiki-Page mit-aktualisieren
3. Working Agreement: "Wiki-Cross-Links sind Teil der Quality-Gates"
4. Stale-Pattern-Sweep für Vault-Notes aus W28 (vor PR #66) planen