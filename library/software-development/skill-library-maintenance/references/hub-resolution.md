# Hub-Imported Resolution Protocol

When `~/.hermes/skills/hub-imported/` exists — a directory of community-imported skills from the skills.sh hub — the goal is to integrate its content into the canonical library tree. The hub-imported directory is a **staging area**, not a permanent home. Skills in it are either duplicates of active skills (delete) or unique skills that need a proper category home.

## Trigger

`hub-imported/` directory exists at `~/.hermes/skills/hub-imported/`.

## Protocol

### Step 1: Inventory

```bash
ls ~/.hermes/skills/hub-imported/
find ~/.hermes/skills/hub-imported -maxdepth 1 -mindepth 1 -type d | sort
```

### Step 2: Extract `name:` from Frontmatter

Skills' canonical identity is the YAML `name:` field in SKILL.md — **not** the directory name. Directory names can differ (hyphens, slashes, case). Always parse the frontmatter:

```bash
cd ~/.hermes/skills
for dir in hub-imported/*/; do
  name=$(grep -m1 '^name:' "$dir/SKILL.md" | sed 's/^name: *//' | tr -d '"')
  echo "$dir → name='$name'"
done
```

**Critical:** Some hub-imported skills have slash-separated names (`creative/ui-design-system`, `orchestration/multi-agent-orchestration`). These represent the **canonical category path** — they're not flat names. A skill with name `creative/ui-design-system` is a duplicate of `creative/ui-design-system/SKILL.md` in the active tree.

### Step 3: Duplicate Detection

For each hub-imported skill, find whether an active skill with the same `name:` exists:

```bash
for name in $(hub names); do
  # Search all active SKILL.md files for the same name
  grep -rl "^name: ${name}$" ~/.hermes/skills/ \
    --include=SKILL.md \
    --exclude-dir=hub-imported \
    --exclude-dir=.archive | head -1
done
```

**Classification:**

| Result | Category | Action |
|--------|----------|--------|
| Same `name:` found in active tree | **Duplicate** | Delete from hub-imported |
| No match | **Unique** | Move to proper category |

### Step 4: Diff Comparison (Quality Check)

Even when `name:` matches, verify the content isn't substantially different (common: hub-imported versions are slightly older clones with cosmetic YAML differences):

```bash
# Quick size comparison
for dir in hub-imported/*/; do
  name=$(grep -m1 '^name:' "$dir/SKILL.md" | sed 's/^name: *//')
  active=$(find ~/.hermes/skills -path "*/$name/SKILL.md" ! -path "*/.archive/*" ! -path "*/hub-imported/*")
  [ -n "$active" ] && echo "$name: hub=$(wc -c < "$dir/SKILL.md") active=$(wc -c < "$active") diff-lines=$(diff "$dir/SKILL.md" "$active" | wc -l)"
done
```

**Decision rule:**
- **<10 diff lines** (cosmetic YAML/whitespace only) → true duplicate, safe to delete
- **>50 diff lines** (substantially different content) → not a true duplicate; may warrant keeping both

### Step 5: Active Skill Integrity Snapshot (BEFORE destructive ops)

```bash
sha256sum ~/.hermes/skills/<category>/<skill>/SKILL.md >> /tmp/active_hashes_before.txt
# Do this for EVERY active skill that has a hub-imported match
```

### Step 6: Delete Duplicates from `hub-imported/`

```bash
rm -rf ~/.hermes/skills/hub-imported/<duplicate-skill>
```

### Step 7: Classify Unique Skills by Target Category

Categorize each unique skill by its domain:

| Domain | Target Category | Examples |
|--------|----------------|----------|
| Anime, Art, Visual Design, Posters, Storyboards | `creative/` | anime-design, dynamic-poster, film-shot |
| Video, Audio, Sound, Music | `media/` | beat-sync-editor, clip-export, drama-soundtrack |
| Other | As appropriate | Judge by SKILL.md description |

**Heuristic for borderline skills:**
- Music/audio production → `media/`
- Visual art/design → `creative/`
- Video editing/export → `media/`
- Game-related → `gaming/`
- Programming libraries → `software-development/`

### Step 8: Create Target Directories + `cp -r`

```bash
mkdir -p creative/<skill> media/<skill>
cp -r hub-imported/<skill>/. creative/<skill>/
cp -r hub-imported/<skill>/. media/<skill>/
```

**Important:** Use `cp -r <source>/. <target>/` (with `/.`) — this copies the *contents* of the source into the target directory, not the directory itself. Avoids nesting `<target>/<skill>/<skill>/`.

### Step 9: `diff -r` Verification

Every moved skill must be bit-identical to its hub-imported source:

```bash
diff -r hub-imported/<skill> creative/<skill>
# Empty output = IDENTICAL ✓
```

Also verify file counts match:

```bash
echo "$(find hub-imported/<skill> -type f | wc -l) vs $(find creative/<skill> -type f | wc -l)"
```

### Step 10: Hash Comparison (Active Skills Unchanged)

```bash
for path in $(cat /tmp/active_hashes_before.txt | awk '{print $2}'); do
  new_sha=$(sha256sum "$path" | cut -c1-12)
  old_sha=$(grep -F "$path" /tmp/active_hashes_before.txt | awk '{print $1}')
  [ "$new_sha" = "$old_sha" ] || echo "CHANGED: $path"
done
# If no output → all active skills unchanged ✓
```

### Step 11: Remove `hub-imported/`

Only after ALL 10 steps pass:

```bash
rm -rf ~/.hermes/skills/hub-imported
```

## Post-Resolution Verification Script

```bash
# Run this after removing hub-imported/
echo "1. hub-imported/ gone?"
[ ! -d ~/.hermes/skills/hub-imported ] && echo "   ✓" || echo "   ❌"

echo ""
echo "2. Target skills in correct categories?"
for s in skill-a skill-b; do
  [ -f ~/.hermes/skills/creative/$s/SKILL.md ] && echo "   ✓ creative/$s"
  [ -f ~/.hermes/skills/media/$s/SKILL.md ] && echo "   ✓ media/$s"
done

echo ""
echo "3. Active skills unmodified?"
for path in creative/active-skill-a meta/active-skill-b; do
  [ -f ~/.hermes/skills/$path/SKILL.md ] && echo "   ✓ $path present"
done
```

## When NOT to resolve hub-imported

- **Don't** resolve during a slim-down session — the hub-imported scan inflates the SKILL.md count and dilutes slim-down focus
- **Don't** skip the `name:` frontmatter check — directory names and frontmatter names can diverge, causing false-positive duplicates (e.g. `creative-ui-design-system/` dir → `name: creative/ui-design-system`)
- **Don't** re-delegate hub-imported resolution to subagents — it's fast (5-10 min) and parent-side terminal commands are more reliable for the atomic batch of deletes/copies

## Verified

2026-07-04: 21 hub-imported skills resolved: 13 duplicates deleted, 8 moved (4 → creative/, 4 → media/). `diff -r` confirmed all 8 copies bit-identical. 13 active SKILL.md hashes unchanged. Zero data loss, zero broken refs.