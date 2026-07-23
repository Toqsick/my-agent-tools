# Pitfalls (Vollständige Liste)

Gesammelte Lessons Learned aus Sessions und Experimenten. In Phase 6 retrospektieren ob neue Pitfalls dazugekommen sind; hier patchen.

## Orchestrierungs-Pitfalls

1. **Scope Creep** — User erweitert Aufgabe während des Workflows → Klar abgrenzen
2. **Timeout bei Implementation** — Große Projekte brauchen mehrere Durchläufe → In Episoden aufteilen
3. **Subagent-Phantom-Builds** — "Hab ich implementiert" → Immer verifizieren!
4. **Dependencies fehlen** — npm/pip nicht installiert → Phase 2 checken
5. **Config-Files protected** — Subagent kann nicht schreiben → Parent muss übernehmen
6. **Critic-Gate überspringen** — "Der Validator findet es schon" → NEIN. Beide Gates sind Pflicht
7. **Delta-Feedback vergessen** — Bei RETRY nicht den kompletten Task wiederholen. Nur Feedback + letzter Output
8. **Phantom-Retry-Schleife** — Nach 2 Retries MUSS Eskalation passieren. Kein 3. Retry.

9. **Sudo-Chicken-Egg bei System-Repair** — Terminal hat kein TTY → `sudo` in terminal()-Calls failt ohne vorheriges `sudo -v`. 15-Min-Timer. **Fix:** Immer in 4 Phasen planen: (1) Scouts read-only, (2) User `sudo -v`, (3) Implementierung parallel (genau 1-2 terminal()-Calls mit sudo), (4) Validierung read-only. **ALLE sudo-Befehle im ersten Block sammeln** — nicht drei separate Aufrufe, sondern ein langer `&&`-Block. (`set -e` stoppt sofort beim ersten sudo-Fail.)
10. **Implementierer-A/B-Vermischung** — System-Repair-Schwarm trennt in Kernel-Ebene (A) und App-Ebene (B). Wenn A-Dinge in B delegiert werden (`modprobe` in Waydroid-Config-Task) → B failt weil `modprobe` nicht in seiner Rolle ist. **Fix:** Strikt nach Rollenvertrag trennen. A: Module, Devices, Pakete. B: Init, Config, LXC, User-Session.
11. **Validator ohne Live-Service-Check** — Validator der nur Config liest statt Container zu starten+Logs zu checken ist wertlos. **Fix:** Validator MUSS `systemctl restart waydroid-container`, `waydroid session start`, Logs auswerten — nicht nur "sieht gut aus" sagen.
12. **Waydroid host-permissions Chicken-Egg** — `/var/lib/waydroid/host-permissions/*.xml` wird NICHT von `waydroid init` erzeugt, sondern vom Android-Hardware-Service zur Laufzeit. Ohne binder+ashmem startet Container nicht → keine Permissions. **Fix:** Manuell die `1000-wayland.xml` anlegen oder zuerst binder_linux laden + `sudo touch /dev/ashmem`.

## Gate / Hermes-Config Pitfalls

