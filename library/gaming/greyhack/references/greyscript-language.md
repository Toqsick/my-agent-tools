# GreyScript Language — Full Reference

Extracted from the `greyhack-greyscript` skill.

## Critical Language Pitfalls (56 Categories)

### Strings
- **Double quotes only** — single quotes cause silent syntax failures
- **`\n` in strings** — literal backslash-n, not newline. Use `char(10)` for real newlines
- **String immutability** — `s[0] = x` throws Runtime-Error. Use `s[0].upper + s[1:]`
- **`.upper` needs parens** — `name.upper()` not `name.upper`
- **`String.values` does NOT exist** — strings are directly iterable
- **`.strip()` does NOT exist in MiniScript** — `.trim()` only in MS2+; for compatibility write a manual strip loop:
  ```greyscript
  while inp.len > 0 and inp[0] == " "; inp = inp[1:]; end while
  while inp.len > 0 and inp[inp.len - 1] == " "; inp = inp[:inp.len - 1]; end while
  ```
  Many scripts that work in Mock-Env silently fail at runtime because the runtime doesn't expose `.strip()`.

### Function calls in `then` clauses
- **`exit("msg")` inside `if X then` REJECTS in greybel-js** — even if the function would be valid elsewhere, the parser trips on a parenthesised function call after `then`. Fix: split into multi-line block:
  ```greyscript
  if X then
      exit
  end if
  ```
  Same for any `funcCall(args)` immediately after `then` if the parser gets confused. Prefer `if X then` followed by a single statement on the next line.

### Indexing
- **Negative indices don't work** — `arr[-1]`, `arr[^0]`, `arr[:-1]` all fail. Use `arr[arr.len-1]`
- **Float as array index** — `rnd * (len-1)` produces Float. Wrap in `floor()` or `ceil()`
- **`indexOf` returns `-1`** when substring NOT found, NOT `null`. Always compare with `== -1` or `!= -1`
- **`lastIndexOf` returns `-1`** when not found, NOT `null`
### Collections

- **Multi-line map literals** — `{"a": 1, "b": 2}` spanning lines fails. Build incrementally: `m = {}; m["a"] = 1`
- **Multi-line list literals** — same trap. Build with `[]` + `.append()`
- **`for x in map` returns KEYS** not values. Use `for k in map.indexes; v = map[k]`
- **`Map.values` does NOT exist** — use `myMap.to_list`
- **`List.indexes` does NOT exist** — use `range(myList.len)`
- **`list.remove(x)` is by index, not value** — must `indexOf()` first
- **`self.values` does NOT exist** on Maps or Lists
- **❌ Type extension of built-in types compiles but fails at runtime** — GreyScript does NOT support adding methods to built-in types like `list`, `map`, or `string`. Code like `list.applyFunction = function(func)` passes `greybel build` (no static warning) but crashes at runtime with `no such method` or `path not found`. The fix is to extract a global helper function that takes the collection as the first parameter:
  ```greyscript
  // ❌ Crashes at runtime:
  list.applyFunction = function(func)
      out = []
      for item in self; out.push(func(item)); end for
      return out
  end function
  someResult = someList.applyFunction(@myFunc)

  // ✅ Works in GreyScript:
  applyFunction = function(lst, func)
      out = []
      for item in lst; out.push(func(item)); end for
      return out
  end function
  result = applyFunction(someList, @myFunc)
  ```
  **Detection grep:** `grep -rn '^\s*\(list\|map\|string\)\.\s*[a-zA-Z]' --include="*.src"`

### Control Flow
- **Single-line `if ... then` has NO `end if`** — only multi-line form needs it.
  - ✅ Valid in GreyScript: `if x then do_something` (no `end if` required)
  - ✅ Valid in GreyScript: `if x then\n  ...\nend if` (multi-line, needs `end if`)
  - ❌ Wrong: counting these as "missing `end if`" — single-line is intentional
  - ⚠️ **greybel-js incompatibility**: `if X then Y end if` on ONE line is rejected by greybel-js. Convert to multi-line form for builds.
