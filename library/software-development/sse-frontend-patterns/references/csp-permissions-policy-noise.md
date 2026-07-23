# Browser-Extension Console Noise — ID Guide

When you open DevTools on a dashboard that connects to `localhost` and the console is full of scary-looking errors, **check if they're from your code or from a browser extension's content script before chasing them.**

## How to tell

Open DevTools → Sources tab → look for `chrome-extension://` or `moz-extension://` URLs in the stack frames. If the source file is `contentscript.js` (or has a webpack hash like `contentscript.js:14083`), it's not your code. It's a content script injected by a browser extension (MetaMask, Phantom, Brave Wallet, etc.).

## Common offenders and their signatures

### Permissions-Policy header warnings

```
Error with Permissions-Policy header: Unrecognized feature: 'private-state-token-redemption'.
Error with Permissions-Policy header: Unrecognized feature: 'private-state-token-issuance'.
Error with Permissions-Policy header: Unrecognized feature: 'browsing-topics'.
Error with Permissions-Policy header: Unrecognized feature: 'run-ad-auction'.
Error with Permissions-Policy header: Origin trial controlled feature not enabled: 'join-ad-interest-group'.
```

**Source:** MetaMask / Phantom / Brave Wallet injecting `Permissions-Policy` and `Interest-Cohort` headers they expect to be silently accepted. Modern browsers reject them as unknown.

**Fix:** None needed in your code. They appear in EVERY page with these extensions. To confirm: open in `Ctrl+Shift+N` (incognito) with extensions disabled.

### MaxListenersExceededWarning

```
contentscript.js:14083 MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 close listeners added.
```

**Source:** MetaMask's internal `ObjectMultiplex` and similar add/remove listeners aggressively. The Node.js EventEmitter (which they polyfill in the browser) warns at 10 listeners.

**Fix:** Not your code, not your problem. It's their internal architecture.

### ObjectMultiplex orphaned data / malformed chunk

```
contentscript.js:14083 ObjectMultiplex - orphaned data for stream "app-init-liveness"
contentscript.js:14083 ObjectMultiplex - malformed chunk without name "[object Object]"
```

**Source:** Same — MetaMask's `ObjectMultiplex` transport. Orphaned data is normal during a wallet-lock/wake event. Not actionable.

### Content Security Policy "eval" warning

```
The Content Security Policy (CSP) prevents the evaluation of arbitrary strings as JavaScript...
1 directive
Source location Directive Status
script-src blocked
```

**Source:** Helmet's default CSP. When the dashboard sets `'unsafe-inline'` for `script-src` (necessary for inline scripts in a single HTML file) but not `'unsafe-eval'`, some extension content scripts that use `new Function()` get blocked. You see this in your dashboard's console when an extension tries to inject a script.

**Fix:** If you don't use `eval`/`new Function` in your own code, you can safely add `'unsafe-eval'` to `script-src` for the price of a more permissive CSP. For Localdev dashboards this is fine. For production, consider splitting inline scripts to external `.js` files so you can drop `unsafe-inline` too.

## The test

```bash
# Chrome
Ctrl+Shift+N  # new incognito window — extensions off by default
# Then navigate to the dashboard. Clean console.
```

If the warnings disappear in incognito, they're from extensions. If they persist, they're from your code.

## Mental model

**Treat console output as "noise + signal" where the ratio is heavily skewed toward noise** when you have any non-trivial browser extensions installed. The 1% that IS your code can be found by:
1. Stack-trace-grep for your own file names
2. Network tab filter (HTTP status + URL are unambiguous)
3. `console.log` your own breadcrumbs with a unique prefix like `[SSE]`, `[apiFetch]`, `[auth]`