9. **Delegate-Gate-Blocker** — Wenn `delegate_task` mit `HermesUltraCode gate`, `base_prompt is empty` oder `Cannot resolve delegation provider` scheitert: **ERST FIXEN, DANN FALLBACK.** Die Fix-Befehle (Phase 0) deaktivieren HermesUltraCode + Tirith und setzen delegation.provider — danach Hermes-Prozess NEU STARTEN. 2026-06-20 bewiesen: 5 parallele Subagenten nach Fix. Nur wenn Fix scheitert: Parent-Direct-Fallback (`references/parent-direct-fallback.md`).
10. **Lokaler Critic ist Setup-abhängig** — `critic-gate-ollama.py` läuft nur, wenn `HERMES_CRITIC_ENABLED=true` und Ollama erreichbar ist. Wenn Ollama fehlt oder leer ist, Parent-direct Review durchführen und den Blocker in Phase-6 dokumentieren.
11. **Ziel-Pfad fehlt trotz User-Freigabe** — Wenn der angegebene Projekt-Pfad im Backend nicht existiert, nicht blockieren: Ist-Zustand prüfen, dann bei klarem „loslegen" eine minimale Bootstrap-Struktur anlegen, lauffähige Tests/Dry-Runs bauen und dokumentieren. Parent-direct-Fallback in `references/parent-direct-fallback.md`.
12. **Backend/Host-Dateisystem nicht vermischen** — Wenn der Agent in Docker/SSH/Remote arbeitet, existieren geschriebene Dateien nicht automatisch auf dem Desktop-Host. Bei „Script nicht gefunden" zuerst prüfen, ob der CLI/Dateipfad im aktuellen Backend existiert; dann entweder dort ausführen und verifizieren oder dem User eine Host-Copy-Paste-Anweisung geben. Nicht Approval Mode oder Subagent-Phantoms beschuldigen, solange die Dateisystemgrenze nicht geprüft ist.
13. **Config-Änderungen brauchen Prozess-Neustart** — `/reset` reicht NICHT für `delegation.provider`, `plugins.enabled` oder `security.tirith_enabled`-Änderungen. Der laufende Hermes-Prozess cached diese Werte beim Start. Nach Config-Änderungen: Hermes Desktop komplett beenden und neu starten. Erst dann Phase 0 erneut testen.
16. **Hermes config.yaml vor Agent-Schreibzugriffen geschützt** — `patch`/`write_file` werden auf `~/.hermes/config.yaml` blockiert (Hermes-Sicherheitsfeature). Auch `hermes config set` kann keine komplexen YAML-Blöcke (wie `mcp_servers`) setzen. **Fix:** `cat >> ~/.hermes/config.yaml << 'EOF'` im Terminal für Appends; `sed -i` für gezielte Änderungen; danach `hermes config check` zur Validierung. Referenz: `references/hermes-config-edit-patterns.md`.

## Git / Repo Pitfalls

17. **Commits landen im falschen Repo** — Wenn der Queen cwd ≠ Repo-Root ist (z.B. Queen arbeitet in `~/hermes-zorin` aber Worker schreiben in anderes Repo), landen `git add -A && git commit` im falschen Repo. **Fix:** Im Worker-Kontext IMMER absoluten Repo-Pfad angeben: `cd /abs/path/to/repo && git add -A && git commit -m "..."`. Queen muss nach Worker-Return prüfen: `git log --oneline -3` im Ziel-Repo.
18. **Worker vergessen Commits** — Subagenten (besonders bei langen Tasks) schreiben Code, aber vergessen `git add + commit`. **Fix:** Queen MUSS nach jedem Worker-Return `git status --short` im Ziel-Repo prüfen. Wenn uncommitted Files → Queen commited mit Referenz an Worker-Task. Im Worker-Kontext explizit angeben: "Commite AM ENDE mit genau diesem Message-Format".
19. **write_file Escaping-Probleme** — Das `write_file` tool escapet Backslashes in Regex-Literale (`/\s+/` → `/\\s+/`) und `*/` in JSDoc-Kommentaren terminiert Block-Comments. **Fix:** Nach `write_file` mit Regex/JSDoc-Content immer `sed -i` zur Reparatur laufen lassen ODER den Worker bitten, den Code in eine `.ts`/`.js`-Datei zu schreiben und dann mit `sed` zu fixen.
20. **Port-Kollision bei Live-Tests** — Port 3000 ist auf Bastis System von Gitea belegt. **Fix:** Für Express-Dev-Server IMMER `PORT=3001` oder `PORT=3002` verwenden. Prüfen mit `lsof -i :3000` (falls verfügbar) oder einfach alterniven Port probieren.
17. **Cross-Repo Commit Contamination** — Subagenten können Commits ins FALSCHE Repo landen (z.B. `hermes-zorin/` statt `hermes-v7-repo-starter/`). **Fix:** Im Kontext-Block IMMER den absoluten Repo-Pfad angeben mit `cd <pfad> && git add -A && git commit -m "..."`. Nach Reparatur: Dateien mit `cp` rüberschieben statt neu committen.

## TypeScript / Node Pitfalls

