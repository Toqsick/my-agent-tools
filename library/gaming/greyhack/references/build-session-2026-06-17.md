# GreyHack Build Session 2026-06-17 — Detailed Notes

## greybel-js Build Results

### Successful Builds (11/12)
| Tool | Lines (uglified) | Import Dependency |
|------|-------------------|-------------------|
| lib_core | 157 | none (base lib) |
| portscan | 80 | lib_core |
| metaxploit | 154 | lib_core |
| decypher | 72 | none (uses crypto.so directly) |
| routerinfo | 75 | lib_core |
| wifi_crack | 74 | lib_core |
| forcer | 36 | none |
| scp_upload | 68 | lib_core |
| ps | 61 | lib_core |
| smtp_enum | 104 | lib_core |
| grsa | 131 | none |

### Failed Builds (1/12)
| Tool | Problem | Fix Complexity |
|------|---------|----------------|
| xmem | 44 `function`, only 22 `end function` | Manual rewrite needed |

## greybel-js Import Path Bug — Details

### Bug Description
`greybel build` resolves relative `import_code` paths incorrectly:
- Source: `greyhack-tools/portscan/portscan.src` with `import_code("../lib_core/lib_core.src")`
- Expected: resolves to `greyhack-tools/lib_core/lib_core.src`
- Actual: resolves to `/root/lib_core/lib_core.src` (wrong root!)

### Root Cause
greybel-js uses `/root/` as the base directory for relative imports, regardless of the actual source file location.

### Workaround
Copy source files directly without greybel-js, then fix import paths with sed:
```bash
cp source.src bin/source.src
sed -i 's|import_code("../lib_core/lib_core.src")|import_code("lib_core")|g' bin/source.src
```

Or use the deploy script: `/home/bratan/bin/greyhack-deploy`

## Regex Replace Double-Paren Bug

When using Python `re.sub` to replace import paths, the replacement can create double closing parens if the pattern doesn't account for existing trailing parens.

```python
# CORRECT — match the full import_code(...) pattern:
content = re.sub(r'import_code\("[^"]*"\)', 'import_code("lib_core")', content)
```

Always verify with `grep -n 'import_code' file.src` after bulk replacements.

## is_folder vs is_binary — Definitive Guidance

- `is_folder` IS a valid GreyScript API method but unreliable for edge cases
- `is_binary` is more reliable: `true` = file, `false` = directory
- Best practice: use `is_binary` for file-vs-directory checks, null-check first

```greyscript
f = pc.File(path)
if not f then fail("Not found: " + path)
if f.is_binary then
  // It's a file
else
  // It's a directory
end if
```

## Fileserver & Host IP

- Host IP: `192.168.178.92` (check with `hostname -I`)
- Fileserver: Port 8765, serves `~/greyhack-tools/`
- Start: `cd ~/greyhack-tools && python3 ~/bin/temp_fileserver.py &`

## Mission: Reraldi@adahidomev.net

- IP: 154.19.190.206
- Tools needed: portscan, metaxploit, decypher
- decypher_v3.src: fixed `get_shell.host_computer` 4x → 1x
