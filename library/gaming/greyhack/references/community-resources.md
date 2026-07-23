# Community Resources & Architecture

## Steam Workshop Guide Reference
- **Guide:** "Basic exploits with scripting" (Steam ID: 1906145953, IZackI, 2019)
- **File:** `~/greyhack-tools/references/steam-guide-scripting.md`
- **Key insight:** `\n` works in GreyScript strings (not only char(10))
- **HTML in terminal:** `<b>`, `<color=#ff0000>`, `<color=#00ff00>` all work
- **Complete scanner + probe scripts** with line-by-line comments

## GreyHack apt-get Package Manager

GreyHack has a built-in package manager:
```
apt-get show              # List all available packages
apt-get search <name>     # Search for a program
apt-get install <name>    # Install a program
apt-get addrepo <ip>      # Add new repository (DANGER: player-made repos may contain malware)
apt-get delrepo <ip>      # Remove a repository
apt-get update            # Update package lists
apt-get upgrade           # Upgrade installed packages
```

**Always check `apt-get search` before building from source!** If a package exists in the repo, install it instead of building manually.

Repository list stored in `sources.txt` in the game filesystem. No repos configured by default (fresh game).

**WARNING:** Player-made repositories may contain malicious software. Only add trusted repos.

## Community Libraries (salmon85)

Useful libraries from salmon85/Grey_hack_scripts on GitHub:
- `includes/json.src` — JSON Parser (349 lines)
- `includes/networking.src` — IP-Range calculation (109 lines)
- `includes/tqdm.src` — Progress bar utility

Copied to `~/greyhack-tools/includes/`.

## ftzi/grey-hack Architecture (Recommended)

The ftzi/grey-hack GitHub repo (https://github.com/ftzi/grey-hack) provides a professional GreyScript project structure:

- `src/lib/` — Libraries (std.src, lib.src, etc.)
- `src/tools/` — Tools (portscan.src, hack.src, etc.)
- `#import` style imports (cleaner than `import_code`)
- Lazy loading libraries with auto-install via `apt-get`
- String/List/Map extensions in `std.src`

**Key Patterns from ftzi:**
```greyscript
// Lazy loading library manager
Lib = {}
Lib._libs = {}
Lib._getLib = function(name)
    if not Lib._libs.hasIndex(name) then
        Lib._libs[name] = Lib.load(name)
    end if
    return Lib._libs[name]
end function

// Auto-install if missing
Lib.load = function(name)
    path = Lib.libPath(name, true)  // true = installIfMissing
    if path == null then exit("Error: Library '" + name + "' not found")
    return include_lib(path)
end function

// String extensions
string.error = function()
    return self.color("red")
end function

// Safe list sort (handles empty/single-element lists)
list.sort2 = function(prop = null)
    if self.len < 2 then return self.copy()
    if prop == null then return self.copy().sort
    return self.copy().sort(prop)
end function
```

**Reference files in `~/greyhack-tools/`:**
- `src/lib/std.src` — Standard library (String/List/Map extensions)
- `src/lib/lib.src` — Library manager (lazy loading + auto-install)
- `src/tools/portscan.src` — Portscan tool using the new architecture
- `includes/ftzi_std.src` — Original ftzi std.src for reference
- `includes/ftzi_lib.src` — Original ftzi lib.src for reference

## GreyHack Sandbox Toolkit

Lokales Python-Entwicklungstoolkit für GreyHack, gebaut via `/multi-agent-work`:

| Modul | Pfad | Funktion |
|-------|------|----------|
| `greyhack-sandbox.py` | `~/projects/greyhack-sandbox/src/` | Python-Wrapper für greybel-js + GreyHackDB |
| `npc_intel.py` | `~/projects/greyhack-sandbox/src/` | NPC-Schwachstellenscanner (6 NPCs, 3 hackbar) |
| `auto_pwn.py` | `~/projects/greyhack-sandbox/src/` | Auto-Exploit-Generator (GreyScript Output) |
| `exploit_template.src` | `~/projects/greyhack-sandbox/src/templates/` | GreyScript Exploit-Template |

**Quick-Start:**
```bash
python3 ~/projects/greyhack-sandbox/src/npc_intel.py scan --severity HIGH
python3 ~/projects/greyhack-sandbox/src/auto_pwn.py exploit Dee --output /tmp/dee_pwn.src
```

**DB-Pfad:** `~/.hermes/Grayhack Game + Data (fork)/Grey Hack/GreyHack_Data/GreyHackDB.db`
**greybel-js:** `~/node_modules/.bin/greybel` (v3.7.12)

## greybel-vs — External Interpreter & IDE

**Repo:** `~/greybel-vs/` (geklont von https://github.com/Toqsick/greybel-vs.git)

### Key Features
- **Interpreter mit Mock-Environment:** Teste GreyScript MIT get_shell, include_lib, metaxploit.so — ohne Spiel!
- **Preview Output:** Sieh sofort was das Spiel zeigen würde
- **Import ins Spiel:** Per Message-Hook (BepInEx) oder Copy-Paste
- **Linter & Syntax-Highlighting:** Fehler BEIM Schreiben finden, nicht erst im Build

### Mock-Environment
- `root:test` als Default-Admin
- `crypto.so`, `metaxploit.so`, `net.so` verfügbar
- Generates simulated computers, networks, filesystems

### Workflow
```bash
# 1. Install dependencies
cd ~/greybel-vs && npm install && npm run compile

# 2. Open VSCode Extension Development Host
code --extensionDevelopmentPath=~/greybel-vs ~/greybel-vs/test-workspace/

# 3. In VSCode: CTRL+SHIFT+P → "Greybel: Run/Debug file from context"
#    → Script runs with full game API simulation
```

### Message-Hook (Optional — für direkten Spiel-Import)
```
1. BepInEx installieren in Grey Hack Ordner
2. GreyHackMessageHook.dll in Plugins/
3. greybel import <file.src> -pt 8332 -id "/home/Bratan"
```

### Pitfalls
- **Mock ≠ Echter Spiel:** Manche APIs verhalten sich anders im echten Spiel
- **Kein wget im Spiel:** Fileserver nur für greybel-js Test nutzbar, nicht für In-Game Downloads
- **Free-Model Instabil:** `nex-agi/nex-n2-pro:free` kann offline gehen; Fallback: `deepseek/deepseek-v4-flash:free`

## Awesome-Hacking Research Workflow

See `references/awesome-hacking-greyhack-research.md` for the Top-20 GreyHack implementation recommendations and the knowledge-base workflow. Key rule: research and plan first; do not edit `src/` or `tools/` until the Top-20 plan and safety filter are written.
