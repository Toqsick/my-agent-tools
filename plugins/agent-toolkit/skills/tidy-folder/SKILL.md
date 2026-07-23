---
name: tidy-folder
description: "Professional folder cleanup and organization assistant. Safely organizes and cleans up directories by scanning contents, recommending cleanup rules, creating mandatory backups before any operation, and using move-to-trash instead of delete. Supports Linux/macOS and Windows (PowerShell). Trigger keywords: tidy, cleanup, organize folder, clean directory, folder organization."
---

# TidyFolder — Safe Folder Cleanup & Organization

## Overview

TidyFolder helps users safely and efficiently organize and clean up folders. The core principle is **Data Safety First** — all operations create backups before changes, and files are moved to trash rather than deleted. It supports Linux/macOS and Windows (PowerShell only) systems.

## Workflow

### Step 1: Environment Check

First, check if currently running in a cloud/sandbox environment or local desktop environment.

- **If cloud/sandbox environment** → Inform user: "This feature requires access to your local file system. Please use TidyFolder in the desktop app." Then offer general folder organization tips and best practices as an alternative.
- **If local desktop environment** → Proceed with the normal workflow below.

### Step 2: Understand Requirements

1. Identify the user's target directory (user-mentioned directory > working directory)
2. **Scan and analyze directory contents**, intelligently recommend cleanup/organization rules based on actual situation:
   - Analyze file type distribution, file sizes, modification dates, etc.
   - Identify potential issues (e.g., excessive temp files, duplicate files, oversized files, long-untouched files)
   - Based on analysis results, propose 2-4 targeted cleanup/organization suggestions for user selection

   **Example Output Format:**
   > I analyzed your directory and found the following:
   > - Found 156 .log files, occupying 2.3GB
   > - 23 files larger than 100MB exist
   > - 45 files haven't been modified in over 90 days
   >
   > **Suggested options:**
   > - **A.** Clean up all .log files (estimated 2.3GB freed)
   > - **B.** Organize files larger than 100MB into a separate folder
   > - **C.** Archive files not modified in 90 days

3. After user confirms selection, proceed to backup step

### Step 3: Mandatory Backup (MUST Execute)

**Before executing any cleanup operation, must create backup archive first!**

#### Linux/macOS Systems:
```bash
# Create timestamped backup
tar -czvf "backup_path/backup_$(date +%Y%m%d_%H%M%S).tar.gz" "target_folder_path"
```

#### Windows Systems (MUST use PowerShell):
```powershell
# Create timestamped backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "target_folder_path" -DestinationPath "backup_path\backup_$timestamp.zip"
```

### Step 4: Execute Cleanup

**The following deletion commands are STRICTLY FORBIDDEN:**
- ❌ `rm`, `rm -rf`, `rm -r`
- ❌ `Remove-Item`, `del`, `rmdir`
- ❌ Any command that directly deletes files or folders

**Only use move commands:**

#### Linux/macOS Systems:
```bash
# Create trash directory
mkdir -p ~/.local/share/Trash/files

# Use mv command to move files to trash
mv "file_or_folder_to_clean" ~/.local/share/Trash/files/
```

#### Windows Systems (MUST use PowerShell):
```powershell
# Create trash directory
$trashPath = "$env:USERPROFILE\.cleanup_trash"
New-Item -ItemType Directory -Force -Path $trashPath

# Use Move-Item command to move files
Move-Item -Path "file_or_folder_to_clean" -Destination $trashPath
```

### Step 5: Report Results

After each cleanup operation, provide a clear report:
- Backup file location and size
- Number of moved files and total size
- Trash directory location
- Instructions on how to restore moved files

## Safety Rules

1. **Backup First**: Never start cleanup without completing backup
2. **Confirmation Mechanism**: Confirm file list to be moved with user before cleanup
3. **Move Instead of Delete**: All "deletion" operations are implemented by moving to trash directory
4. **Keep Records**: Log all move operations for easy user recovery

## Windows System Special Notes

When executing commands on Windows systems:
- **MUST use PowerShell**, do not use CMD
- Use `Compress-Archive` for compression
- Use `Move-Item` for moving
- Use backslashes `\` for paths or escaped forward slashes

## Common Mistakes to Avoid

- Never skip the backup step, even for small cleanups
- Never use `rm`, `Remove-Item`, `del`, or any deletion command — always move to trash
- Never operate without user confirmation of the file list
- Never assume the environment is local — always check first
- Never use CMD on Windows — always use PowerShell
