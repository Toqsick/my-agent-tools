# GreyHack Script Storage — Konsolidierung & Cleanup

Wenn die Script-Sammlung im Spielordner (`Grey Hack/yuno-tools/` oder `/home/Bratan/bin/`) zu groß wird, ist **Konsolidierung in einen All-in-One Multi-Command Scripter** der effektivste Weg.

## Größen-Realität (gemessen 2026-07-03)

| Stand | Größe | Files |
|-------|-------|-------|
| 31 einzelne Scripts (mission_v2/v3/v4, dee_hack*, deep_recon, etc.) | 96.6 KB | 31 |
| **1 All-in-One `yuno.src`** (scan/hack/loot/defend/crack/bank) | **16.9 KB** | 1 |
| **Ersparnis** | **−79.7 KB (−83%)** | −30 |

greybel-build verifiziert ✅.

## All-in-One Scripter Pattern (Best Practice)

### Struktur
```greyscript
// === PARAMETER-CHECK ===
if params.len < 1 then
    print("BEFEHLE: scan | hack | loot | defend | crack | bank" + char(10))
    exit(0)
end if
cmd = params[0]

// === HELP ===
if cmd == "help" then ... end if

// === SCAN ===
if cmd == "scan" then
    // args: params[1] = IP, params[2] = optional port
    ...
    exit(0)  // WICHTIG: jeder Block endet mit exit(0)
end if

// === HACK / LOOT / DEFEND / CRACK / BANK ===
if cmd == "hack" then ... end if
// ... weitere Subcommands ...

// === FALLBACK ===
print("[!] Unbekannt: " + cmd + char(10))
```

### Kritische Syntax-Constraints (aus realen Builds)

| Pitfall | Fix |
|---------|-----|
| Inline `if ... then BODY end if` auf einer Zeile | greybel-js REJECTS — Multi-Line `if/then/BODY/end if` erzwingen |
| Ternary `"X" if cond else "Y"` | Nicht valide in GreyScript — voller if/else Block |
| `params[^0]` (caret) | Funktioniert nicht — `params[params.len - 1]` benutzen |
| `if found == false` mit `found = false` und nie zugewiesen | Vergleich OK, aber: `indexOf` returns `-1` nicht `null` |
| Variable deklariert aber nie zugewiesen in nested loops | greybel warned — immer initialisieren: `shell = null` am Anfang |
| `if p1 != null` für indexOf-Check | FALSCH — `if p1 >= 0` benutzen (indexOf returns -1) |

### Vollständiges Working Template: `yuno.src`
Siehe `templates/yuno-all-in-one.src` im Skill — 17 KB, buildable, mit allen 6 Subcommands.

## YUNO Evolution (Stand 2026-07-03)

Fünf Iterationen, alle auf dem "All-in-One Scripter"-Pattern:

| Version | Größe | Features | Datei |
|---------|-------|----------|-------|
| yuno.src (V1) | 17 KB | 7 Subcommands, early-exit dispatcher | `templates/yuno-all-in-one.src` |
| yuno_v2.src | 45 KB | 50+ Commands, interactive `user_input()`-Shell, `main_session`-State, auto-lib-load | `~/docs/system/greyhack-yuno-v2-2026-07-03.md` |
| yuno_v3.src | 52 KB | + Theme-System (3 themes via Map-Switch), Macro-System (`@<name>`), getyuno (Tool-Repo) | `~/docs/system/greyhack-yuno-v3-2026-07-03.md` |
| yuno_v5.src | ~65 KB | V3 + 51 Syntax-Fixes + P0-Bugfixes + CI-Stabilisierung (19/19 Builds grün) | `~/greyhack-tools/yuno_v5_source.src` |
| **yuno_v6.src** | **78.2 KB** | V5 + 6 neue Features: Disk-Persistenz, Full State Restore, Plugin Auto-Load, History-aware Suggest, Sniffer-Integration, Cooperative Mode | `references/yuno-v6-architecture.md` |

Im Vergleich (gemessen 2026-07-03):
- **Viper** (EntitySeaker): 162 KB / 94 files / 85 commands — Original-Reference
- **YUNO V6**: 78.2 KB / 1 file / 61 commands — **52% kleiner als Viper** + 6 exklusive Killer-Features
- **V6-Δ zu V5:** +13 KB (+20%) für Persistenz + Coop + Suggest-Upgrade

