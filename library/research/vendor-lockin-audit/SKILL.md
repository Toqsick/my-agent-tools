---



name: vendor-lockin-audit
description: 'Use when user asks whether a hardware device works without its manufacturer ecosystem, SaaS, or companion app, or wants a feature-by-feature lock-in and exit audit. NOT for generic product recommendations or software-vendor procurement. Maps sensors, OS barriers, bootloader or Knox limits, open alternatives, exports, and confidence-ranked sources.'
version: 1.0.0
author: Yuno (Basti's Hermes Agent)
tags:
- research
- hardware
- ecosystem
- vendor-lockin
- compatibility
license: MIT
trigger_keywords: ['and', 'vendor-lockin-audit', 'whether', 'hardware', 'device']
keywords: ['feature', 'user', 'asks', 'whether', 'hardware']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---




# Vendor Lock-In Audit

A systematic research methodology for answering: **"What features of device X work without the manufacturer's ecosystem?"**

Applies to: smartwatches (Galaxy Watch, Fitbit, Garmin, Pixel Watch), smart home (IoT hubs, sensors), automotive (telematics, companion apps), drones, headphones, and any device with proprietary app requirements.

## When to load

- User asks: "Can I use device X without app Y / service Z?"
- User asks: "How locked-in am I to brand X?"
- User asks about buying a device but doesn't want to be dependent on the manufacturer's app.
- Any question about a specific sensor/feature on a vendor-locked device.

## Before starting

1. Identify the **exact model** (Wi-Fi vs. LTE matters for bootloader/Knox).
2. Identify the **exact OS version** on the device — workarounds break on specific firmware updates. A version number is NOT optional.
3. Is the question about a **single feature** ("Can I use ECG without Samsung Health?") or **full independence** ("Can I wipe Samsung Health and still use the watch?")? Scope it early.

## Workflow

### Phase 1 — Discovery (parallel source gathering)

Run 6–8 parallel queries covering:

| # | Angle | Example query |
|---|-------|---------------|
| 1 | Primary community workaround | `"SHM Mod" Galaxy Watch ECG BP non-Samsung` |
| 2 | Workaround lifecycle status | `"EOL" "end of life" "RIP" "SHM MOD" Patreon` |
| 3 | Official developer SDK | `site:developer.samsung.com health sensor SDK restrictions` |
| 4 | Open-source replacement viability | `Gadgetbridge Samsung Galaxy Watch support issue` |
| 5 | Bootloader/unlock/rollback status | `Galaxy Watch bootloader unlock Knox trip hard brick` |
| 6 | Per-feature lock-in (targeted) | `Galaxy Watch skin temperature third party app continuous` |
| 7 | Accuracy/reliability caveats | `Galaxy Watch SpO2 BIA accuracy vs medical` |
| 8 | OS-level lockout (latest update) | `"One UI 8 Watch" "system only" ECG BP` |

**Search priority:** community sources (Reddit, XDA) > official docs (developer portals) > open-source issues (Codeberg, GitHub) > long-term reviews (tech press).

### Phase 2 — Source verification

For each promising source, extract with `web_extract` or raw `curl`. Tag each:

- `[VERIFIED]` — page loaded, content confirmed
- `[UNVERIFIED]` — search snippet informative but page didn't load
- `[UNREACHABLE]` — 404 / Cloudflare / timeout

**Critical: always check Patreon** for primary dev EOL announcements. Developers announce project death there before GitHub READMEs reflect it.

### Phase 3 — Primary maintainer status check

For community mods, check all four:

1. **GitHub README** — banner warnings, `RIP` statements
2. **Patreon / donation page** — most recent post for maintenance status
3. **XDA thread** — first post changelog + last update date
4. **Successor project** — same dev, different app? What features does it support?

### Phase 4 — Per-feature lock-in mapping

Create a table with one row per feature/sensor. Do NOT give an all-or-nothing answer.

Columns: Feature | Samsung-free? | How | Confidence

For each feature, classify:
- **Locked** — no known path without manufacturer app
- **Third-party path exists** — specific app/workaround needed
- **Mod unlockable** — works via community mod with OS version caveat
- **Raw accessible** — sensor SDK gives raw data but processed output is locked
- **Trend-only** — manufacturer app shows trends; raw spot values not exposed

### Phase 5 — OS-level barrier assessment

Check systematically:
1. **Bootloader unlock** — available? Wi-Fi vs. LTE differences? Hard-brick risk?
2. **Anti-rollback / RPM** — was a rollback-prevention update shipped? When?
3. **Knox / attestation trip** — permanent? What features die? (Pay, Pass, Health, Secure Folder, etc.)
4. **System-component lockout** — latest OS version that breaks workarounds? What changed?

Source: `github.com/zenfyrdev/bootloader-unlock-wall-of-shame` for unreleased/missing bootloader unlock models.

### Phase 6 — Open-source alternative assessment

1. Does Gadgetbridge (or equivalent) support it? Pull the exact device list from `gadgetbridge.org/gadgets/` or Codeberg issue tracker.
2. If unsupported: is the blocker a priority gap or a protocol/hardware barrier? (System-only BLE GATT, vendor-encrypted HID, etc.)
3. What does the community use instead? (Sleep as Android + sideloaded companion, Home Assistant + custom bridge, etc.)

### Phase 7 — Data export assessment

When the user wants to keep manufacturer app but export data elsewhere:
1. Does Health Connect (or equivalent) exist?
2. Is it one-way or two-way?
3. Are there sync timing caveats? (Samsung dev blog: continuous HR NOT synced immediately.)
4. Can export apps read in background or only foreground?

### Phase 8 — Confidence & output delivery

#### Confidence levels

| Level | Definition | Examples |
|-------|-----------|----------|
| HIGH | Primary dev statement, official SDK docs, GitHub primary repo, engineering changelog | Mod author saying "EOL", Samsung dev blog, broken commit diff |
| MEDIUM | XDA thread, reputable press (Android Authority, Ars), bootloader docs, Patreon | Hands-on article, cross-referenced community report |
| LOW | Single Reddit/forum anecdote, YouTube comment | One user's unsupported claim |

#### Output structure

```
## 1. Headline Finding (confidence tag)

## 2. Sensor-by-Sensor Lock-In Table

## 3. What Official Docs Understate (3-5 tagged bullets)

## 4. OS-Level Barriers (per-model: bootloader, Knox, rollback)

## 5. Open-Source / Alternative Status

## 6. Data Export Assessment (if applicable)

## 7. Confidence & Source Hierarchy

## 8. Practical Guidance (actionable 1-paragraph summary)
```

## Pitfalls

- **Do NOT cite official compatibility lists as complete.** The manufacturer's published feature set (e.g. Sleep Apnea countries) is often smaller than mods unlock.
- **Do NOT claim a sensor is "unusable" without checking the sensor SDK.** Raw data may be exposed even if the processed output is locked (e.g. Samsung Sensor SDK lets third-party apps read raw ECG/PPG).
- **Do NOT ignore Patreon as a primary source.** Devs announce EOL there before GitHub by weeks or months.
- **Do NOT conflate "Gadgetbridge does not support it" with "cannot support it."** One is a priority/issue gap; the other is a protocol-hardware barrier.
- **Do NOT give an all-or-nothing answer.** The correct answer is almost always: "ECG/BP: locked; HR/steps: open; sleep: partially; rest: scattered."
- **Do NOT ignore LTE vs. Wi-Fi model differences.** Bootloader unlock often differs; LTE models can hard-brick where Wi-Fi models can't.
- **Do NOT rely on one source type.** Forums catch real-world usage, dev docs catch API realities, and tech press catch the summary. Combine all three.

## Related skills

- `research-tools` — general research; its "Comparative Decision Research" section is a parent workflow that this skill extends.
- `tech-fact-check` — for verifying specific tech claims found during research.

## Reference files

- `references/galaxy-watch-ecosystem-lockin-2026-07.md` — Full worked example: Galaxy Watch 6 Classic vs. Samsung Health ecosystem. 25+ sources, sensor-by-sensor table, One UI 8 analysis, SHM Mod EOL evidence.
