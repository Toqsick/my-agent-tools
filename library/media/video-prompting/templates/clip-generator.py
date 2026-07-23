#!/usr/bin/env python3
"""Reusable multi-clip video generator template.

Drop-in CLI script for "I have a prompt package + an API key + I want videos generated".
Adapt the `generate_first_clip` function per project (replace prompt payload, model id,
endpoint). The CLI argument shape, polling, downloading, error handling, and CLI UX
stay stable across projects.

Usage:
    python3 clip-generator.py --clip 1 \\
        --api-key "$MINIMAX_VIDEO_KEY" \\
        --first-frame-url "https://i.imgur.com/abc.jpg"

Loops clips 1, 2, 3a; customize `main()` to map clip numbers to prompt functions.

Compatible with: api.minimax.io (HailuoAI Video), generic Bearer-auth video APIs.
NOT compatible with: FAL.ai queue-based APIs (different polling shape), Vertex AI
video models (different auth).
"""
import argparse
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://api.minimax.io/v1"
CLIP_DIR = Path.home() / "video-clips"
CLIP_DIR.mkdir(exist_ok=True)


def upload_local(path: Path) -> str:
    """Stub: HailuoAPI has no public upload endpoint in our tested paths.

    Workaround: host the first-frame on any public CDN (imgur, catbox.moe, your
    own bucket) and pass `--first-frame-url` directly. Skip this helper entirely.
    """
    raise NotImplementedError(
        "Use --first-frame-url with a manually hosted URL instead."
    )


def post_with_prompt(api_key: str, payload: dict, endpoint: str = "/video_generation") -> str:
    """POST the prompt payload, return task_id or raise with full context."""
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    br = data.get("base_resp", {})
    sc = br.get("status_code")
    if sc not in (0, None) and not data.get("task_id"):
        raise RuntimeError(f"API error {sc}: {br.get('status_msg')} | full={data}")
    task_id = data.get("task_id") or ""
    if not task_id:
        raise RuntimeError(f"No task_id returned: {data}")
    return task_id


def poll_task(api_key: str, task_id: str, query_path: str = "/query/video_generation",
              max_wait: int = 600) -> dict:
    """Poll task status until success/failed or timeout.

    Status-code compatibility:
    - Most providers return `status` or `state` at root. Some nest under base_resp.
    - We accept either and only log on state change to keep output terse.
    """
    start = time.time()
    last_state = None
    while time.time() - start < max_wait:
        req = urllib.request.Request(
            f"{API_BASE}{query_path}?task_id={task_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            print(f"  poll HTTP {e.code}, retrying in 5s...")
            time.sleep(5)
            continue
        state = (data.get("status") or data.get("state")
                 or data.get("base_resp", {}).get("status_msg", "?"))
        if state != last_state:
            print(f"  [{int(time.time()-start)}s] state={state}")
            last_state = state
        if str(state).lower() in ("success", "completed", "succeeded"):
            return data
        if str(state).lower() in ("failed", "fail", "error"):
            raise RuntimeError(f"Task failed: {data}")
        time.sleep(10)
    raise TimeoutError(f"Task not finished after {max_wait}s: {data}")


def download_video(url: str, dest: Path) -> Path:
    urllib.request.urlretrieve(url, dest)
    print(f"  Saved {dest} ({dest.stat().st_size} bytes)")
    return dest


# ──────────────────────────────────────────────────────────────────────
# Per-clip prompt functions. Customise each for your project.
# ──────────────────────────────────────────────────────────────────────

def generate_clip_1(api_key: str, first_frame_url: str) -> str:
    """Example: a 8-second cyberpunk approach clip."""
    return post_with_prompt(api_key, {
        "model": "MiniMax-Hailuo-2.3",
        "first_frame_image": first_frame_url,
        "prompt": (
            "Cinematic first-person POV dolly-in shot through a dark cyberpunk "
            "service alley. Cold cyan + warm tungsten lighting. Wet concrete "
            "reflections. End slow tilt-up to neon-lit megabuilding facade. "
            "Anamorphic 35mm, film grain, photorealistic. CDPR Phantom Liberty."
        ),
        "duration": 8,
        "resolution": "1080P",
    })


def generate_clip_2(api_key: str, first_frame_url: str) -> str:
    """Example: continuation clip. Adjust prompt + first frame."""
    return post_with_prompt(api_key, {
        "model": "MiniMax-Hailuo-2.3",
        "first_frame_image": first_frame_url,
        "prompt": "Replace with clip 2 prompt body.",
        "duration": 8,
        "resolution": "1080P",
    })


CLIP_FUNCTIONS = {
    1: generate_clip_1,
    2: generate_clip_2,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-clip video generator (api.minimax.io compatible)"
    )
    parser.add_argument("--clip", type=int, required=True, help="clip number")
    parser.add_argument("--api-key", required=True,
                        help='sk-api-... or env var name like "$MINIMAX_VIDEO_KEY"')
    parser.add_argument("--first-frame", type=Path,
                        help="local first-frame path (needs upload helper)")
    parser.add_argument("--first-frame-url", type=str,
                        help="public URL of first frame (preferred)")
    args = parser.parse_args()

    api_key = args.api_key
    if api_key.startswith("$"):
        api_key = os.environ.get(api_key[1:], "")
        if not api_key:
            print(f"Env-var {api_key} not set"); return 2

    if args.first_frame_url:
        url = args.first_frame_url
    elif args.first_frame:
        try:
            url = upload_local(args.first_frame)
        except NotImplementedError as e:
            print(f"{e}\nTip: host the image and use --first-frame-url"); return 3
    else:
        parser.error("--first-frame or --first-frame-url required")

    if args.clip not in CLIP_FUNCTIONS:
        print(f"Clip {args.clip} not configured. Add it to CLIP_FUNCTIONS.")
        return 1

    print(f"Clip {args.clip}: first frame = {url}")
    task_id = CLIP_FUNCTIONS[args.clip](api_key, url)
    print(f"Task-ID: {task_id}")
    result = poll_task(api_key, task_id)
    video_url = result.get("video_url") or result.get("file_url") or result.get("url")
    if not video_url:
        print(f"No video URL in result: {result}"); return 4
    out = CLIP_DIR / f"clip{args.clip}-task-{task_id}.mp4"
    download_video(video_url, out)
    print(f"Done: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
