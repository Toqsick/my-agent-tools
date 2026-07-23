# Compact Fix PR Body — Reales Beispiel

> GreyHack null-guard Fixes (2026-07-04)
> Branch: `fix/merge-main-cluster-fixes-into-develop`
> 2 Dateien, +30/-10, Build 19/19 PASS

---

## Zusammenfassung

Bug-Hunt via 3 parallelen Subagent-Scouts (mxwrap, recon_lite, recon).
Von ~30 gemeldeten GreyScript-1.5.1-Befunden waren 5 echt, der Rest
false positives (typisch: Property-vs-Method-Irrtum bei `is_closed`,
`.len`, `.port_number`).

**Build:** 19/19 PASS vor und nach den Fixes — reine Defensiv-Erweiterung,
kein Verhaltensänderung im Happy-Path.

## Was ändert sich

### `src/tools/recon_lite.src`

| Zeile | Fix |
|-------|-----|
| 34-37 | `_recon_lite_ts` → `_recon_lite_source_ip` umbenannt (Funktion liefert `local_ip`, keinen Zeitstempel) |
| 99    | Report-Field-Key `"ts"` → `"src_ip"` (ehrlicher Name, JSON-stabil für Consumer) |
| 150-153 | `params == null` Guard am CLI-Entry — Crash-Fix bei `import_code` als Library |
| 161   | Operator-Precedence `or`/`and` in save-Trigger explizit geklammert: `cli_bool_flag(args, "save") or (args.len >= 3 and args[2] == "save")` |

### `src/tools/mxwrap.src`

| Zeile | Fix |
|-------|-----|
| 147   | `run_exploit` Return-Guard: `typeof(kshell) != "shell"` (vorher `== "string"` — fehlerhaft, alle nicht-shell returns als string angenommen) |
| 152-156 | `host_computer == null` Guard nach `run_exploit` (verhindert null-ref) |
| 205-227 | `pc == null` Guard in `mx_patch` + lokales `_chmod_or_warn` Helper — chmod-Denials erzeugen jetzt `warn()` statt silent failure |

## Tests

```
$ bash scripts/ci-build.sh
Results: 19 passed, 0 failed out of 19
Build OK
```

## Out of scope (false positives der Scouts, NICHT angewendet)

| Fund | Status | Begründung |
|------|--------|------------|
| `is_closed`/`.len`/`.port_number` ohne `()` | FP | In GreyScript 1.5.1 sind das Properties, keine Methods |
| `typeof(x) == "string"` | FP | `typeof` ist real und gibt `"string"` zurück |
| Umlaute in Kommentaren | FP | GS 1.5.1 parsed UTF-8 in Kommentaren klaglos |
| `port_number` method-vs-property | FP | Siehe erster Eintrag |

## Kontext

- Branch: `fix/merge-main-cluster-fixes-into-develop` (von `develop` abgezweigt)
- Vorgänger: `18c8a6a` (greybel-js 3.7.x CLI-Subcommand)
- Doku: `docs/greyhack-pipeline.md` Abschnitt 4 (Bug-Patterns & Fixes)
- Cluster: passt zu #41 (Cluster-1: negativer Index) — gleicher Defensiv-Stil

## Checkliste

- [x] Build grün (19/19)
- [x] Keine neuen Warnings
- [x] Doku-Konvention deutsch
- [x] Scope minimal: nur die 5 echten Funde
- [x] Cluster-Referenz dokumentiert
- [ ] In-Game smoke-test (manuell, portmon + recon_lite in der Game-CLI)
- [ ] Reviewer: bitte speziell die `typeof != "shell"` Änderung gegen GreyScript-1.5.1-Reference checken
