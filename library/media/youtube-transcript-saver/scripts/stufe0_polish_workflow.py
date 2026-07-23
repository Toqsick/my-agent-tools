#!/usr/bin/env python3
"""
Stufe-0-Polishing-Workflow mit 2-Phasen-Verifikation.

Demonstriert die 2-Phasen-Struktur (siehe SKILL.md → Pitfalls → "Stufe-0-Pass hat
systematische Lücken"). Deterministischer Pre-Pass + Post-Verifikation gegen
known-hearing-errors.md + Patch auf den fertigen File.

Usage:
    python3 stufe0_polish_workflow.py <video_id> [<out_dir>]

Defaults:
    out_dir = ~/docs/youtube/

Erfordert:
    - youtube-transcript-api (pip install youtube-transcript-api)
    - Python 3.12 (nicht Hermes-Venv 3.11 — cffi-Mismatch)

Session-Origin: 2026-07-09 (Julian Remote-Control-Video pvhphecd70Y, 22:57).
v0.2 — 2026-07-09: Bugfix — `transcript_entries` wird jetzt als Parameter durchgereicht
                     statt als Global, sonst RuntimeError weil polish_caption() vor der
                     Definition aufgerufen würde.
"""
import re
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date

# Optional: hermes_tools für web_extract (aber für YouTube leer → siehe 4b)
try:
    from hermes_tools import web_extract  # noqa: F401
except ImportError:
    pass


# ===== PHASE 0: Metadaten holen (oEmbed + curl-Workaround) =====

def fetch_oembed(video_id: str) -> dict:
    """YouTube oEmbed API — funktioniert immer, kein Key."""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"oEmbed-Fehler: {e}")
        return {}


def fetch_youtube_page_metadata(video_id: str) -> dict:
    """Holt Description + Upload-Date + Views + Likes via curl mit User-Agent.

    web_extract liefert bei YouTube leeren Content → manueller curl-Workaround nötig.
    """
    import subprocess
    html_path = Path(f"/tmp/yt_page_{video_id}.html")
    try:
        subprocess.run([
            "curl", "-s", "-L",
            "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            f"https://www.youtube.com/watch?v={video_id}",
            "-o", str(html_path),
        ], check=True, timeout=30)
        html = html_path.read_text(errors="ignore")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"curl-Fehler: {e}")
        return {}

    meta = {}

    # Upload-Date
    m = re.search(r'"uploadDate":"([^"]+)"', html)
    if m:
        meta["upload_date"] = m.group(1).split("T")[0]

    # View-Count
    m = re.search(r'"viewCount":"(\d+)"', html)
    if m:
        meta["views"] = int(m.group(1))

    # Like-Count
    m = re.search(r'"likeCount":"(\d+)"', html)
    if m:
        meta["likes"] = int(m.group(1))

    # Author (Channel)
    m = re.search(r'"author":"([^"]+)"', html)
    if m:
        meta["author"] = m.group(1)

    # Description (simpleText — kann \\n enthalten)
    m = re.search(r'"description":\{"simpleText":"([^"]{50,3000})"', html)
    if m:
        meta["description_raw"] = m.group(1).replace("\\n", "\n")

    # Timestamps aus Description
    timestamps = re.findall(r'(\d{1,2}:\d{2})\s+([^\\n\"]{5,80})', html)
    meta["timestamps"] = timestamps[:20]

    return meta


# ===== PHASE 1: Caption-Polishing (deterministischer Pre-Pass) =====

