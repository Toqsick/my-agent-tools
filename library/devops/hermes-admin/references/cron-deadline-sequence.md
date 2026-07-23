# Deadline Reminder Sequence — Worked Example

**Source session:** 2026-07-19 — Kimi Token Cup (WM 2026 Tippspiel)
**Pattern:** 4 escalating one-shot cron jobs for token expiry deadline

---

## The Scenario

Basti won promotional tokens at Kimi's Token Cup WM-Tippspiel (Spain pick).
Hard deadline: 31.07.2026 23:59 Beijing Time (= 17:59 MESZ).
Value at stake: ~309M–684M tokens depending on Spain's final result.

## The 4 Cron Jobs

| Job-ID | Schedule (MESZ) | Tone | Message focus |
|--------|-----------------|------|---------------|
| `64a80e7fedad` | 26.07. 18:00 (T-5d) | Informational | "5 days left, starting to plan?" |
| `8c12538d7c60` | 29.07. 18:00 (T-2d) | Urgent | "2 days, now is the time to spend!" |
| `619021261f8a` | 31.07. 12:00 (T-12h) | Critical | "12 hours until total expiry!" |
| `822287c0a30e` | 31.07. 13:59 (T-4h) | Last chance | "4 hours left, stop reading act NOW" |

## What Each Job Carried (Context Self-Containment)

Every cron job's prompt contained:

1. **The deadline** in multiple timezones (Beijing + MESZ)
2. **The value at stake** (token-range from two scenarios)
3. **Where to spend** (Kimi App, Web, Kimi Code CLI, Kimi Work Desktop)
4. **Where NOT to spend** (OpenRouter API — separate billing)
5. **Concrete action steps** (open kimi.com, start K3 chat, run Kimi Code CLI)
6. **Delivery target** (`telegram:7222661188` — Basti's DM)
7. **Creator identity** (Yuno, with Basti's preferred style: German, urgent but helpful)

No agent needs prior session context — everything to compose the message is in the prompt.

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Interval spacing** | T-5d → T-2d → T-12h → T-4h | Last interval is shortest — the closer the deadline, the more likely the user procrastinates |
| **Model** | MiniMax-M3 (cost-effective) | Each cron run is an independent Telegram send — zero reasoning required |
| **Provider** | minimax | Pinned explicitly to avoid provider-drift (#44585) |
| **Delivery** | `deliver=telegram:7222661188` | Direct DM, not inline — no gateway dependency for the send |
| **Last job buffer** | 4h before deadline | User still has time to act on the message |
| **Removal on early action** | Not implemented for this case | No explicit "I'm done" signal expected; if the user acted earlier, cancellation is manual |

## What to Tweak per Use Case

- **Larger value** (e.g. $500+): Add T-1h or partner-level escalation
- **Smaller value** (e.g. free trial days): 2 jobs suffice (T-3d + T-12h)
- **Non-Telegram channel**: `deliver=discord:#channel` or `deliver=local` (to Hermes desktop)
- **Bi-directional cancel**: If the user can say "done", add a one-shot cancel cron at job creation time
