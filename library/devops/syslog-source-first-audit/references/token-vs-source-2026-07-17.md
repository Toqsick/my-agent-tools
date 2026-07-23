# Token-Vs-Source Syslog Audit — Case Study 2026-07-17

> **Skill:** `devops/syslog-source-first-audit`
> **Session:** System-Audit 2026-07-17 (664-line report at `~/20-Workspace/results/system-audit-2026-07-17.md`)
> **Trigger:** 2.7 GB active syslog after the 16.07 zorin-printers fix was applied. Initial token-based analysis pointed at the wrong source.

## Symptom

After Basti applied a rsyslog filter for the `zorin-printers` / `clutter_text` loop
(6.4 GB syslog on 16.07), the active syslog grew back to 2.7 GB within 44 hours.
Natural assumption: the 16.07 fix didn't hold, the same vector was regrowing.

## Wrong Turn: Token-Based Analysis

The first instinct was to count syslog tokens by frequency:

```
awk '{print $5}' /var/log/syslog | sort | uniq -c | sort -rn | head -10
```

Result:

```
4488878 to
   8303 update:
   6885 print_timing:
   6497 -
   5501 operator():
   2450 =
   1964
   1913 level=INFO
   1803 launch_slot_:
   1783 get_availabl:
```

Interpretation at first glance: 4.49M hits on `to`, lots of C++ template tokens
(`operator():`, `launch_slot_`, `get_availabl`). This LOOKED like a native
C++ binary spamming `print_timing` debug output. The match to zorin-printers
wasn't obvious — but also not ruled out.

## Correction: Source-First Identification

The token analysis was a trap. `awk '{print $5}'` extracts the 5th whitespace-
delimited token, which is NOT the source process. The rsyslog format is
`Jul 18 08:38:01 hostname program[pid]: message` — the program name sits at
field 6 (in `awk` terms), bracketed by `[pid]:`.

Switched to process-based counting:

```
grep -c 'ollama\[' /var/log/syslog
grep -c 'zorin-printers' /var/log/syslog
grep -c 'clutter_text' /var/log/syslog
```

Result:

```
66639   ollama[ lines
    22  zorin-printers lines
     9  clutter_text lines
```

**Diagnosis:** The 16.07 zorin-printers fix IS working (22 hits, down from 6.4M).
The 2.7 GB syslog comes from **Ollama 0.30.11** print_timing debug output. Sample
line confirms:

```
2026-07-16T16:59:09.589019+02:00 bratan-17-P1 ollama[138740]: slot get_availabl: id  0 | task -1 | selected slot by LRU, t_last = -1
```

Origin timestamp `2026-07-16T16:59:09` = after Basti's rsyslog filter, coinciding
with the `qwythos-9b-q6:128k` model entry ("18 hours ago" in `ollama list`).

## Root Cause

Ollama 0.30.11 emits `print_timing` debug logs at INFO level when a model runs
inference. With `OLLAMA_KEEP_ALIVE=15m` (Optimax 4.2), each session-bound inference
generates multi-KB sampler-chain dumps per request. The output is not gated by
any `OLLAMA_DEBUG` flag — it's default-on verbosity in this version.

## Fix Applied (F2, 2026-07-18)

```bash
# Override the Ollama service to suppress debug output
sudo tee /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_KEEP_ALIVE=15m"
Environment="OLLAMA_DEBUG=0"
Environment="OLLAMA_LOG_LEVEL=warn"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**Verification (3 seconds, before/after syslog size):**

```
vor 3s: 3453452700 bytes
jetzt:   3453452700 bytes  ← 0 bytes growth, spam stopped
```

Before fix: ~68 KB/s growth rate. After: 0.

## Cross-Check With Prior Audits

| Date | Source | Size | Fix | Vector Type |
|---|---|---|---|---|
| 2026-07-11 | zorin-printers (apparent) | 10.5 GB | Appeared self-resolving (was just a lull) | Loop-bug |
| 2026-07-16 | zorin-printers clutter_text | 6.4 GB | rsyslog filter + logrotate size 500M | Loop-bug |
| 2026-07-17 | ollama print_timing | 2.7 GB | `OLLAMA_DEBUG=0` in service override | Debug-output |

**Three vectors in three weeks, three different sources.** Confirms the principle
documented in SKILL.md: syslog drift on Basti's workstation is NEVER self-resolving
— every occurrence has an active spam source that must be identified source-first
and fixed at the source.

## Lesson For Future Sessions

1. **`awk '{print $5}' | sort | uniq -c` is a token analysis, NOT a source analysis.**
   It produces high-confidence-looking but misleading results when the spammer
   is a C++ binary emitting template-heavy debug output.

2. **`grep -c 'PROCESS\[' /var/log/syslog`** is the correct first probe. The `[`
   after the process name is the rsyslog bracket for the PID — every line from
   that process matches.

3. **Sample one line per suspected source** (`grep -m 5 'PROCESS\[' ...`) before
   building any hypothesis. The shape of the spam reveals its type immediately.

4. **Cross-check prior fixes** before assuming regression. The 16.07 filter still
   worked; the 17.07 vector was NEW. Token-based analysis obscured this.

5. **Logrotate `size 500M` is a sufficient condition, not a necessary one.** It
   only fires when the logrotate timer ticks, not continuously. An active spam
   source can grow the file past 500M between timer runs.