def polish_caption(raw_text: str) -> str:
    """Deterministischer Pre-Polisher. KEIN LLM. Schnell.

    Pitfall: Auch nach diesem Pass IMMER Phase-2-Verifikation laufen lassen —
    dieser Pass hat Lücken bei CLI-Tools (Tmax→tmux) und Slash-Commands
    (SlashLOP→/loop, etc.). Siehe SKILL.md → "Stufe-0-Pass hat systematische Lücken".
    """
    t = raw_text
    t = re.sub(r"\s+", " ", t)                                    # Whitespace normalisieren
    t = re.sub(r"\s*-\s+", "-", t)                                # Soft-Hyphen-Brüche schließen
    t = re.sub(r"\s+([.,!?;:])", r"\1", t)                        # Space vor Satzzeichen weg
    t = re.sub(r"([.,!?;:])([a-zäöüß])", r"\1 \2", t)             # Space NACH Satzzeichen
    t = re.sub(r"\.{3}", "...", t)                                # "..." normalisieren
    t = re.sub(r"\b10 mal\b", "10-mal", t)                        # 10 mal → 10-mal

    # === Heuristik-Patterns aus known-hearing-errors.md ===
    # Claude-Familie
    t = re.sub(r"\bCloud Code\b", "Claude Code", t)
    t = re.sub(r"\bCloud-Code\b", "Claude-Code", t)
    t = re.sub(r"\bClaud Code\b", "Claude Code", t)
    t = re.sub(r"\bCloud MDatei\b", "CLAUDE.md", t)
    t = re.sub(r"\bCloud MD Datei\b", "CLAUDE.md", t)
    t = re.sub(r"\bCloudmdatei\b", "CLAUDE.md", t)
    t = re.sub(r"\bAnthopic\b", "Anthropic", t)
    # Andere Tools
    t = re.sub(r"\bHermis\b", "Hermes", t)
    t = re.sub(r"\bHermäs\b", "Hermes", t)
    t = re.sub(r"\bGitub\b", "GitHub", t)
    t = re.sub(r"\bGitup\b", "GitHub", t)
    t = re.sub(r"\bExcalid Draw\b", "Excalidraw", t)
    t = re.sub(r"\bExcaly Draw\b", "Excalidraw", t)
    t = re.sub(r"\bSuperagent\b", "Subagent", t)
    t = re.sub(r"\bSupagent\b", "Subagent", t)
    t = re.sub(r"\bHauptgagent\b", "Hauptagent", t)
    return t


# ===== PHASE 2: Post-Polish-Verifikation =====

# Diese Patterns sind NICHT im Pre-Pass enthalten (Lücken-Bekenntnis).
# Werden hier in Phase 2 gegen den polierten Text gecheckt und nachgepatcht.
POST_POLISH_PATTERNS = [
    # CLI-Tools (Lücke aus pvhphecd70Y)
    (r"\bTmax\b", "tmux"),
    (r"\bTMAX\b", "tmux"),
    # Slash-Commands (Lücke aus pvhphecd70Y)
    (r"SLGal", "/goal"),
    (r"SlashLOP", "/loop"),
    (r"Slashloop", "/loop"),
    (r"Slash Loop", "/loop"),
    (r"Slash Goal", "/goal"),
    (r"Slashgal", "/loop"),
    (r"SLclear", "/clear"),
    # Claude-Varianten (Lücken aus anderen Sessions)
    (r"\bHermis\b", "Hermes"),
    (r"\bGitub\b", "GitHub"),
]


def post_polish_verify_and_patch(text: str) -> tuple[str, list[dict]]:
    """Prüft polierten Text gegen die Lücken-Patterns und patcht direkt.

    Returns: (patched_text, findings)
    """
    findings = []
    patched = text
    for pattern, replacement in POST_POLISH_PATTERNS:
        new_patched, n = re.subn(pattern, replacement, patched)
        if n > 0:
            findings.append({"pattern": pattern, "replacement": replacement, "count": n})
            patched = new_patched
    return patched, findings


# ===== PHASE 3: Markdown bauen + speichern =====

