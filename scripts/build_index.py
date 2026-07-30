#!/usr/bin/env python3
"""build_index.py — regenerate INDEX.json + NAVIGATION.md for my-agent-tools.

This is the maintainability backbone of the repo's routing layer. It scans every
SKILL.md in two tiers — the *installed* plugin (loaded into each Claude Code
session) and the browsable *library* (fetched on demand via the GitHub MCP) —
normalizes their wildly inconsistent frontmatter into one uniform record, and
emits a single machine-readable catalog plus a human/LLM navigation file.

Nobody hand-edits a ~1,400-entry index; run this after any import:

    python3 scripts/build_index.py

Deterministic: `generated_at` is taken from the current git HEAD commit time, so
two consecutive runs on the same tree produce byte-identical output.

Outputs (repo root):
  INDEX.json     — master catalog {schemaVersion, counts, categories, skills[], agents[], workflows[]}
  NAVIGATION.md  — category tables with counts (installed + library) + agents + workflows
  routing/registry/* — repository-relative MCP-aware routing artifacts

No third-party deps required beyond PyYAML (falls back to a minimal parser).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
    _HAVE_YAML = True
except Exception:  # pragma: no cover
    _HAVE_YAML = False

REPO = Path(__file__).resolve().parent.parent
INSTALLED_DIR = REPO / "plugins" / "agent-toolkit" / "skills"
LIBRARY_DIR = REPO / "library"
AGENTS_DIR = REPO / "plugins" / "agent-toolkit" / "agents"
WORKFLOWS_DIR = REPO / "workflows"
NAMESPACE = "agent-toolkit"
REPO_SLUG = "Toqsick/my-agent-tools"
SCHEMA_VERSION = "2.0"  # keep in sync with scripts/build_routing.py

# ---- installed-skill provenance map (best-effort) --------------------------
MINIMAX = {
    "minimax-ai-agent-builder", "minimax-crypto-trading", "minimax-docx",
    "minimax-pdf", "superpower-10x", "mmx-cli",
}
DOWNLOADS_CURATED = {
    "pptx-generator", "n8n", "clickhouse-best-practices", "nano-banana-pro",
    "prompt-engineer", "deep-research-agent", "frontend-design",
    "mckinsey-presentation-generator", "research-paper-generator",
    "seo-geo-optimization-expert", "web-scraper", "excel-xlsx", "job-hunter",
    "sales-power-map", "saas-niche-finder",
}

# ---------------------------------------------------------------------------


def git_head_time() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "log", "-1", "--format=%cI"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Empty frontmatter if none."""
    if text.startswith("﻿"):
        text = text.lstrip("﻿")
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", text, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return "", text


def minimal_parse(block: str) -> dict:
    """Dependency-free fallback: extract flat scalar/list keys we care about."""
    data: dict = {}
    key = None
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^\s*-\s+", raw) and key:  # block list item
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(raw.split("-", 1)[1].strip().strip("'\""))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            data[key] = []  # may be a block list; items appended above
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        else:
            data[key] = val.strip("'\"")
    return data


def parse_frontmatter(text: str) -> tuple[dict, str]:
    block, body = split_frontmatter(text)
    if not block.strip():
        return {}, body
    if _HAVE_YAML:
        try:
            data = yaml.safe_load(block)
            if isinstance(data, dict):
                return data, body
        except Exception:
            pass
    return minimal_parse(block), body


def as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        return [p.strip().strip("'\"") for p in re.split(r"[,;]", s) if p.strip()]
    return [str(v)]


