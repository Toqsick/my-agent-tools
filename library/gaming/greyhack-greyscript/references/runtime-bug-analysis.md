# Runtime Bug Analysis for Compiling Sources

A file that BUILDS successfully may still fail at runtime. When a user reports "build passes but crashes when I run `<cmd>`", do NOT just re-check compiler bugs — the error is a runtime crash (`Key Not Found`, `Path "X" not found in`, `Variable not declared`). Run this distinct audit after confirming the file compiles cleanly.

## Ordered scan — check in this sequence

### 1. Undefined module-level variables — `commands` dict missing

Each module needs its own `commands` dict registered BEFORE the main dispatch block. If a module accesses `commands.hasIndex(cmd)` or `commands[cmd].run(cmdArgs)` but `commands` is never defined locally, Runtime Error `Variable not declared`. This is the #1 modularization mistake.

```greyscript
// BUG: main dispatch references undefined variable
if params.len > 0 then
    cmd = params[0]
    ...
    if commands.hasIndex(cmd) then    // ← CRASH: 'commands' not declared
        commands[cmd].run(cmdArgs)
    else
        print(style("[!] Unknown: " + cmd, "red"))
    end if
end if

// FIX: register local command dict before dispatch
commands = {
    "corruptlogs": @cmd_corruptlogs,
    "nslookup": @cmd_nslookup,
    "whois": @cmd_whois,
    "sniffer": @cmd_sniffer,
    "coop": @cmd_coop,
}
```

**Verification:** search for `commands[cmd]` or `commands.hasIndex`, then walk backward to see if `commands = {` precedes it in the same module.

### 2. Missing fields on shared state objects (YUNO_SHARED/main_session)

When a module stores state on `main_session.someField`, that field MUST be initialized in the initializer module (`yuno_core`). If it's only set when a specific command runs, it may not exist when another module tries to READ it.

```greyscript
// BUG: netcatList accessed in cmd_coop but not in main_session init
// yuno_core initializes:
main_session = {"version":"6.0.0", "exit":false, ...}
// yuno_crypto_net does:
peerId = "peer_" + str(main_session.netcatList.len + 1)  // ← CRASH: Key Not Found

// FIX: initialize in yuno_core's dict:
main_session = {"version":"6.0.0", "exit":false, ..., "netcatList": {}}
```

**Verification:** search for ALL `main_session.<field>` accesses across modules, then check the `main_session` init dict in `yuno_core` for each one. Every field must either be initialized to a sensible default (empty list `[]`, empty map `{}`, `null`, `0`, `""`) OR be guarded by `if not main_session.hasIndex("field") then main_session.field = default` before first use.

### 3. API results used without type check

Several GreyScript API calls return DIFFERENT types on success vs failure — most critically `connect_service` (returns `Service` on success, STRING error on failure). Always `typeof()` before use.

```greyscript
// BUG: result used as Service unconditionally
listener = shell.connect_service("127.0.0.1", port)
// listener might be a string like "Connection refused"
// Using listener as Service object crashes

// FIX:
result = shell.connect_service("127.0.0.1", port)
if typeof(result) == "string" then
    print(style("[!] Connection error: " + result, "red"))
    return
end if
listener = result
```

**Known API calls where type varies:**

| API call | Success type | Failure type |
|----------|-------------|-------------|
| `shell.connect_service(ip, port)` | `Service` | `string` (error) |
| `meta.scan_address(lib, addr)` | `map` (info) | `null` |
| `lib.overflow(addr, val)` | `Shell`/`Computer`/`File`/`Number`/`String` | `null` or error string |
| `sniffer.next` | `map` (packet) | `null` |
| `pc.File(path)` | `File` | `null` |
| `crypto.smtp_user_list(ip, port)` | `list` | `null` or `string` |

### 4. Dead code from API calls — result assigned but never used

When an API call assigns its result to a variable that is NEVER referenced again, it's either dead code (remove it) or a missing type check + error handling step. This is particularly dangerous because it looks correct (the variable exists) but silently discards error information.

```greyscript
// BUG: listener variable assigned but never used — error swallowed
listener = shell.connect_service("127.0.0.1", port)
main_session.netcatList[peerId] = {...}
// listener is never read again — the connection might have failed silently
```

**Verification:** for every `variable = someAPI(...)` call, search forward for subsequent references to `variable`. If none exist, it's either dead code (remove) or missing error handling (add typeof check + return on failure).

### 5. Fields accessed without `hasIndex` guard on map-literals

GreyScript crashes with `Key Not Found` when accessing a map field that doesn't exist. Unlike objects, maps have NO default `null` return. Each dynamic field access must be guarded:

```greyscript
// BUG: unchecked access
if main_session.netcatList.len == 0 then ...   // ← crash if netcatList doesn't exist

// FIX with hasIndex guard:
if main_session.hasIndex("netcatList") and main_session.netcatList.len == 0 then ...
// OR initialized default in main_session (preferred, see #2)
```

## Priority order for this audit

#1 first (most common modularization bug), then #2 (most destructive — crashes on module load, not just command execution), then #3+#4 (API safety — silent data loss unless caught), then #5 (defensive programming).

## Real-world benchmark

`yuno_crypto_net.src` (175 lines, 6KB) had 3 runtime bugs: #1 (commands dict missing), #2 (netcatList not in main_session), #4 (listener assigned but unused). All compiler-clean. All found in <5 minutes with this ordered audit.