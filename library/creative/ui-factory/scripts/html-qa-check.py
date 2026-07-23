#!/usr/bin/env python3
"""
HTML-QA-Check — strukturelle Validierung eines Single-File-HTML-Builds.
Prüft: Wohlgeformtheit, CSS-Brace-Balance, Token-Konsistenz, Inline-Style-Audit, File-Größe.

Usage:  python3 html-qa-check.py <path/to/index.html>
Return: Exit-Code 0 = PASS, 1 = FAIL

Entwickelt 2026-07-08 für den Yuno-MiniMax-Bundles Landing-Page-Build.
"""

import re
import html.parser
import sys

def check_html(path):
    with open(path) as f:
        src = f.read()

    lines = src.count('\n')
    bytes_ = len(src)
    print(f"📄 {path}")
    print(f"   Lines: {lines}  |  Bytes: {bytes_}")
    if bytes_ > 80_000:
        print(f"   ⚠️  >80 KB — erwäge External-Files für Tokens")

    # --- 1. HTML Wohlgeformtheit (Tag-Balance) ---
    class TagBalancer(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.errors = []
            self.void = {'meta','link','img','br','hr','input','source','area','base','col','embed','param','track','wbr'}
        def handle_starttag(self, tag, attrs):
            if tag not in self.void:
                self.stack.append((tag, self.getpos()))
        def handle_endtag(self, tag):
            if not self.stack:
                self.errors.append(f"Extra </{tag}>")
                return
            top, _ = self.stack[-1]
            if top != tag:
                self.errors.append(f"Mismatch: </{tag}> schließt <{top}>")
            self.stack.pop()

    balancer = TagBalancer()
    balancer.feed(src)
    remaining = len(balancer.stack)
    errors = balancer.errors
    status = "✅ PASS" if (remaining == 0 and len(errors) == 0) else "❌ FAIL"
    print(f"   HTML Well-Formed: {status}  (stack={remaining}, errors={len(errors)})")
    for e in errors[:3]:
        print(f"      {e}")

    # --- 2. CSS-Brace-Balance ---
    css_match = re.search(r'<style>(.*?)</style>', src, re.DOTALL)
    if css_match:
        css = css_match.group(1)
        css_no_comments = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
        open_b = css_no_comments.count('{')
        close_b = css_no_comments.count('}')
        css_lines = css.count('\n')
        status = "✅ PASS" if open_b == close_b else "❌ FAIL"
        print(f"   CSS Braces: {status}  (open={open_b}, close={close_b}, diff={open_b-close_b})")
        print(f"   CSS lines: {css_lines}")
    else:
        print(f"   ⚠️  Kein <style> Block gefunden!")

    # --- 3. Token-Konsistenz (var(--*) vs hardcoded Hex) ---
    var_usage = len(re.findall(r'var\(--[a-z0-9-]+\)', src))
    total_hex = len(re.findall(r'#[0-9A-Fa-f]{6}', src))
    # Hex in :root-Bereich zählen
    root_match = re.search(r':root\s*{([^}]+)}', src, re.DOTALL)
    in_root = 0
    if root_match:
        in_root = len(re.findall(r'#[0-9A-Fa-f]{6}', root_match.group(1)))
    outside_hex = total_hex - in_root
    print(f"   var(--*) usage: {var_usage}")
    print(f"   Hardcoded Hex total: {total_hex}  (in :root={in_root}, outside={outside_hex})")
    # meta theme-color ist legitim
    theme_color_matches = len(re.findall(r'<meta[^>]*theme-color[^>]*>', src))
    legit_outside = theme_color_matches
    suspicious = outside_hex - legit_outside
    status = "✅ PASS" if suspicious <= 0 else f"⚠️  {suspicious} suspect hex outside :root"
    print(f"   Token-Konsistenz: {status}")

    # --- 4. Inline-Style-Audit ---
    inline_styles = re.findall(r'style="([^"]*)"', src)
    print(f"   Inline style attrs: {len(inline_styles)}")
    for s in inline_styles:
        hint = "ok" if any(k in s for k in ['margin-left:auto', 'flex', 'grid', 'color:var', 'border-color:var']) else "CHECK"
        print(f"      [{hint}] style=\"{s[:80]}\"")

    # --- 5. Externe Assets ---
    ext_fonts = len(re.findall(r'fonts\.googleapis|@font-face|@import', src))
    ext_scripts = len(re.findall(r'<script[^>]*src="https?://', src))
    print(f"   External fonts: {ext_fonts}")
    print(f"   External scripts: {ext_scripts}")
    if ext_fonts > 0 or ext_scripts > 0:
        print(f"   ⚠️  Externe Requests — single-file build sollte 0 haben")

    print()
    failed = (remaining > 0 or len(errors) > 0 or open_b != close_b)
    return 1 if failed else 0

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    sys.exit(check_html(path))
