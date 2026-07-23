# Ollama Model Storage Cleanup

Selective deletion of specific Ollama models while preserving others. Recipes,
pitfalls, and the storage-layout details you need before touching anything.

## Storage anatomy

Ollama keeps two layers per model on disk:

```
~/.ollama/models/
├── manifests/
│   ├── registry.ollama.ai/library/<model>/<tag>      # standard library
│   ├── registry.ollama.ai/<namespace>/<model>/<tag>  # custom namespace
│   └── hf.co/<namespace>/<model>/<tag>               # direct HF imports
└── blobs/
    └── sha256-<digest>                                # content-addressed
```

Each manifest is a JSON document listing `layers[].digest` and `size`. The
actual model weight files live in `blobs/` and are **shared by digest** — same
`sha256-abc...` is the same file (hardlinked or just same path reused).

**Critical consequence for cleanup:** if model A and model B share a 14 GB
layer (e.g. same Gemma-4 base weights, different LoRA), deleting A's manifest
without checking means you also need to keep that 14 GB blob — otherwise
B breaks.

## Multi-install detection (always do this first)

`ollama list` lies. It only shows models the *running* service has been told
about. On a typical Linux box you can have two parallel stores:

| Root                                   | Configured by                          |
|----------------------------------------|----------------------------------------|
| `~/.ollama/` (user)                    | `OLLAMA_MODELS` env or default         |
| `/usr/share/ollama/.ollama` (system)   | `/etc/systemd/system/ollama.service`   |
| `/var/snap/ollama/common/`             | Snap install                          |

Always identify which one the active service uses *and* which others exist:

```bash
# 1. Where does the running service actually read from?
systemctl show ollama -p ExecStart -p Environment --no-pager
ps -ef | grep -E "ollama serve" | grep -v grep

# 2. What's the size of every Ollama root you can find?
sudo du -sh /usr/share/ollama 2>/dev/null
du -sh ~/.ollama 2>/dev/null
sudo du -sh /var/snap/ollama 2>/dev/null

# 3. What's visible from ollama list?
ollama list

# 4. What's actually on disk?
find ~/.ollama/models/manifests /usr/share/ollama/.ollama/models/manifests \
     -name '*.json' -o -type f 2>/dev/null
```

In a typical session you'll find one root has 5 models and `ollama list`
shows 1 — that gap is your cleanup target.

## The two-step cleanup procedure

### Step 1 — Classify (dry-run)

Always show the user what would be deleted before touching anything. The
goal: build KEEP and DEL sets for both manifests and blobs.

**Key insight:** a blob is KEEP if *any* KEEP manifest references it. So:

```
KEEP_blobs = ⋃ {layer.digest for layer in m.layers for m in KEEP_manifests}
DEL_blobs  = all_blob_files − KEEP_blobs
```

See the dry-run script below for the full implementation.

### Step 2 — Execute (after explicit user OK)

```bash
# Always stop the service first so blobs aren't mmapped / locked
sudo systemctl stop ollama

# Delete manifests (cheap, safe — they're just JSON)
sudo rm -rf <manifest_path_1> <manifest_path_2> ...

# Delete orphaned blobs (big savings — these are the GB)
# IMPORTANT: use a bash script, NOT `sudo xargs rm` from a pipe.
# Sudo can't prompt for a password in a pipe and fails with
# "3 Fehlversuche bei der Passwort-Eingabe".
sudo bash /tmp/clean_blobs.sh

sudo systemctl start ollama

# Verify
ollama list
du -sh ~/.ollama /usr/share/ollama/.ollama
```

## Dry-run script (Python, tested 2026-07-03)

Save as `/tmp/ollama_dryrun.py` and edit `KEEP_FRIENDLY` to your set:

