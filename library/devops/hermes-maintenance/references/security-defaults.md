# config.yaml Security-Defaults (verified 2026-06-30)

> Extracted from hermes-maintenance SKILL.md Section 3. Hermes V7.3 security configuration defaults and verification.

Diese sind ALLE in der aktuellen Hermes V7.3 default-Config aktiv:
- `security.tirith_enabled: true`
- `security.allow_private_urls: false` (SSRF-Schutz)
- `security.redact_pii: true`
- `security.redact_secrets: true`
- `security.website_blocklist.enabled: true` mit 3 cloud-metadata domains:
  - `169.254.169.254`
  - `metadata.google.internal`
  - `metadata.goog`

**Verifikation:** `grep -E "tirith|allow_private|redact|blocklist" ~/.hermes/config.yaml`

**Optional-Härtung (für Produktion):**
- `tirith_fail_open: false` setzen wenn Tirith-LTS läuft (blockt Commands bei Tirith-Crash statt silent-fallback)
- Log-Routing von stderr → journald/syslog für Alerting
