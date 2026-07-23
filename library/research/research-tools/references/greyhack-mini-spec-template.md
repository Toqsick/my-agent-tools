# GreyHack Mini-Spec Template

Use this template after Awesome-Hacking research produces a tool candidate and before touching GreyScript implementation files.

## Header

```markdown
# Mini-Spec <tool-name>

**Datum:** YYYY-MM-DD
**Status:** Spec only — keine Implementation.
**Branch:** Feature-Branch von `develop`, niemals `main` ohne explizite Freigabe.
**Safety:** Spiel-interne Methode; keine realen Exploit-, Payload-, Credential- oder Netzwerkziele.
```

## Sections

1. **Ziel** — Was das Tool im Spiel leisten soll.
2. **Warum zuerst** — Welche Research- oder P1-P4-Lücke es schließt.
3. **Abhängigkeiten** — P0-Kernhelpers zuerst, instabile Tools nicht übernehmen.
4. **Vorgeschlagene Datei** — Neuer Pfad, z.B. `src/tools/recon_lite.src`.
5. **API / Funktionen** — Names, Inputs, Outputs, Fehlerverhalten.
6. **CLI** — Parameter, Help, Usage, leere Listen.
7. **Safety-Grenzen** — Erlaubt vs. nicht erlaubt.
8. **Tests / Build** — Testdatei und `./scripts/ci-build.sh --out-dir /tmp/greybel-build ...`.
9. **Implementierungsaufgaben** — kleine, sequenzielle Schritte.
10. **Erfolgskriterien** — Build sauber, keine `main`-Änderung, keine realen Angriffsinhalte.

## GreyHack Defaults

- P0 hat Vorrang vor P1-P4.
- `develop` nicht direkt beschmutzen; Experimente auf Feature-Branch von `develop`.
- `main` nur nach expliziter User-Freigabe.
- Neue Tools zuerst als Spec dokumentieren, dann implementieren.
- Wenn bestehende Tools instabil sind, neue Datei erstellen statt komplexes Legacy-Tool zu überschreiben.
- Keine realen Exploit-PoCs, CVE-Ketten, Credential-Listen, Payloads oder externen Netzwerkziele übernehmen.
