# Standard Tool Skeleton & lib_core Pattern

> Canonical patterns for every tool. Keep these in sync with `templates/lib_core.src`.
> The "boring repetition across tools" is intentional — predictable structure = easier debugging.

## Standard Tool Skeleton

```greyscript
import_code("/home/Bratan/bin/lib_core")
ctx = getContext
shell = ctx["shell"]
pc = ctx["pc"]

showHelp("ToolName", "description", "toolname <arg1>", ["toolname 1.2.3.4"])

arg = requireParam(0, "arg")
if not validIP(arg) then fail("Bad IP")
end if

banner
render("ToolName", ["Target: " + arg])

// main logic with ok()/warn()/fail()/step(n,total,msg) for progress

logToFile(pc, "/home/Bratan/.logs/toolname.log", "summary")
```

## Bulletproof Hello World (verified API only)

```greyscript
print("")
print("  ==========================")
print("     HELLO GREYHACK!")
print("  ==========================")
print("")
pc = get_shell.host_computer
print("My LAN IP: " + pc.lan_ip)
print("")
print("Welcome to GreyHack!")
print("")
```

**What works:** `get_shell.host_computer`, `pc.lan_ip`, `print()`.
**What crashes:** `get_shell.get_name`, `get_shell.get_user`, anything not in `references/api-objects.md`.

## Debugging a first-script crash

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `command not found` | Typed code in shell, not in .src file | Write a .src file, build, run |
| `Runtime Error: Key Not Found: 'X' not found in map` | Method `X` doesn't exist on this object | Check `references/api-signatures-verified.md` |
| `Build error` at compile time | Syntax issue in .src file | Check `references/language-pitfalls.md` |
| Runs but shows nothing | Forgot `print()` around the value | GreyScript doesn't auto-print return values |
