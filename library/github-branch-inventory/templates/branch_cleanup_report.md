# 🧹 Branch-Cleanup-Scan — {REPO_OWNER}/{REPO_OR_ORGS}

**Stichtag:** {REFERENCE_DATE}
**Repos gescannt:** {REPO_LIST}
**Threshold STALE:** >{THRESHOLD_DAYS} Tage ohne Commit auf Branch-Spitze (committer.date)
**Modus:** Read-only via `{gh|curl}`{MCP_FALLBACK_NOTE}

---

## 📊 Zusammenfassung

| Kennzahl | Wert |
|---|---|
| **Repos gescannt** | {N} |
| **Branches gesamt** | {N} |
| **🔴 STALE (>{THRESHOLD_DAYS} Tage)** | **{N}** |
| **🟡 WARN ({WARN_LO}-{THRESHOLD_DAYS} Tage)** | **{N}** |
| **🟢 ACTIVE (≤{WARN_LO} Tage)** | **{N}** |
| **Sicher löschbar** | **{N}** |
| **Kandidaten für Aufräumen** | {N} |

{ONE_LINE_VERDICT}

---

## 🟢 Branch-Tabelle (alle {N} Branches, sortiert nach Alter absteigend)

> Spalten: **Repo | Branch | Letzter Commit | Alter (Tage) | Status | Empfehlung**

### {REPO_NAME} ({N} Branches)

| Repo | Branch | Letztes Commit | Alter | Status | Empfehlung |
|---|---|---|---|---|---|
| {repo} | `{branch}` | {date} | {n}d | {🟢/🟡/🔴} | **{RECOMMENDATION}** |

---

## 🎯 Heuristiken für Auto-Delete-Empfehlung

Folgende Branch-Pattern als automatisch **DELETE-empfohlen** markieren, sobald sie >{THRESHOLD_DAYS} Tage alt sind:

1. **`backup/*`** — Einmal-Snapshots, niemals langlebig.
2. **`copilot/task-<id>-<uuid>-*`** — auto-generierte Copilot-Coding-Agent-Branches.
3. **`copilot/<sha>`** — Branch-Name IS commit hash; ephemeral.
4. **`copilot/actions-run-<id>`** — Run-Snapshot-Branches.
5. **`master` neben `main`** — Default-Branch-Konflikt.
6. **`translation/<lang>-N`** bei N ≥ 2 — gestaffelte Snapshots.
7. **`import/*`** mit nur 1-2 Commits.
8. **`ci/*` & `docs/*` Branches** älter als {THRESHOLD_DAYS} Tage.

---

## ⚠️ Issues Encountered

{ISSUES_LIST}

---

## 🧾 Reproducibility

```bash
# Re-run des Scans in 7 Tagen:
{REPRO_COMMAND}
```

Nächster Sweep in 7 Tagen zeigt den Drift — {NEXT_SWEEP_HINT}.
