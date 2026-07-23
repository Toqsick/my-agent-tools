# Greydecode 1.5 Extended Edition — Session Notes

Extracted from PDF at `/home/bratan/Downloads/Greydecode 1.5 Extended Edition.pdf` (682 lines).
Basis: MiniScript 1.5.1, Grey Hack build 0.8.4490a+.

## Document Structure (for future re-reference)

1. Einordnung — what this doc is, builds on "Clean Edition"
2. Wie GreyScript gedacht werden sollte — three-layer model
3. Die wichtigsten Sprachregeln — language pitfalls (strings, numbers, lists, maps, etc.)
4. Script-Design — small / modular / productive; one script = one job
5. Das Standard-Template — canonical script skeleton
6. Shell, Computer, File, Router verstehen — object semantics
7. Crypto, Metaxploit, AptClient verstehen — system libraries
8. Fehlerbehandlung als Grundprinzip — "if you only internalize one section, this"
9. Core-Library ausführlich erklärt — render/fail/warn/ok/requireParam/validIP/getFile
10. Praxis-Skripte — portscan / routerinfo / smtp_enum / scp_upload / wifi_crack
11. Metaxploit-Workflow Schritt für Schritt — 6 Stufen
12. Code Smells und bessere Alternativen — 5 common anti-patterns
13. Lernpfad — study order
14. Kurzreferenz — quick reference

## Key Quotes

> "Das Grundgerüst eines Skripts sollte langweilig sein. Das ist etwas Gutes. Langweilige Struktur bedeutet: erwartbar, stabil, wartbar."

> "Viele verwechseln 'modular' mit 'mehr Dateien, mehr Komplexität'. Das Gegenteil ist der Fall: Ein kleines Tool ist leichter zu prüfen, leichter zu reparieren und leichter neu zu kombinieren."

> "Du weißt nicht vorher sicher, was zurückkommt. Genau deshalb verlangt die Doku ausdrücklich eine Typprüfung mit typeof."

## Design Philosophy

- **Early exit** beats nested ifs. `if not valid then fail(...)` keeps main logic clean.
- **Capture context once**: `shell = get_shell; pc = shell.host_computer` at the top.
- **Help text is mandatory**: tools that can't self-explain are half-finished.
- **Parameters captured to locals**: `ip = params[^0]` then use `ip`, not `params[^0]` scattered everywhere.
- **Render() standardizes headers**: every tool prints a consistent framed title.

## Anti-Patterns Explicitly Called Out

| Smell | Fix |
|-------|-----|
| Repeated `get_shell.host_computer` | Cache to `shell`/`pc` |
| God-script doing scan+ssh+copy+exploit+menu | One script, one job |
| Late error detection | Check return value immediately |
| Clever string formatting | Simple lines, short headers |
| No `--help` path | Always include it |

## Specific API Insights

- `smtp_user_list()` is the canonical example of "check three cases": null, string (error), list.
- `aireplay()` returns the cap path on success OR an error string on failure — never assume it's a file object.
- `lib.overflow()` can return Shell, Computer, File, String, Number, or null — routing the result by `typeof()` is mandatory.
- `scp()` returns `1` on success, not the path; always `if result != 1 then fail(...)`.
- `chmod()` returns `1` on success — not the new permission code.
- `indexOf()` may return `null` (not `-1`) on miss — check with `if idx != null then list.remove(idx)`.

## Suggested Learning Path (from the doc)

1. Language basics (strings, lists, maps, functions)
2. Shell/Computer/File/Router objects
3. One-task tools (portscan, routerinfo)
4. Core library extraction (lib_core)
5. Crypto workflows (WiFi, SMTP)
6. Metaxploit workflow
7. Modular toolset + launcher
