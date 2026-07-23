# Pattern: Bypass the PATH gotcha with `ln -sf` after every wrapper install

When you put a wrapper script in `~/50-System/bin/` (or any non-PATH directory), it is **not callable by name** until you symlink it into a real PATH directory (`~/.local/bin/`, `/usr/local/bin/`, or the system `/usr/bin/`). The user will get `command not found` even though the file is exactly where you put it.

**Symptom:**
```
$ minimax-code --check
bash: minimax-code: command not found
# (file exists at /home/bratan/50-System/bin/minimax-code with +x)
```

**Root cause:** `~/50-System/bin/` is a private scripts directory. It is **not** in `$PATH` for any standard Linux Mint / Ubuntu shell. The user's shell only searches `$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/snap/bin`.

**Fix (idempotent — can re-run as often as needed):**

```bash
# Primary: ~/.local/bin (no sudo, user-level)
ln -sf ~/50-System/bin/<name> ~/.local/bin/<name>

# Backup: /usr/local/bin (requires sudo)
sudo ln -sf ~/50-System/bin/<name> /usr/local/bin/<name>

# Verify it's now in PATH
which <name>     # should print the symlink path
command -v <name>  # same, but works in non-interactive shells
```

**Then either reload the shell or check explicitly:**

```bash
# If PATH doesn't include ~/.local/bin yet, add to ~/.profile or ~/.bashrc:
test -d "$HOME/.local/bin" && export PATH="$HOME/.local/bin:$PATH"

# Reload without logging out:
exec $SHELL    # or:  source ~/.bashrc
```

**Why this keeps biting:**

1. You create the wrapper at `~/50-System/bin/` (your private scripts dir)
2. You chmod +x it
3. You forget to symlink to a PATH dir
4. User tries `<name>` → "command not found"
5. User assumes the script is broken
6. **Reality:** Script is fine, just not in PATH

**Add a verification step to every wrapper install:**

```bash
# After ln -sf, ALWAYS run:
which <name> || echo "❌ Wrapper not in PATH"
```

**Lesson:** When you create ANY user-invokable command, **always** symlink it to a PATH directory as part of the same workflow. Treat `chmod +x` and `ln -sf` as one step.

## Real example from session 2026-07-08

```bash
# Created wrapper at ~/50-System/bin/minimax-code
chmod +x ~/50-System/bin/minimax-code
# User reports: "minimax-code: command not found"

# Fix:
ln -sf ~/50-System/bin/minimax-code ~/.local/bin/minimax-code
ln -sf ~/50-System/bin/minimax-code ~/bin/minimax-code    # backup
which minimax-code    # → /home/bratan/.local/bin/minimax-code ✅
```

## Same for desktop-file PATH registration

If a `.desktop` file uses `Exec=/path/to/script` with an absolute path that is not in PATH, the application launcher may fail silently. Use the symlink location:

```ini
[Desktop Entry]
Exec=/home/bratan/.local/bin/minimax-code   # not /home/bratan/50-System/bin/...
# OR rely on PATH:
Exec=minimax-code   # works if ~/.local/bin is in PATH
```

## Related

- `wine-electron-apps` SKILL.md — all wrappers in that domain follow the same pattern
- Bottles CLI itself has this issue (`flatpak run --command=bottles-cli ...` required)
- Linux Mint ships with `~/.local/bin` in `~/.profile` (loaded at login), so usually works after first login
