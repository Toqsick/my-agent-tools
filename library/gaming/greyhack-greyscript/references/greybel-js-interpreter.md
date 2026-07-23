# greybel-js Interpreter & Testing Workflows

Verified 2026-06-27 against greybel-js 2.x and greybel-vs 2.8.13.

## greybel-js CLI Commands

```bash
# Execute in Mock Environment
greybel execute script.src -et Mock -si

# Build (compile) to binary
greybel build script.src /tmp/output/ -dbf

# Import into game (requires BepInEx message-hook on port 8332)
greybel import script.src -pt 8332
```

## Mock Environment (`-et Mock`)

The Mock Environment simulates GreyScript without the game. Uses `greybel-gh-mock-intrinsics` under the hood.

### What WORKS in Mock:
- `include_lib("/lib/metaxploit.so")` → returns object
- `include_lib("/lib/crypto.so")` → returns object
- `get_shell.host_computer` → returns Computer object
- `pc.public_ip`, `pc.local_ip` → return strings
- `pc.get_name()` → returns string
- Basic print/output flow
- Parameter parsing (`params`, `params.len`)
- All language constructs (loops, conditionals, functions, maps, lists)

### What DOES NOT work in Mock (verified 2026-06-27):
- `include_lib("/lib/net.so")` → returns null
- `computer.ConfigOS` → null
- `computer.users` → Runtime error: "Path not found in map"
- `computer.FileSystem.GetFolder("/")` → Runtime error
- `computer.File(path)` → Runtime error
- `shell.connect_service()` → not functional
- `meta.net_use()` → not functional
- **`fail()` NOT available** (discovered 2026-07-07) — `fail("reason")` is an **in-game GreyScript shell function** (`Fail` class in `Shell.cs`), NOT exposed in greybel's Mock Environment. Mock execution throws `Runtime error: Path "fail" not found in map` when any code calls `fail()`. Greybel's `build` succeeds (compile-time only checks syntax), but `execute -et Mock` crashes at the call site.
  - **Workaround for testing:** Use a `fail`-shim that falls back to `print`:
    ```
    if typeof(fail) != "function" then
        fail = function(msg)
            print("[FAIL] " + msg)
        end function
    end if
    ```
  - **Impact:** GreyScript test files (`tests.src`) that use `fail()` for assertions cannot run via `greybel execute` without a shim. The existing codebase's test pattern (`parse-exploit-reqs/tests.src`) only works in-game.

**Conclusion:** Mock is ONLY for syntax/flow validation. For real API testing, use in-game execution.

## greybel-vs Extension (VSCode)

Repository: `github.com/ayecue/greybel-vs`

### Setup
```bash
git clone https://github.com/ayecue/greybel-vs.git ~/greybel-vs
cd ~/greybel-vs
npm install
npm run compile
```

### Launch Extension Development Host
```bash
code --extensionDevelopmentPath=./greybel-vs test-workspace/
```

### Commands (CTRL+SHIFT+P)
- `Greybel: Build file from context` — compile .src
- `Greybel: Run/Debug file from context` — execute in Mock
- `Greybel: Import file into the game` — requires message-hook
- `Greybel: API` — browse API reference
- `Greybel: Preview output` — in-game-like output preview

### Settings (`.vscode/settings.json`)
```json
{
  "greybel.interpreter.seed": "test",
  "greybel.interpreter.environmentType": "mock",
  "greybel.createInGame.active": false
}
```

## In-Game Testing (No BepInEx)

Without message-hook, the only way to test scripts is manual copy-paste:

1. **Host:** `cat script.src` → copy output
2. **In-Game CodeEditor:** New → paste → Save → Build → Run
3. **OR In-Game Terminal:**
   ```
   cat > /home/Bratan/bin/script.src
   [paste content]
   [Enter]
   [Ctrl+C]
   build /home/Bratan/bin/script.src /home/Bratan/bin/script
   script
   ```

## Official API Documentation

The canonical API reference is in the greyscript-meta npm package:
```
node_modules/greyscript-meta/dist/descriptions/en/*.json
```

Key files:
- `metaxploit.json` — Metaxploit API
- `net-session.json` — NetSession API  
- `meta-lib.json` — MetaLib/overflow API
- `shell.json` — Shell API
- `computer.json` — Computer API
- `file.json` — File API
- `crypto.json` — Crypto API

Online: https://documentation.greyscript.org (often outdated)
