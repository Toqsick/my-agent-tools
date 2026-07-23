# greybel-js Path Resolution Workaround

**Problem:** greybel-js on the host searches for files at the exact `import_code()` path.
Tools in `~/greyhack-tools/` use `import_code("/home/Bratan/bin/lib_core")` — absolute paths
that don't exist on the host filesystem. The build fails with:
`"Dependency /home/bratan/greyhack-tools/home/Bratan/bin/lib_core does not exist..."`

**Fix (template):**

```bash
# 1. Temp-Verzeichnis mit korrekter Spiegelung des In-Game-Pfads
mkdir -p /tmp/gh-build/home/Bratan/bin

# 2. Alle .src-Dateien kopieren
cp ~/greyhack-tools/*.src /tmp/gh-build/home/Bratan/bin/

# 3. master_installer.src (importiert ALLE Tools) auch kopieren
cp ~/greyhack-tools/master_installer.src /tmp/gh-build/

# 4. Absolute import_code-Pfade auf relative umbiegen
sed -i 's|import_code("/home/Bratan/bin/\(.*\)")|import_code("\1.src")|' /tmp/gh-build/home/Bratan/bin/*.src

# 5. master_installer.src ins selbe Verzeichnis legen
cp /tmp/gh-build/master_installer.src /tmp/gh-build/home/Bratan/bin/

# 6. Build ausführen
cd /tmp/gh-build/home/Bratan/bin
npx greybel build master_installer.src --installer --uglify --ingame-directory /home/Bratan/bin

# 7. Installer auslesen
cat build/installer0.src
```

## Session-specific errors encountered and fixed
- `backdoor.src` line 28-29: `if ... then stealth = true\n    end if` → removed `end if`
- `hermes_api.src` lines 35-37: single quotes → double quotes with simpler text
- `hermes_api.src` and `hermes_daemon.src`: use `HTTP.Request()` → excluded from installer

## zKsav subfolder behavior
After the installer runs in game, greybel-uglify places files in a randomized subfolder (e.g. `zKsav/`) instead of directly in the target directory. **Fix:**
```
cp /home/Bratan/bin/zKsav/*.src /home/Bratan/bin/
build /home/Bratan/bin/build_all.src /home/Bratan/bin/build_all
build_all /home/Bratan/bin
launcher
```

## Pre-check: HTTP.Request files
GreyScript has NO `HTTP.Request()`. Before building with greybel-js, check which files use it:
```bash
grep -l "HTTP\.Request" ~/greyhack-tools/*.src
```
Exclude those files from `master_installer.src` — they will cause build errors.