**V6 = bisher größtes YUNO-Update.** Alles aus V3/V5 bleibt erhalten. Neue Features sind als optionale Patches eingebaut — bestehende Code-Blöcke blieben unberührt.

**Wann welche Version?**
- V1 (17 KB) reicht für simple Tools (scan/hack/loot/etc.) ohne interactive shell
- V2 (45 KB) wenn du 30+ Commands mit State-Management brauchst
- V3 (52 KB) für Full-Feature-Frameworks mit Theme/Macro/Tool-Repo
- V5 (~65 KB) für stabilen Daily-Driver (P0-sauber, CI-grün)
- V6 (78 KB) für **Disk-Persistenz** (Config speichern/restoren beim Spiel-Exit)

**Fork-and-Extend:** V6 wurde via 6 Patches aus V5 abgeleitet (kein Rewrite). Workflow:
1. V5-Code komplett lesen
2. Patches zwischen bestehende Blöcke einfügen
3. `npx greybel build yuno_v6.src -u` → Build OK
4. `npx greybel execute /build/yuno_v6.src -p help --silent` → Mock-Env OK
5. Kopie nach `~/greyhack-tools/` für In-Game-Deployment

## Workflow-Lesson: Vor Löschen IMMER Bestandsaufnahme

**Wenn Basti sagt "ich werde alle alten Scripts löschen":**

1. **NICHT** sofort `rm -rf` ausführen — Basti meint "fast alle", nicht zwangsläufig alle.
2. **Bestandsaufnahme** machen:
   - Welche Pfade sind betroffen? (Spielordner vs. Repo vs. beide?)
   - Welche Files sind unique im Repo vs. im Spielordner?
   - Welche sind duplikate (selbe Logik, verschiedene Versionen)?
3. **Optionsliste** mit 2–4 klaren Varianten anbieten:
   - **A (⭐⭐⭐)**: Nur Spielordner aufräumen, Repo unberührt
   - **B**: Spielordner + ein zweiter Pfad
   - **C**: Aggressiv (Repo build/bin/backups mit)
   - **D**: User gibt Liste explizit vor
4. **Erst nach expliziter Wahl** löschen.

Begründung: Basti hat im Repo einen kompletten Installer + alle P0-Fixes + Greybel-Pipeline. Blind alles killen würde Production-Assets zerstören. User-Preference passt zur globalen Yuno-Regel "bei destruktiven Ops nie blind ausführen".

## Empfohlene Lösch-Strategie für `Grey Hack/yuno-tools/`

```bash
# 1. Sicher: alle alten Scripts in einem Rutsch (nur Spielordner!)
cd /mnt/DATA/Programme/Steam/steamapps/common/Grey\ Hack/yuno-tools/
# Backup-Pattern: in tar.gz bevor löschen
tar czf /tmp/yuno-tools-backup-$(date +%Y%m%d).tar.gz *.src
# Alles außer yuno.src löschen
find . -maxdepth 1 -name "*.src" ! -name "yuno.src" -delete
# yunu-tools/ (Tippfehler-Ordner) ebenfalls, wenn nur 1 File drin
rm -rf /mnt/DATA/Programme/Steam/steamapps/common/Grey\ Hack/yunu-tools/
```

Repo `~/greyhack-tools/` bleibt komplett — der Installer ist 370 KB und die Build-Pipeline baut alle Tools.

## Build-Verifikation

Nach jedem neuen/konsolidierten Script:
```bash
cd /mnt/DATA/Programme/Steam/steamapps/common/Grey\ Hack/yuno-tools/
npx greybel build yuno.src -u 2>&1 | head -30
# Erwartet: "Build done. Available in .../build."
```

Bei Syntax-Fehlern: typisch sind die 2 Patterns oben (single-line if, ternary). Beide müssen VOR Build manuell korrigiert werden.

## Siehe auch

- `templates/yuno-all-in-one.src` — vollständiges Working Template (17 KB, alle 6 Subcommands)
- `references/greyscript-language.md` — vollständige Sprach-Referenz mit allen 56 Pitfall-Kategorien
- `references/build-troubleshooting.md` — wenn greybel-build fehlschlägt