# Hermes V7.1 Umsetzung — FINALER PLAN (approved: kompletter Plan, Branch feat/security-kernel)

## Kontext
`~/Dokumente/Perplexity/reop plan.md` (Perplexity-Export, nur Prosa — Code existiert nirgends) beschreibt V7.1:
P0 Skill-Supply-Chain-Sicherheit, P1 Architektur (ContextEngine, tool-use Self-Registration), Memory-Konsolidierung, Profile.
Ziel-Repo: `~/30-Library/hermes-v7` (Node18+/TS5.5, Jest+ts-jest inline in package.json, Coverage-Gate 70%,
Branch `feat/security-kernel`, nur .gitignore dirty — NICHT mit committen). Remote Toqsick/hermes-v7 — NICHT pushen, nur lokal committen.
`~/.hermes/` (Home) UND `.hermes/` im Repo (Live-Kopie inkl. mnemosyne.db) sind tabu. Tests nur mit mkdtemp-Pfaden.

## Entscheidungen (Defaults übernommen)
E1 beides: optionales `provenance` in v7.skill-schema.json + eigenes Sidecar-Schema `config/hub-skill.provenance-schema.json`
E2 `provenance.json` Sidecar pro Hub-Skill, wird MIT gehasht; meta.yaml bleibt byte-treu
E3 handgeschriebene Validierung (kein ajv) · E4 dependency-freier Mini-YAML-Parser (flache key:value) · E5 CLI via `tsc && node dist/...`
E6 startup-guard config-getrieben: `HermesConfig.security.skillIntegrity` + `deps`-Injection, Kernel unverändert
E7 CI-Job in ci.yml · E8 Push-Filter um `feat/**` erweitern · E9 `src/profile/`

