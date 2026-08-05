# Sudoers-Setup für `get_firewall_state`

Das MCP-Tool `get_firewall_state` liest den UFW-Status und die lauschenden
TCP-Ports ab. Beide Kommandos benötigen root-Rechte:

- `ufw status verbose` — nur root sieht die vollständige Regel-Liste.
- `ss -tlnp` — nur root sieht die zu den Sockets gehörigen Prozesse.

Statt dem MCP-Server broad sudo zu geben, gibt es eine **eng begrenzte
NOPASSWD-Regel**, die genau diese beiden Read-Only-Kommandos für den
Workstation-User erlaubt.

## Voraussetzung: absolute Pfade verifizieren

`sudoers` matcht auf den exakten argv[0], den das Tool aufruft. Auf dieser
Workstation (Zorin OS 18.1) sind das:

```bash
command -v ufw ss
# /usr/sbin/ufw
# /usr/bin/ss
```

Falls die Pfade auf einer anderen Distribution abweichen, passe sowohl das
Sudoers-Snippet als auch die Konstanten `_UFW_BIN` / `_SS_BIN` in
`src/mcp_server_basti/server.py` an.

## Sudoers-Snippet installieren

Datei `/etc/sudoers.d/mcp-basti-firewall` (mode `0440`, root:root) anlegen:

```sudoers
# mcp-server-basti: erlaubt passwortlose, read-only Firewall-Inspektion.
# Installiert von Basti; Datei löschen, um get_firewall_state zu deaktivieren.
Cmnd_Alias MCP_BASTI_FW = /usr/sbin/ufw status verbose, /usr/bin/ss -tlnp
bratan ALL=(root) NOPASSWD: MCP_BASTI_FW
```

Installieren + validieren:

```bash
sudo install -m 0440 -o root -g root /dev/stdin /etc/sudoers.d/mcp-basti-firewall <<'EOF'
# mcp-server-basti: erlaubt passwortlose, read-only Firewall-Inspektion.
Cmnd_Alias MCP_BASTI_FW = /usr/sbin/ufw status verbose, /usr/bin/ss -tlnp
bratan ALL=(root) NOPASSWD: MCP_BASTI_FW
EOF
sudo visudo -c   # Syntax-Check; muss "parsed OK" melden
```

> Den User (`bratan`) und ggf. die Pfade an die eigene Box anpassen.

## Verifizieren

```bash
sudo -n /usr/sbin/ufw status verbose   # kein Passwort-Prompt → Regel greift
sudo -n /usr/bin/ss -tlnp
```

Danach liefert das MCP-Tool strukturierte `{ufw, listening_ports}` zurück.

## Degradation ohne die Regel

Ist die sudoers-Datei nicht installiert (oder die Pfade stimmen nicht), ruft
das Tool `sudo -n` auf. `sudo -n` scheitert **sofort**, statt ein Passwort zu
verlangen — der Tool fängt das ab und raiset einen `ToolError`, der auf diese
Datei verweist. Es gibt **keinen** stillen Partial-Result: der Contract ist
„Firewall-State oder ein klarer Fehler".

## Sicherheitshinweise

- Die Regel erlaubt **nur** die zwei genannten Read-Only-Kommandos mit exakten
  Argumenten — kein `ufw` ohne args, kein `ss` mit anderen Flags, keine Shell.
- `Cmnd_Alias` mit Komma-getrennten exakten Kommandos ist der sicherste
  sudoers-Mechanismus (kein Wildcard-Matching, das ausgenutzt werden könnte).
- Datei mode `0440` und root:root sind zwingend (sonst ignoriert sudo sie).
- Entferne die Datei, um das Tool zu deaktivieren — der Server advertised
  `get_firewall_state` weiterhin (Discovery ist statisch), aber Aufrufe
  degradieren sauber zu `ToolError`.