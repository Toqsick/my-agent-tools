---
name: hermes-maintenance-core
title: "Hermes Maintenance — Core (Reality-Check, Config, SSE)"
description: "Use when doing core Hermes maintenance: reality-check before changes, Tirith verification, config.yaml security defaults, Perplexity-style analysis, SSE pipeline patterns, build documentation standards. NOT for pitfall recovery (use hermes-maintenance-pitfalls)."
category: devops
version: '1.0'
created: '2026-07-23'
author: Yuno (split from hermes-maintenance)
lane: koenigin
agent: universal
trigger_keywords: ['hermes', 'reality-check', 'tirith', 'config', 'security', 'sse', 'pipeline', 'doku']
keywords: ['hermes', 'maintenance', 'config', 'security', 'sse', 'reality-check']
related_skills: ['hermes-maintenance-patterns', 'hermes-maintenance-pitfalls']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from hermes-maintenance 2026-07-23)'

license: MIT
---

# Hermes Maintenance — Core (Reality-Check, Config, SSE)

_Extracted from hermes-maintenance on 2026-07-23._

## 1. Reality-Check BEFORE Making Changes

Wenn der User (oder Perplexity) eine Liste von "Fixes" vorschlägt, IMMER erst prüfen ob sie schon umgesetzt sind — kann Stunden sparen.

- **Pattern:** `grep -E "tirith|allow_private_urls|redact_pii|website_blocklist" ~/.hermes/config.yaml` → wenn schon drin, ist Perplexity-Info veraltet
- **Mnemosyne-Korrektur:** Wenn Mnemosyne-Recall nicht der Realität entspricht → `mnemosyne_invalidate` + `mnemosyne_remember` mit korrigiertem Fakt

## 2. Tirith v0.3.1 — Live-Verify Pattern

Tirith ist das Pre-Exec Security-Guard von Hermes. **NIEMALS nur "ist installiert" checken — IMMER live-testen.**

- Test-Script: `scripts/tirith-live-test.sh`
- **Pitfall:** `tirith scan` ohne input piped hängt — `check` ist der richtige subcommand für inline-commands

## 3. config.yaml Security-Defaults (verified 2026-06-30)

Alle P0-Security-Defaults sind in Hermes V7.3 default-Config aktiv (`tirith_enabled`, `allow_private_urls: false`, `redact_pii/secrets: true`, `website_blocklist` mit 3 cloud-metadata domains).

- **Verifikation:** `grep -E "tirith|allow_private|redact|blocklist" ~/.hermes/config.yaml`
- **Details + Optional-Härtung:** → `references/security-defaults.md`

## 4. Perplexity-style Security Analysis — Reality-Filter

Externe AI-Analysen als **Hypothese** lesen, nicht als Befund. Jeden Punkt real-verifizieren (grep, cat, code-read) bevor entschieden wird welche Lücken echt sind.

- **Was oft FALSCH/VERALTET ist:** "Tirith eingebaut" (check `tirith_enabled`), "SSRF-Schutz vorhanden" (check `allow_private_urls`), "Audit-Log fehlt" (check V7 Hash-Chain)
- **Full workflow:** → `references/perplexity-analysis.md`

## 6. Hermes V7.3 SSE-Pipeline — Production-Grade Pattern

SSE v2 ist die Production-Implementation mit Backpressure-Handling, Idle-Timeout, Max-Clients (100, LRU), Last-Event-ID, Heartbeat (15s).

- **Architecture:** ENV flag (`SSE_VERSION=v2`) statt hardcoded, Runtime-Store mit computed metrics, Mutation API
- **Helmet/CSP/CORS pitfalls:** Helmet-Default `Cross-Origin-Resource-Policy: same-origin` blockt Browser-EventSource. CSP default `script-src 'self'` blockt inline scripts. CORS-Origin-Array setzt keinen Header ohne Origin.
- **SSE-Rate-Limit:** 10/60s default — nervig beim Dev, gut für Production
- **Ring-Buffer Aggregate:** SSE als Single-Source-of-Truth, Polling-Reduce 75%
- **Trust-Proxy:** MUSS gesetzt sein hinter reverse-proxy, sonst teilen alle Clients einen Rate-Limit-Bucket
- **Full details + code:** → `references/sse-pipeline-patterns.md` and `references/sse-pipeline-v2.md`

## 9. Doku-Standard für Builds

Nach jedem nicht-trivialen Build (5+ API-Calls) SOFORT dokumentieren.

- **Format:** `~/docs/system/<topic>-<YYYY-MM-DD>.md` mit: Datum/Kontext, Vorher/Nachher, Architektur-Entscheidungen, Smoke-Tests, Geänderte Dateien, Lessons Learned
- **README.md-Index updaten:** Jeder Build-Report bekommt einen Eintrag im `~/docs/system/README.md`

## 10. Git-Commit-Pattern für Build-Commits

Nach erfolgreichem Build IMMER committen mit `feat:` scope + Aufzählung der Änderungen + Doku/Build-Report-Pfade. **NICHT pushen** ohne explizite User-Freigabe.
