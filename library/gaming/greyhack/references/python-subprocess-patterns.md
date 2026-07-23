# Python ↔ Greybel Subprocess Patterns

> **Stand:** 20. Juni 2026
> **Ziel:** greybel-js als Python-Subprozess steuern (build, execute, parse)
> **Voraussetzungen:** Node.js v20+, `npm install -g greybel-js`, Python 3.11+

## 1. greybel execute als Subprozess

```python
import subprocess
from pathlib import Path

def greybel_execute(src_path: str, params: list = None, env_vars: dict = None,
                     silent: bool = True, seed: int = None,
                     env_type: str = "Mock", timeout: int = 30) -> dict:
    """Führt ein GreyScript mit greybel execute aus."""
    src = Path(src_path)
    if not src.exists():
        return {"success": False, "stderr": f"File not found: {src}", "rc": 1, "lines": []}

    cmd = ["greybel", "execute", str(src)]
    if params:
        cmd.extend(["-p"] + [str(p) for p in params])
    if env_vars:
        for k, v in env_vars.items():
            cmd.extend(["-vr", f"{k}={v}"])
    if silent:
        cmd.append("-si")
    if seed is not None:
        cmd.extend(["-s", str(seed)])
    if env_type:
        cmd.extend(["-et", env_type])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    stdout_lines = [l.strip() for l in result.stdout.split("\n") if l.strip()]

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "rc": result.returncode,
        "lines": stdout_lines
    }
```

### Getestete CLI-Optionen

| Option | Funktion | Getestet |
|--------|----------|----------|
| `-p <args>` | CLI-Parameter durchreichen | params=["hello","world"] → `params = ["hello","world"]` |
| `-vr "K=V"` | Umgebungsvariablen setzen | funktioniert |
| `-si` | Silent mode (kein noise) | funktioniert |
| `-s <seed>` | Seed für Mock-Umgebung | funktioniert |
| `-et <type>` | Env type: Mock/In-Game | Mock getestet |
| `-d` | Debugger (REPL!) | NICHT für CI — hängt interaktiv |
| `-i` | Interaktive params | NICHT für Automatisierung |

## 2. greybel build als Subprozess

```python
def greybel_build(src_path: str, output_dir: str = None, uglify: bool = False) -> dict:
    """Kompiliert eine GreyScript-Quelldatei mit greybel-js."""
    src = Path(src_path)
    if not src.exists():
        return {"success": False, "stderr": f"File not found: {src}", "rc": 1}

    cmd = ["greybel", "build", str(src)]
    if uglify:
        cmd.append("-u")
    if output_dir:
        cmd.extend([output_dir, "-dbf"])
    cmd.append("-si")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    output_path = None
    if result.returncode == 0:
        output_path = str(Path(output_dir) / src.stem) if output_dir else str(src.with_suffix(""))

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "rc": result.returncode,
        "output": output_path
    }
```

## 3. JSON-Output parsen

```python
import json

def greybel_execute_json(src_path: str, params: list = None) -> dict:
    """Führt GreyScript aus und parst JSON-Output (letzte JSON-Zeile)."""
    result = greybel_execute(src_path, params=params)
    if not result["success"]:
        return {"success": False, "error": result["stderr"], "rc": result["rc"]}

    for line in reversed(result["lines"]):
        try:
            return {"success": True, "data": json.loads(line), "raw": result["stdout"], "rc": 0}
        except json.JSONDecodeError:
            continue

    return {"success": False, "error": "No valid JSON in output",
            "raw": result["stdout"], "rc": result["rc"]}

def parse_greybel_output(stdout: str, format: str = "lines") -> any:
    """Parst greybel Output: 'lines' | 'json' | 'keyvalue' | 'csv'"""
    lines = [l.strip() for l in stdout.split("\n") if l.strip()]
    if format == "lines":
        return lines
    elif format == "json":
        for line in reversed(lines):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        return None
    elif format == "keyvalue":
        result = {}
        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result
    elif format == "csv":
        return [line.split(",") for line in lines]
    return lines
```

## 4. Häufige Fehler

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `greybel execute -d` hängt | Debugger startet REPL → interaktiv | Nur manuell, nie in CI |
| `greybel build` crasht bei one-liner if | `-u` unterstützt kein einzeiliges if/then/end if | Immer multi-line |
| JSON-Parsing schlägt fehl | `print()` fügt `\n` hinzu | `strip()` vor `json.loads()` |
| `greybel execute` timeout | Script läuft endlos | Immer `timeout=30` |
| `-si` unterdrückt auch Fehler | Silent filtert stderr | Ohne `-si` für Debugging |