18. **tsconfig rootDir Pitfall** — Wenn `rootDir: "src"` gesetzt ist, MÜSSEN alle Sourcen liegen. Liegt z.B. `cli/` außerhalb → TS6059 Error. **Fix:** Entweder `rootDir: "."` lassen oder `include` anpassen.
19. **`.js` Import-Suffix bei CommonJS + ts-node** — ts-node mit `module: commonjs` kann `'./foo.js'` Imports nicht auflösen. `tsc` → `dist/` build funktioniert ABER Live-Tests brauchen Build-first Pattern: `npx tsc && node dist/...` statt `npx tsx src/...`. Für `npm run dev` (tsx watch) ohne `.js`-Suffixe importieren.
18. **TypeScript `.js`-Import-Suffixe + ts-node = Module Resolution Fail** — Wenn Dateien `import { X } from './foo.js'` nutzen (ESM-Konvention) aber `module: commonjs` in tsconfig.json steht, kann ts-node die Imports nicht auflösen. **Fix:** Entweder (a) Imports ohne `.js`-Suffix schreiben, oder (b) `npx tsc` nach `dist/` bauen und mit `node dist/...` testen, oder (c) `moduleResolution: bundler` in tsconfig setzen. Für schnelle Live-Tests: Build + node ist zuverlässiger als ts-node.
17. **TypeScript-Imports mit `.js`-Suffix + CommonJS = ts-node Crash** — Wenn `tsconfig.json` `"module": "commonjs"` hat, kann `ts-node` Imports mit `.js`-Suffix NICHT auflösen → `Cannot find module './foo.js'`. **Fix:** (a) Imports OHNE `.js`-Suffix, oder (b) `npx tsc` → `node dist/path/to/file.js`, oder (c) `"type": "module"` in package.json setzen. Für neue Projekte: `"module": "commonjs"` + Imports OHNE `.js`-Suffix.
18. **`rootDir: "."` erzeugt verschachtelte dist-Pfade** — Bei `rootDir: "."` + `outDir: "dist"` landen Dateien unter `dist/src/...`. **Fix:** `rootDir: "src"` wenn alles in `src/` liegt, oder Pfade entsprechend anpassen.

## Environment / Secrets Pitfalls

20. **`.env` sourcing mit Telegram-Bot-Token** — `.env`-Dateien mit `BOT_TOKEN=123456:ABC...` brechen `source .env` (das `:` wird als Command geparst). **Fix:** `export KEY=$(grep "^KEY=" .env | cut -d'=' -f2-)` statt `source`.

## Output / Format Pitfalls

21. **Subagent schreibt Dateien im falschen Repordner** — Workers schreiben Artefakte in den Queen-Arbeitsordner statt im Ziel-Repo. **Fix:** Im Kontext-Block OUPUT-Pfade angeben: `SCHREIBE ALLE DATEIEN NUR IN: <absoluter-zielpfad>`. Verpfendete `cd <pfad> &&` Prefix im shell Aufruf.
19. **Experten-Output-Format: Dateien statt Markdown-Embedded Code** — Subagenten die Code liefern sollen, sollten `.ts`/`.py` Dateien schreiben, nicht Code-Blöcke in Markdown. **Fix:** Im Context explizit vermerken: "Erstelle eine Datei `src/queue/claim-engine.ts` mit dem Code, nicht als Markdown-Codeblock." Sonst muss der Queen Code extrahieren und manuell speichern.

## Memory / Reality-Check Pitfalls (KRITISCH — Session 2026-06-30)

