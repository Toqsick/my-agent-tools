# Cross-Session Lesson Consolidation — Query-Erfahrungen & Referenzen

> **Eingesetzt:** 2026-07-07
> **Quell-Sessions:** `20260705_135346_e0e13b`, `20260618_040154_8ec797`, diverse Cron/Telegram-Sessions
> **Output:** 17 Lessons, 26.6 KB, 3 Kategorien
> **Ort:** `~/Dokumente/Obsidian Vault/07 Archiv/2026-07-07 - Self-Improving Lessons Hardware Performance.md`

## Verwendete Session-Search-Queries

### Discovery-Phase (nach Sessions suchen)

| Query | Limit | Treffer | Bemerkung |
|-------|-------|---------|-----------|
| `Coolbits powersave NVMe scheduler governor` | 5 | ✅ session 48890 (Performance-Plan) | Gefunden |
| `telegram chat not found gateway timeout delivery error` | 5 | ❌ 0 Treffer | **Zu spezifisch** |
| `cron gateway timeout telegram delivery chat not found error restart block` | 10 | ❌ 0 Treffer | **Textbaustein zu lang** |
| `hermes gateway restart block stop telegram bot` | 10 | ✅ session 47126 (Yuno Chat Setup) | Gefunden |
| `TELEGRAM_CHAT_ID chat not found message too long timeout` | 5 | ❌ 0 Treffer | — |
| `yuno-cleaner cron inline telegram token secret crontab backup restore` | 5 | ❌ 0 Treffer | — |
| `Mnemosyne Cron Monthly Cleanup Telegram timeout 10KB` | 5 | ❌ 0 Treffer | — |
| `Zweiter Monitor Auflösung Troubleshooting` | 5 | ✅ session 48890 | Titel-Kontext |
| session_id `20260705_135346_e0e13b` (Direkt) | — | ✅ Performance-Plan + Crontab-Recovery | 229 Messages |
| session_id `20260618_040154_8ec797` (Direkt) | — | ✅ EDID-Fix gesamte Session | 376 Messages |

### Scroll-Phase (in Session eintauchen)

| Target-Session | around_message_id | window | Ergebnis |
|----------------|-------------------|--------|----------|
| `20260705_135346_e0e13b` | 48829 | 15 | Performance-Plan-Eingabe (User-Prompt) ✅ |
| `20260705_135346_e0e13b` | 48835 | 10 | Vollständiger Plan-Assistant ✅ |
| `20260705_135346_e0e13b` | 48890 | 5 | Vault-Befüllung ✅ |
| `20260705_135346_e0e13b` | 49000 | 5 | Crontab-Recovery (Mitte, Snapshot) ✅ |
| `20260705_135346_e0e13b` | 48700, 48750 | 8-10 | ❌ "not in session" (IDs außerhalb Range) |
| `20260618_040154_8ec797` | 10950 | 5 | Card1/card2-Topologie ✅ |
| `20260618_040154_8ec797` | 11020 | 15 | EDID-Fix-Mitte, Vollbild ✅ |
| `20260628_131246_808b5a` | — | read | Systemdoku (376 Msgs, truncated 105KB+) ⚠️ |

## Scroll-Pitfalls (was schiefging)

### 1. FTS5-Trefferquote: 0/7 = 0 % bei langen Phrasen

7 von 7 Discovery-Queries mit >4 Wörtern lieferten 0 Treffer, obwohl der
Inhalt in den Sessions existierte. **Ursache:** FTS5-Indexing zerlegt in
Einzelwörter — Phrasen wie "cron gateway timeout telegram" werden als
AND-Verknüpfung gesucht, und wenn ein Wort im Index anders vorkommt
(z.B. "timeout" vs "timed out") → 0 Treffer.

**Fix:** Kurze Queries (1-3 Wörter), Multiple Winkel parallel:

```python
# Statt einer langen Query:
session_search(query="cron gateway timeout telegram delivery error chat not found", limit=5)

# Besser: Drei kurze parallel:
session_search(query="cron AND gateway", limit=3)
session_search(query="telegram AND timeout", limit=3)
session_search(query="chat not found", limit=3)
```

### 2. "around_message_id out of range" bei tiefen Scrolls

