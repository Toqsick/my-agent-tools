# Anti-AI Tells in Daily Notes

> Validated 2026-07-13 via Humanizer self-audit (wave 2). Apply EVERY time you write, rewrite, or verify a Daily Note. Do NOT skip — the self-audit has caught real issues in every pass so far.

## Why This Matters

Daily Notes are the most-read vault files. AI tells damage their credibility — a note that *looks* algorithm-generated undermines the whole "real logbook" design. The `humanizer` skill (29 patterns) covers general writing; this reference covers the patterns **most common in Yuno's Daily Note output**.

## Verify Before Self-Report

**Workflow rule:** When finishing a Daily Note, the order is:
1. Run ALL self-audit checks (see below)
2. **Report** the raw results — don't filter, don't pre-fix
3. Fix any issues found
4. Re-run checks to confirm they're clean
5. Then deliver the final report

Do NOT run the checks, see they're clean, and just say "done". The verification *is* the proof. If you found issues, document what you fixed and why.

## The 5 Patterns to Watch

### 1. Inline-Header Bullet Lists (Humanizer Pattern 16)

**AI tell:**
```
- **Diagnose:** PYTHONPATH auf Hermes-Venv gesetzt
- **Fix:** Wrapper mit env -i
- **Verifiziert:** GPT-2 Test OK
```

**Human version:**
```
Diagnose war simpel: Hermes setzt PYTHONPATH auf die 3.11-Venv, lm-eval braucht
3.12. Lösung: ein Wrapper-Script das lm-eval in sauberer Umgebung startet.
Quick-Test hat gezeigt: GPT-2 auf gsm8k, null Treffer (erwartet).
```

**Rule:** Never use `**Header:** text` as a bullet structure. Write proper sentences. `**Wichtig:**` in a standalone line (not a bullet) is okay for emphasis — but only once per section max.

### 2. Boldface Overuse (Humanizer Pattern 15)

**AI tell:**
```
**Root Cause:** `httpx.ConnectError: Temporary failure in name resolution` → `api.minimax.io` war kurz nicht erreichbar
**Bewertung:** Transienter DNS/Provider-Outage, KEIN Drift-Problem (alle Jobs gepinnt)
**Verifiziert:** Provider jetzt erreichbar
```

**Human version:**
```
Vier Crons sind alle am gleichen Fehler gestorben: `api.minimax.io` war kurz
nicht erreichbar. Jetzt geht's wieder (PING funktioniert, 101ms).
War ein normaler Provider-Ausfall, kein Drift.
```

**Rule:** Bold is for **headings**, **one or two critical keywords** per note, and **checkbox priority markers** (as prescribed in the template). It is NOT for every technical term. Before bolding something, ask: "Would a human writing in a notebook bold this?"

**Known exception:** The template prescribes `**Wichtigstes**` in checkboxes — that's by-design and okay. But don't extend bold to every noun.

**Additional check: mid-sentence boldface.** AI-generated text often uses **one or two bolded words** in the middle of a sentence for emphasis, like "this is **critical** because the system **will** crash". Humans don't write this way. A grep for `[a-zA-Z0-9]**` catches this pattern (boldface immediately preceded by a word character = mid-sentence use). Check this separately from total boldface count.

### 3. Em-Dash Overuse (Humanizer Pattern 14)

**AI tell:**
```
lieber kurze echte Daily als perfekte leere — Wichtig: bevor man cronjob feuert — erst prüfen ob's Drift ist oder Transient — Lesson: bei Scripts die exit 0 liefern — muss man Logs lesen
```

**Human version:**
```
Lieber eine kurze echte Daily als eine perfekte leere. Wichtig: bevor man
cronjob feuert, erst prüfen ob's Drift oder Transient ist. Bei Scripts die
immer exit 0 liefern, muss man die Logs lesen.
```

**Rule:** **Zero em-dashes.** The AI's natural rhythm is em-dash-heavy. Every em-dash should be a period, comma, or new sentence. If you reach for an em-dash, it's a sign to rethink the sentence structure.

**Exception for titles:** `# 2026-07-13 — Vault-Hygiene…` is a case where a colon (`:`) or en-dash (`–`) works better and avoids the em-dash entirely. Titles are not exempt from the zero rule.

### 4. Negative Parallelism / Tailing Negations (Humanizer Pattern 9)

**Primary pattern — "kein X nötig":**
```
kein manueller Fix nötig
kein Action nötig wenn ja
```

**Secondary pattern — "nicht X, sondern Y":**
```
kein Drift, sondern ein normaler Provider-Ausfall
```

**Human version:**
```
Beim nächsten Tick laufen die Crons automatisch wieder grün.
War ein normaler Provider-Ausfall, kein Drift.
```

**Rule:** "kein X nötig" and "nicht X, sondern Y" are both dead giveaways. Just say what happened instead. "Crons laufen wieder grün" beats "kein manueller Fix nötig". "War ein normaler Provider-Ausfall, kein Drift" beats "also kein Drift, sondern ein normaler Provider-Ausfall".

The secondary pattern is subtle — it looks like normal writing but the "nicht X, sondern Y" rhetorical structure is a hallmark of AI textual reasoning. The fix is usually to split it into two short sentences or drop the "sondern" entirely.

### 5. AI Vocabulary (Humanizer Pattern 7+)

**Dead giveaways in German:**

| AI tell | Replace with |
|---|---|
| `crucial` / `critical` | `wichtig` / `entscheidend` (use sparingly) |
| `pivotal` | drop entirely |
| `robust` | `zuverlässig` or describe what it handles |
| `leverage` / `nutzen` | `verwenden` / `einsetzen` |
| `seamless` | `nahtlos` (only when literally true) |
| `holistic` | drop entirely |
| `comprehensive` | `umfassend` (only when verified) |
| `delve into` / `eintauchen` | drop entirely |
| `tapestry` | drop entirely |
| `paramount` | drop entirely |

**Rule:** If an English AI-hallmark word appears in a German text, it's a transplant. The English terms above are the most common in Yuno's output. Check for them in both English and translated German forms.

## Self-Audit Quick Check (Verified Commands)

Run ALL checks BEFORE reporting to the user. The targets are strict — do not relax them.

```bash
F="/home/bratan/Dokumente/Obsidian Vault/06 Daily Notes/2026-07-XX.md"

echo "=== Em-Dashes (ziel: 0) ==="
grep -c "—" "$F" || echo "0"

echo "=== Mid-sentence Boldface (ziel: 0) ==="
grep -cE "[a-zA-Z0-9]\*\*" "$F" || echo "0"

echo "=== Inline-Header (ziel: 0) ==="
grep -cE "^[[:space:]]*[-*][[:space:]]*#" "$F" || echo "0"

echo "=== Negative Parallelism (ziel: 0) ==="
grep -cEi "nicht nur|sondern|kein.*, sondern" "$F" || echo "0"

echo "=== AI-Vokabeln (ziel: 0) ==="
grep -ciE "crucial|pivotal|robust|leverage|seamless|holistic|comprehensive|delve|tapestry|paramount" "$F" || echo "0"

echo "=== kein X nötig (ziel: 0) ==="
grep -ciE "kein.*nötig|keine.*nötig" "$F" || echo "0"
```

If any count is > 0: fix it, then re-run the full check. Do NOT deliver a report that says "mostly clean" or "only one issue". Fix the issue first.

## Relation to Humanizer Skill

The full `humanizer` skill covers 29 patterns. This reference covers the 5 that most affect Daily Notes. When writing other vault documents (resources, MOCs, permanent notes), load the humanizer skill directly and apply all 29.