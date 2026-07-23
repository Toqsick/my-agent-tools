"""
Yuno Voice Reply Plugin — automatic TTS playback of Hermes responses.

Nimmt den Yuno-Response-Text, generiert TTS via Hermes-interne text_to_speech-API
(ohne Provider-Override), spielt das MP3 auf dem PulseAudio-Default-Sink ab.

SAFETY:
  - Provider aus config.yaml gelesen, NICHT überschrieben
  - Toggle via plugin.enabled — default OFF
  - Filterblöcke (Code, Bilder, File-Refs) werden vor Synthese entfernt
"""

from __future__ import annotations
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("yuno_voice_reply")

DEFAULTS = {
    "enabled": False,
    "min_chars": 50,
    "max_chars": 1800,
    "skip_if_contains": ["```", "MEDIA:", "![", "<file:", "/tmp/"],
    "player": "paplay",
    "fallback_player": "ffplay",
    "cache_dir": "~/.hermes/cache/audio/yuno-replies",
    "persist_audio": False,
}

# Entfernt Code-Blöcke, Inline-Code, Markdown-Images, URLs, Headings
_PREPROCESS_PATTERNS = [
    re.compile(r"```.*?```", re.DOTALL),
    re.compile(r"`[^`]*`"),
    re.compile(r"!\[[^\]]*\]\([^)]+\)"),
    re.compile(r"\[([^\]]+)\]\([^)]+\)"),
    re.compile(r"^#{1,6}\s+", re.MULTILINE),
    re.compile(r"<file:[^>]+>"),
]


def _load_config(ctx) -> dict:
    cfg = dict(DEFAULTS)
    try:
        pcfg = ctx.plugin_config("yuno_voice_reply") if hasattr(ctx, "plugin_config") else None
        if isinstance(pcfg, dict):
            cfg.update(pcfg)
    except Exception as e:
        log.debug("Plugin-Config-Read fehlgeschlagen: %s", e)
    return cfg


def _preprocess(text: str, cfg: dict) -> str | None:
    for blocker in cfg.get("skip_if_contains", []):
        if blocker in text:
            return None
    cleaned = text
    for pat in _PREPROCESS_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = re.sub(r"\s{3,}", "  ", cleaned).strip()
    if len(cleaned) < cfg.get("min_chars", 50):
        return None
    maxc = cfg.get("max_chars", 1800)
    if len(cleaned) > maxc:
        cleaned = cleaned[:maxc].rsplit(" ", 1)[0] + "…"
    return cleaned


def _tts_call(text: str, ctx) -> Path | None:
    for cand in ("synthesize_tts", "text_to_speech", "speak"):
        fn = getattr(ctx, cand, None)
        if callable(fn):
            try:
                result = fn(text=text)
                if isinstance(result, (str, Path)):
                    return Path(result)
                if isinstance(result, dict) and "file_path" in result:
                    return Path(result["file_path"])
            except Exception as e:
                log.warning("ctx.%s failed: %s", cand, e)
    try:
        from hermes.tools.audio import synthesize_voice
        out = synthesize_voice(text=text)
        if isinstance(out, (str, Path)):
            return Path(out)
        if isinstance(out, dict) and "file_path" in out:
            return Path(out["file_path"])
    except Exception as e:
        log.debug("hermes.tools.audio unavailable: %s", e)
    log.warning("Keine TTS-API — Plugin tut nichts.")
    return None


def _play(mp3: Path, cfg: dict) -> bool:
    if not mp3.exists():
        return False
    for player_name in (cfg.get("player"), cfg.get("fallback_player")):
        if not player_name:
            continue
        try:
            args = [player_name, str(mp3)]
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
    log.error("Kein Player (paplay/ffplay) verfügbar.")
    return False


def register(ctx):
    cfg = _load_config(ctx)
    log.info("register(enabled=%s, min_chars=%s)", cfg["enabled"], cfg["min_chars"])
    if not cfg["enabled"]:
        log.info("Plugin disabled per config — stumm.")
        return

    def on_post_response(text: str, **kwargs) -> None:
        if not text or not isinstance(text, str):
            return
        cleaned = _preprocess(text, cfg)
        if not cleaned:
            return
        mp3 = _tts_call(cleaned, ctx)
        if mp3 and _play(mp3, cfg) and not cfg.get("persist_audio", False):
            try:
                mp3.unlink(missing_ok=True)
            except Exception:
                pass

    for hook_name in ("post_response", "on_response", "response_complete"):
        if hasattr(ctx, "on") and callable(ctx.on):
            try:
                ctx.on(hook_name, on_post_response)
                log.info("Hook %s registriert", hook_name)
                break
            except Exception:
                pass
        if hasattr(ctx, "register_hook") and callable(ctx.register_hook):
            try:
                ctx.register_hook(hook_name, on_post_response)
                log.info("Hook %s registriert (register_hook)", hook_name)
                break
            except Exception:
                pass