Bei Session `20260705_135346_e0e13b` lagen die sichtbaren Message-IDs im
Bereich 48829–49057. Scroll-Versuche auf 48700 oder 48750 schlugen fehl,
weil diese IDs außerhalb des gespeicherten Message-Bereichs lagen.

**Fix:** Vor dem Scroll immer die bookend_start-IDs checken. Die älteste
Message-ID ist die Untergrenze.

### 3. Massive Truncation bei Session-Read (20260628)

`session_search(session_id="20260628_131246_808b5a")` lieferte
"Full output could not be saved to sandbox (179,792 chars)" — der Read-Modus
hat die gesamte 376-Message-Session geladen.

**Fix:** Immer `limit=3` bei Discovery (verhindert whole-session-read),
und für tiefe Analysen immer `around_message_id` mit `window=10-20`
verwenden (nicht raw-read).

### 4. Discovery-Hit auf tool-output statt user/assistant

Manche Discovery-Treffer landeten auf tool-Output (JSON-Responses,
Status-Meldungen). Der Snippet-Kontext war dann nutzlos (zeigte nur
Tool-Response-Content, nicht das User-Problem).

**Fix:** `role_filter='user,assistant'` setzen in session_search. Oder:
die 2 Messages vor dem Match lesen (via retry mit window=3).

### 5. Scroll-Kosten-Optimierung

Jeder Scroll-Call mit window=15 kostet ~200 Input-Tokens (je nach
Message-Länge). Bei 3 Sessions × 3 Scroll-Calls = ~1.800 Tokens für
Discovery + ~1.200 Tokens für Content = ~3.000 Tokens gesamt.

**Optimierung:**
- Batch immer 2-3 parallele Scrolls/Discoveries pro Response
- window=10 präziser als window=20 (selten relevant)
- discovery-truncation vermeiden (limit=3 statt 10)

### 6. Tesseract-PSM-Parallel-Check (neu: 2026-07-07)

**Symptom:** PSM 3 vs PSM 6 liefern unterschiedliche Texte für gleiches Bild
(z.B. "1542" vs "1522" für Port-Nummer). Welcher ist richtig?

**Root Cause:** Tesseract PSM (Page Segmentation Mode) beeinflusst
Spalten-Erkennung. PSM 6 = "Uniform block of text" erkennt Port-Nummern
manchmal falsch bei ungewöhnlichem Font oder DPI. PSM 3 = "Auto" ist bei
langen Texten stabiler, aber bei UI-Elementen schwächer.

**Empfehlung:** Für kritische Werte (IPs, Ports, Versionen, Usernamen):
2-3 PSMs parallel + Majority-Vote:

```python
results = []
for psm in [3, 4, 6]:
    r = subprocess.run(["tesseract", img, "-", "-l", "eng", "--psm", str(psm)], ...)
    results.append(r.stdout.strip())
# Wenn alle 3 gleiche Zahl: vertraue. Wenn nur 2: Majority-Vote.
# Wenn alle 3 abweichen (selten): vertraue PSM 4 (column mode).
```

### 7. Cuad-Driver Key-Name-Inkonsistenz (neu: 2026-07-07)

**Symptom:** `cua-driver call get_window_state` gibt Screenshot-Base64
zurück, aber der Key-Name variiert zwischen Versionen:
- `screenshot_png_b64` (manche Versionen)
- `screenshot_base64` (andere)
- `screenshot_file_path` (wieder andere)

**Fix (Try-Key-Chain):**
```python
for key in ("screenshot_png_b64", "screenshot_base64", "screenshot"):
    png_b64 = data.get(key)
    if png_b64: return base64.b64decode(png_b64)
for key in ("screenshot_file_path",):
    path = data.get(key)
    if path and os.path.exists(path): return Path(path).read_bytes()
```

### 8. Storage-Bloat-Monitoring (neu: 2026-07-07)

**Symptom:** Observer-Skill (5s Interval) erzeugt 254 Captures in 15
Minuten. Vault wächst von 177 auf 452 Notizen ohne Cleanup.

**Empfehlung:** Wenn Background-Processes Dateien in beobachteten
Verzeichnissen erzeugen: vorher `find | wc -l`, nachher erneut prüfen.
Wenn Zuwachs > 10 pro Minute: Daily-Note-Format vorschlagen.
Maximum 100 Captures ohne User-Warnung.

### 9. User-Driven Navigation Pattern (neu: 2026-07-07)

