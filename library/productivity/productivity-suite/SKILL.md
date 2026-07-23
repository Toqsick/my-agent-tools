---
name: productivity-suite
description: >-
  Use when user asks for choosing a productivity integration, routing work across Airtable, Notion, Google Workspace, email, PDF, or PowerPoint tools, or planning a mixed office-automation workflow. NOT for deep troubleshooting of one integration or software build or CI automation. Acts as a gateway to the appropriate productivity skill and summarizes the supported command-line and API toolchain.
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - productivity
    - airtable
    - notion
    - google-workspace
    - email
    - pdf
    - powerpoint
    - apple
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['productivity', 'integration', 'the', 'and', 'productivity-suite']
keywords: ['productivity', 'integration', 'automation', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['mlops-suite', 'multi-agent-code-gen-pipeline']
---


# Productivity Suite

Covers: Airtable, Notion, Google Workspace, email (Himalaya), PDF editing, PowerPoint, Apple Notes/Reminders, Teams meetings.

## Airtable
```bash

set -euo pipefail
# REST API via curl
curl -s -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  "https://api.airtable.com/v0/{baseId}/{tableName}"
```

## Notion
```bash

set -euo pipefail
# ntn CLI or REST API
ntn pages list
ntn databases query --database-id $DB_ID
```

## Google Workspace
```bash

set -euo pipefail
# gws CLI for Gmail, Calendar, Drive, Docs, Sheets
gws auth login
gws gmail list --query "is:unread"
gws calendar list --days 7
```

## Email (Himalaya — IMAP/SMTP CLI)
```bash

set -euo pipefail
himalaya --account personal list
himalaya --account personal read 1
himalaya --account personal write
```

## PDF Editing
```bash

set -euo pipefail
# nano-pdf (NL prompts)
nano-pdf edit document.pdf "Fix typo on page 3"

# OCR
ocrmypdf input.pdf output.pdf
```

## PowerPoint
```python
from pptx import Presentation
prs = Presentation("deck.pptx")
# manipulate slides
prs.save("output.pptx")
```

set -euo pipefail
## Apple Notes/Reminders (macOS only)
```bash
# AppleScript or shortnotes CLI
shortnotes list
shortnotes create "Title" "Body"
```

## Teams Meeting Pipeline
See `references/teams-meeting-pipeline.md` for the full pipeline setup.
