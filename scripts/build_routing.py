#!/usr/bin/env python3
"""Build the repository-relative skill/MCP routing registry.

Scans both skill tiers in this repository and writes the generated artifacts
under ``routing/registry``.  Paths are repository-relative so the catalog is
portable when the repository is cloned elsewhere.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALLED = REPO / "plugins" / "agent-toolkit" / "skills"
LIBRARY = REPO / "library"
OUT = REPO / "routing" / "registry"

DOMAIN_RULES = [
    ("agents/orchestration", [r"\borchestr", r"multi-agent", r"swarm", r"subagent", r"kanban", r"dispatch", r"\bagent\b", r"delegate", r"queen", r"yuno"]),
    ("zcode/tooling-meta", [r"\bskill\b", r"\bmcp\b", r"zcode", r"claude-code", r"agent-config", r"context-engineer", r"prompt-engineer"]),
    ("content/media", [r"video", r"audio", r"image", r"music", r"song", r"podcast", r"youtube", r"tiktok", r"creative", r"design", r"art", r"voice", r"soundtrack", r"gif", r"pixel", r"anime", r"presentation", r"infographic", r"icon", r"poster"]),
    ("web/frontend", [r"frontend", r"\bui\b", r"react", r"vue", r"tailwind", r"\bcss\b", r"landing", r"threejs", r"webgl", r"\bhtml\b", r"dashboard"]),
    ("backend/database", [r"backend", r"database", r"sql", r"postgres", r"supabase", r"clickhouse", r"api", r"express", r"koa", r"nest", r"\bcode\b", r"refactor", r"debug", r"typescript", r"python"]),
    ("devops/infra", [r"docker", r"kubernetes", r"\bk8s\b", r"deploy", r"infra", r"github", r"\bci\b", r"\bcd\b", r"linux", r"nginx", r"host", r"system", r"waydroid", r"wine", r"display", r"wifi", r"nvidia", r"\bvpc\b"]),
    ("AI/ML/LLM", [r"\bllm\b", r"\bml\b", r"\bai\b", r"model", r"huggingface", r"ollama", r"llama", r"vllm", r"axolotl", r"comfyui", r"minimax", r"gemini", r"\bdspy\b", r"rag", r"embedding", r"weights", r"wandb", r"jupyter", r"bioinformatic"]),
    ("productivity/notes", [r"obsidian", r"notion", r"apple", r"reminder", r"note", r"email", r"imessage", r"himalaya", r"calendar", r"briefing", r"report", r"kanban", r"todo", r"findmy"]),
    ("research/web", [r"research", r"arxiv", r"web.?search", r"web.?archive", r"scraper", r"firecrawl", r"perplexity", r"zread", r"web.?reader", r"polymarket", r"trend", r"wiki", r"knowledge", r"digest"]),
    ("security/audit", [r"security", r"audit", r"vuln", r"\bctf\b", r"forensic", r"attestation", r"lockin", r"vendor", r"hygiene"]),
    ("gaming/greyhack", [r"greyhack", r"greyscript", r"minecraft", r"pokemon", r"game", r"cp77", r"modding"]),
    ("iot/hardware", [r"3d.?print", r"stl", r"parametric", r"openhue", r"wear", r"esp", r"iot", r"raspberry"]),
    ("communication", [r"telegram", r"webhook", r"feishu", r"teamspeak", r"discord", r"agentmail", r"slack"]),
    ("writing/docs", [r"\bdocx\b", r"\bpdf\b", r"\bxlsx\b", r"\bexcel\b", r"epub", r"writing", r"humaniz", r"blog", r"seo", r"transcript", r"documentation", r"prd", r"spec", r"manim"]),
]
META_BUCKETS = {"agents/orchestration", "zcode/tooling-meta"}

SKILL_TO_MCP = {
    "github-workflow": ("github", "GitHub MCP / gh CLI fallback"),
    "github-issues": ("github", "GitHub MCP / gh CLI fallback"),
    "github-code-review": ("github", "GitHub MCP / gh CLI fallback"),
    "github-pr-workflow": ("github", "GitHub MCP / gh CLI fallback"),
    "github-auth": ("github", "GitHub MCP / gh CLI fallback"),
    "github-repo-management": ("github", "GitHub MCP / gh CLI fallback"),
    "github-branch-inventory": ("github", "GitHub MCP / gh CLI fallback"),
    "github-pr-merge-readiness": ("github", "GitHub MCP / gh CLI fallback"),
    "github-sweep-orchestration": ("github", "GitHub MCP / gh CLI fallback"),
    "github-portfolio-launch": ("github", "GitHub MCP / gh CLI fallback"),
    "github-grayhack-workflow": ("github", "GitHub MCP / gh CLI fallback"),
    "web_search": ("web-search-prime", "Web Search Prime; verify server availability"),
    "arxiv": ("web-search-prime", "ArXiv via web search; verify server availability"),
    "firecrawl-web": ("firecrawl", "Firecrawl MCP; verify server availability"),
    "notebooklm-bridge": ("notebooklm", "NotebookLM MCP; verify server availability"),
    "blender-mcp": ("blender", "Blender MCP; verify server availability"),
    "touchdesigner-mcp": ("touchdesigner", "TouchDesigner MCP; verify server availability"),
    "linear": ("linear", "Linear API; verify server availability"),
    "notion": ("notion", "Notion API; verify server availability"),
    "supabase": ("supabase", "Supabase/Postgres; verify server availability"),
    "supabase-postgres-best-practices": ("supabase", "Supabase/Postgres; verify server availability"),
    "airtable": ("airtable", "Airtable API; verify server availability"),
    "spotify": ("spotify", "Spotify API; verify server availability"),
    "maps": ("maps", "Google Maps API; verify server availability"),
    "openhue": ("openhue", "Philips Hue API; verify server availability"),
    "findmy": ("findmy", "Apple FindMy; verify server availability"),
    "imessage": ("imessage", "macOS iMessage bridge; verify server availability"),
    "himalaya": ("himalaya", "himalaya CLI; verify server availability"),
    "agentmail": ("agentmail", "AgentMail API; verify server availability"),
    "feishu-webhook": ("feishu", "Feishu/Lark webhook; verify server availability"),
    "1password": ("1password", "1Password MCP; verify server availability"),
    "google-workspace": ("google-workspace", "Google Workspace API; verify server availability"),
    "mmx-cli": ("mmx", "MMX CLI; verify server availability"),
}

NAME_DIR_MISMATCHES = {
    "pitfalls": "multi-agent-pitfalls-cheatsheet",
    "media": "animal-podcast",
    "navigator": "skill-navigator",
    "integration": "hermes-memory",
    "image": "image-remix",
    "audio": "voice-clone",
    "video": "youtube-creator",
    "creative-ideation": "ideation",
    "lm-evaluation-harness": "evaluating-llms-harness",
    "segment-anything": "segment-anything-model",
    "vllm": "serving-llms-vllm",
    "excel-xlsx": "Excel / XLSX",
    "data-analysis": "Data Analysis",
}


def parse_frontmatter(text: str) -> dict:
    if text.startswith("\ufeff"):
        text = text[1:]
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    result: dict[str, str] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        current = lines[i]
        scalar = re.match(r"^([\w-]+):\s*(.*)$", current)
        if not scalar:
            i += 1
            continue
        key, value = scalar.groups()
        value = value.strip()
        if value in {">", "|", ">-", "|-"}:
            i += 1
            parts = []
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                parts.append(lines[i].strip())
                i += 1
            result[key] = " ".join(p for p in parts if p)
            continue
        result[key] = value.strip("'\"")
        i += 1
    return result


def classify(name: str, description: str) -> str:
    blob = f"{name} {description}".lower()
    for bucket, patterns in DOMAIN_RULES:
        if any(re.search(pattern, blob) for pattern in patterns):
            return bucket
    return "other"


def build_record(path: Path, tier: str, base: Path) -> dict:
    fm = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    directory = path.parent.name
    name = str(fm.get("name") or directory).strip()
    description = re.sub(r"\s+", " ", str(fm.get("description") or "")).strip()
    relative = path.relative_to(REPO).as_posix()
    category = str(fm.get("category") or fm.get("domain") or "").strip()
    if not category:
        parts = path.parent.relative_to(base).parts
        category = parts[0] if len(parts) > 1 else "standalone"
    domain = classify(name, description)
    coupling = SKILL_TO_MCP.get(name)
    return {
        "id": f"{tier}:{relative}",
        "name": name,
        "dir": directory,
        "tier": tier,
        "path": relative,
        "source_root": "repo",
        "domain": domain,
        "is_meta": domain in META_BUCKETS,
        "description": description[:600],
        "mcp_server": coupling[0] if coupling else None,
        "mcp_note": coupling[1] if coupling else None,
        "name_dir_mismatch": NAME_DIR_MISMATCHES.get(directory),
    }


def scan(base: Path, tier: str) -> list[dict]:
    if not base.exists():
        return []
    records = []
    for path in sorted(base.rglob("SKILL.md")):
        if "/.archive/" in path.as_posix():
            continue
        records.append(build_record(path, tier, base))
    return records


def write_yaml(skills: list[dict]) -> None:
    by_domain: dict[str, list[str]] = {}
    for record in skills:
        by_domain.setdefault(record["domain"], []).append(record["name"])
    bucket_map = {
        "CODE_GENERATION": ["backend/database", "web/frontend", "zcode/tooling-meta"],
        "DATA_RETRIEVAL": ["backend/database", "research/web", "productivity/notes"],
        "ANALYSIS": ["research/web", "zcode/tooling-meta", "AI/ML/LLM", "security/audit"],
        "COMMUNICATION": ["communication", "content/media", "writing/docs"],
        "INFRASTRUCTURE": ["devops/infra", "backend/database"],
        "RESEARCH": ["research/web", "AI/ML/LLM"],
    }
    lines = [
        "# GENERATED by scripts/build_index.py; do not hand-edit.",
        "# Candidate lists are derived from repository-relative skill frontmatter.",
        "",
        "meta_penalty:",
        "  buckets: ['agents/orchestration', 'zcode/tooling-meta']",
        f"  count: {sum(record['is_meta'] for record in skills)}",
        "  rule: De-prioritize these buckets unless the request is explicitly about the agent system.",
        "",
        "name_dir_mismatches:",
    ]
    for directory, name in NAME_DIR_MISMATCHES.items():
        lines.append(f"  {directory}: {json.dumps(name, ensure_ascii=False)}")
    lines.extend(["", "intent_buckets:"])
    for intent, domains in bucket_map.items():
        candidates = []
        for domain in domains:
            candidates.extend(sorted(set(by_domain.get(domain, [])))[:8])
        lines.append(f"  {intent}:")
        lines.append(f"    candidate_domains: {json.dumps(domains)}")
        lines.append(f"    sample_candidates: {json.dumps(candidates[:20], ensure_ascii=False)}")
    lines.extend([
        "",
        "mcp_servers_configured:",
        "  - github  # Dockerized toqsick/github-mcp-server:develop; PAT passed by host env",
        "mcp_servers_unconfigured_overrides:",
        "  - web-search-prime",
        "  - firecrawl",
        "  - notebooklm",
        "  - blender",
        "  - touchdesigner",
        "  - linear",
        "  - notion",
        "  - supabase",
        "  - airtable",
        "  - spotify",
        "  - maps",
        "  - openhue",
        "  - findmy",
        "  - imessage",
        "  - himalaya",
        "  - agentmail",
        "  - feishu",
        "  - 1password",
        "  - google-workspace",
        "  - mmx",
        "",
        "see_also:",
        "  - registry.json",
        "  - skill-to-mcp.csv",
        "  - ../config/mcp-template.json",
    ])
    (OUT / "routing.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    skills = sorted(scan(INSTALLED, "installed") + scan(LIBRARY, "library"), key=lambda r: (r["tier"], r["path"]))
    registry = {
        "schemaVersion": "2.0",
        "generated_by": "scripts/build_index.py",
        "repo": "Toqsick/my-agent-tools",
        "source": "repository-relative skill trees",
        "counts": {
            "installed": sum(r["tier"] == "installed" for r in skills),
            "library": sum(r["tier"] == "library" for r in skills),
            "total": len(skills),
            "mcp_coupled": sum(bool(r["mcp_server"]) for r in skills),
            "meta_penalized": sum(r["is_meta"] for r in skills),
        },
        "skills": skills,
    }
    (OUT / "registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT / "skill-to-mcp.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["skill_name", "mcp_server", "note", "configured"])
        for record in skills:
            if record["mcp_server"]:
                writer.writerow([record["name"], record["mcp_server"], record["mcp_note"], record["mcp_server"] == "github"])
    write_yaml(skills)
    print(f"routing registry: {len(skills)} skills; {registry['counts']['mcp_coupled']} MCP mappings; {registry['counts']['meta_penalized']} meta-penalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