**Symptom:** 2-Wege-Navigation funktioniert besser als autonomous clicks
wenn Anti-Cheat blockt. User sagt "bin drauf" → Agent screenshotted +
extrahiert. 9 Manual-Kapitel in <10 Minuten vs. 0 erfolgreiche automatisierte Klicks.

**Empfehlung:** Wenn 3 aufeinanderfolgende Tool-Calls fehlschlagen und das
Problem ein Input-Block ist (unverifiable, keine State-Change): sofort auf
User-Driven-Navigation umschalten. User erwartet diesen Fallback.

## Output-Schema (17 Lessons, 2026-07-07)

Das finale Dokument hatte dieses Schema:

```
# Self-Improving Lessons — <Thema> (Konsolidiert <Datum>)

**Quell-Sessions:**
1. <session_id> (<Kurztitel>)
2. ...

---

## 🟥 <KATEGORIE-NAME>

### [<DATUM>] <Lesson-Titel>
- **Symptom:** ...
- **Root Cause:** ...
- **Fix:** ...
- **Guard:** ...
- **Status:** verified | hypothese
- **Kategorie:** tool-quirk | build-error | workflow | orchestration | hardware

---

## 🟧 <KATEGORIE-2>
...

## 🔗 Cross-References
- `<Link zu Datei oder Skill>`
```

### Categories used (2026-07-07)

| Category | Prefix | # Lessons | Topics |
|----------|--------|-----------|--------|
| PERFORMANCE / TREIBER | 🟥 | 6 | Coolbits/Wayland, Lockdown, Governor, GameMode, PCIe, NVMe |
| DISPLAY / EDID | 🟥 | 5 | EDID-kaputt, MST-Routing, GRUB-Pfad, xorg.conf, Coolbits |
| CRON / TELEGRAM / GATEWAY | 🟥 | 6 | Inline-Secrets, Crontab-Dedup, 25-Tage-Sperre, HTML-vs-Markdown, Chat-not-found, 10KB-Timeout |
| SYSTEM-WARTUNG / WORKFLOW | 🟧 | 3 | Stufen-Reihenfolge, 8-Ordner-Struktur, Safety-Nets |

### Lesson Template (Einzel-Eintrag)

Jede Lesson ist self-contained — eine zukünftige Session kann sie lesen
und das Problem in 5 Minuten lösen, ohne die Original-Session zu laden:

```markdown
### [2026-06-18] Acer XB240H EDID-Binary war kaputt (136 Bytes, Müll-Timings)

- **Symptom:** Zweitmonitor nur 1024x768@60Hz statt 1920x1080@144Hz. Kernel-Log: 8×/Boot `i915: *ERROR* Invalid firmware EDID "edid/acer-xb240h.bin"`.
- **Root Cause:** EDID-Datei war 136 Bytes statt 128 — Detailed Timing Descriptors zeigten "7×752 @ 837Hz" (Müll), Established+Standard Timings leer, 8 Extra-Bytes am Ende. i915 lehnte ab.
- **Fix:** Komplett neues 128-Byte-EDID v1.4 synthetisiert via Python: CVT-RB v2 (pixclk 325.08 MHz), Range V 50-144 Hz, Name "Acer XB240H". Checksum-validiert. Installiert nach `/lib/firmware/edid/` + `/usr/lib/firmware/edid/`.
- **Guard:** `python3 -c "data=open('/lib/firmware/edid/acer-xb240h.bin','rb').read(); print(len(data), sum(data)&0xFF==0)"`. Nach Boot: `dmesg | grep -iE "edid|firmware" | grep -i invalid` muss leer sein.
- **Status:** verified
- **Kategorie:** hardware
- **Cross-Reference:** Verwandt mit "GRUB EDID-Pfad muss DP-1 sein (Root-Connector)"
```

## Referenzen

Referenz-Output-Dokument:
`~/Dokumente/Obsidian Vault/07 Archiv/2026-07-07 - Self-Improving Lessons Hardware Performance.md`

Enthält 17 vollständige Lessons plus Cross-References, 26.6 KB.

## Verbundene Skills

- `daily-briefing` `references/cron-delivery-patterns.md` — Telegram Delivery Timeout (+10KB) Pattern
- `daily-briefing` `references/telegram-delivery-errors.md` — Chat-not-found Diagnostic
- `linux-display-setup` — Display/EDID-Troubleshooting
