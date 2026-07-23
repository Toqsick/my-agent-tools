# GitHub Authentication

Setup authentication for GitHub operations.

## gh CLI Authentication

```bash
# Interactive login
gh auth login

# Token-based login
echo "<token>" | gh auth login --with-token

# Check status
gh auth status
```

## HTTPS Token Authentication

```bash
git config --global credential.helper store
# Paste token on first operation
```

## SSH Authentication

```bash
ssh-keygen -t ed25519
# Add public key at https://github.com/settings/keys
```

## API Authentication without gh CLI

```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/...
```