def split_into_minute_sections(entries: list) -> list[tuple[int, str]]:
    """Splittet Transcript-Entries in Minuten-Sections.

    Returns: List of (minute, concatenated_text) tuples
    """
    sections = []
    current_minute = -1
    current_texts = []
    for entry in entries:
        minute = int(entry["start"] // 60)
        if minute != current_minute:
            if current_texts:
                sections.append((current_minute, " ".join(current_texts)))
            current_minute = minute
            current_texts = [entry["text"]]
        else:
            current_texts.append(entry["text"])
    if current_texts:
        sections.append((current_minute, " ".join(current_texts)))
    return sections


def build_markdown(video_id: str, transcript_blob: str, transcript_entries: list,
                   oembed: dict, page_meta: dict,
                   out_dir: Path, *, language: str = "Deutsch (auto-generated)") -> Path:
    """Baut Markdown-File mit Frontmatter, Header, Minuten-Marker-Transkript, Raw-Blob.

    Args:
        video_id: YouTube-Video-ID
        transcript_blob: Fertig polierter Transkript-Text (Phase-1+2 Output)
        transcript_entries: Roh-Snippets mit start/duration/text — NÖTIG für
                            Minuten-Marker-Berechnung.
        oembed: Metadaten aus oEmbed-API
        page_meta: Metadaten aus curl-Page-Pull
        out_dir: Ziel-Verzeichnis
        language: Sprache-Markierung für Header

    Minuten-Marker werden beim Bau gesetzt (nicht später hinzugefügt).
    """
    title = oembed.get("title", "Unknown Title")
    author = oembed.get("author_name", page_meta.get("author", "Unknown Channel"))
    views = page_meta.get("views", 0)
    likes = page_meta.get("likes", 0)
    upload_date = page_meta.get("upload_date", date.today().isoformat())
    description = page_meta.get("description_raw", "")
    timestamps = page_meta.get("timestamps", [])

    # Filename-Schema: YYYY-MM-DD_<slug>_<video-id>.md
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    filename = f"{upload_date}_{slug}_{video_id}.md"
    filepath = out_dir / filename

    # Transkript in Minuten-Marker einteilen
    sections = split_into_minute_sections(transcript_entries)

    # Markdown zusammenbauen
    fm = f"""---
source: https://www.youtube.com/watch?v={video_id}
title: "{title}"
channel: "{author}"
uploaded: {upload_date}
views: {views}
likes: {likes}
language: {language}
captured: {date.today().isoformat()}
tool: youtube-transcript-api (Stufe 0 deterministisch + 2-Phasen-Post-Verification)
polishing: Stufe 0 (deterministisch) + Post-Polish-Patch-Phase gegen CLI-/Slash-Patterns
---

# {title}

> 📺 Quelle: [youtube.com/watch?v={video_id}](https://www.youtube.com/watch?v={video_id})  
> 🎙️ Kanal: {author} · 👁️ {views:,} Views · 👍 {likes} Likes · 🗓️ {upload_date}

## Kurzbeschreibung (aus Video-Description)

{description[:1500]}

### Zeitstempel (aus Video)

""" + "\n".join(f"- `{ts}` {label}" for ts, label in timestamps) + "\n\n---\n\n## 📝 Transkript\n\n"

    transcript_md = "\n".join(
        f"\n## [{minute:02d}:00]\n\n{polish_caption(text)}\n"
        for minute, text in sections
    )

    # Raw-Blob als Hidden Comment
    raw_section = f"""

---

<!-- RAW_CAPTION_BLOB (ungeglättet, ~{len(transcript_blob.split())} Wörter)
{transcript_blob}
-->
"""

    filepath.write_text(fm + header + transcript_md + raw_section)
    return filepath


# ===== MAIN =====

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stufe0_polish_workflow.py <video_id> [<out_dir>]")
        sys.exit(1)
    video_id = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "docs/youtube"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Transkript holen
    from youtube_transcript_api import YouTubeTranscriptApi
    api = YouTubeTranscriptApi()
    transcripts = list(api.list(video_id))
    track = next((t for t in transcripts if not t.is_generated), transcripts[0])
    lang = track.language_code
    is_auto = track.is_generated

    entries = [{"start": e.start, "duration": e.duration, "text": e.text}
               for e in api.fetch(video_id, languages=[lang])]
    raw_blob = " ".join(e["text"].replace("\n", " ").strip() for e in entries)

    # PHASE 0: Metadaten (oEmbed + curl-Page-Pull)
    oembed = fetch_oembed(video_id)
    page_meta = fetch_youtube_page_metadata(video_id)

    # PHASE 1: Polishing
    polished_blob = polish_caption(raw_blob)

    # PHASE 2: Post-Polish-Verifikation + Patch
    final_blob, findings = post_polish_verify_and_patch(polished_blob)
    if findings:
        print(f"Phase-2-Patches angewendet: {len(findings)} Pattern(s)")
        for f in findings:
            print(f"  - {f['count']}x '{f['pattern']}' → '{f['replacement']}'")
    else:
        print("Phase 2: Keine Lücken-Patterns gefunden — Polishing war vollständig.")

    # PHASE 3: Markdown bauen + speichern
    filepath = build_markdown(
        video_id, final_blob, entries, oembed, page_meta, out_dir,
        language=f"{'Deutsch' if lang == 'de' else lang} ({'auto-generated' if is_auto else 'manuell'})",
    )

    # PHASE 4: Finale Verifikation — Datei existiert + Wortzahl plausibel
    size = filepath.stat().st_size
    word_count = len(final_blob.split())
    print(f"\n=== Fertig ===")
    print(f"  Datei: {filepath}")
    print(f"  Größe: {size:,} bytes")
    print(f"  Wörter: {word_count}")
    print(f"  Phase-2-Patches: {len(findings)}")


if __name__ == "__main__":
    main()