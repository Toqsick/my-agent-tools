# Multi-Agent Scout Pattern — Lessons Learned

> Extracted from hermes-maintenance SKILL.md Section 5.

Beim Parallelisieren von 3+ Subagenten für Research:

**Format-Drift:** Scouts liefern leicht unterschiedliche Markdown-Strukturen. **Lösung:** Format-Vorgabe ins Goal schreiben ("H1/H2/H3, identische Sektion-Struktur wie Scout 1").

**Code-Skizzen-Scope-Creep:** Scouts schreiben manchmal 500-Zeilen-PoCs in Research-Docs. **Lösung:** Cap auf 200 Zeilen für Research-Doc, vollständiger Code in separates PoC-Repo.

**Konvergenz-Quote tracken:** Wie viele Scouts landen bei gleicher Empfehlung? >2/3 Konvergenz = hohes Vertrauen. 1/3 = mehr Research nötig.

**Synthese-Anker:** Jeder Scout-Output soll am Ende einen "Empfehlungs-Block" mit Bewertung + Aufwandschätzung haben.

**Parent-Direct-Vorab:** Parallel zu Scouts kannst du schon mal Parent-Synthese-Skizze schreiben. Spart Zeit, Scouts-Ergebnisse mergen sich leichter in vorhandenes Skelett.

**Concrete Scout-Scoping für Hermes-V7-SSE Meta-Evaluation (Session 2026-06-30):**
- Scout-A: Frontend/UX — Liest `dashboard/hermes-sse-dashboard.html`, meldet KPI-Slots, Mobile-Bugs, A11y-Gaps, EventLog-Visualisierung, Theme-Persist. Output: `~/docs/system/dashboard-ux-eval-2026-06-30.md`
- Scout-B: Backend/API — Auditiert alle 8 Routes auf Validation-Lücken, Cache-TTL-Konsistenz, Error-Format, Auth-Coverage, SSE-v2-Usage, Test-Sweet-Spot. Output: `~/docs/system/dashboard-backend-eval-2026-06-30.md`
- Scout-C: Integrations/Polish — Empfiehlt SSE-Single-Source-of-Truth, Audit-Replay-Range, Canary-Stats, Cron-Output-Links, Webhooks. Output: `~/docs/system/dashboard-polish-recs-2026-06-30.md`

**Toolset-Zuweisung:** Scout-A+C brauchen `web` (für Design-Recherche), Scout-B nicht. ALLE brauchen `terminal`+`file` (sonst nur Schätzungen statt Messungen).
