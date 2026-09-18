#!/usr/bin/env python3
"""Discover the marketplace's plugins and where their skills and agents live.

A plugin is any ``plugins/<name>/`` carrying ``.claude-plugin/plugin.json``.
The manifest's ``skills`` / ``agents`` keys are polymorphic — Claude Code accepts
both shapes and this repository uses both:

* a **string** naming a directory to scan, e.g. ``"skills": "skills"``
  (dev-loop-toolkit) — every ``SKILL.md`` beneath it is installed;
* a **list** of explicit paths, e.g. ``"skills": ["./skills/n8n", …]``
  (agent-toolkit) — that list is the real load switch, so a directory present on
  disk but absent from the list must NOT be indexed as installed;
* **absent** — fall back to the conventional ``skills/`` / ``agents/`` directory.

Shared by scripts/build_index.py and scripts/build_routing.py so the manifest
shapes are understood in exactly one place.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


class Plugin:
    __slots__ = ("name", "version", "root", "skills_root", "skill_dirs", "agents_dir")

    def __init__(self, name, version, root, skills_root, skill_dirs, agents_dir):
        self.name = name
        self.version = version
        self.root = root
        self.skills_root = skills_root      # Path | None — base for category derivation
        self.skill_dirs = skill_dirs        # list[Path] — the skills that actually load
        self.agents_dir = agents_dir        # Path | None

    def __repr__(self):  # pragma: no cover
        return f"<Plugin {self.name} v{self.version}: {len(self.skill_dirs)} skills>"


def _resolve_entries(root: Path, value, default_dirname: str, marker: str) -> tuple[Path | None, list[Path]]:
    """Return (base directory, the concrete entry directories/files)."""
    if isinstance(value, str):
        base = (root / value).resolve()
        return base, sorted(p.parent for p in base.rglob(marker)) if base.is_dir() else []
    if isinstance(value, list):
        base = (root / default_dirname).resolve()
        out = []
        for entry in value:
            p = (root / str(entry).lstrip("./")).resolve()
            if p.is_dir() and (p / marker).is_file():
                out.append(p)
            elif p.is_file():
                out.append(p.parent)
            else:
                print(f"WARN: {root.name}: manifest lists {entry!r} but it has no {marker}",
                      file=sys.stderr)
        return (base if base.is_dir() else None), sorted(set(out))
    base = (root / default_dirname).resolve()
    if base.is_dir():
        return base, sorted(p.parent for p in base.rglob(marker))
    return None, []


def discover_plugins(repo: Path) -> list[Plugin]:
    """Every plugin under ``repo/plugins`` that carries a manifest, name-sorted."""
    found: list[Plugin] = []
    for manifest in sorted((repo / "plugins").glob("*/.claude-plugin/plugin.json")):
        root = manifest.parent.parent
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN: unreadable manifest {manifest}: {e}", file=sys.stderr)
            continue
        skills_root, skill_dirs = _resolve_entries(root, data.get("skills"), "skills", "SKILL.md")
        skill_dirs = [d for d in skill_dirs if "/.archive/" not in d.as_posix()]
        agents_value = data.get("agents")
        agents_dir = None
        if isinstance(agents_value, str):
            cand = (root / agents_value).resolve()
            agents_dir = cand if cand.is_dir() else None
        elif agents_value is None:
            cand = (root / "agents").resolve()
            agents_dir = cand if cand.is_dir() else None
        found.append(Plugin(
            name=str(data.get("name") or root.name),
            version=str(data.get("version") or ""),
            root=root,
            skills_root=skills_root,
            skill_dirs=skill_dirs,
            agents_dir=agents_dir,
        ))
    return found