```python
"""Dry-run: identify which manifests and blobs would be deleted.

Touches NOTHING. Just prints the KEEP/DEL classification + exact rm commands.
"""
import json
import os

# Friendly names of models to KEEP, e.g. "yuxinlu1/<model>:Q8_0"
# Format: "<namespace>/<model>:<tag>" or "library/<model>:<tag>"
KEEP_FRIENDLY = {
    "yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q8_0",
}

MANIFEST_DIR = "/home/bratan/.ollama/models/manifests"
BLOBS_DIR = "/home/bratan/.ollama/models/blobs"


def to_friendly(rel_path):
    """Convert an Ollama manifest rel-path to '<ns>/<model>:<tag>'.

    Three layouts exist:
      registry.ollama.ai/library/<model>/<tag>           4 parts
      registry.ollama.ai/<ns>/<model>/<tag>              5 parts
      hf.co/<ns>/<model>/<tag>                           4 parts
    """
    parts = rel_path.split("/")
    if len(parts) < 4:
        return rel_path
    if parts[0] == "registry.ollama.ai" and parts[1] == "library":
        return f"library/{parts[2]}:{parts[3]}"
    if parts[0] == "registry.ollama.ai":
        return f"{parts[1]}/{parts[2]}:{parts[3]}"
    if parts[0] == "hf.co":
        return f"{parts[1]}/{parts[2]}:{parts[3]}"
    return rel_path


# Collect manifests with their friendly names + layer digests
manifests = []
for root, _, files in os.walk(MANIFEST_DIR):
    for f in files:
        path = os.path.join(root, f)
        with open(path) as fp:
            data = json.load(fp)
        rel = path.replace(MANIFEST_DIR + "/", "")
        friendly = to_friendly(rel)
        layers = data.get("layers") or []
        digests = {
            (l.get("digest") or "").replace("sha256:", "")
            for l in layers if l and l.get("digest")
        }
        size = sum(l.get("size", 0) for l in layers if l)
        manifests.append({
            "path": path, "rel": rel, "friendly": friendly,
            "digests": digests, "size": size,
        })

keep_manifests = [m for m in manifests if m["friendly"] in KEEP_FRIENDLY]
del_manifests  = [m for m in manifests if m["friendly"] not in KEEP_FRIENDLY]

keep_blobs = set()
for m in keep_manifests:
    keep_blobs |= m["digests"]

all_blob_files = {f for f in os.listdir(BLOBS_DIR) if f.startswith("sha256-")}
all_blob_digests = {f.replace("sha256-", "") for f in all_blob_files}
del_blob_files = sorted({f"sha256-{d}" for d in all_blob_digests - keep_blobs})


def blob_size(name):
    p = os.path.join(BLOBS_DIR, name)
    return os.path.getsize(p) if os.path.exists(p) else 0


total     = sum(blob_size(f) for f in all_blob_files)
keep_size = sum(blob_size(f"sha256-{d}") for d in keep_blobs)
del_size  = total - keep_size

# ---- REPORT ----
print(f"KEEP_FRIENDLY = {KEEP_FRIENDLY}\n")
print("KEEP-MANIFESTE:")
for m in keep_manifests:
    print(f"  KEEP  {m['friendly']}  ({m['size']/1024/1024/1024:.2f} GB)")
print("\nDEL-MANIFESTE:")
for m in del_manifests:
    print(f"  DEL   {m['friendly']}  ({m['size']/1024/1024/1024:.2f} GB)")
print(f"\nUSER-OLLAMA VORHER:  {total/1024/1024/1024:.2f} GB")
print(f"KEEP (geplant):      {keep_size/1024/1024/1024:.2f} GB")
print(f"DEL (geplant):       {del_size/1024/1024/1024:.2f} GB")
print(f"\n{len(del_manifests)} Manifeste + {len(del_blob_files)} Blobs wuerden geloescht.")
print("\n# Auszufuehrende Befehle (noch NICHT ausgefuehrt):")
print("sudo systemctl stop ollama\n")
for m in del_manifests:
    print(f'sudo rm -rf "{m["path"]}"')
print()
for chunk in [del_blob_files[i:i+3] for i in range(0, len(del_blob_files), 3)]:
    print("sudo rm -f " + " ".join(f'"{BLOBS_DIR}/{f}"' for f in chunk))
print("\nsudo systemctl start ollama")
```

## Cleanup bash script (the safe way to delete many blobs)

**Never** use `sudo | xargs rm` — sudo cannot prompt for a password over a pipe
and silently fails. Write a script and call `sudo bash`:

```bash
#!/bin/bash
# /tmp/clean_blobs.sh — delete all sha256 blobs except KEEP set
set -e
KEEP=(
  "sha256-18629e26f7b800357fe95ae3804c9be49af58ebc73e80754c301ebe997e29fbb"
  # add more sha256- prefixes here
)
shopt -s nullglob
cd /home/bratan/.ollama/models/blobs  # adjust to your root
count=0
for f in sha256-*; do
  skip=0
  for k in "${KEEP[@]}"; do
    [[ "$f" == "$k" ]] && { skip=1; break; }
  done
  [[ $skip -eq 0 ]] && { rm -fv "$f"; count=$((count+1)); }
done
echo "----"
echo "Geloescht: $count Dateien"
```

Run with:

```bash
sudo bash /tmp/clean_blobs.sh
```

## Path-parsing pitfalls (recurring bugs)

A naive `rel.split("/")[2]` approach fails because layouts differ:

| Path                                                          | Split result (after `manifests/`)      |
|---------------------------------------------------------------|----------------------------------------|
| `registry.ollama.ai/library/gemma4/12b`                       | 4 parts: `library` is index 1          |
| `registry.ollama.ai/pdurugyan/qwen3.5/9b`                     | 5 parts: namespace at index 1          |
| `hf.co/yuxinlu1/gemma-4-12B.../Q8_0`                         | 4 parts: ns at index 1, no "library"   |

If you write `parts[2]/parts[3]:parts[4]` and the path has 4 parts, you index
out of range or get the wrong friendly name. Always branch by prefix:

```python
if parts[0] == "registry.ollama.ai" and parts[1] == "library":
    # parts[2]=model, parts[3]=tag
elif parts[0] == "registry.ollama.ai":
    # parts[1]=ns, parts[2]=model, parts[3]=tag
elif parts[0] == "hf.co":
    # parts[1]=ns, parts[2]=model, parts[3]=tag
```

## Common verification commands after cleanup

```bash
# What the service sees now
ollama list
systemctl status ollama --no-pager | head -5

# Total disk usage across all known roots
du -sh ~/.ollama /usr/share/ollama/.ollama

# Spot-check a KEEP model still loads
timeout 30 ollama run <your-keep-model>:Q8_0 "Sag Hallo."
```

## Why this skill exists

On 2026-07-03 a user asked "wie viele ollama modelle habe ich, alle bis auf
gemma 4 löschen". The naive read of `ollama list` returned 1 model (12 GB),
but `~/.ollama/models/manifests/` contained 16 manifests spanning 75 GB —
including 7+ Gemma-4 variants, DeepSeek-R1, Qwen3.5, nomic-embed. The
`xentriom/...` model the user actually wanted to keep lived in the
*system* Ollama root (`/usr/share/ollama/.ollama`), separate from the
user root. A blind `rm -rf ~/.ollama` would have lost a working 12 GB
Gemma-4 and also broken the user-side `yuxinlu1` Coder model whose 14 GB
base blob was shared with `unsloth/BF16`. The dry-run-first procedure
above freed 63 GB cleanly with both KEEP models intact.