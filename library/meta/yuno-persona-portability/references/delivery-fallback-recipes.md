# Delivery Fallback Recipes — Bundle-to-Target Transportation

When the user wants a persona bundle delivered to a target (Drive, phone,
another agent), and the **direct upload path is blocked** (OAuth not set up,
tool missing, network unavailable), these recipes provide a friction-free
fallback ladder.

## Recipe 1: Google Drive (when `google-workspace` is `NOT_AUTHENTICATED`)

**Symptom:** `python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check` returns `NOT_AUTHENTICATED` or the skill is missing.

**Ladder of fallback options:**

### Option A — Manual drag-drop (0 setup)
```bash
# 1. Build the bundle ZIP on local disk
cd /home/bratan/workspace
zip -r /tmp/bundle.zip <bundle-dir>/

# 2. Report to user:
#    - Path: /tmp/bundle.zip
#    - Size: <bytes>
#    - MD5:  $(md5sum /tmp/bundle.zip)
#    - Folder URL: https://drive.google.com/drive/u/0/folders/<FOLDER_ID>

# 3. User drag-drops in Drive web UI — done in 5 seconds for ≤50 KB bundles
```

**User-side effort:** 1 drag-drop. No CLI, no setup.

### Option B — Telegram self-DM (0 setup)
```bash
# Telegram delivery to Basti's own chat (saves to phone automatically)
# Requires Hermes gateway with Telegram configured (check ~/.hermes/config.yaml
# for telegram.home_channel)
```

**User-side effort:** File appears in phone's Telegram app. Open → save to
Drive if needed (3 taps).

### Option C — QR code (when bundle ≤ 30 KB)
```bash
qrencode -o /tmp/bundle.png < /tmp/bundle.zip
# User scans with phone camera → opens Drive web UI → upload from camera roll
```

**User-side effort:** 1 scan + 1 upload.

### Option D — GitHub private gist
```bash
gh gist create --private <bundle-file>
# User clicks link on phone → "Save to Drive" from gist view
```

**User-side effort:** 1 tap save-to-drive.

### Option E — One-time OAuth setup (~10 min, then forever)
Only worth it if Drive uploads will happen frequently. See
`google-workspace` skill Step 2-5.

---

## Recipe 2: Direct upload to another agent (when target agent has no HTTPS endpoint)

**Symptom:** Target agent runs on local network with no public URL.

```bash
# SCP if SSH is available
scp -r /tmp/bundle/ user@target-host:/path/to/bundle/

# Or sneakernet if machines are physically close
# Or share via Telegram (see Recipe 1 Option B)
```

---

## Recipe 3: Cross-platform file share (when tools are limited)

| Tool | Bundle size limit | Setup |
|---|---|---|
| Telegram self-DM | 2 GB | 0 (if gateway configured) |
| Email attachment | 25 MB | 0 (with himalaya skill) |
| QR code | ~3 KB binary | 0 |
| Local LAN share | unlimited | 0 |
| Drive (via web UI) | unlimited | Drive account |
| Dropbox public link | unlimited | Dropbox account |
| GitHub gist | 100 MB per gist | 0 (gh CLI) |
| rsync | unlimited | SSH |

---

## Diagnostic: "Why didn't Drive upload work?"

Run this checklist when user asks for Drive upload:

```bash
# 1. Is the google-workspace skill installed?
test -f ~/.hermes/skills/productivity/google-workspace/scripts/setup.py \
  && echo "✓ skill installed" || echo "✗ skill missing"

# 2. Is OAuth set up?
python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check
# Expected: AUTHENTICATED
# If NOT_AUTHENTICATED → use fallback recipes above

# 3. Is gcloud authenticated? (looks similar but is GCP-only)
gcloud auth list 2>&1 | head -5
# Note: gcloud credentials ≠ Drive API tokens

# 4. Is rclone configured for Drive?
rclone listremotes | grep -i drive \
  && echo "✓ Drive remote configured" || echo "✗ no Drive remote"

# 5. Is gsutil here? (warning: GCS not Drive!)
which gsutil && echo "⚠ gsutil = GCS only, NOT Drive"
```

**If all checks fail:** Lead with Recipe 1 Option A (manual drag-drop). Do
NOT promise auto-upload.

---

## Real-world case (2026-07-04)

User said: "hau alles was MaxHermes braucht hier rein dann route ich darauf
google-drive://bastick123@gmail.com/0AGou6bsAJkh6Uk9PVA"

Attempted paths that failed:
- `mcp_github_*` → 401 (separate issue, not related)
- `gsutil cp` → not applicable (GCS, not Drive)
- `gcloud storage cp` → requires GCS bucket, not user's Drive
- `rclone copyto drive:...` → no Drive remote configured
- Direct `google-api-python-client` → no `google_token.json`

Resolution: Built ZIP at `/tmp/yuno-mobil-setup.zip` (36 KB, MD5
`ae9f765e3b536dcc7ddac37c0d90492b`), provided drag-drop path, user uploaded
manually. Bundle worked.

**Lesson:** When in doubt about cloud upload paths, build the artifact
locally FIRST and present manual delivery options. Don't spend tool calls
discovering dead-ends.