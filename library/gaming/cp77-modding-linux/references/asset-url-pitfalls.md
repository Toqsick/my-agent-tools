# GitHub Asset URL Pitfall

`/releases/latest/download/` ist **UNZUVERLÄSSIG**. GitHub redirectet oft auf 404.

**FALSCH** (führt zu 404):
```
https://github.com/psiberx/cp2077-codeware/releases/latest/download/Codeware.zip  → ❌
```

**RICHTIG** (exakte Release-Tag-URL verwenden):
```
https://github.com/psiberx/cp2077-codeware/releases/download/v1.20.3/Codeware-1.20.3.zip  → ✅
```

Workflow:
1. `curl -fsSL "https://api.github.com/repos/<owner>/<repo>/releases/latest"` → `tag_name`
2. `browser_download_url` aus dem JSON lesen
3. Diese URL verwenden — **nicht** selbst zusammensetzen