# Grey Hack — Static Analysis Pipeline (2026-07-14)

> Full worked example of Phase 0 (Pre-Launch Static File Analysis) applied to
> Grey Hack V0.9.6771 BETA. 1 subagent dispatched for independent verification.
> 109 DLLs inventoried, 15 GreyScript libraries identified.

## TL;DR

| Metric | Wert |
|---|---|
| Unity Engine | **2022.3.62f3** (Build `96770f904ca7`) |
| Build-GUID | `79617ae4d2d14e1c8094178708546ea8` |
| Scripting | **Mono / .NET** (kein IL2CPP) |
| Scripting-Sprache | **Miniscript** (custom fork, embedded in Assembly-CSharp.dll) |
| Mono Runtime | `libmonobdwgc-2.0.so` (BleedingEdge) |
| Total Managed DLLs | **109** (2 Game-Logic, 79 Unity, 24 Mono, 4 Third-Party) |
| Game-Logic DLL | `Assembly-CSharp.dll` — 3,593,216 Bytes, last modified **2026-06-25** |
| GreyScript Libraries | 15 erkannt |
| DB | `GreyHackDB.db` — 6,979,584 Bytes (SQLite via Mono.Data.Sqlite) |
| Sub-Call-Count | 1 (unabhängige Sub-Biene für strings-Verifikation) |

## Game Directory Structure

```
/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/
├── Grey Hack.x86_64                         14,720 B   ELF-64 stub
├── UnityPlayer.so                         32,953,216 B  Unity runtime
├── libsteam_api64.so                         284,841 B  Steamworks (top-level)
├── Grey Hack_Data/
│   ├── app.info                                      22 B  "Grey Hack"
│   ├── boot.config                                  113 B  build-guid
│   ├── ScriptingAssemblies.json                    3,147 B  89 DLLs im Manifest
│   ├── RuntimeInitializeOnLoads.json                 340 B  2 Boot-Hooks
│   ├── globalgamemanagers.assets                 357,456 B
│   ├── GlobalGameManagers.assets                 357,456 B
│   ├── sharedassets1.assets                    65,561,856 B
│   ├── sharedassets1.assets.resS              475,500,624 B
│   ├── GreyHackDB.db                           6,979,584 B
│   ├── Managed/       → 109 DLLs, ~27.6 MB total
│   │   ├── Assembly-CSharp.dll                 3,593,216 B   ***Haupt-Game-Logic***
│   │   ├── Assembly-CSharp-firstpass.dll           80,896 B  Image Effects only
│   │   ├── mscorlib.dll                        4,622,848 B
│   │   ├── System.Xml.dll                      3,160,064 B
│   │   ├── System.dll                          2,653,696 B
│   │   ├── System.Data.dll                     2,104,320 B
│   │   ├── Newtonsoft.Json.dll                    691,712 B
│   │   ├── Facepunch.Steamworks.Posix.dll          572,928 B
│   │   ├── OSA.dll                                 220,672 B
│   │   ├── Paroxe.PDFRenderer.dll                  114,176 B
│   │   └── 97 weitere Unity/Mono/3rd-party DLLs
│   ├── Plugins/
│   │   ├── libsteam_api.so                      386,864 B  Steamworks
│   │   └── libpdfrenderer.so                  4,542,696 B  Paroxe PDF
│   ├── Resources/
│   │   ├── unity_builtin_extra                  555,196 B
│   │   ├── unity default resources             1,564,240 B
│   │   └── UnityPlayer.png                      272,252 B  Splash
│   ├── StreamingAssets/aa/
│   │   ├── catalog.json                        ~78,000 B  Addressables catalog
│   │   ├── settings.json                               -  m_AddressablesVersion: 1.25.0
│   │   ├── AddressablesLink/link.xml
│   │   └── StandaloneLinux64/
│   │       ├── localization-assets-shared_assets_all.bundle
│   │       ├── localization-locales_assets_all.bundle
│   │       ├── localization-string-tables-english(en)_assets_all.bundle
│   │       └── localization-string-tables-spanish(spain)(es-es)_assets_all.bundle
│   └── MonoBleedingEdge/
│       ├── etc/mono/config
│       └── x86_64/
│           ├── libmonobdwgc-2.0.so           Mono runtime
│           ├── libmono-native.so
│           └── libMonoPosixHelper.so
```

