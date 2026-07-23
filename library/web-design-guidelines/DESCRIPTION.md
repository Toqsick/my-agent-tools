# web-design-guidelines — Skill-Beschreibung

**Name:** web-design-guidelines
**Version:** 1.0.0
**Autor:** Vercel
**Quelle:** https://github.com/vercel-labs/agent-skills
**Installs:** 420K+ (skills.sh Leaderboard #2)
**Lizenz:** MIT

## Was ist das?

Review-Tool für UI Code gegen Vercels Web Interface Guidelines. Prüft HTML/CSS/JS Dateien gegen einen umfangreichen Regelwerk für Web-Design, Accessibility und UX.

## Wann nutzen?

- "Review mein UI" / "Check Accessibility" / "Audit Design"
- "Review UX" / "Check meine Seite gegen Best Practices"
- Code-Reviews für Web-Projekte
- Accessibility-Audits

## Wie funktioniert's?

1. **Guidelines laden** — Die latest Rules von GitHub fetchen:
   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```
2. **Dateien lesen** — Die angegebenen UI-Dateien einlesen
3. **Regeln anwenden** — Gegen alle Guidelines prüfen
4. **Findings ausgeben** — Im `file:line` Format mit konkreten Verstößen

## Guidelines Source

Die Guidelines werden vor jedem Review frisch von GitHub geladen. Sie enthalten:
- Design-Regeln (Layout, Typografie, Farben)
- Accessibility-Regeln (ARIA, Kontrast, Keyboard-Navigation)
- UX-Regeln (Loading States, Error Handling, Feedback)
- Output-Format-Anweisungen

## Verwendung

```bash
# Guidelines laden
curl -sL "https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"

# Dann UI-Dateien prüfen
```

## Output-Format

Findings werden im Format `file:line: [RULE] Beschreibung` ausgeben.

## Hinweis für Hermes

Das Skill ist primär für Claude Code/Cursor gedacht. Für Hermes nutze:
- `web_extract` für Webseiten-Analyse
- `browser` für interaktive Seiten
- Manuelle Reviews mit den Guidelines als Referenz
