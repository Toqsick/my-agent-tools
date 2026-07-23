---

name: apple-notes
description: 'Use when user asks for apple notes, Prerequisites, When to Use, When NOT to Use. NOT for Android, Windows. Manages Apple Notes via the memo CLI on macOS.'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- macos
metadata:
  hermes:
    tags:
    - Notes
    - Apple
    - macOS
    - note-taking
    related_skills:
    - obsidian
prerequisites:
  commands:
  - memo
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['apple', 'notes', 'not', 'apple-notes', 'prerequisites']
keywords: ['apple', 'notes', 'user', 'asks', 'prerequisites']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['apple-reminders', 'findmy', 'imessage']
---



# Apple Notes

Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

## When to Use

- User asks to create, view, or search Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Exporting notes to Markdown/HTML

## When NOT to Use

- Obsidian vault management → use the `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes → use the `memory` tool instead

## Quick Reference

### View Notes

```bash

set -euo pipefail
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create Notes

```bash

set -euo pipefail
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title
```

### Edit Notes

```bash

set -euo pipefail
memo notes -e                     # Interactive selection to edit
```

### Delete Notes

```bash

set -euo pipefail
memo notes -d                     # Interactive selection to delete
```

### Move Notes

```bash

set -euo pipefail
memo notes -m                     # Move note to folder (interactive)
```

### Export Notes

```bash

set -euo pipefail
memo notes -ex                    # Export to HTML/Markdown
```

## Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

## Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management
