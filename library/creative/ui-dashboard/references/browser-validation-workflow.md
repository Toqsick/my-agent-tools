# Browser-Validation Workflow for JS-heavy Dashboards

> Session insight from Yuno-Operator Live-Deploy (2026-07-08)

## Problem

Dashboard deploys look perfect in the code review — skeletons render, CSS is balanced, token usage is clean — but in the browser they show **only skeletons** with "connecting…" or "Last Update: connecting…". The JS silently failed.

**Headless Chrome with `--virtual-time-budget` CANNOT validate async JS.** It fires the screenshot BEFORE `setTimeout()` / `fetch()` / `Promise.then()` resolve, even at 30s budget. You see the skeleton and think "it works, just slow" — but the real browser would still be loading minutes later.

## The Fix: Browser-Tool Debugging Pipeline

Don't rely on headless Chrome for JS validation. Use Hermes browser tools:

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  1. Build    │ ──→ │ 2. Start Server  │ ──→ │ 3. browser_     │ ──→ │ 4. browser_  │
│   dashboard  │     │  (background)   │     │    navigate     │     │    console   │
└─────────────┘     └─────────────────┘     └────────┬────────┘     └──────┬───────┘
                                                      │                     │
                                                      │                     ▼
                                                      │              ┌──────────────┐
                                                      │              │ JS Errors?   │
                                                      └──────────────┤              │
                                                                     │ YES → FIX    │
                                                                     │              │
                                                                     │ NO → browser │
                                                                     │     _vision  │
                                                                     └──────┬───────┘
                                                                            │
                                                                            ▼
                                                                     ┌──────────────┐
                                                                     │ 5. Verify    │
                                                                     │    live-data │
                                                                     │    render    │
                                                                     └──────────────┘
```

### Step 1 — Navigate + Snapshot

```python
browser_navigate(url="http://127.0.0.1:8767/index.html?bust=1")
```

The snapshot shows elements (skeleton cards, "connecting…" text). If the JS worked, you'd see actual data values. **If the page shows "connecting…" after navigation, the JS has an error.**

### Step 2 — Check Console Errors

```python
browser_console()
```

Returns `js_errors` array. This is the **smoking gun**. If empty-string errors appear (`{"message": "", "source": "exception"}`), they're uncaught JS exceptions swallowed by async context.

### Step 3 — See the Visual State

```python
browser_vision(question="Live-Daten sichtbar? Nur skeleton?")
```

See exactly what a real user sees.

### Step 4 — Fix + Refresh Cycle

1. Patch the JS file
2. `browser_navigate(url="http://127.0.0.1:8767/index.html?bust=2")` (increment bust parameter to skip cache)
3. Repeat from Step 2 until console errors = 0 AND snapshot shows data values

## Common JS Failures in Dashboard Deploys

### Failure 1 — `String(s)` throws on null/undefined

**Symptom:** Template literal `${data.system.memory.used_gb}` works until a value is 0 or null.

**Fix:**
```javascript
function escapeHtml(s) {
  return String(s == null ? '' : s)     // ← null guard
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')...;
}
```

Add null-guard to EVERY function that calls `String()` or accesses nested properties.

### Failure 2 — `document.getElementById()` before element exists

**Symptom:** Script runs in `<head>` where elements don't exist yet. Or badge-count elements are conditionally rendered.

**Fix — Defer or guard:**
```javascript
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('my-element');
  if (!el) return;  // ← guard
  el.textContent = 'value';
});
```

### Failure 3 — `fetch()` error silently swallowed

**Symptom:** Skeleton never resolves because fetch failed but catch block is missing.

**Fix — Always add catch:**
```javascript
async function fetchData() {
  try {
    const res = await fetch(DATA_URL, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);  // ← non-200 is NOT success
    const data = await res.json();
    render(data);
  } catch (err) {  // ← ALWAYS have catch
    console.error('fetchData failed:', err);
    showErrorBanner();
  }
}
```

### Failure 4 — Unicode chars in JS object keys

**Symptom:** Object literal like `{ ✓: true }` causes parse error in strict contexts.

**Fix:** Quote all non-ASCII keys:
```javascript
const iconMap = { '✓': '✓', '✦': '✦', '◆': '◆' };  // ← quoted
```

### Failure 5 — Hoisting ordering (function defined after use)

**Symptom:** `function declarations` ARE hoisted in JS, but `const fn = () => {}` is NOT. If `runMemorySearch()` calls `escapeHtml()` which is defined 30 lines below as a function declaration — that's fine. If defined as `const escapeHtml = () => {}` that's a `ReferenceError`.

**Fix:** Keep `function escapeHtml() {}` (declaration syntax, hoisted) until proven otherwise.

## `?theme=` URL-Override Pattern for Deterministic Screenshots

When you need headless screenshots of every theme variant, **do NOT use localStorage-wrapper** (a helper HTML that sets localStorage then meta-refreshes). That pattern fails because headless Chrome does NOT persist localStorage between file:// page loads.

### The Fix: URL-Override in initTheme

Add a URL-query-parameter override in your theme-initialisation function:

```javascript
(function initTheme() {
  let theme = 'cozy';
  try {
    const qs = new URLSearchParams(location.search).get('theme');
    const allowed = ['cozy', 'dark', 'cyberpunk', 'hc'];
    if (qs && allowed.includes(qs)) {            // URL-param wins
      theme = qs;
      localStorage.setItem('yuno-theme', qs);
    } else {
      const saved = localStorage.getItem('yuno-theme');
      if (saved && allowed.includes(saved)) theme = saved;
    }
  } catch (e) {}
  setTheme(theme);
})();
```

### Screenshot Loop (reliable, deterministic)

```bash
for theme in cozy dark cyberpunk hc; do
  google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size=1600,1500 --virtual-time-budget=10000 \
    --screenshot="gallery/v3-$theme.png" \
    "http://127.0.0.1:8767/index.html?theme=$theme&v=$(date +%s)"
