# Decision-Tree: Welches workflow-template?

> Schnellauswahl. Trigger-Wort → Template-Pfad.

## Kurzfassung (1-Liner)

```
Server härten           → 01-server-hardening
Repo/CI aufräumen       → 02-repo-cicd
Security/CVE            → 03-security-cve
GreyScript bauen        → 04-greyscript
Ollama/LLM optimieren   → 05-ollama-llm
Kombiniert              → Siehe `combinations.md`
```

## Langversion (Decision-Tree)

```
Was ist die Aufgabe?
│
├─ Server/Linux härten
│   ├─ Eigener Laptop (zorin-medion-2026-07-05)
│   │   → 01-server-hardening (mit "MEDION-Setup"-Profil)
│   ├─ GCP-VM / Cloud-Instanz
│   │   → 01-server-hardening (mit "Cloud-VM"-Profil)
│   ├─ Homelab (Self-Hosted, NAS, etc.)
│   │   → 01-server-hardening (mit "Homelab"-Profil)
│   └─ Produktivsystem mit Live-Traffic
│       → 01-server-hardening (mit "Production"-Profil + zusätzlicher Rollback-Pflicht)
│
├─ Bestehendes Repo aufräumen + CI/CD aufsetzen
│   ├─ GreyScript-Sammlung
│   │   → 02-repo-cicd (Profil: greyscript-lib)
│   ├─ Python (mit/ohne PyPI)
│   │   → 02-repo-cicd (Profil: python-package)
│   ├─ Obsidian-Vault / Markdown-Sammlung
│   │   → 02-repo-cicd (Profil: docs-vault)
│   ├─ Monorepo mit Sub-Packages
│   │   → 02-repo-cicd (Profil: monorepo)
│   └─ Statische Webseite / Hugo / MkDocs
│       → 02-repo-cicd (Profil: static-site)
│
├─ Security-Research / CVE-Analyse
│   ├─ Bekannte CVE mit Exploit-Datenbank
│   │   → 03-security-cve (Standard-Profil)
│   ├─ Eigenes System / Library auf Schwachstellen prüfen
│   │   → 03-security-cve (Profil: internal-audit)
│   └─ Exploit-Tool in GreyScript entwickeln
│       → 04-greyscript + 03-security-cve (kombiniert)
│
├─ GreyScript-Tool entwickeln
│   ├─ Multi-Tool / Service-Installer
│   │   → 04-greyscript (Profil: orchestration)
│   ├─ Netzwerk-Scanner / Port-Sniffer
│   │   → 04-greyscript (Profil: scanner)
│   ├─ Passwort-Cracker / Crypto-Tool
│   │   → 04-greyscript (Profil: crypto) + 03-security-cve (kombiniert)
│   └─ Library / Framework (.src-Datei für Re-use)
│       → 04-greyscript (Profil: library)
│
├─ Ollama / Lokales LLM-Setup
│   ├─ Erst-Setup auf neuem System
│   │   → 05-ollama-llm (Profil: greenfield)
│   ├─ Bestehendes Setup optimieren (Performance, GPU, Quant)
│   │   → 05-ollama-llm (Profil: optimize)
│   ├─ Idle-Problem (Modell bleibt resident, GPU-Konflikt mit Gaming)
│   │   → 05-ollama-llm (Profil: idle-mgmt) — Basti-spezifisch
│   └─ Multi-Modell-Routing aufsetzen
│       → 05-ollama-llm (Profil: routing)
│
└─ Kombiniert/multi-domain
    → Siehe `combinations.md`
```

## Konflikt-Resolution

Falls **mehrere** Templates passen:

| Wenn... | Dann... |
|---------|---------|
| Hauptaufgabe = A, A braucht B als Sub-Task | Lade A, integriere B als Phase |
| A und B sind gleichgewichtig | Lade beide, lasse Sub-Agents parallel laufen |
| A und B überlappen konzeptionell | Lade eines, dokumentiere den Overlap im Plan |

**Faustregel**: Nimm das Template, wo der Plan-Entscheidungsbaum entsteht. Das andere wird Sub-Task.

## Wenn keines passt

Falls **gar kein** Template passt:

1. Lade `multi-agent-master-workflow` (generisches Pattern)
2. Oder lade `plan` (Implementation-Plan ohne Domain-Kontext)
3. Falls regelmäßig dasselbe fehlt: Issue aufmachen, Template vorschlagen