- **greybel-js incompatibility — even with semicolon**: `if X then print("y"); return end if` is ALSO rejected. The parser expects one statement, then `end if` only on multi-line. Always expand inline `if/then/statement/end if` to:
  ```greyscript
  if X then
      print("y")
      return
  end if
  ```
  This is the #1 cause of "no matching open if block" errors during build.
- **greybel-js rejects ternary expressions** — `("a" if cond else "b")` is not valid GreyScript. Use full if/else block.
- **`0` is truthy** — use `!= 0` not `if result`
- **`else if` shares the parent's `end if`** — never needs its own
- **State must reset inside loops** — variables storing iteration state must be reset each iteration

### Return Values
- **`delete` returns `""` (empty string) on success**, `null` on failure — NOT `1`. Check `== ""` for success or `typeof(res) == "string"` for error detection
- **`touch()` returns `""` (empty string) on success** — NOT `1`, NOT `null`
- **`shell.build()` returns File on success, String on error** — `== 1` is always false
- **`File.chmod()` takes String** — `"o-rwx"` not `600`
- **`get_content` returns `null` on unreadable** — `or ""` masks errors

### Functions
- **`@` prefix for callbacks** — `@self.method` passes function reference
- **No `str_repeat()`** — define your own spacer function
- **No `get_system_time`** — use fixed prefixes
- **No `mkdir`** — use `pc.touch(path + "/.__init"); tmp = pc.File(...); if tmp then tmp.delete`
- **No `HTTP.Request`** — does NOT exist in GreyScript
- **API uses NO underscore** — correct: `getcontent`, `setcontent`, `getfiles`, `list_files`, `is_folder`. Wrong: `get_content`, `set_content`, `get_files`. If both variants appear in one file, it's a merge artifact. Always use the no-underscore form.
- **`globals.x = value` does NOT make `x` locally available** — `globals.sh = get_shell` creates `globals.sh` but NOT a local variable `sh`. Any subsequent `sh.build(...)` will crash with "variable is not defined". Always use direct local assignment: `shell = get_shell`.

### Error Handling
- **Silent catch blocks** — empty `catch e` swallows errors. At minimum add `print("[WARN] " + e)`
- **`catch e` without handling** — document if intentional (fallback pattern)

### Null Safety
- **Always null-check before `.is_folder`** — `pc.File(path)` returns null if path doesn't exist
- **`is_folder` is VALID** — official API lists it. But needs null-check before
- **`not is_binary` is ambiguous** — means "text OR folder", not "folder"
- **Polymorphic API returns** — Crypto/Metaxploit return null/error-string/list/object. Always `typeof()`

### Compiler Error Signatures
| Error | Cause |
|-------|-------|
| `no matching open if block` | `end if` after single-line if, or greybel-js rejecting `if/then/action/end if` on one line |
| `got Keyword[XX:X - XX:X: value = 'if'] where ")" is required` | Ternary expression `("a" if cond else "b")` — greybel-js cannot parse it |
| `unexpected token` near `^` | Negative index |
| `undefined function` near `.len` | String/object API mismatch |
| `Invalid character 39` | Single quote used |
| `Invalid character 39` | Single quote used |

## Standard Script Template
```
import_code("/home/Bratan/bin/lib_core")
ctx = getContext
shell = ctx["shell"]
pc = ctx["pc"]
showHelp("ToolName", "description", "toolname <arg1>", ["toolname 1.2.3.4"])
arg = requireParam(0, "arg")
if not validIP(arg) then fail("Bad IP")
banner
render("ToolName", ["Target: " + arg])
# main logic
logToFile(pc, "/home/Bratan/.logs/toolname.log", "summary")
```