## Phase 1 (P0) — Dateien
- `src/security/skill-integrity.ts` NEU: computeSkillHash (sha256-tree-v1: rekursiv, Symlink=Fehler, POSIX-Pfade byte-lexikografisch sortiert, sha256(concat(relPath+"\0"+fileHashHex+"\n"))), loadAllowlist, validateProvenance, verifySkillIntegrity → SkillIntegrityReport
- `src/security/types.ts`: SkillAllowlist(Entry), SkillIntegrityViolation/Report/Mode; HermesConfig.security.skillIntegrity?: {enabled, mode?, allowlistPath?, skillsDir?}
- `src/security/index.ts`: Re-Exports
- `config/v7.skill-schema.json`: + optionales provenance-Objekt
- `config/hub-skill.provenance-schema.json` NEU
- `skills/hub-imported/<21>/provenance.json` NEU (generiert via CLI init-provenance aus meta.yaml: hubVersion, trustTier aus source:, importedAt 2026-07-03 laut git log von c07b058 — prüfen!)
- `cli/skill-integrity.ts` NEU: approve|verify|init-provenance; npm-Scripts skills:verify (strict, exit 1) / skills:approve
- `config/skill-allowlist.json` NEU: {schemaVersion:1, algorithm:"sha256-tree-v1", skills:{"hub-imported/<name>": {hash,version,approvedBy,approvedAt,trustTier}}}
- `src/security/startup-guard.ts`: runStartupGuard(cfg, deps?) — skillIntegrity nur wenn enabled; strict→errors (Kernel wirft), warn→warnings
- `.github/workflows/ci.yml`: Job skill-integrity (npm run skills:verify); push-Filter + feat/**
- Tests: `src/security/__tests__/skill-integrity.test.ts` (+__fixtures__/skills/hub-imported/demo-skill/), `startup-guard.test.ts`; kernel.test.ts UNVERÄNDERT lassen

## Phase 2 (P1)
- tool-use (CJS, additiv): defaultRegistry, registerTool(def), discoverTools(dir=__dirname/tools); `tools/echo.js`+`shell.js`(dangerous)+`http-fetch.js` mit Self-Registration; Test auto-discovery.test.js; ToolRegistry/DANGEROUS_PATTERNS unverändert
- `src/context/`: types.ts (ContextEngine: name, currentTokens, needsCompression, compress, apply; ContextSnapshot/Plan), registry.ts (register/get wirft fail-closed/list), noop-engine.ts, naive-engine.ts (= exakt heutige buildReducedScopeTask-Logik aus depp-worker: 0.5^retryIndex, min 128, [REDUCED SCOPE RETRY n]), index.ts (Import = Self-Registration)
- `src/depp/depp-worker.ts`: 4. Konstruktor-Param contextEngine = getContextEngine('naive'); buildReducedScopeTask ersetzt; VOR Refactor Outputs als Fixture einfrieren (Äquivalenztest)

## Phase 3
- `src/storage/mnemosyne-store.ts`: MNEMOSYNE_SCHEMA_VERSION=2, schema_meta.json (fehlt+Entries=v1→lazy nicht-destruktive Migration nur im baseDir), Banks: baseDir/banks/<bank>/, 'default' bleibt flach; write/read/allEntries mit bank='default'-Param, listBanks(); Map<bank,Map<key,entry>>; MemoryEntry.bank? auch in src/core/types.ts (sonst Typbruch split-brain-resolver)
- `src/storage/memory-provider.ts` NEU: MemoryProvider-Interface (onSessionStart, preLlmCall→MemoryInjection, postToolCall, close) + MnemosyneMemoryProvider (naive Keyword-Suche, Redaction via security/redact)
- Tests storage/__tests__ (NUR mkdtemp!)

## Phase 4
- `src/profile/`: types.ts (ProfileConfig: name, security, skills{mode local|hub_imported, dir?}, contextEngine?, memory?), hermes-profile.ts (HermesProfile.bootstrap: Kernel.startup → Skills (local=SkillLoader via require+`.d.ts`-Stub; hub_imported=NEUER hub-skill-index.ts, liest provenance.json+SKILL.md, führt NICHTS aus) → getContextEngine (wirft) → MnemosyneStore/Provider (default baseDir NIE homedir, z.B. `.hermes-profiles-data/<name>/mnemosyne`)), shutdown()
- `config/profiles/default.json`; ROADMAP.md: Context-Ring-UI Backlog (kein WebUI im Repo, nur src/dashboard/html-export.ts)

## Commit-Sequenz (deutsch, Stil wie Historie; jeder Commit grün: tsc --noEmit + npm test; .gitignore-Änderung NIE mitstagen; git add mit expliziten Pfaden)
1 feat(security): skill-integrity … · 2 feat(skills): Provenance … · 3 feat(cli): skill-integrity-CLI … + allowlist · 4 feat(security): startup-guard … · 5 ci: … · 6 refactor(tool-use) · 7 feat(context) · 8 refactor(depp) · 9 feat(storage): mnemosyne … · 10 feat(storage): MemoryProvider · 11 feat(profile) · 12 docs(roadmap)

## Verifikation
- Pro Commit: npx tsc --noEmit && npm test (Coverage 70% beachten, R2: Logik in src/, CLI dünn)
- Real: skills:approve --all → skills:verify (checked:21, exit 0)
- Tamper im SCRATCHPAD (Kopie): Byte in SKILL.md ändern→HASH_MISMATCH exit 1; unbekanntes Dir→NOT_IN_ALLOWLIST; provenance.json löschen→MISSING_PROVENANCE
- Startup: SecurityKernel.startup mit skillIntegrity enabled gegen intakt (ok) vs. manipulierte Kopie (wirft)
- Depp: Snapshot-Äquivalenz Naive vs. alt

## Risiken
R1 keine neuen JS→TS-require-Kanten (Präzedenz-Bruch existiert in core/audit-log.js) · R4 nie homedir/cwd-Live-Daten in Tests/Defaults · R5 Hashes roh ohne EOL-Normalisierung, CI=Referenz · R6 MemoryEntry-Duplikat synchron halten
