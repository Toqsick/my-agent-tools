# Pitfalls

1. **NICHT** `/releases/latest/download/` verwenden — IMMER exakte Asset-URL aus API holen
2. **NICHT** Saves unter `~/Documents/` suchen — die sind nur im Wine-Prefix
3. **NICHT** `set -e` in Bash-Skripten ohne `|| true` für Debug-Outputs verwenden — crasht auf nicht-kritischen Fehlern
4. **NICHT** CET-Ordner als `.zip` in `cyber_engine_tweaks/` erwarten — CET entpackt `.asi` in `bin/x64/plugins/` und Daten nach `cyber_engine_tweaks/`
5. **IMMER** Smoke-Check vor erstem Game-Start — 12 Komponenten prüfen
6. **CASE-SENSITIVITY** beachten bei Pfad-Vergleichen (`red4ext/` != `RED4ext/`)
7. **FRAMEWORK-ORDER** einhalten — RED4ext zuerst, dann CET, dann XL-Plugins
8. **NICHT** .csd/.csm Backups doppelt komprimieren — Steam packt selbst
9. **REDLAUNCHER CRASHT IMMER UNTER PROTON** — Ist kein Bug in deiner Mod-Installation! Der Exit-Code `-1073741819 (0xC0000005)` ist ein bekannter Proton/Wine-Fehler mit Qt-GUI-Prozessen. Fix immer via `--launcher-skip`.
10. **REDMOD-TOGGLE IST IMMER AUS UNTER PROTON** — Der "Mods erlauben"-Schalter im REDlauncher crasht unter Proton grundsätzlich (Wine kann Qt-Child-Prozesse nicht zuverlässig spawnen). Die Mods laden trotzdem (RED4ext/CET/XL-Plugins sind DLL-Injection und unabhängig).
11. **BEI LaunchOptions-Edit IMMER lokale Backup machen** — `localconfig.vdf` wird von Steam bei Launcher-Reparatur überschrieben.
12. **REDprelauncher.log ist die Primary Source** für Launcher-Probleme — der Log liegt im Wine-Prefix.
13. **REDscript Runtime != REDscript Compiler** — `jac3km4/redscript` auf GitHub liefert NUR `scc.exe` (Compiler). Das Runtime-Plugin `redscript.dll` für custom .reds gibt es NUR auf Nexus Mods #1511.
14. **RED4ext.log kann unter Proton still fehlen** — Auch bei korrekter Installation wird manchmal nie `red4ext.log` geschrieben.
15. **GE-Proton spült jedes Mal dateien ins Game-Root** — `vkd3d-proton.cache`, `version.dll`, `winmm.dll` erscheinen nach jedem Game-Start im Game-Ordner. Das ist normales GE-Proton-Verhalten.
16. **NICHT wine-Befehle außerhalb der Proton-Wrapper-Umgebung verwenden** — `wine` direkt aufgerufen crasht auf Flatpak-Systemen.
17. **NIEMALS `pkill -f` mit generischem Pattern wie `remote-debugging-port`** — Das matcht **auch Hermes-Prozesse** und killt die eigene Session.
18. **Brave Cookies-DB ist encrypted (seit v1.92+)** — Direkte SQLite-Extraktion liefert leere `value`-Spalte. **Einzige zuverlässige Methode:** Separate Brave-Debug-Instanz via CDP, dann `Network.getCookies` via WebSocket.
19. **Cloudflare-Cookies (`cf_clearance`, `__cf_bm`) sind an TLS-Fingerprint gebunden** — Selbst mit korrekt exportiertem `nexusmods_session` Cookie bekommt `curl` HTTP 403.
20. **CDP Page-Navigation ist zu langsam für Bulk-Downloads** — `Page.navigate` + Warten auf `Page.loadEventFired` braucht 3-5 Sekunden pro Mod. Für 444 Mods sind das 20-30 Minuten reine Wartezeit.
21. **Web-Tools (Firecrawl/Brave Search API) oft nicht konfiguriert** — Vor jeder Aufgabe prüfen ob Web-Tools aktiv sind.
22. **execute_code blockt nach erstem tool-Fehler in der Session** — Workaround: Auf `terminal` + Python heredoc umsteigen.
23. **Bottles+Vortex = 3 GB Overhead für Download-Use-Case** — Der Wine-Prefix alleine ist 3 GB. Wenn du Vortex nur zum Runterladen nutzt, ist der Aufwand nicht gerechtfertigt.
24. **RT-Toggles per JSON setzen: `RayTracedLighting` NIE auf `On` setzen** — Gültige Werte sind `Off`, `Medium`, `Ultra`, `Psycho`.
25. **UserSettings.json RT-Edit wird von CP77 überschrieben, wenn Capability-Detection fehlschlägt** — CP77 prüft beim Start via `D3D12_OPTIONS5` ob DXR verfügbar ist.
26. **VKD3D-Proton < 5300 = kein Blackwell/RTX-5000-RT-Support** — GE-Proton10-34 hat vkd3d-proton Build 5122 (~2023).
27. **Full Reset als Differenzial-Diagnose für RT-Toggles** — Wenn RT-Toggles trotz Proton-Wechsel + UserSettings-Edit ausgegraut bleiben, ist ein Full Reset der **ultimative Test**.