def collapse(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip() if s is not None else ""


def first_sentence(desc: str, cap: int = 180) -> str:
    desc = collapse(desc)
    m = re.match(r"^(.*?[.!?])(\s|$)", desc)
    hint = m.group(1) if m else desc
    return hint[:cap].rstrip()


def derive_description(fm: dict, body: str) -> str:
    d = collapse(fm.get("description") or fm.get("summary") or "")
    if d:
        return d[:600]
    # fall back to first non-heading paragraph of the body
    for para in re.split(r"\r?\n\s*\r?\n", body):
        p = collapse(re.sub(r"^#+\s*", "", para.strip()))
        if p and not p.startswith("|") and len(p) > 20:
            return p[:600]
    return ""


def collect_triggers(fm: dict) -> list[str]:
    keys = ("triggers", "trigger", "trigger-words", "trigger_keywords",
            "keywords", "tags")
    seen, out = set(), []
    for k in keys:
        for t in as_list(fm.get(k)):
            tl = t.lower()
            if tl and tl not in seen and len(tl) <= 40:
                seen.add(tl)
                out.append(tl)
    return out


def build_record(skill_md: Path, tier: str, base: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    if not isinstance(fm, dict):
        fm = {}
    slug = skill_md.parent.name
    rel = skill_md.relative_to(REPO).as_posix()
    # category: frontmatter first, else first path segment under the tier base
    category = collapse(fm.get("category") or fm.get("domain") or "")
    if not category:
        try:
            parts = skill_md.parent.relative_to(base).parts
            category = parts[0] if len(parts) > 1 else "standalone"
        except Exception:
            category = "standalone"
    tags = [t.lower() for t in as_list(fm.get("tags"))]
    desc = derive_description(fm, body)
    rec = {
        "id": slug,
        "name": collapse(fm.get("name")) or slug,
        "description": desc,
        "tier": tier,
        "namespace": f"{NAMESPACE}:{slug}" if tier == "installed" else None,
        "path": rel,
        "category": category,
        "tags": tags,
        "triggers": collect_triggers(fm),
        "routing_hint": first_sentence(desc),
        "source": provenance(slug, tier, fm),
    }
    # optional / sparse facets — only include when present
    for key in ("domain", "subdomain", "license"):
        val = collapse(fm.get(key))
        if val:
            rec[key] = val
    for key in ("mitre_attack", "nist_csf"):
        vals = as_list(fm.get(key))
        if vals:
            rec[key] = vals
    ver = fm.get("version")
    if ver not in (None, ""):
        rec["version"] = str(ver)
    return rec


def provenance(slug: str, tier: str, fm: dict) -> str:
    if tier == "library":
        return "hermes-arsenal"
    if slug in MINIMAX:
        return "minimax"
    if slug == "zcode-subagent-team":
        return "zcode"
    if slug in DOWNLOADS_CURATED:
        return "downloads"
    if slug.startswith("superpowers-"):
        return "superpowers"
    if fm.get("mitre_attack") or fm.get("nist_csf"):
        return "kyssta-cyber"
    return "original"


def scan_tier(base: Path, tier: str) -> list[dict]:
    if not base.exists():
        return []
    records = []
    for skill_md in sorted(base.rglob("SKILL.md")):
        if "/.archive/" in skill_md.as_posix():
            continue
        try:
            records.append(build_record(skill_md, tier, base))
        except Exception as e:  # never let one bad file break the whole index
            print(f"WARN: failed to parse {skill_md}: {e}", file=sys.stderr)
    return records


def scan_agents() -> list[dict]:
    if not AGENTS_DIR.exists():
        return []
    out = []
    for md in sorted(AGENTS_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(fm, dict):
            fm = {}
        out.append({
            "id": md.stem,
            "name": collapse(fm.get("name")) or md.stem,
            "description": collapse(fm.get("description")),
            "model": collapse(fm.get("model")) or "inherit",
            "path": md.relative_to(REPO).as_posix(),
        })
    return out


def scan_workflows() -> list[dict]:
    if not WORKFLOWS_DIR.exists():
        return []
    out = []
    for md in sorted(WORKFLOWS_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(fm, dict):
            fm = {}
        phases = fm.get("phases") if isinstance(fm.get("phases"), list) else []
        out.append({
            "id": collapse(fm.get("id")) or md.stem,
            "name": collapse(fm.get("name")) or md.stem,
            "when": collapse(fm.get("when_to_use") or fm.get("when")),
            "skills": as_list(fm.get("skills")),
            "agents": as_list(fm.get("agents")),
            "phases": phases,
            "path": md.relative_to(REPO).as_posix(),
        })
    return out


def build_categories(skills: list[dict]) -> list[dict]:
    agg: dict[str, dict] = {}
    for s in skills:
        c = agg.setdefault(s["category"], {"id": s["category"], "count": 0,
                                           "installed": 0, "library": 0})
        c["count"] += 1
        c[s["tier"]] += 1
    return sorted(agg.values(), key=lambda x: (-x["count"], x["id"]))


def build_tag_vocabulary(skills: list[dict]) -> list[str]:
    tags = set()
    for s in skills:
        tags.update(s.get("tags", []))
    return sorted(tags)


def main() -> int:
    installed = scan_tier(INSTALLED_DIR, "installed")
    library = scan_tier(LIBRARY_DIR, "library")
    skills = sorted(installed + library,
                    key=lambda s: (0 if s["tier"] == "installed" else 1,
                                   s["category"], s["id"], s["path"]))
    agents = scan_agents()
    workflows = scan_workflows()
    categories = build_categories(skills)

    index = {
        "schemaVersion": SCHEMA_VERSION,
        "generated_at": git_head_time(),
        "repo": REPO_SLUG,
        "how_to_use": "See ROUTING.md. Fetch this file, match a task against "
                      "each skill's triggers/tags/category, rank, then fetch the "
                      "chosen skill's `path`. Installed skills also load in-session "
                      "as their `namespace`. Multi-step work: see `workflows`.",
        "counts": {
            "installed": len(installed),
            "library": len(library),
            "skills_total": len(skills),
            "agents": len(agents),
            "workflows": len(workflows),
            "categories": len(categories),
        },
        "tag_vocabulary": build_tag_vocabulary(skills),
        "categories": categories,
        "skills": skills,
        "agents": agents,
        "workflows": workflows,
    }

    (REPO / "INDEX.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    write_navigation(index)
    from build_routing import main as build_routing
    build_routing()
    print(f"INDEX.json: {len(installed)} installed + {len(library)} library "
          f"= {len(skills)} skills, {len(agents)} agents, {len(workflows)} workflows, "
          f"{len(categories)} categories")
    return 0


def write_navigation(index: dict) -> None:
    c = index["counts"]
    lines: list[str] = []
    lines.append("# NAVIGATION — my-agent-tools skill index")
    lines.append("")
    lines.append("> **Generated by `scripts/build_index.py` — do not hand-edit.** "
                 "The machine-readable source of truth is [`INDEX.json`](INDEX.json); "
                 "routing rules are in [`ROUTING.md`](ROUTING.md).")
    lines.append(f"> Snapshot: HEAD `{index['generated_at'] or 'uncommitted'}` · "
                 f"**{c['skills_total']} skills** "
                 f"({c['installed']} installed + {c['library']} library) · "
                 f"{c['agents']} agents · {c['workflows']} workflows · "
                 f"{c['categories']} categories")
    lines.append("")
    lines.append("Two tiers: **installed** skills load into every Claude Code session as "
                 "`agent-toolkit:<name>`; **library** skills are browsable reference, fetched "
                 "on demand by `path` via the GitHub MCP (never auto-loaded).")
    lines.append("")

    # Installed skills, grouped by category
    lines.append("## Installed skills (session-loaded)")
    lines.append("")
    inst = [s for s in index["skills"] if s["tier"] == "installed"]
    by_cat: dict[str, list[dict]] = {}
    for s in inst:
        by_cat.setdefault(s["category"], []).append(s)
    for cat in sorted(by_cat):
        lines.append(f"### {cat} ({len(by_cat[cat])})")
        lines.append("")
        lines.append("| Skill | Invoke as | What it does |")
        lines.append("|---|---|---|")
        for s in sorted(by_cat[cat], key=lambda x: x["id"]):
            hint = (s["routing_hint"] or s["description"]).replace("|", "\\|")[:120]
            lines.append(f"| `{s['id']}` | `{s['namespace']}` | {hint} |")
        lines.append("")

    # Library, category table only (too large to list individually)
    lines.append("## Library (browsable via MCP, fetch by path)")
    lines.append("")
    lines.append("Not session-loaded. Discover via [`INDEX.json`](INDEX.json) → match → "
                 "fetch the skill's `path`. Category counts:")
    lines.append("")
    lines.append("| Category | Skills |")
    lines.append("|---|---|")
    lib_cats: dict[str, int] = {}
    for s in index["skills"]:
        if s["tier"] == "library":
            lib_cats[s["category"]] = lib_cats.get(s["category"], 0) + 1
    for cat, n in sorted(lib_cats.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {cat} | {n} |")
    lines.append("")

    # Agents
    lines.append("## Agents")
    lines.append("")
    lines.append("| Agent | Model | Purpose |")
    lines.append("|---|---|---|")
    for a in index["agents"]:
        d = (a["description"] or "").replace("|", "\\|")[:120]
        lines.append(f"| `{a['id']}` | {a['model']} | {d} |")
    lines.append("")

    # Workflows
    lines.append("## Workflows (multi-skill patterns)")
    lines.append("")
    lines.append("| Workflow | When to use |")
    lines.append("|---|---|")
    for w in index["workflows"]:
        when = (w["when"] or "").replace("|", "\\|")[:140]
        lines.append(f"| [`{w['id']}`]({w['path']}) | {when} |")
    lines.append("")

    (REPO / "NAVIGATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
