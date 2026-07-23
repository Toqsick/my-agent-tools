# Template-Kombinationen

> **Hinweis**: Existiert nur als Stub. Wird in v1.1 ausgebaut (siehe Changelog "Lessons Learned").

## Bekannte Kombinationen

### Exploit-Tool in GreyScript

**Templates**: `04-greyscript` + `03-security-cve`

**Reihenfolge**:
1. `03-security-cve` Standard-Profil für Scope-Guardian + Recon
2. `04-greyscript` für Architektur + Library-Scout + Code
3. Vor Phase-2-Codegeneration: erneuter Ethics-Legal-Review-Pass für jede explizite Exploit-Funktion

**Mnemosyne-Hook**: doppelt (security 0.8 + greyhack 0.7)

### Ollama-Server auf gehärtetem VPS

**Templates**: `01-server-hardening` + `05-ollama-llm` (Profil: greenfield)

**Reihenfolge**:
1. `01-server-hardening` zuerst — Cloud-VM-Profil
2. `05-ollama-llm` als Sub-Block 5 im Hardening-Plan

**Mnemosyne-Hook**: doppelt (security-audit 0.7 + ai-infrastructure 0.8)

### Repo-Audit mit Security-Audit

**Templates**: `02-repo-cicd` + `03-security-cve` (Profil: internal-audit)

**Reihenfolge**:
1. `02-repo-cicd` für Repo-Hygiene
2. `03-security-cve` als zusätzlicher Sub-Agent für Dependency-Scan + Secret-Scan

**Mnemosyne-Hook**: doppelt (devops 0.6 + security-research 0.8)

### GreyHack-Tool mit Auto-Build in Repository

**Templates**: `04-greyscript` + `02-repo-cicd`

**Reihenfolge**:
1. `02-repo-cicd` (`greyscript-lib`-Profil) zuerst — Repo-Struktur
2. `04-greyscript` als Sub-Task im Repo-Workspace

**Mnemosyne-Hook**: doppelt (devops 0.6 + greyhack 0.7)

## Kombinations-Disziplin

1. **Einmal-Pass pro Template**: kein Doppel-Review.
2. **Mnemosyne-Hook pro Template**: nicht zusammenfassen — separater Speicher-Eintrag ist Information-Density-Boost.
3. **Reihenfolge in Changelog dokumentieren**.

## Geplante Erweiterungen (v1.1+)

- Explizite Decision-Tree-Tabelle für "Welche Kombi?"
- Test-Templates für die Kombis
- Cross-Template-Rollback-Plan-Generator
