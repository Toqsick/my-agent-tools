# Reference — URL Source Triage Worked Example

Captured from the Phase 1 reconnaissance for a Brave-vs-Perplexity comparison project on Linux Flatpak (research date 2026-07-23). Holds concrete URL taxonomy in action + the long-tail items that should not pollute the SKILL.md body.

## Final URL matrix (15 specified + 5 bonus probes, 20 total)

### Category A — Brave Stable Releases & Versionierung

| URL | Tag | Reason |
|---|---|---|
| `github.com/brave/brave-browser/releases` | **[VERIFIED]** HTTP 200 | API + page; current Stable v1.93.126 (Chromium 151.0.7922.34, 2026-07-22T21:52:13Z) |
| `brave.com/latest/` | **[VERIFIED]** HTTP 200 | Title "Brave Release Notes \| Brave"; content JS-rendered, search snippet "Upgraded Chromium to 150.0.7871.182" matches v1.92.143 |
| `github.com/brave/brave-browser/blob/master/CHANGELOG.md` | **[PHANTOM 404]** | Brave maintains per-tag GitHub releases, no master CHANGELOG.md |
| `www.bravesoftware.com/releases` | **[UNVERIFIED — bot-blocked]** HTTP 401 | Cloudflare 401; search snippet is marketing only |

### Category B — Perplexity Browser Add-on / Comet

| URL | Tag | Reason |
|---|---|---|
| `chromewebstore.google.com/detail/perplexity-ai-companion/hlgbcneanomplepojfcnclggenpcoldo` | **[VERIFIED]** HTTP 200 | Title "Perplexity - AI Companion - Chrome Web Store"; permissions/manifest in SPA render, not server HTML |
| `www.perplexity.ai/help-center/en/articles/11502647-supported-browsers-for-perplexity-web-app` | **[UNVERIFIED — bot-blocked]** HTTP 403 | Cloudflare block; existence confirmed via sitemap |
| `www.perplexity.ai/comet` | **[UNVERIFIED — bot-blocked]** HTTP 403 | Search snippet only |
| `comet-help.perplexity.ai/en/articles/11734730-operating-system-requirements` | **[PHANTOM]** 403 → redirect to `/help-center/comet/` | Article path silently serves root; Wikipedia confirms Comet lacks Linux release date |
| `comet-help.perplexity.ai/en/articles/11172798-getting-started-with-comet` | **[PHANTOM]** same as above | Same redirect pattern |
| `www.bleepingcomputer.com/news/security/fake-perplexity-extension-on-chrome-web-store-tracked-searches/` | **[VERIFIED]** HTTP 200 | Schema.org datePublished 2026-06-30T11:46:19-04:00, author Bill Toulas |
| `community.brave.app/t/incompatibility-of-brave-shield-with-ublock-origin/648045` | **[VERIFIED]** HTTP 200 | og:title confirmed; Discourse SPA hides replies |

### Category C — Brave auf Linux Flatpak

| URL | Tag | Reason |
|---|---|---|
| `flathub.org/apps/com.brave.Browser` | **[VERIFIED]** HTTP 200, redirect → `/en/apps/com.brave.Browser` | Title "Install Brave on Linux \| Flathub" |
| `docs.flatpak.org/en/latest/sandbox-permissions.html` | **[UNVERIFIED — bot-blocked]** HTTP 429 (`cf-mitigated: challenge`) | Real doc, CF challenge blocks; fallback: local `flatpak-doc` pkg |
| `github.com/flathub/com.brave.Browser` | **[VERIFIED]** HTTP 200 | Repo root listing via API confirms `com.brave.Browser.yaml` exists; `.json` does **not** |

### Category D — Chrome DevTools Protocol (FCP + JS-Heap)

| URL | Tag | Reason |
|---|---|---|
| `chromedevtools.github.io/devtools-protocol/` | **[VERIFIED]** HTTP 200 | Title "Chrome DevTools Protocol"; meta description mentions "version tot" |
| `chromedevtools.github.io/devtools-protocol/timeline/` | **[PHANTOM 404]** | Path doesn't exist in `tot` |
| `chromedevtools.github.io/devtools-protocol/tot/runtime/#method-evaluate` | **[PHANTOM 404]** | `/tot/runtime/` lowercase 404; correct is `/tot/Runtime/` (CamelCase) |
| `chromedevtools.github.io/devtools-protocol/tot/Runtime/` *(corrected path)* | **[VERIFIED]** HTTP 200 | Bonus probe; `id="method-evaluate"` and `id="method-getHeapUsage"` anchors present |
| `chromedevtools.github.io/devtools-protocol/tot/Performance/` *(bonus)* | **[VERIFIED]** HTTP 200 | Title "Chrome DevTools Protocol - Performance domain"; `id="method-getMetrics"`, FCP in metrics response |

### Category E — Linux Browser-Benchmark-Methodik

