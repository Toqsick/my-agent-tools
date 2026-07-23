# Viper 2.2.1 — Integration mit Yuno

**Source:** https://github.com/EntitySeaker/viper-git
**Lokale Kopie:** `/tmp/viper-git/`
**Lizenz:** (siehe GitHub)

## Was ist Viper?

Viper ist ein vollständiges interaktives Hacking-Terminal für GreyHack:
- **162 KB** einzelnes `.src` File (gebaut aus 94 Files via `build.sh`/`build.py`)
- **85 Commands** in der Default-Installation
- Theme-System mit User-Settings
- Session-Management (`targets`, `use`, `back`)
- Library-Management (`libs`, `uselib`, `getlib`)
- Crypto-Tools (AES128, SHA256, MD5, GPG)
- Metasploit-Integration (`msfvenom`, `msfconsole`)
- **Plugin-Architektur via `getviper`**

## Architektur

```
┌─────────────────────────────────────────┐
│  /home/volk/viper.src (162 KB)          │  ← User startet das
│  while not exit                         │
│    input = user_input(TTY(...))         │  ← Hauptschleife
│    command_logic(input)                 │
│      commands[command].run(...)         │  ← Dispatch
└─────────────────────────────────────────┘

commands = {
    "help": help, "clear": clear, "credits": credits,
    "nmap": nmap, "exploitscan": exploitscan, "exploit": exploit,
    "targets": targets, "use": use, "back": back, ...
}
```

## File-Struktur (Repo)

```
viper-git/
├── libs/          (5 files: encryption, json, security, sha256, Escape)
├── functions/     (15 files: nmap_scan, exploit_scan, ssh, ascii_print, etc.)
├── core_commands/ (2 files: list_files, read_file)
├── commands/      (76 files: nmap, ssh, exploit, msfconsole, ...)
├── main/          (1 file: main.src — die Hauptschleife)
├── images/        (2 files: viper.img, raw_image — ASCII Art)
└── viper.src      (gebautes Single-File)
```

## Build-Prozess

```bash
# build.sh (sequenziell):
for i in $(ls ./libs); do cat ./libs/$i >> ./viper.src; done
for i in $(ls ./functions); do cat ./functions/$i >> ./viper.src; done
for i in $(ls ./core_commands); do cat ./core_commands/$i >> ./viper.src; done
for i in $(ls ./commands); do cat ./commands/$i >> ./viper.src; done
cat ./main/main.src >> ./viper.src

# build.py: gleiche Logik in Python
```

## Plugin-Mechanismus: `getviper`

```greyscript
getviper = function(object, args)
    viperPath = object.host_computer.File(args[0])
    cargo = get_custom_object
    clearInterface(cargo)
    object.launch(args[0], argument)
    if hasIndex(cargo, "viper") then
        // IMPORT Objects der zweiten Viper-Instanz
        for index in @cargo.viper
            if not verifyObject(@index.value.object) then
                print("AV detected injection!")
                return
            end if
            main_session.objectList[main_session.objectList.len] = index.value
        end for
    end if
end function
```

**Wichtig:** Plugins müssen `get_custom_object` exponieren mit `viper` (Objects) und `vlibs` (Libraries).

## Yuno-Integration: 3 Optionen

### Option A: Yuno als Viper-Plugin (EMPFOHLEN)
- 15 min Aufwand, kein Refactoring
- Yuno exposiert `get_custom_object` mit `viper` Key
- User ruft `getviper /home/gregor/Config/yuno.src` in Viper
- Yuno-Commands (hack/loot/defend/bank) ergänzen Vipers 85 Commands
- **Vorteil:** Beide Welten coexisting
- **Nachteil:** Zwei Scripts laufen parallel

### Option B: Hybrid-Script
- Yunos 3 fehlende Commands (hack/loot/defend/bank) als Viper-Commands
- 30 min Aufwand
- Viper-Skelett mit Yuno-Plugins
- **Vorteil:** Single Tool, alle Features
- **Nachteil:** Wartung von zwei Code-Basen

### Option C: Yuno komplett auf Viper-Skelett
- 1h Aufwand, viel Refactoring
- Yuno-Kommandos werden in Vipers command-Dictionary integriert
- **Vorteil:** Unified
- **Nachteil:** Yuno verliert Eigenständigkeit

## Build-Status

```
$ greybel build viper.src -u
Build done. Available in /mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/build.
Exit code: 0
```

Viper baut **sauber** — keine Syntax-Fehler mit greybel-js.

## Was Viper kann, was Yuno nicht kann

| Feature | Viper | Yuno |
|---------|-------|------|
| Interaktive Shell mit Sessions | ✅ | ❌ |
| Metasploit (msfvenom/msfconsole) | ✅ | ❌ |
| Variables & Macros | ✅ | ❌ |
| AES128/SHA256/MD5/GPG | ✅ | nur MD5 |
| Theme-System | ✅ | ❌ |
| Settings Save/Load | ✅ | ❌ |
| File-System browsing (fs, ls, cat) | ✅ | ls only |
| **Auto-Hack (scan→exploit→loot in 1)** | ❌ | ✅ |
| **Bank-Transfer** | ❌ | ✅ |
| **Defense-Check** | ❌ | ✅ |
| Size | 162 KB | 17 KB |
| Dependencies | include_lib für 3 Libs | include_lib für 2 Libs |

## Lessons für Yuno-V2

Falls Yuno jemals Viper-Features adoptieren will:
- **Themes:** Farben über `user_session.theme` dict, dann `do_style(text, color, "static")`
- **Settings:** `vars`, `addvar`, `delvar` — persistent via `saveSettings()`/`loadSettings()`
- **Macros:** `@macro_name` Trigger, lädt File aus `/Config/Macros/`
- **Sessions:** `add_session({"IP":..., "objectType":..., "object":...})` für Push/Pop
- **ObjectList:** Generic Hash-basiertes System statt dedizierter Variablen

## Pitfalls

1. **Viper ist 162 KB** — größer als die HDD (350 MB) im Verhältnis klein, aber im GreyHack-FileSystem wird es ~5 GB groß nach build.
2. **Main-Loop ist Endlos:** `while not main_session.exit` blockiert — `exit` muss explizit aufgerufen werden, sonst kein Return.
3. **`object.launch(args[0])`** startet ein zweites Viper — rekursiv möglich, aber gefährlich für Performance.
4. **AES128-Implementation:** Komplett in Pure-GreyScript, ~200 Zeilen. NICHT für Production-Crypto — GreyHack-Lernprojekt.
5. **Viper-Updates:** Check regelmäßig auf GitHub, neue Versionen kommen oft.