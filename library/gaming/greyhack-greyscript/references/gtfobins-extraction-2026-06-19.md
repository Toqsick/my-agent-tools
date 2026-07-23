# GTFOBins Extraction — GreyHack SUID Exploit Tool

> Stand: 19. Juni 2026
> Methode: API-Extraktion via GitHub Tree API + Einzelabruf der YAML-Frontmatter

## Datenquelle

GTFOBins (https://gtfobins.github.io) — 478 Unix-Binaries mit dokumentierten
LPE/Shell/FileRead/FileWrite-Techniken. Rohdaten als Markdown + YAML-Frontmatter
unter `_gtfobins/<binaryname>` im GitHub-Repo GTFOBins/GTFOBins.github.io.

**Kein JSON-Endpunkt verfügbar.** `api.json` ist ein Jekyll-Template, kein API-Output.
Die echten Daten stecken in den individuellen Dateien unter `_gtfobins/`.

## Extrahierte Daten

```python
# 63 Key-Binaries extrahiert via curl + Frontmatter-Parse
# Ergebnis: ~/docs/system/gtfobins-greyhack-database.json (15.6 KB)

key_bins = [
    'bash', 'find', 'python', 'perl', 'php', 'node', 'lua',
    'vim', 'nmap', 'awk', 'env', 'expect', 'strace', 'tcpdump',
    'socat', 'zip', 'tar', 'screen', 'tmux', 'script', 'xargs',
    'rsync', 'scp', 'docker', 'systemctl', 'gdb', 'sqlite3', 'wget',
    'chattr', 'chmod', 'chown', 'cp', 'mv', 'install', 'mount',
    'setcap', 'setfacl', 'unsquashfs', 'unzip',
    # ... und 22 weitere
]
```

## Ergebnis

| Kategorie | Count | Beispiele |
|-----------|-------|-----------|
| SUID Shell | 31 | bash, python, find, vim, nmap, docker |
| SUID LPE | 10 | cp, chmod, chown, mount, setcap, unzip |
| Sudo LPE | 50 | bash, docker, find, python, vim, nmap |

## GreyScript Tool: `suid_exploit.src`

Pfad: `src/tools/suid_exploit.src` im `greyscripts` Repo.

Features:
1. `suid_exploit local` — durchsucht das lokale System nach SUID-Binaries
2. Matcht gefundene Binaries gegen 40+ GTFOBins-Techniken
3. Zeigt für jedes Binary den Exploit-Befehl (Shell-Spawn oder LPE-Pfad)
4. Unterstützt: bash -p, python os.execl, find -exec, vim :!sh, nmap --interactive uvm.

### In-Game Install

```greyscript
pc = get_shell.host_computer
pc.wget("http://192.168.178.92:8765/src/tools/suid_exploit.src", "/home/Bratan/bin/suid_exploit.src")
shell = get_shell
shell.build("/home/Bratan/bin/suid_exploit.src", "/home/Bratan/bin/suid_exploit")
pc.File("/home/Bratan/bin/suid_exploit.src").delete
suid_exploit local
```

## API Extraktions-Rezept

```bash
# 1. Alle 478 Binary-Namen abrufen
curl -sL 'https://api.github.com/repos/GTFOBins/GTFOBins.github.io/git/trees/master?recursive=1' | \
  python3 -c "import sys,json;d=json.load(sys.stdin);[print(i['path'].replace('_gtfobins/','')) for i in d['tree'] if i['path'].startswith('_gtfobins/')]"

# 2. Einzelnes Binary abrufen
curl -sL "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/_gtfobins/find"

# 3. SUID-Binaries suchen (im Frontmatter nach 'suid:' suchen)
for bin in find python cp; do
    curl -sL "https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/master/_gtfobins/$bin" | grep -c "suid:"
done
```

## Fazit

GTFOBins ist eine hervorragende Quelle für GreyHack-LPE-Tools. Die 31 SUID-Shell-Binaries
decken die häufigsten Escalation-Pfade ab, die auch in GreyHack-Missionen vorkommen.
Das `suid_exploit` Tool automatisiert den Abgleich und zeigt dem Spieler sofort
die nutzbaren Exploit-Befehle.