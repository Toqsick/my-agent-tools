# Mnemosyne-Disziplin für workflow-template

**Standardregel**: Nach jeder Session, in der ein workflow-template eingesetzt wurde, **eine** `mnemosyne_remember`-Call aus dem Template-spezifischen Hook.

## Standard-Param

```python
mnemosyne_remember(
    content="<template-spezifischer Hook-Output>",
    importance=<0.6-0.9>,    # siehe Template-Tabelle
    source="<domain>",       # siehe Template-Tabelle
    extract_entities=True,   # immer wenn möglich
    veracity="<tool|stated>"
)
```

## Template → Hook-Mapping

| Template | Importance | Source | Veracity-Beispiel | Hook-Content-Pattern |
|----------|------------|--------|-------------------|----------------------|
| 01-server-hardening | 0.7 | security-audit | "tool" für Messungen | `Server-Hardening Session <system>: angewendet: <block>, Tests bestanden: <ja/nein>, Restrisiko: <offene>` |
| 02-repo-cicd | 0.6 | devops | "tool" für CI-Status | `Repo-Cleanup <name>: Typ=<typ>, Branches reorganisiert: <ja/nein>, CI: <lint+test+release>, Restarbeiten: <links>` |
| 03-security-cve | 0.8 | security-research | "tool" für CVE-Daten | `CVE-Analyse <CVE-ID>: Befund=<kurz>, Klassifikation=<CWE>, CVSS=<wert>, Lab-Test=<bestanden/offen>, Research-Log=<pfad>` |
| 04-greyscript | 0.7 | greyhack | "tool" für Build-Result | `GreyScript-Tool <name>: Zweck=<x>, Grösse=<kb>, Libraries=<list>, Dependencies=<list>, Build-Pipeline=<greybel-js/in-game>, Pitfalls-getroffen=<list>` |
| 05-ollama-llm | 0.8 | ai-infrastructure | "tool" für Benchmarks | `Ollama-Setup Basti: Models=<list>, Quant=<default>, num_ctx=<default>, Service-Mode=<always/idle/timer>, GPU-Konflikt=<gelöst/offen>` |

## Hook-Beispiele pro Template

### 01-server-hardening
```python
mnemosyne_remember(
    content="Server-Hardening Session zorin-medion 2026-07-05: angewendet: ssh-config-restrict, firewall-block-none, fail2ban-init; Tests bestanden: ja (zweite ssh-session offen); Restrisiko: fluidsynth 9800 weiter offen",
    importance=0.7, source="security-audit", extract_entities=True, veracity="tool"
)
```

### 02-repo-cicd
```python
mnemosyne_remember(
    content="Repo-Cleanup greyhack-tools 2026-07-05: Typ=greyscript-lib, Branches reorganisiert: nein (nur main+develop), CI: keine; Restarbeiten: 14 offene Bugs aus danielstein/* analysieren",
    importance=0.6, source="devops", extract_entities=True, veracity="tool"
)
```

### 03-security-cve
```python
mnemosyne_remember(
    content="CVE-Analyse CVE-2026-XXXXX 2026-07-05: Befund=SQL-Injection in user/profile-endpoint, Klassifikation=CWE-89, CVSS=7.5 estimated, Lab-Test=bestanden, Research-Log=~/docs/system/cve-2026-xxxxx.md",
    importance=0.8, source="security-research", extract_entities=True, extract=True, veracity="tool"
)
```

### 04-greyscript
```python
mnemosyne_remember(
    content="GreyScript-Tool scanner_v2 2026-07-05: Zweck=netzwerk-port-scanner, Grösse=8.3kb, Libraries=metaxploit+lib_core_v2.2, Dependencies=metaxploit.so, Build-Pipeline=greybel-js, Pitfalls-getroffen=0-truthy in counter (gefixt via != null check)",
    importance=0.7, source="greyhack", extract_entities=True, veracity="tool"
)
```

### 05-ollama-llm
```python
mnemosyne_remember(
    content="Ollama-Setup Basti 2026-07-05: Models=[qwen2.5-coder:7b-q5,qwen2.5:7b-q4,deepseek-coder:6.7b-q5], Quant=Q5_K_M, num_ctx=8192, Service-Mode=idle-via-api-keep-alive=0, GPU-Konflikt=gelöst (nvidia-powerd, gaming-pause vor request)",
    importance=0.8, source="ai-infrastructure", extract_entities=True, veracity="tool"
)
```

## Hook-Best-Practices

1. **Immer pro Session** — nicht "sammeln und am Ende zusammen".
2. **Content sachlich**, keine Aussagen wie "Cool!", "Funktioniert super!" → nur Beobachtungen.
3. **Pfade konkret** — `~/path/to/file.md` statt "Doku".
4. **Restrisiko explizit** — auch wenn null. "Restrisiko: keines" ist Information.
5. **Veracity korrekt** — `tool` für `terminal/output`, `stated` für explizite Basti-Aussagen, `inferred` für eigene Ableitungen.

## Workflow-Schritt-Checkliste (Pro Session)

- [ ] Template-Einsatz gestartet → Hook-Inhalt vorbereiten
- [ ] Session läuft → Hook-Inhalt bei Findings ergänzen
- [ ] Session-Ende → `mnemosyne_remember`-Call ausführen
- [ ] Antwort an Basti → Mnemosyne-Call-ID zeigen (zur Verification)