| URL | Tag | Reason |
|---|---|---|
| `www.phoronix.com/review/firefox-chrome-2026` | **[UNVERIFIED — bot-blocked]** HTTP 403 | Article confirmed: "Firefox 149 vs. Chrome 147", 2026-04-10 10:20 EDT, JetStream 3, Panther Lake + Ubuntu 26.04; CF blocks |
| `github.com/brave/brave-browser/wiki` | **[VERIFIED]** HTTP 200 | Title "Home · brave/brave-browser Wiki · GitHub"; real pages include `Brave-Release-Schedule`, `(Re)packaging`, `Adding-a-protocol-scheme-to-Brave`, etc.; **no** `Benchmarks` / `Performance-Testing` pages exist |
| `web.dev/articles/lcp` | **[VERIFIED]** HTTP 200 | Last-Modified 2025-09-04; stable Google canonical; description covers LCP measurement |

## Tallies

- `[VERIFIED]`: **9** (45%)
- `[UNVERIFIED — bot-blocked]`: **6** (30%) — search snippets added to rows
- `[PHANTOM 404]`: **3** (15%) — workarounds documented
- `[PHANTOM]` (silent redirect): **2** (10%)

Acceptable for a Phase 1 hand-off per the SKILL.md contract.

## Cross-cutting findings established by sources

These are facts about *the world*, not about the target system. Listed only because they will inform Phase 2/3 collector design and should not require re-fetching.

- **Brave Stable channel today:** v1.93.126, Chromium 151.0.7922.34, published 2026-07-22. Beta v1.94.94 (same Chromium), Nightly v1.95.3.
- **Comet Browser releases:** Win + macOS 2025-07-09, Android 2025-11-20, iOS 2026-03-18. No Linux release on record per Wikipedia.
- **CDP methods for measurement:** `Performance.getMetrics` (FCP), `Runtime.getHeapUsage` + `Runtime.evaluate` (JS heap). Confirm by `grep id="method-..."` against `/tot/<DomainName>/` page.
- **Flathub Brave manifest (`com.brave.Browser.yaml`, master):** `runtime: org.freedesktop.Platform`, `runtime-version: '25.08'`, `base: org.chromium.Chromium.BaseApp` (25.08). Finish-args include X11+Wayland, PulseAudio, FIDO2 (pcsc + bluetooth + bluez), GSecrets + KWallet5/6, UPower, Notifications, ScreenSaver family, MPRIS, dconf.
- **Brave webstore origin:** publisher "Perplexity" has clean record per CWS ownership badge; BleepingComputer 2026-06-30 documents a separately-named **fake** extension that tracked searches — useful for risk note in Phase 2.
- **Brave community uBO-Shields thread title:** "Incompatibility of brave shield with ublock origin" (verified by og:title; replies not extracted, SPA-rendered).

## Reproducing this matrix

```bash
# 1. Status sweep
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
for url in "${URLS[@]}"; do
  curl -kIL -s -o /dev/null \
       -w "%{http_code} | %{url_effective} | %{num_redirects}\n" \
       --max-time 15 -A "$UA" "$url"
done

# 2. Content extraction (curl+UA fallback when FIRECRAWL is unconfigured)
curl -sL --max-time 25 -A "$UA" "https://brave.com/latest/" \
  | sed 's/<[^>]*>/ /g' | tr -s ' \n\t' ' ' | head -c 1500

# 3. GitHub releases (structured JSON preferred over HTML)
curl -s -H 'Accept: application/vnd.github+json' \
  'https://api.github.com/repos/brave/brave-browser/releases?per_page=10' \
  | python3 -c 'import json,sys;[print(r["tag_name"], r["prerelease"], r["published_at"]) for r in json.load(sys.stdin)]'

# 4. Flathub manifest discovery
curl -s 'https://api.github.com/repos/flathub/com.brave.Browser/contents/' \
  | python3 -c 'import json,sys;[print(x["name"]) for x in json.load(sys.stdin)]'
# → confirms com.brave.Browser.yaml

# 5. CDP structure discovery (case-sensitive)
for path in "tot/Runtime" "tot/runtime" "tot/Performance" "tot/performance" "tot/Timeline"; do
  echo -n "/devtools-protocol/${path}/ -> "
  curl -kIs -o /dev/null -w "%{http_code}\n" --max-time 10 \
    "https://chromedevtools.github.io/devtools-protocol/${path}/"
done
```

## Notes for next-phase collector

These are not actionable as Phase-1 facts but flagged so Phase 3 doesn't waste cycles:

- `[PHANTOM 404]` and `[PHANTOM]` rows should drive the **methodology** — any Phase 3 attempt to call `Performance.getMetrics` must use the `/tot/Performance/` (CamelCase) page, not the `/tot/performance/` lowercase variant.
- `[UNVERIFIED — bot-blocked]` rows should be re-attempted in Phase 3 with a session cookie or via a non-bot path (e.g. browser MCP, logged-in curl).
- The BleepingComputer article's **fake-Perplexity** extension is a relevant threat-model note for selecting which CWS extension id to install at the target.