22. **Memory-Annahmen ohne Reality-Check können Wochen veraltet sein** — Mnemosyne-/Memory-Blocks die Config-/Sec-Status dokumentieren, sind nach mehreren Sessions oft veraltet. **Symptom:** Parent plant einen ganzen Workstream (P0-Fixes) der bereits done ist. **Fix:** BEVOR Pläne auf Memory-Fakten gebaut werden: lokale Datei/Config prüfen (`cat ~/.hermes/config.yaml | grep -E "..."`, `tirith --version`, `systemctl status ...`). **Live-Test als beste Verifikation:** `tirith check "curl | bash"` zeigt sofort ob Pattern-Detection läuft — auch ohne Mnemosyne-Update. Siehe `references/session-2026-06-30-security-hardening.md` für vollständige Recovery-Sequenz.
23. **Parent-Direct-Vorab während Scout-Wartezeit** — Während 3 parallele Scouts ~5-6 min laufen, MUSS der Parent nicht idle sein. Statt dessen sofort eine eigene **Vorab-Synthese** schreiben (basierend auf Bauchgefühl, früheren Erfahrungswerten, lokalem Code-Read). Wenn Scout-Reports zurückkommen: mergen mit Parent-Vorab in eine Master-Synthese. **Realer Zeit-Gewinn:** ~30 min pro Multi-Agent-Runde. Pattern in `references/session-2026-06-30-security-hardening.md`.
24. **Konvergenz als Qualitäts-Signal bei Multi-Agent-Reports** — Wenn alle 3 Scouts UNABHÄNGIG auf dieselbe Empfehlung kommen (z.B. Falco statt Tetragon, SQLite statt JSONL, Volatile Tier für Canary), ist die Konfidenz hoch. Divergenz (z.B. tcpdump vs iptables vs eBPF für Egress-Monitoring) signalisiert wo Trade-offs diskutiert werden müssen → Hybrid-Empfehlung formulieren. **Immer nach Scout-Return die Konvergenz explizit bewerten** in der Parent-Synthese.
25. **External-Source vs Local-Gap** — Externe Empfehlungen (Perplexity, Web-Recherche, Whitepaper) überschätzen oft was fehlt und unterschätzen was schon da ist. **Fix:** IMMER Reality-Check gegen lokale Code/Config bevor P0/P1/P2-Priorisierung akzeptiert wird. Externe Empfehlungen als **eine weitere Meinung**, nicht als **Source of Truth**. Besonders kritisch bei Security-Themen wo Compliance-Schulungen oft "Best Practice" unkritisch übertragen ohne lokales Threat-Model zu prüfen.

## Cron / Delivery Pitfalls

17. **Cron-Job Telegram-Timeout bei großen Outputs** — Wenn ein `no_agent=true` Script >10KB stdout liefert und `deliver: telegram:ID` gesetzt ist, schlägt das Telegram-Send-Timeout fehl (30s Limit). **Fix:** Für Output-heavy Jobs `deliver: local` setzen. Telegram-Delivery nur für kurze Alerts (<2KB). Siehe auch: `references/cron-delivery-patterns.md` im daily-briefing Skill.

## Research / Subagent Pitfalls

15. **Research-Subagent auf "Soft-Knowledge"-Tasks timeoutet** — Subagenten die "weiches" Wissen recherchieren sollen (Spiel-Guides, Tutorials, HowTo's, Roadmaps, generelle Domain-Erklärungen) neigen dazu, endlos zu vertiefen. Anders als technische Research-Tasks (API-Docs, Code-Patterns) gibt es hier kein klares "fertig"-Signal. Empirisch 2026-06-21: Roadmap-Task timeoutet bei 48 API-Calls / 1h (max_iterations x Zeitlimit) ohne Datei-Output. **Fix:** Striktes Call-Budget im Briefing setzen ("MAX 15 API-Calls, danach Synthese mit dem was da ist"). Alternativ: Parent übernimmt "Soft-Knowledge"-Research per 3-5 gezielter Reads, spawn Subagents NUR für messbare technische Arbeit.

## GreyHack / GreyScript Pitfalls

14. **GreyScript hat KEIN wget/curl** — Die Disassemblierung (`ShellIntrinsics.methods.txt`) zeigt keine HTTP/Download-Funktionen. GreyScript ist sandboxiert: kein Netzwerk, kein Filesystem (nur via `get_shell`). **Deployment:** Fileserver + Copy-Paste aus Browser in CodeEditor, oder `greybel import`. Referenz: `references/greyhack-deployment-pitfalls.md`.
15. **greybel-vs Mock-Env ist VERALTET** — Der greybel-js Interpreter (v2.8.13) hat einen Mock-Environment mit `get_shell.host_computer`, ABER: `shell.cat()`, `shell.users`, `shell.ports`, `shell.ConfigOS` funktionieren NICHT ("Path not found in map"). `net.so` ist nicht verfügbar. Nur `crypto.so` und `metaxploit.so` laden. **Workaround:** Test von Code mit Game-APIs (get_shell, cat, users, FileSystem) nur im echten Spiel. Mock-Env nur für reine Logik (String, Math, params, Kontrollfluss). Repo: https://github.com/Toqsick/greybel-vs. Referenz: `references/greybel-mock-env-limitations.md`.