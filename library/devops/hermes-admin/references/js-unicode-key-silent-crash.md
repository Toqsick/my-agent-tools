# Silent V8 Crash: Unicode Object Keys in JavaScript

Discovered 2026-07-08 while debugging a live Hermes dashboard frontend that showed "connecting…" forever with zero console errors.

## The Bug

An unused object literal with Unicode-char keys caused V8 to silently skip the entire `<script>` block — no `SyntaxError`, no `ReferenceError`, no console output, just a dead script.

```javascript
// THIS CRASHES V8 SILENTLY:
const iconMap = {
  ok: '✓',
  '◆': '◆',
  '✦': '✦',
  '⏰': '⏰',
  '◇': '◇',    // ← This line
  '⚙': '⚙'
};
```

The `iconMap` variable was **never used** — the script continued normally with other working code after this line. Yet V8 refused to execute **any** of the script (not even code before this line), with only a bare `"exception"` in the console (no message text).

## Why It Happens

- V8's parser handles Unicode object keys differently than standard ASCII keys
- Certain Unicode code points in object literal keys trigger an early syntax validation that can fail silently in non-strict mode
- The error propagates as a generic `"exception"` with no message — Chrome DevTools shows just `undefined` as the error value
- Node.js with `--check` (syntax validation) does NOT catch this — it passes clean

## How to Detect

1. **Browser console shows `"exception"` entries with empty message** — distinct from normal `SyntaxError`/`TypeError` which always have a message string
2. **`document.title` stays at its initial value** — if your script changes `document.title` on load and it doesn't change, the script never ran
3. **Isolate via bisection**: comment out half the script, check if title changes → narrow to the offending line
4. **`new Function(script)` in Node.js** will NOT reproduce it — only actual V8 parsing in a browser context triggers it

## How to Fix

- **Replace Unicode object keys with lookups:** `const iconMap = {}; iconMap['✓'] = '✓';` works fine
- Or simply **remove unused variables** with Unicode keys
- Or convert to `Map`: `const iconMap = new Map([['✓', '✓']]);`

## Prevention

- Avoid Unicode characters as object literal keys — even quoted (`'✓': '✓'`) doesn't always help
- Prefer `Map` over object literals when keys are non-ASCII
- Add a `document.title = 'Script Ran';` at the top of your script as a canary — if title doesn't change, the script didn't execute
- Run a quick test in headless Chrome with `--dump-dom` and grep for the canary string