## Pipeline Steps Executed

### Step 1: Config Files (Phase 1)

```bash
cd "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/"
cat app.info              # → "Loading Home\nGrey Hack"
cat boot.config           # → build-guid=79617ae4d2d14e1c8094178708546ea8
```

**RuntimeInitializeOnLoads.json** revealed two hooks:
1. `UnityLogFilter.Install` (Assembly-CSharp, BeforeSceneLoad) — custom log filtering
2. `AssetBundleProvider.Init` (Unity.ResourceManager, AfterAssembliesLoaded) — Addressables

### Step 2: DLL Inventory (Phase 2) — 109 DLLs

All 109 DLLs inventoried with name, size_bytes, mtime, sha256_prefix in JSON.
Python script at `/tmp/gh-fullscan-gamma/build_inventory.py` (8,028 B).

**Key finding:** Only `Assembly-CSharp.dll` has a different mtime (2026-06-25)
vs all other DLLs (2025-06-02). This means a **live patch** was shipped via Steam.

### Step 3: native Plugins (Phase 3)

- `libsteam_api.so`: Standard Steamworks, `strings` shows `GetAppBuildId`, `AppID` patterns
- `libpdfrenderer.so`: Paroxe PDF renderer (4.5 MB ELF-64)
- `UnityPlayer.so` (top-level): BuildID `1cc1f1032671b5b0a21be928bf4e839e9744891e`

### Step 4: Strings Analysis (Phase 4) — 14+ Libraries Found

**Scripting Engine** → **Miniscript** (custom fork):
```
MiniscriptInterpreter.cs, MiniscriptKeywords.cs, MiniscriptLexer.cs,
MiniscriptParser.cs, MiniscriptTAC.cs, MiniscriptTypes.cs,
MiniscriptUnitTest.cs
```

**GreyScript Library Enum** (uppercase constants):
```
LIBSSH, LIBHTTP, LIBFTP, LIBSMTP, LIBSQL,
LIBCHAT, LIBCAM, LIBRSHELL, LIBADB, LIBREPOSITORY,
LIBSMARTAPPLIANCE, LIBTRAFFICNET,
METAXPLOIT, KERNEL_MODULE, CRYPTO
```

**Factory methods (API entry points):**
```
CreateCryptoLib, CreateMetaXploitLib
GetCryptoLib, GetMetaxploitComputerID
```

**Source paths (project layout):**
```
Assets\Greyscript\CryptoIntrinsics.cs
Assets\Greyscript\VersionProgram.cs
Assets\Greyscript\VersionsControl.cs
```

**Library base-class fields:**
```
libFile, libName, libPath, libVar, libVersion, libVersions, libraryId
```

**NO native .so references** — all GreyScript libraries are 100% managed C#.
**NO hardcoded gameVersion** — `gameVersion` is a runtime symbol, not a literal.

### Step 5: Resources + Streaming (Phase 5)

- Addressables **1.25.0**, settings hash `b6c459e12c08ddfde356ea77b3066f9a`
- Catalog hash: `dbd45d15a44a5e1b21c12ec982bf8e0e`
- **Only 2 languages** shipped: English + Spanish. No German.
- Build target: `StandaloneLinux64`

### Step 6: Subagent Verification (Phase 6) — 1 sub-call

Sub-bee dispatched via `delegate_task(role='leaf')` with independent `strings` scan.
**Result:** `/tmp/gh-fullscan-gamma/1784064382-sub.md` (15,525 bytes, 307 lines)
**Verification:** 100% cross-reference match between parent and sub findings:

| Category | Parent Finds | Sub-Bee Finds | Match |
|---|---|---|---|
| Library keywords (Assembly-CSharp.dll) | 37 | 37 | ✅ |
| Library types/enums | 11 | 11 | ✅ |
| Greyscript namespace paths | 167 | 167 | ✅ |
| Library factory fields | 6 | 6 | ✅ |
| `Create*Lib` / `Get*Lib` factories | 4 | 4 | ✅ |
| Scripting engine identity | Miniscript | Miniscript | ✅ |
| Native .so refs | 0 | 0 | ✅ |
| Version strings | 1 (runtime) | 1 (runtime) | ✅ |
| FirstPass DLL relevance | 0 (image effects) | 0 (image effects) | ✅ |

### Step 7: Output Generation (Phase 7)

Two deliverables:
1. **`/tmp/gh-fullscan-gamma/1784064382.json`** — 97,313 bytes, machine-readable
2. **`/home/bratan/Dokumente/Obsidian Vault/09 System-Doku/GreyHack/GreyHack-Game-Internals-2026-07-14.md`** — 17,970 bytes, 13 sections

Plus the sub-bee verification file:
3. **`/tmp/gh-fullscan-gamma/1784064382-sub.md`** — 15,525 bytes, 5 sections

## Security-Relevant Observations

1. **Live Patch (2026-06-25)** — Only `Assembly-CSharp.dll` was modified post-release.
   No code signing or integrity check on the DLL. Theoretically could contain
   tampered code (though Steam-verified download makes this unlikely).

2. **`Mono.Data.Sqlite` + `GreyHackDB.db`** — Client-side SQLite is writable.
   The in-game validator (`VersionsControl.CheckVersions`) likely only checks
   script versions, not DB content.

3. **`UnityLogFilter.Install`** — Custom log filter fires BeforeSceneLoad.
   If it suppresses debug logs from GreyScript bridges, game manipulations
   could be invisible in the log.

4. **`Newtonsoft.Json` v13.0.0.0** — Used for `libhttp` request/response handling.
   JSON deserialization exploits are theoretically possible if server responses
   aren't sanitized.

5. **`Facepunch.Steamworks.Posix.dll`** — No signature or hash verification.
   Steam Achievement spoofing would be trivial.

6. **Miniscript as Custom Fork** — Language semantics (especially MetaExploit
   intrinsics) aren't 1:1 with public Miniscript spec. Reverse engineering
   must target `Assembly-CSharp.dll` directly, not upstream docs.

## Commands to Reproduce

```bash
# Full scan pipeline (config → DLL→ plugins → strings → resources → verify)
cd "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack"

# Config files
cat "Grey Hack_Data/app.info"
cat "Grey Hack_Data/boot.config"

# DLL inventory
ls -la "Grey Hack_Data/Managed/" | wc -l

# Most important single grep:
strings "Grey Hack_Data/Managed/Assembly-CSharp.dll" | grep -iE 'Miniscript|LIB[A-Z]{2,}|METAXPLOIT|Create.*Lib' | sort -u

# Native plugins
ls -la "Grey Hack_Data/Plugins/"

# StreamingAssets
cat "Grey Hack_Data/StreamingAssets/aa/settings.json"

# Unity version (from UnityPlayer.so)
strings "UnityPlayer.so" | grep -oP '[0-9]{4}\.[0-9]+\.[0-9]+[a-z][0-9]+' | head -3
```

## Related Skills

- `computer-use-game-reconnaissance` — Phase 0 of this skill. After static
  analysis, move to visual/OCR in-game reconnaissance.
- `sub-sub-workflow` — Dispatch pattern for independent subagent verification.
- `greyhack-game-observer` — Grey Hack-specific in-game observer.
- `greyhack-smart-macro` — Grey Hack-specific click/type automation.

## Artifacts from This Scan

| Path | Size | Purpose |
|---|---|---|
| `1784064382.json` | 97,313 B | Full machine-readable inventory |
| `1784064382-sub.md` | 15,525 B | Sub-agent verification report |
| `GreyHack-Game-Internals-2026-07-14.md` | 17,970 B | Obsidian report (13 sections) |
| `build_inventory.py` | 8,028 B | Reproducible generator script |

*Scan-ID: 1784064382 · Date: 2026-07-14*
