# Pattern (f) Backslash-Escape Fix — Session Reference (2026-07-07)

Concrete fix transcript from one agent batch. Reference for any agent hitting the same pattern in `greyhack-tools` or related `.src` repos.

## What was fixed

Four `.src` files in `greyhack-tools/` had `\"` (or `\\`) escapes inside string literals. All four were migrated to `char()` calls and verified backslash-free + `greybel build` clean (3/4 builds green; 1 out-of-scope import failure).

## Files & exact diffs

### `src/recon/mission_report.src:107`
```diff
-	safe = safe.replace("\", "_")
+	safe = safe.replace(char(92), "_")
```
Note: tab indent preserved. Patch tool initially stripped tabs — restored with `sed -i '106,109s/^/\t/'`.

### `greyhack-tools/minitest/testApi.src:25`
```diff
-        printer("expected \""+value1+"\" to be equal to \""+value2+"\"")
+        printer("expected "+char(34)+value1+char(34)+" to be equal to "+char(34)+value2+char(34))
```

### `greyhack-tools/portscan/portscan.src:107`
```diff
-    info("Nutze \"metaxploit\" oder \"auto_exploit\" fuer weitere Analyse")
+    info("Nutze "+char(34)+"metaxploit"+char(34)+" oder "+char(34)+"auto_exploit"+char(34)+" fuer weitere Analyse")
```
Build fails on `import_code("/home/Bratan/bin/lib_core")` — environment issue, NOT this fix. Pattern (f) is complete.

### `greyhack-tools/dankestein/secure.src:111`
```diff
-    print("can\"t access folders")
+    print("can"+char(34)+"t access folders")
```

## Backups created
`*.bak-20260707-095031` next to each modified file.

## Full report
`/tmp/fix-report-agent-c.md` (6223 bytes, sentinel `##AGENT_C_DONE##`).

## Generalization

Any `.src` file in the greyhack-tools family with the literal text `\"` or `\\` inside a string is a Pattern (f) candidate. Run the verification checklist from SKILL.md before declaring done:

```
rg "\\\\" <files>            # must be 0
greybel build <src> <out> -dbf   # must say "Build done"
```