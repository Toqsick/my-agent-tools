#!/usr/bin/env python3
"""
depps_spawn.py - Workaround smoke-test for the owl-alpha 404 bug.

Context (see /home/bratan/docs/system/hermes-owl-alpha-provider-bug-2026-07-01.md):
  - Hermes delegate_task caches delegation.* config in CLI_CONFIG at agent-start,
    so editing delegation.provider / delegation.model does NOT affect already-running
    subagent workflows.
  - openrouter/owl-alpha was removed by OpenRouter and now returns 404.
  - Workaround: call OpenRouter API directly with a working free-tier model,
    bypassing the hermes CLI_CONFIG cache. This file recreates the v0.2.0
    spawn helper that the slim-down on 2026-07-02 removed.

Usage:
  depps_spawn.py health
  depps_spawn.py spawn --goal "..." [--context "..."] [--model openai/gpt-oss-20b:free]
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AUDIT_DIR = Path.home() / ".hermes" / "depps-audit"
SENTINEL = "##DEPPS_DONE##"
DEFAULT_MODEL = "openai/gpt-oss-20b:free"


def _load_openrouter_key():
    env = Path.home() / ".hermes" / ".env"
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def _audit_log(event, **fields):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = AUDIT_DIR / f"{day}.jsonl"
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "worker": DEFAULT_MODEL,
        "event": event,
    }
    rec.update(fields)
    with path.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def cmd_health(_args):
    key = _load_openrouter_key()
    if not key:
        print("ERROR: OPENROUTER_API_KEY missing in ~/.hermes/.env")
        return 1
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": "Bearer " + key},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            free = sorted(
                m["id"] for m in data.get("data", []) if ":free" in m["id"].lower()
            )
            print("OK  HTTP 200 - OpenRouter reachable.")
            print("     " + str(len(free)) + " free-tier models available.")
            for mid in free[:5]:
                print("     - " + mid)
            _audit_log("health", free_count=len(free), first_five=free[:5])
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print("ERROR HTTP " + str(e.code) + ": " + body)
        _audit_log("health_error", http_code=e.code, body=body)
        return 2
    except Exception as e:
        print("ERROR " + type(e).__name__ + ": " + repr(e))
        _audit_log("health_error", exc=repr(e))
        return 3


def cmd_spawn(args):
    key = _load_openrouter_key()
    if not key:
        print("ERROR: OPENROUTER_API_KEY missing in ~/.hermes/.env")
        return 1

    prompt = args.goal
    if args.context:
        prompt += "\n\nCONTEXT:\n" + args.context
    prompt += (
        "\n\nWhen you have finished, end your reply with the exact sentinel line: "
        + SENTINEL
    )

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": args.max_tokens,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hermes.local/depps-spawn",
        },
        method="POST",
    )

    task_id = "depps-" + str(int(time.time())) + "-" + str(os.getpid())
    toolsets = [t.strip() for t in args.toolsets.split(",") if t.strip()]
    _audit_log(
        "spawn",
        task_id=task_id,
        goal_len=len(args.goal),
        context_len=len(args.context or ""),
        toolsets=toolsets,
        model=args.model,
        fallback="none",
    )

    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = resp.read().decode()
            data = json.loads(body)
            if "choices" not in data:
                # API returned an error payload, not a chat completion
                raise RuntimeError("no 'choices' in response: " + body[:200])
            duration = round(time.time() - started, 2)
            choice = data["choices"][0]
            msg = choice.get("message", {}) or {}
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning") or ""
            # Sentinel can appear in content OR in reasoning tokens (reasoning-only models).
            search_text = (content or "") + "\n" + (reasoning or "")
            if not content and reasoning:
                content = "[reasoning-only] " + reasoning
            usage = data.get("usage", {}) or {}
            sentinel_found = bool(search_text.strip()) and SENTINEL in search_text
            _audit_log(
                "spawn_ok",
                task_id=task_id,
                model=data.get("model", args.model),
                duration_s=duration,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                sentinel_found=sentinel_found,
            )
            print("=== TASK " + task_id + " (" + str(duration) + "s) ===")
            print(content)
            print("=== END TASK " + task_id + " ===")
            print("sentinel_found=" + str(sentinel_found))
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        duration = round(time.time() - started, 2)
        _audit_log(
            "spawn_http_error",
            task_id=task_id,
            http_code=e.code,
            duration_s=duration,
            body=body,
        )
        print("ERROR HTTP " + str(e.code) + ": " + body)
        return 2
    except Exception as e:
        duration = round(time.time() - started, 2)
        import traceback
        tb = traceback.format_exc()
        _audit_log(
            "spawn_error",
            task_id=task_id,
            exc=repr(e),
            duration_s=duration,
            traceback=tb[:800],
        )
        print("ERROR " + type(e).__name__ + ": " + repr(e))
        print(tb)
        return 3


def main():
    p = argparse.ArgumentParser(prog="depps_spawn.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")

    sp = sub.add_parser("spawn")
    sp.add_argument("--goal", required=True)
    sp.add_argument("--context", default="")
    sp.add_argument("--model", default=DEFAULT_MODEL)
    sp.add_argument("--provider", default="openrouter")
    sp.add_argument("--toolsets", default="file,terminal")
    sp.add_argument("--max-tokens", type=int, default=400)
    sp.add_argument("--timeout", type=int, default=60)

    args = p.parse_args()
    if args.cmd == "health":
        return cmd_health(args)
    if args.cmd == "spawn":
        return cmd_spawn(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())