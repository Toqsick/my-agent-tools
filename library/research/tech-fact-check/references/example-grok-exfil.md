# Worked example — "Grok 4.5 exfiltrates GitHub repos to xAI"

This is a condensed case study of a Phase-1-to-Phase-5 fact-check
performed 2026-07-13. Kept as a reference for what a complete
verify-a-claim cycle looks like in this skill.

## Phase 1 — Reframe

**Popular framing** (HN headline, 2026-07-12, 486 pts):
> "xAI Grok Build CLI sends your entire codebase and secrets to its
> servers, no opt-out"

**Reframed literal claim** (the actual findable mechanism):
> The xAI Grok Build CLI (a coding tool, not the Grok 4.5 model itself)
> uploads the local working tree as a git bundle via `POST /v1/storage`
> to a Google Cloud Storage bucket named `grok-code-session-traces`,
> regardless of the "Improve the model" toggle. Wire-captured by an
> independent researcher on `grok 0.2.93`, 2026-07-10.

What the popular framing got wrong:
- "Grok 4.5" — actually the CLI `grok 0.2.93`, which uses Grok 4.5 as
  the default model.
- "GitHub repos" — actually the **local clone** on the user's machine.
- "To xAI servers" — actually to a **Google Cloud Storage bucket**
  operated by xAI. Two different cloud providers.

## Phase 2 — Source waterfall

| Tier | Source | What it gave |
|---|---|---|
| Primary | `gist.github.com/cereblab/dc9a40...` (researcher's writeup) | Full mechanism, SHA-256 evidence, repro recipe |
| Primary | `github.com/cereblab/grok-build-exfil-repro` | Reproducible harness (`mitmproxy` + canary repo) |
| Reputable secondary | Korean security blog (`ahastudio/til`) | Independent re-read of the report |
| Community | HN item `?id=48877371` (486 pts, 183 comments) | "Improve the model doesn't help" sanity-check from multiple users |
| Provider artifact | `/v1/settings` capture (2026-07-13) | xAI's server-side response (`trace_upload_enabled: false`) |

## Phase 3 — What counts as evidence

The researcher delivered on all four:
- **Wire-level** — `secrets_responses_body.bin` (raw HTTP body, with
  decryption step), `wire_12gb.log` (mitmproxy output with status codes).
- **Reproduction** — `cereblab/grok-build-exfil-repro` (mitmproxy +
  canary repo, anyone can run).
- **Scope statements** — §7 "What we did NOT prove": training, 3 GB
  direct-PUT capture, exhaustive docs audit, all account tiers.
- **Failure-mode honesty** — retracted an earlier claim about queue-drain
  inferring upload ("we were wrong, the wire capture supersedes that
  inference").

## Phase 4 — Precise restatement (one paragraph)

> xAI's Grok Build CLI (`grok 0.2.93`) routes two parallel HTTP
> streams when running: (a) the model-turn channel `POST cli-chat-proxy
> .grok.com/v1/responses` carrying file contents the agent is reading,
> and (b) a storage channel `POST .../v1/storage` carrying the entire
> working tree, snapshotted as a git bundle and routed to a Google
> Cloud Storage bucket `grok-code-session-traces` (per binary strings
> `xai-data-collector/src/{gcs,storage_client,file_access_tracker,...}.rs`).
> The storage channel operates independent of (a) — an agent given the
> prompt "reply OK, do not read any files" still uploads the whole repo
> (recoverable as `git clone` from `uploaded_repo.bundle`, SHA-256
> `73b9c0af...`). On a 12 GB never-read repo, channel B moved
> ~5.10 GiB / 73 chunks all HTTP 200, while channel A moved 192 KB
> total — a ~27 800× ratio that pins the upload to the codebase, not
> to what was read. The "Improve the model" account toggle does not
> gate this stream — `POST /v1/settings` continued to return
> `trace_upload_enabled: true` after toggle-off.

That paragraph is what an unredacted, unheadlined, mechanism-level
restatement looks like.

## Phase 5 — Verdict + matrix

**Verdict**: Popular headline was substantially correct but misframed.
The mechanism is real and the researcher-bundled evidence is strong;
the victims are local repos (not GitHub-hosted), the agent is Grok
Build (not Grok 4.5 the model), and the destination is GCS (not
generic "xAI servers"). No CVE, no xAI blog post, no security
advisory. xAI flipped `disable_codebase_upload: true` server-side on
2026-07-13 — implicit acknowledgement without statement.

| Sub-claim | Confidence |
|---|---|
| `.env` sent unredacted via `/v1/responses` | High — wire-captured |
| Entire local repo uploaded as git bundle via `/v1/storage` | High — `git clone` recovers never-read file |
| Destination is `gs://grok-code-session-traces` | High — binary strings + captured `metadata.json` |
| Multi-GB uploads return HTTP 200 | High — `wire_12gb.log`, ~5.10 GiB verified |
| "Improve the model" toggle stops the upload | **Refuted** — toggle-off still uploads |
| Repo contents used for model training | Not proven — explicitly out of scope |
| Same behaviour in Grok Web/API | Not tested |
| Same behaviour in `grok 0.2.99` (newer) | Partial — bundle channel off, but new bypass via `git cat-file` in `/v1/responses` |

## Lessons distilled

1. **Tier 0 probe before Tier 1 — but if you have to ask, Firecrawl is
   usually off.** Skip directly to MCP + curl.
2. **The user's question is rarely precise.** "Did X leak Y?" needs a
   reframe into actor + mechanism before the rest of the work makes
   sense.
3. **Server-side flag flips count as acknowledgement.** Even without a
   blog post, the absence of a feature next week is evidence.
4. **"Single researcher claim" is not the same as "unverified."** A
   researcher with wire captures, a repro repo, and an honest §7 is
   publishable evidence. A viral tweet is not.
5. **Don't oversell the conclusion.** Training claim was unverified,
   should stay unverified. Anyone claiming "xAI trains on it" is
   speculating beyond the evidence.