done
```

The `&v=$(date +%s)` cache-bust ensures each call gets a fresh page load with the correct theme.

### When to Use This vs browser_vision

| Method | Use When | Caveat |
|--------|----------|--------|
| `browser_vision()` inside a live session | One-off visual check during dev | Only captures current state |
| `?theme=` + headless Chrome | All 4 themes, automated gallery | async JS may not resolve — first verify with browser tools |
| `browser_vision()` on each theme click | Manual per-theme inspection | Slow for 4+ themes |
| `?theme=` + `--virtual-time-budget` | CI/automation for reproducible screenshots | Budget must be long enough for fetch() to resolve |

## Headless Chrome Screenshot: When It Lies

```bash
# This DOES NOT capture async JS state
google-chrome --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=30000 \
  --screenshot=/tmp/dashboard.png \
  "http://127.0.0.1:8767/index.html"
```

**Why it fails:** `--virtual-time-budget` counts wall-clock time, not JS event-loop cycles. If `fetch()` is still waiting for the response when the budget expires, Chrome captures whatever is on screen — the skeleton.

**The real fix for screenshot validation:**

1. First verify the page works with browser_tools (see pipeline above)
2. THEN use headless Chrome with `--virtual-time-budget=5000+` only for visual comparison, knowing the data is real
3. Alternative: use `browser_vision()` for the real screenshot

## Validation Checklist Additions

Before declaring a dashboard deploy "done", add these checks to the main checklist:

- [ ] `browser_navigate` → snapshot shows real data values (not skeleton/"connecting…")
- [ ] `browser_console` → `js_errors` array is empty (0 errors)
- [ ] `browser_console` → `console_messages` has no `fetch` errors or `404` warnings
- [ ] Refresh (click Refresh button or re-navigate) → data updates with new timestamp
- [ ] All 4 themes render without console errors
- [ ] Network tab check: `/api/data` returns 200 with valid JSON (via `browser_console(expression='fetch("/api/data").then(r=>r.ok)')`)