## Core Library (lib_core.src)
Must include: `render()`, `hr()`, `banner()`, `fail()`, `warn()`, `ok()`, `info()`, `step()`, `requireParam()`, `optionalParam()`, `lastParam()`, `validIP()`, `validPort()`, `getFile()`, `getDir()`, `fileExists()`, `ensureDir()`, `getContext()`, `showHelp()`, `confirm()`, `logToFile()`.

**Maps in lib_core MUST use sequential assignment**, never multi-line `{...}` literals.

## YUNO All-in-One Scripter Patterns (battle-tested 2026-07-03)

The YUNO project (V1=17KB, V2=45KB, V3=52KB) is a working demonstration of compressing an entire hacking framework into a single GreyScript file. Key design rules:

### Pattern 1: Command Dispatcher with early-exit blocks (V1 / Viper-style)
The classic "single-file multi-tool" pattern. Each subcommand is its own `if/then/end if` block, ending in `exit(0)` to prevent fall-through:

```greyscript
if params.len < 1 then
    print("Usage: yuno help | scan | hack | loot ...")
    exit(0)
end if
cmd = params[0]
if cmd == "help" then
    print("=== YUNO HELP ===")
    // ...
    exit(0)
end if
if cmd == "scan" then
    if not is_valid_ip(params[1]) then exit(0) end if
    // scan logic
    exit(0)
end if
// fallback
print("Unknown: " + cmd)
```

**Why this works:** Each block is self-contained; no registry; readable top-to-bottom; each `exit(0)` prevents fall-through. Good up to ~15 commands. Beyond that, switches to Pattern 2.

### Pattern 2: Interactive shell with `user_input()` + `commands{}` map (V2/V3 / Viper-style)
For 50+ commands, use a registry + main loop. This is the only way to keep dispatch clean at scale:

```greyscript
commands = {
    "help": cmd_help, "scan": cmd_scan, "hack": cmd_hack, "exit": cmd_exit, ...
}

while not main_session.exit
    prompt = style("yuno", "red") + "[" + style(pub_ip, "yellow") + "] > "
    inp = user_input(prompt)
    if typeof(inp) != "string" then break
    // strip, parse, dispatch
    if commands.hasIndex(cmd) then
        main_session.buffer.push({"cmd": cmd, "args": cmdArgs})  // for loop
        commands[cmd].run(cmdArgs)
    end if
end while
```

**Critical pitfall — `user_input()` blocks indefinitely:** when testing with greybel execute, you must pipe input AND wait between commands. The TTY re-prints partial inputs as newlines otherwise, making output look like a glitch. For automated tests:
```bash
# Feed input with explicit waits
( echo "credits"; sleep 0.5; echo "exit" ) | npx greybel execute tool.src --silent
```

### Pattern 3: `main_session` state object
Centralise all session state in one map. Viper uses this exact pattern; YUNO V2/V3 adopts it:

```greyscript
main_session = {
    "exit": false, "MetaxploitLib": null, "object": get_shell,
    "pub_ip": null, "loc_ip": null, "current_user": active_user,
    "objectList": {}, "sessionList": [], "libList": {},
    "vars": {}, "buffer": [], "handlerType": "start"
}
```

### Pattern 4: Auto-load libraries with graceful degradation
At script start, attempt to load expected libraries and **continue if missing**:

```greyscript
import_lib = function(name, path)
    lib = include_lib(path)
    if not lib then lib = include_lib(parent_path(program_path) + "/" + path.split("/")[-1])
    if not lib then
        print("[!] " + name + " not found")
        return
    end if
    main_session[name] = lib
    print("[+] " + name + " loaded")
end function

import_lib("MetaxploitLib", "/lib/metaxploit.so")
import_lib("cryptoLib", "/lib/crypto.so")
import_lib("aptclientLib", "/lib/aptclient.so")
```

### Pattern 5: Auto-hack (exploit + brute + loot) combined — the killer feature
Viper lacks this. One command does three phases:

```greyscript
cmd_hack.run = function(args)
    target = args[0]
    shell = null
    // PHASE 1: auto-exploit across common ports
    for port in COMMON_PORTS
        session = main_session.MetaxploitLib.net_use(target, port)
        if session then
            lib = session.dump_lib
            for area in main_session.MetaxploitLib.scan(lib)
                if try_exploit(target, port, lib, area) then
                    shell = result; break
                end if
            end for
        end if
    end for
    // PHASE 2: SSH brute if no shell
    if not shell then
        for u in BRUTE_USERS
            for p in BRUTE_PASSES
                test = get_shell.connect_service(target, 22, u, p)
                if typeof(test) == "shell" then shell = test
            end for
        end for
    end if
    // PHASE 3: auto-loot (read_configs)
    if shell then read_configs(shell)
end function
```

### Pattern 6: Theme system via Map-switching (V3)
Three themes in three separate maps, dynamic switch via `load_theme()`:

```greyscript
THEME_DEFAULT = {"red": "#e60000", "green": "#00ff00", "blue": "#000099", ...}
THEME_DARK    = {"red": "#ff4444", "green": "#44ff44", "blue": "#4444ff", ...}
THEME_OCEAN   = {"red": "#ff5577", "green": "#55ffaa", "blue": "#0055aa", ...}

current_theme = THEME_DEFAULT

style = function(text, color)
    if not current_theme.hasIndex(color) then return text
    return "<color=" + current_theme[color] + ">" + text + "</color>"
end function

load_theme = function(name)
    if name == "dark" then current_theme = THEME_DARK; return true
    if name == "ocean" then current_theme = THEME_OCEAN; return true
    if name == "default" then current_theme = THEME_DEFAULT; return true
    return false
end function
```

**Key insight:** A theme is just a Map of colour names → hex codes. `style()` looks up from the current map. Switching is a single assignment.

### Pattern 7: Macro system via `@<name>` prefix in main loop (V3)
Viper's macro trick. In the main loop, BEFORE splitting the first token into a command, check for `@`:

```greyscript
// In main loop, after parsing:
if cmd.indexOf("@") == 0 then
    macroName = cmd[1:]
    macroFile = pc.File(homeDir + "/Config/Macros/" + macroName)
    if not macroFile then continue
    for line in macroFile.get_content.split(char(10))
        if line == "" or line.indexOf("#") == 0 then continue
        lparts = line.split(" ")
        if commands.hasIndex(lparts[0]) then
            commands[lparts[0]].run(lparts[1:])
        end if
    end for
    continue
end if
```

Macros are plain text files in `/home/$USER/Config/Macros/`, one command per line, `#` for comments.

### Pattern 8: `getyuno` (tool-repo pattern) for cross-instance launching (V3)
Like Viper's `getviper`. To start another instance from inside the running shell:

```greyscript
cmd_getyuno.run = function(args)
    yunoPath = args[0]
    if not get_shell.host_computer.File(yunoPath) then
        print("Yuno not found!"); return
    end if
    argStr = args[1:].join(" ") if args.len > 1 else ""
    get_shell.launch(yunoPath, argStr)
end function
```

### Pattern 9: Version sync everywhere
When bumping versions, sync the version string in:
- The banner (3 `print(style(...))` lines)
- The help title line
- The credits title block
- Doc comments at the top of the file
- All References in `~/docs/system/`

Forgetting any one = confusing "is this V2 or V3?" moments later. Always grep the version string across the whole file before shipping.

## See also

- `templates/yuno-all-in-one.src` — V1 working template, 17 KB
- `~/docs/system/greyhack-yuno-v3-2026-07-03.md` — Full V3 architecture and DB IDs
- `references/storage-consolidation.md` — Why all-in-one is the right approach
- `~/docs/system/greyhack-yuno-v2-2026-07-03.md` — V2 architecture (45 KB interactive)
- `~/docs/system/greyhack-storage-cleanup-2026-07-03.md` — Cleanup workflow + DB-Edit patterns
</file_content>